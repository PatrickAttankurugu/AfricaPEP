"""Build PEP -> family/associate/org relationship edges from extracted data."""
from typing import Optional

import structlog
from rapidfuzz import fuzz

from africapep.pipeline.extractor import extract_entities
from africapep.database.neo4j_client import Neo4jClient

log = structlog.get_logger()


def build_relationships_from_text(text: str, person_id: str,
                                  client: Neo4jClient,
                                  known_persons: dict[str, str] = None):
    """Extract relationship signals from text and create graph edges.

    Args:
        text: Raw text containing relationship signals
        person_id: Neo4j ID of the source person
        client: Neo4j client
        known_persons: dict mapping name -> person_id for existing persons
    """
    if not text:
        return

    known_persons = known_persons or {}
    entities = extract_entities(text)

    for rel in entities.relationships:
        related_name = rel["related_person"]
        rel_type = rel["relationship_type"]

        # Try to find the related person in known persons
        matched_id = _find_person(related_name, known_persons)

        if matched_id:
            if rel_type in ("SPOUSE", "CHILD", "SIBLING", "PARENT"):
                client.link_family(person_id, matched_id, rel_type)
                log.info("relationship_created", type="FAMILY",
                         subtype=rel_type, person=person_id, related=matched_id)
            else:
                client.link_associate(person_id, matched_id, rel_type)
                log.info("relationship_created", type="ASSOCIATE",
                         subtype=rel_type, person=person_id, related=matched_id)
        else:
            log.debug("relationship_person_not_found",
                      related_name=related_name, rel_type=rel_type)


def _find_person(name: str, known_persons: dict[str, str],
                 threshold: float = 0.80) -> Optional[str]:
    """Find a person ID by fuzzy name matching."""
    best_match = None
    best_score = 0.0

    for known_name, known_id in known_persons.items():
        score = fuzz.token_sort_ratio(name, known_name) / 100.0
        if score > best_score and score >= threshold:
            best_score = score
            best_match = known_id

    return best_match


def detect_relationships_batch(texts: list[tuple[str, str]],
                               client: Neo4jClient,
                               known_persons: dict[str, str] = None):
    """Process multiple (person_id, text) pairs for relationship extraction."""
    known_persons = known_persons or {}
    total = 0

    for person_id, text in texts:
        build_relationships_from_text(text, person_id, client, known_persons)
        total += 1

    log.info("batch_relationships_processed", total=total)
