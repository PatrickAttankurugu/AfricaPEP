"""GET /api/v1/pep/{id} — full PEP profile retrieval."""
import asyncio

from fastapi import APIRouter, HTTPException
import structlog

from africapep.api.schemas import PepProfileResponse, PositionResponse, SourceResponse, tier_to_risk_level
from africapep.database.neo4j_client import neo4j_client

log = structlog.get_logger()
router = APIRouter()


@router.get("/pep/{pep_id}", response_model=PepProfileResponse)
async def get_pep_profile(pep_id: str):
    """Get full PEP profile including all positions, sources, and name variants."""
    results = await asyncio.to_thread(neo4j_client.get_person, pep_id)

    if not results:
        raise HTTPException(status_code=404, detail="PEP not found")

    record = results[0]
    person = record["p"]

    # Build positions list
    positions = []
    for pos_data in record.get("positions", []):
        pos = pos_data.get("position")
        if pos:
            held = pos_data.get("held", {}) or {}
            positions.append(PositionResponse(
                title=pos.get("title", ""),
                institution=pos.get("institution", ""),
                country=pos.get("country", ""),
                branch=pos.get("branch", ""),
                start_date=str(pos.get("start_date")) if pos.get("start_date") else None,
                end_date=str(pos.get("end_date")) if pos.get("end_date") else None,
                is_current=held.get("is_current", pos.get("is_current", True)),
            ))

    # Build sources list
    sources = []
    for src in record.get("sources", []):
        if src:
            sources.append(SourceResponse(
                source_url=src.get("source_url", ""),
                source_type=src.get("source_type", ""),
                country=src.get("country", ""),
                scraped_at=str(src.get("scraped_at")) if src.get("scraped_at") else None,
            ))

    pep_tier = person.get("pep_tier", 2)

    return PepProfileResponse(
        id=person.get("id", pep_id),
        full_name=person.get("full_name", ""),
        aliases=person.get("name_variants", []),
        date_of_birth=str(person.get("date_of_birth")) if person.get("date_of_birth") else None,
        nationality=person.get("nationality", ""),
        gender=person.get("gender", ""),
        pep_tier=pep_tier,
        risk_level=tier_to_risk_level(pep_tier),
        is_active_pep=person.get("is_active_pep", True),
        positions=positions,
        sources=sources,
    )
