# Name-matching evaluation harness + phonetic matching — design

**Date:** 2026-06-21
**Status:** Approved for implementation

## Problem

`hybrid_name_score` (`africapep/pipeline/scoring.py`) is the heart of AfricaPEP's
matching: it is called by **both** entity resolution (dedup, precision-first) and
screening (AML name match, recall-first). Today it is `max(Levenshtein
token-sort, Jaro-Winkler)` — pure orthographic edit distance, which:

- **Cannot match transliteration/spelling variants** ("Mohammed/Muhammad/Mohamed",
  "Diallo/Jallow") → screening misses real PEPs and resolution under-merges
  transliterated duplicates.
- **Over-merges orthographically-close but distinct people** in resolution (a
  known open bug) because a single blended number, gated at a magic 0.85, cannot
  distinguish "same name spelled differently" from "two different short names".

There is also **no way to measure match quality** — no labeled benchmark — so any
"improvement" is unprovable and the over-merge went undetected.

## Goals

1. A **name-matching evaluation harness** that produces precision / recall / F1
   and a dedicated **merge-precision** metric, grounded in Wikidata QID identity
   labels, runnable as a script and as a regression-guarding pytest.
2. **Phonetic matching** added as a *separate signal*, deployable now with no new
   infrastructure (pure-Python).
3. A **scorer refactor** that exposes component sub-scores so each caller applies
   its own risk policy: screening boosts recall; resolution requires
   corroboration before auto-merge (fixing the over-merge).

## Non-goals (YAGNI / deferred)

- Embeddings, `pgvector`, ANN blocking (see "Future" below).
- Probabilistic record linkage (Fellegi–Sunter / Splink).
- Neural transliteration.
- The Position/Organisation/SourceRecord per-run-UUID duplication bug.

These become *measured* follow-ons once the harness exists to justify them.

## Architecture

Three independently-testable units; callers change only in how they consume scores.

| Unit | File | Responsibility |
|---|---|---|
| Phonetic encoder | `africapep/pipeline/phonetic.py` (new) | Encode a name to phonetic keys; return 0–1 phonetic similarity between two names. Pure-Python. |
| Scorer (refactor) | `africapep/pipeline/scoring.py` | `name_match_components(a, b) -> NameMatchScore(orthographic, phonetic)`. Keep `hybrid_name_score` as a thin backward-compatible wrapper. |
| Eval harness | `scripts/eval_name_matching.py` (new) + `tests/test_name_matching_eval.py` (new) | Build QID-grounded labeled pairs, compute metrics, guard regression. |

### Data flow

```
name pair ──> name_match_components() ──> {orthographic, phonetic}
                                               │
                  ┌────────────────────────────┴───────────────────────────┐
        screening (recall)                                     resolution (precision)
   match = max(orthographic, phonetic)        auto-merge iff orthographic>=MERGE
   surface for review                          OR (phonetic>=PHON AND corroborated
                                               by DOB or position match)
```

## Component 1 — Phonetic encoder (`phonetic.py`)

- **Algorithm:** Double Metaphone via the `jellyfish` library (lightweight,
  maintained, pure-Python; no model, no disk cost). Generates primary + alternate
  codes, catching cross-spelling variants.
- **Token-aware:** encode each name token, compare as sets (names reorder across
  cultures). Phonetic similarity = size of best-matching token alignment / max
  token count, in 0–1.
- **API:**
  - `phonetic_keys(name: str) -> list[tuple[str, str]]` — (primary, alternate) per token.
  - `phonetic_similarity(a: str, b: str) -> float` — 0–1.
- **Edge cases:** empty / single-token / punctuation-only names return 0.0
  cleanly; non-ASCII is diacritic-folded (reuse normaliser helper) before encoding.

## Component 2 — Scorer refactor (`scoring.py`)

- New dataclass `NameMatchScore(orthographic: float, phonetic: float)` with a
  convenience `.best` = `max(orthographic, phonetic)`.
- `name_match_components(a, b) -> NameMatchScore`:
  - `orthographic` = existing `max(token_sort_ratio, Jaro-Winkler)` (unchanged math).
  - `phonetic` = `phonetic_similarity(a, b)`.
- `hybrid_name_score(a, b) -> float` retained, now `= name_match_components(a, b).orthographic`
  — **identical** to today's behaviour, so existing callers/tests are unaffected
  until deliberately migrated.

## Component 3 — Per-caller policy

- **Screening (`screen.py`):** rerank/match score becomes
  `name_match_components(query, candidate).best` (and over each name variant).
  Recall-first: phonetic-only matches now surface for human review. Threshold
  semantics unchanged (caller still passes `threshold`).
- **Resolution (`resolver.py`):** replace the single-score auto-merge test. Keep
  the composite for ranking, but **auto-merge requires corroboration**:
  - `orthographic >= MERGE_THRESHOLD (0.85)`  **OR**
  - `phonetic >= PHONETIC_THRESHOLD (0.90)` **AND** a second signal agrees
    (DOB equal, or position/institution fuzzy match above the existing position
    sub-score bar).
  - Phonetic alone never triggers a merge → tightens the over-merging path.
  - QID fast-path (exact same QID) is unchanged and still wins first.

## Component 4 — Evaluation harness

**Ground truth from Wikidata QIDs (free labels):**
- **Positive pairs** (same person): name variants sharing a QID — from stored
  `name_variants` and multilingual labels.
- **Negative pairs** (different people): different QIDs. Include **hard negatives**
  — different QIDs in the *same blocking bucket* (country + surname initial), the
  exact pairs resolution confuses.

**Metrics:**
- Precision / recall / F1 at a threshold.
- Precision–recall curve across thresholds (evidence-based threshold selection).
- **merge-precision:** of pairs scoring at/above the auto-merge rule, fraction
  truly same-QID — directly measures the over-merge bug.
- Reported per the orthographic-only baseline vs the orthographic+phonetic policy,
  so the delta is explicit.

**Two entry points:**
- `scripts/eval_name_matching.py` — full report against a sampled dataset
  (JSON fixture, or pulled from the DB when available). Prints tables.
- `tests/test_name_matching_eval.py` — runs on a small committed fixture of
  labeled pairs; **asserts metrics do not regress** below a committed baseline
  (precision, recall, merge-precision floors).

## Testing & verification

- Unit: phonetic encoder (known variant pairs match; distinct names don't; edge
  cases), scorer returns both components, `hybrid_name_score` wrapper unchanged.
- Eval pytest: metrics computed on fixtures, asserted against baseline floors.
- Before/after: run harness on current `main` to capture baseline numbers, then
  after the change — prove merge-precision rose (over-merge reduced) and screening
  recall rose or held, with numbers.

## Dependencies

- Add `jellyfish` to `requirements.txt` (pure-Python, small). No infra changes,
  no server disk impact beyond a small wheel. Deployable via the existing
  `docker cp` + restart path (no rebuild needed for a pure-Python dep only if the
  wheel is already present; otherwise a one-time `pip install` in-container or a
  rebuild — noted for the deploy step).

## Future / out-of-scope decisions (captured for the next spec)

**Embeddings — open vs closed (decided):** use **open-source, self-hosted**, not a
closed API.
- Rationale: this is a KYC/AML system handling PEP PII; sending every screened
  name to a third-party US API (OpenAI/Cohere/Voyage) is a data-residency /
  retention / cross-border-egress problem. Self-hosting keeps PII on our infra,
  removes per-call cost on the screening hot path, and gives deterministic,
  auditable, version-pinned scores. (Anthropic has no embedding model; their
  ecosystem points to Voyage, which still has the egress problem.)
- Model choice: **not** vanilla `all-MiniLM-L6-v2` (English-centric). Baseline =
  `paraphrase-multilingual-MiniLM-L12-v2` (~470MB, CPU-fine). Real SOTA target =
  **fine-tune a small name-embedder** on the QID-derived pairs this harness
  produces — task-specialized small model beats a large general one for proper-noun
  variation, at zero marginal query cost and zero PII egress.
- Server reality: at ~95% disk, no GPU — fine-tune offline, serve on CPU; needs
  `pgvector` (not yet installed) for ANN. All deferred until the harness proves the
  gain over phonetic.
