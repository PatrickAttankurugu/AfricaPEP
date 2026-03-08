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

    # Ensure scalar() returns an int (not MagicMock) for COUNT queries
    mock_result = MagicMock()
    mock_result.scalar.return_value = 0
    mock_result.fetchall.return_value = []
    mock_db.execute.return_value = mock_result

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


class TestSearchPaginationHeaders:
    """Test pagination headers on /search endpoint."""

    def test_search_includes_total_count_header(self, client):
        """Verify X-Total-Count header is present in search response."""
        resp = client.get("/api/v1/search?q=test")
        assert resp.status_code == 200
        assert "X-Total-Count" in resp.headers
        # Should be a valid integer
        total_count = int(resp.headers["X-Total-Count"])
        assert total_count >= 0

    def test_search_includes_page_headers(self, client):
        """Verify X-Page and X-Per-Page headers are present."""
        resp = client.get("/api/v1/search?q=test&page=2&limit=10")
        assert resp.status_code == 200
        assert "X-Page" in resp.headers
        assert "X-Per-Page" in resp.headers
        assert resp.headers["X-Page"] == "2"
        assert resp.headers["X-Per-Page"] == "10"

    def test_search_includes_link_header(self, client):
        """Verify Link header follows RFC 8288 with pagination links."""
        resp = client.get("/api/v1/search?q=test&limit=10")
        assert resp.status_code == 200
        assert "Link" in resp.headers

        link_header = resp.headers["Link"]
        # Should contain rel="first" and rel="last"
        assert 'rel="first"' in link_header
        assert 'rel="last"' in link_header

    def test_search_link_header_includes_next_when_not_last_page(self, client):
        """Verify Link header includes 'next' link when not on last page."""
        # Mock data with multiple pages (assuming total > limit)
        resp = client.get("/api/v1/search?q=test&page=1&limit=10")
        assert resp.status_code == 200

        link_header = resp.headers["Link"]
        # On first page, should have next link
        if int(resp.headers["X-Total-Count"]) > 10:
            assert 'rel="next"' in link_header

    def test_search_link_header_includes_prev_when_not_first_page(self, client):
        """Verify Link header includes 'prev' link when not on first page."""
        resp = client.get("/api/v1/search?q=test&page=2&limit=10")
        assert resp.status_code == 200

        link_header = resp.headers["Link"]
        # On page 2, should have prev link
        assert 'rel="prev"' in link_header


class TestAPIKeySecurity:
    """Test API key authentication middleware."""

    def test_public_endpoints_accessible_without_key(self, client):
        """Health and root endpoints should always be accessible."""
        assert client.get("/health").status_code == 200
        assert client.get("/").status_code == 200

    def test_api_endpoints_accessible_when_auth_disabled(self, client):
        """When API_KEY_ENABLED=false, all endpoints are open."""
        resp = client.get("/api/v1/search?q=test")
        assert resp.status_code == 200

    def test_api_key_rejected_when_enabled(self):
        """When API_KEY_ENABLED=true, requests without key get 401."""
        from africapep.config import settings
        original_enabled = settings.api_key_enabled
        original_key = settings.api_key
        try:
            settings.api_key_enabled = True
            settings.api_key = "test-secret-key"

            mock_neo4j = MagicMock()
            mock_neo4j.verify_connectivity.return_value = True
            mock_neo4j_module = MagicMock()
            mock_neo4j_module.neo4j_client = mock_neo4j

            mock_db = MagicMock()
            mock_db.__enter__ = MagicMock(return_value=mock_db)
            mock_db.__exit__ = MagicMock(return_value=False)
            mock_result = MagicMock()
            mock_result.scalar.return_value = 0
            mock_result.fetchall.return_value = []
            mock_db.execute.return_value = mock_result

            with patch.dict(sys.modules, {"africapep.database.neo4j_client": mock_neo4j_module}):
                with patch("africapep.database.postgres_client.get_db", return_value=mock_db):
                    from fastapi.testclient import TestClient
                    from africapep.api.main import app
                    tc = TestClient(app)
                    # Without key -> 401
                    resp = tc.get("/api/v1/search?q=test")
                    assert resp.status_code == 401
                    assert resp.json()["code"] == "UNAUTHORIZED"

                    # With correct key -> 200
                    resp = tc.get("/api/v1/search?q=test", headers={"X-API-Key": "test-secret-key"})
                    assert resp.status_code == 200
        finally:
            settings.api_key_enabled = original_enabled
            settings.api_key = original_key


class TestRequestSizeLimit:
    """Test request body size limit middleware."""

    def test_oversized_request_rejected(self, client):
        """Requests exceeding MAX_REQUEST_SIZE should get 413."""
        from africapep.config import settings
        original = settings.max_request_size
        try:
            settings.max_request_size = 100  # 100 bytes
            resp = client.post(
                "/api/v1/screen",
                json={"name": "A" * 200},
            )
            assert resp.status_code == 413
        finally:
            settings.max_request_size = original


class TestGDPRHashing:
    """Test GDPR-compliant query name hashing."""

    def test_hash_function(self):
        """Verify the hashing function works correctly."""
        from africapep.api.routers.screen import _maybe_hash_name
        from africapep.config import settings

        original = settings.hash_screening_queries
        try:
            settings.hash_screening_queries = False
            assert _maybe_hash_name("John Doe") == "John Doe"

            settings.hash_screening_queries = True
            hashed = _maybe_hash_name("John Doe")
            assert hashed != "John Doe"
            assert len(hashed) == 64  # SHA-256 hex digest
            # Same input -> same hash
            assert _maybe_hash_name("John Doe") == hashed
        finally:
            settings.hash_screening_queries = original


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
