import re

from bs4 import BeautifulSoup


REMOVE_TAGS = [
    "script",
    "style",
    "svg",
    "noscript",
    "iframe",
    "canvas",
    "template",
    "nav",
    "footer",
]


def html_to_clean_text(html: str) -> str:
    """
    Convert raw HTML into compact, readable text.

    Removes:
    - scripts
    - CSS
    - SVGs
    - navigation/footer boilerplate
    - excessive whitespace
    """

    soup = BeautifulSoup(html, "lxml")

    for tag_name in REMOVE_TAGS:
        for tag in soup.find_all(tag_name):
            tag.decompose()

    text = soup.get_text(
        separator=" ",
        strip=True
    )

    text = re.sub(r"\s+", " ", text)

    return text.strip()


def extract_emails(text: str) -> list[str]:
    """
    Extract public email addresses from page text.
    """

    pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"

    emails = re.findall(pattern, text)

    return sorted(set(
        email.lower()
        for email in emails
    ))
