# AfricaPEP — African Politically Exposed Persons Database

[![CI](https://github.com/PatrickAttankurugu/AfricaPEP/actions/workflows/ci.yml/badge.svg)](https://github.com/PatrickAttankurugu/AfricaPEP/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-compose-blue.svg)](https://docs.docker.com/compose/)
[![Tests](https://img.shields.io/badge/tests-170%2B-brightgreen.svg)](#running-tests)
[![Countries](https://img.shields.io/badge/countries-54-orange.svg)](#database-coverage)
[![PEPs](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fapi-pep.patrickaiafrica.com%2Fapi%2Fv1%2Fstats&query=%24.total_peps&label=PEP%20profiles&color=8A2BE2)](#database-coverage)
[![Contributing](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

A production-grade, open-source PEP (Politically Exposed Persons) database covering **all 54 African Union member states**. Built for KYC/AML compliance teams who need reliable PEP screening without expensive third-party data subscriptions.

**Live demo:** [pep.patrickaiafrica.com](https://pep.patrickaiafrica.com) |**Frontend repo:** [africapep-frontend](https://github.com/PatrickAttankurugu/africapep-frontend)

## Why AfricaPEP?

- **48,000+ verified PEP profiles** — Sourced from Wikidata's community-maintained, referenced database
- **Complete African coverage** — All 54 AU member states
- **Free and open source** — No licensing fees, no API quotas, no vendor lock-in
- **Graph-powered** — Neo4j captures PEP relationships, family ties, and political networks
- **Fuzzy matching** — pg_trgm + rapidfuzz catches name variations, transliterations, and misspellings
- **FATF-compliant** — Tier 1/2/3 classification per FATF Recommendation 12
- **Full audit trail** — Every screening logged, every data point traceable to its source

## Data Source

AfricaPEP pulls verified politician data from [Wikidata](https://www.wikidata.org/), a free, collaborative knowledge base maintained by the Wikimedia Foundation. Every record in Wikidata is community-verified and linked to references (Wikipedia, government websites, news sources).

The scraper queries Wikidata's public SPARQL endpoint for all persons who hold or held political positions in African countries. This includes:

- Presidents, Vice Presidents, Prime Ministers
- Cabinet Ministers and Deputy Ministers
- Members of Parliament and Senate
- Judges (Supreme Court, Constitutional Court, Appeals Court)
- Governors, Regional Commissioners
- Central Bank officials
- Military and intelligence leadership
- Electoral commission members
- Heads of state-owned enterprises
- Ambassadors
- Political party leaders

**Re-seeding pulls fresh data** — run `python -m africapep.database.seed` anytime to get the latest from Wikidata.

Wikidata is currently the sole data source, queried through one parameterized SPARQL scraper that runs per country. The scraper framework (rate limiting, retries, per-source isolation) is built to support national sources such as government gazettes, electoral commissions, and judiciary websites: these are open contribution opportunities, tracked as [`new-scraper` issues](https://github.com/PatrickAttankurugu/AfricaPEP/issues?q=is%3Aissue+is%3Aopen+label%3Anew-scraper).

## Architecture

```
+-------------------------------------------------------------+
|                        DATA SOURCE                          |
|              Wikidata SPARQL Endpoint                       |
|    Community-verified | Referenced | 48,000+ African PEPs  |
+-------------------------------------------------------------+
                             |
                             v
+-------------------------------------------------------------+
|                   WIKIDATA SCRAPER                          |
|  SPARQL queries per country | Rate-limited | Deduplication  |
|  Polite 2s delay between countries | 54 country queries     |
+-------------------------------------------------------------+
                             |
                             v
+-------------------------------------------------------------+
|                     NLP PIPELINE                            |
|  Name normalisation | FATF Tier classification              |
|  Entity resolution (rapidfuzz) | Duplicate merging          |
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
|  POST /screen | POST /screen/batch | GET /search            |
|  GET /stats   | GET /countries     | GET /health            |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|                   NEXT.JS FRONTEND                          |
|  Name screening | Batch screening | Country coverage        |
|  PEP search     | Statistics dashboard                     |
+-------------------------------------------------------------+
```

## Quick Start

One command from clone to a working, populated screening API:

```bash
git clone https://github.com/PatrickAttankurugu/AfricaPEP.git && cd AfricaPEP
make quickstart
```

That boots Neo4j + PostgreSQL + the API, applies schema, and seeds the bundled offline sample dataset (2 countries, ~500 real records, no live scraping). Takes 2-3 minutes on a cold clone, most of it the Docker image build.

```bash
# Verify
curl http://localhost:8000/health
curl -X POST http://localhost:8000/api/v1/screen -H "Content-Type: application/json" -d '{"name": "Adama Barrow"}'

# When you want the full dataset: live-seed all 54 countries from Wikidata (48,000+ profiles, takes a while)
make seed
```

## Local Development (Hot-Reload)

To run the API and scraper with instantaneous hot-reloading for local development:

```bash
# First ensure setup was run
make setup

# Stop the original detached containers
docker compose down

# Run the development environment with hot-reloading
make run
```

## API Documentation

Interactive docs at `http://localhost:8000/docs` (Swagger UI) or `/redoc`.

For complete endpoint documentation, authentication details, request and response examples, validation rules, rate limits, and error handling, see:

- [API Guide](docs/API.md)


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

### Batch Screening (up to 50 names)

```bash
curl -X POST http://localhost:8000/api/v1/screen/batch \
  -H "Content-Type: application/json" \
  -d '{
    "names": [
      {"name": "Bola Tinubu", "country": "NG"},
      {"name": "Paul Kagame"},
      {"name": "Cyril Ramaphosa", "country": "ZA"}
    ],
    "threshold": 0.65
  }'
```

### Search PEPs

```bash
curl "http://localhost:8000/api/v1/search?q=minister&country=GH&tier=1&active=true"
```

### Country Coverage

```bash
curl http://localhost:8000/api/v1/countries
```

### Statistics

```bash
curl http://localhost:8000/api/v1/stats
```

## Run Scrapers Manually

```bash
# Scrape a single country from Wikidata
python -c "
from africapep.scraper.spiders.wikidata_scraper import WikidataScraper
records = WikidataScraper(country_code='NG').scrape()
print(f'Found {len(records)} PEPs for Nigeria')
"

# Full re-seed (all 54 countries)
python -m africapep.database.seed

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

## Matching Quality

Name matching is measured, not asserted. A QID-grounded evaluation harness (`scripts/eval_name_matching.py`) scores the real production rules against labeled pairs where ground truth comes from Wikidata QIDs, including deliberately hard cases: transliterations (Mohammed/Muhammad), diacritics, and different people who share a blocking bucket.

Current results on the 23-pair adversarial fixture:

| Rule | Precision | Recall | F1 |
|------|-----------|--------|-----|
| Screening (threshold 0.75, recall-first) | 0.71 | 1.00 | 0.83 |
| High threshold 0.90, orthographic only | 0.91 | 0.83 | 0.87 |
| High threshold 0.90, + phonetic | 0.92 | 1.00 | 0.96 |
| Auto-merge gate (orthographic >= 0.85) | 0.92 | 1.00 | 0.96 |

Two design decisions fall straight out of these numbers: screening is deliberately recall-first (a compliance analyst reviews candidates; a missed PEP is worse than a false candidate), while merging is precision-first with corroboration required for phonetic-only matches (a false merge could flag an innocent person).

The fixture set is small and grows by contribution: if you know name variants from your country that should (or should not) match, adding labeled pairs to `tests/fixtures/name_match_pairs.json` is a five-minute contribution that directly hardens the matcher. Run the harness with `python scripts/eval_name_matching.py`.

## Project Structure

```
africapep/
├── api/            # FastAPI routes + Pydantic schemas
├── database/       # Neo4j client, PostgreSQL client, sync, seed
├── pipeline/       # NLP normaliser, FATF classifier, entity resolver
├── scraper/        # BaseScraper + WikidataScraper (SPARQL-based)
└── scheduler/      # APScheduler job definitions
tests/              # 170+ tests covering scraper, pipeline, and API
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


## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Good first issues

New to the project? Look for issues labeled [`good first issue`](https://github.com/PatrickAttankurugu/AfricaPEP/labels/good%20first%20issue). Currently open:

- Add French name transliteration support (#2)
- Improve FATF tier classification for judiciary roles (#3)
- Add party affiliation extraction from Wikidata (#5)
- Add AU, ECOWAS, SADC, and EAC officials as regional PEPs (#7)
- Add Arabic name transliteration for North African countries (#8)
- Add Docker Compose one-command local setup (#14)

You do not need to write code to contribute: compliance professionals can validate country data quality (#15). See [CONTRIBUTING-DATA.md](CONTRIBUTING-DATA.md).

### Other ways to contribute

- **Add supplementary data sources** — Government gazettes, electoral commissions, judiciary websites
- **Improve NLP pipeline** — Better name normalisation, African naming conventions, relationship detection
- **Add regional bodies** — AU Commission, ECOWAS, SADC, EAC officials
- **Frontend** — Improve the Next.js screening UI, add data visualisations
- **Documentation** — Improve docs, add tutorials, translate to French/Arabic/Portuguese
- **Testing** — Add edge cases, performance tests, end-to-end tests

## Design Principles

- **Verified data sources:** All PEP data sourced from Wikidata's referenced, community-maintained database
- **Full source provenance:** Every record links to a `SourceRecord` with source URL + scrape timestamp
- **Never delete:** Positions are end-dated, not deleted. Inactive PEPs are flagged, not removed
- **Polite scraping:** Rate-limited queries, User-Agent identification
- **Graph-first:** Neo4j is the source of truth; PostgreSQL is a search index synced from it
- **Industry-standard API:** Screening responses follow OpenSanctions/ComplyAdvantage patterns

## Community

- [ROADMAP](ROADMAP.md) — Where the project is going
- [GitHub Discussions](https://github.com/PatrickAttankurugu/AfricaPEP/discussions) — Ask questions, share ideas
- [GitHub Issues](https://github.com/PatrickAttankurugu/AfricaPEP/issues) — Report bugs, request features
- [CHANGELOG](CHANGELOG.md) — See what's new
- [Security Policy](SECURITY.md) — Report vulnerabilities responsibly

## Author

**Patrick Attankurugu** — [LinkedIn](https://www.linkedin.com/in/patrick-ai-africa/) | [X/Twitter](https://x.com/patrickaiafrica) | [Email](mailto:patricka.azuma@gmail.com)

## License

MIT - see [LICENSE](LICENSE) for details.
