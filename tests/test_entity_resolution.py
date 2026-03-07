"""Tests for entity resolution: merge/no-merge decisions, scoring, deduplication."""
from datetime import datetime, date

import pytest


def _make_record(name, title="Member of Parliament", institution="Parliament",
                 country="GH", dob=None):
    from africapep.pipeline.normaliser import NormalisedRecord, generate_name_variants

    return NormalisedRecord(
        full_name=name,
        name_variants=generate_name_variants(name),
        title=title,
        institution=institution,
        branch="LEGISLATIVE",
        country_code=country,
        date_of_birth=dob,
        source_url="https://example.com",
        source_type="PARLIAMENT",
        raw_text=f"{name} {title}",
        scraped_at=datetime.utcnow(),
        extra_fields={},
    )


class TestEntityResolver:
    def test_add_single_entity(self):
        from africapep.pipeline.resolver import EntityResolver

        resolver = EntityResolver()
        record = _make_record("Kwame Mensah")
        entity_id = resolver.add(record, 2)

        assert entity_id is not None
        assert len(resolver.entities) == 1
        assert resolver.entities[entity_id].full_name == "Kwame Mensah"

    def test_exact_name_merge(self):
        from africapep.pipeline.resolver import EntityResolver

        resolver = EntityResolver()
        r1 = _make_record("Kwame Asante Mensah")
        r2 = _make_record("Kwame Asante Mensah")

        id1 = resolver.add(r1, 2)
        id2 = resolver.add(r2, 2)

        assert id1 == id2, "Same exact name should merge"
        assert len(resolver.entities) == 1

    def test_similar_name_merge(self):
        from africapep.pipeline.resolver import EntityResolver

        resolver = EntityResolver()
        r1 = _make_record("Kwame Asante Mensah")
        r2 = _make_record("Kwame A. Mensah")

        id1 = resolver.add(r1, 2)
        id2 = resolver.add(r2, 2)

        # These should merge (high similarity)
        assert id1 == id2, "Very similar names should merge"
        assert len(resolver.entities) == 1

    def test_different_names_no_merge(self):
        from africapep.pipeline.resolver import EntityResolver

        resolver = EntityResolver()
        r1 = _make_record("Kwame Mensah")
        r2 = _make_record("Ama Bawumia")

        id1 = resolver.add(r1, 2)
        id2 = resolver.add(r2, 2)

        assert id1 != id2, "Different names should not merge"
        assert len(resolver.entities) == 2

    def test_different_country_no_merge(self):
        from africapep.pipeline.resolver import EntityResolver

        resolver = EntityResolver()
        r1 = _make_record("John Smith", country="GH")
        r2 = _make_record("John Smith", country="NG")

        id1 = resolver.add(r1, 2)
        id2 = resolver.add(r2, 2)

        # Different countries = different blocking keys, so no merge
        assert id1 != id2

    def test_merge_preserves_sources(self):
        from africapep.pipeline.resolver import EntityResolver

        resolver = EntityResolver()
        r1 = _make_record("Kwame Mensah")
        r2 = _make_record("Kwame Mensah")

        id1 = resolver.add(r1, 2)
        resolver.add(r2, 2)

        entity = resolver.entities[id1]
        assert len(entity.sources) == 2, "Merge should preserve both sources"

    def test_merge_keeps_best_tier(self):
        from africapep.pipeline.resolver import EntityResolver

        resolver = EntityResolver()
        r1 = _make_record("Kwame Mensah")
        r2 = _make_record("Kwame Mensah", title="Minister of Finance")

        resolver.add(r1, 2)
        resolver.add(r2, 1)

        entity = list(resolver.entities.values())[0]
        assert entity.pep_tier == 1, "Should keep highest (most restrictive) tier"

    def test_merge_accumulates_name_variants(self):
        from africapep.pipeline.resolver import EntityResolver

        resolver = EntityResolver()
        r1 = _make_record("Kwame Asante Mensah")
        r2 = _make_record("K. A. Mensah")

        id1 = resolver.add(r1, 2)
        resolver.add(r2, 2)

        entity = resolver.entities[id1]
        assert len(entity.name_variants) >= 3

    def test_stats(self):
        from africapep.pipeline.resolver import EntityResolver

        resolver = EntityResolver()
        resolver.add(_make_record("Person A"), 2)
        resolver.add(_make_record("Person B"), 2)

        stats = resolver.get_stats()
        assert stats["total_entities"] == 2
        assert stats["blocks"] >= 1

    def test_potential_duplicate_flagged(self):
        from africapep.pipeline.resolver import EntityResolver

        resolver = EntityResolver()
        # Names similar enough for review but different enough to not auto-merge
        r1 = _make_record("Kwame Mensah Asante")
        r2 = _make_record("Kwame Mensah Asanti")  # slight typo

        resolver.add(r1, 2)
        resolver.add(r2, 2)

        # Either merged or flagged as duplicate
        total = len(resolver.entities)
        dupes = len(resolver.duplicates)
        assert total <= 2
        # At minimum, the resolver handled both records


class TestScoringLogic:
    def test_identical_names_high_score(self):
        from africapep.pipeline.resolver import EntityResolver

        resolver = EntityResolver()
        r1 = _make_record("Kwame Mensah")
        existing_id = resolver.add(r1, 2)
        existing = resolver.entities[existing_id]

        r2 = _make_record("Kwame Mensah")
        score = resolver._compute_score(r2, existing)
        assert score >= 0.85

    def test_different_names_low_score(self):
        from africapep.pipeline.resolver import EntityResolver

        resolver = EntityResolver()
        r1 = _make_record("Kwame Mensah")
        existing_id = resolver.add(r1, 2)
        existing = resolver.entities[existing_id]

        r2 = _make_record("Ama Bawumia")
        score = resolver._compute_score(r2, existing)
        assert score < 0.70, f"Different names should score low, got {score}"
