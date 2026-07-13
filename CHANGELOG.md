# Changelog

All notable changes to AfricaPEP will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-07-13

### Added
- Phonetic name matching (Double Metaphone via jellyfish) alongside orthographic scoring, with a QID-grounded evaluation harness (#26)
- Offline Splink probabilistic dedup pass with AML-safe merge policy: auto-merge only at >=0.99 probability with corroboration, review queue below (#27)
- Expanded Wikidata catchment for low-coverage countries via three isolated SPARQL branches (country, jurisdiction, citizenship) (#23)
- Comprehensive public API guide at docs/API.md, covering auth, validation rules, rate limits, and error formats (#30, contributed by @Atharv-AC)
- Bundled offline sample dataset (510 real records, Seychelles + Gambia) and `make seed-sample` for a populated local API in under a minute (#35)
- ROADMAP.md, CONTRIBUTING-DATA.md (non-code contribution guide), and a country data validation issue template (#33)
- requirements-dev.txt for development tooling (#34)

### Fixed
- Cross-run Person node duplication: node ids now derive deterministically from Wikidata QIDs (#24)
- Per-run Position/Organisation node duplication: content-derived ids (#32)
- Splink false-merging non-Latin names that produced empty metaphone keys (#28)
- Scraper SPARQL timeout too low for the citizenship catchment branch (#25)
- CI red on every push due to two lint errors; entity resolution tests (20) were silently excluded from the default pytest run and now run in CI (#31)

### Changed
- Public claims reconciled with reality: 34,000+ profiles and 170+ tests stated consistently across README, badges, and the OpenAPI description (#33)
- README states plainly that Wikidata is the sole current data source via one parameterized scraper; national sources are framed as contribution opportunities (#33)
- Removed dead scaffolding never wired into the pipeline (Playwright utils, proxy rotator, PDF parser, spaCy NER extractor and relationship builder, unused ORM models) and pruned seven unused dependencies; Docker image loses two spaCy models and tesseract, CI runs ~40% faster (#34)

### Security
- requests bumped to 2.32.3 (CVE-2024-35195) (#33)
- Production docker-compose now fails loudly when database passwords are unset instead of defaulting to `changeme` (#33)
- API key comparison uses constant-time `secrets.compare_digest` (#33)
- Per-worker in-memory rate limit behaviour documented as a known caveat (#33, tracked for Redis in #38)

## [1.0.0] - 2026-03-08

### Added
- Wikidata SPARQL scraper covering all 54 African Union member states
- NLP pipeline: name normalisation, FATF tier classification, entity resolution
- Neo4j graph database as source of truth with full relationship modelling
- PostgreSQL search index with pg_trgm fuzzy matching and tsvector full-text search
- FastAPI with industry-standard screening response format
  - `POST /api/v1/screen` — single name screening with fuzzy matching
  - `POST /api/v1/screen/batch` — batch screening (up to 50 names)
  - `GET /api/v1/search` — full-text search with country/tier/active filters
  - `GET /api/v1/stats` — database statistics
  - `GET /api/v1/countries` — country coverage information
  - `GET /health` — health check
- Match explanation in screening responses (scoring breakdown)
- FATF Recommendation 12 compliant tier classification (Tier 1/2/3)
- Full audit trail — every screening logged to `screening_log` table
- Docker Compose setup for all services
- Next.js frontend with screening UI, batch screening, and statistics dashboard
- 79 unit and integration tests
- CI pipeline with GitHub Actions
- 32,000+ verified PEP profiles from Wikidata
