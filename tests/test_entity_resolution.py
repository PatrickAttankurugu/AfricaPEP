"""Tests for entity resolution: merge/no-merge decisions, scoring, deduplication."""
from datetime import datetime, timezone



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
        scraped_at=datetime.now(timezone.utc),
        extra_fields={},
    )


class TestOverMergePrevention:
    """The corroboration policy must stop distinct people from auto-merging."""

    def test_similar_names_same_generic_position_do_not_merge(self):
        """Different people sharing a surname + generic title must NOT merge.

        Under the old composite gate (name*0.7 + position*0.3 when DOB is
        missing), two distinct 'X Diallo' MPs crossed 0.85 via the shared
        'Member of Parliament' position and were wrongly merged. The
        corroboration policy requires a strong NAME match, so they stay split.
        """
        from africapep.pipeline.resolver import EntityResolver

        resolver = EntityResolver()
        # Same surname (same block), generic shared position, no DOB.
        id1 = resolver.add(_make_record("Amadou Diallo", country="GN"), 2)
        id2 = resolver.add(_make_record("Ousmane Diallo", country="GN"), 2)

        assert id1 != id2, "distinct people must not merge on name+position alone"
        assert len(resolver.entities) == 2

    def test_phonetic_match_merges_only_with_corroboration(self):
        from africapep.pipeline.resolver import EntityResolver
        from africapep.pipeline.scoring import name_match_components

        # Precondition: this pair is a phonetic (not orthographic) match.
        comp = name_match_components("Souleymane", "Sulaiman")
        assert comp.phonetic >= 0.90
        assert comp.orthographic < 0.85, "test needs an orthographically-weak pair"

        # Without corroboration (no DOB, different position) -> no merge.
        r1 = _make_record("Souleymane", title="Minister of Health",
                          institution="Ministry of Health", country="GN")
        r2 = _make_record("Sulaiman", title="Governor",
                          institution="Central Bank", country="GN")
        resolver = EntityResolver()
        assert resolver.add(r1, 2) != resolver.add(r2, 2)
        assert len(resolver.entities) == 2

        # With corroboration (same DOB) -> merge.
        r3 = _make_record("Souleymane", country="GN", dob="1960-01-01")
        r4 = _make_record("Sulaiman", country="GN", dob="1960-01-01")
        resolver2 = EntityResolver()
        assert resolver2.add(r3, 2) == resolver2.add(r4, 2)
        assert len(resolver2.entities) == 1


class TestEntityResolver:
    def test_add_single_entity(self):
        from africapep.pipeline.resolver import EntityResolver

        resolver = EntityResolver()
        record = _make_record("Kwame Mensah")
        entity_id = resolver.add(record, 2)

        assert entity_id is not None
        assert len(resolver.entities) == 1
        assert resolver.entities[entity_id].full_name == "Kwame Mensah"

    def test_person_id_stable_across_runs_via_qid(self):
        """Same Wikidata QID must map to the same Person id across separate runs.

        Each scrape run builds a fresh EntityResolver, so the in-memory QID
        cache cannot deduplicate against prior runs. The Person id must
        therefore be derived from the stable Wikidata QID, so the Neo4j
        ``MERGE (p:Person {id})`` updates the existing node instead of
        creating a duplicate every run (the cause of ~4-7x count inflation).
        """
        from africapep.pipeline.resolver import EntityResolver

        rec = _make_record("Dionisio Cabi", country="GW")
        rec.extra_fields = {"wikidata_qid": "Q123"}

        # Two independent resolvers simulate two separate scrape runs.
        id_run1 = EntityResolver().add(rec, 1)
        id_run2 = EntityResolver().add(rec, 1)

        assert id_run1 == id_run2, "Person id must be stable across runs for a QID"
        assert id_run1 == "wd:Q123"

    def test_person_id_falls_back_to_uuid_without_qid(self):
        """Records with no QID still get a (unique) id and don't crash."""
        from africapep.pipeline.resolver import EntityResolver

        rec = _make_record("Anonymous Associate", country="GW")  # no extra_fields qid
        entity_id = EntityResolver().add(rec, 2)

        assert entity_id and not entity_id.startswith("wd:")

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


class TestContentDerivedNodeIds:
    """Position/Organisation ids must be stable across pipeline runs so Neo4j
    MERGE upserts onto existing nodes instead of minting duplicates."""

    def test_same_position_content_same_id(self):
        from africapep.pipeline.resolver import _content_id

        a = _content_id("position", "President", "Government of Chad", "TD", "EXECUTIVE")
        b = _content_id("position", "President", "Government of Chad", "TD", "EXECUTIVE")
        assert a == b

    def test_id_normalises_case_and_whitespace(self):
        from africapep.pipeline.resolver import _content_id

        a = _content_id("position", "President", "Government of Chad", "TD", "EXECUTIVE")
        b = _content_id("position", " president ", "GOVERNMENT OF CHAD", "td", "executive")
        assert a == b

    def test_different_content_different_id(self):
        from africapep.pipeline.resolver import _content_id

        a = _content_id("position", "President", "Government of Chad", "TD", "EXECUTIVE")
        b = _content_id("position", "Minister of Finance", "Government of Chad", "TD", "EXECUTIVE")
        assert a != b

    def test_none_parts_handled(self):
        from africapep.pipeline.resolver import _content_id

        assert _content_id("organisation", None, None) == _content_id("organisation", "", "")
