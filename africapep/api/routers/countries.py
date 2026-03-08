"""GET /api/v1/countries — list all supported African countries with PEP counts."""
import asyncio
import time as _time

from fastapi import APIRouter
from sqlalchemy import text
import structlog

from africapep.database.postgres_client import get_db

log = structlog.get_logger()
router = APIRouter()

# ── Simple in-memory TTL cache ──
_COUNTRIES_CACHE_TTL = 600  # 10 minutes
_countries_cache: dict = {"data": None, "expires_at": 0.0}

REGIONS = {
    "DZ": "North", "EG": "North", "LY": "North", "MA": "North", "TN": "North", "SD": "North",
    "BJ": "West", "BF": "West", "CV": "West", "CI": "West", "GM": "West", "GH": "West",
    "GN": "West", "GW": "West", "LR": "West", "ML": "West", "MR": "West", "NE": "West",
    "NG": "West", "SN": "West", "SL": "West", "TG": "West",
    "BI": "East", "KM": "East", "DJ": "East", "ER": "East", "ET": "East", "KE": "East",
    "MG": "East", "MU": "East", "MZ": "East", "RW": "East", "SC": "East", "SO": "East",
    "SS": "East", "TZ": "East", "UG": "East",
    "AO": "Central", "CM": "Central", "CF": "Central", "TD": "Central", "CG": "Central",
    "CD": "Central", "GQ": "Central", "GA": "Central", "ST": "Central",
    "BW": "Southern", "SZ": "Southern", "LS": "Southern", "MW": "Southern", "NA": "Southern",
    "ZA": "Southern", "ZM": "Southern", "ZW": "Southern",
}

COUNTRY_NAMES = {
    "DZ": "Algeria", "AO": "Angola", "BJ": "Benin", "BW": "Botswana", "BF": "Burkina Faso",
    "BI": "Burundi", "CM": "Cameroon", "CV": "Cape Verde", "CF": "Central African Republic",
    "TD": "Chad", "KM": "Comoros", "CG": "Congo (Brazzaville)", "CD": "DR Congo",
    "CI": "Cote d'Ivoire", "DJ": "Djibouti", "EG": "Egypt", "GQ": "Equatorial Guinea",
    "ER": "Eritrea", "SZ": "Eswatini", "ET": "Ethiopia", "GA": "Gabon", "GM": "Gambia",
    "GH": "Ghana", "GN": "Guinea", "GW": "Guinea-Bissau", "KE": "Kenya", "LS": "Lesotho",
    "LR": "Liberia", "LY": "Libya", "MG": "Madagascar", "MW": "Malawi", "ML": "Mali",
    "MR": "Mauritania", "MU": "Mauritius", "MA": "Morocco", "MZ": "Mozambique",
    "NA": "Namibia", "NE": "Niger", "NG": "Nigeria", "RW": "Rwanda",
    "ST": "Sao Tome & Principe", "SN": "Senegal", "SC": "Seychelles", "SL": "Sierra Leone",
    "SO": "Somalia", "ZA": "South Africa", "SS": "South Sudan", "SD": "Sudan",
    "TZ": "Tanzania", "TG": "Togo", "TN": "Tunisia", "UG": "Uganda", "ZM": "Zambia",
    "ZW": "Zimbabwe",
}


def _fetch_country_counts():
    """Fetch PEP counts per country from the database (sync)."""
    counts = {}
    try:
        with get_db() as db:
            rows = db.execute(text(
                "SELECT COALESCE(nationality, 'XX'), COUNT(*) "
                "FROM pep_profiles GROUP BY nationality"
            )).fetchall()
            counts = {row[0]: row[1] for row in rows}
    except Exception:
        pass
    return counts


@router.get("/countries")
async def list_countries():
    """List all 54 supported African countries with PEP counts and regions.

    Results are cached in-memory for 10 minutes.
    """
    now = _time.monotonic()
    if _countries_cache["data"] is not None and now < _countries_cache["expires_at"]:
        return _countries_cache["data"]

    # Get PEP counts per country from database
    counts = await asyncio.to_thread(_fetch_country_counts)

    countries = []
    for code, name in sorted(COUNTRY_NAMES.items(), key=lambda x: x[1]):
        countries.append({
            "code": code,
            "name": name,
            "region": REGIONS.get(code, "Unknown"),
            "pep_count": counts.get(code, 0),
        })

    result = {
        "total_countries": len(countries),
        "countries": countries,
    }

    _countries_cache["data"] = result
    _countries_cache["expires_at"] = now + _COUNTRIES_CACHE_TTL

    return result
