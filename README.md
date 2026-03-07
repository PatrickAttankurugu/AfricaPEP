# AfricaPEP — African Politically Exposed Persons Database

A production-grade, open-source PEP (Politically Exposed Persons) database built specifically for the African market. Designed for KYC/AML compliance teams who need reliable PEP screening without expensive third-party data subscriptions.

**Zero dependency on paid PEP databases.** All data sourced directly from official African government websites — parliaments, gazettes, electoral commissions, and presidencies.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        DATA SOURCES                             │
│  Parliament Sites │ Gov Gazettes (PDF) │ Electoral Commissions  │
│  Presidency Sites │ Judiciary Websites  │ SOE Boards             │
└────────────┬────────────────┬────────────────┬──────────────────┘
             │                │                │
             ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────┐
│                     SCRAPER LAYER                               │
│  BeautifulSoup │ Playwright (JS) │ PDF Parser (pdfplumber+OCR) │
│  Rate limiting │ Retry (3x)      │ Robots.txt respect          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     NLP PIPELINE                                │
│  spaCy NER │ Custom EntityRuler │ Regex Pattern Matching        │
│  Name normalisation │ Date extraction │ Relationship detection  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                  ENTITY RESOLUTION                              │
│  Blocking (country+surname) │ rapidfuzz scoring │ Auto-merge    │
│  >=0.85 merge │ 0.70-0.84 review │ <0.70 separate              │
└────────────┬────────────────────────────────┬───────────────────┘
             │                                │
             ▼                                ▼
┌──────────────────────┐       ┌──────────────────────────────────┐
│      NEO4J           │       │         POSTGRESQL               │
│   (Graph DB)         │──────>│      (Search Index)              │
│ Source of truth       │ sync  │ pg_trgm fuzzy match             │
│ Relationships         │       │ tsvector full-text search        │
│ Full provenance       │       │ Screening log                   │
└──────────┬───────────┘       └──────────────┬───────────────────┘
           │                                   │
           └──────────────┬────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FASTAPI                                    │
│  POST /screen │ GET /pep/{id} │ GET /pep/{id}/graph             │
│  GET /search  │ GET /stats    │ GET /health                     │
└─────────────────────────────────────────────────────────────────┘
```

## Supported Countries

| Country | Parliament | Presidency | Judiciary | Gazette | Electoral |
|---------|-----------|-----------|-----------|---------|-----------|
| Ghana   | ✅        | ✅        | ✅        | ✅      | ✅        |
| Nigeria | ✅        | ✅        | ✅        | —       | ✅        |
| Kenya   | ✅        | ✅        | —         | ✅      | —         |
| South Africa | ✅   | ✅        | —         | —       | —         |
| Rwanda  | ✅        | —         | —         | —       | —         |
| Uganda  | ✅        | —         | —         | —       | —         |
| Ethiopia | —        | ✅        | —         | —       | —         |
| Tanzania | ✅        | ✅        | —         | —       | —         |
| Senegal | —         | ✅        | —         | —       | —         |
| Namibia | ✅        | —         | —         | —       | —         |
| Cameroon | —        | ✅        | —         | —       | —         |
| Côte d'Ivoire | ✅  | —         | —         | —       | —         |
| Malawi  | —         | ✅        | —         | —       | —         |
| Zambia  | ✅        | —         | —         | —       | —         |
| Egypt   | —         | ✅        | —         | —       | —         |
| Morocco | —         | ✅        | —         | —       | —         |
| Botswana | ✅       | —         | —         | —       | —         |
| Zimbabwe | ✅       | —         | —         | —       | —         |
| Mozambique | —      | ✅        | —         | —       | —         |
| Angola  | —         | ✅        | —         | —       | —         |
| DR Congo | ✅       | —         | —         | —       | —         |
| Tunisia | —         | ✅        | —         | —       | —         |
| Gambia  | —         | ✅        | —         | —       | —         |
| Sierra Leone | —    | ✅        | —         | —       | —         |

## Quick Start (Docker)

```bash
# 1. Clone and configure
git clone <repo-url> && cd africapep
cp .env.example .env

# 2. Start all services
docker compose up -d

# 3. Initialize databases
docker compose exec api python -m africapep.database.init

# 4. Seed with fixture data
docker compose exec api python -m africapep.database.seed

# 5. API is live at http://localhost:8000
curl http://localhost:8000/health
```

## Quick Start (Local Development)

```bash
# 1. Prerequisites: Python 3.11+, Neo4j 5, PostgreSQL 15
pip install -r requirements.txt
python -m spacy download en_core_web_lg
python -m playwright install chromium

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
  -d '{"name": "Kwame Mensah", "country": "GH", "threshold": 0.75}'
```

Response:
```json
{
  "query": "Kwame Mensah",
  "matches": [
    {
      "pep_id": "uuid-here",
      "matched_name": "Kwame Asante Mensah",
      "match_score": 0.89,
      "pep_tier": 2,
      "is_active": true,
      "positions": [{"title": "Member of Parliament", "institution": "Parliament of Ghana"}],
      "nationality": "GH"
    }
  ],
  "screening_id": "uuid",
  "screened_at": "2024-01-01T00:00:00Z"
}
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

### Search

```bash
curl "http://localhost:8000/api/v1/search?q=minister&country=GH&tier=1&active=true"
```

### Statistics

```bash
curl http://localhost:8000/api/v1/stats
```

## Run Scrapers Manually

```bash
# All scrapers
python -c "from africapep.scheduler.jobs import run_all_scrapers; run_all_scrapers()"

# Gazette scrapers only
python -c "from africapep.scheduler.jobs import run_gazette_scrapers; run_gazette_scrapers()"

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

1. **Blocking:** Group candidates by `country_code + surname_initial` to avoid O(n²)
2. **Scoring:** Weighted composite:
   - Name similarity (rapidfuzz token_sort_ratio): 50%
   - Date of birth match: 30%
   - Position/institution match: 20%
3. **Decision:**
   - Score ≥ 0.85 → Auto-merge
   - Score 0.70–0.84 → Flag for review
   - Score < 0.70 → Separate entities
4. **Merging:** All source records preserved. Name variants accumulated. Most restrictive PEP tier kept.

## Adding a New Country Scraper

1. Create `africapep/scraper/spiders/{country}_{source}.py`
2. Inherit from `BaseScraper` (or `BaseGovGazetteScraper` for gazette PDFs)
3. Implement `scrape()` and `_load_fixture()` methods
4. Add to `ALL_SCRAPERS` in `africapep/scraper/spiders/__init__.py`
5. Add fixture test in `tests/test_scrapers.py`
6. Update PEP tier classifier with country-specific titles

```python
from africapep.scraper.base_scraper import BaseScraper, RawPersonRecord

class NewCountryScraper(BaseScraper):
    country_code = "XX"
    source_type = "PARLIAMENT"

    def scrape(self) -> list[RawPersonRecord]:
        # Your scraping logic here
        ...

    def _load_fixture(self) -> list[RawPersonRecord]:
        return self._synthetic_fixture()
```

## Data Source Update Frequencies

| Source | Schedule | Day |
|--------|----------|-----|
| All scrapers | Weekly | Sunday 02:00 UTC |
| Gazette scrapers | Mid-week | Wednesday 06:00 UTC |
| Neo4j → PostgreSQL sync | Weekly | Sunday 06:00 UTC |
| Stats logging | Daily | 00:00 UTC |

## Running Tests

```bash
pytest tests/ -v

# Specific test file
pytest tests/test_pipeline.py -v

# With coverage
pytest tests/ --cov=africapep --cov-report=html
```

## Project Structure

```
africapep/
├── api/            # FastAPI routes + Pydantic schemas
├── database/       # Neo4j client, PostgreSQL client, ORM models, sync
├── pipeline/       # NLP extractor, normaliser, classifier, resolver
├── scraper/        # Base scraper, spiders (per country/source), utils
└── scheduler/      # APScheduler job definitions
```

## Design Principles

- **Full source provenance:** Every record links to a `SourceRecord` with URL + scrape timestamp
- **Never delete:** Positions are end-dated, not deleted. Inactive PEPs are flagged, not removed
- **Polite scraping:** 2s+ delay between requests, User-Agent identification, robots.txt respect
- **Graph-first:** Neo4j is the source of truth; PostgreSQL is a search index synced from it

## License

MIT
