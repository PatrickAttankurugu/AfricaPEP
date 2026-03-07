from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
import time
import random

import structlog
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from africapep.config import settings

log = structlog.get_logger()

USER_AGENTS = [
    "AfricaPEP-Bot/1.0 (KYC research; contact@africapep.dev) Python/3.11",
    "AfricaPEP-Scraper/1.0 (AML compliance research) +https://africapep.dev",
    "AfricaPEP-Crawler/1.0 (academic PEP research; contact@africapep.dev)",
]


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
    extra_fields: dict = field(default_factory=dict)


class BaseScraper(ABC):
    """Abstract base class all scrapers inherit from.

    Provides: polite rate limiting, retry logic, structured logging,
    and a fixture mode for testing without hitting live servers.
    """

    country_code: str = ""
    source_type: str = ""
    delay_seconds: float = settings.scraper_delay_seconds

    def __init__(self, use_fixture: bool = False):
        self.use_fixture = use_fixture
        self.session = requests.Session()
        self.session.headers["User-Agent"] = random.choice(USER_AGENTS)

    @abstractmethod
    def scrape(self) -> list[RawPersonRecord]:
        ...

    @abstractmethod
    def _load_fixture(self) -> list[RawPersonRecord]:
        ...

    def run(self) -> list[RawPersonRecord]:
        scraper_name = self.__class__.__name__
        if self.use_fixture:
            log.info("scraper_fixture_mode", scraper=scraper_name)
            return self._load_fixture()
        try:
            log.info("scraper_started", scraper=scraper_name)
            records = self.scrape()
            log.info("scraper_finished", scraper=scraper_name, records=len(records))
            return records
        except Exception as e:
            log.error("scraper_failed", scraper=scraper_name, error=str(e))
            return []

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
    def _get(self, url: str) -> requests.Response:
        """GET with polite delay + retry (3x with exponential backoff)."""
        delay = self.delay_seconds + random.uniform(0, 1)
        time.sleep(delay)
        log.info("scraper_request", url=url, delay=round(delay, 1))
        resp = self.session.get(url, timeout=30)
        log.info("scraper_response", url=url, status=resp.status_code)
        resp.raise_for_status()
        return resp

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
    def _post(self, url: str, data=None, json=None) -> requests.Response:
        """POST with polite delay + retry."""
        delay = self.delay_seconds + random.uniform(0, 1)
        time.sleep(delay)
        log.info("scraper_post_request", url=url)
        resp = self.session.post(url, data=data, json=json, timeout=30)
        resp.raise_for_status()
        return resp
