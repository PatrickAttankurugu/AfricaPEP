"""Tests for scraper base classes and individual scrapers."""
from datetime import datetime

import pytest


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
        scraped_at=datetime.utcnow(),
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
        scraped_at=datetime.utcnow(),
    )
    assert r.extra_fields == {}


def test_base_scraper_is_abstract():
    import inspect
    from africapep.scraper.base_scraper import BaseScraper

    assert inspect.isabstract(BaseScraper)


def test_base_scraper_cannot_instantiate():
    from africapep.scraper.base_scraper import BaseScraper

    with pytest.raises(TypeError):
        BaseScraper()


# ── Ghana Parliament ──

def test_ghana_parliament_fixture():
    from africapep.scraper.spiders.ghana_parliament import GhanaParliamentScraper

    scraper = GhanaParliamentScraper(use_fixture=True)
    records = scraper.run()

    assert isinstance(records, list)
    assert len(records) >= 5, "Should have at least 5 fixture MPs"

    for r in records:
        assert r.country_code == "GH"
        assert r.source_type == "PARLIAMENT"
        assert len(r.full_name) > 2
        assert r.title == "Member of Parliament"
        assert r.institution == "Parliament of Ghana"


def test_ghana_parliament_fixture_has_extra_fields():
    from africapep.scraper.spiders.ghana_parliament import GhanaParliamentScraper

    records = GhanaParliamentScraper(use_fixture=True).run()
    if records:
        r = records[0]
        assert "party" in r.extra_fields or "constituency" in r.extra_fields


# ── Ghana Presidency ──

def test_ghana_presidency_fixture():
    from africapep.scraper.spiders.ghana_presidency import GhanaPresidencyScraper

    records = GhanaPresidencyScraper(use_fixture=True).run()
    assert isinstance(records, list)
    assert len(records) >= 5
    for r in records:
        assert r.country_code == "GH"
        assert r.source_type == "PRESIDENCY"


# ── Nigeria NASS ──

def test_nigeria_nass_fixture():
    from africapep.scraper.spiders.nigeria_nass import NigeriaNASSScraper

    records = NigeriaNASSScraper(use_fixture=True).run()
    assert isinstance(records, list)
    assert len(records) >= 5
    for r in records:
        assert r.country_code == "NG"
        assert r.source_type == "PARLIAMENT"


# ── Nigeria Presidency ──

def test_nigeria_presidency_fixture():
    from africapep.scraper.spiders.nigeria_presidency import NigeriaPresidencyScraper

    records = NigeriaPresidencyScraper(use_fixture=True).run()
    assert isinstance(records, list)
    assert len(records) >= 5
    for r in records:
        assert r.country_code == "NG"


# ── Kenya Parliament ──

def test_kenya_parliament_fixture():
    from africapep.scraper.spiders.kenya_parliament import KenyaParliamentScraper

    records = KenyaParliamentScraper(use_fixture=True).run()
    assert isinstance(records, list)
    assert len(records) >= 5
    for r in records:
        assert r.country_code == "KE"


# ── South Africa Parliament ──

def test_southafrica_parliament_fixture():
    from africapep.scraper.spiders.southafrica_parliament import SouthAfricaParliamentScraper

    records = SouthAfricaParliamentScraper(use_fixture=True).run()
    assert isinstance(records, list)
    assert len(records) >= 5
    for r in records:
        assert r.country_code == "ZA"


# ── Ghana Judiciary ──

def test_ghana_judiciary_fixture():
    from africapep.scraper.spiders.ghana_judiciary import GhanaJudiciaryScraper

    records = GhanaJudiciaryScraper(use_fixture=True).run()
    assert isinstance(records, list)
    assert len(records) >= 5
    for r in records:
        assert r.country_code == "GH"
        assert r.source_type == "JUDICIARY"
        assert "Court" in r.institution


# ── Nigeria Judiciary ──

def test_nigeria_judiciary_fixture():
    from africapep.scraper.spiders.nigeria_judiciary import NigeriaJudiciaryScraper

    records = NigeriaJudiciaryScraper(use_fixture=True).run()
    assert isinstance(records, list)
    assert len(records) >= 5
    for r in records:
        assert r.country_code == "NG"
        assert r.source_type == "JUDICIARY"


# ── Kenya Presidency ──

def test_kenya_presidency_fixture():
    from africapep.scraper.spiders.kenya_presidency import KenyaPresidencyScraper

    records = KenyaPresidencyScraper(use_fixture=True).run()
    assert isinstance(records, list)
    assert len(records) >= 5
    for r in records:
        assert r.country_code == "KE"
        assert r.source_type == "PRESIDENCY"


# ── Rwanda Parliament ──

def test_rwanda_parliament_fixture():
    from africapep.scraper.spiders.rwanda_parliament import RwandaParliamentScraper

    records = RwandaParliamentScraper(use_fixture=True).run()
    assert isinstance(records, list)
    assert len(records) >= 5
    for r in records:
        assert r.country_code == "RW"
        assert r.source_type == "PARLIAMENT"


# ── Uganda Parliament ──

def test_uganda_parliament_fixture():
    from africapep.scraper.spiders.uganda_parliament import UgandaParliamentScraper

    records = UgandaParliamentScraper(use_fixture=True).run()
    assert isinstance(records, list)
    assert len(records) >= 5
    for r in records:
        assert r.country_code == "UG"
        assert r.source_type == "PARLIAMENT"


# ── South Africa Presidency ──

def test_southafrica_presidency_fixture():
    from africapep.scraper.spiders.southafrica_presidency import SouthAfricaPresidencyScraper

    records = SouthAfricaPresidencyScraper(use_fixture=True).run()
    assert isinstance(records, list)
    assert len(records) >= 5
    for r in records:
        assert r.country_code == "ZA"
        assert r.source_type == "PRESIDENCY"


# ── Ethiopia Presidency ──

def test_ethiopia_presidency_fixture():
    from africapep.scraper.spiders.ethiopia_presidency import EthiopiaPresidencyScraper

    records = EthiopiaPresidencyScraper(use_fixture=True).run()
    assert isinstance(records, list)
    assert len(records) >= 5
    for r in records:
        assert r.country_code == "ET"
        assert r.source_type == "PRESIDENCY"


# ── Tanzania Presidency ──

def test_tanzania_presidency_fixture():
    from africapep.scraper.spiders.tanzania_presidency import TanzaniaPresidencyScraper

    records = TanzaniaPresidencyScraper(use_fixture=True).run()
    assert isinstance(records, list)
    assert len(records) >= 5
    for r in records:
        assert r.country_code == "TZ"
        assert r.source_type == "PRESIDENCY"


# ── Senegal Presidency ──

def test_senegal_presidency_fixture():
    from africapep.scraper.spiders.senegal_presidency import SenegalPresidencyScraper

    records = SenegalPresidencyScraper(use_fixture=True).run()
    assert isinstance(records, list)
    assert len(records) >= 5
    for r in records:
        assert r.country_code == "SN"
        assert r.source_type == "PRESIDENCY"


# ── ALL_SCRAPERS registry ──

def test_all_scrapers_registry():
    from africapep.scraper.spiders import ALL_SCRAPERS

    assert len(ALL_SCRAPERS) >= 19, "Should have at least 19 scrapers registered"
    for cls in ALL_SCRAPERS:
        scraper = cls(use_fixture=True)
        records = scraper.run()
        assert isinstance(records, list), f"{cls.__name__} should return a list"
        assert len(records) >= 1, f"{cls.__name__} should have at least 1 fixture record"
