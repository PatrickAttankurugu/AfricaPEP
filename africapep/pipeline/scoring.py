"""Hybrid name-matching scorer: Levenshtein + Jaro-Winkler.

Takes the max of token_sort_ratio (Levenshtein-based, handles word
reordering) and Jaro-Winkler similarity (handles prefix typos, short
name variations). This maximises recall for PEP screening — a name
pair only needs to score well on ONE algorithm to match.
"""
from rapidfuzz import fuzz
from rapidfuzz.distance import JaroWinkler


def hybrid_name_score(name_a: str, name_b: str) -> float:
    """Return the best of Levenshtein token-sort and Jaro-Winkler scores.

    Both scores are normalised to 0.0–1.0.
    """
    levenshtein = fuzz.token_sort_ratio(name_a, name_b) / 100.0
    jaro_winkler = JaroWinkler.similarity(name_a.lower(), name_b.lower())
    return max(levenshtein, jaro_winkler)
