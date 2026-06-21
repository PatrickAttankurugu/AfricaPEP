"""Phonetic name matching for cross-spelling / transliteration variants.

Orthographic edit distance (Levenshtein, Jaro-Winkler) cannot tell that
"Mohammed" / "Muhammad" / "Mohamed" or "Diallo" / "Jallow" are the same name
spelled differently. Phonetic encoding maps names that *sound* alike to the
same key, recovering those matches.

Algorithm: Metaphone as the primary code, with Soundex as a complementary
"alternate" code (the installed ``jellyfish`` build does not ship Double
Metaphone). Comparing token sets across both codes approximates the
primary+alternate recall of Double Metaphone while staying pure-Python with no
new infrastructure.

Token-aware: each name token is encoded separately and compared as a set,
because name word order varies across cultures (surname-first vs given-first).
"""
from __future__ import annotations

import jellyfish

from africapep.pipeline.normaliser import _transliterate_name


def _tokens(name: str) -> list[str]:
    """Lower-cased, ASCII-folded, alphabetic-only tokens of a name."""
    folded = _transliterate_name(name or "").lower()
    return [t for t in folded.replace("-", " ").split() if t.isalpha()]


def _encode_token(token: str) -> tuple[str, str]:
    """Return (metaphone, soundex) codes for a single token.

    Either code may be empty for tokens jellyfish cannot encode; callers treat
    empty codes as non-matching.
    """
    try:
        primary = jellyfish.metaphone(token)
    except Exception:  # noqa: BLE001 - never let encoding crash a match
        primary = ""
    try:
        alternate = jellyfish.soundex(token)
    except Exception:  # noqa: BLE001
        alternate = ""
    return primary, alternate


def phonetic_keys(name: str) -> list[tuple[str, str]]:
    """Return (metaphone, soundex) phonetic keys per token of *name*.

    Empty list for blank / punctuation-only names.
    """
    return [_encode_token(t) for t in _tokens(name)]


def _tokens_match(a: tuple[str, str], b: tuple[str, str]) -> bool:
    """Two encoded tokens match if either code agrees (and is non-empty)."""
    return bool((a[0] and a[0] == b[0]) or (a[1] and a[1] == b[1]))


def phonetic_similarity(a: str, b: str) -> float:
    """Return a 0.0-1.0 phonetic similarity between two names.

    Greedy one-to-one alignment of tokens (each token used at most once),
    normalised by the larger token count so that extra tokens on one side
    reduce the score. Returns 0.0 when either name has no encodable tokens.
    """
    keys_a = phonetic_keys(a)
    keys_b = phonetic_keys(b)
    if not keys_a or not keys_b:
        return 0.0

    unmatched_b = list(keys_b)
    matched = 0
    for ka in keys_a:
        for i, kb in enumerate(unmatched_b):
            if _tokens_match(ka, kb):
                matched += 1
                unmatched_b.pop(i)
                break

    return matched / max(len(keys_a), len(keys_b))
