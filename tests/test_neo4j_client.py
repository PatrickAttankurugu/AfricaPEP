"""Tests for Neo4jClient in africapep.database.neo4j_client.

The ``neo4j`` driver package may not be installed in the test environment,
so we inject a mock ``neo4j`` module into ``sys.modules`` before importing
the client.
"""
import sys
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# Provide a fake ``neo4j`` package so the import of neo4j_client succeeds
# even when the real driver is not installed.
# ---------------------------------------------------------------------------
_mock_neo4j_pkg = MagicMock()
_mock_neo4j_pkg.GraphDatabase = MagicMock()
_mock_neo4j_pkg.Driver = MagicMock


def _get_client_class(mock_gdb):
    """Import Neo4jClient with neo4j + settings mocked out."""
    # Ensure the module is re-loaded each time so patches take effect
    mod_name = "africapep.database.neo4j_client"
    if mod_name in sys.modules:
        del sys.modules[mod_name]

    with patch.dict(sys.modules, {"neo4j": _mock_neo4j_pkg}):
        with patch("africapep.config.settings") as mock_settings:
            mock_settings.neo4j_uri = "bolt://localhost:7687"
            mock_settings.neo4j_user = "neo4j"
            mock_settings.neo4j_password = "test"

            # Point GraphDatabase.driver at our mock_gdb
            _mock_neo4j_pkg.GraphDatabase = mock_gdb

            # Force reimport
            import importlib
            if mod_name in sys.modules:
                mod = importlib.reload(sys.modules[mod_name])
            else:
                mod = importlib.import_module(mod_name)

    return mod.Neo4jClient


class TestVerifyConnectivity:
    def test_success(self):
        mock_driver = MagicMock()
        mock_gdb = MagicMock()
        mock_gdb.driver.return_value = mock_driver

        Neo4jClient = _get_client_class(mock_gdb)
        client = Neo4jClient()
        assert client.verify_connectivity() is True
        mock_driver.verify_connectivity.assert_called_once()

    def test_failure(self):
        mock_driver = MagicMock()
        mock_driver.verify_connectivity.side_effect = Exception("Connection refused")
        mock_gdb = MagicMock()
        mock_gdb.driver.return_value = mock_driver

        Neo4jClient = _get_client_class(mock_gdb)
        client = Neo4jClient()
        assert client.verify_connectivity() is False

    def test_reconnects_if_driver_none(self):
        mock_driver = MagicMock()
        mock_gdb = MagicMock()
        mock_gdb.driver.return_value = mock_driver

        Neo4jClient = _get_client_class(mock_gdb)
        client = Neo4jClient()
        client._driver = None  # Simulate lost connection

        assert client.verify_connectivity() is True
        # driver() should have been called again to reconnect
        assert mock_gdb.driver.call_count >= 2


class TestRun:
    def test_run_returns_list_of_dicts(self):
        mock_record = MagicMock()
        mock_record.__iter__ = MagicMock(return_value=iter([("name", "Alice")]))
        mock_record.keys.return_value = ["name"]

        mock_result = MagicMock()
        mock_result.__iter__ = MagicMock(return_value=iter([mock_record]))

        mock_session = MagicMock()
        mock_session.__enter__ = MagicMock(return_value=mock_session)
        mock_session.__exit__ = MagicMock(return_value=False)
        mock_session.run.return_value = mock_result

        mock_driver = MagicMock()
        mock_driver.session.return_value = mock_session

        mock_gdb = MagicMock()
        mock_gdb.driver.return_value = mock_driver

        Neo4jClient = _get_client_class(mock_gdb)
        client = Neo4jClient()
        results = client.run("MATCH (n) RETURN n.name AS name")
        assert isinstance(results, list)


class TestUpsertPersonBatch:
    def test_batch_upsert_calls_execute_write(self):
        mock_session = MagicMock()
        mock_session.__enter__ = MagicMock(return_value=mock_session)
        mock_session.__exit__ = MagicMock(return_value=False)
        mock_session.execute_write.return_value = ["id-1", "id-2"]

        mock_driver = MagicMock()
        mock_driver.session.return_value = mock_session

        mock_gdb = MagicMock()
        mock_gdb.driver.return_value = mock_driver

        Neo4jClient = _get_client_class(mock_gdb)
        client = Neo4jClient()
        persons = [
            {"id": "id-1", "full_name": "A", "name_variants": [], "date_of_birth": None,
             "nationality": "GH", "gender": "M", "pep_tier": 1, "is_active_pep": True},
            {"id": "id-2", "full_name": "B", "name_variants": [], "date_of_birth": None,
             "nationality": "NG", "gender": "F", "pep_tier": 2, "is_active_pep": True},
        ]
        ids = client.upsert_person_batch(persons, batch_size=10)
        assert ids == ["id-1", "id-2"]
        mock_session.execute_write.assert_called_once()

    def test_batch_upsert_chunks(self):
        mock_session = MagicMock()
        mock_session.__enter__ = MagicMock(return_value=mock_session)
        mock_session.__exit__ = MagicMock(return_value=False)
        mock_session.execute_write.return_value = ["id-1"]

        mock_driver = MagicMock()
        mock_driver.session.return_value = mock_session

        mock_gdb = MagicMock()
        mock_gdb.driver.return_value = mock_driver

        Neo4jClient = _get_client_class(mock_gdb)
        client = Neo4jClient()
        persons = [
            {"id": f"id-{i}", "full_name": f"P{i}", "name_variants": [],
             "date_of_birth": None, "nationality": "GH", "gender": "M",
             "pep_tier": 1, "is_active_pep": True}
            for i in range(3)
        ]
        client.upsert_person_batch(persons, batch_size=1)
        assert mock_session.execute_write.call_count == 3


class TestBatchUpsertPositions:
    def test_positions_delegated_to_run_write_batch(self):
        mock_session = MagicMock()
        mock_session.__enter__ = MagicMock(return_value=mock_session)
        mock_session.__exit__ = MagicMock(return_value=False)

        mock_driver = MagicMock()
        mock_driver.session.return_value = mock_session

        mock_gdb = MagicMock()
        mock_gdb.driver.return_value = mock_driver

        Neo4jClient = _get_client_class(mock_gdb)
        client = Neo4jClient()
        positions = [
            {"id": "pos-1", "title": "President", "institution": "Govt",
             "country": "GH", "branch": "EXECUTIVE", "start_date": None,
             "end_date": None, "is_current": True},
        ]
        client.batch_upsert_positions(positions)
        mock_session.execute_write.assert_called_once()


class TestGetPerson:
    def test_get_person_calls_run(self):
        mock_result = MagicMock()
        mock_result.__iter__ = MagicMock(return_value=iter([]))

        mock_session = MagicMock()
        mock_session.__enter__ = MagicMock(return_value=mock_session)
        mock_session.__exit__ = MagicMock(return_value=False)
        mock_session.run.return_value = mock_result

        mock_driver = MagicMock()
        mock_driver.session.return_value = mock_session

        mock_gdb = MagicMock()
        mock_gdb.driver.return_value = mock_driver

        Neo4jClient = _get_client_class(mock_gdb)
        client = Neo4jClient()
        result = client.get_person("person-001")
        assert isinstance(result, list)
        mock_session.run.assert_called_once()


class TestGetStats:
    def test_get_stats_returns_first_record(self):
        stats_data = {"total_persons": 100, "active": 80, "sources": 50}
        mock_record = MagicMock()
        mock_record.__iter__ = MagicMock(return_value=iter(stats_data.items()))
        mock_record.keys.return_value = list(stats_data.keys())

        mock_result = MagicMock()
        mock_result.__iter__ = MagicMock(return_value=iter([mock_record]))

        mock_session = MagicMock()
        mock_session.__enter__ = MagicMock(return_value=mock_session)
        mock_session.__exit__ = MagicMock(return_value=False)
        mock_session.run.return_value = mock_result

        mock_driver = MagicMock()
        mock_driver.session.return_value = mock_session

        mock_gdb = MagicMock()
        mock_gdb.driver.return_value = mock_driver

        Neo4jClient = _get_client_class(mock_gdb)
        client = Neo4jClient()
        stats = client.get_stats()
        assert isinstance(stats, dict)

    def test_get_stats_empty_returns_dict(self):
        mock_result = MagicMock()
        mock_result.__iter__ = MagicMock(return_value=iter([]))

        mock_session = MagicMock()
        mock_session.__enter__ = MagicMock(return_value=mock_session)
        mock_session.__exit__ = MagicMock(return_value=False)
        mock_session.run.return_value = mock_result

        mock_driver = MagicMock()
        mock_driver.session.return_value = mock_session

        mock_gdb = MagicMock()
        mock_gdb.driver.return_value = mock_driver

        Neo4jClient = _get_client_class(mock_gdb)
        client = Neo4jClient()
        stats = client.get_stats()
        assert stats == {}


class TestClose:
    def test_close_calls_driver_close(self):
        mock_driver = MagicMock()
        mock_gdb = MagicMock()
        mock_gdb.driver.return_value = mock_driver

        Neo4jClient = _get_client_class(mock_gdb)
        client = Neo4jClient()
        client.close()
        mock_driver.close.assert_called_once()
        assert client._driver is None

    def test_close_noop_when_no_driver(self):
        mock_driver = MagicMock()
        mock_gdb = MagicMock()
        mock_gdb.driver.return_value = mock_driver

        Neo4jClient = _get_client_class(mock_gdb)
        client = Neo4jClient()
        client._driver = None
        client.close()  # Should not raise
