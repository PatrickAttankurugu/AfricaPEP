"""Evaluate name-matching quality on QID-grounded labeled pairs.

Ground truth comes from Wikidata QIDs: name variants that share a QID are the
same person (positive pairs); names under different QIDs are different people
(negative pairs). The hardest -- and most informative -- negatives are different
people in the *same blocking bucket* (country + surname initial), which is
exactly where entity resolution confuses people.

Reports, for both the orthographic-only baseline and the orthographic+phonetic
policy:
  - precision / recall / F1 at a screening threshold,
  - a precision-recall curve across thresholds,
  - merge-precision: of pairs a merge rule would auto-merge, the fraction that
    are truly the same person. Compares the name-only orthographic merge gate
    against a phonetic-alone gate, showing why resolution requires corroboration
    (phonetic alone is lower-precision).

Run:
    python -m scripts.eval_name_matching                 # built-in fixture set
    python -m scripts.eval_name_matching pairs.json      # custom labeled pairs
where pairs.json is a list of {"a": str, "b": str, "same": bool}.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from africapep.pipeline.scoring import name_match_components  # noqa: E402

# Thresholds mirrored from the resolver so the harness measures the real rules.
MERGE_THRESHOLD = 0.85
PHONETIC_MERGE_THRESHOLD = 0.90
SCREENING_THRESHOLD = 0.75
# A high precision threshold where transliteration variants fall just below the
# orthographic bar; phonetic recovers them here.
HIGH_THRESHOLD = 0.90


@dataclass
class Pair:
    a: str
    b: str
    same: bool


@dataclass
class Metrics:
    precision: float
    recall: float
    f1: float
    tp: int
    fp: int
    fn: int
    tn: int


def _metrics(pairs: list[Pair], predict_same) -> Metrics:
    tp = fp = fn = tn = 0
    for p in pairs:
        pred = predict_same(p.a, p.b)
        if pred and p.same:
            tp += 1
        elif pred and not p.same:
            fp += 1
        elif not pred and p.same:
            fn += 1
        else:
            tn += 1
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)
          if (precision + recall) else 0.0)
    return Metrics(precision, recall, f1, tp, fp, fn, tn)


def evaluate(pairs: list[Pair]) -> dict:
    """Compute the full metric set used by both the report and the test."""
    ortho = lambda a, b: name_match_components(a, b).orthographic  # noqa: E731
    phon = lambda a, b: name_match_components(a, b).phonetic  # noqa: E731
    best = lambda a, b: name_match_components(a, b).best  # noqa: E731

    return {
        # Screening: recall-first. Baseline vs orthographic+phonetic.
        "screening_orthographic": _metrics(
            pairs, lambda a, b: ortho(a, b) >= SCREENING_THRESHOLD),
        "screening_best": _metrics(
            pairs, lambda a, b: best(a, b) >= SCREENING_THRESHOLD),
        # At a high precision threshold, phonetic recovers transliteration
        # variants that fall just below the orthographic bar.
        "high_orthographic": _metrics(
            pairs, lambda a, b: ortho(a, b) >= HIGH_THRESHOLD),
        "high_best": _metrics(
            pairs, lambda a, b: best(a, b) >= HIGH_THRESHOLD),
        # Merge gates: orthographic name gate vs phonetic-alone gate.
        "merge_orthographic": _metrics(
            pairs, lambda a, b: ortho(a, b) >= MERGE_THRESHOLD),
        "merge_phonetic_alone": _metrics(
            pairs, lambda a, b: phon(a, b) >= PHONETIC_MERGE_THRESHOLD),
    }


def _pr_curve(pairs: list[Pair], score_fn) -> list[tuple[float, float, float]]:
    out = []
    for t in [i / 20 for i in range(10, 21)]:  # 0.50 .. 1.00
        m = _metrics(pairs, lambda a, b: score_fn(a, b) >= t)
        out.append((t, m.precision, m.recall))
    return out


def builtin_pairs() -> list[Pair]:
    """Load the committed fixture pairs shared with the regression test."""
    fixture = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "tests", "fixtures", "name_match_pairs.json",
    )
    with open(fixture, encoding="utf-8") as f:
        data = json.load(f)
    return [Pair(d["a"], d["b"], d["same"]) for d in data]


def _print_metrics(label: str, m: Metrics) -> None:
    print(f"  {label:24} P={m.precision:.3f} R={m.recall:.3f} "
          f"F1={m.f1:.3f}  (tp={m.tp} fp={m.fp} fn={m.fn} tn={m.tn})")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pairs", nargs="?", help="JSON file of labeled pairs")
    args = parser.parse_args()

    if args.pairs:
        with open(args.pairs, encoding="utf-8") as f:
            data = json.load(f)
        pairs = [Pair(d["a"], d["b"], d["same"]) for d in data]
    else:
        pairs = builtin_pairs()

    pos = sum(1 for p in pairs if p.same)
    print(f"Evaluating {len(pairs)} pairs ({pos} same, {len(pairs) - pos} different)\n")

    res = evaluate(pairs)
    print("Screening (recall-first, threshold {:.2f}):".format(SCREENING_THRESHOLD))
    _print_metrics("orthographic only", res["screening_orthographic"])
    _print_metrics("orthographic+phonetic", res["screening_best"])

    print("\nHigh threshold {:.2f} (phonetic recovers transliteration variants):"
          .format(HIGH_THRESHOLD))
    _print_metrics("orthographic only", res["high_orthographic"])
    _print_metrics("orthographic+phonetic", res["high_best"])

    print("\nMerge gates (precision-first):")
    _print_metrics("orthographic >= 0.85", res["merge_orthographic"])
    _print_metrics("phonetic-alone >= 0.90", res["merge_phonetic_alone"])
    print("  -> phonetic-alone precision is why resolution requires corroboration.")

    print("\nPR curve (orthographic+phonetic best):")
    for t, p, r in _pr_curve(pairs, lambda a, b: name_match_components(a, b).best):
        print(f"  t={t:.2f}  P={p:.3f}  R={r:.3f}")


if __name__ == "__main__":
    main()
