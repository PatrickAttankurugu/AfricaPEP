# AfricaPEP System Design
**Date:** 2026-03-06
**Status:** Approved
**Project:** African PEP Database — KYC/AML Portfolio Project

---

## 1. Overview

AfricaPEP is a production-grade, open-source African Politically Exposed Persons (PEP)
database built entirely from official government primary sources. It is designed for the
KYC/AML space and targets the African market with zero dependency on paid PEP data vendors.

**Philosophy:**
- Zero paid data sources — all data from official African government websites
- Full source provenance on every record (URL + scrape timestamp + source type)
- Built specifically for Africa — handles African honorifics, naming conventions, gazette formats
- Polite scraping — minimum 2s delay, randomised user-agents, robots.txt respected

---

## 2. Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11+ |
| Graph DB | Neo4j 5 Community Edition |
| Search DB | PostgreSQL 15 |
| Scraping | Scrapy + Playwright + BeautifulSoup |
| PDF Parsing | pdfplumber + PyMuPDF (fitz) + pytesseract (OCR fallback) |
| NLP/NER | spaCy en_core_web_lg + custom EntityRuler |
| Fuzzy Matching | rapidfuzz |
| API | FastAPI + Uvicorn |
| Scheduler | APScheduler (embedded) |
| Containerisation | Docker + Docker Compose |
| Config | Pydantic Settings + .env |
| Logging | structlog (structured JSON to stdout) |
| Testing | pytest + pytest-asyncio + httpx |

---

## 3. Architecture

```
Government websites / Gazette PDFs
        │
        ▼
┌─────────────────────┐
│   Scraper Layer     │  (Scrapy/Playwright/BS4/pdfplumber)
│   10 spiders        │  → RawPersonRecord dataclasses
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│   NLP Pipeline      │  spaCy NER + EntityRuler
│   extractor.py      │  → structured PersonEntity
│   normaliser.py     │  → clean names, dates, ISO codes
│   classifier.py     │  → PEP tier 1/2/3
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│   Entity Resolver   │  blocking + rapidfuzz scoring
│   resolver.py       │  → merge/flag/separate decisions
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│      Neo4j          │  Graph: Person→Position→Org→Country
│   (source of truth) │  + SourceRecord nodes (never deleted)
└────────┬────────────┘
         │  sync.py (batch)
         ▼
┌─────────────────────┐
│    PostgreSQL       │  pep_profiles + tsvector search index
│   (search index)    │  screening_log, source_records,
│                     │  change_log, scheduler_log
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│    FastAPI          │  POST /screen, GET /pep/{id},
│    REST API         │  GET /graph/{id}, GET /search,
│    :8000            │  GET /stats, GET /health
└─────────────────────┘
```

---

## 4. Neo4j Graph Schema

### Node Types

```cypher
(:Person {
  id: string,           // UUID, primary key
  full_name: string,
  name_variants: list,  // all name forms found across sources
  date_of_birth: date,
  nationality: string,  // ISO 3166-1 alpha-2
  gender: string,
  pep_tier: int,        // 1=head of state, 2=senior official, 3=other PEP
  is_active_pep: bool,
  created_at: datetime,
  updated_at: datetime
})

(:Position {
  id: string,
  title: string,
  institution: string,
  country: string,
  branch: string,       // EXECUTIVE|LEGISLATIVE|JUDICIAL|MILITARY|SOE
  start_date: date,
  end_date: date,       // null if current
  is_current: bool
})

(:Organisation {
  id: string,
  name: string,
  org_type: string,     // GOVT|PARLIAMENT|SOE|PARTY|MILITARY
  country: string,
  registration_number: string
})

(:Country {
  code: string,         // ISO 3166-1 alpha-2
  name: string,
  region: string        // WEST_AFRICA|EAST_AFRICA|SOUTHERN_AFRICA|etc
})

(:SourceRecord {
  id: string,
  source_url: string,
  source_type: string,  // PARLIAMENT|GAZETTE|ELECTORAL|PRESIDENCY|JUDICIARY
  scraped_at: datetime,
  raw_text: string,
  country: string
})
```

### Relationship Types

```cypher
(:Person)-[:HELD_POSITION {start_date, end_date, is_current}]->(:Position)
(:Position)-[:AT_ORGANISATION]->(:Organisation)
(:Person)-[:FAMILY_OF {relationship_type: "SPOUSE|CHILD|SIBLING|PARENT"}]->(:Person)
(:Person)-[:ASSOCIATED_WITH {relationship_type: "BUSINESS|POLITICAL|KNOWN"}]->(:Person)
(:Person)-[:CITIZEN_OF]->(:Country)
(:Person)-[:SOURCED_FROM]->(:SourceRecord)
(:Organisation)-[:BASED_IN]->(:Country)
```

---

## 5. PostgreSQL Schema

```sql
-- Primary search table, synced from Neo4j
pep_profiles (
  id UUID PRIMARY KEY,
  neo4j_id VARCHAR,
  full_name VARCHAR,
  name_variants TEXT[],
  date_of_birth DATE,
  nationality CHAR(2),
  pep_tier SMALLINT,
  is_active_pep BOOLEAN,
  current_positions JSONB,
  country VARCHAR,
  updated_at TIMESTAMPTZ,
  search_vector TSVECTOR
)

-- API screening audit log
screening_log (
  id UUID PRIMARY KEY,
  query_name VARCHAR,
  query_date TIMESTAMPTZ,
  match_count INT,
  top_match_score FLOAT,
  results JSONB
)

-- Raw source records, synced from Neo4j
source_records (
  id UUID PRIMARY KEY,
  neo4j_id VARCHAR,
  source_url TEXT,
  source_type VARCHAR,
  country CHAR(2),
  scraped_at TIMESTAMPTZ,
  raw_text TEXT
)

-- Change detection audit trail
change_log (
  id UUID PRIMARY KEY,
  entity_id VARCHAR,
  field_changed VARCHAR,
  old_value TEXT,
  new_value TEXT,
  detected_at TIMESTAMPTZ
)

-- Scheduler run history
scheduler_log (
  id UUID PRIMARY KEY,
  job_name VARCHAR,
  started_at TIMESTAMPTZ,
  finished_at TIMESTAMPTZ,
  records_processed INT,
  status VARCHAR,         -- SUCCESS|FAILURE
  error_message TEXT
)

-- Indexes
CREATE INDEX ON pep_profiles USING GIN(search_vector);
CREATE INDEX ON pep_profiles USING GIN(name_variants);
CREATE EXTENSION pg_trgm;
CREATE INDEX ON pep_profiles USING GIN(full_name gin_trgm_ops);
```

---

## 6. Scraper Design

### RawPersonRecord Dataclass
```python
@dataclass
class RawPersonRecord:
    full_name: str
    title: str
    institution: str
    country_code: str
    source_url: str
    source_type: str
    raw_text: str
    scraped_at: datetime
    extra_fields: dict
```

### Fixture Strategy
Each spider has a `_load_fixture()` method. The same parsing logic runs on
both live HTTP responses and locally-saved fixture files. Fixtures are real
captures from the actual sites saved to `tests/fixtures/{spider_name}/`.

| Spider | URL | Method | Schedule |
|---|---|---|---|
| ghana_parliament | parliament.gh/mps | BeautifulSoup | Weekly |
| ghana_presidency | presidency.gov.gh/cabinet | Playwright | Weekly |
| ghana_ec | ec.gov.gh/results | BS4 + PDF | Election cycle |
| ghana_gazette | gazette.gov.gh | PDF + OCR | Weekly |
| nigeria_nass | nass.gov.ng/members | Playwright | Weekly |
| nigeria_presidency | statehouse.gov.ng | Playwright + BS4 | Weekly |
| nigeria_inec | inecnigeria.org | BS4 + PDF | Election cycle |
| kenya_parliament | parliament.go.ke/mps | BeautifulSoup | Weekly |
| kenya_gazette | kenyagazette.go.ke | PDF + OCR | Weekly |
| southafrica_parliament | parliament.gov.za/mps | Playwright | Weekly |

### PDF Pipeline
1. Download PDF to `./data/raw_pdfs/{country}/{filename}`
2. Extract with pdfplumber
3. If avg chars/page < 100 → fall back to pytesseract OCR
4. Pass extracted text to NLP pipeline

---

## 7. NLP Pipeline

### spaCy Custom EntityRuler Patterns
African honorifics and titles added as patterns:
`Hon., Alhaji, Alhaja, Otunba, Chief, Nana, Dr., Prof., Rtd., Engr., Oba, Ooni`

### Extraction Targets
- PERSON entities (spaCy NER)
- ORG entities (ministries, institutions)
- DATE entities associated with appointments
- Job titles via regex patterns:
  - `"appointed as Minister of..."`
  - `"His Excellency ... President of..."`
  - `"Hon. ... Member of Parliament for..."`
  - `"Senator ... representing..."`
  - `"Justice ... of the Supreme Court"`
- Relationship signals: `"wife of", "son of", "business partner of"`

---

## 8. Entity Resolution Algorithm

### Blocking
Group candidates by `country_code + surname_initial` → O(n) per block

### Scoring (composite)
| Component | Weight | Method |
|---|---|---|
| Name similarity | 0.5 | rapidfuzz.token_sort_ratio |
| DOB match | 0.3 | exact=1.0, year-only=0.5, missing=0.0 |
| Position/institution | 0.2 | exact=1.0, fuzzy=0.5 |

### Decision Thresholds
- Score ≥ 0.85 → auto-merge (same person)
- Score 0.70–0.84 → `POTENTIAL_DUPLICATE` flag
- Score < 0.70 → separate entities

### Merge Rules
- Union of `name_variants` lists
- Most-complete attribute set wins
- ALL `SourceRecord` nodes preserved — raw data never deleted

---

## 9. PEP Tier Classification (FATF Recommendation 12)

### Tier 1 — Heads of State / Government Level
President, Vice President, Prime Minister, Deputy PM, Speaker of Parliament,
Senate President, Chief Justice, Supreme Court Justices, Central Bank Governor,
Deputy Governor, all Cabinet Ministers, Military Chiefs of Staff, Inspector General of Police

### Tier 2 — Senior Officials
Members of Parliament / Senators, High Court Judges, Ambassadors / High Commissioners,
Director-Generals of key agencies, Board Chairs/CEOs of major SOEs
(COCOBOD, NNPCL, etc.), Regional/State Governors, Deputy Governors

### Tier 3 — Other PEPs
Local government chairs/mayors, lower court judges, mid-level government appointees

Classification is rule-based: title/institution strings matched against
per-country lookup tables.

---

## 10. API Design (Open — No Auth)

| Method | Endpoint | Description |
|---|---|---|
| POST | /api/v1/screen | Fuzzy name screening |
| GET | /api/v1/pep/{id} | Full PEP profile |
| GET | /api/v1/pep/{id}/graph | Relationship graph (Neo4j) |
| GET | /api/v1/search | Full-text search with filters |
| GET | /api/v1/stats | Database statistics |
| GET | /api/v1/health | DB connectivity check |

All endpoints: request validation (Pydantic), screening queries logged to
`screening_log`, proper HTTP status codes, OpenAPI docs auto-generated.

**Screening algorithm:** pg_trgm similarity on `full_name` + `name_variants`
for candidate retrieval → rapidfuzz re-ranking → return sorted by score.

---

## 11. Scheduler Jobs

| Job | Schedule | Description |
|---|---|---|
| run_all_scrapers | Sunday 02:00 UTC | All 10 scrapers |
| run_gazette_scrapers | Wednesday 06:00 UTC | Ghana + Kenya gazettes |
| sync_neo4j_to_postgres | Sunday 06:00 UTC | Batch sync after scrapers |
| log_database_stats | Daily 00:00 UTC | Stats to scheduler_log |

All jobs: log start/end + record count, catch all exceptions (never crash scheduler).

---

## 12. Key Design Decisions

| Decision | Choice |
|---|---|
| API auth | None (open) |
| Scrapers | Live + fixture fallback |
| Seed data | `python -m database.seed` (~50 real records) |
| Scraper concurrency | Sequential with asyncio.sleep(2) |
| Sync mechanism | Batch job (Neo4j → PostgreSQL) |
| OCR trigger threshold | < 100 chars/page |
| Change detection | End-date old positions, never overwrite |
| Logging | structlog JSON to stdout |

---

## 13. Implementation Order

1. Docker Compose + environment config
2. PostgreSQL schema + Neo4j constraints
3. Database init script (`python -m database.init`)
4. BaseScraper + Ghana Parliament spider (fully working, with fixture)
5. NLP pipeline (extractor, normaliser, classifier)
6. Entity resolver
7. Neo4j → PostgreSQL sync
8. All remaining 9 scrapers + fixtures
9. Seed script (`python -m database.seed`)
10. FastAPI (all 6 endpoints)
11. APScheduler jobs
12. Test suite (entity resolution, classifier, screening API, PDF parser)
13. README

---

## 14. Files Beyond the Spec

- `database/init.py` — init script
- `database/seed.py` — seed script
- `tests/fixtures/` — HTML and PDF fixture files per spider
- `docs/plans/` — this design doc
