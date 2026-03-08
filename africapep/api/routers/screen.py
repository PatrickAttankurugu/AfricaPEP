"""POST /api/v1/screen — fuzzy name screening against PEP database.
POST /api/v1/screen/batch — batch screening for multiple names.
"""
import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import OperationalError, InterfaceError
from rapidfuzz import fuzz
import structlog

from africapep.api.schemas import (
    ScreeningRequest, ScreeningResponse, MatchResult,
    PositionResponse, SourceResponse, MatchExplanation,
    BatchScreeningRequest, BatchScreeningResponse, BatchScreeningResultItem,
    tier_to_risk_level,
)
from africapep.database.postgres_client import get_db

log = structlog.get_logger()
router = APIRouter()


@router.post("/screen", response_model=ScreeningResponse)
def screen_name(request: ScreeningRequest, req: Request):
    """Screen a name against the PEP database using fuzzy matching.

    Uses PostgreSQL pg_trgm similarity for initial candidate retrieval,
    then re-ranks results with rapidfuzz token_sort_ratio.

    Rate limit: 60 requests per minute.
    """
    if not request.name or not request.name.strip():
        return JSONResponse(
            status_code=400,
            content={"detail": "Name field cannot be empty or whitespace.", "code": "INVALID_INPUT"},
        )

    screening_id = str(uuid.uuid4())
    screened_at = datetime.now(timezone.utc).isoformat()

    try:
        matches = _find_matches(request.name, request.country, request.threshold)
    except (OperationalError, InterfaceError) as e:
        log.error("screening_db_unavailable", query=request.name, error=str(e))
        raise HTTPException(
            status_code=503,
            detail="Database is temporarily unavailable. Please try again later.",
        )
    except Exception as e:
        log.error("screening_failed", query=request.name, error=str(e))
        raise HTTPException(status_code=500, detail="Screening failed")

    # Log the screening (non-critical, don't fail if this errors)
    _log_screening(screening_id, request.name, matches)

    return ScreeningResponse(
        query=request.name,
        threshold=request.threshold,
        total_matches=len(matches),
        matches=matches,
        screening_id=screening_id,
        screened_at=screened_at,
    )


@router.post("/screen/batch", response_model=BatchScreeningResponse)
def screen_batch(request: BatchScreeningRequest, req: Request):
    """Screen multiple names against the PEP database in a single request.

    Accepts up to 50 names per batch. Returns an array of screening results.

    Rate limit: 20 requests per minute.
    """
    if len(request.names) > 50:
        return JSONResponse(
            status_code=400,
            content={
                "detail": "Maximum 50 names per batch request.",
                "code": "BATCH_SIZE_EXCEEDED",
            },
        )

    results = []
    total_matches = 0

    for entry in request.names:
        screening_id = str(uuid.uuid4())
        screened_at = datetime.now(timezone.utc).isoformat()

        try:
            matches = _find_matches(entry.name, entry.country, request.threshold)
        except (OperationalError, InterfaceError) as e:
            log.error("batch_screening_db_unavailable", query=entry.name, error=str(e))
            raise HTTPException(
                status_code=503,
                detail="Database is temporarily unavailable. Please try again later.",
            )
        except Exception as e:
            log.error("batch_screening_failed", query=entry.name, error=str(e))
            # For batch, include an empty result rather than failing entirely
            matches = []

        total_matches += len(matches)

        # Log each screening (non-critical)
        _log_screening(screening_id, entry.name, matches)

        results.append(BatchScreeningResultItem(
            query_name=entry.name,
            match_count=len(matches),
            matches=matches,
        ))

    batch_screening_id = str(uuid.uuid4())
    batch_screened_at = datetime.now(timezone.utc).isoformat()

    return BatchScreeningResponse(
        results=results,
        total_queries=len(request.names),
        total_matches=total_matches,
        screening_id=batch_screening_id,
        screened_at=batch_screened_at,
        threshold=request.threshold,
    )


def _find_matches(query_name: str, country: str = None,
                  threshold: float = 0.75) -> list[MatchResult]:
    """Query PostgreSQL for candidate matches, then re-rank with rapidfuzz."""

    # Build SQL query using pg_trgm similarity
    sql = """
        SELECT id, neo4j_id, full_name, name_variants, date_of_birth,
               nationality, pep_tier, is_active_pep, current_positions,
               first_seen, last_seen,
               similarity(full_name, :query) AS trgm_score
        FROM pep_profiles
        WHERE similarity(full_name, :query) > :min_sim
    """
    params = {"query": query_name, "min_sim": max(0.1, threshold - 0.3)}

    if country:
        sql += " AND (nationality = :country OR country = :country)"
        params["country"] = country.upper()

    sql += " ORDER BY trgm_score DESC LIMIT 50"

    matches = []

    with get_db() as db:
        result = db.execute(text(sql), params)
        rows = result.fetchall()

        for row in rows:
            # Re-rank using rapidfuzz
            primary_score = fuzz.token_sort_ratio(query_name, row.full_name) / 100.0
            name_scores = [primary_score]
            matched_variant = None

            # Also check against name variants
            aliases = []
            if row.name_variants:
                for variant in row.name_variants:
                    aliases.append(variant)
                    score = fuzz.token_sort_ratio(query_name, variant) / 100.0
                    if score > primary_score:
                        name_scores.append(score)
                        matched_variant = variant

            best_score = max(name_scores)

            if best_score < threshold:
                continue

            pep_tier = row.pep_tier or 2
            is_active = row.is_active_pep if row.is_active_pep is not None else True

            # Parse positions from JSONB
            positions = []
            if row.current_positions:
                for pos in (row.current_positions if isinstance(row.current_positions, list) else []):
                    positions.append(PositionResponse(
                        title=pos.get("title", ""),
                        institution=pos.get("institution", ""),
                        country=pos.get("country", ""),
                        branch=pos.get("branch", ""),
                        is_current=True,
                    ))

            # Build match explanation
            explanation = MatchExplanation(
                name_similarity=round(primary_score, 4),
                best_variant_score=round(best_score, 4),
                method="rapidfuzz_token_sort",
                matched_variant=matched_variant,
            )

            # Format dates
            dob = str(row.date_of_birth) if row.date_of_birth else None
            first_seen = row.first_seen.isoformat() if hasattr(row, 'first_seen') and row.first_seen else None
            last_seen = row.last_seen.isoformat() if hasattr(row, 'last_seen') and row.last_seen else None

            matches.append(MatchResult(
                pep_id=str(row.neo4j_id or row.id),
                matched_name=row.full_name,
                match_score=round(best_score, 4),
                match=best_score >= threshold,
                pep_tier=pep_tier,
                risk_level=tier_to_risk_level(pep_tier),
                is_active=is_active,
                nationality=row.nationality or "",
                date_of_birth=dob,
                aliases=aliases,
                positions=positions,
                sources=[],
                datasets=["africapep-wikidata"],
                first_seen=first_seen,
                last_seen=last_seen,
                explanation=explanation,
            ))

    # Sort by score descending
    matches.sort(key=lambda m: m.match_score, reverse=True)
    return matches[:20]


def _log_screening(screening_id: str, query_name: str, matches: list[MatchResult]):
    """Log screening query and results to screening_log table."""
    try:
        with get_db() as db:
            db.execute(text("""
                INSERT INTO screening_log (id, query_name, query_date, match_count, top_match_score, results)
                VALUES (:id, :name, NOW(), :count, :top_score, CAST(:results AS jsonb))
            """), {
                "id": screening_id,
                "name": query_name,
                "count": len(matches),
                "top_score": matches[0].match_score if matches else 0.0,
                "results": json.dumps([m.model_dump() for m in matches[:5]], default=str),
            })
    except Exception as e:
        log.error("screening_log_failed", error=str(e))
