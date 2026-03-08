# Contributing to AfricaPEP

Thank you for your interest in contributing to AfricaPEP — the open-source African PEP database for KYC/AML compliance.

## Quick Links

- **Live demo:** [pep.patrickaiafrica.com](https://pep.patrickaiafrica.com)
- **API docs:** [api-pep.patrickaiafrica.com/docs](https://api-pep.patrickaiafrica.com/docs)
- **Issues:** [GitHub Issues](https://github.com/PatrickAttankurugu/AfricaPEP/issues)
- **Discussions:** [GitHub Discussions](https://github.com/PatrickAttankurugu/AfricaPEP/discussions)

## Getting Started

### 1. Fork and clone

1. Click the **Fork** button at [github.com/PatrickAttankurugu/AfricaPEP](https://github.com/PatrickAttankurugu/AfricaPEP)
2. Clone your fork:

```bash
git clone https://github.com/<your-github-username>/AfricaPEP.git
cd AfricaPEP
git remote add upstream https://github.com/PatrickAttankurugu/AfricaPEP.git
```

### 2. Set up your environment

**Option A: Docker (recommended)**

```bash
cp .env.example .env
docker compose up -d
docker compose exec api python -m africapep.database.init
docker compose exec api python -m africapep.database.seed
```

**Option B: Local**

```bash
# Requires Python 3.11+, Neo4j 5, PostgreSQL 15
pip install -r requirements.txt
python -m spacy download en_core_web_sm

cp .env.example .env
# Edit .env with your database credentials

python -m africapep.database.init
python -m africapep.database.seed
```

### 3. Run tests

```bash
# All unit tests (no database needed)
pytest tests/ -v -m "not integration"

# All tests including integration
pytest tests/ -v

# With coverage
pytest tests/ --cov=africapep --cov-report=html
```

All tests must pass before submitting a PR.

### 4. Create a branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bugfix-name
```

## How to Contribute

### Good First Issues

Look for issues labeled [`good first issue`](https://github.com/PatrickAttankurugu/AfricaPEP/labels/good%20first%20issue). These are small, well-defined tasks ideal for newcomers.

### Data & Scraping

AfricaPEP pulls data from [Wikidata's SPARQL endpoint](https://query.wikidata.org/). The single `WikidataScraper` covers all 54 African countries.

Ways to improve data quality:

- **Expand the SPARQL query** — Add fields like date of birth, party affiliation, or education
- **Add supplementary data sources** — Government gazettes, electoral commissions, judiciary websites (create a new scraper inheriting from `BaseScraper`)
- **Improve entity resolution** — Better deduplication scoring, handling of transliterated names
- **Add regional bodies** — AU Commission, ECOWAS, SADC, EAC officials

Example: adding a new data source scraper:

```python
from africapep.scraper.base_scraper import BaseScraper, RawPersonRecord

class GovernmentGazetteScraper(BaseScraper):
    source_type = "GAZETTE"

    def __init__(self, country_code: str):
        super().__init__()
        self.country_code = country_code

    def scrape(self) -> list[RawPersonRecord]:
        # Your scraping logic here
        ...
```

### NLP Pipeline

- Better name normalisation for African naming conventions (patronymics, clan names, Arabic transliterations)
- Improved FATF tier classification — add country-specific political titles
- Date format parsing for various conventions used across Africa

### API & Backend

- Add new endpoints (e.g., relationship graph queries, PEP timeline)
- Improve fuzzy matching algorithm
- Add API authentication / rate limiting
- Performance optimisation for large result sets

### Frontend (Next.js)

- Improve the screening UI/UX
- Add data visualisations (PEP distribution maps, network graphs)
- Accessibility improvements
- Internationalisation (French, Arabic, Portuguese, Swahili)

### Documentation

- Improve API documentation with more examples
- Write tutorials for common use cases
- Translate docs into other languages

### Testing

- Add tests for uncovered modules
- Add end-to-end tests
- Add performance/load tests

## Architecture Overview

```
Wikidata SPARQL  -->  WikidataScraper  -->  NLP Pipeline  -->  Entity Resolver
                                            (normalise)        (deduplicate)
                                            (classify)
                                                                    |
                                                          +---------+---------+
                                                          v                   v
                                                       Neo4j             PostgreSQL
                                                   (graph/truth)       (search index)
                                                          |                   |
                                                          +--------+----------+
                                                                   v
                                                               FastAPI
                                                                   v
                                                            Next.js Frontend
```

**Key principle:** Neo4j is the source of truth. PostgreSQL is a search index synced from Neo4j.

## Code Style

- **Python 3.11+** with type hints
- Follow existing patterns in the codebase
- Keep functions focused and well-named
- Use `structlog` for logging (not `print`)
- Add tests for any new functionality

## Pull Request Process

1. Create a feature branch from `main`
2. Make your changes with clear, atomic commits
3. Add/update tests as needed
4. Ensure all tests pass: `pytest tests/ -v`
5. Update documentation if your change affects the public API
6. Open a PR with a clear title and description
7. Reference any related issues (e.g., "Closes #42")

### PR Title Convention

```
feat: add date of birth extraction from Wikidata
fix: handle timeout in SPARQL queries
docs: add batch screening API example
test: add entity resolver edge cases
refactor: simplify fuzzy matching pipeline
```

## Scraping Ethics

When writing scrapers:

- **Respect robots.txt** — check and obey directives
- **Rate limit** — minimum 2 seconds between requests
- **User-Agent** — identify as AfricaPEP
- **Public data only** — only scrape publicly available data
- **No auth bypass** — never circumvent login walls or CAPTCHAs

## Code of Conduct

We are committed to providing a welcoming and inclusive environment. All participants are expected to:

- Be respectful and constructive in all interactions
- Welcome newcomers and help them get started
- Focus on technical merits of contributions
- Accept constructive criticism gracefully
- Maintain a harassment-free environment for everyone

See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) for details.

## Questions?

- Open a [GitHub Discussion](https://github.com/PatrickAttankurugu/AfricaPEP/discussions) for questions
- Open an [Issue](https://github.com/PatrickAttankurugu/AfricaPEP/issues) for bugs or feature requests
- Email: patricka.azuma@gmail.com
- LinkedIn: [Patrick Attankurugu](https://www.linkedin.com/in/patrick-ai-africa/)
- X/Twitter: [@patrickaiafrica](https://x.com/patrickaiafrica)
