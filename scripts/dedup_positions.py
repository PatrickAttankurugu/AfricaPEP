"""Deduplicate Position and Organisation nodes in Neo4j.

Before #32, Position/Organisation ids were random, so every pipeline run
minted new nodes for the same real-world position ("President of Ghana"
existing 5x). #32 made ids deterministic (uuid5 over content), which stops
NEW duplication but leaves the old duplicate nodes in place. This script
cleans them up:

- Groups Position nodes by (title, institution, country, branch) and
  Organisation nodes by (name, country), case-insensitively, matching the
  content-id derivation in the resolver.
- Keeps the node whose id already equals the canonical content id when one
  exists; otherwise keeps one node and RENAMES its id to the canonical
  content id, so future seed runs MERGE onto it instead of re-creating.
- Re-points relationships onto the keeper, preserving relationship
  properties. Distinct HELD_POSITION periods (e.g. two presidential terms)
  are kept as separate relationships; identical periods collapse to one.
- Detach-deletes the emptied duplicates.

Usage:
    python -m scripts.dedup_positions --dry-run   # report only, no writes
    python -m scripts.dedup_positions             # apply
"""
from __future__ import annotations

import argparse
import os
import sys
import uuid

from neo4j import GraphDatabase

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from africapep.config import settings  # noqa: E402

# Must mirror africapep/pipeline/resolver.py exactly.
_CONTENT_ID_NAMESPACE = uuid.UUID("7f3d9b2a-4c81-4f6e-9d25-8a1b3c5e7f90")


def _content_id(*parts: str | None) -> str:
    key = "|".join((p or "").strip().lower() for p in parts)
    return str(uuid.uuid5(_CONTENT_ID_NAMESPACE, key))


def dedup_positions(session, dry_run: bool) -> tuple[int, int]:
    groups = list(session.run("""
        MATCH (pos:Position)
        WITH toLower(trim(coalesce(pos.title, ''))) AS t,
             toLower(trim(coalesce(pos.institution, ''))) AS i,
             toLower(trim(coalesce(pos.country, ''))) AS c,
             toLower(trim(coalesce(pos.branch, ''))) AS b,
             collect(pos) AS nodes
        WHERE size(nodes) > 1
        RETURN [n IN nodes | n.id] AS ids,
               nodes[0].title AS title,
               nodes[0].institution AS institution,
               nodes[0].country AS country,
               nodes[0].branch AS branch,
               size(nodes) AS count
        ORDER BY count DESC
    """))
    print(f"Position duplicate groups: {len(groups)}")
    removed = 0

    for g in groups:
        canonical = _content_id(
            "position", g["title"], g["institution"], g["country"], g["branch"]
        )
        ids = g["ids"]
        keeper = canonical if canonical in ids else ids[0]
        dups = [i for i in ids if i != keeper]
        print(f"  {g['count']}x '{g['title']}' ({g['country']}) -> keep {keeper}"
              + ("" if keeper == canonical else f", rename to {canonical}"))
        if dry_run:
            removed += len(dups)
            continue

        if keeper != canonical:
            session.run(
                "MATCH (p:Position {id: $old}) SET p.id = $new",
                {"old": keeper, "new": canonical},
            )
            keeper = canonical

        # Re-point HELD_POSITION, preserving properties; a rel with the same
        # period on the keeper counts as already present (identical periods
        # collapse, distinct terms survive).
        session.run("""
            UNWIND $dups AS did
            MATCH (person:Person)-[r:HELD_POSITION]->(dup:Position {id: did})
            MATCH (keep:Position {id: $keeper})
            WHERE NOT EXISTS {
                MATCH (person)-[k:HELD_POSITION]->(keep)
                WHERE coalesce(k.start_date, '') = coalesce(r.start_date, '')
                  AND coalesce(k.end_date, '') = coalesce(r.end_date, '')
            }
            CREATE (person)-[nk:HELD_POSITION]->(keep)
            SET nk = properties(r)
        """, {"dups": dups, "keeper": keeper})

        # Re-point AT_ORGANISATION (no meaningful properties on this rel)
        session.run("""
            UNWIND $dups AS did
            MATCH (dup:Position {id: did})-[:AT_ORGANISATION]->(org:Organisation)
            MATCH (keep:Position {id: $keeper})
            MERGE (keep)-[:AT_ORGANISATION]->(org)
        """, {"dups": dups, "keeper": keeper})

        session.run("""
            UNWIND $dups AS did
            MATCH (dup:Position {id: did})
            DETACH DELETE dup
        """, {"dups": dups})
        removed += len(dups)

    return len(groups), removed


def dedup_organisations(session, dry_run: bool) -> tuple[int, int]:
    groups = list(session.run("""
        MATCH (org:Organisation)
        WITH toLower(trim(coalesce(org.name, ''))) AS n,
             toLower(trim(coalesce(org.country, ''))) AS c,
             collect(org) AS nodes
        WHERE size(nodes) > 1
        RETURN [x IN nodes | x.id] AS ids,
               nodes[0].name AS name,
               nodes[0].country AS country,
               size(nodes) AS count
        ORDER BY count DESC
    """))
    print(f"Organisation duplicate groups: {len(groups)}")
    removed = 0

    for g in groups:
        canonical = _content_id("organisation", g["name"], g["country"])
        ids = g["ids"]
        keeper = canonical if canonical in ids else ids[0]
        dups = [i for i in ids if i != keeper]
        print(f"  {g['count']}x '{g['name']}' ({g['country']})")
        if dry_run:
            removed += len(dups)
            continue

        if keeper != canonical:
            session.run(
                "MATCH (o:Organisation {id: $old}) SET o.id = $new",
                {"old": keeper, "new": canonical},
            )
            keeper = canonical

        session.run("""
            UNWIND $dups AS did
            MATCH (pos:Position)-[:AT_ORGANISATION]->(dup:Organisation {id: did})
            MATCH (keep:Organisation {id: $keeper})
            MERGE (pos)-[:AT_ORGANISATION]->(keep)
        """, {"dups": dups, "keeper": keeper})

        session.run("""
            UNWIND $dups AS did
            MATCH (dup:Organisation {id: did})
            DETACH DELETE dup
        """, {"dups": dups})
        removed += len(dups)

    return len(groups), removed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true",
                        help="Report duplicate groups without modifying anything")
    args = parser.parse_args()

    driver = GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
    )
    mode = "DRY RUN" if args.dry_run else "APPLY"
    print(f"Position/Organisation dedup ({mode})")

    with driver.session() as session:
        pos_groups, pos_removed = dedup_positions(session, args.dry_run)
        org_groups, org_removed = dedup_organisations(session, args.dry_run)

        totals = session.run("""
            MATCH (p:Position) WITH count(p) AS positions
            MATCH (o:Organisation)
            RETURN positions, count(o) AS organisations
        """).single()

    driver.close()
    verb = "would remove" if args.dry_run else "removed"
    print(f"\nPositions: {pos_groups} groups, {verb} {pos_removed} duplicates "
          f"({totals['positions']} nodes now)")
    print(f"Organisations: {org_groups} groups, {verb} {org_removed} duplicates "
          f"({totals['organisations']} nodes now)")
    if not args.dry_run:
        print("\nRemember to re-sync PostgreSQL: "
              "python -c \"from africapep.database.sync import sync_all; sync_all()\"")
    print("Done.")


if __name__ == "__main__":
    main()
