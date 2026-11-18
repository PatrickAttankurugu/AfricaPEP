"""Tests for the source_records count used by GET /api/v1/stats.

source_records holds tens of millions of rows in production, so an exact
COUNT(*) takes about 30 seconds. The stats endpoint uses the planner's
row estimate instead and only falls back to COUNT(*) when the table has
never been analysed.
"""
from unittest.mock import MagicMock

from africapep.api.routers.search import _count_source_records


def _db_returning(*scalars):
    """Mock session whose successive execute().scalar() calls return scalars."""
    db = MagicMock()
    results = []
    for value in scalars:
        result = MagicMock()
        result.scalar.return_value = value
        results.append(result)
    db.execute.side_effect = results
    return db


def _sql_of(call):
    return str(call.args[0])


def test_uses_planner_estimate_when_table_analysed():
    db = _db_returning(29702776.0)

    assert _count_source_records(db) == 29702776
    assert db.execute.call_count == 1
    assert "reltuples" in _sql_of(db.execute.call_args_list[0])


def test_falls_back_to_exact_count_when_never_analysed():
    # Postgres reports reltuples = -1 for a table that has never been analysed.
    db = _db_returning(-1.0, 1234)

    assert _count_source_records(db) == 1234
    assert "COUNT(*)" in _sql_of(db.execute.call_args_list[1])


def test_falls_back_to_exact_count_when_table_missing_from_catalog():
    db = _db_returning(None, 0)

    assert _count_source_records(db) == 0
    assert db.execute.call_count == 2
