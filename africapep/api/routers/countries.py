"""GET /api/v1/countries — list all supported African countries with PEP counts."""
from fastapi import APIRouter
from sqlalchemy import text
import structlog

from africapep.database.postgres_client import get_db

log = structlog.get_logger()
router = APIRouter()

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


@router.get("/countries")
def list_countries():
    """List all 54 supported African countries with PEP counts and regions."""
    # Get PEP counts per country from database
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

    countries = []
    for code, name in sorted(COUNTRY_NAMES.items(), key=lambda x: x[1]):
        countries.append({
            "code": code,
            "name": name,
            "region": REGIONS.get(code, "Unknown"),
            "pep_count": counts.get(code, 0),
        })

    return {
        "total_countries": len(countries),
        "countries": countries,
    }
