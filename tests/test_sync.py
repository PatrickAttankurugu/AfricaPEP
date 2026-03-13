"""Tests for sync_all() and helpers in africapep.database.sync."""
import sys
import json
import uuid as uuid_mod
from unittest.mock import MagicMock, patch

from tests.conftest import sample_person_neo4j

# Mock the neo4j driver before importing sync (not installed in test env)
if "neo4j" not in sys.modules:
    sys.modules["neo4j"] = MagicMock()

_mock_neo4j_client_mod = MagicMock()
sys.modules.setdefault("africapep.database.neo4j_client", _mock_neo4j_client_mod)

from africapep.database.sync import _deterministic_id, _parse_date, sync_all  # noqa: E402


class TestDeterministicId:
    def test_returns_valid_uuid(self):
        result = _deterministic_id("person-001")
        parsed = uuid_mod.UUID(result)
        assert str(parsed) == result

    def test_same_input_same_output(self):
        assert _deterministic_id("person-001") == _deterministic_id("person-001")

    def test_different_input_different_output(self):
        assert _deterministic_id("person-001") != _deterministic_id("person-002")

    def test_idempotent_across_calls(self):
        results = {_deterministic_id("some-stable-id") for _ in range(50)}
        assert len(results) == 1


class TestSyncAllHappyPath:
    @patch("africapep.database.sync.get_db")
    @patch("africapep.database.sync.neo4j_client")
    def test_sync_persons_calls_upsert(self, mock_neo4j, mock_get_db):
        person = sample_person_neo4j()
        mock_neo4j.run.side_effect = [[person], []]

        db = MagicMock()
        db.__enter__ = MagicMock(return_value=db)
        db.__exit__ = MagicMock(return_value=False)
        mock_get_db.return_value = db

        synced = sync_all()
        assert synced == 1
        assert db.execute.call_count >= 1

    @patch("africapep.database.sync.get_db")
    @patch("africapep.database.sync.neo4j_client")
    def test_sync_multiple_persons(self, mock_neo4j, mock_get_db):
        persons = [
            sample_person_neo4j(person_id="p1", full_name="Person One"),
            sample_person_neo4j(person_id="p2", full_name="Person Two"),
            sample_person_neo4j(person_id="p3", full_name="Person Three"),
        ]
        mock_neo4j.run.side_effect = [persons, []]

        db = MagicMock()
        db.__enter__ = MagicMock(return_value=db)
        db.__exit__ = MagicMock(return_value=False)
        mock_get_db.return_value = db

        assert sync_all() == 3

    @patch("africapep.database.sync.get_db")
    @patch("africapep.database.sync.neo4j_client")
    def test_sync_returns_zero_for_empty(self, mock_neo4j, mock_get_db):
        mock_neo4j.run.side_effect = [[], []]

        db = MagicMock()
        db.__enter__ = MagicMock(return_value=db)
        db.__exit__ = MagicMock(return_value=False)
        mock_get_db.return_value = db

        assert sync_all() == 0


class TestSyncAllMissingFields:
    @patch("africapep.database.sync.get_db")
    @patch("africapep.database.sync.neo4j_client")
    def test_none_full_name_defaults_to_empty(self, mock_neo4j, mock_get_db):
        person = sample_person_neo4j()
        person["full_name"] = None
        mock_neo4j.run.side_effect = [[person], []]

        db = MagicMock()
        db.__enter__ = MagicMock(return_value=db)
        db.__exit__ = MagicMock(return_value=False)
        mock_get_db.return_value = db

        assert sync_all() == 1
        call_params = db.execute.call_args[0][1]
        assert call_params["full_name"] == ""

    @patch("africapep.database.sync.get_db")
    @patch("africapep.database.sync.neo4j_client")
    def test_none_name_variants_defaults_to_list(self, mock_neo4j, mock_get_db):
        person = sample_person_neo4j()
        person["name_variants"] = None
        mock_neo4j.run.side_effect = [[person], []]

        db = MagicMock()
        db.__enter__ = MagicMock(return_value=db)
        db.__exit__ = MagicMock(return_value=False)
        mock_get_db.return_value = db

        assert sync_all() == 1
        call_params = db.execute.call_args[0][1]
        assert call_params["name_variants"] == []

    @patch("africapep.database.sync.get_db")
    @patch("africapep.database.sync.neo4j_client")
    def test_none_dob_handled(self, mock_neo4j, mock_get_db):
        person = sample_person_neo4j()
        person["date_of_birth"] = None
        mock_neo4j.run.side_effect = [[person], []]

        db = MagicMock()
        db.__enter__ = MagicMock(return_value=db)
        db.__exit__ = MagicMock(return_value=False)
        mock_get_db.return_value = db

        assert sync_all() == 1
        call_params = db.execute.call_args[0][1]
        assert call_params["dob"] is None

    @patch("africapep.database.sync.get_db")
    @patch("africapep.database.sync.neo4j_client")
    def test_positions_without_title_filtered(self, mock_neo4j, mock_get_db):
        person = sample_person_neo4j()
        person["current_positions"] = [
            {"title": "President", "institution": "Govt", "country": "NG", "branch": "EXECUTIVE"},
            {"title": None, "institution": "Unknown", "country": "NG", "branch": ""},
            {"institution": "No Title", "country": "NG"},
        ]
        mock_neo4j.run.side_effect = [[person], []]

        db = MagicMock()
        db.__enter__ = MagicMock(return_value=db)
        db.__exit__ = MagicMock(return_value=False)
        mock_get_db.return_value = db

        assert sync_all() == 1
        call_params = db.execute.call_args[0][1]
        positions = json.loads(call_params["positions"])
        assert len(positions) == 1
        assert positions[0]["title"] == "President"


class TestSyncErrors:
    @patch("africapep.database.sync.neo4j_client")
    def test_neo4j_error_propagates(self, mock_neo4j):
        mock_neo4j.run.side_effect = Exception("Neo4j connection failed")
        
        with pytest.raises(Exception, match="Neo4j connection failed"):
            sync_all()

    @patch("africapep.database.sync.get_db")
    @patch("africapep.database.sync.neo4j_client")
    def test_postgres_error_propagates(self, mock_neo4j, mock_get_db):
        mock_neo4j.run.side_effect = [[sample_person_neo4j()], []]
        
        db = MagicMock()
        db.__enter__.side_effect = Exception("Postgres connection failed")
        mock_get_db.return_value = db
        
        with pytest.raises(Exception, match="Postgres connection failed"):
            sync_all()


class TestSyncIdempotency:
    @patch("africapep.database.sync.get_db")
    @patch("africapep.database.sync.neo4j_client")
    def test_sync_is_idempotent(self, mock_neo4j, mock_get_db):
        person = sample_person_neo4j(person_id="p1")
        # Same result for multiple runs
        mock_neo4j.run.side_effect = [[person], [], [person], []]

        db = MagicMock()
        db.__enter__ = MagicMock(return_value=db)
        mock_get_db.return_value = db

        # First run
        sync_all()
        id1 = db.execute.call_args[0][1]["id"]
        
        # Second run
        sync_all()
        id2 = db.execute.call_args[0][1]["id"]
        
        # Deterministic IDs should match
        assert id1 == id2
        assert id1 == _deterministic_id("p1")
