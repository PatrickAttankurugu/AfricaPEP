"""Measure Wikidata PEP coverage lift per country.

Compares the *baseline* catchment (positions tied to a country via P17 only --
the original scraper behaviour) against the *expanded* catchment (P17, plus
applies-to-jurisdiction P1001, plus citizens holding a public office) for one
or more countries. Reports distinct-principal counts and the percentage lift.

This queries the live Wikidata SPARQL endpoint with COUNT(DISTINCT ?person),
so it measures the reachable ceiling of distinct office-holders -- not relatives
or associates, which the pipeline adds downstream.

Usage:
    python -m scripts.measure_coverage                # the 6 low-coverage tail
    python -m scripts.measure_coverage GW ST DJ       # specific countries
    python -m scripts.measure_coverage --all          # all 54 countries

Note: the expanded query walks position subclasses (P279*) and can take 30-120s
per country; be patient and polite. Run sparingly.
"""
from __future__ import annotations

import argparse
import os
import sys
import time
import urllib.parse
import urllib.request
import json
from typing import Optional

# Allow running both as ``python -m scripts.measure_coverage`` and directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from africapep.scraper.spiders.wikidata_scraper import (
    COUNTRY_QIDS,
    PUBLIC_OFFICE_QID,
)

SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"
USER_AGENT = (
    "AfricaPEP-coverage/1.0 "
    "(https://github.com/PatrickAttankurugu/AfricaPEP; measure_coverage.py)"
)

# The six lowest-coverage countries (default target set).
DEFAULT_COUNTRIES = ["GW", "ST", "DJ", "LS", "SC", "ER"]


def _baseline_where(qid: str) -> str:
    """Distinct people whose position is tied to the country via P17 (original)."""
    return f"?x wdt:P39 ?p . ?p wdt:P17 wd:{qid}"


def _expanded_where(qid: str) -> str:
    """Distinct people reachable via P17, P1001, or citizen + public office."""
    return (
        f"{{ ?x wdt:P39 ?p . {{ ?p wdt:P17 wd:{qid} }} "
        f"UNION {{ ?p wdt:P1001 wd:{qid} }} }} "
        f"UNION {{ ?x wdt:P27 wd:{qid} ; wdt:P39 ?p . "
        f"?p wdt:P279* wd:{PUBLIC_OFFICE_QID} }}"
    )


def _run_count(where: str, tries: int = 4) -> Optional[int]:
    """Run a COUNT(DISTINCT ?x) query, retrying on transient errors."""
    query = f"SELECT (COUNT(DISTINCT ?x) AS ?c) WHERE {{ {where} }}"
    url = SPARQL_ENDPOINT + "?" + urllib.parse.urlencode({"query": query})
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/sparql-results+json",
            "User-Agent": USER_AGENT,
        },
    )
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                data = json.load(resp)
            return int(data["results"]["bindings"][0]["c"]["value"])
        except Exception as exc:  # noqa: BLE001
            if attempt == tries - 1:
                print(f"    ! query failed: {type(exc).__name__}", file=sys.stderr)
                return None
            time.sleep(5 * (attempt + 1))
    return None


def measure(codes: list[str]) -> None:
    header = f"{'Country':10} {'baseline(P17)':>14} {'expanded':>10} {'lift':>8}"
    print(header)
    print("-" * len(header))
    for code in codes:
        code = code.upper()
        qid = COUNTRY_QIDS.get(code)
        if not qid:
            print(f"{code:10} {'unknown country code':>33}")
            continue
        base = _run_count(_baseline_where(qid))
        time.sleep(2)
        exp = _run_count(_expanded_where(qid))
        time.sleep(2)
        if base is None or exp is None:
            print(f"{code:10} {str(base):>14} {str(exp):>10} {'ERR':>8}")
            continue
        lift = f"+{round((exp - base) / base * 100)}%" if base else "n/a"
        print(f"{code:10} {base:>14} {exp:>10} {lift:>8}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("countries", nargs="*", help="ISO alpha-2 codes")
    parser.add_argument("--all", action="store_true", help="measure all 54 countries")
    args = parser.parse_args()

    if args.all:
        codes = sorted(COUNTRY_QIDS.keys())
    elif args.countries:
        codes = args.countries
    else:
        codes = DEFAULT_COUNTRIES
    measure(codes)


if __name__ == "__main__":
    main()
