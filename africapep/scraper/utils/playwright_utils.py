"""Async Playwright browser automation helpers for JS-rendered pages."""
import asyncio
import random
from typing import Optional

import structlog

log = structlog.get_logger()

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
]


async def get_page_content(url: str, wait_selector: Optional[str] = None,
                           timeout: int = 30000) -> str:
    """Launch headless Chromium, navigate to URL, return page HTML."""
    from playwright.async_api import async_playwright

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=random.choice(USER_AGENTS),
            viewport={"width": 1920, "height": 1080},
        )
        page = await context.new_page()

        try:
            log.info("playwright_navigate", url=url)
            await page.goto(url, wait_until="networkidle", timeout=timeout)

            if wait_selector:
                await page.wait_for_selector(wait_selector, timeout=timeout)

            content = await page.content()
            log.info("playwright_done", url=url, length=len(content))
            return content
        except Exception as e:
            log.error("playwright_failed", url=url, error=str(e))
            return ""
        finally:
            await browser.close()


def get_page_content_sync(url: str, wait_selector: Optional[str] = None,
                          timeout: int = 30000) -> str:
    """Synchronous wrapper around async Playwright page fetch."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                return pool.submit(
                    asyncio.run,
                    get_page_content(url, wait_selector, timeout)
                ).result()
        else:
            return loop.run_until_complete(
                get_page_content(url, wait_selector, timeout)
            )
    except RuntimeError:
        return asyncio.run(get_page_content(url, wait_selector, timeout))


async def get_multiple_pages(urls: list[str], wait_selector: Optional[str] = None,
                             delay: float = 2.0) -> dict[str, str]:
    """Fetch multiple pages sequentially with polite delays."""
    from playwright.async_api import async_playwright

    results = {}
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=random.choice(USER_AGENTS),
        )
        page = await context.new_page()

        for url in urls:
            try:
                await asyncio.sleep(delay + random.uniform(0, 1))
                await page.goto(url, wait_until="networkidle", timeout=30000)
                if wait_selector:
                    await page.wait_for_selector(wait_selector, timeout=15000)
                results[url] = await page.content()
            except Exception as e:
                log.error("playwright_page_failed", url=url, error=str(e))
                results[url] = ""

        await browser.close()

    return results
