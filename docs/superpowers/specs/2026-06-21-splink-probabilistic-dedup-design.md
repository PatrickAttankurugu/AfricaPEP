# Splink probabilistic dedup pass — design

**Date:** 2026-06-21
**Status:** Approved for implementation

## Problem

Entity resolution (`resolver.py`) uses hand-tuned weights (name 0.5 / DOB 0.3 /
position 0.2) and a magic 0.85 threshold. After the QID-stable-id fix, same-QID
records dedupe correctly, but **cross-QID duplicates** (two different Wikidata
items that are the same human) and no-QID records are never linked. The hand-tuned
gate gives no calibrated probability, so the merge/no-merge line is unprincipled
and unauditable — a poor fit for an AML product.

## Goal

A **probabilistic record-linkage batch pass** using Splink (Fellegi-Sunter via
DuckDB) that scores Person pairs with calibrated match probabilities, clusters
duplicates, and acts with an AML-safe policy: auto-merge only very-high-confidence
clusters, queue medium-confidence pairs for human review, ignore the rest.

## Constraints / decisions

- **Offline-capable**: runs off the server (against a Postgres dump or live read),
  so the ~400 MB Splink/DuckDB dependency never touches the 95%-full server image.
- **Splink stays out of the runtime image**: a separate `requirements-dedup.txt`;
  the containers' `requirements.txt` is unchanged.
- **AML-safe action policy** (your decision): auto-merge ≥0.99 *with corroboration*;
  review 0.90–0.99; ignore <0.90.
- **Batch, separate from scraping**: incremental `add()` keeps ingesting; this is a
  periodic/manual cleanup pass that supersedes the crude `scripts/dedup_neo4j.py`.

## Non-goals (YAGNI)

Replacing incremental `add()`; Spark/Athena backends; real-time linkage;
auto-approving the review queue (human-approved only).

## Architecture

```
Postgres pep_profiles (or CSV dump)
        │  read flat rows: neo4j_id, full_name, name_variants, dob, nationality, positions
        ▼
  prepare DataFrame  ── add phonetic surname key + metaphone column (reuse phonetic.py)
        ▼
  Splink (DuckDB)  ── settings → train (u-sampling + EM) → predict pairwise probs → cluster
        ▼
  classify_clusters()  ── PURE policy (no Splink): auto-merge / review / ignore
        ▼
  driver acts:  merge in Neo4j  +  write duplicate_review  +  re-sync Postgres
        │  (default --dry-run: report only, change nothing)
```

### Components

| Unit | File | Responsibility | Splink? |
|---|---|---|---|
| Model | `africapep/pipeline/splink_resolver.py` | Build settings, train, predict, cluster. | yes |
| Policy | same module: `classify_pairs()` | Route pairwise (prob, corroboration) → AUTO_MERGE / REVIEW / IGNORE. Pure function over a list/DataFrame. | **no** (unit-testable) |
| Driver | `scripts/run_splink_dedup.py` | Read input (Postgres or `--input CSV`); run model; `--dry-run` default; else merge Neo4j + write review + resync. | yes |
| Review table | `africapep/database/schema/postgres_schema.sql` | `duplicate_review`. | n/a |
| Optional deps | `requirements-dedup.txt` | `splink==4.0.16` (+ transitive). NOT in runtime image. | n/a |

## Splink model configuration

- **Backend:** DuckDB (in-process, in-memory; trivial for ~21K rows).
- **Blocking rules** (limit pairs): `block_on("nationality", "phonetic_surname")`,
  and `block_on("date_of_birth")`. Union of rules generates candidate pairs.
- **Comparisons:**
  - `full_name`: `JaroWinklerAtThresholds("full_name", [0.92, 0.82])` plus a
    phonetic level (exact match on a precomputed `metaphone_name` column) so
    transliteration variants register. Levels: exact / JW≥0.92 / phonetic / JW≥0.82 / else.
  - `date_of_birth`: exact / same-year / else; null-handled.
  - `nationality`: exact / else (also a blocking key).
  - `position` (top current title+institution): fuzzy / else.
- **Training (the part the smoke test showed is fragile):**
  1. `estimate_probability_two_random_records_match(deterministic_rules, recall)`
     — set the prior instead of leaving the 0.0001 default.
  2. `estimate_u_using_random_sampling(max_pairs=1e6)`.
  3. EM with **column-fixing** blocking rules — one EM run per fixed column so the
     others' m-values are observed: `block_on("date_of_birth")` and
     `block_on("phonetic_surname")`. (A single naive EM rule leaves `full_name`
     untrained — confirmed in API smoke test.)
- **Calibration check:** report match-probability separation on the QID-labeled
  pairs from `tests/fixtures/name_match_pairs.json` (ties into the eval harness):
  same-person pairs should score high, different-person low.

## Action policy (AML-safe)

`classify_pairs()` consumes pairwise predictions `(neo4j_id_l, neo4j_id_r,
match_probability)` plus the row attributes needed for corroboration:

- `probability ≥ 0.99` **and** corroboration (exact DOB match **or** position
  match ≥ 0.85 — reuses the resolver's corroboration rule) → **AUTO_MERGE**.
- `0.90 ≤ probability < 0.99`, or ≥0.99 without corroboration → **REVIEW**.
- `< 0.90` → **IGNORE**.

Thresholds in `africapep/config.py` (`splink_automerge_prob=0.99`,
`splink_review_prob=0.90`) so posture is tunable without code change.

Clustering: connected components at the review threshold define candidate groups;
within a group, pairs are routed per the rule above. Auto-merge consolidates a
cluster to the most-connected node (union positions/sources/name_variants), exactly
like `dedup_neo4j.py`'s merge step.

## `duplicate_review` table

```sql
CREATE TABLE IF NOT EXISTS duplicate_review (
    id              UUID PRIMARY KEY,
    neo4j_id_a      TEXT NOT NULL,
    neo4j_id_b      TEXT NOT NULL,
    name_a          TEXT,
    name_b          TEXT,
    match_probability DOUBLE PRECISION NOT NULL,
    matched_fields  JSONB,
    status          TEXT NOT NULL DEFAULT 'PENDING',  -- PENDING|MERGED|REJECTED
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (neo4j_id_a, neo4j_id_b)
);
```

## Driver (`scripts/run_splink_dedup.py`)

- `--input <csv>`: read rows from a dump (offline); default reads live Postgres.
- `--dry-run` (default ON): print the merge plan + review counts, change nothing.
- `--apply`: perform Neo4j merges, write `duplicate_review`, re-sync Postgres.
- `--output <json>`: write the full classification (for offline review / audit).
- Reuses `neo4j_client` merge helpers and `sync_all()`.

## Testing & verification

- **Pure policy tests (always run, no Splink):** `classify_pairs()` routes
  ≥0.99+corroboration → AUTO_MERGE; 0.90–0.99 → REVIEW; <0.90 → IGNORE; ≥0.99
  without corroboration → REVIEW.
- **Splink integration test (`importorskip('splink')`):** train on a synthetic
  labeled DataFrame (same/different people incl. transliteration variants); assert
  same-person rows land in one cluster and different-person rows do not.
- **Calibration script:** report probability separation on the QID fixture.
- **Dry-run on prod data** before any `--apply`.

## Dependency & deploy

- `requirements-dedup.txt` (new): `splink==4.0.16`. Installed only where the batch
  runs (locally / an ops box), never in `africapep-api`/`africapep-scraper`.
- No server image change; no API hot-path change. Running `--apply` writes to
  Neo4j + Postgres over their existing connections.
