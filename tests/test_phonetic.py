"""Tests for phonetic name matching."""


def test_phonetic_matches_transliteration_variants():
    from africapep.pipeline.phonetic import phonetic_similarity

    # Same name, different transliteration -> should sound identical
    assert phonetic_similarity("Mohammed", "Muhammad") == 1.0
    assert phonetic_similarity("Ahmed Mohammed", "Ahmad Muhammad") == 1.0
    assert phonetic_similarity("Aboubacar", "Abubakar") == 1.0


def test_phonetic_distinguishes_different_given_names():
    from africapep.pipeline.phonetic import phonetic_similarity

    # Same surname but clearly different given names should not be ~1.0
    assert phonetic_similarity("Amadou Diallo", "Ousmane Diallo") < 1.0
    assert phonetic_similarity("Mohammed Toure", "Ibrahim Toure") < 1.0


def test_phonetic_is_token_order_independent():
    from africapep.pipeline.phonetic import phonetic_similarity

    assert phonetic_similarity("Mohammed Ali", "Ali Mohammed") == 1.0


def test_phonetic_edge_cases_return_zero():
    from africapep.pipeline.phonetic import phonetic_similarity

    assert phonetic_similarity("", "Mohammed") == 0.0
    assert phonetic_similarity("Mohammed", "") == 0.0
    assert phonetic_similarity("", "") == 0.0
    assert phonetic_similarity("---", "Mohammed") == 0.0


def test_phonetic_keys_skip_blank():
    from africapep.pipeline.phonetic import phonetic_keys

    assert phonetic_keys("") == []
    keys = phonetic_keys("Mohammed Ali")
    assert len(keys) == 2
    assert all(isinstance(k, tuple) and len(k) == 2 for k in keys)
