"""NLP/NER pipeline: extract Person, Organisation, Title, Date from raw text.

Uses spaCy en_core_web_lg with custom EntityRuler for African honorifics and titles.
"""
import re
from typing import Optional
from dataclasses import dataclass, field

import spacy
from spacy.language import Language
from spacy.tokens import Span
import structlog

log = structlog.get_logger()

# ── Custom patterns for African titles and honorifics ──

AFRICAN_HONORIFICS = [
    "Hon.", "Honourable", "Honorable", "Rt. Hon.", "Right Honourable",
    "Alhaji", "Alhaja", "Hajia", "Hajj",
    "Otunba", "Chief", "Nana", "Asantehene", "Ooni", "Oba", "Obong",
    "Emir", "Sultan", "Sarki",
    "Dr.", "Prof.", "Professor", "Engr.", "Engineer",
    "Gen.", "General", "Maj. Gen.", "Brig.", "Brigadier",
    "Col.", "Colonel", "Capt.", "Captain", "Cmdr.", "Commander",
    "Rtd.", "Retired",
    "Justice", "CJ", "JSC",
    "Amb.", "Ambassador", "H.E.", "His Excellency", "Her Excellency",
    "Sen.", "Senator", "Rep.", "Representative",
    "Barr.", "Barrister", "Adv.", "Advocate", "Atty.",
    "Comrade", "Cde.",
]

TITLE_PATTERNS = [
    # "appointed as Minister of ..."
    re.compile(r"appointed\s+(?:as\s+)?(?:the\s+)?(.{5,80}?)(?:\s+of\s+|\s+for\s+|\s*[,.])", re.I),
    # "Minister of Finance"
    re.compile(r"(Minister\s+(?:of|for)\s+[A-Z][^,.\n]{3,60})", re.I),
    # "Member of Parliament for ..."
    re.compile(r"(Member\s+of\s+Parliament\s+for\s+[A-Z][^,.\n]{3,40})", re.I),
    # "Senator representing ..."
    re.compile(r"(Senator\s+representing\s+[A-Z][^,.\n]{3,40})", re.I),
    # "Justice ... of the Supreme Court"
    re.compile(r"(Justice\s+[A-Z][^,.\n]{3,60}?\s+of\s+the\s+[^,.\n]{3,40})", re.I),
    # "President of ..."
    re.compile(r"(President\s+of\s+[A-Z][^,.\n]{3,60})", re.I),
    # "Governor of ..."
    re.compile(r"(Governor\s+of\s+[A-Z][^,.\n]{3,40})", re.I),
    # "Speaker of ..."
    re.compile(r"(Speaker\s+of\s+[^,.\n]{3,60})", re.I),
    # "Director[- ]General of ..."
    re.compile(r"(Director[- ]General\s+of\s+[^,.\n]{3,60})", re.I),
    # "Chairman/Chairperson of ..."
    re.compile(r"(Chair(?:man|person|woman)\s+of\s+[^,.\n]{3,60})", re.I),
]

RELATIONSHIP_PATTERNS = [
    (re.compile(r"(?:wife|husband|spouse)\s+of\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})", re.I), "SPOUSE"),
    (re.compile(r"(?:son|daughter|child)\s+of\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})", re.I), "CHILD"),
    (re.compile(r"(?:brother|sister|sibling)\s+of\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})", re.I), "SIBLING"),
    (re.compile(r"(?:father|mother|parent)\s+of\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})", re.I), "PARENT"),
    (re.compile(r"(?:business\s+partner|co-director|associate)\s+of\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})", re.I), "BUSINESS"),
    (re.compile(r"(?:political\s+ally|political\s+associate)\s+of\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})", re.I), "POLITICAL"),
]

DATE_PATTERNS = [
    re.compile(r"(\d{1,2})\s*(?:st|nd|rd|th)?\s+(January|February|March|April|May|June|July|August|September|October|November|December)[,\s]+(\d{4})", re.I),
    re.compile(r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(\d{4})", re.I),
    re.compile(r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})"),
    re.compile(r"(\d{4})[/-](\d{1,2})[/-](\d{1,2})"),
]


@dataclass
class ExtractedEntity:
    """Result of NER extraction from raw text."""
    persons: list[str] = field(default_factory=list)
    organisations: list[str] = field(default_factory=list)
    titles: list[str] = field(default_factory=list)
    dates: list[str] = field(default_factory=list)
    relationships: list[dict] = field(default_factory=list)


# ── spaCy setup (lazy loaded) ──

_nlp: Optional[Language] = None


def _get_nlp() -> Language:
    global _nlp
    if _nlp is None:
        try:
            _nlp = spacy.load("en_core_web_lg")
        except OSError:
            log.warning("spacy_model_fallback", model="en_core_web_sm")
            try:
                _nlp = spacy.load("en_core_web_sm")
            except OSError:
                log.error("spacy_no_model_available")
                _nlp = spacy.blank("en")

        # Add custom EntityRuler for African honorifics
        if "entity_ruler" not in _nlp.pipe_names:
            ruler = _nlp.add_pipe("entity_ruler", before="ner" if "ner" in _nlp.pipe_names else None)
            patterns = []
            for honorific in AFRICAN_HONORIFICS:
                patterns.append({
                    "label": "HONORIFIC",
                    "pattern": [{"LOWER": w.lower().rstrip(".")} for w in honorific.split()],
                })
            ruler.add_patterns(patterns)

    return _nlp


def extract_entities(text: str) -> ExtractedEntity:
    """Run full NER extraction on raw text."""
    if not text or len(text.strip()) < 10:
        return ExtractedEntity()

    nlp = _get_nlp()
    # Limit text length to avoid memory issues
    doc = nlp(text[:50000])

    result = ExtractedEntity()

    # 1. Extract PERSON entities via spaCy NER
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            name = ent.text.strip()
            # Clean up honorifics
            for hon in AFRICAN_HONORIFICS:
                if name.startswith(hon):
                    name = name[len(hon):].strip()
            if len(name) > 3 and name not in result.persons:
                result.persons.append(name)
        elif ent.label_ == "ORG":
            org = ent.text.strip()
            if len(org) > 2 and org not in result.organisations:
                result.organisations.append(org)
        elif ent.label_ == "DATE":
            result.dates.append(ent.text.strip())

    # 2. Extract titles via regex patterns
    for pattern in TITLE_PATTERNS:
        for match in pattern.finditer(text):
            title = match.group(1).strip()
            if title and title not in result.titles:
                result.titles.append(title)

    # 3. Extract relationships
    for pattern, rel_type in RELATIONSHIP_PATTERNS:
        for match in pattern.finditer(text):
            related_name = match.group(1).strip()
            result.relationships.append({
                "related_person": related_name,
                "relationship_type": rel_type,
                "context": text[max(0, match.start()-50):match.end()+50],
            })

    # 4. Extract dates via regex (supplement spaCy)
    for pattern in DATE_PATTERNS:
        for match in pattern.finditer(text):
            date_str = match.group(0)
            if date_str not in result.dates:
                result.dates.append(date_str)

    log.debug("entities_extracted",
              persons=len(result.persons),
              orgs=len(result.organisations),
              titles=len(result.titles))

    return result


def extract_persons_from_text(text: str) -> list[str]:
    """Convenience: extract just person names from text."""
    return extract_entities(text).persons


def extract_titles_from_text(text: str) -> list[str]:
    """Convenience: extract just position titles from text."""
    return extract_entities(text).titles
