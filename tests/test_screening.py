"""Tests for _find_matches() in africapep.api.routers.screen."""
from unittest.mock import MagicMock, patch

import pytest

# Import factory helpers from conftest (they are plain functions, not fixtures)
from tests.conftest import sample_pep_row, sample_position


def _make_db_context(rows):
    """Build a mock get_db() context manager that returns *rows* on fetchall."""
    db = MagicMock()
    db.__enter__ = MagicMock(return_value=db)
    db.__exit__ = MagicMock(return_value=False)
    mock_result = MagicMock()
    mock_result.fetchall.return_value = rows
    db.execute.return_value = mock_result
    return db


class TestFindMatchesMatching:
    """Names that are similar should produce results above the threshold."""

    @patch("africapep.api.routers.screen.get_db")
    def test_exact_match_returns_result(self, mock_get_db):
        row = sample_pep_row(full_name="Kwame Mensah", trgm_score=1.0)
        mock_get_db.return_value = _make_db_context([row])

        from africapep.api.routers.screen import _find_matches

        results = _find_matches("Kwame Mensah", threshold=0.75)
        assert len(results) >= 1
        assert results[0].matched_name == "Kwame Mensah"
        assert results[0].match_score >= 0.75

    @patch("africapep.api.routers.screen.get_db")
    def test_close_match_above_threshold(self, mock_get_db):
        row = sample_pep_row(full_name="Kwame Mensah", trgm_score=0.80)
        mock_get_db.return_value = _make_db_context([row])

        from africapep.api.routers.screen import _find_matches

        results = _find_matches("Kwame Mensa", threshold=0.60)
        assert len(results) >= 1
        assert results[0].match_score >= 0.60


class TestFindMatchesFiltering:
    """Names that are too different should be filtered out."""

    @patch("africapep.api.routers.screen.get_db")
    def test_no_match_below_threshold(self, mock_get_db):
        row = sample_pep_row(full_name="Completely Different Name", trgm_score=0.15)
        mock_get_db.return_value = _make_db_context([row])

        from africapep.api.routers.screen import _find_matches

        results = _find_matches("Kwame Mensah", threshold=0.75)
        assert len(results) == 0

    @patch("africapep.api.routers.screen.get_db")
    def test_empty_db_returns_empty(self, mock_get_db):
        mock_get_db.return_value = _make_db_context([])

        from africapep.api.routers.screen import _find_matches

        results = _find_matches("Anyone", threshold=0.75)
        assert results == []


class TestFindMatchesCountryFilter:
    """Country parameter should be forwarded as a SQL filter."""

    @patch("africapep.api.routers.screen.get_db")
    def test_country_filter_passed_in_params(self, mock_get_db):
        db = _make_db_context([])
        mock_get_db.return_value = db

        from africapep.api.routers.screen import _find_matches

        _find_matches("Kwame Mensah", country="GH", threshold=0.75)

        # The execute call should include country in the params
        call_args = db.execute.call_args
        params = call_args[0][1]  # second positional arg is the param dict
        assert params["country"] == "GH"

    @patch("africapep.api.routers.screen.get_db")
    def test_country_filter_uppercased(self, mock_get_db):
        db = _make_db_context([])
        mock_get_db.return_value = db

        from africapep.api.routers.screen import _find_matches

        _find_matches("Test", country="gh", threshold=0.75)
        params = db.execute.call_args[0][1]
        assert params["country"] == "GH"


class TestFindMatchesVariants:
    """Name variants stored on the row should be checked by rapidfuzz."""

    @patch("africapep.api.routers.screen.get_db")
    def test_variant_match_raises_score(self, mock_get_db):
        # The primary name is different, but a variant matches well
        row = sample_pep_row(
            full_name="A.B. Tinubu",
            name_variants=["Bola Ahmed Tinubu"],
            trgm_score=0.30,
        )
        mock_get_db.return_value = _make_db_context([row])

        from africapep.api.routers.screen import _find_matches

        results = _find_matches("Bola Ahmed Tinubu", threshold=0.60)
        assert len(results) >= 1
        # The best score should come from the variant, not the primary name
        assert results[0].explanation.matched_variant == "Bola Ahmed Tinubu"
        assert results[0].match_score >= 0.60

    @patch("africapep.api.routers.screen.get_db")
    def test_aliases_populated_from_variants(self, mock_get_db):
        row = sample_pep_row(
            full_name="Kwame Mensah",
            name_variants=["K. Mensah", "Kwame A. Mensah"],
            trgm_score=0.90,
        )
        mock_get_db.return_value = _make_db_context([row])

        from africapep.api.routers.screen import _find_matches

        results = _find_matches("Kwame Mensah", threshold=0.50)
        assert len(results) >= 1
        assert "K. Mensah" in results[0].aliases
        assert "Kwame A. Mensah" in results[0].aliases


class TestFindMatchesOrdering:
    """Results should be sorted by match_score descending."""

    @patch("africapep.api.routers.screen.get_db")
    def test_results_sorted_by_score_desc(self, mock_get_db):
        row_high = sample_pep_row(
            neo4j_id="high",
            full_name="Kwame Mensah",
            trgm_score=0.95,
        )
        row_low = sample_pep_row(
            neo4j_id="low",
            full_name="Kwame Mens",
            trgm_score=0.60,
        )
        mock_get_db.return_value = _make_db_context([row_low, row_high])

        from africapep.api.routers.screen import _find_matches

        results = _find_matches("Kwame Mensah", threshold=0.50)
        assert len(results) == 2
        assert results[0].match_score >= results[1].match_score

    @patch("africapep.api.routers.screen.get_db")
    def test_results_capped_at_20(self, mock_get_db):
        rows = [
            sample_pep_row(neo4j_id=f"id-{i}", full_name="Kwame Mensah", trgm_score=0.90)
            for i in range(30)
        ]
        mock_get_db.return_value = _make_db_context(rows)

        from africapep.api.routers.screen import _find_matches

        results = _find_matches("Kwame Mensah", threshold=0.50)
        assert len(results) <= 20


class TestFindMatchesPositions:
    """current_positions JSONB should be parsed into PositionResponse."""

    @patch("africapep.api.routers.screen.get_db")
    def test_positions_parsed(self, mock_get_db):
        row = sample_pep_row(
            full_name="Kwame Mensah",
            trgm_score=0.95,
            current_positions=[
                {"title": "President", "institution": "Govt", "country": "GH", "branch": "EXECUTIVE"},
            ],
        )
        mock_get_db.return_value = _make_db_context([row])

        from africapep.api.routers.screen import _find_matches

        results = _find_matches("Kwame Mensah", threshold=0.50)
        assert len(results) >= 1
        assert len(results[0].positions) == 1
        assert results[0].positions[0].title == "President"
