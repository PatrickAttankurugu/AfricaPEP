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


def test_exact_match():
    from africapep.pipeline.scoring import name_match_components

    for name in ["William James", "Marie-Claire", "O'Connor"]:
        score = name_match_components(name, name)
        assert score.orthographic == 1.0
        assert score.phonetic == 1.0
        assert score.best == 1.0


def test_word_reordering():
    from africapep.pipeline.scoring import name_match_components

    for i, j in [("Nelson Mandela", "Mandela Nelson"),
                 ("Peter Parker", "Parker Peter"),
                 ("Jose Maria Neves", "Maria Neves Jose")]:
        score = name_match_components(i, j)
        assert score.best == 1


def test_prefix_typos():
    from africapep.pipeline.scoring import name_match_components

    for i, j in [("Aelson Mandela", "Nelson Mandela"),
                 ("Peter Parker", "Peter Parkes"),
                 ("Jose Maria Neves", "KJose Maria Neves")]:
        score = name_match_components(i, j)
        assert score.best >= 0.8


def test_short_name_typos():
    from africapep.pipeline.scoring import name_match_components

    for i, j in [("Al", "El"), ("Ngozi", "Ngoz"), ("Nel", "Kel")]:
        score = name_match_components(i, j)
        assert score.best >= 0.6


def test_dissimilar_names():
    from africapep.pipeline.scoring import name_match_components

    for i, j in [("Nelson Mandela", "Robert Mugabe"),
        ("Olusegun Obasanjo", "Cyril Ramaphosa"),
        ("Wangari Maathai", "Ellen Johnson")]:
        score = name_match_components(i, j)
        assert score.best < 0.6


def test_empty_strings():
    from africapep.pipeline.scoring import name_match_components

    score_left = name_match_components("", "Peter Parker")
    assert score_left.best == 0.0

    score_right = name_match_components("Nelson Mandela", "")
    assert score_right.best == 0.0

    score_both = name_match_components("", "")
    assert score_both.best == 1.0


def test_single_word_names():
    from africapep.pipeline.scoring import name_match_components

    exact_score = name_match_components("Marie", "Marie")
    assert exact_score.best == 1.0

    typo_score = name_match_components("Nelson", "Nelcom")
    assert typo_score.best >= 0.8

    different_score = name_match_components("Nelson", "John")
    assert different_score.best < 0.5
