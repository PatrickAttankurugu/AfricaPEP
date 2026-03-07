"""Polite scraping utilities: rate limiting, user agent rotation, robots.txt respect."""
import random
import time
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser
from functools import lru_cache

import structlog

log = structlog.get_logger()

USER_AGENTS = [
    "AfricaPEP-Bot/1.0 (KYC research; contact@africapep.dev) Python/3.11",
    "AfricaPEP-Scraper/1.0 (AML compliance research) +https://africapep.dev",
    "AfricaPEP-Crawler/1.0 (academic PEP research; contact@africapep.dev)",
]


def get_random_user_agent() -> str:
    return random.choice(USER_AGENTS)


class RateLimiter:
    """Simple per-domain rate limiter."""

    def __init__(self, min_delay: float = 2.0, max_delay: float = 5.0):
        self.min_delay = min_delay
        self.max_delay = max_delay
        self._last_request: dict[str, float] = {}

    def wait(self, url: str):
        domain = urlparse(url).netloc
        now = time.time()
        last = self._last_request.get(domain, 0)
        delay = random.uniform(self.min_delay, self.max_delay)
        elapsed = now - last

        if elapsed < delay:
            sleep_time = delay - elapsed
            log.debug("rate_limit_wait", domain=domain, sleep=round(sleep_time, 1))
            time.sleep(sleep_time)

        self._last_request[domain] = time.time()


@lru_cache(maxsize=50)
def check_robots_txt(base_url: str, path: str = "/") -> bool:
    """Check if a URL path is allowed by robots.txt."""
    try:
        parsed = urlparse(base_url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        rp = RobotFileParser()
        rp.set_url(robots_url)
        rp.read()
        allowed = rp.can_fetch(USER_AGENTS[0], path)
        log.debug("robots_check", url=base_url, path=path, allowed=allowed)
        return allowed
    except Exception as e:
        log.warning("robots_txt_failed", url=base_url, error=str(e))
        return True  # assume allowed if robots.txt is unreachable


rate_limiter = RateLimiter()
