# Changelog

All notable changes to AfricaPEP will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
