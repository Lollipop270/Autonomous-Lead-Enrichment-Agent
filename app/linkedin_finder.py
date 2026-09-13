import asyncio
import re
from urllib.parse import quote, urlparse

from playwright.async_api import Browser


SEARCH_ENGINE_URL = "https://www.bing.com/search"

SEARCH_TIMEOUT_MS = 20000

MAX_SEARCH_RESULTS = 10


def is_founder_role(role: str) -> bool:
    """
    Return True when the person's role indicates
    that they are a founder or co-founder.
    """

    if not role:
        return False

    normalized = role.lower().strip()

    founder_keywords = (
        "founder",
        "co-founder",
        "cofounder",
    )

    return any(
        keyword in normalized
        for keyword in founder_keywords
    )


def is_linkedin_profile_url(url: str) -> bool:
    """
    Check whether a URL is a LinkedIn personal
    profile URL.

    Accepts:
        https://linkedin.com/in/example
        https://www.linkedin.com/in/example/

    Rejects:
        https://linkedin.com/company/example
        https://linkedin.com/jobs/
    """

    if not url:
        return False

    try:
        parsed = urlparse(url)

        hostname = parsed.netloc.lower()

        if hostname.startswith("www."):
            hostname = hostname[4:]

        path = parsed.path.lower()

        return (
            hostname == "linkedin.com"
            and path.startswith("/in/")
        )

    except Exception:
        return False


def normalize_linkedin_url(url: str) -> str:
    """
    Normalize a LinkedIn profile URL.
    """

    parsed = urlparse(url)

    path = parsed.path.rstrip("/")

    return f"https://www.linkedin.com{path}"


def normalize_text(text: str) -> str:
    """
    Normalize text for comparison.
    """

    return re.sub(
        r"\s+",
        " ",
        text.lower().strip(),
    )


def name_matches(
    person_name: str,
    text: str,
) -> bool:
    """
    Check whether the person's full name appears
    in the search result.
    """

    if not person_name or not text:
        return False

    return normalize_text(
        person_name
    ) in normalize_text(text)


def company_name_from_domain(
    domain: str,
) -> str:
    """
    Convert a company domain into a simple company name.

    postman.com -> postman
    supabase.com -> supabase
    vapi.ai -> vapi
    """

    domain = domain.lower().strip()

    domain = domain.replace(
        "https://",
        "",
    )

    domain = domain.replace(
        "http://",
        "",
    )

    domain = domain.replace(
        "www.",
        "",
    )

    return domain.split(".")[0]


def company_matches(
    company_domain: str,
    text: str,
) -> bool:
    """
    Check whether the company name appears
    in the search result text.
    """

    if not company_domain or not text:
        return False

    company_name = company_name_from_domain(
        company_domain
    )

    return company_name in normalize_text(
        text
    )


def build_search_query(
    person_name: str,
    company_domain: str,
) -> str:
    """
    Build a search query using the person's name,
    company name, and LinkedIn.
    """

    company_name = company_name_from_domain(
        company_domain
    )

    return (
        f'"{person_name}" '
        f'"{company_name}" '
        f'LinkedIn'
    )


async def extract_linkedin_candidates(
    page,
) -> list[dict]:
    """
    Extract LinkedIn profile URLs from the
    current search results page.
    """

    candidates = []

    links = await page.locator(
        "a[href]"
    ).all()

    for link in links:

        try:
            href = await link.get_attribute(
                "href"
            )

            if not href:
                continue

            if not is_linkedin_profile_url(
                href
            ):
                continue

            title = await link.inner_text()

            surrounding_text = ""

            try:
                parent = link.locator(
                    "xpath=.."
                )

                surrounding_text = (
                    await parent.inner_text(
                        timeout=2000
                    )
                )

            except Exception:
                pass

            candidates.append(
                {
                    "url": normalize_linkedin_url(
                        href
                    ),
                    "title": title,
                    "text": surrounding_text,
                }
            )

            if len(candidates) >= MAX_SEARCH_RESULTS:
                break

        except Exception:
            continue

    return candidates


def score_candidate(
    candidate: dict,
    person_name: str,
    company_domain: str,
) -> int:
    """
    Score a search result.

    A higher score indicates a stronger match.
    """

    score = 0

    title = candidate.get(
        "title",
        "",
    )

    text = candidate.get(
        "text",
        "",
    )

    url = candidate.get(
        "url",
        "",
    )

    searchable_text = (
        f"{title} {text}"
    )

    # Correct LinkedIn profile URL.
    if is_linkedin_profile_url(url):
        score += 2

    # Person's name appears.
    if name_matches(
        person_name,
        searchable_text,
    ):
        score += 4

    # Company name appears.
    if company_matches(
        company_domain,
        searchable_text,
    ):
        score += 3

    return score


async def find_linkedin_profile(
    browser: Browser,
    person_name: str,
    role: str,
    company_domain: str,
) -> str | None:
    """
    Search for a founder's LinkedIn profile
    using Playwright and Bing.

    No additional API key is required.
    """

    if not is_founder_role(role):
        return None

    query = build_search_query(
        person_name,
        company_domain,
    )

    search_url = (
        f"{SEARCH_ENGINE_URL}"
        f"?q={quote(query)}"
    )

    print(
        f"[LinkedIn] Searching for "
        f"{person_name}..."
    )

    context = await browser.new_context(
        viewport={
            "width": 1280,
            "height": 900,
        },
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        ),
    )

    page = await context.new_page()

    try:

        await page.goto(
            search_url,
            wait_until="domcontentloaded",
            timeout=SEARCH_TIMEOUT_MS,
        )

        await page.wait_for_timeout(1500)

        body_text = await page.locator(
            "body"
        ).inner_text()

        lower_text = body_text.lower()

        blocked_indicators = [
            "captcha",
            "verify you are human",
            "unusual traffic",
            "robot",
        ]

        if any(
            indicator in lower_text
            for indicator in blocked_indicators
        ):
            print(
                "[!] Search engine blocked "
                "automated search."
            )

            return None

        candidates = (
            await extract_linkedin_candidates(
                page
            )
        )

        if not candidates:
            print(
                f"[-] No LinkedIn candidates "
                f"found for {person_name}"
            )

            return None

        scored_candidates = []

        for candidate in candidates:

            score = score_candidate(
                candidate,
                person_name,
                company_domain,
            )

            scored_candidates.append(
                (
                    score,
                    candidate,
                )
            )

        scored_candidates.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        best_score, best_candidate = (
            scored_candidates[0]
        )

        # Require a reasonably strong match.
        if best_score < 6:

            print(
                f"[-] No sufficiently confident "
                f"LinkedIn match for {person_name}"
            )

            return None

        linkedin_url = (
            best_candidate["url"]
        )

        print(
            f"[+] LinkedIn found: "
            f"{linkedin_url}"
        )

        return linkedin_url

    except Exception as exc:

        print(
            f"[!] LinkedIn search failed for "
            f"{person_name}: {exc}"
        )

        return None

    finally:

        await page.close()
        await context.close()


async def enrich_founder_linkedin(
    browser: Browser,
    leadership,
    company_domain: str,
):
    """
    Find LinkedIn URLs for founders/co-founders.

    Existing LinkedIn URLs are preserved.
    """

    for member in leadership:

        # Don't replace a URL already discovered
        # from the company website.
        if member.linkedin_url:
            continue

        # Only search founders/co-founders.
        if not is_founder_role(
            member.role
        ):
            continue

        linkedin_url = (
            await find_linkedin_profile(
                browser=browser,
                person_name=member.name,
                role=member.role,
                company_domain=company_domain,
            )
        )

        if linkedin_url:
            member.linkedin_url = (
                linkedin_url
            )

        # Avoid sending searches too quickly.
        await asyncio.sleep(1)

    return leadership
