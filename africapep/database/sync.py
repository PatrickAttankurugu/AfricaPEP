"""Sync Neo4j graph data to PostgreSQL search index."""
import json
import uuid
from datetime import datetime, timezone
from sqlalchemy import text
import structlog

from africapep.database.neo4j_client import neo4j_client
from africapep.database.postgres_client import get_db

log = structlog.get_logger()


def sync_all():
    """Pull all Person nodes from Neo4j and upsert into pep_profiles."""
    query = """
    MATCH (p:Person)
    OPTIONAL MATCH (p)-[hp:HELD_POSITION]->(pos:Position)
    WHERE hp.is_current = true
    WITH p, collect({
        title: pos.title,
        institution: pos.institution,
        country: pos.country,
        branch: pos.branch
    }) AS current_positions
    RETURN p.id AS id, p.full_name AS full_name,
           p.name_variants AS name_variants,
           p.date_of_birth AS date_of_birth,
           p.nationality AS nationality,
           p.pep_tier AS pep_tier,
           p.is_active_pep AS is_active_pep,
           current_positions
    """
    persons = neo4j_client.run(query)
    synced = 0

    with get_db() as db:
        for person in persons:
            neo4j_id = person["id"]
            full_name = person["full_name"] or ""
            name_variants = person.get("name_variants") or []
            dob = person.get("date_of_birth")
            nationality = person.get("nationality")
            pep_tier = person.get("pep_tier")
            is_active = person.get("is_active_pep", True)
            positions = person.get("current_positions") or []

            # Filter out empty position dicts
            positions = [p for p in positions if p.get("title")]

            db.execute(text("""
                INSERT INTO pep_profiles
                    (id, neo4j_id, full_name, name_variants, date_of_birth,
                     nationality, pep_tier, is_active_pep, current_positions,
                     country, updated_at)
                VALUES
                    (:id, :neo4j_id, :full_name, :name_variants, :dob,
                     :nationality, :pep_tier, :is_active, CAST(:positions AS jsonb),
                     :country, :updated_at)
                ON CONFLICT (neo4j_id) DO UPDATE SET
                    full_name = EXCLUDED.full_name,
                    name_variants = EXCLUDED.name_variants,
                    date_of_birth = EXCLUDED.date_of_birth,
                    nationality = EXCLUDED.nationality,
                    pep_tier = EXCLUDED.pep_tier,
                    is_active_pep = EXCLUDED.is_active_pep,
                    current_positions = EXCLUDED.current_positions,
                    country = EXCLUDED.country,
                    updated_at = EXCLUDED.updated_at
            """), {
                "id": str(uuid.uuid4()),
                "neo4j_id": neo4j_id,
                "full_name": full_name,
                "name_variants": list(name_variants) if name_variants else [],
                "dob": _parse_date(dob),
                "nationality": nationality,
                "pep_tier": pep_tier,
                "is_active": is_active,
                "positions": json.dumps(positions),
                "country": nationality,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            })
            synced += 1

    # Sync source records
    sources = neo4j_client.run("""
        MATCH (s:SourceRecord) RETURN s.id AS id, s.source_url AS source_url,
        s.source_type AS source_type, s.country AS country,
        s.scraped_at AS scraped_at, s.raw_text AS raw_text
    """)

    with get_db() as db:
        for src in sources:
            db.execute(text("""
                INSERT INTO source_records (id, neo4j_id, source_url, source_type, country, scraped_at, raw_text)
                VALUES (:id, :neo4j_id, :url, :type, :country, :scraped, :text)
                ON CONFLICT DO NOTHING
            """), {
                "id": str(uuid.uuid4()),
                "neo4j_id": src["id"],
                "url": src.get("source_url"),
                "type": src.get("source_type"),
                "country": src.get("country"),
                "scraped": str(src.get("scraped_at")) if src.get("scraped_at") else None,
                "text": src.get("raw_text", "")[:10000],
            })

    log.info("sync_complete", persons_synced=synced, sources_synced=len(sources))
    return synced


def _parse_date(dob):
    """Parse a date value into a string suitable for PostgreSQL DATE column."""
    if not dob:
        return None
    dob_str = str(dob)
    # Try common date formats
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%d/%m/%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(dob_str.split("T")[0].split(" ")[0], fmt).date().isoformat()
        except (ValueError, IndexError):
            continue
    return None
