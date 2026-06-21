"""Regression guard for name-matching quality.

Runs the evaluation harness on the committed labeled-pair fixture and asserts
metrics do not regress below baseline floors. Floors are set just under the
values measured at implementation time, so a real degradation fails CI while
normal variation does not.
"""
import importlib.util
import os
import sys

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load_harness():
    path = os.path.join(_ROOT, "scripts", "eval_name_matching.py")
    spec = importlib.util.spec_from_file_location("eval_name_matching", path)
    module = importlib.util.module_from_spec(spec)
    # Register before exec so dataclass field resolution can find the module.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def results():
    harness = _load_harness()
    return harness.evaluate(harness.builtin_pairs())


def test_screening_recall_floor(results):
    # Screening is recall-first: it must catch (nearly) all true matches.
    assert results["screening_best"].recall >= 0.95


def test_phonetic_never_reduces_screening_recall(results):
    assert results["screening_best"].recall >= results["screening_orthographic"].recall


def test_phonetic_recovers_variants_at_high_threshold(results):
    # The core phonetic win: at a high precision threshold, orthographic misses
    # transliteration variants that phonetic recovers.
    assert results["high_best"].recall > results["high_orthographic"].recall
    assert results["high_best"].recall >= 0.95


def test_merge_gate_precision_floor(results):
    # Guard the over-merge fix: the orthographic merge gate must stay precise.
    assert results["merge_orthographic"].precision >= 0.85


def test_phonetic_alone_is_not_safe_to_merge(results):
    # Documents WHY resolution requires corroboration: phonetic alone produces
    # at least one false merge on the labeled set.
    assert results["merge_phonetic_alone"].fp >= 1
