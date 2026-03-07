"""GET /api/v1/search — full-text search with filters.
GET /api/v1/stats — database statistics.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Query
from sqlalchemy import text
import structlog

from africapep.api.schemas import (
    SearchResponse, SearchResultItem, PositionResponse, StatsResponse,
)
from africapep.database.postgres_client import get_db

log = structlog.get_logger()
router = APIRouter()


@router.get("/search", response_model=SearchResponse)
def search_peps(
    q: str = Query(..., min_length=1, description="Search query"),
    country: str = Query(None, min_length=2, max_length=2),
    tier: int = Query(None, ge=1, le=3),
    active: bool = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    """Full-text search with filters using PostgreSQL tsvector index."""
    offset = (page - 1) * limit

    # Build the query
    conditions = []
    params = {"limit": limit, "offset": offset}

    # Full-text search using tsvector
    if q:
        # Use plainto_tsquery for simple queries, websearch_to_tsquery for complex
        conditions.append(
            "(search_vector @@ plainto_tsquery('english', :query) "
            "OR full_name ILIKE :like_query "
            "OR :query = ANY(name_variants))"
        )
        params["query"] = q
        params["like_query"] = f"%{q}%"

    if country:
        conditions.append("(nationality = :country OR country = :country)")
        params["country"] = country.upper()

    if tier is not None:
        conditions.append("pep_tier = :tier")
        params["tier"] = tier

    if active is not None:
        conditions.append("is_active_pep = :active")
        params["active"] = active

    where_clause = " AND ".join(conditions) if conditions else "TRUE"

    # Count total
    count_sql = f"SELECT COUNT(*) FROM pep_profiles WHERE {where_clause}"
    # Fetch results
    fetch_sql = f"""
        SELECT id, neo4j_id, full_name, name_variants, pep_tier,
               is_active_pep, nationality, current_positions
        FROM pep_profiles
        WHERE {where_clause}
        ORDER BY pep_tier ASC, full_name ASC
        LIMIT :limit OFFSET :offset
    """

    with get_db() as db:
        total = db.execute(text(count_sql), params).scalar() or 0

        rows = db.execute(text(fetch_sql), params).fetchall()
        results = []
        for row in rows:
            positions = []
            if row.current_positions and isinstance(row.current_positions, list):
                for pos in row.current_positions:
                    positions.append(PositionResponse(
                        title=pos.get("title", ""),
                        institution=pos.get("institution", ""),
                        country=pos.get("country", ""),
                        branch=pos.get("branch", ""),
                        is_current=True,
                    ))

            results.append(SearchResultItem(
                id=str(row.neo4j_id or row.id),
                full_name=row.full_name,
                pep_tier=row.pep_tier or 2,
                is_active=row.is_active_pep if row.is_active_pep is not None else True,
                nationality=row.nationality or "",
                positions=positions,
            ))

    return SearchResponse(
        query=q,
        total=total,
        page=page,
        limit=limit,
        results=results,
    )


@router.get("/stats", response_model=StatsResponse)
def get_stats():
    """Database statistics: total PEPs, by country, by tier, sources count."""
    with get_db() as db:
        total = db.execute(text("SELECT COUNT(*) FROM pep_profiles")).scalar() or 0
        active = db.execute(text(
            "SELECT COUNT(*) FROM pep_profiles WHERE is_active_pep = true"
        )).scalar() or 0
        sources = db.execute(text("SELECT COUNT(*) FROM source_records")).scalar() or 0

        # By country
        country_rows = db.execute(text(
            "SELECT COALESCE(nationality, 'XX') AS c, COUNT(*) AS n "
            "FROM pep_profiles GROUP BY nationality ORDER BY n DESC"
        )).fetchall()
        by_country = {row.c: row.n for row in country_rows}

        # By tier
        tier_rows = db.execute(text(
            "SELECT COALESCE(pep_tier, 0) AS t, COUNT(*) AS n "
            "FROM pep_profiles GROUP BY pep_tier ORDER BY t"
        )).fetchall()
        by_tier = {f"tier_{row.t}": row.n for row in tier_rows}

        # Last updated
        last = db.execute(text(
            "SELECT MAX(updated_at) FROM pep_profiles"
        )).scalar()

    return StatsResponse(
        total_peps=total,
        by_country=by_country,
        by_tier=by_tier,
        last_updated=last.isoformat() if last else None,
        sources_count=sources,
        active_peps=active,
    )
