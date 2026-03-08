"""GET /health — system health check."""
import asyncio

from fastapi import APIRouter

from africapep.api.schemas import HealthResponse
from africapep.database.neo4j_client import neo4j_client
from africapep.database.postgres_client import verify_connectivity as pg_verify

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    neo4j_ok, pg_ok = await asyncio.gather(
        asyncio.to_thread(neo4j_client.verify_connectivity),
        asyncio.to_thread(pg_verify),
    )

    neo4j_status = "connected" if neo4j_ok else "disconnected"
    pg_status = "connected" if pg_ok else "disconnected"

    overall = "healthy" if neo4j_status == "connected" and pg_status == "connected" else "degraded"

    return HealthResponse(
        status=overall,
        neo4j=neo4j_status,
        postgres=pg_status,
        version="1.0.0",
    )
