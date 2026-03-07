# Contributing to AfricaPEP

Thank you for your interest in contributing to AfricaPEP! This project aims to provide free, comprehensive PEP screening coverage for all African countries.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/AfricaPEP.git`
3. Create a branch: `git checkout -b feature/your-feature-name`
4. Set up your development environment (see below)

### Development Setup

```bash
# Install dependencies
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# Configure
cp .env.example .env
# Edit .env with your local database credentials

# Or use Docker (recommended)
docker compose up -d
docker compose exec api python -m africapep.database.init
docker compose exec api python -m africapep.database.seed
```

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=africapep --cov-report=html
```

All tests must pass before submitting a PR.

## How to Contribute

### Adding a New Country Scraper

This is the most impactful way to contribute. Many countries currently only have presidency scrapers — adding parliament, judiciary, or gazette scrapers dramatically improves coverage.

1. Create `africapep/scraper/spiders/{country}_{source}.py`
2. Inherit from `BaseScraper` (or `BaseGovGazetteScraper` for gazette PDFs)
3. Implement `scrape()` and `_load_fixture()` methods
4. Add to `ALL_SCRAPERS` in `africapep/scraper/spiders/__init__.py`
5. Add fixture test in `tests/test_scrapers.py`
6. Update PEP tier classifier with country-specific titles if needed

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

### Improving Existing Scrapers

- Fix broken selectors when government websites change
- Add more data extraction (dates, relationships, party affiliation)
- Improve fixture data with more realistic test records

### NLP Pipeline Improvements

- Better name normalisation for different naming conventions
- Improved entity resolution scoring
- Date format parsing for various African date conventions

### Bug Reports

Open an issue with:
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python version, Docker version)

### Feature Requests

Open an issue describing:
- The problem you're trying to solve
- Your proposed solution
- Any alternatives you've considered

## Code Style

- Python 3.11+ with type hints
- Follow existing code patterns and conventions
- Keep functions focused and well-named
- Add tests for new functionality

## Pull Request Process

1. Update tests if you've changed functionality
2. Ensure all tests pass: `pytest tests/ -v`
3. Update documentation if needed
4. Write a clear PR description explaining what and why
5. Reference any related issues

## Scraping Ethics

When writing scrapers, please follow these principles:

- **Respect robots.txt** — Check and obey robots.txt directives
- **Rate limiting** — Minimum 2 seconds between requests
- **User-Agent** — Identify as AfricaPEP in the User-Agent string
- **Public data only** — Only scrape publicly available government data
- **No authentication bypass** — Never circumvent login walls or CAPTCHAs

## Code of Conduct

- Be respectful and constructive
- Welcome newcomers and help them get started
- Focus on the technical merits of contributions
- Maintain a harassment-free environment for everyone

## Questions?

Open a [GitHub Discussion](../../discussions) or an issue if you need help getting started.
