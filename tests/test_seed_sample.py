"""Tests for the bundled offline sample dataset."""
from africapep.database.seed_sample import load_sample


def test_sample_loads():
    records, relationships = load_sample()
    assert len(records) >= 400
    assert len(relationships) >= 50


def test_sample_covers_two_countries():
    records, _ = load_sample()
    countries = {r.country_code for r in records}
    assert countries == {"SC", "GM"}


def test_sample_records_are_complete():
    records, _ = load_sample()
    for r in records:
        assert r.full_name
        assert r.title
        assert r.source_url.startswith("https://")
        assert r.scraped_at is not None


def test_sample_relationships_reference_types():
    _, relationships = load_sample()
    allowed = {"SPOUSE", "CHILD", "SIBLING", "FATHER", "MOTHER"}
    for rel in relationships:
        assert rel.person_qid.startswith("Q")
        assert rel.relationship_type in allowed
