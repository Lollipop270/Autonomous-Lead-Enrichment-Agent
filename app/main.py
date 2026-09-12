import argparse
import asyncio
import json
from pathlib import Path

from .config import GEMINI_MODEL
from .cost_tracker import (
    estimate_cost,
    estimate_tokens,
)
from .crawler import WebsiteCrawler
from .extractor import extract_emails
from .llm import extract_company_intelligence
from .schemas import CompanyResult


def calculate_confidence(
    intelligence,
    pages_scraped: int,
    extracted_emails: list[str],
) -> float:
    """
    Calculate a simple confidence score based on the
    completeness of the extracted company intelligence.
    """

    score = 0.0

    if intelligence.company_overview:
        score += 0.20

    if intelligence.target_audience:
        score += 0.20

    if extracted_emails:
        score += 0.15

    if intelligence.leadership:
        score += 0.20

    if any(
        member.linkedin_url
        for member in intelligence.leadership
    ):
        score += 0.10

    if pages_scraped >= 3:
        score += 0.15
    elif pages_scraped >= 2:
        score += 0.10
    elif pages_scraped >= 1:
        score += 0.05

    return round(
        min(score, 1.0),
        2,
    )


async def process_domain(
    crawler: WebsiteCrawler,
    domain: str,
) -> CompanyResult:
    """
    Crawl and enrich a single company domain.

    A failure for one domain is isolated and returned as
    an error rather than terminating the entire run.
    """

    print(f"\n[+] Processing {domain}")

    crawl_result = await crawler.crawl(domain)

    print(
        f"[+] Pages scraped: "
        f"{len(crawl_result.pages)}"
    )

    # If no usable pages were retrieved, return a failed
    # result for this domain instead of crashing.
    if not crawl_result.pages:
        return CompanyResult(
            domain=domain,
            confidence_score=0.0,
            errors=(
                crawl_result.errors
                or ["No pages could be scraped."]
            ),
        )

    # --------------------------------------------------
    # Combine cleaned website content
    # --------------------------------------------------

    combined_text_parts = []

    for page in crawl_result.pages:
        combined_text_parts.append(
            f"""
URL: {page.url}

CONTENT:
{page.text}
"""
        )

    combined_text = "\n".join(
        combined_text_parts
    )

    # --------------------------------------------------
    # Deterministic email extraction
    # --------------------------------------------------

    emails = extract_emails(
        combined_text
    )

    try:
        # --------------------------------------------------
        # LLM structured extraction
        # --------------------------------------------------

        intelligence = extract_company_intelligence(
            domain,
            combined_text,
        )

        # --------------------------------------------------
        # Merge and normalize emails
        # --------------------------------------------------

        merged_emails = sorted(
            {
                email.strip().lower()
                for email in (
                    emails
                    + intelligence.contact_points
                )
                if email and email.strip()
            }
        )

        # --------------------------------------------------
        # Confidence scoring
        # --------------------------------------------------

        confidence = calculate_confidence(
            intelligence,
            len(crawl_result.pages),
            merged_emails,
        )

        # --------------------------------------------------
        # Token/cost estimation
        # --------------------------------------------------

        input_tokens = estimate_tokens(
            combined_text
        )

        output_text = (
            intelligence.model_dump_json()
        )

        output_tokens = estimate_tokens(
            output_text
        )

        cost = estimate_cost(
            input_tokens,
            output_tokens,
            GEMINI_MODEL,
        )

        # --------------------------------------------------
        # Build final result
        # --------------------------------------------------

        return CompanyResult(
            domain=domain,
            company_overview=(
                intelligence.company_overview
            ),
            target_audience=(
                intelligence.target_audience
            ),
            contact_points=merged_emails,
            leadership=intelligence.leadership,
            confidence_score=confidence,
            pages_scraped=[
                page.url
                for page in crawl_result.pages
            ],
            errors=crawl_result.errors,
            estimated_input_tokens=input_tokens,
            estimated_output_tokens=output_tokens,
            estimated_cost_usd=cost,
        )

    except Exception as exc:
        """
        Keep the pipeline alive if Gemini or another
        extraction step fails for this domain.
        """

        return CompanyResult(
            domain=domain,
            confidence_score=0.0,
            pages_scraped=[
                page.url
                for page in crawl_result.pages
            ],
            errors=[
                *crawl_result.errors,
                f"LLM extraction failed: {exc}",
            ],
        )


async def run(domains: list[str]):
    """
    Process all supplied domains sequentially and write
    the final results to output/output.json.
    """

    from .crawler import create_browser

    playwright, browser = await create_browser()

    try:
        crawler = WebsiteCrawler(
            browser=browser
        )

        results = []

        for domain in domains:
            result = await process_domain(
                crawler,
                domain,
            )

            results.append(result)

            print(
                f"[+] Confidence: "
                f"{result.confidence_score}"
            )

            if result.errors:
                print(
                    f"[!] Errors: "
                    f"{result.errors}"
                )

        # --------------------------------------------------
        # Write JSON output
        # --------------------------------------------------

        output_dir = Path("output")

        output_dir.mkdir(
            exist_ok=True
        )

        output_file = (
            output_dir / "output.json"
        )

        output_file.write_text(
            json.dumps(
                [
                    result.model_dump()
                    for result in results
                ],
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        print(
            f"\n[✓] Results written to "
            f"{output_file}"
        )

    finally:
        await browser.close()
        await playwright.stop()


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Autonomous AI Lead Enrichment Agent"
        )
    )

    parser.add_argument(
        "domains",
        nargs="+",
        help=(
            "Company domains, e.g. "
            "postman.com supabase.com"
        ),
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    asyncio.run(
        run(args.domains)
    )
