"""Tests for scraper base classes and WikidataScraper."""
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

import pytest


# ── RawPersonRecord ──

def test_raw_person_record_fields():
    from africapep.scraper.base_scraper import RawPersonRecord

    r = RawPersonRecord(
        full_name="Kwame Mensah",
        title="MP",
        institution="Parliament of Ghana",
        country_code="GH",
        source_url="https://parliament.gh",
        source_type="PARLIAMENT",
        raw_text="Kwame Mensah MP for Accra",
        scraped_at=datetime.now(timezone.utc),
        extra_fields={"party": "NDC"},
    )
    assert r.full_name == "Kwame Mensah"
    assert r.country_code == "GH"
    assert r.extra_fields["party"] == "NDC"
    assert isinstance(r.scraped_at, datetime)


def test_raw_person_record_defaults():
    from africapep.scraper.base_scraper import RawPersonRecord

    r = RawPersonRecord(
        full_name="Test",
        title="",
        institution="",
        country_code="GH",
        source_url="http://example.com",
        source_type="TEST",
        raw_text="",
        scraped_at=datetime.now(timezone.utc),
    )
    assert r.extra_fields == {}


# ── BaseScraper ──

def test_base_scraper_is_abstract():
    import inspect
    from africapep.scraper.base_scraper import BaseScraper

    assert inspect.isabstract(BaseScraper)


def test_base_scraper_cannot_instantiate():
    from africapep.scraper.base_scraper import BaseScraper

    with pytest.raises(TypeError):
        BaseScraper()


# ── WikidataScraper ──

def test_wikidata_scraper_init():
    from africapep.scraper.spiders.wikidata_scraper import WikidataScraper

    scraper = WikidataScraper(country_code="GH")
    assert scraper.country_code == "GH"
    assert scraper.source_type == "WIKIDATA"


def test_wikidata_scraper_invalid_country():
    from africapep.scraper.spiders.wikidata_scraper import WikidataScraper

    with pytest.raises(ValueError, match="Unknown country code"):
        WikidataScraper(country_code="XX")


def test_wikidata_scraper_case_insensitive():
    from africapep.scraper.spiders.wikidata_scraper import WikidataScraper

    scraper = WikidataScraper(country_code="ng")
    assert scraper.country_code == "NG"


def test_wikidata_scraper_all_54_countries():
    from africapep.scraper.spiders.wikidata_scraper import COUNTRY_QIDS

    assert len(COUNTRY_QIDS) == 54, "Should cover all 54 African countries"
    # Spot check some countries
    assert "NG" in COUNTRY_QIDS  # Nigeria
    assert "GH" in COUNTRY_QIDS  # Ghana
    assert "ZA" in COUNTRY_QIDS  # South Africa
    assert "KE" in COUNTRY_QIDS  # Kenya
    assert "EG" in COUNTRY_QIDS  # Egypt


def test_wikidata_scraper_query_build():
    from africapep.scraper.spiders.wikidata_scraper import _build_query

    query = _build_query("Q1033")  # Nigeria
    assert "Q1033" in query
    assert "SELECT" in query
    assert "personLabel" in query
    assert "positionLabel" in query


def test_get_uses_configurable_request_timeout():
    """_get passes the instance request_timeout to session.get, not a hardcoded value."""
    from africapep.scraper.spiders.wikidata_scraper import WikidataScraper

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"results": {"bindings": []}}

    with patch("africapep.scraper.spiders.wikidata_scraper.time.sleep"), \
         patch("africapep.scraper.base_scraper.time.sleep"):
        scraper = WikidataScraper(country_code="GH")
        scraper.request_timeout = 90
        scraper.session.get = MagicMock(return_value=mock_response)
        scraper._get("https://example.com/sparql")

    _, kwargs = scraper.session.get.call_args
    assert kwargs.get("timeout") == 90, "should pass the instance request_timeout through"


def test_wikidata_scraper_uses_longer_sparql_timeout():
    """The Wikidata scraper needs a longer timeout than the base default.

    The citizenship/office-class branch runs a P279* subclass walk that takes
    far longer than the 30s base timeout, so it must use the dedicated longer
    SPARQL timeout or it always times out (Branch C dropped in production).
    """
    from africapep.scraper.base_scraper import BaseScraper
    from africapep.scraper.spiders.wikidata_scraper import WikidataScraper

    scraper = WikidataScraper(country_code="GH")
    assert scraper.request_timeout > BaseScraper.request_timeout
    assert scraper.request_timeout >= 90


def test_wikidata_jurisdiction_query_uses_p1001():
    from africapep.scraper.spiders.wikidata_scraper import _build_jurisdiction_query

    query = _build_jurisdiction_query("Q1007")  # Guinea-Bissau
    assert "wdt:P1001 wd:Q1007" in query
    assert "personLabel" in query


def test_wikidata_citizenship_query_uses_p27_and_returns_position():
    from africapep.scraper.spiders.wikidata_scraper import _build_citizenship_query

    query = _build_citizenship_query("Q986")  # Eritrea
    assert "wdt:P27 wd:Q986" in query
    # The position QID must be selectable so it can be office-class filtered
    assert "?position " in query


def test_wikidata_office_class_filter():
    from africapep.scraper.spiders.wikidata_scraper import (
        _build_office_class_filter,
        PUBLIC_OFFICE_QID,
    )

    query = _build_office_class_filter(["Q30461", "Q83307"])
    assert "VALUES ?position" in query
    assert "wd:Q30461" in query and "wd:Q83307" in query
    assert f"wdt:P279* wd:{PUBLIC_OFFICE_QID}" in query


def test_wikidata_queries_are_multilingual():
    from africapep.scraper.spiders.wikidata_scraper import (
        _build_query,
        _build_jurisdiction_query,
        _build_citizenship_query,
        LABEL_LANGS,
    )

    # English must remain first so Latin/searchable names win
    assert LABEL_LANGS.startswith("en")
    for q in (_build_query("Q1"), _build_jurisdiction_query("Q1"),
              _build_citizenship_query("Q1")):
        assert f'wikibase:language "{LABEL_LANGS}"' in q


def _sparql_response(bindings):
    """Build a mock requests.Response carrying SPARQL JSON bindings."""
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {"results": {"bindings": bindings}}
    return resp


def test_wikidata_multi_branch_merges_and_office_filters():
    """All three branches merge; citizenship branch keeps only public offices."""
    import urllib.parse
    from africapep.scraper.spiders.wikidata_scraper import WikidataScraper

    ent = "http://www.wikidata.org/entity/"
    branch_a = [{
        "person": {"value": ent + "Q1"},
        "personLabel": {"value": "Alpha ViaP17"},
        "positionLabel": {"value": "President"},
    }]
    branch_b = [{
        "person": {"value": ent + "Q2"},
        "personLabel": {"value": "Beta ViaP1001"},
        "positionLabel": {"value": "Minister of Finance"},
    }]
    citizen_candidates = [
        {  # holds a public office -> should be kept
            "person": {"value": ent + "Q3"},
            "position": {"value": ent + "Q100"},
            "personLabel": {"value": "Gamma Citizen"},
            "positionLabel": {"value": "Senator"},
        },
        {  # holds a non-office position -> should be dropped
            "person": {"value": ent + "Q4"},
            "position": {"value": ent + "Q200"},
            "personLabel": {"value": "Delta Athlete"},
            "positionLabel": {"value": "Footballer"},
        },
    ]
    office_class = [{"position": {"value": ent + "Q100"}}]  # only Q100 is a public office

    def dispatch(url, timeout=None):
        q = urllib.parse.unquote(url)
        if "P279" in q:
            return _sparql_response(office_class)
        if "P106" in q:
            return _sparql_response([])  # Branch D: no occupation-only people
        if "P1001" in q:
            return _sparql_response(branch_b)
        if "wdt:P27" in q:
            return _sparql_response(citizen_candidates)
        return _sparql_response(branch_a)  # P17 baseline

    with patch("africapep.scraper.base_scraper.time.sleep"), \
         patch("africapep.scraper.spiders.wikidata_scraper.time.sleep"):
        scraper = WikidataScraper(country_code="GW")
        scraper.session.get = MagicMock(side_effect=dispatch)
        records = scraper.scrape()

    names = sorted(r.full_name for r in records)
    assert names == ["Alpha ViaP17", "Beta ViaP1001", "Gamma Citizen"]
    # The footballer (non-public-office citizen) must be excluded
    assert "Delta Athlete" not in names


def test_wikidata_keyword_fallback_recovers_unclassed_offices():
    """Citizens whose position fails the P279 walk are kept when the label is
    clearly political (small-country ontology gaps), but noise stays out."""
    import urllib.parse
    from africapep.scraper.spiders.wikidata_scraper import WikidataScraper

    ent = "http://www.wikidata.org/entity/"
    citizen_candidates = [
        {  # political label, NOT in office_class -> recovered by keyword fallback
            "person": {"value": ent + "Q10"},
            "position": {"value": ent + "Q300"},
            "personLabel": {"value": "Epsilon President"},
            "positionLabel": {"value": "Vice President of the Comoros"},
        },
        {  # monarch, NOT in office_class -> recovered (new monarch keywords)
            "person": {"value": ent + "Q11"},
            "position": {"value": ent + "Q301"},
            "personLabel": {"value": "Zeta Monarch"},
            "positionLabel": {"value": "King of Eswatini"},
        },
        {  # matches 'ambassador' keyword but denylisted -> dropped
            "person": {"value": ent + "Q12"},
            "position": {"value": ent + "Q302"},
            "personLabel": {"value": "Eta Goodwill"},
            "positionLabel": {"value": "NEF ambassador"},
        },
        {  # no political keyword at all -> dropped
            "person": {"value": ent + "Q13"},
            "position": {"value": ent + "Q303"},
            "personLabel": {"value": "Theta Referee"},
            "positionLabel": {"value": "FIFA referee"},
        },
    ]

    def dispatch(url, timeout=None):
        q = urllib.parse.unquote(url)
        if "P279" in q:
            return _sparql_response([])  # ontology knows none of them
        if "P106" in q:
            return _sparql_response([])
        if "wdt:P27" in q:
            return _sparql_response(citizen_candidates)
        return _sparql_response([])  # branches A/B empty

    with patch("africapep.scraper.base_scraper.time.sleep"), \
         patch("africapep.scraper.spiders.wikidata_scraper.time.sleep"):
        scraper = WikidataScraper(country_code="KM")
        scraper.session.get = MagicMock(side_effect=dispatch)
        records = scraper.scrape()

    names = sorted(r.full_name for r in records)
    assert names == ["Epsilon President", "Zeta Monarch"]


def test_wikidata_occupation_politician_branch():
    """Branch D: occupation=politician with no P39 lands with title Politician."""
    import urllib.parse
    from africapep.scraper.spiders.wikidata_scraper import WikidataScraper

    ent = "http://www.wikidata.org/entity/"
    occupation_only = [{
        "person": {"value": ent + "Q20"},
        "personLabel": {"value": "Iota OccupationOnly"},
        "dob": {"value": "1970-05-01T00:00:00Z"},
    }]

    def dispatch(url, timeout=None):
        q = urllib.parse.unquote(url)
        if "P106" in q:
            return _sparql_response(occupation_only)
        return _sparql_response([])

    with patch("africapep.scraper.base_scraper.time.sleep"), \
         patch("africapep.scraper.spiders.wikidata_scraper.time.sleep"):
        scraper = WikidataScraper(country_code="ER")
        scraper.session.get = MagicMock(side_effect=dispatch)
        records = scraper.scrape()

    assert len(records) == 1
    assert records[0].full_name == "Iota OccupationOnly"
    assert records[0].title == "Politician"
    assert records[0].extra_fields["wikidata_qid"] == "Q20"
    assert records[0].extra_fields["date_of_birth"] == "1970-05-01"


def test_wikidata_office_class_batch_splits_on_failure():
    """A failing office-class batch is retried as two halves, not dropped."""
    from africapep.scraper.spiders.wikidata_scraper import WikidataScraper

    ent = "http://www.wikidata.org/entity/"
    calls = {"n": 0}

    def fake_run_query(query):
        calls["n"] += 1
        if calls["n"] == 1:
            raise Exception("504 Server Error")  # full batch times out
        # halves succeed; echo back whichever QIDs were asked for
        asked = [q for q in ("Q1", "Q2", "Q3", "Q4") if f"wd:{q}" in query]
        return {"results": {"bindings": [
            {"position": {"value": ent + q}} for q in asked
        ]}}

    with patch("africapep.scraper.base_scraper.time.sleep"), \
         patch("africapep.scraper.spiders.wikidata_scraper.time.sleep"):
        scraper = WikidataScraper(country_code="GM")
        scraper._run_query = fake_run_query
        office = scraper._fetch_office_class_qids({"Q1", "Q2", "Q3", "Q4"})

    assert office == {"Q1", "Q2", "Q3", "Q4"}
    assert calls["n"] == 3  # 1 failed full batch + 2 successful halves


def test_wikidata_branch_failure_does_not_regress_baseline():
    """If a broad branch fails, the P17 baseline branch still returns results."""
    import urllib.parse
    from africapep.scraper.spiders.wikidata_scraper import WikidataScraper

    ent = "http://www.wikidata.org/entity/"
    branch_a = [{
        "person": {"value": ent + "Q1"},
        "personLabel": {"value": "Alpha ViaP17"},
        "positionLabel": {"value": "President"},
    }]

    def dispatch(url, timeout=None):
        q = urllib.parse.unquote(url)
        if "wdt:P17" in q and "P1001" not in q and "wdt:P27" not in q:
            return _sparql_response(branch_a)
        raise Exception("branch unavailable")  # B and C blow up

    with patch("africapep.scraper.base_scraper.time.sleep"), \
         patch("africapep.scraper.spiders.wikidata_scraper.time.sleep"):
        scraper = WikidataScraper(country_code="GW")
        scraper.session.get = MagicMock(side_effect=dispatch)
        records = scraper.scrape()

    # Baseline coverage preserved despite the other branches failing
    assert [r.full_name for r in records] == ["Alpha ViaP17"]


def test_wikidata_scraper_parse_date():
    from africapep.scraper.spiders.wikidata_scraper import _parse_date

    assert _parse_date("2023-05-29T00:00:00Z") == "2023-05-29"
    assert _parse_date(None) is None
    assert _parse_date("") is None


def test_wikidata_scraper_scrape_with_mock():
    from africapep.scraper.spiders.wikidata_scraper import WikidataScraper

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "results": {
            "bindings": [
                {
                    "personLabel": {"value": "Bola Tinubu", "type": "literal"},
                    "positionLabel": {"value": "President of Nigeria", "type": "literal"},
                    "institutionLabel": {"value": "Federal Government of Nigeria", "type": "literal"},
                },
                {
                    "personLabel": {"value": "Godswill Akpabio", "type": "literal"},
                    "positionLabel": {"value": "President of the Senate", "type": "literal"},
                    "institutionLabel": {"value": "National Assembly", "type": "literal"},
                    "start": {"value": "2023-06-13T00:00:00Z"},
                    "dob": {"value": "1962-12-09T00:00:00Z"},
                },
                {
                    "personLabel": {"value": "Q12345", "type": "literal"},
                    "positionLabel": {"value": "Some Position", "type": "literal"},
                },
            ]
        }
    }

    with patch("africapep.scraper.spiders.wikidata_scraper.time.sleep"), \
         patch("africapep.scraper.base_scraper.time.sleep"):
        scraper = WikidataScraper(country_code="NG")
        scraper.session.get = MagicMock(return_value=mock_response)
        records = scraper.scrape()

    # Should have 2 records (Q12345 entry filtered out)
    assert len(records) == 2
    assert records[0].full_name == "Bola Tinubu"
    assert records[0].title == "President of Nigeria"
    assert records[0].country_code == "NG"
    assert records[0].source_type == "WIKIDATA"
    assert records[1].full_name == "Godswill Akpabio"
    assert records[1].extra_fields["start_date"] == "2023-06-13"
    assert records[1].extra_fields["is_current"] is True

    # Verify extraction of Date of Birth (P569) from the mock SPARQL response
    assert records[1].extra_fields["date_of_birth"] == "1962-12-09"


def test_wikidata_scraper_deduplicates():
    from africapep.scraper.spiders.wikidata_scraper import WikidataScraper

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "results": {
            "bindings": [
                {
                    "personLabel": {"value": "John Doe", "type": "literal"},
                    "positionLabel": {"value": "Minister", "type": "literal"},
                },
                {
                    "personLabel": {"value": "John Doe", "type": "literal"},
                    "positionLabel": {"value": "Minister", "type": "literal"},
                },
                {
                    "personLabel": {"value": "John Doe", "type": "literal"},
                    "positionLabel": {"value": "Governor", "type": "literal"},
                },
            ]
        }
    }

    with patch("africapep.scraper.spiders.wikidata_scraper.time.sleep"), \
         patch("africapep.scraper.base_scraper.time.sleep"):
        scraper = WikidataScraper(country_code="GH")
        scraper.session.get = MagicMock(return_value=mock_response)
        records = scraper.scrape()

    # Same person+position should be deduplicated, different position kept
    assert len(records) == 2


def test_wikidata_scraper_handles_api_error():
    from africapep.scraper.spiders.wikidata_scraper import WikidataScraper

    with patch("africapep.scraper.spiders.wikidata_scraper.time.sleep"), \
         patch("africapep.scraper.base_scraper.time.sleep"):
        scraper = WikidataScraper(country_code="GH")
        scraper.session.get = MagicMock(side_effect=Exception("API timeout"))
        # run() catches exceptions and returns []
        records = scraper.run()

    assert records == []


def test_wikidata_scraper_run_returns_list():
    from africapep.scraper.spiders.wikidata_scraper import WikidataScraper

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"results": {"bindings": []}}

    with patch("africapep.scraper.spiders.wikidata_scraper.time.sleep"), \
         patch("africapep.scraper.base_scraper.time.sleep"):
        scraper = WikidataScraper(country_code="GH")
        scraper.session.get = MagicMock(return_value=mock_response)
        records = scraper.run()

    assert isinstance(records, list)


# ── Module exports ──

def test_spiders_module_exports():
    from africapep.scraper.spiders import WikidataScraper, COUNTRY_QIDS

    assert WikidataScraper is not None
    assert len(COUNTRY_QIDS) == 54
