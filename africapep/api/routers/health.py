"""GET /health — system health check."""
from fastapi import APIRouter

from africapep.api.schemas import HealthResponse
from africapep.database.neo4j_client import neo4j_client
from africapep.database.postgres_client import verify_connectivity as pg_verify

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health_check():
    neo4j_status = "connected" if neo4j_client.verify_connectivity() else "disconnected"
    pg_status = "connected" if pg_verify() else "disconnected"

    overall = "healthy" if neo4j_status == "connected" and pg_status == "connected" else "degraded"

    return HealthResponse(
        status=overall,
        neo4j=neo4j_status,
        postgres=pg_status,
        version="1.0.0",
    )
