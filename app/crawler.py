from dataclasses import dataclass
from urllib.parse import urlparse

from playwright.async_api import (
    Browser,
    Page,
    async_playwright,
)

from .config import (
    MAX_CONTENT_CHARS,
    MAX_PAGES_PER_DOMAIN,
    PAGE_TIMEOUT_MS,
)
from .extractor import html_to_clean_text
from .resilience import retry_async


# Pages that are particularly useful for company
# intelligence and lead enrichment.
PRIORITY_PATH_KEYWORDS = {
    "/about": 10,
    "/about-us": 10,
    "/company": 10,
    "/team": 10,
    "/leadership": 10,
    "/contact": 9,
    "/contact-us": 9,
    "/pricing": 8,
    "/product": 7,
    "/products": 7,
    "/solutions": 7,
    "/customers": 6,
    "/security": 5,
    "/careers": 4,
}


# Pages that generally don't contain useful company
# intelligence for this assignment.
EXCLUDED_PATH_KEYWORDS = {
    "/login",
    "/signin",
    "/sign-in",
    "/register",
    "/signup",
    "/sign-up",
    "/dashboard",
    "/auth",
    "/oauth",
    "/checkout",
    "/cart",
}


@dataclass
class CrawledPage:
    url: str
    text: str


@dataclass
class CrawlResult:
    pages: list[CrawledPage]
    errors: list[str]


class WebsiteCrawler:

    def __init__(
        self,
        browser: Browser,
        max_pages: int = MAX_PAGES_PER_DOMAIN,
    ):
        self.browser = browser
        self.max_pages = max_pages

    @staticmethod
    def _canonicalize_url(url: str) -> str:
        """
        Normalize URLs so equivalent URLs are not crawled
        multiple times.

        Examples:

            https://postman.com/
            https://postman.com

        become:

            https://postman.com

        www/non-www is normalized as well.
        """

        parsed = urlparse(url)

        scheme = parsed.scheme.lower()

        hostname = parsed.netloc.lower()

        # Treat www.example.com and example.com as the
        # same website for crawling purposes.
        if hostname.startswith("www."):
            hostname = hostname[4:]

        path = parsed.path.rstrip("/")

        # Keep query strings only when they are meaningful.
        # For this assignment, most tracking parameters
        # are unnecessary.
        return (
            f"{scheme}://{hostname}{path}"
            if path
            else f"{scheme}://{hostname}"
        )

    @staticmethod
    def _same_domain(
        base_url: str,
        candidate_url: str,
    ) -> bool:

        base_host = urlparse(
            base_url
        ).netloc.lower()

        candidate_host = urlparse(
            candidate_url
        ).netloc.lower()

        if base_host.startswith("www."):
            base_host = base_host[4:]

        if candidate_host.startswith("www."):
            candidate_host = candidate_host[4:]

        return (
            candidate_host == base_host
            or candidate_host.endswith(
                "." + base_host
            )
        )

    @staticmethod
    def _is_excluded_url(url: str) -> bool:
        """
        Determine whether a URL is unlikely to provide
        useful company intelligence.
        """

        path = urlparse(
            url
        ).path.lower().rstrip("/")

        for excluded in EXCLUDED_PATH_KEYWORDS:

            if (
                path == excluded
                or path.startswith(excluded + "/")
            ):
                return True

        return False

    @staticmethod
    def _score_url(url: str) -> int:
        """
        Give relevant pages a higher crawl priority.
        """

        path = urlparse(
            url
        ).path.lower().rstrip("/")

        score = 0

        for keyword, points in PRIORITY_PATH_KEYWORDS.items():

            if (
                path == keyword
                or path.startswith(keyword + "/")
            ):
                score = max(score, points)

        # Slight preference for shallow URLs because
        # they are more likely to be company-level pages.
        depth = len(
            [
                part
                for part in path.split("/")
                if part
            ]
        )

        if depth == 1:
            score += 2

        elif depth == 2:
            score += 1

        return score

    async def _fetch_page_once(
        self,
        page: Page,
        url: str,
    ) -> CrawledPage | None:
        """
        Fetch a single page once.

        Exceptions are allowed to propagate so that the
        retry mechanism can handle transient failures.
        """

        response = await page.goto(
            url,
            wait_until="domcontentloaded",
            timeout=PAGE_TIMEOUT_MS,
        )

        # Allow JavaScript-rendered content to settle.
        await page.wait_for_timeout(2000)

        if response is not None and response.status >= 400:
            raise RuntimeError(
                f"HTTP {response.status}"
            )

        html = await page.content()

        text = html_to_clean_text(html)

        if not text:
            raise ValueError(
                "Page contained no extractable text."
            )

        return CrawledPage(
            url=url,
            text=text[:MAX_CONTENT_CHARS],
        )

    async def _fetch_page(
        self,
        page: Page,
        url: str,
    ) -> CrawledPage | None:
        """
        Fetch a page with retry and graceful failure.
        """

        try:

            return await retry_async(
                lambda: self._fetch_page_once(
                    page,
                    url,
                ),
                max_attempts=3,
                base_delay=1.0,
                operation_name=f"Fetching {url}",
            )

        except Exception as exc:

            print(
                f"[!] Failed to fetch {url}: {exc}"
            )

            return None

    async def _discover_links(
        self,
        page: Page,
        base_url: str,
    ) -> list[str]:
        """
        Discover relevant same-domain links from the
        current page.
        """

        links = await page.locator(
            "a[href]"
        ).evaluate_all(
            """
            elements => elements.map(
                e => e.href
            )
            """
        )

        valid = []
        seen = set()

        for link in links:

            if not link:
                continue

            if link.startswith(
                (
                    "mailto:",
                    "tel:",
                    "javascript:",
                )
            ):
                continue

            canonical_url = self._canonicalize_url(
                link
            )

            if not self._same_domain(
                base_url,
                canonical_url,
            ):
                continue

            if self._is_excluded_url(
                canonical_url
            ):
                continue

            if canonical_url in seen:
                continue

            seen.add(canonical_url)
            valid.append(canonical_url)

        return valid

    def _rank_links(
        self,
        links: list[str],
    ) -> list[str]:
        """
        Rank discovered pages by relevance to the
        company intelligence task.
        """

        return sorted(
            links,
            key=lambda url: self._score_url(url),
            reverse=True,
        )

    async def crawl(
        self,
        domain: str,
    ) -> CrawlResult:

        base_url = (
            domain
            if domain.startswith("http")
            else f"https://{domain}"
        )

        base_url = self._canonicalize_url(
            base_url
        )

        pages: list[CrawledPage] = []
        errors: list[str] = []

        context = await self.browser.new_context(
            user_agent=(
                "Mozilla/5.0 "
                "(Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/131 Safari/537.36"
            )
        )

        page = await context.new_page()

        try:

            # -----------------------------------------
            # 1. Fetch homepage
            # -----------------------------------------

            homepage = await self._fetch_page(
                page,
                base_url,
            )

            if homepage:

                pages.append(homepage)

            else:

                errors.append(
                    f"Homepage could not be retrieved: "
                    f"{base_url}"
                )

            # -----------------------------------------
            # 2. Discover internal links
            # -----------------------------------------

            discovered = []

            if homepage:

                try:

                    discovered = (
                        await self._discover_links(
                            page,
                            base_url,
                        )
                    )

                except Exception as exc:

                    errors.append(
                        f"Link discovery failed: {exc}"
                    )

            # -----------------------------------------
            # 3. Rank links by relevance
            # -----------------------------------------

            discovered = self._rank_links(
                discovered
            )

            # -----------------------------------------
            # 4. Crawl relevant pages
            # -----------------------------------------

            visited = {
                self._canonicalize_url(
                    p.url
                )
                for p in pages
            }

            for url in discovered:

                if len(pages) >= self.max_pages:
                    break

                canonical_url = (
                    self._canonicalize_url(url)
                )

                if canonical_url in visited:
                    continue

                visited.add(canonical_url)

                result = await self._fetch_page(
                    page,
                    canonical_url,
                )

                if result:

                    pages.append(result)

                else:

                    errors.append(
                        f"Page could not be retrieved: "
                        f"{canonical_url}"
                    )

        except Exception as exc:

            errors.append(
                f"Crawler failure for {domain}: {exc}"
            )

        finally:

            await context.close()

        return CrawlResult(
            pages=pages,
            errors=errors,
        )


async def create_browser():

    playwright = await async_playwright().start()

    browser = await playwright.chromium.launch(
        headless=True
    )

    return playwright, browser
