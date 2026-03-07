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


# ── Tanzania Parliament ──

def test_tanzania_parliament_fixture():
    from africapep.scraper.spiders.tanzania_parliament import TanzaniaParliamentScraper

    records = TanzaniaParliamentScraper(use_fixture=True).run()
    assert isinstance(records, list)
    assert len(records) >= 5
    for r in records:
        assert r.country_code == "TZ"
        assert r.source_type == "PARLIAMENT"


# ── Namibia Parliament ──

def test_namibia_parliament_fixture():
    from africapep.scraper.spiders.namibia_parliament import NamibiaParliamentScraper

    records = NamibiaParliamentScraper(use_fixture=True).run()
    assert isinstance(records, list)
    assert len(records) >= 5
    for r in records:
        assert r.country_code == "NA"
        assert r.source_type == "PARLIAMENT"


# ── Cameroon Presidency ──

def test_cameroon_presidency_fixture():
    from africapep.scraper.spiders.cameroon_presidency import CameroonPresidencyScraper

    records = CameroonPresidencyScraper(use_fixture=True).run()
    assert isinstance(records, list)
    assert len(records) >= 5
    for r in records:
        assert r.country_code == "CM"
        assert r.source_type == "PRESIDENCY"


# ── Côte d'Ivoire Parliament ──

def test_cotedivoire_parliament_fixture():
    from africapep.scraper.spiders.cotedivoire_parliament import CoteDIvoireParliamentScraper

    records = CoteDIvoireParliamentScraper(use_fixture=True).run()
    assert isinstance(records, list)
    assert len(records) >= 5
    for r in records:
        assert r.country_code == "CI"
        assert r.source_type == "PARLIAMENT"


# ── Malawi Presidency ──

def test_malawi_presidency_fixture():
    from africapep.scraper.spiders.malawi_presidency import MalawiPresidencyScraper

    records = MalawiPresidencyScraper(use_fixture=True).run()
    assert isinstance(records, list)
    assert len(records) >= 5
    for r in records:
        assert r.country_code == "MW"
        assert r.source_type == "PRESIDENCY"


# ── Zambia Parliament ──

def test_zambia_parliament_fixture():
    from africapep.scraper.spiders.zambia_parliament import ZambiaParliamentScraper

    records = ZambiaParliamentScraper(use_fixture=True).run()
    assert isinstance(records, list)
    assert len(records) >= 5
    for r in records:
        assert r.country_code == "ZM"
        assert r.source_type == "PARLIAMENT"


# ── Egypt Presidency ──

def test_egypt_presidency_fixture():
    from africapep.scraper.spiders.egypt_presidency import EgyptPresidencyScraper

    records = EgyptPresidencyScraper(use_fixture=True).run()
    assert isinstance(records, list)
    assert len(records) >= 5
    for r in records:
        assert r.country_code == "EG"
        assert r.source_type == "PRESIDENCY"


# ── Morocco Presidency ──

def test_morocco_presidency_fixture():
    from africapep.scraper.spiders.morocco_presidency import MoroccoPresidencyScraper

    records = MoroccoPresidencyScraper(use_fixture=True).run()
    assert isinstance(records, list)
    assert len(records) >= 5
    for r in records:
        assert r.country_code == "MA"
        assert r.source_type == "PRESIDENCY"


# ── Botswana Parliament ──

def test_botswana_parliament_fixture():
    from africapep.scraper.spiders.botswana_parliament import BotswanaParliamentScraper

    records = BotswanaParliamentScraper(use_fixture=True).run()
    assert isinstance(records, list)
    assert len(records) >= 5
    for r in records:
        assert r.country_code == "BW"
        assert r.source_type == "PARLIAMENT"


# ── Zimbabwe Parliament ──

def test_zimbabwe_parliament_fixture():
    from africapep.scraper.spiders.zimbabwe_parliament import ZimbabweParliamentScraper

    records = ZimbabweParliamentScraper(use_fixture=True).run()
    assert isinstance(records, list)
    assert len(records) >= 5
    for r in records:
        assert r.country_code == "ZW"
        assert r.source_type == "PARLIAMENT"


# ── Mozambique Presidency ──

def test_mozambique_presidency_fixture():
    from africapep.scraper.spiders.mozambique_presidency import MozambiquePresidencyScraper

    records = MozambiquePresidencyScraper(use_fixture=True).run()
    assert isinstance(records, list)
    assert len(records) >= 5
    for r in records:
        assert r.country_code == "MZ"
        assert r.source_type == "PRESIDENCY"


# ── Angola Presidency ──

def test_angola_presidency_fixture():
    from africapep.scraper.spiders.angola_presidency import AngolaPresidencyScraper

    records = AngolaPresidencyScraper(use_fixture=True).run()
    assert isinstance(records, list)
    assert len(records) >= 5
    for r in records:
        assert r.country_code == "AO"
        assert r.source_type == "PRESIDENCY"


# ── DRC Parliament ──

def test_drc_parliament_fixture():
    from africapep.scraper.spiders.drc_parliament import DRCParliamentScraper

    records = DRCParliamentScraper(use_fixture=True).run()
    assert isinstance(records, list)
    assert len(records) >= 5
    for r in records:
        assert r.country_code == "CD"
        assert r.source_type == "PARLIAMENT"


# ── Tunisia Presidency ──

def test_tunisia_presidency_fixture():
    from africapep.scraper.spiders.tunisia_presidency import TunisiaPresidencyScraper

    records = TunisiaPresidencyScraper(use_fixture=True).run()
    assert isinstance(records, list)
    assert len(records) >= 5
    for r in records:
        assert r.country_code == "TN"
        assert r.source_type == "PRESIDENCY"


# ── Gambia Presidency ──

def test_gambia_presidency_fixture():
    from africapep.scraper.spiders.gambia_presidency import GambiaPresidencyScraper

    records = GambiaPresidencyScraper(use_fixture=True).run()
    assert isinstance(records, list)
    assert len(records) >= 5
    for r in records:
        assert r.country_code == "GM"
        assert r.source_type == "PRESIDENCY"


# ── Sierra Leone Presidency ──

def test_sierraleone_presidency_fixture():
    from africapep.scraper.spiders.sierraleone_presidency import SierraLeonePresidencyScraper

    records = SierraLeonePresidencyScraper(use_fixture=True).run()
    assert isinstance(records, list)
    assert len(records) >= 5
    for r in records:
        assert r.country_code == "SL"
        assert r.source_type == "PRESIDENCY"


# ── Algeria Presidency ──

def test_algeria_presidency_fixture():
    from africapep.scraper.spiders.algeria_presidency import AlgeriaPresidencyScraper
    records = AlgeriaPresidencyScraper(use_fixture=True).run()
    assert isinstance(records, list)
    assert len(records) >= 5
    for r in records:
        assert r.country_code == "DZ"
        assert r.source_type == "PRESIDENCY"


# ── Benin Presidency ──

def test_benin_presidency_fixture():
    from africapep.scraper.spiders.benin_presidency import BeninPresidencyScraper
    records = BeninPresidencyScraper(use_fixture=True).run()
    assert isinstance(records, list)
    assert len(records) >= 5
    for r in records:
        assert r.country_code == "BJ"
        assert r.source_type == "PRESIDENCY"


# ── Burkina Faso Presidency ──

def test_burkinafaso_presidency_fixture():
    from africapep.scraper.spiders.burkinafaso_presidency import BurkinaFasoPresidencyScraper
    records = BurkinaFasoPresidencyScraper(use_fixture=True).run()
    assert isinstance(records, list)
    assert len(records) >= 5
    for r in records:
        assert r.country_code == "BF"
        assert r.source_type == "PRESIDENCY"


# ── Burundi Presidency ──

def test_burundi_presidency_fixture():
    from africapep.scraper.spiders.burundi_presidency import BurundiPresidencyScraper
    records = BurundiPresidencyScraper(use_fixture=True).run()
    assert isinstance(records, list)
    assert len(records) >= 5
    for r in records:
        assert r.country_code == "BI"
        assert r.source_type == "PRESIDENCY"


# ── Cape Verde Presidency ──

def test_capeverde_presidency_fixture():
    from africapep.scraper.spiders.capeverde_presidency import CapeVerdePresidencyScraper
    records = CapeVerdePresidencyScraper(use_fixture=True).run()
    assert isinstance(records, list)
    assert len(records) >= 5
    for r in records:
        assert r.country_code == "CV"
        assert r.source_type == "PRESIDENCY"


# ── Central African Republic Presidency ──

def test_car_presidency_fixture():
    from africapep.scraper.spiders.car_presidency import CARPresidencyScraper
    records = CARPresidencyScraper(use_fixture=True).run()
    assert isinstance(records, list)
    assert len(records) >= 5
    for r in records:
        assert r.country_code == "CF"
        assert r.source_type == "PRESIDENCY"


# ── Chad Presidency ──

def test_chad_presidency_fixture():
    from africapep.scraper.spiders.chad_presidency import ChadPresidencyScraper
    records = ChadPresidencyScraper(use_fixture=True).run()
    assert isinstance(records, list)
    assert len(records) >= 5
    for r in records:
        assert r.country_code == "TD"
        assert r.source_type == "PRESIDENCY"


# ── Comoros Presidency ──

def test_comoros_presidency_fixture():
    from africapep.scraper.spiders.comoros_presidency import ComorosPresidencyScraper
    records = ComorosPresidencyScraper(use_fixture=True).run()
    assert isinstance(records, list)
    assert len(records) >= 5
    for r in records:
        assert r.country_code == "KM"
        assert r.source_type == "PRESIDENCY"


# ── Congo (Brazzaville) Presidency ──

def test_congo_presidency_fixture():
    from africapep.scraper.spiders.congo_presidency import CongoPresidencyScraper
    records = CongoPresidencyScraper(use_fixture=True).run()
    assert isinstance(records, list)
    assert len(records) >= 5
    for r in records:
        assert r.country_code == "CG"
        assert r.source_type == "PRESIDENCY"


# ── Djibouti Presidency ──

def test_djibouti_presidency_fixture():
    from africapep.scraper.spiders.djibouti_presidency import DjiboutiPresidencyScraper
    records = DjiboutiPresidencyScraper(use_fixture=True).run()
    assert isinstance(records, list)
    assert len(records) >= 5
    for r in records:
        assert r.country_code == "DJ"
        assert r.source_type == "PRESIDENCY"


# ── Equatorial Guinea Presidency ──

def test_eqguinea_presidency_fixture():
    from africapep.scraper.spiders.eqguinea_presidency import EqGuineaPresidencyScraper
    records = EqGuineaPresidencyScraper(use_fixture=True).run()
    assert isinstance(records, list)
    assert len(records) >= 5
    for r in records:
        assert r.country_code == "GQ"
        assert r.source_type == "PRESIDENCY"


# ── Eritrea Presidency ──

def test_eritrea_presidency_fixture():
    from africapep.scraper.spiders.eritrea_presidency import EritreaPresidencyScraper
    records = EritreaPresidencyScraper(use_fixture=True).run()
    assert isinstance(records, list)
    assert len(records) >= 5
    for r in records:
        assert r.country_code == "ER"
        assert r.source_type == "PRESIDENCY"


# ── Eswatini Presidency ──

def test_eswatini_presidency_fixture():
    from africapep.scraper.spiders.eswatini_presidency import EswatiniPresidencyScraper
    records = EswatiniPresidencyScraper(use_fixture=True).run()
    assert isinstance(records, list)
    assert len(records) >= 5
    for r in records:
        assert r.country_code == "SZ"
        assert r.source_type == "PRESIDENCY"


# ── Gabon Presidency ──

def test_gabon_presidency_fixture():
    from africapep.scraper.spiders.gabon_presidency import GabonPresidencyScraper
    records = GabonPresidencyScraper(use_fixture=True).run()
    assert isinstance(records, list)
    assert len(records) >= 5
    for r in records:
        assert r.country_code == "GA"
        assert r.source_type == "PRESIDENCY"


# ── Guinea Presidency ──

def test_guinea_presidency_fixture():
    from africapep.scraper.spiders.guinea_presidency import GuineaPresidencyScraper
    records = GuineaPresidencyScraper(use_fixture=True).run()
    assert isinstance(records, list)
    assert len(records) >= 5
    for r in records:
        assert r.country_code == "GN"
        assert r.source_type == "PRESIDENCY"


# ── Guinea-Bissau Presidency ──

def test_guineabissau_presidency_fixture():
    from africapep.scraper.spiders.guineabissau_presidency import GuineaBissauPresidencyScraper
    records = GuineaBissauPresidencyScraper(use_fixture=True).run()
    assert isinstance(records, list)
    assert len(records) >= 5
    for r in records:
        assert r.country_code == "GW"
        assert r.source_type == "PRESIDENCY"


# ── Lesotho Presidency ──

def test_lesotho_presidency_fixture():
    from africapep.scraper.spiders.lesotho_presidency import LesothoPresidencyScraper
    records = LesothoPresidencyScraper(use_fixture=True).run()
    assert isinstance(records, list)
    assert len(records) >= 5
    for r in records:
        assert r.country_code == "LS"
        assert r.source_type == "PRESIDENCY"


# ── Liberia Presidency ──

def test_liberia_presidency_fixture():
    from africapep.scraper.spiders.liberia_presidency import LiberiaPresidencyScraper
    records = LiberiaPresidencyScraper(use_fixture=True).run()
    assert isinstance(records, list)
    assert len(records) >= 5
    for r in records:
        assert r.country_code == "LR"
        assert r.source_type == "PRESIDENCY"


# ── Libya Presidency ──

def test_libya_presidency_fixture():
    from africapep.scraper.spiders.libya_presidency import LibyaPresidencyScraper
    records = LibyaPresidencyScraper(use_fixture=True).run()
    assert isinstance(records, list)
    assert len(records) >= 5
    for r in records:
        assert r.country_code == "LY"
        assert r.source_type == "PRESIDENCY"


# ── Madagascar Presidency ──

def test_madagascar_presidency_fixture():
    from africapep.scraper.spiders.madagascar_presidency import MadagascarPresidencyScraper
    records = MadagascarPresidencyScraper(use_fixture=True).run()
    assert isinstance(records, list)
    assert len(records) >= 5
    for r in records:
        assert r.country_code == "MG"
        assert r.source_type == "PRESIDENCY"


# ── Mali Presidency ──

def test_mali_presidency_fixture():
    from africapep.scraper.spiders.mali_presidency import MaliPresidencyScraper
    records = MaliPresidencyScraper(use_fixture=True).run()
    assert isinstance(records, list)
    assert len(records) >= 5
    for r in records:
        assert r.country_code == "ML"
        assert r.source_type == "PRESIDENCY"


# ── Mauritania Presidency ──

def test_mauritania_presidency_fixture():
    from africapep.scraper.spiders.mauritania_presidency import MauritaniaPresidencyScraper
    records = MauritaniaPresidencyScraper(use_fixture=True).run()
    assert isinstance(records, list)
    assert len(records) >= 5
    for r in records:
        assert r.country_code == "MR"
        assert r.source_type == "PRESIDENCY"


# ── Mauritius Presidency ──

def test_mauritius_presidency_fixture():
    from africapep.scraper.spiders.mauritius_presidency import MauritiusPresidencyScraper
    records = MauritiusPresidencyScraper(use_fixture=True).run()
    assert isinstance(records, list)
    assert len(records) >= 5
    for r in records:
        assert r.country_code == "MU"
        assert r.source_type == "PRESIDENCY"


# ── Niger Presidency ──

def test_niger_presidency_fixture():
    from africapep.scraper.spiders.niger_presidency import NigerPresidencyScraper
    records = NigerPresidencyScraper(use_fixture=True).run()
    assert isinstance(records, list)
    assert len(records) >= 5
    for r in records:
        assert r.country_code == "NE"
        assert r.source_type == "PRESIDENCY"


# ── São Tomé and Príncipe Presidency ──

def test_saotome_presidency_fixture():
    from africapep.scraper.spiders.saotome_presidency import SaoTomePresidencyScraper
    records = SaoTomePresidencyScraper(use_fixture=True).run()
    assert isinstance(records, list)
    assert len(records) >= 5
    for r in records:
        assert r.country_code == "ST"
        assert r.source_type == "PRESIDENCY"


# ── Seychelles Presidency ──

def test_seychelles_presidency_fixture():
    from africapep.scraper.spiders.seychelles_presidency import SeychellesPresidencyScraper
    records = SeychellesPresidencyScraper(use_fixture=True).run()
    assert isinstance(records, list)
    assert len(records) >= 5
    for r in records:
        assert r.country_code == "SC"
        assert r.source_type == "PRESIDENCY"


# ── Somalia Presidency ──

def test_somalia_presidency_fixture():
    from africapep.scraper.spiders.somalia_presidency import SomaliaPresidencyScraper
    records = SomaliaPresidencyScraper(use_fixture=True).run()
    assert isinstance(records, list)
    assert len(records) >= 5
    for r in records:
        assert r.country_code == "SO"
        assert r.source_type == "PRESIDENCY"


# ── South Sudan Presidency ──

def test_southsudan_presidency_fixture():
    from africapep.scraper.spiders.southsudan_presidency import SouthSudanPresidencyScraper
    records = SouthSudanPresidencyScraper(use_fixture=True).run()
    assert isinstance(records, list)
    assert len(records) >= 5
    for r in records:
        assert r.country_code == "SS"
        assert r.source_type == "PRESIDENCY"


# ── Sudan Presidency ──

def test_sudan_presidency_fixture():
    from africapep.scraper.spiders.sudan_presidency import SudanPresidencyScraper
    records = SudanPresidencyScraper(use_fixture=True).run()
    assert isinstance(records, list)
    assert len(records) >= 5
    for r in records:
        assert r.country_code == "SD"
        assert r.source_type == "PRESIDENCY"


# ── Togo Presidency ──

def test_togo_presidency_fixture():
    from africapep.scraper.spiders.togo_presidency import TogoPresidencyScraper
    records = TogoPresidencyScraper(use_fixture=True).run()
    assert isinstance(records, list)
    assert len(records) >= 5
    for r in records:
        assert r.country_code == "TG"
        assert r.source_type == "PRESIDENCY"


# ── ALL_SCRAPERS registry ──

def test_all_scrapers_registry():
    from africapep.scraper.spiders import ALL_SCRAPERS

    assert len(ALL_SCRAPERS) >= 65, "Should have at least 65 scrapers registered"
    for cls in ALL_SCRAPERS:
        scraper = cls(use_fixture=True)
        records = scraper.run()
        assert isinstance(records, list), f"{cls.__name__} should return a list"
        assert len(records) >= 1, f"{cls.__name__} should have at least 1 fixture record"
