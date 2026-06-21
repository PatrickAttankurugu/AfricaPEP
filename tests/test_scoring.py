"""Tests for the name-matching scorer (components + backward-compat wrapper)."""


def test_name_match_components_returns_both_signals():
    from africapep.pipeline.scoring import name_match_components, NameMatchScore

    score = name_match_components("Mohammed Ali", "Muhammad Ali")
    assert isinstance(score, NameMatchScore)
    assert 0.0 <= score.orthographic <= 1.0
    assert 0.0 <= score.phonetic <= 1.0
    # Transliteration: phonetic should be the stronger signal here
    assert score.phonetic == 1.0
    assert score.best == max(score.orthographic, score.phonetic)


def test_hybrid_name_score_is_orthographic_only_unchanged():
    """The legacy wrapper must equal the orthographic component exactly."""
    from africapep.pipeline.scoring import hybrid_name_score, name_match_components

    for a, b in [("Mohammed Ali", "Muhammad Ali"),
                 ("Kwame Mensah", "Kwame Asante"),
                 ("Nelson Mandela", "Robert Mugabe")]:
        assert hybrid_name_score(a, b) == name_match_components(a, b).orthographic


def test_best_never_below_orthographic():
    from africapep.pipeline.scoring import name_match_components

    for a, b in [("Ahmed Mohammed", "Ahmad Muhammad"),
                 ("Jose Maria Neves", "Jose Maria Neves"),
                 ("Ali Bongo", "Omar Bongo")]:
        s = name_match_components(a, b)
        assert s.best >= s.orthographic
