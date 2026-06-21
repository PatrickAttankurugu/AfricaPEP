"""Probabilistic record linkage for cross-QID duplicate Person records.

The incremental resolver dedupes within a scrape run and (since the stable-id
fix) collapses same-QID records. What remains are *cross-QID* duplicates -- two
different Wikidata items that are the same human -- and no-QID records. This
module scores Person pairs with calibrated Fellegi-Sunter match probabilities
(Splink, DuckDB backend) and applies an AML-safe action policy.

Two layers, deliberately separated:
- **Policy** (``classify_pair`` / ``is_corroborated`` / ``decide_pairs``): pure
  Python, no Splink, unit-testable without the heavy dependency. Routes a
  (probability, corroboration) pair to AUTO_MERGE / REVIEW / IGNORE.
- **Model** (``prepare_dataframe`` / ``train_linker`` / ``predict_pairs``):
  imports Splink and pandas lazily, so importing this module for the policy
  layer never requires the optional dependency.

Splink is an OFFLINE batch dependency (see ``requirements-dedup.txt``); it is
never installed in the runtime service image.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from rapidfuzz import fuzz

from africapep.config import settings
from africapep.pipeline.phonetic import phonetic_keys

# Position similarity that counts as corroborating a name match (mirrors the
# incremental resolver's POSITION_CORROBORATION).
POSITION_CORROBORATION = 0.85


class PairAction(str, Enum):
    AUTO_MERGE = "AUTO_MERGE"
    REVIEW = "REVIEW"
    IGNORE = "IGNORE"


@dataclass(frozen=True)
class PairDecision:
    id_a: str
    id_b: str
    probability: float
    corroborated: bool
    action: PairAction


# ── Policy layer (pure; no Splink) ──

def classify_pair(
    probability: float,
    corroborated: bool,
    *,
    automerge_prob: Optional[float] = None,
    review_prob: Optional[float] = None,
) -> PairAction:
    """Route a scored pair to an action under the AML-safe policy.

    - probability >= automerge_prob AND corroborated -> AUTO_MERGE
    - probability >= review_prob (incl. high-prob but uncorroborated) -> REVIEW
    - otherwise -> IGNORE
    """
    automerge_prob = (settings.splink_automerge_prob
                      if automerge_prob is None else automerge_prob)
    review_prob = (settings.splink_review_prob
                   if review_prob is None else review_prob)

    if probability >= automerge_prob and corroborated:
        return PairAction.AUTO_MERGE
    if probability >= review_prob:
        return PairAction.REVIEW
    return PairAction.IGNORE


def is_corroborated(row_a: dict, row_b: dict) -> bool:
    """True if DOB or a held position independently agrees between two rows.

    ``row_*`` are flat dicts with ``date_of_birth`` and ``position`` keys
    (``position`` = a representative "title @ institution" string, possibly
    empty). Mirrors the incremental resolver's corroboration rule so the two
    resolution paths agree on what "a second signal" means.
    """
    dob_a = (row_a.get("date_of_birth") or "").strip()
    dob_b = (row_b.get("date_of_birth") or "").strip()
    if dob_a and dob_b and dob_a == dob_b:
        return True

    pos_a = (row_a.get("position") or "").strip()
    pos_b = (row_b.get("position") or "").strip()
    if pos_a and pos_b:
        if fuzz.token_sort_ratio(pos_a, pos_b) / 100.0 >= POSITION_CORROBORATION:
            return True

    return False


def decide_pairs(pairs, rows_by_id, **thresholds) -> list[PairDecision]:
    """Classify scored pairs into actions.

    Args:
        pairs: iterable of (id_a, id_b, probability).
        rows_by_id: mapping id -> flat row dict (for corroboration lookup).
        thresholds: optional automerge_prob / review_prob overrides.
    """
    decisions: list[PairDecision] = []
    for id_a, id_b, prob in pairs:
        row_a = rows_by_id.get(id_a, {})
        row_b = rows_by_id.get(id_b, {})
        corro = is_corroborated(row_a, row_b)
        action = classify_pair(prob, corro, **thresholds)
        decisions.append(PairDecision(id_a, id_b, float(prob), corro, action))
    return decisions


# ── Feature helpers (pure; no Splink) ──

def metaphone_name_key(name: str) -> str:
    """Space-joined primary metaphone codes of a name's tokens ("" if none)."""
    return " ".join(primary for primary, _ in phonetic_keys(name) if primary)


def phonetic_surname_key(name: str) -> str:
    """Primary metaphone of the last token (surname), "" if none."""
    keys = phonetic_keys(name)
    return keys[-1][0] if keys else ""


# ── Model layer (lazy Splink import) ──

def prepare_dataframe(rows: list[dict]):
    """Build the Splink input DataFrame from flat Person rows.

    Each row needs: ``neo4j_id``, ``full_name``, ``date_of_birth``,
    ``nationality``, ``position``. Adds derived ``phonetic_surname`` and
    ``metaphone_name`` columns used by blocking and the phonetic comparison.
    """
    import pandas as pd

    records = []
    for r in rows:
        name = r.get("full_name") or ""
        records.append({
            "unique_id": r["neo4j_id"],
            "full_name": name,
            "date_of_birth": r.get("date_of_birth") or None,
            "nationality": r.get("nationality") or None,
            "position": r.get("position") or "",
            "phonetic_surname": phonetic_surname_key(name),
            "metaphone_name": metaphone_name_key(name),
        })
    return pd.DataFrame.from_records(records)


def build_settings():
    """Build the Splink SettingsCreator for dedupe_only linkage."""
    from splink import SettingsCreator, block_on
    import splink.comparison_library as cl
    import splink.comparison_level_library as cll

    name_comparison = cl.CustomComparison(
        output_column_name="full_name",
        comparison_levels=[
            cll.NullLevel("full_name"),
            cll.ExactMatchLevel("full_name"),
            cll.JaroWinklerLevel("full_name", 0.92),
            # Phonetic agreement: same metaphone encoding of the whole name.
            cll.ExactMatchLevel("metaphone_name"),
            cll.JaroWinklerLevel("full_name", 0.82),
            cll.ElseLevel(),
        ],
    )

    return SettingsCreator(
        link_type="dedupe_only",
        blocking_rules_to_generate_predictions=[
            block_on("nationality", "phonetic_surname"),
            block_on("date_of_birth"),
        ],
        comparisons=[
            name_comparison,
            cl.ExactMatch("date_of_birth"),
            cl.ExactMatch("nationality"),
        ],
        retain_intermediate_calculation_columns=True,
    )


def train_linker(df):
    """Train a Splink Linker on the prepared DataFrame and return it."""
    from splink import Linker, DuckDBAPI, block_on

    linker = Linker(df, build_settings(), db_api=DuckDBAPI())

    # Prior P(two random records match): estimate from deterministic rules so
    # we don't fall back to the 0.0001 default.
    linker.training.estimate_probability_two_random_records_match(
        ["l.full_name = r.full_name", "l.date_of_birth = r.date_of_birth"],
        recall=0.7,
    )
    linker.training.estimate_u_using_random_sampling(max_pairs=1e6)

    # EM with column-fixing blocking rules: fix one column so the others'
    # m-values are observed (a single naive EM rule leaves name untrained).
    linker.training.estimate_parameters_using_expectation_maximisation(
        block_on("date_of_birth")
    )
    linker.training.estimate_parameters_using_expectation_maximisation(
        block_on("phonetic_surname")
    )
    return linker


def predict_pairs(linker, threshold: Optional[float] = None):
    """Return a list of (id_a, id_b, probability) above the review threshold."""
    threshold = settings.splink_review_prob if threshold is None else threshold
    preds = linker.inference.predict(threshold_match_probability=threshold)
    pdf = preds.as_pandas_dataframe()
    return [
        (row.unique_id_l, row.unique_id_r, float(row.match_probability))
        for row in pdf.itertuples()
    ]
