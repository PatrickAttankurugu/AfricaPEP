"""PEP Tier Classification per FATF Recommendation 12.

TIER 1: Heads of state/government level
TIER 2: Senior officials
TIER 3: Other PEPs
"""
import structlog

log = structlog.get_logger()

# ── TIER 1: Highest risk ──
# Heads of state, ministers, supreme court justices, central bank governors, military chiefs

TIER_1_TITLES = [
    # Executive heads
    "president", "vice president", "vice-president",
    "prime minister", "deputy prime minister",
    "head of state", "head of government",
    # Legislative heads
    "speaker of parliament", "speaker of the house",
    "speaker of the national assembly", "speaker of the senate",
    "senate president", "president of the senate",
    "deputy speaker",
    # Judicial heads
    "chief justice", "deputy chief justice",
    "justice of the supreme court", "supreme court justice",
    "president of the court of appeal",
    # Central bank
    "governor of the central bank", "central bank governor",
    "governor of the bank of ghana", "governor of the reserve bank",
    "governor of the cbn", "deputy governor of the central bank",
    "deputy governor of the bank", "deputy governor of the reserve",
    # Ministers (all portfolios)
    "minister of", "minister for",
    "cabinet minister", "senior minister",
    "attorney general", "attorney-general",
    # Military chiefs
    "chief of defence staff", "chief of army staff",
    "chief of naval staff", "chief of air staff",
    "chief of the defence force", "commander-in-chief",
    "inspector general of police", "inspector-general of police",
    "national security adviser",
    # Former heads of state remain Tier 1 PEPs
    "former president", "former prime minister",
    "former vice president", "former head of state",
    # Candidates for highest office
    "candidate", "presidential candidate",
    # Cabinet Secretary (Kenya style)
    "cabinet secretary",
]

TIER_1_INSTITUTIONS = [
    "presidency", "office of the president", "state house",
    "cabinet", "federal executive council",
    "supreme court", "constitutional court",
    "central bank", "reserve bank", "bank of ghana",
    "central bank of nigeria", "south african reserve bank",
    "central bank of kenya",
]

# ── TIER 2: Senior officials ──

TIER_2_TITLES = [
    # Parliament members
    "member of parliament", "senator",
    "member of the national assembly",
    "member of the house of representatives",
    "member of the house of reps",
    # Judges
    "high court judge", "judge of the high court",
    "appeal court judge", "judge of the court of appeal",
    "judge of the federal high court",
    # Ambassadors
    "ambassador", "high commissioner",
    "permanent representative",
    # Agency heads
    "director general", "director-general",
    "executive director", "managing director",
    "commissioner",
    # SOE heads
    "chairman of", "chairperson of",
    "chief executive officer", "ceo",
    "board chairman",
    # Regional/State leaders
    "governor", "deputy governor",
    "premier", "chief minister",
    "regional minister",
    # Deputies and former officials
    "former governor", "former minister", "former senator",
    "deputy", "member of the house",
]

TIER_2_INSTITUTIONS = [
    "parliament", "national assembly", "senate",
    "house of representatives", "house of reps",
    "high court", "court of appeal", "federal high court",
    # Major SOEs
    "cocobod", "ghana cocoa board",
    "nnpc", "nnpcl", "nigerian national petroleum",
    "eskom", "transnet", "south african airways",
    "kenya power", "kenya airways",
    "ghana national petroleum", "gnpc",
    "nigeria ports authority", "npa",
    "electoral commission", "inec",
    "anti-corruption", "efcc", "eoco", "chraj",
]

# ── TIER 3: Other PEPs ──

TIER_3_TITLES = [
    "mayor", "metropolitan chief executive",
    "municipal chief executive", "district chief executive",
    "local government chairman", "local government chair",
    "councillor", "council member",
    "magistrate", "district judge",
    "deputy minister", "assistant minister",
    "acting minister",
    "permanent secretary", "deputy director",
    "special adviser", "special advisor",
]

TIER_3_INSTITUTIONS = [
    "local government", "district assembly",
    "metropolitan assembly", "municipal assembly",
    "city council", "county government",
    "magistrate court", "district court",
]


def classify_pep_tier(title: str, institution: str = "") -> int:
    """Classify a PEP into tier 1, 2, or 3 based on FATF guidelines.

    Args:
        title: Position title (e.g., "Minister of Finance")
        institution: Organisation name (e.g., "Federal Executive Council")

    Returns:
        PEP tier: 1 (highest), 2 (senior), or 3 (other)
    """
    title_lower = title.lower().strip() if title else ""
    inst_lower = institution.lower().strip() if institution else ""
    combined = f"{title_lower} {inst_lower}"

    # Check from highest risk to lowest: Tier 1 -> Tier 2 -> Tier 3
    # This ensures "Deputy Governor of the Central Bank" matches
    # "central bank" (Tier 1) before "deputy" (Tier 2/3).
    for pattern in TIER_1_TITLES:
        if pattern in combined:
            log.debug("tier_classified", tier=1, title=title, match=pattern)
            return 1

    for pattern in TIER_1_INSTITUTIONS:
        if pattern in inst_lower:
            log.debug("tier_classified", tier=1, institution=institution, match=pattern)
            return 1

    for pattern in TIER_2_TITLES:
        if pattern in combined:
            log.debug("tier_classified", tier=2, title=title, match=pattern)
            return 2

    for pattern in TIER_2_INSTITUTIONS:
        if pattern in inst_lower:
            log.debug("tier_classified", tier=2, institution=institution, match=pattern)
            return 2

    for pattern in TIER_3_TITLES:
        if pattern in combined:
            log.debug("tier_classified", tier=3, title=title, match=pattern)
            return 3

    for pattern in TIER_3_INSTITUTIONS:
        if pattern in inst_lower:
            log.debug("tier_classified", tier=3, institution=institution, match=pattern)
            return 3

    # Default: if we have any title or institution, classify as tier 2
    # (conservative approach — better to over-classify than miss)
    if title_lower or inst_lower:
        log.debug("tier_default", tier=2, title=title, institution=institution)
        return 2

    return 3


def get_tier_description(tier: int) -> str:
    """Human-readable tier description."""
    descriptions = {
        1: "Tier 1 - Head of State/Government Level (highest risk)",
        2: "Tier 2 - Senior Official (elevated risk)",
        3: "Tier 3 - Other PEP (standard enhanced due diligence)",
    }
    return descriptions.get(tier, f"Unknown tier: {tier}")


def is_high_risk_pep(tier: int) -> bool:
    """Whether this PEP tier requires enhanced due diligence."""
    return tier <= 2
