from app.linkedin_finder import (
    is_founder_role,
    is_linkedin_profile_url,
    normalize_linkedin_url,
    build_search_query,
    company_name_from_domain,
)


def test_founder_role():

    assert is_founder_role(
        "CEO/Co-Founder"
    )


def test_cofounder_role():

    assert is_founder_role(
        "Co-Founder"
    )


def test_founder_role_case_insensitive():

    assert is_founder_role(
        "Founder & CEO"
    )


def test_non_founder_role():

    assert not is_founder_role(
        "CFO"
    )


def test_linkedin_profile_url():

    assert is_linkedin_profile_url(
        "https://www.linkedin.com/in/jane-doe"
    )


def test_linkedin_profile_url_without_www():

    assert is_linkedin_profile_url(
        "https://linkedin.com/in/jane-doe"
    )


def test_linkedin_company_url_rejected():

    assert not is_linkedin_profile_url(
        "https://www.linkedin.com/company/postman"
    )


def test_linkedin_jobs_url_rejected():

    assert not is_linkedin_profile_url(
        "https://www.linkedin.com/jobs/"
    )


def test_normalize_linkedin_url():

    result = normalize_linkedin_url(
        "https://linkedin.com/in/jane-doe/"
    )

    assert result == (
        "https://www.linkedin.com/in/jane-doe"
    )


def test_company_name_from_domain():

    assert company_name_from_domain(
        "postman.com"
    ) == "postman"


def test_search_query():

    result = build_search_query(
        "Abhinav Asthana",
        "postman.com",
    )

    assert '"Abhinav Asthana"' in result

    assert '"postman"' in result

    assert "LinkedIn" in result
