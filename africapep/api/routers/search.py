"""GET /api/v1/search — full-text search with filters.
GET /api/v1/stats — database statistics.
"""

import asyncio
import time as _time

from fastapi import APIRouter, Query, HTTPException, Response
from sqlalchemy import text
from sqlalchemy.exc import OperationalError, InterfaceError
import structlog

from africapep.api.schemas import (
    SearchResponse, SearchResultItem, PositionResponse, StatsResponse,
    tier_to_risk_level,
)
from africapep.database.postgres_client import get_db

log = structlog.get_logger()
router = APIRouter()

# ── Simple in-memory TTL cache ──
_STATS_CACHE_TTL = 300  # 5 minutes
_stats_cache: dict = {"data": None, "expires_at": 0.0}


def _run_search(where_clause: str, count_sql: str, fetch_sql: str, params: dict):
    """Execute search queries synchronously (called via to_thread)."""
    with get_db() as db:
        total = db.execute(text(count_sql), params).scalar() or 0
        rows = db.execute(text(fetch_sql), params).fetchall()
    return total, rows


@router.get("/search", response_model=SearchResponse)
async def search_peps(
    response: Response,
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
        # Escape LIKE wildcards to prevent pattern injection
        escaped_q = q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        params["like_query"] = f"%{escaped_q}%"

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

    try:
        total, rows = await asyncio.to_thread(
            _run_search, where_clause, count_sql, fetch_sql, params
        )
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

            pep_tier = row.pep_tier or 2
            results.append(SearchResultItem(
                id=str(row.neo4j_id or row.id),
                full_name=row.full_name,
                pep_tier=pep_tier,
                risk_level=tier_to_risk_level(pep_tier),
                is_active=row.is_active_pep if row.is_active_pep is not None else True,
                nationality=row.nationality or "",
                positions=positions,
            ))
    except (OperationalError, InterfaceError) as e:
        log.error("search_db_unavailable", query=q, error=str(e))
        raise HTTPException(
            status_code=503,
            detail="Database is temporarily unavailable. Please try again later.",
        )

    # Add pagination headers (RFC 8288)
    response.headers["X-Total-Count"] = str(total)
    response.headers["X-Page"] = str(page)
    response.headers["X-Per-Page"] = str(limit)

    # Build Link header
    total_pages = (total + limit - 1) // limit  # Ceiling division
    base_url = "/api/v1/search"
    query_params = f"?q={q}"
    if country:
        query_params += f"&country={country}"
    if tier is not None:
        query_params += f"&tier={tier}"
    if active is not None:
        query_params += f"&active={active}"

    links = []
    # First page
    links.append(f'<{base_url}{query_params}&page=1&limit={limit}>; rel="first"')
    # Last page
    links.append(f'<{base_url}{query_params}&page={total_pages}&limit={limit}>; rel="last"')
    # Next page
    if page < total_pages:
        links.append(f'<{base_url}{query_params}&page={page + 1}&limit={limit}>; rel="next"')
    # Previous page
    if page > 1:
        links.append(f'<{base_url}{query_params}&page={page - 1}&limit={limit}>; rel="prev"')

    response.headers["Link"] = ", ".join(links)

    return SearchResponse(
        query=q,
        total=total,
        page=page,
        limit=limit,
        results=results,
    )


def _run_stats():
    """Execute stats queries synchronously (called via to_thread)."""
    with get_db() as db:
        total = db.execute(text("SELECT COUNT(*) FROM pep_profiles")).scalar() or 0
        active = db.execute(text(
            "SELECT COUNT(*) FROM pep_profiles WHERE is_active_pep = true"
        )).scalar() or 0
        sources = db.execute(text("SELECT COUNT(*) FROM source_records")).scalar() or 0

        country_rows = db.execute(text(
            "SELECT COALESCE(nationality, 'XX') AS c, COUNT(*) AS n "
            "FROM pep_profiles GROUP BY nationality ORDER BY n DESC"
        )).fetchall()
        by_country = {row[0]: row[1] for row in country_rows}

        tier_rows = db.execute(text(
            "SELECT COALESCE(pep_tier, 0) AS t, COUNT(*) AS n "
            "FROM pep_profiles GROUP BY pep_tier ORDER BY t"
        )).fetchall()
        by_tier = {}
        for row in tier_rows:
            t = row[0]
            nn = row[1]
            key = f"tier_{t}" if t else "unclassified"
            by_tier[key] = nn

        last = db.execute(text(
            "SELECT MAX(updated_at) FROM pep_profiles"
        )).scalar()

    return total, active, sources, by_country, by_tier, last


@router.get("/stats", response_model=StatsResponse)
async def get_stats():
    """Database statistics: total PEPs, by country, by tier, sources count.

    Results are cached in-memory for 5 minutes to avoid repeated heavy queries.
    """
    now = _time.monotonic()
    if _stats_cache["data"] is not None and now < _stats_cache["expires_at"]:
        return _stats_cache["data"]

    try:
        total, active, sources, by_country, by_tier, last = await asyncio.to_thread(
            _run_stats
        )
    except (OperationalError, InterfaceError) as e:
        log.error("stats_db_unavailable", error=str(e))
        raise HTTPException(
            status_code=503,
            detail="Database is temporarily unavailable. Please try again later.",
        )

    result = StatsResponse(
        total_peps=total,
        by_country=by_country,
        by_tier=by_tier,
        last_updated=last.isoformat() if last else None,
        sources_count=sources,
        active_peps=active,
    )

    _stats_cache["data"] = result
    _stats_cache["expires_at"] = now + _STATS_CACHE_TTL

    return result
