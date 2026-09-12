from app.crawler import WebsiteCrawler


def create_crawler():
    """
    Create a crawler instance without launching a real browser.

    The tests below only exercise static/helper methods, so a
    browser instance is not required.
    """
    return WebsiteCrawler.__new__(WebsiteCrawler)


def test_same_domain_accepts_same_domain():

    assert WebsiteCrawler._same_domain(
        "https://example.com",
        "https://example.com/about",
    )


def test_same_domain_accepts_subdomain():

    assert WebsiteCrawler._same_domain(
        "https://example.com",
        "https://www.example.com/about",
    )


def test_same_domain_rejects_external_domain():

    assert not WebsiteCrawler._same_domain(
        "https://example.com",
        "https://google.com/about",
    )


def test_rank_links_prioritises_relevant_pages():

    crawler = create_crawler()

    links = [
        "https://example.com/blog",
        "https://example.com/about",
        "https://example.com/random",
        "https://example.com/contact",
    ]

    ranked = crawler._rank_links(links)

    assert ranked.index(
        "https://example.com/about"
    ) < ranked.index(
        "https://example.com/blog"
    )

    assert ranked.index(
        "https://example.com/contact"
    ) < ranked.index(
        "https://example.com/blog"
    )


def test_rank_links_keeps_all_links():

    crawler = create_crawler()

    links = [
        "https://example.com/blog",
        "https://example.com/about",
        "https://example.com/contact",
    ]

    ranked = crawler._rank_links(links)

    assert len(ranked) == len(links)

    assert set(ranked) == set(links)


def test_rank_links_preserves_duplicate_links():

    crawler = create_crawler()

    links = [
        "https://example.com/about",
        "https://example.com/about",
        "https://example.com/contact",
    ]

    ranked = crawler._rank_links(links)

    assert len(ranked) == 3

    assert ranked.count(
        "https://example.com/about"
    ) == 2

    assert ranked.count(
        "https://example.com/contact"
    ) == 1


def test_score_url_returns_higher_score_for_priority_page():

    crawler = create_crawler()

    priority_score = crawler._score_url(
        "https://example.com/about"
    )

    normal_score = crawler._score_url(
        "https://example.com/blog"
    )

    assert priority_score > normal_score
