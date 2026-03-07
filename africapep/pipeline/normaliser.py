"""Standardise names, dates, country codes from raw scraper records."""
import re
import unicodedata
from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

import structlog

from africapep.scraper.base_scraper import RawPersonRecord

log = structlog.get_logger()

# ── Name normalisation ──

HONORIFIC_PREFIXES = [
    "hon.", "honourable", "honorable", "rt. hon.", "right honourable",
    "alhaji", "alhaja", "hajia", "hajj",
    "otunba", "chief", "nana", "oba", "ooni", "obong",
    "emir", "sultan", "sarki",
    "dr.", "prof.", "professor", "engr.", "engineer",
    "gen.", "general", "maj. gen.", "brig.", "brigadier",
    "col.", "colonel", "capt.", "captain", "cmdr.",
    "rtd.", "retired",
    "justice", "amb.", "ambassador", "h.e.",
    "sen.", "senator", "rep.", "representative",
    "barr.", "barrister", "adv.", "advocate",
    "mr.", "mrs.", "ms.", "miss", "mme.", "sir", "dame", "lady",
]

# ISO 3166-1 alpha-2 for target countries
COUNTRY_ALIASES = {
    "ghana": "GH", "gh": "GH",
    "nigeria": "NG", "ng": "NG",
    "kenya": "KE", "ke": "KE",
    "south africa": "ZA", "za": "ZA", "rsa": "ZA",
    "ethiopia": "ET", "et": "ET",
    "tanzania": "TZ", "tz": "TZ",
    "uganda": "UG", "ug": "UG",
    "senegal": "SN", "sn": "SN",
    "cameroon": "CM", "cm": "CM",
    "egypt": "EG", "eg": "EG",
    "morocco": "MA", "ma": "MA",
    "rwanda": "RW", "rw": "RW",
}

INSTITUTION_NORMALISATION = {
    "parliament of ghana": "Parliament of Ghana",
    "ghana parliament": "Parliament of Ghana",
    "national assembly": "National Assembly",
    "national assembly of nigeria": "National Assembly of Nigeria",
    "senate of nigeria": "Senate of Nigeria",
    "house of representatives": "House of Representatives",
    "parliament of kenya": "Parliament of Kenya",
    "kenya national assembly": "National Assembly of Kenya",
    "parliament of south africa": "Parliament of South Africa",
    "national assembly of south africa": "National Assembly of South Africa",
}

BRANCH_LOOKUP = {
    "president": "EXECUTIVE",
    "vice president": "EXECUTIVE",
    "prime minister": "EXECUTIVE",
    "minister": "EXECUTIVE",
    "cabinet": "EXECUTIVE",
    "secretary": "EXECUTIVE",
    "governor": "EXECUTIVE",
    "member of parliament": "LEGISLATIVE",
    "senator": "LEGISLATIVE",
    "representative": "LEGISLATIVE",
    "speaker": "LEGISLATIVE",
    "mp": "LEGISLATIVE",
    "justice": "JUDICIAL",
    "judge": "JUDICIAL",
    "chief justice": "JUDICIAL",
    "magistrate": "JUDICIAL",
    "general": "MILITARY",
    "brigadier": "MILITARY",
    "colonel": "MILITARY",
    "inspector general": "MILITARY",
    "commissioner": "EXECUTIVE",
}


@dataclass
class NormalisedRecord:
    """Cleaned, standardised person record ready for entity resolution."""
    full_name: str
    name_variants: list[str]
    title: str
    institution: str
    branch: str
    country_code: str
    date_of_birth: Optional[date]
    source_url: str
    source_type: str
    raw_text: str
    scraped_at: datetime
    extra_fields: dict


def normalise_name(raw_name: str) -> str:
    """Normalise a person's name: remove honorifics, fix case, unicode normalise."""
    if not raw_name:
        return ""

    # Unicode normalisation
    name = unicodedata.normalize("NFC", raw_name)

    # Remove extra whitespace
    name = re.sub(r"\s+", " ", name).strip()

    # Remove honorific prefixes
    name_lower = name.lower()
    for prefix in sorted(HONORIFIC_PREFIXES, key=len, reverse=True):
        if name_lower.startswith(prefix):
            name = name[len(prefix):].strip()
            name_lower = name.lower()

    # Title case
    name = name.title()

    # Fix common title-case issues (Mc, O', etc.)
    name = re.sub(r"\bMc([a-z])", lambda m: "Mc" + m.group(1).upper(), name)
    name = re.sub(r"\bO'([a-z])", lambda m: "O'" + m.group(1).upper(), name)

    # Remove trailing commas, periods
    name = name.rstrip(",.")

    return name.strip()


def generate_name_variants(full_name: str) -> list[str]:
    """Generate alternative name forms for fuzzy matching."""
    variants = {full_name}

    parts = full_name.split()
    if len(parts) >= 2:
        # First Last
        variants.add(f"{parts[0]} {parts[-1]}")
        # Last, First
        variants.add(f"{parts[-1]}, {parts[0]}")
        # First Middle Last -> First Last
        if len(parts) >= 3:
            variants.add(f"{parts[0]} {parts[-1]}")
            # Last First Middle
            variants.add(f"{parts[-1]} {' '.join(parts[:-1])}")
        # Initials
        initials = " ".join(p[0] + "." for p in parts[:-1]) + " " + parts[-1]
        variants.add(initials)

    return list(variants)


def normalise_country(raw: str) -> str:
    """Normalise country to ISO 3166-1 alpha-2."""
    if not raw:
        return ""
    raw_lower = raw.strip().lower()
    if raw_lower in COUNTRY_ALIASES:
        return COUNTRY_ALIASES[raw_lower]
    if len(raw) == 2 and raw.upper() in {v for v in COUNTRY_ALIASES.values()}:
        return raw.upper()
    return raw.upper()[:2]


def normalise_institution(raw: str) -> str:
    """Normalise institution name."""
    if not raw:
        return ""
    key = raw.strip().lower()
    return INSTITUTION_NORMALISATION.get(key, raw.strip().title())


def determine_branch(title: str, institution: str = "") -> str:
    """Determine government branch from title/institution."""
    combined = (title + " " + institution).lower()
    for keyword, branch in BRANCH_LOOKUP.items():
        if keyword in combined:
            return branch
    return "EXECUTIVE"  # default


def parse_date(raw: str) -> Optional[date]:
    """Try to parse a date string into a date object."""
    if not raw:
        return None

    formats = [
        "%d %B %Y", "%B %d, %Y", "%B %d %Y",
        "%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%d",
        "%d-%m-%Y", "%d %b %Y", "%b %d, %Y",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(raw.strip(), fmt).date()
        except ValueError:
            continue

    # Try year-only
    year_match = re.search(r"\b(19|20)\d{2}\b", raw)
    if year_match:
        try:
            return date(int(year_match.group(0)), 1, 1)
        except ValueError:
            pass

    return None


def normalise_record(record: RawPersonRecord) -> NormalisedRecord:
    """Full normalisation pipeline for a raw person record."""
    full_name = normalise_name(record.full_name)
    variants = generate_name_variants(full_name)
    country = normalise_country(record.country_code)
    institution = normalise_institution(record.institution)
    branch = determine_branch(record.title, institution)

    dob = None
    if "date_of_birth" in record.extra_fields:
        dob = parse_date(record.extra_fields["date_of_birth"])

    return NormalisedRecord(
        full_name=full_name,
        name_variants=variants,
        title=record.title.strip(),
        institution=institution,
        branch=branch,
        country_code=country,
        date_of_birth=dob,
        source_url=record.source_url,
        source_type=record.source_type,
        raw_text=record.raw_text,
        scraped_at=record.scraped_at,
        extra_fields=record.extra_fields,
    )
