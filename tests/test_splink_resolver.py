"""Tests for the Splink probabilistic dedup pass.

The policy layer is pure Python and always tested. The Splink model layer is
exercised only when Splink is installed (importorskip), since it is an offline
batch dependency kept out of the runtime image.
"""
import pytest

from africapep.pipeline.splink_resolver import (
    PairAction,
    classify_pair,
    is_corroborated,
    decide_pairs,
    metaphone_name_key,
    phonetic_surname_key,
)


# ── Policy layer (always runs) ──

def test_classify_pair_auto_merge_requires_corroboration():
    # High probability + corroboration -> auto-merge
    assert classify_pair(0.995, True, automerge_prob=0.99, review_prob=0.90) \
        == PairAction.AUTO_MERGE
    # High probability WITHOUT corroboration -> review, never auto-merge
    assert classify_pair(0.995, False, automerge_prob=0.99, review_prob=0.90) \
        == PairAction.REVIEW


def test_classify_pair_review_band():
    assert classify_pair(0.95, True, automerge_prob=0.99, review_prob=0.90) \
        == PairAction.REVIEW
    assert classify_pair(0.90, False, automerge_prob=0.99, review_prob=0.90) \
        == PairAction.REVIEW


def test_classify_pair_ignore_below_review():
    assert classify_pair(0.89, True, automerge_prob=0.99, review_prob=0.90) \
        == PairAction.IGNORE
    assert classify_pair(0.10, True) == PairAction.IGNORE


def test_is_corroborated_by_dob():
    a = {"date_of_birth": "1960-01-01", "position": ""}
    b = {"date_of_birth": "1960-01-01", "position": ""}
    assert is_corroborated(a, b) is True


def test_is_corroborated_by_position():
    a = {"date_of_birth": "", "position": "Minister of Finance @ Ministry"}
    b = {"date_of_birth": "", "position": "Minister of Finance @ Ministry"}
    assert is_corroborated(a, b) is True


def test_not_corroborated_when_signals_differ_or_missing():
    assert is_corroborated(
        {"date_of_birth": "1960-01-01", "position": "President @ Govt"},
        {"date_of_birth": "1975-05-05", "position": "Footballer @ Club"},
    ) is False
    # Missing on both sides cannot corroborate
    assert is_corroborated({"date_of_birth": "", "position": ""},
                           {"date_of_birth": "", "position": ""}) is False


def test_decide_pairs_routes_with_corroboration_lookup():
    rows = {
        "a": {"date_of_birth": "1942-12-17", "position": "President @ Govt"},
        "b": {"date_of_birth": "1942-12-17", "position": "President @ Govt"},
        "c": {"date_of_birth": "1990-01-01", "position": "Mayor @ City"},
    }
    decisions = decide_pairs(
        [("a", "b", 0.999), ("a", "c", 0.92)], rows,
        automerge_prob=0.99, review_prob=0.90,
    )
    by_pair = {(d.id_a, d.id_b): d for d in decisions}
    assert by_pair[("a", "b")].action == PairAction.AUTO_MERGE
    assert by_pair[("a", "b")].corroborated is True
    assert by_pair[("a", "c")].action == PairAction.REVIEW  # corro False, mid prob


def test_phonetic_feature_helpers():
    # Same-sounding surnames share a phonetic surname key
    assert phonetic_surname_key("Sory Kaba") == phonetic_surname_key("Sori Kabba")
    assert metaphone_name_key("Mohammed Buhari") == metaphone_name_key("Muhammad Buhari")
    assert phonetic_surname_key("") == ""
    assert metaphone_name_key("") == ""


# ── Model layer (requires Splink) ──

def test_splink_model_clusters_true_duplicates():
    pytest.importorskip("splink")
    from africapep.pipeline.splink_resolver import (
        prepare_dataframe, train_linker, predict_pairs,
    )

    rows = [
        {"neo4j_id": "wd:Q1", "full_name": "Mohammed Buhari",
         "date_of_birth": "1942-12-17", "nationality": "NG", "position": "President @ Govt"},
        {"neo4j_id": "wd:Q2", "full_name": "Muhammadu Buhari",
         "date_of_birth": "1942-12-17", "nationality": "NG", "position": "President @ Govt"},
        {"neo4j_id": "wd:Q3", "full_name": "Sory Kaba",
         "date_of_birth": "1960-01-01", "nationality": "GN", "position": "Director @ Govt"},
        {"neo4j_id": "wd:Q4", "full_name": "Sori Kabba",
         "date_of_birth": "1960-01-01", "nationality": "GN", "position": "Director @ Govt"},
        {"neo4j_id": "wd:Q5", "full_name": "Paul Biya",
         "date_of_birth": "1933-02-13", "nationality": "CM", "position": "President @ Govt"},
        {"neo4j_id": "wd:Q6", "full_name": "Franck Biya",
         "date_of_birth": "1971-01-01", "nationality": "CM", "position": "Businessman @ Co"},
        {"neo4j_id": "wd:Q7", "full_name": "Nelson Mandela",
         "date_of_birth": "1918-07-18", "nationality": "ZA", "position": "President @ Govt"},
        {"neo4j_id": "wd:Q8", "full_name": "Ellen Johnson",
         "date_of_birth": "1938-10-29", "nationality": "LR", "position": "President @ Govt"},
    ]
    import warnings
    warnings.filterwarnings("ignore")
    df = prepare_dataframe(rows)
    linker = train_linker(df)
    pairs = predict_pairs(linker, threshold=0.5)
    matched = {tuple(sorted((a, b))) for a, b, _ in pairs}

    # True cross-spelling duplicates must be linked.
    assert ("wd:Q1", "wd:Q2") in matched, "Buhari variants should link"
    assert ("wd:Q3", "wd:Q4") in matched, "Kaba variants should link"
    # Distinct people must NOT be linked.
    assert ("wd:Q5", "wd:Q6") not in matched, "Paul/Franck Biya must not merge"
    assert ("wd:Q7", "wd:Q8") not in matched, "unrelated must not merge"
