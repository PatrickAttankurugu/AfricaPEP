"""Integration tests for API endpoints using FastAPI TestClient.

These tests require database connections.
Run with: pytest tests/test_api_integration.py -v -m integration
"""
import sys
import pytest
from unittest.mock import patch, MagicMock

pytestmark = pytest.mark.integration


@pytest.fixture
def client():
    """Create a TestClient with mocked database connections."""
    mock_neo4j = MagicMock()
    mock_neo4j.verify_connectivity.return_value = True
    mock_neo4j.get_stats.return_value = {
        "total_persons": 100, "active": 80, "sources": 50
    }

    mock_db = MagicMock()
    mock_db.__enter__ = MagicMock(return_value=mock_db)
    mock_db.__exit__ = MagicMock(return_value=False)

    # Pre-populate the module in sys.modules with our mock before importing the app
    mock_neo4j_module = MagicMock()
    mock_neo4j_module.Neo4jClient = MagicMock(return_value=mock_neo4j)
    mock_neo4j_module.neo4j_client = mock_neo4j

    with patch.dict(sys.modules, {"africapep.database.neo4j_client": mock_neo4j_module}):
        with patch("africapep.database.postgres_client.get_db", return_value=mock_db):
            from fastapi.testclient import TestClient
            from africapep.api.main import app
            yield TestClient(app)


class TestHealthEndpoint:
    def test_health_returns_200(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data
        assert "neo4j" in data
        assert "postgres" in data
        assert "version" in data


class TestRootEndpoint:
    def test_root_returns_service_info(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["service"] == "AfricaPEP API"
        assert "version" in data


class TestScreenEndpoint:
    def test_screen_requires_name(self, client):
        resp = client.post("/api/v1/screen", json={})
        assert resp.status_code == 400

    def test_screen_rejects_short_name(self, client):
        resp = client.post("/api/v1/screen", json={"name": "A"})
        assert resp.status_code == 400
        data = resp.json()
        assert "code" in data

    def test_screen_rejects_invalid_threshold(self, client):
        resp = client.post("/api/v1/screen", json={"name": "Test Name", "threshold": 2.0})
        assert resp.status_code == 400


class TestBatchScreenEndpoint:
    def test_batch_rejects_empty_names(self, client):
        resp = client.post("/api/v1/screen/batch", json={"names": []})
        assert resp.status_code == 400

    def test_batch_rejects_too_many_names(self, client):
        names = [{"name": f"Person {i}"} for i in range(51)]
        resp = client.post("/api/v1/screen/batch", json={"names": names})
        assert resp.status_code == 400


class TestSearchEndpoint:
    def test_search_requires_query(self, client):
        resp = client.get("/api/v1/search")
        assert resp.status_code == 400

    def test_search_rejects_invalid_tier(self, client):
        resp = client.get("/api/v1/search?q=test&tier=5")
        assert resp.status_code == 400


class TestSchemaValidation:
    def test_batch_screening_request_schema(self):
        from africapep.api.schemas import BatchScreeningRequest, BatchNameEntry

        req = BatchScreeningRequest(
            names=[BatchNameEntry(name="Bola Tinubu", country="NG")],
            threshold=0.65,
        )
        assert len(req.names) == 1
        assert req.threshold == 0.65

    def test_error_response_schema(self):
        from africapep.api.schemas import ErrorResponse

        err = ErrorResponse(detail="Test error", code="TEST_ERROR")
        assert err.detail == "Test error"
        assert err.code == "TEST_ERROR"
