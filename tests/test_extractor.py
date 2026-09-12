from app.extractor import (
    extract_emails,
    html_to_clean_text,
)


def test_extract_emails():
    text = """
    Contact us at hello@example.com or
    support@example.org.
    """

    emails = extract_emails(text)

    assert emails == [
        "hello@example.com",
        "support@example.org",
    ]


def test_extract_emails_removes_duplicates():
    text = """
    Contact hello@example.com.
    Email hello@example.com again.
    """

    emails = extract_emails(text)

    assert emails == [
        "hello@example.com",
    ]


def test_extract_emails_normalizes_case():
    text = """
    Contact SUPPORT@Example.COM.
    """

    emails = extract_emails(text)

    assert emails == [
        "support@example.com",
    ]


def test_html_to_clean_text_removes_unnecessary_elements():
    html = """
    <html>
        <head>
            <style>
                body { color: red; }
            </style>
        </head>

        <body>
            <nav>
                Home About Contact
            </nav>

            <h1>Example Company</h1>

            <p>
                We build software for developers.
            </p>

            <script>
                console.log("should not appear");
            </script>

            <svg>
                <path></path>
            </svg>

            <footer>
                Copyright 2026
            </footer>
        </body>
    </html>
    """

    text = html_to_clean_text(html)

    assert "Example Company" in text
    assert "We build software for developers." in text

    assert "color: red" not in text
    assert "console.log" not in text
    assert "should not appear" not in text
