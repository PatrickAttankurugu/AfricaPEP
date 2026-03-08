"""Tests for the FastAPI screening API.

These tests use synthetic data and mock database calls.
"""
import pytest


class TestScreeningAPI:
    """Test the screening endpoint logic."""

    def test_screening_request_validation(self):
        from africapep.api.schemas import ScreeningRequest

        # Valid request
        req = ScreeningRequest(name="Kwame Mensah", country="GH", threshold=0.75)
        assert req.name == "Kwame Mensah"
        assert req.country == "GH"
        assert req.threshold == 0.75

    def test_screening_request_defaults(self):
        from africapep.api.schemas import ScreeningRequest

        req = ScreeningRequest(name="Test Name")
        assert req.country is None
        assert req.threshold == 0.75

    def test_screening_request_min_name_length(self):
        from africapep.api.schemas import ScreeningRequest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            ScreeningRequest(name="A")

    def test_screening_request_threshold_bounds(self):
        from africapep.api.schemas import ScreeningRequest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            ScreeningRequest(name="Test", threshold=1.5)

        with pytest.raises(ValidationError):
            ScreeningRequest(name="Test", threshold=-0.1)


class TestSearchParams:
    def test_search_params_defaults(self):
        from africapep.api.schemas import SearchParams

        params = SearchParams(q="test")
        assert params.page == 1
        assert params.limit == 20
        assert params.country is None
        assert params.tier is None

    def test_search_params_validation(self):
        from africapep.api.schemas import SearchParams
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            SearchParams(q="test", tier=5)

        with pytest.raises(ValidationError):
            SearchParams(q="test", limit=200)


class TestResponseModels:
    def test_match_result(self):
        from africapep.api.schemas import MatchResult

        match = MatchResult(
            pep_id="test-uuid",
            matched_name="Kwame Mensah",
            match_score=0.89,
            match=True,
            pep_tier=1,
            risk_level="high",
            is_active=True,
            nationality="GH",
        )
        assert match.match_score == 0.89
        assert match.pep_tier == 1
        assert match.match is True
        assert match.risk_level == "high"
        assert match.datasets == ["africapep-wikidata"]

    def test_screening_response(self):
        from africapep.api.schemas import ScreeningResponse, MatchResult

        resp = ScreeningResponse(
            query="Kwame Mensah",
            threshold=0.75,
            total_matches=1,
            matches=[
                MatchResult(
                    pep_id="uuid-1",
                    matched_name="Kwame Asante Mensah",
                    match_score=0.89,
                    match=True,
                    pep_tier=1,
                    risk_level="high",
                    is_active=True,
                    nationality="GH",
                )
            ],
            screening_id="screen-uuid",
            screened_at="2024-01-01T00:00:00Z",
        )
        assert len(resp.matches) == 1
        assert resp.matches[0].match_score == 0.89
        assert resp.threshold == 0.75
        assert resp.total_matches == 1

    def test_graph_response(self):
        from africapep.api.schemas import GraphResponse, GraphNode, GraphEdge

        resp = GraphResponse(
            nodes=[
                GraphNode(id="1", label="Kwame Mensah", type="Person"),
                GraphNode(id="2", label="Minister of Finance", type="Position"),
            ],
            edges=[
                GraphEdge(source="1", target="2", type="HELD_POSITION"),
            ],
        )
        assert len(resp.nodes) == 2
        assert len(resp.edges) == 1

    def test_stats_response(self):
        from africapep.api.schemas import StatsResponse

        stats = StatsResponse(
            total_peps=100,
            by_country={"GH": 40, "NG": 35, "KE": 25},
            by_tier={"tier_1": 20, "tier_2": 50, "tier_3": 30},
            sources_count=500,
            active_peps=80,
        )
        assert stats.total_peps == 100
        assert stats.by_country["GH"] == 40

    def test_health_response(self):
        from africapep.api.schemas import HealthResponse

        health = HealthResponse(
            status="healthy",
            neo4j="connected",
            postgres="connected",
        )
        assert health.status == "healthy"


class TestFuzzyMatchScoring:
    """Test the actual fuzzy matching logic used in screening."""

    def test_exact_match_high_score(self):
        from rapidfuzz import fuzz

        score = fuzz.token_sort_ratio("Kwame Mensah", "Kwame Mensah") / 100.0
        assert score >= 0.99

    def test_partial_match(self):
        from rapidfuzz import fuzz

        score = fuzz.token_sort_ratio("Kwame Mensah", "Kwame Asante Mensah") / 100.0
        assert score >= 0.70

    def test_reordered_name_match(self):
        from rapidfuzz import fuzz

        score = fuzz.token_sort_ratio("Mensah Kwame", "Kwame Mensah") / 100.0
        assert score >= 0.95, "Token sort should handle name reordering"

    def test_completely_different_low_score(self):
        from rapidfuzz import fuzz

        score = fuzz.token_sort_ratio("Kwame Mensah", "Amina Mohammed") / 100.0
        assert score < 0.50

    def test_similar_surname_different_first(self):
        from rapidfuzz import fuzz

        score = fuzz.token_sort_ratio("Kwame Mensah", "Kofi Mensah") / 100.0
        assert 0.50 <= score <= 0.90

    def test_abbreviated_name(self):
        from rapidfuzz import fuzz

        score = fuzz.token_sort_ratio("K. Mensah", "Kwame Mensah") / 100.0
        assert score >= 0.50
