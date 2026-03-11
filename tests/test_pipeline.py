"""Tests for the NLP pipeline: normaliser, classifier, extractor."""
from datetime import datetime, timezone

import pytest


# ── Normaliser tests ──

class TestNormaliser:
    def test_normalise_name_basic(self):
        from africapep.pipeline.normaliser import normalise_name

        assert normalise_name("JOHN SMITH") == "John Smith"
        assert normalise_name("  john  smith  ") == "John Smith"

    def test_normalise_name_removes_honorifics(self):
        from africapep.pipeline.normaliser import normalise_name

        assert normalise_name("Hon. Kwame Mensah") == "Kwame Mensah"
        assert normalise_name("Dr. Amina Mohammed") == "Amina Mohammed"
        assert normalise_name("Alhaji Bola Tinubu") == "Bola Tinubu"
        assert normalise_name("Chief Olusegun Obasanjo") == "Olusegun Obasanjo"
        assert normalise_name("Nana Addo Dankwa") == "Addo Dankwa"

    def test_normalise_name_empty(self):
        from africapep.pipeline.normaliser import normalise_name

        assert normalise_name("") == ""
        assert normalise_name(None) == ""

        assert len(variants) >= 3

    def test_normalise_diacritics(self):
        from africapep.pipeline.normaliser import normalise_diacritics

        assert normalise_diacritics("Félix") == "Felix"
        assert normalise_diacritics("François") == "Francois"
        assert normalise_diacritics("M'Baye") == "MBaye"

    def test_generate_name_variants_french(self):
        from africapep.pipeline.normaliser import generate_name_variants

        variants = generate_name_variants("Charles de Gaulle")
        assert "Charles De Gaulle" in variants  # title case
        # Check if transliteration variant exists (though already ASCII)
        assert "Charles de Gaulle" in variants

    def test_normalise_country(self):
        from africapep.pipeline.normaliser import normalise_country

        assert normalise_country("GH") == "GH"
        assert normalise_country("gh") == "GH"
        assert normalise_country("ghana") == "GH"
        assert normalise_country("Nigeria") == "NG"
        assert normalise_country("kenya") == "KE"
        assert normalise_country("south africa") == "ZA"

    def test_determine_branch(self):
        from africapep.pipeline.normaliser import determine_branch

        assert determine_branch("Minister of Finance") == "EXECUTIVE"
        assert determine_branch("Member of Parliament") == "LEGISLATIVE"
        assert determine_branch("Senator") == "LEGISLATIVE"
        assert determine_branch("Chief Justice") == "JUDICIAL"
        assert determine_branch("General") == "MILITARY"

    def test_parse_date(self):
        from africapep.pipeline.normaliser import parse_date

        d = parse_date("15 January 2024")
        assert d is not None
        assert d.year == 2024
        assert d.month == 1
        assert d.day == 15

        d2 = parse_date("2024-03-15")
        assert d2 is not None
        assert d2.year == 2024

        assert parse_date("") is None
        assert parse_date(None) is None

    def test_normalise_record(self):
        from africapep.pipeline.normaliser import normalise_record
        from africapep.scraper.base_scraper import RawPersonRecord

        record = RawPersonRecord(
            full_name="Hon. Kwame Mensah",
            title="Member of Parliament",
            institution="Parliament of Ghana",
            country_code="GH",
            source_url="https://parliament.gh",
            source_type="PARLIAMENT",
            raw_text="Hon. Kwame Mensah MP",
            scraped_at=datetime.now(timezone.utc),
        )

        normalised = normalise_record(record)
        assert normalised.full_name == "Kwame Mensah"
        assert normalised.country_code == "GH"
        assert normalised.branch == "LEGISLATIVE"
        assert len(normalised.name_variants) >= 2


# ── Classifier tests ──

class TestClassifier:
    def test_tier_1_president(self):
        from africapep.pipeline.classifier import classify_pep_tier

        assert classify_pep_tier("President of the Republic") == 1
        assert classify_pep_tier("Vice President") == 1

    def test_tier_1_ministers(self):
        from africapep.pipeline.classifier import classify_pep_tier

        assert classify_pep_tier("Minister of Finance") == 1
        assert classify_pep_tier("Minister for Defence") == 1
        assert classify_pep_tier("Attorney General") == 1

    def test_tier_1_chief_justice(self):
        from africapep.pipeline.classifier import classify_pep_tier

        assert classify_pep_tier("Chief Justice") == 1
        assert classify_pep_tier("Justice of the Supreme Court") == 1
        assert classify_pep_tier("Constitutional Court Judge") == 1
        assert classify_pep_tier("Président de la Cour Suprême") == 1

    def test_judiciary_french_tiers(self):
        from africapep.pipeline.classifier import classify_pep_tier

        assert classify_pep_tier("Juge d'appel") == 2
        assert classify_pep_tier("Magistrat") == 3

    def test_tier_1_central_bank(self):
        from africapep.pipeline.classifier import classify_pep_tier

        assert classify_pep_tier("Governor of the Central Bank") == 1
        assert classify_pep_tier("", "Central Bank of Nigeria") == 1

    def test_tier_1_speaker(self):
        from africapep.pipeline.classifier import classify_pep_tier

        assert classify_pep_tier("Speaker of Parliament") == 1
        assert classify_pep_tier("Senate President") == 1

    def test_tier_1_military_chiefs(self):
        from africapep.pipeline.classifier import classify_pep_tier

        assert classify_pep_tier("Chief of Defence Staff") == 1
        assert classify_pep_tier("Inspector General of Police") == 1

    def test_tier_2_mp(self):
        from africapep.pipeline.classifier import classify_pep_tier

        assert classify_pep_tier("Member of Parliament") == 2
        assert classify_pep_tier("Senator") == 2

    def test_tier_2_judge(self):
        from africapep.pipeline.classifier import classify_pep_tier

        assert classify_pep_tier("High Court Judge") == 2
        assert classify_pep_tier("Judge of the Court of Appeal") == 2

    def test_tier_2_ambassador(self):
        from africapep.pipeline.classifier import classify_pep_tier

        assert classify_pep_tier("Ambassador") == 2
        assert classify_pep_tier("High Commissioner") == 2

    def test_tier_2_governor(self):
        from africapep.pipeline.classifier import classify_pep_tier

        assert classify_pep_tier("Governor") == 2
        assert classify_pep_tier("Deputy Governor") == 2

    def test_tier_2_soe(self):
        from africapep.pipeline.classifier import classify_pep_tier

        assert classify_pep_tier("CEO", "NNPC") == 2
        assert classify_pep_tier("Chairman of COCOBOD") == 2

    def test_tier_3_local_govt(self):
        from africapep.pipeline.classifier import classify_pep_tier

        assert classify_pep_tier("Mayor") == 3
        assert classify_pep_tier("District Chief Executive") == 3
        assert classify_pep_tier("Magistrate") == 3

    def test_tier_description(self):
        from africapep.pipeline.classifier import get_tier_description

        assert "highest risk" in get_tier_description(1).lower()
        assert "senior" in get_tier_description(2).lower()

    def test_is_high_risk(self):
        from africapep.pipeline.classifier import is_high_risk_pep

        assert is_high_risk_pep(1) is True
        assert is_high_risk_pep(2) is True
        assert is_high_risk_pep(3) is False


# ── PDF Parser tests ──

class TestPDFParser:
    def test_pdf_parser_file_not_found(self):
        from africapep.scraper.utils.pdf_parser import extract_text_from_pdf

        with pytest.raises(FileNotFoundError):
            extract_text_from_pdf("/nonexistent/path.pdf")

    def test_table_extractor_file_not_found(self):
        from africapep.scraper.utils.pdf_parser import extract_tables_from_pdf

        with pytest.raises(FileNotFoundError):
            extract_tables_from_pdf("/nonexistent/path.pdf")
