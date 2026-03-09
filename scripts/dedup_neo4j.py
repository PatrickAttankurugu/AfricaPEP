"""Deduplicate existing Person nodes in Neo4j.

Finds Person nodes with the same full_name + nationality, merges their
positions, sources, and name_variants into the node with the most
relationships, then deletes the duplicates.

Usage:
    python -m scripts.dedup_neo4j
"""
from neo4j import GraphDatabase
from africapep.config import settings
import structlog

log = structlog.get_logger()


def main():
    driver = GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
    )

    with driver.session() as session:
        # Step 1: Find duplicate groups (same full_name + nationality)
        dupes = session.run("""
            MATCH (p:Person)
            WITH p.full_name AS name, p.nationality AS nat, collect(p) AS nodes
            WHERE size(nodes) > 1
            RETURN name, nat, [n IN nodes | n.id] AS ids, size(nodes) AS count
            ORDER BY count DESC
        """)
        dupe_groups = list(dupes)
        print(f"Found {len(dupe_groups)} duplicate groups")

        for group in dupe_groups:
            name = group["name"]
            ids = group["ids"]
            print(f"  Merging {group['count']}x '{name}' ({group['nat']})")

            # Pick the node with the most HELD_POSITION relationships as primary
            counts = session.run("""
                UNWIND $ids AS pid
                MATCH (p:Person {id: pid})
                OPTIONAL MATCH (p)-[:HELD_POSITION]->(pos)
                RETURN pid, count(pos) AS pos_count
                ORDER BY pos_count DESC
            """, {"ids": ids})
            count_list = list(counts)
            primary_id = count_list[0]["pid"]
            secondary_ids = [c["pid"] for c in count_list[1:]]

            print(f"    Primary: {primary_id}")

            # Step 2: Merge name_variants from secondaries into primary
            session.run("""
                MATCH (primary:Person {id: $primary_id})
                UNWIND $secondary_ids AS sid
                MATCH (s:Person {id: sid})
                WITH primary, s,
                     [v IN s.name_variants WHERE NOT v IN primary.name_variants] AS new_variants
                SET primary.name_variants = primary.name_variants + new_variants
                WITH primary, s
                SET primary.date_of_birth = coalesce(primary.date_of_birth, s.date_of_birth)
            """, {"primary_id": primary_id, "secondary_ids": secondary_ids})

            # Step 3: Move HELD_POSITION relationships
            session.run("""
                UNWIND $secondary_ids AS sid
                MATCH (s:Person {id: sid})-[r:HELD_POSITION]->(pos:Position)
                MATCH (primary:Person {id: $primary_id})
                WHERE NOT (primary)-[:HELD_POSITION]->(pos)
                MERGE (primary)-[:HELD_POSITION]->(pos)
                DELETE r
            """, {"primary_id": primary_id, "secondary_ids": secondary_ids})

            # Step 4: Move SOURCED_FROM relationships
            session.run("""
                UNWIND $secondary_ids AS sid
                MATCH (s:Person {id: sid})-[r:SOURCED_FROM]->(src:SourceRecord)
                MATCH (primary:Person {id: $primary_id})
                WHERE NOT (primary)-[:SOURCED_FROM]->(src)
                MERGE (primary)-[:SOURCED_FROM]->(src)
                DELETE r
            """, {"primary_id": primary_id, "secondary_ids": secondary_ids})

            # Step 5: Move CITIZEN_OF relationships
            session.run("""
                UNWIND $secondary_ids AS sid
                MATCH (s:Person {id: sid})-[r:CITIZEN_OF]->(c:Country)
                MATCH (primary:Person {id: $primary_id})
                WHERE NOT (primary)-[:CITIZEN_OF]->(c)
                MERGE (primary)-[:CITIZEN_OF]->(c)
                DELETE r
            """, {"primary_id": primary_id, "secondary_ids": secondary_ids})

            # Step 6: Move any FAMILY_OF / ASSOCIATED_WITH relationships
            session.run("""
                UNWIND $secondary_ids AS sid
                MATCH (s:Person {id: sid})-[r]->(target)
                WHERE type(r) IN ['FAMILY_OF', 'ASSOCIATED_WITH']
                MATCH (primary:Person {id: $primary_id})
                WITH primary, r, target, type(r) AS rtype
                CALL {
                    WITH primary, target, rtype
                    WITH primary, target, rtype
                    WHERE rtype = 'FAMILY_OF'
                    MERGE (primary)-[:FAMILY_OF]->(target)
                }
                DELETE r
            """, {"primary_id": primary_id, "secondary_ids": secondary_ids})

            # Step 7: Delete remaining relationships and secondary nodes
            session.run("""
                UNWIND $secondary_ids AS sid
                MATCH (s:Person {id: sid})
                DETACH DELETE s
            """, {"secondary_ids": secondary_ids})

            print(f"    Deleted {len(secondary_ids)} duplicate(s)")

        # Summary
        total = session.run("MATCH (p:Person) RETURN count(p) AS count")
        print(f"\nTotal Person nodes after dedup: {total.single()['count']}")

    driver.close()
    print("Done.")


if __name__ == "__main__":
    main()
