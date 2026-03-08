from neo4j import GraphDatabase, Driver
from typing import Optional
import structlog

from africapep.config import settings

log = structlog.get_logger()

# Default batch size for UNWIND operations
_DEFAULT_BATCH_SIZE = 500


class Neo4jClient:
    """Neo4j connection manager with pooling and auto-reconnect."""

    def __init__(self):
        self._driver: Optional[Driver] = None
        try:
            self._connect()
        except Exception as exc:
            log.warning("neo4j_init_deferred", error=str(exc),
                        hint="Will retry on first query")
            self._driver = None

    def _connect(self):
        self._driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
            max_connection_pool_size=50,
        )

    def close(self):
        if self._driver:
            self._driver.close()
            self._driver = None

    def verify_connectivity(self) -> bool:
        try:
            if not self._driver:
                self._connect()
            self._driver.verify_connectivity()
            return True
        except Exception as e:
            log.error("neo4j_connectivity_failed", error=str(e))
            return False

    def _ensure_connected(self):
        """Ensure the driver is initialised, reconnecting if necessary."""
        if self._driver is None:
            self._connect()

    def run(self, query: str, params: dict = None) -> list:
        self._ensure_connected()
        with self._driver.session() as session:
            result = session.run(query, params or {})
            return [dict(r) for r in result]

    def run_write(self, query: str, params: dict = None):
        self._ensure_connected()
        with self._driver.session() as session:
            session.execute_write(lambda tx: tx.run(query, params or {}))

    def apply_constraints(self, cypher_file: str):
        with open(cypher_file) as f:
            statements = [s.strip() for s in f.read().split(";") if s.strip()]
        for stmt in statements:
            try:
                self.run_write(stmt)
                log.info("constraint_applied", stmt=stmt[:80])
            except Exception as e:
                log.warning("constraint_skipped", stmt=stmt[:80], error=str(e))

    # ── Graph write operations ──

    def upsert_person(self, person: dict) -> str:
        """Upsert a Person node within a single managed transaction."""
        self._ensure_connected()
        query = """
        MERGE (p:Person {id: $id})
        SET p.full_name = $full_name,
            p.name_variants = $name_variants,
            p.date_of_birth = $date_of_birth,
            p.nationality = $nationality,
            p.gender = $gender,
            p.pep_tier = $pep_tier,
            p.is_active_pep = $is_active_pep,
            p.updated_at = datetime(),
            p.created_at = coalesce(p.created_at, datetime())
        RETURN p.id AS id
        """

        def _do_upsert(tx, params):
            result = tx.run(query, params)
            record = result.single()
            return record["id"] if record else params["id"]

        with self._driver.session() as session:
            return session.execute_write(_do_upsert, person)

    def upsert_person_batch(self, persons: list[dict],
                            batch_size: int = _DEFAULT_BATCH_SIZE) -> list[str]:
        """Upsert multiple Person nodes using UNWIND for batched writes.

        Sends all rows in a single Cypher statement per batch instead of
        one transaction per person, reducing round-trips from N to
        ceil(N / batch_size).
        """
        self._ensure_connected()
        query = """
        UNWIND $rows AS row
        MERGE (p:Person {id: row.id})
        SET p.full_name = row.full_name,
            p.name_variants = row.name_variants,
            p.date_of_birth = row.date_of_birth,
            p.nationality = row.nationality,
            p.gender = row.gender,
            p.pep_tier = row.pep_tier,
            p.is_active_pep = row.is_active_pep,
            p.updated_at = datetime(),
            p.created_at = coalesce(p.created_at, datetime())
        RETURN p.id AS id
        """
        all_ids: list[str] = []
        for start in range(0, len(persons), batch_size):
            chunk = persons[start:start + batch_size]

            def _do_batch(tx, rows):
                result = tx.run(query, {"rows": rows})
                return [record["id"] for record in result]

            with self._driver.session() as session:
                ids = session.execute_write(_do_batch, chunk)
                all_ids.extend(ids)

        return all_ids

    # ── Generic batch write helpers ──

    def run_write_batch(self, query: str, rows: list[dict],
                        batch_size: int = _DEFAULT_BATCH_SIZE):
        """Execute a Cypher write statement with UNWIND $rows in batches.

        The caller's *query* must reference ``$rows`` (or use ``UNWIND $rows
        AS row``) so that the driver can stream all items in one round-trip
        per chunk.
        """
        self._ensure_connected()
        for start in range(0, len(rows), batch_size):
            chunk = rows[start:start + batch_size]

            def _do(tx, items):
                tx.run(query, {"rows": items})

            with self._driver.session() as session:
                session.execute_write(_do, chunk)

    def batch_upsert_positions(self, positions: list[dict],
                               batch_size: int = _DEFAULT_BATCH_SIZE):
        """Batch-upsert Position nodes using UNWIND."""
        query = """
        UNWIND $rows AS row
        MERGE (pos:Position {id: row.id})
        SET pos.title = row.title,
            pos.institution = row.institution,
            pos.country = row.country,
            pos.branch = row.branch,
            pos.start_date = row.start_date,
            pos.end_date = row.end_date,
            pos.is_current = row.is_current
        """
        self.run_write_batch(query, positions, batch_size)

    def batch_upsert_organisations(self, orgs: list[dict],
                                   batch_size: int = _DEFAULT_BATCH_SIZE):
        """Batch-upsert Organisation nodes using UNWIND."""
        query = """
        UNWIND $rows AS row
        MERGE (o:Organisation {id: row.id})
        SET o.name = row.name,
            o.org_type = row.org_type,
            o.country = row.country,
            o.registration_number = row.registration_number
        """
        self.run_write_batch(query, orgs, batch_size)

    def batch_create_source_records(self, sources: list[dict],
                                    batch_size: int = _DEFAULT_BATCH_SIZE):
        """Batch-create SourceRecord nodes using UNWIND."""
        query = """
        UNWIND $rows AS row
        MERGE (s:SourceRecord {id: row.id})
        SET s.source_url = row.source_url,
            s.source_type = row.source_type,
            s.scraped_at = datetime(row.scraped_at),
            s.raw_text = row.raw_text,
            s.country = row.country
        """
        self.run_write_batch(query, sources, batch_size)

    def batch_link_person_position(self, links: list[dict],
                                   batch_size: int = _DEFAULT_BATCH_SIZE):
        """Batch-create HELD_POSITION relationships using UNWIND."""
        query = """
        UNWIND $rows AS row
        MATCH (p:Person {id: row.pid}), (pos:Position {id: row.posid})
        MERGE (p)-[r:HELD_POSITION]->(pos)
        SET r.start_date = row.start, r.end_date = row.end,
            r.is_current = row.current
        """
        self.run_write_batch(query, links, batch_size)

    def batch_link_position_org(self, links: list[dict],
                                batch_size: int = _DEFAULT_BATCH_SIZE):
        """Batch-create AT_ORGANISATION relationships using UNWIND."""
        query = """
        UNWIND $rows AS row
        MATCH (pos:Position {id: row.posid}), (o:Organisation {id: row.oid})
        MERGE (pos)-[:AT_ORGANISATION]->(o)
        """
        self.run_write_batch(query, links, batch_size)

    def batch_link_person_country(self, links: list[dict],
                                  batch_size: int = _DEFAULT_BATCH_SIZE):
        """Batch-create CITIZEN_OF relationships using UNWIND."""
        query = """
        UNWIND $rows AS row
        MATCH (p:Person {id: row.pid}), (c:Country {code: row.code})
        MERGE (p)-[:CITIZEN_OF]->(c)
        """
        self.run_write_batch(query, links, batch_size)

    def batch_link_person_source(self, links: list[dict],
                                 batch_size: int = _DEFAULT_BATCH_SIZE):
        """Batch-create SOURCED_FROM relationships using UNWIND."""
        query = """
        UNWIND $rows AS row
        MATCH (p:Person {id: row.pid}), (s:SourceRecord {id: row.sid})
        MERGE (p)-[:SOURCED_FROM]->(s)
        """
        self.run_write_batch(query, links, batch_size)

    def batch_link_org_country(self, links: list[dict],
                               batch_size: int = _DEFAULT_BATCH_SIZE):
        """Batch-create BASED_IN relationships using UNWIND."""
        query = """
        UNWIND $rows AS row
        MATCH (o:Organisation {id: row.oid}), (c:Country {code: row.code})
        MERGE (o)-[:BASED_IN]->(c)
        """
        self.run_write_batch(query, links, batch_size)

    def upsert_position(self, position: dict) -> str:
        self._ensure_connected()
        query = """
        MERGE (pos:Position {id: $id})
        SET pos.title = $title,
            pos.institution = $institution,
            pos.country = $country,
            pos.branch = $branch,
            pos.start_date = $start_date,
            pos.end_date = $end_date,
            pos.is_current = $is_current
        RETURN pos.id AS id
        """

        def _do_upsert(tx, params):
            result = tx.run(query, params)
            record = result.single()
            return record["id"] if record else params["id"]

        with self._driver.session() as session:
            return session.execute_write(_do_upsert, position)

    def upsert_organisation(self, org: dict) -> str:
        self._ensure_connected()
        query = """
        MERGE (o:Organisation {id: $id})
        SET o.name = $name,
            o.org_type = $org_type,
            o.country = $country,
            o.registration_number = $registration_number
        RETURN o.id AS id
        """

        def _do_upsert(tx, params):
            result = tx.run(query, params)
            record = result.single()
            return record["id"] if record else params["id"]

        with self._driver.session() as session:
            return session.execute_write(_do_upsert, org)

    def ensure_country(self, code: str, name: str, region: str):
        query = """
        MERGE (c:Country {code: $code})
        SET c.name = $name, c.region = $region
        """
        self.run_write(query, {"code": code, "name": name, "region": region})

    def create_source_record(self, source: dict) -> str:
        self._ensure_connected()
        query = """
        CREATE (s:SourceRecord {
            id: $id, source_url: $source_url,
            source_type: $source_type, scraped_at: datetime($scraped_at),
            raw_text: $raw_text, country: $country
        })
        RETURN s.id AS id
        """

        def _do_create(tx, params):
            result = tx.run(query, params)
            record = result.single()
            return record["id"] if record else params["id"]

        with self._driver.session() as session:
            return session.execute_write(_do_create, source)

    def link_person_position(self, person_id: str, position_id: str,
                             start_date=None, end_date=None, is_current=True):
        query = """
        MATCH (p:Person {id: $pid}), (pos:Position {id: $posid})
        MERGE (p)-[r:HELD_POSITION]->(pos)
        SET r.start_date = $start, r.end_date = $end, r.is_current = $current
        """
        self.run_write(query, {"pid": person_id, "posid": position_id,
                               "start": start_date, "end": end_date,
                               "current": is_current})

    def link_position_org(self, position_id: str, org_id: str):
        query = """
        MATCH (pos:Position {id: $posid}), (o:Organisation {id: $oid})
        MERGE (pos)-[:AT_ORGANISATION]->(o)
        """
        self.run_write(query, {"posid": position_id, "oid": org_id})

    def link_person_country(self, person_id: str, country_code: str):
        query = """
        MATCH (p:Person {id: $pid}), (c:Country {code: $code})
        MERGE (p)-[:CITIZEN_OF]->(c)
        """
        self.run_write(query, {"pid": person_id, "code": country_code})

    def link_person_source(self, person_id: str, source_id: str):
        query = """
        MATCH (p:Person {id: $pid}), (s:SourceRecord {id: $sid})
        MERGE (p)-[:SOURCED_FROM]->(s)
        """
        self.run_write(query, {"pid": person_id, "sid": source_id})

    def link_family(self, person1_id: str, person2_id: str, rel_type: str):
        query = """
        MATCH (p1:Person {id: $pid1}), (p2:Person {id: $pid2})
        MERGE (p1)-[r:FAMILY_OF]->(p2)
        SET r.relationship_type = $rel
        """
        self.run_write(query, {"pid1": person1_id, "pid2": person2_id, "rel": rel_type})

    def link_associate(self, person1_id: str, person2_id: str, rel_type: str):
        query = """
        MATCH (p1:Person {id: $pid1}), (p2:Person {id: $pid2})
        MERGE (p1)-[r:ASSOCIATED_WITH]->(p2)
        SET r.relationship_type = $rel
        """
        self.run_write(query, {"pid1": person1_id, "pid2": person2_id, "rel": rel_type})

    def link_org_country(self, org_id: str, country_code: str):
        query = """
        MATCH (o:Organisation {id: $oid}), (c:Country {code: $code})
        MERGE (o)-[:BASED_IN]->(c)
        """
        self.run_write(query, {"oid": org_id, "code": country_code})

    # ── Graph read operations ──

    def get_person(self, person_id: str) -> dict:
        query = """
        MATCH (p:Person {id: $id})
        OPTIONAL MATCH (p)-[hp:HELD_POSITION]->(pos:Position)
        OPTIONAL MATCH (pos)-[:AT_ORGANISATION]->(org:Organisation)
        OPTIONAL MATCH (p)-[:SOURCED_FROM]->(src:SourceRecord)
        RETURN p, collect(DISTINCT {position: pos, org: org, held: hp}) AS positions,
               collect(DISTINCT src) AS sources
        """
        return self.run(query, {"id": person_id})

    def get_person_graph(self, person_id: str) -> dict:
        query = """
        MATCH (p:Person {id: $id})
        OPTIONAL MATCH (p)-[r1]->(n1)
        OPTIONAL MATCH (p)<-[r2]-(n2)
        OPTIONAL MATCH (p)-[:HELD_POSITION]->(pos)-[r3:AT_ORGANISATION]->(org)
        WITH p, collect(DISTINCT {node: n1, rel: type(r1), dir: 'out'}) +
                collect(DISTINCT {node: n2, rel: type(r2), dir: 'in'}) +
                collect(DISTINCT {node: org, rel: 'AT_ORGANISATION', dir: 'out'}) AS connections
        RETURN p, connections
        """
        return self.run(query, {"id": person_id})

    def search_persons(self, name: str, country: str = None, limit: int = 20) -> list:
        where = "WHERE p.full_name CONTAINS $name"
        if country:
            where += " AND p.nationality = $country"
        query = f"""
        MATCH (p:Person) {where}
        OPTIONAL MATCH (p)-[:HELD_POSITION]->(pos:Position)
        RETURN p, collect(pos) AS positions
        ORDER BY p.full_name LIMIT $limit
        """
        params = {"name": name, "limit": limit}
        if country:
            params["country"] = country
        return self.run(query, params)

    def get_stats(self) -> dict:
        query = """
        MATCH (p:Person) WITH count(p) AS total_persons
        MATCH (p2:Person) WHERE p2.is_active_pep = true WITH total_persons, count(p2) AS active
        MATCH (s:SourceRecord) WITH total_persons, active, count(s) AS sources
        RETURN total_persons, active, sources
        """
        result = self.run(query)
        return result[0] if result else {}

    def end_date_position(self, person_id: str, position_id: str, end_date: str):
        query = """
        MATCH (p:Person {id: $pid})-[r:HELD_POSITION]->(pos:Position {id: $posid})
        SET r.end_date = $end, r.is_current = false
        SET pos.end_date = $end, pos.is_current = false
        """
        self.run_write(query, {"pid": person_id, "posid": position_id, "end": end_date})


try:
    neo4j_client = Neo4jClient()
except Exception as _exc:
    log.warning("neo4j_client_init_failed", error=str(_exc),
                hint="Client created with deferred connection")
    neo4j_client = Neo4jClient.__new__(Neo4jClient)
    neo4j_client._driver = None
