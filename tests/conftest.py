"""Shared pytest fixtures for the AfricaPEP test suite."""
import sys
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_db():
    """A MagicMock that works as a context manager (get_db replacement).

    * ``execute().scalar()`` returns ``0``
    * ``execute().fetchall()`` returns ``[]``
    """
    db = MagicMock()
    db.__enter__ = MagicMock(return_value=db)
    db.__exit__ = MagicMock(return_value=False)

    mock_result = MagicMock()
    mock_result.scalar.return_value = 0
    mock_result.fetchall.return_value = []
    db.execute.return_value = mock_result

    return db


@pytest.fixture
def mock_neo4j():
    """A MagicMock that mimics :class:`Neo4jClient`.

    * ``verify_connectivity()`` returns ``True``
    * ``get_stats()`` returns sample aggregate data
    * ``run()`` returns ``[]`` by default
    """
    client = MagicMock()
    client.verify_connectivity.return_value = True
    client.get_stats.return_value = {
        "total_persons": 100,
        "active": 80,
        "sources": 50,
    }
    client.run.return_value = []
    return client


@pytest.fixture
def client(mock_neo4j, mock_db):
    """Reusable FastAPI ``TestClient`` with mocked database connections."""
    mock_neo4j_module = MagicMock()
    mock_neo4j_module.Neo4jClient = MagicMock(return_value=mock_neo4j)
    mock_neo4j_module.neo4j_client = mock_neo4j

    with patch.dict(sys.modules, {"africapep.database.neo4j_client": mock_neo4j_module}):
        with patch("africapep.database.postgres_client.get_db", return_value=mock_db):
            from fastapi.testclient import TestClient
            from africapep.api.main import app

            yield TestClient(app)


# ── Sample data factories ──

def sample_pep_row(
    *,
    neo4j_id="neo4j-001",
    full_name="Kwame Mensah",
    name_variants=None,
    date_of_birth="1965-03-12",
    nationality="GH",
    pep_tier=1,
    is_active_pep=True,
    current_positions=None,
    first_seen=None,
    last_seen=None,
    trgm_score=0.85,
    country="GH",
):
    """Return a MagicMock that mimics a SQLAlchemy Row from pep_profiles."""
    row = MagicMock()
    row.id = "uuid-001"
    row.neo4j_id = neo4j_id
    row.full_name = full_name
    row.name_variants = name_variants or []
    row.date_of_birth = date_of_birth
    row.nationality = nationality
    row.pep_tier = pep_tier
    row.is_active_pep = is_active_pep
    row.current_positions = current_positions or []
    row.first_seen = first_seen
    row.last_seen = last_seen
    row.trgm_score = trgm_score
    row.country = country
    return row


def sample_position(
    *,
    title="President",
    institution="Federal Government",
    country="NG",
    branch="EXECUTIVE",
):
    """Return a dict suitable for position data."""
    return {
        "title": title,
        "institution": institution,
        "country": country,
        "branch": branch,
    }


def sample_person_neo4j(
    *,
    person_id="person-001",
    full_name="Bola Tinubu",
    name_variants=None,
    date_of_birth="1952-03-29",
    nationality="NG",
    pep_tier=1,
    is_active_pep=True,
    current_positions=None,
):
    """Return a dict that mimics a Neo4j Person record."""
    return {
        "id": person_id,
        "full_name": full_name,
        "name_variants": name_variants or ["Ahmed Bola Tinubu"],
        "date_of_birth": date_of_birth,
        "nationality": nationality,
        "pep_tier": pep_tier,
        "is_active_pep": is_active_pep,
        "current_positions": current_positions or [
            {"title": "President", "institution": "Federal Government", "country": "NG", "branch": "EXECUTIVE"}
        ],
    }
