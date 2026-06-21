"""Run the Splink probabilistic dedup pass over Person records.

Offline-capable batch tool. Reads flat Person rows (live PostgreSQL or a CSV
dump), scores pairs with Splink, and applies the AML-safe policy: auto-merge
very-high-confidence corroborated clusters in Neo4j, queue medium-confidence
pairs in the ``duplicate_review`` table, ignore the rest.

Default is --dry-run (report only; change nothing). Requires the offline deps:
    pip install -r requirements.txt -r requirements-dedup.txt

Usage:
    python scripts/run_splink_dedup.py                    # dry-run, live Postgres
    python scripts/run_splink_dedup.py --input rows.csv   # dry-run, offline dump
    python scripts/run_splink_dedup.py --apply            # perform merges + review
    python scripts/run_splink_dedup.py --output plan.json # save full classification

CSV/dump columns: neo4j_id, full_name, date_of_birth, nationality, position
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from africapep.pipeline.splink_resolver import (  # noqa: E402
    PairAction, prepare_dataframe, train_linker, predict_pairs, decide_pairs,
)


def _position_str(current_positions) -> str:
    """Representative 'title @ institution' from a current_positions JSON list."""
    if isinstance(current_positions, str):
        try:
            current_positions = json.loads(current_positions)
        except (ValueError, TypeError):
            return ""
    if isinstance(current_positions, list) and current_positions:
        p = current_positions[0]
        if isinstance(p, dict):
            return f"{p.get('title', '')} @ {p.get('institution', '')}".strip(" @")
    return ""


def load_rows_from_postgres() -> list[dict]:
    from sqlalchemy import text
    from africapep.database.postgres_client import get_db

    rows = []
    with get_db() as db:
        result = db.execute(text(
            "SELECT neo4j_id, full_name, date_of_birth, nationality, "
            "current_positions FROM pep_profiles WHERE neo4j_id IS NOT NULL"
        ))
        for r in result.fetchall():
            rows.append({
                "neo4j_id": r.neo4j_id,
                "full_name": r.full_name,
                "date_of_birth": str(r.date_of_birth) if r.date_of_birth else "",
                "nationality": r.nationality,
                "position": _position_str(r.current_positions),
            })
    return rows


def load_rows_from_csv(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [
            {
                "neo4j_id": r["neo4j_id"],
                "full_name": r.get("full_name", ""),
                "date_of_birth": r.get("date_of_birth", "") or "",
                "nationality": r.get("nationality", ""),
                "position": r.get("position", ""),
            }
            for r in csv.DictReader(f)
        ]


def _union_find(pairs):
    """Cluster auto-merge pairs into connected components (id -> root)."""
    parent = {}

    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        parent[find(a)] = find(b)

    for a, b in pairs:
        union(a, b)
    clusters: dict[str, list[str]] = {}
    for node in list(parent):
        clusters.setdefault(find(node), []).append(node)
    return [c for c in clusters.values() if len(c) > 1]


# ── Neo4j merge (mirrors scripts/dedup_neo4j.py) ──

def _merge_cluster(session, ids: list[str]) -> str:
    """Merge a cluster of Person ids into the most-connected node; return it."""
    counts = session.run(
        "UNWIND $ids AS pid MATCH (p:Person {id: pid}) "
        "OPTIONAL MATCH (p)-[:HELD_POSITION]->(pos) "
        "RETURN pid, count(pos) AS c ORDER BY c DESC", {"ids": ids})
    ordered = [r["pid"] for r in counts]
    primary, secondaries = ordered[0], ordered[1:]
    session.run("""
        MATCH (primary:Person {id: $p})
        UNWIND $sids AS sid MATCH (s:Person {id: sid})
        WITH primary, s,
             [v IN s.name_variants WHERE NOT v IN primary.name_variants] AS nv
        SET primary.name_variants = primary.name_variants + nv,
            primary.date_of_birth = coalesce(primary.date_of_birth, s.date_of_birth)
    """, {"p": primary, "sids": secondaries})
    for rel in ("HELD_POSITION", "SOURCED_FROM", "CITIZEN_OF"):
        session.run(f"""
            UNWIND $sids AS sid
            MATCH (s:Person {{id: sid}})-[r:{rel}]->(t)
            MATCH (primary:Person {{id: $p}})
            WHERE NOT (primary)-[:{rel}]->(t)
            MERGE (primary)-[:{rel}]->(t) DELETE r
        """, {"p": primary, "sids": secondaries})
    session.run("UNWIND $sids AS sid MATCH (s:Person {id: sid}) DETACH DELETE s",
                {"sids": secondaries})
    return primary


def apply_changes(decisions, rows_by_id) -> dict:
    """Perform auto-merges in Neo4j, write review rows to Postgres, re-sync."""
    from neo4j import GraphDatabase
    from sqlalchemy import text
    from africapep.config import settings
    from africapep.database.postgres_client import get_db
    from africapep.database.sync import sync_all

    auto = [(d.id_a, d.id_b) for d in decisions if d.action == PairAction.AUTO_MERGE]
    reviews = [d for d in decisions if d.action == PairAction.REVIEW]
    clusters = _union_find(auto)

    merged_clusters = 0
    driver = GraphDatabase.driver(
        settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password))
    with driver.session() as session:
        for ids in clusters:
            _merge_cluster(session, ids)
            merged_clusters += 1
    driver.close()

    with get_db() as db:
        for d in reviews:
            a, b = sorted((d.id_a, d.id_b))
            db.execute(text("""
                INSERT INTO duplicate_review
                    (id, neo4j_id_a, neo4j_id_b, name_a, name_b,
                     match_probability, matched_fields, status)
                VALUES (:id, :a, :b, :na, :nb, :prob, CAST(:mf AS jsonb), 'PENDING')
                ON CONFLICT (neo4j_id_a, neo4j_id_b) DO UPDATE
                    SET match_probability = EXCLUDED.match_probability
            """), {
                "id": str(uuid.uuid4()), "a": a, "b": b,
                "na": rows_by_id.get(d.id_a, {}).get("full_name"),
                "nb": rows_by_id.get(d.id_b, {}).get("full_name"),
                "prob": d.probability,
                "mf": json.dumps({"corroborated": d.corroborated}),
            })

    synced = sync_all()
    return {"merged_clusters": merged_clusters, "review_rows": len(reviews),
            "resynced": synced}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", help="CSV dump instead of live Postgres")
    parser.add_argument("--apply", action="store_true",
                        help="perform merges + write review (default: dry-run)")
    parser.add_argument("--output", help="write full classification JSON here")
    args = parser.parse_args()

    rows = load_rows_from_csv(args.input) if args.input else load_rows_from_postgres()
    print(f"Loaded {len(rows)} Person rows")
    rows_by_id = {r["neo4j_id"]: r for r in rows}

    df = prepare_dataframe(rows)
    linker = train_linker(df)
    pairs = predict_pairs(linker)
    decisions = decide_pairs([(a, b, p) for a, b, p in pairs], rows_by_id)

    counts = {a.value: 0 for a in PairAction}
    for d in decisions:
        counts[d.action.value] += 1
    print(f"Scored pairs: {len(decisions)}  -> {counts}")

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump([{
                "id_a": d.id_a, "id_b": d.id_b, "probability": d.probability,
                "corroborated": d.corroborated, "action": d.action.value,
                "name_a": rows_by_id.get(d.id_a, {}).get("full_name"),
                "name_b": rows_by_id.get(d.id_b, {}).get("full_name"),
            } for d in decisions], f, indent=2, ensure_ascii=False)
        print(f"Wrote classification -> {args.output}")

    if args.apply:
        result = apply_changes(decisions, rows_by_id)
        print(f"APPLIED: {result}")
    else:
        clusters = _union_find(
            [(d.id_a, d.id_b) for d in decisions if d.action == PairAction.AUTO_MERGE])
        print(f"DRY-RUN: would merge {len(clusters)} cluster(s), "
              f"queue {counts['REVIEW']} review pair(s). Re-run with --apply.")


if __name__ == "__main__":
    main()
