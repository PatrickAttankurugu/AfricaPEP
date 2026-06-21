"""Name-matching scorer exposing orthographic and phonetic sub-scores.

Two callers consume this with opposite error costs:
- Screening (AML) is recall-first: a missed PEP is a compliance failure, so it
  uses the *best* of the sub-scores to surface more candidates for review.
- Entity resolution is precision-first at the auto-merge line: it requires
  orthographic agreement, or phonetic agreement corroborated by another signal,
  before merging -- so a phonetic-only coincidence never collapses two distinct
  people.

Exposing the components (rather than one blended number) lets each caller apply
its own policy. ``hybrid_name_score`` is retained, unchanged, as the
orthographic score so existing callers keep their exact behaviour.
"""
from dataclasses import dataclass

from rapidfuzz import fuzz
from rapidfuzz.distance import JaroWinkler

from africapep.pipeline.phonetic import phonetic_similarity


@dataclass(frozen=True)
class NameMatchScore:
    """Component sub-scores for a name pair, each normalised 0.0-1.0."""
    orthographic: float
    phonetic: float

    @property
    def best(self) -> float:
        """Recall-first combined score: the stronger of the two signals."""
        return max(self.orthographic, self.phonetic)


def _orthographic_score(name_a: str, name_b: str) -> float:
    """Best of Levenshtein token-sort and Jaro-Winkler, normalised 0.0-1.0.

    Token-sort handles word reordering; Jaro-Winkler handles prefix typos and
    short-name variation.
    """
    levenshtein = fuzz.token_sort_ratio(name_a, name_b) / 100.0
    jaro_winkler = JaroWinkler.similarity(name_a.lower(), name_b.lower())
    return max(levenshtein, jaro_winkler)


def name_match_components(name_a: str, name_b: str) -> NameMatchScore:
    """Return orthographic and phonetic sub-scores for a name pair."""
    return NameMatchScore(
        orthographic=_orthographic_score(name_a, name_b),
        phonetic=phonetic_similarity(name_a, name_b),
    )


def hybrid_name_score(name_a: str, name_b: str) -> float:
    """Orthographic name similarity, 0.0-1.0 (unchanged legacy behaviour).

    Retained for backward compatibility: equal to
    ``name_match_components(a, b).orthographic``.
    """
    return _orthographic_score(name_a, name_b)
