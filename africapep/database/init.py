"""Database initialization script.
Run with: python -m africapep.database.init
"""
import sys
from pathlib import Path
import structlog

from africapep.database.neo4j_client import neo4j_client
from africapep.database.postgres_client import verify_connectivity, apply_schema

log = structlog.get_logger()
SCHEMA_DIR = Path(__file__).parent / "schema"


def main():
    print("=" * 40)
    print("  AfricaPEP Database Initialization")
    print("=" * 40)
    print()

    # 1. PostgreSQL
    print("[1/4] Checking PostgreSQL connectivity...")
    if not verify_connectivity():
        print("  FAIL: Cannot connect to PostgreSQL")
        sys.exit(1)
    print("  OK")

    print("[2/4] Applying PostgreSQL schema...")
    apply_schema(str(SCHEMA_DIR / "postgres_schema.sql"))
    print("  OK")

    # 2. Neo4j
    print("[3/4] Checking Neo4j connectivity...")
    if not neo4j_client.verify_connectivity():
        print("  FAIL: Cannot connect to Neo4j")
        sys.exit(1)
    print("  OK")

    print("[4/4] Applying Neo4j constraints and indexes...")
    neo4j_client.apply_constraints(str(SCHEMA_DIR / "neo4j_constraints.cypher"))
    print("  OK")

    # 3. Seed countries
    print()
    print("Seeding African countries...")
    _seed_countries()
    print("  OK")

    print()
    print("=" * 40)
    print("  Initialization complete!")
    print("=" * 40)
    neo4j_client.close()


AFRICAN_COUNTRIES = {
    "GH": ("Ghana", "WEST_AFRICA"),
    "NG": ("Nigeria", "WEST_AFRICA"),
    "KE": ("Kenya", "EAST_AFRICA"),
    "ZA": ("South Africa", "SOUTHERN_AFRICA"),
    "ET": ("Ethiopia", "EAST_AFRICA"),
    "TZ": ("Tanzania", "EAST_AFRICA"),
    "UG": ("Uganda", "EAST_AFRICA"),
    "SN": ("Senegal", "WEST_AFRICA"),
    "CI": ("Cote d'Ivoire", "WEST_AFRICA"),
    "CM": ("Cameroon", "CENTRAL_AFRICA"),
    "AO": ("Angola", "SOUTHERN_AFRICA"),
    "MZ": ("Mozambique", "SOUTHERN_AFRICA"),
    "ZW": ("Zimbabwe", "SOUTHERN_AFRICA"),
    "RW": ("Rwanda", "EAST_AFRICA"),
    "BW": ("Botswana", "SOUTHERN_AFRICA"),
    "NA": ("Namibia", "SOUTHERN_AFRICA"),
    "EG": ("Egypt", "NORTH_AFRICA"),
    "MA": ("Morocco", "NORTH_AFRICA"),
    "TN": ("Tunisia", "NORTH_AFRICA"),
    "DZ": ("Algeria", "NORTH_AFRICA"),
    "MW": ("Malawi", "SOUTHERN_AFRICA"),
    "ZM": ("Zambia", "SOUTHERN_AFRICA"),
    "CD": ("Democratic Republic of the Congo", "CENTRAL_AFRICA"),
    "GM": ("Gambia", "WEST_AFRICA"),
    "SL": ("Sierra Leone", "WEST_AFRICA"),
    "BJ": ("Benin", "WEST_AFRICA"),
    "BF": ("Burkina Faso", "WEST_AFRICA"),
    "BI": ("Burundi", "EAST_AFRICA"),
    "CV": ("Cape Verde", "WEST_AFRICA"),
    "CF": ("Central African Republic", "CENTRAL_AFRICA"),
    "TD": ("Chad", "CENTRAL_AFRICA"),
    "KM": ("Comoros", "EAST_AFRICA"),
    "CG": ("Republic of the Congo", "CENTRAL_AFRICA"),
    "DJ": ("Djibouti", "EAST_AFRICA"),
    "GQ": ("Equatorial Guinea", "CENTRAL_AFRICA"),
    "ER": ("Eritrea", "EAST_AFRICA"),
    "SZ": ("Eswatini", "SOUTHERN_AFRICA"),
    "GA": ("Gabon", "CENTRAL_AFRICA"),
    "GN": ("Guinea", "WEST_AFRICA"),
    "GW": ("Guinea-Bissau", "WEST_AFRICA"),
    "LS": ("Lesotho", "SOUTHERN_AFRICA"),
    "LR": ("Liberia", "WEST_AFRICA"),
    "LY": ("Libya", "NORTH_AFRICA"),
    "MG": ("Madagascar", "EAST_AFRICA"),
    "ML": ("Mali", "WEST_AFRICA"),
    "MR": ("Mauritania", "WEST_AFRICA"),
    "MU": ("Mauritius", "EAST_AFRICA"),
    "NE": ("Niger", "WEST_AFRICA"),
    "ST": ("Sao Tome and Principe", "CENTRAL_AFRICA"),
    "SC": ("Seychelles", "EAST_AFRICA"),
    "SO": ("Somalia", "EAST_AFRICA"),
    "SS": ("South Sudan", "EAST_AFRICA"),
    "SD": ("Sudan", "NORTH_AFRICA"),
    "TG": ("Togo", "WEST_AFRICA"),
}


def _seed_countries():
    for code, (name, region) in AFRICAN_COUNTRIES.items():
        neo4j_client.ensure_country(code, name, region)


if __name__ == "__main__":
    main()
