"""Entity Resolution: deduplicate persons across multiple scraper sources.

Algorithm:
1. BLOCKING: Group by country + first letter of surname
2. SCORING: Composite score from name similarity, DOB match, position match
3. DECISION: Auto-merge >= 0.85, review 0.70-0.84, separate < 0.70
4. MERGING: Preserve all source records, merge name variants
"""
import uuid
from datetime import datetime, timezone
from typing import Optional
from dataclasses import dataclass, field

from rapidfuzz import fuzz
import structlog

from typing import TYPE_CHECKING

from africapep.pipeline.normaliser import NormalisedRecord

if TYPE_CHECKING:
    from africapep.database.neo4j_client import Neo4jClient

log = structlog.get_logger()

MERGE_THRESHOLD = 0.85
REVIEW_THRESHOLD = 0.70

# Scoring weights
NAME_WEIGHT = 0.5
DOB_WEIGHT = 0.3
POSITION_WEIGHT = 0.2


@dataclass
class ResolvedEntity:
    """A deduplicated person entity with all merged data."""
    id: str
    full_name: str
    name_variants: list[str]
    date_of_birth: Optional[str]
    nationality: str
    gender: str
    pep_tier: int
    is_active_pep: bool
    positions: list[dict]
    sources: list[dict]
    extra_fields: dict = field(default_factory=dict)


@dataclass
class PotentialDuplicate:
    """Two entities flagged for manual review."""
    entity_a_id: str
    entity_b_id: str
    score: float
    reason: str


class EntityResolver:
    """Deduplicate person records across scraper sources."""

    def __init__(self):
        self.entities: dict[str, ResolvedEntity] = {}
        self.duplicates: list[PotentialDuplicate] = []
        self._blocks: dict[str, list[str]] = {}  # block_key -> [entity_ids]

    def _block_key(self, record: NormalisedRecord) -> str:
        """Generate blocking key: country + first letter of surname."""
        parts = record.full_name.split()
        surname_initial = parts[-1][0].upper() if parts else "X"
        return f"{record.country_code}:{surname_initial}"

    def add(self, record: NormalisedRecord, pep_tier: int) -> str:
        """Add a normalised record, resolving against existing entities.

        Returns the entity ID (existing or new).
        """
        block = self._block_key(record)

        # Find best match within the same block
        best_match_id = None
        best_score = 0.0

        for existing_id in self._blocks.get(block, []):
            existing = self.entities[existing_id]
            score = self._compute_score(record, existing)

            if score > best_score:
                best_score = score
                best_match_id = existing_id

        source_record = {
            "source_url": record.source_url,
            "source_type": record.source_type,
            "raw_text": record.raw_text[:5000],
            "scraped_at": record.scraped_at.isoformat() if hasattr(record.scraped_at, 'isoformat') else str(record.scraped_at),
            "country": record.country_code,
        }

        position = {
            "title": record.title,
            "institution": record.institution,
            "branch": record.branch,
            "country": record.country_code,
            "is_current": True,
        }

        if best_score >= MERGE_THRESHOLD and best_match_id:
            # Auto-merge
            self._merge_into(best_match_id, record, pep_tier, source_record, position)
            log.info("entity_merged", entity_id=best_match_id,
                     name=record.full_name, score=round(best_score, 3))
            return best_match_id

        elif best_score >= REVIEW_THRESHOLD and best_match_id:
            # Flag for review, but still create new entity
            self.duplicates.append(PotentialDuplicate(
                entity_a_id=best_match_id,
                entity_b_id="",  # will be filled below
                score=best_score,
                reason=f"Name match: {record.full_name} vs {self.entities[best_match_id].full_name}",
            ))
            log.info("entity_potential_duplicate", name=record.full_name,
                     existing=self.entities[best_match_id].full_name,
                     score=round(best_score, 3))

        # Create new entity
        entity_id = str(uuid.uuid4())
        entity = ResolvedEntity(
            id=entity_id,
            full_name=record.full_name,
            name_variants=record.name_variants,
            date_of_birth=str(record.date_of_birth) if record.date_of_birth else None,
            nationality=record.country_code,
            gender="",
            pep_tier=pep_tier,
            is_active_pep=True,
            positions=[position] if record.title else [],
            sources=[source_record],
            extra_fields=record.extra_fields,
        )
        self.entities[entity_id] = entity

        # Update review duplicate with new entity ID
        if self.duplicates and not self.duplicates[-1].entity_b_id:
            self.duplicates[-1].entity_b_id = entity_id

        # Add to block index
        if block not in self._blocks:
            self._blocks[block] = []
        self._blocks[block].append(entity_id)

        return entity_id

    def _compute_score(self, record: NormalisedRecord, existing: ResolvedEntity) -> float:
        """Compute composite similarity score between record and existing entity."""
        # 1. Name similarity (weight: 0.5)
        name_scores = []
        for variant in [record.full_name] + record.name_variants:
            for existing_variant in [existing.full_name] + existing.name_variants:
                score = fuzz.token_sort_ratio(variant, existing_variant) / 100.0
                name_scores.append(score)
        name_score = max(name_scores) if name_scores else 0.0

        # 2. DOB match (weight: 0.3)
        dob_score = 0.0
        if record.date_of_birth and existing.date_of_birth:
            rec_dob = str(record.date_of_birth)
            ext_dob = existing.date_of_birth
            if rec_dob == ext_dob:
                dob_score = 1.0
            elif rec_dob[:4] == ext_dob[:4]:  # Same year
                dob_score = 0.5
        # If either DOB missing, neutral (don't penalise)
        elif not record.date_of_birth or not existing.date_of_birth:
            dob_score = 0.0

        # 3. Position/institution match (weight: 0.2)
        pos_score = 0.0
        if record.title and existing.positions:
            for pos in existing.positions:
                title_sim = fuzz.token_sort_ratio(
                    record.title, pos.get("title", "")
                ) / 100.0
                inst_sim = fuzz.token_sort_ratio(
                    record.institution, pos.get("institution", "")
                ) / 100.0
                combined = max(title_sim, inst_sim)
                if combined > pos_score:
                    pos_score = combined

        # Compute weighted composite
        # If DOB is missing, redistribute weight to name
        if not record.date_of_birth or not existing.date_of_birth:
            composite = name_score * 0.7 + pos_score * 0.3
        else:
            composite = (name_score * NAME_WEIGHT +
                         dob_score * DOB_WEIGHT +
                         pos_score * POSITION_WEIGHT)

        return composite

    def _merge_into(self, entity_id: str, record: NormalisedRecord,
                    pep_tier: int, source: dict, position: dict):
        """Merge new record data into existing entity."""
        entity = self.entities[entity_id]

        # Add new name variants
        for variant in record.name_variants:
            if variant not in entity.name_variants:
                entity.name_variants.append(variant)
        if record.full_name not in entity.name_variants:
            entity.name_variants.append(record.full_name)

        # Keep most complete DOB
        if record.date_of_birth and not entity.date_of_birth:
            entity.date_of_birth = str(record.date_of_birth)

        # Keep highest (most restrictive) PEP tier
        if pep_tier < entity.pep_tier:
            entity.pep_tier = pep_tier

        # Add position if not duplicate
        if position.get("title"):
            is_dup = any(
                fuzz.ratio(position["title"], p.get("title", "")) > 90
                for p in entity.positions
            )
            if not is_dup:
                entity.positions.append(position)

        # Always add source record
        entity.sources.append(source)

        # Merge extra_fields
        entity.extra_fields.update(record.extra_fields)

    def flush_to_neo4j(self, client: "Neo4jClient") -> int:
        """Write all resolved entities to Neo4j graph database."""
        written = 0

        for entity in self.entities.values():
            try:
                # Create Person node
                client.upsert_person({
                    "id": entity.id,
                    "full_name": entity.full_name,
                    "name_variants": entity.name_variants,
                    "date_of_birth": entity.date_of_birth,
                    "nationality": entity.nationality,
                    "gender": entity.gender,
                    "pep_tier": entity.pep_tier,
                    "is_active_pep": entity.is_active_pep,
                })

                # Link to country
                client.link_person_country(entity.id, entity.nationality)

                # Create positions and link
                for pos in entity.positions:
                    pos_id = str(uuid.uuid4())
                    client.upsert_position({
                        "id": pos_id,
                        "title": pos.get("title", ""),
                        "institution": pos.get("institution", ""),
                        "country": pos.get("country", entity.nationality),
                        "branch": pos.get("branch", "EXECUTIVE"),
                        "start_date": pos.get("start_date"),
                        "end_date": pos.get("end_date"),
                        "is_current": pos.get("is_current", True),
                    })
                    client.link_person_position(entity.id, pos_id)

                    # Create org and link
                    if pos.get("institution"):
                        org_id = str(uuid.uuid4())
                        client.upsert_organisation({
                            "id": org_id,
                            "name": pos["institution"],
                            "org_type": _infer_org_type(pos["institution"]),
                            "country": pos.get("country", entity.nationality),
                            "registration_number": "",
                        })
                        client.link_position_org(pos_id, org_id)
                        client.link_org_country(org_id, pos.get("country", entity.nationality))

                # Create source records and link
                for src in entity.sources:
                    src_id = str(uuid.uuid4())
                    client.create_source_record({
                        "id": src_id,
                        "source_url": src.get("source_url", ""),
                        "source_type": src.get("source_type", ""),
                        "scraped_at": src.get("scraped_at", datetime.now(timezone.utc).isoformat()),
                        "raw_text": src.get("raw_text", "")[:5000],
                        "country": src.get("country", entity.nationality),
                    })
                    client.link_person_source(entity.id, src_id)

                written += 1
            except Exception as e:
                log.error("entity_write_failed", entity_id=entity.id,
                          name=entity.full_name, error=str(e))

        log.info("resolver_flush_complete", entities=written,
                 duplicates=len(self.duplicates))
        return written

    def get_stats(self) -> dict:
        """Return resolver statistics."""
        return {
            "total_entities": len(self.entities),
            "potential_duplicates": len(self.duplicates),
            "blocks": len(self._blocks),
        }


def _infer_org_type(institution: str) -> str:
    """Infer organisation type from name."""
    inst_lower = institution.lower()
    if any(w in inst_lower for w in ["parliament", "assembly", "senate", "house of"]):
        return "PARLIAMENT"
    if any(w in inst_lower for w in ["court", "judiciary", "tribunal"]):
        return "GOVT"
    if any(w in inst_lower for w in ["party", "congress", "democratic"]):
        return "PARTY"
    if any(w in inst_lower for w in ["military", "army", "navy", "air force", "defence", "defense"]):
        return "MILITARY"
    if any(w in inst_lower for w in ["corporation", "authority", "board", "company", "limited"]):
        return "SOE"
    return "GOVT"
