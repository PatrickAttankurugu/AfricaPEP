# AfricaPEP — African Politically Exposed Persons Database

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-compose-blue.svg)](https://docs.docker.com/compose/)
[![Tests](https://img.shields.io/badge/tests-131%20passing-brightgreen.svg)](#running-tests)
[![Countries](https://img.shields.io/badge/countries-54-orange.svg)](#supported-countries-54)
[![PEPs](https://img.shields.io/badge/PEP%20profiles-4%2C243-purple.svg)](#database-coverage)

A production-grade, open-source PEP (Politically Exposed Persons) database covering **all 54 African Union member states**. Built for KYC/AML compliance teams who need reliable PEP screening without expensive third-party data subscriptions.

**Zero dependency on paid PEP databases.** All data sourced directly from official African government websites — parliaments, gazettes, electoral commissions, and presidencies.

## Why AfricaPEP?

- **Complete African coverage** — All 54 AU member states with 65 data scrapers
- **Free and open source** — No licensing fees, no API quotas, no vendor lock-in
- **Graph-powered** — Neo4j captures PEP relationships, family ties, and political networks
- **Fuzzy matching** — pg_trgm + rapidfuzz catches name variations, transliterations, and misspellings
- **FATF-compliant** — Tier 1/2/3 classification per FATF Recommendation 12
- **Full audit trail** — Every screening logged, every data point traceable to its source URL

## Architecture

```
+-------------------------------------------------------------+
|                        DATA SOURCES                         |
|  Parliament Sites | Gov Gazettes (PDF) | Electoral Commissions  |
|  Presidency Sites | Judiciary Websites  | SOE Boards             |
+-------------------------------------------------------------+
                             |
                             v
+-------------------------------------------------------------+
|                     SCRAPER LAYER                           |
|  BeautifulSoup | Playwright (JS) | PDF Parser (pdfplumber)  |
|  Rate limiting | Retry (3x)      | Robots.txt respect       |
+-------------------------------------------------------------+
                             |
                             v
+-------------------------------------------------------------+
|                     NLP PIPELINE                            |
|  spaCy NER | Custom EntityRuler | Regex Pattern Matching    |
|  Name normalisation | Date extraction | Relationship detect |
+-------------------------------------------------------------+
                             |
                             v
+-------------------------------------------------------------+
|                  ENTITY RESOLUTION                          |
|  Blocking (country+surname) | rapidfuzz scoring | Auto-merge|
|  >=0.85 merge | 0.70-0.84 review | <0.70 separate          |
+-------------------------------------------------------------+
             |                                |
             v                                v
+----------------------+       +------------------------------+
|      NEO4J           |       |         POSTGRESQL           |
|   (Graph DB)         |------>|      (Search Index)          |
| Source of truth       | sync  | pg_trgm fuzzy match         |
| Relationships         |       | tsvector full-text search    |
| Full provenance       |       | Screening log               |
+----------------------+       +------------------------------+
           |                                   |
           +------------------+----------------+
                              v
+-------------------------------------------------------------+
|                      FASTAPI                                |
|  POST /screen | GET /pep/{id} | GET /pep/{id}/graph         |
|  GET /search  | GET /stats    | GET /health                 |
+-------------------------------------------------------------+
```

## Database Coverage

**4,243 PEP profiles** across all 54 African Union member states, sourced from 65 data scrapers:

| # | Country | Code | PEPs | Sources |
|---|---------|------|-----:|---------|
| 1 | Nigeria | NG | **432** | Presidency, National Assembly, Judiciary, Governors, INEC |
| 2 | Ghana | GH | **380** | Presidency, Parliament, Judiciary, Gazette, Electoral Commission |
| 3 | Kenya | KE | **189** | Presidency, Parliament, Gazette |
| 4 | Tanzania | TZ | **138** | Presidency, Parliament |
| 5 | South Africa | ZA | **121** | Presidency, Parliament |
| 6 | Cameroon | CM | **84** | Presidency |
| 7 | Rwanda | RW | **68** | Parliament |
| 8 | Uganda | UG | **67** | Parliament |
| 9 | Morocco | MA | **65** | Presidency |
| 10 | Tunisia | TN | **63** | Presidency |
| 11 | Ethiopia | ET | **63** | Presidency |
| 12 | Egypt | EG | **63** | Presidency |
| 13 | Zambia | ZM | **63** | Parliament |
| 14 | Algeria | DZ | **63** | Presidency |
| 15 | Mauritius | MU | **62** | Presidency |
| 16 | Liberia | LR | **62** | Presidency |
| 17 | Central African Rep. | CF | **62** | Presidency |
| 18 | Burundi | BI | **62** | Presidency |
| 19 | Mali | ML | **62** | Presidency |
| 20 | Malawi | MW | **62** | Presidency |
| 21 | Gambia | GM | **62** | Presidency |
| 22 | Zimbabwe | ZW | **62** | Parliament |
| 23 | Congo (Brazzaville) | CG | **62** | Presidency |
| 24 | Niger | NE | **61** | Presidency |
| 25 | Libya | LY | **61** | Presidency |
| 26 | DR Congo | CD | **61** | Parliament |
| 27 | Benin | BJ | **61** | Presidency |
| 28 | South Sudan | SS | **61** | Presidency |
| 29 | Gabon | GA | **61** | Presidency |
| 30 | Namibia | NA | **61** | Parliament |
| 31 | Botswana | BW | **61** | Parliament |
| 32 | Lesotho | LS | **61** | Presidency |
| 33 | Madagascar | MG | **60** | Presidency |
| 34 | Senegal | SN | **60** | Presidency |
| 35 | Mozambique | MZ | **60** | Presidency |
| 36 | Chad | TD | **60** | Presidency |
| 37 | Eritrea | ER | **60** | Presidency |
| 38 | Sudan | SD | **60** | Presidency |
| 39 | Togo | TG | **60** | Presidency |
| 40 | Eswatini | SZ | **59** | Presidency |
| 41 | Cote d'Ivoire | CI | **59** | Parliament |
| 42 | Comoros | KM | **59** | Presidency |
| 43 | Guinea-Bissau | GW | **59** | Presidency |
| 44 | Sierra Leone | SL | **59** | Presidency |
| 45 | Djibouti | DJ | **59** | Presidency |
| 46 | Angola | AO | **59** | Presidency |
| 47 | Sao Tome & Principe | ST | **58** | Presidency |
| 48 | Mauritania | MR | **58** | Presidency |
| 49 | Guinea | GN | **57** | Presidency |
| 50 | Equatorial Guinea | GQ | **57** | Presidency |
| 51 | Cape Verde | CV | **56** | Presidency |
| 52 | Seychelles | SC | **54** | Presidency |
| 53 | Burkina Faso | BF | **53** | Presidency |
| 54 | Somalia | SO | **51** | Presidency |
| | **TOTAL** | | **4,243** | **65 scrapers** |

## Quick Start (Docker)

```bash
# 1. Clone and configure
git clone https://github.com/PatrickAttankurugu/AfricaPEP.git && cd AfricaPEP
cp .env.example .env

# 2. Start all services
docker compose up -d

# 3. Initialize databases
docker compose exec api python -m africapep.database.init

# 4. Seed with PEP data (4,200+ profiles across all 54 countries)
docker compose exec api python -m africapep.database.seed

# 5. API is live at http://localhost:8000
curl http://localhost:8000/health
```

## Quick Start (Local Development)

```bash
# 1. Prerequisites: Python 3.11+, Neo4j 5, PostgreSQL 15
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# 2. Configure
cp .env.example .env
# Edit .env with your database credentials

# 3. Initialize and seed
python -m africapep.database.init
python -m africapep.database.seed

# 4. Start API
uvicorn africapep.api.main:app --reload --port 8000
```

## API Documentation

Interactive docs at `http://localhost:8000/docs` (Swagger UI) or `/redoc`.

### Screen a Name

```bash
curl -X POST http://localhost:8000/api/v1/screen \
  -H "Content-Type: application/json" \
  -d '{"name": "William Ruto", "threshold": 0.75}'
```

Response:
```json
{
  "query": "William Ruto",
  "matches": [
    {
      "pep_id": "uuid-here",
      "matched_name": "William Samoei Ruto",
      "match_score": 1.0,
      "pep_tier": 1,
      "is_active": true,
      "positions": [{"title": "President of the Republic of Kenya", "institution": "Office Of The President Of Kenya"}],
      "nationality": "KE"
    }
  ],
  "screening_id": "uuid",
  "screened_at": "2026-03-07T00:00:00Z"
}
```

### Search PEPs

```bash
curl "http://localhost:8000/api/v1/search?q=minister&country=GH&tier=1&active=true"
```

### Get PEP Profile

```bash
curl http://localhost:8000/api/v1/pep/{pep_id}
```

### Get Relationship Graph

```bash
# Returns JSON suitable for D3.js / vis.js rendering
curl http://localhost:8000/api/v1/pep/{pep_id}/graph
```

### Statistics

```bash
curl http://localhost:8000/api/v1/stats
```

## Run Scrapers Manually

```bash
# All scrapers
python -c "from africapep.scheduler.jobs import run_all_scrapers; run_all_scrapers()"

# Single country scraper
python -c "
from africapep.scraper.spiders.ghana_parliament import GhanaParliamentScraper
records = GhanaParliamentScraper().run()
print(f'Found {len(records)} records')
"

# Sync Neo4j -> PostgreSQL
python -c "from africapep.database.sync import sync_all; sync_all()"
```

## Database Schema

### Neo4j Graph Model

**Nodes:** `Person`, `Position`, `Organisation`, `Country`, `SourceRecord`

**Relationships:**
- `(:Person)-[:HELD_POSITION]->(:Position)`
- `(:Position)-[:AT_ORGANISATION]->(:Organisation)`
- `(:Person)-[:FAMILY_OF {type}]->(:Person)`
- `(:Person)-[:ASSOCIATED_WITH {type}]->(:Person)`
- `(:Person)-[:CITIZEN_OF]->(:Country)`
- `(:Person)-[:SOURCED_FROM]->(:SourceRecord)`

### PostgreSQL Tables

- `pep_profiles` — search index with pg_trgm and tsvector
- `screening_log` — audit trail of all screening queries
- `source_records` — synced from Neo4j
- `change_log` — entity change history
- `scheduler_log` — job execution history

## PEP Tier Classification (FATF Rec. 12)

| Tier | Risk Level | Examples |
|------|-----------|---------|
| 1 | Highest | President, Ministers, Chief Justice, Central Bank Governor, Military Chiefs |
| 2 | Elevated | MPs, Senators, Judges, Ambassadors, SOE Heads, Governors |
| 3 | Standard | Mayors, Magistrates, Local Government Chairs |

## Entity Resolution Algorithm

1. **Blocking:** Group candidates by `country_code + surname_initial` to avoid O(n^2)
2. **Scoring:** Weighted composite:
   - Name similarity (rapidfuzz token_sort_ratio): 50%
   - Date of birth match: 30%
   - Position/institution match: 20%
3. **Decision:**
   - Score >= 0.85 -> Auto-merge
   - Score 0.70-0.84 -> Flag for review
   - Score < 0.70 -> Separate entities
4. **Merging:** All source records preserved. Name variants accumulated. Most restrictive PEP tier kept.

## Project Structure

```
africapep/
├── api/            # FastAPI routes + Pydantic schemas
├── database/       # Neo4j client, PostgreSQL client, ORM models, sync
├── pipeline/       # NLP extractor, normaliser, classifier, resolver
├── scraper/        # Base scraper, 65 spiders (per country/source), utils
└── scheduler/      # APScheduler job definitions
tests/              # 131 tests covering all scrapers and pipeline
docs/               # Design documents and plans
```

## Running Tests

```bash
# All tests
pytest tests/ -v

# Specific test file
pytest tests/test_scrapers.py -v

# With coverage
pytest tests/ --cov=africapep --cov-report=html

# Inside Docker
docker compose exec api python -m pytest tests/ -v
```

## Data Source Update Frequencies

| Source | Schedule | Day |
|--------|----------|-----|
| All scrapers | Weekly | Sunday 02:00 UTC |
| Gazette scrapers | Mid-week | Wednesday 06:00 UTC |
| Neo4j -> PostgreSQL sync | Weekly | Sunday 06:00 UTC |
| Stats logging | Daily | 00:00 UTC |

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Ways to contribute:

- **Add new data sources** — Parliament, judiciary, or gazette scrapers for countries that only have presidency coverage
- **Improve NLP pipeline** — Better name extraction, date parsing, or entity resolution
- **Add new countries** — Sub-national PEP lists, regional bodies (AU, ECOWAS, SADC)
- **Frontend** — Build a web UI for the screening API
- **Documentation** — Improve docs, add examples, translate to other languages

## Design Principles

- **Full source provenance:** Every record links to a `SourceRecord` with URL + scrape timestamp
- **Never delete:** Positions are end-dated, not deleted. Inactive PEPs are flagged, not removed
- **Polite scraping:** 2s+ delay between requests, User-Agent identification, robots.txt respect
- **Graph-first:** Neo4j is the source of truth; PostgreSQL is a search index synced from it

## License

MIT - see [LICENSE](LICENSE) for details.
