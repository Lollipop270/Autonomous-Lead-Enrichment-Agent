import pytest
from pydantic import ValidationError

from app.schemas import (
    CompanyIntelligence,
    CompanyResult,
    LeadershipMember,
)


def test_leadership_member_schema():

    member = LeadershipMember(
        name="Jane Doe",
        role="CEO",
        linkedin_url=(
            "https://linkedin.com/in/janedoe"
        ),
    )

    assert member.name == "Jane Doe"
    assert member.role == "CEO"
    assert (
        member.linkedin_url
        == "https://linkedin.com/in/janedoe"
    )


def test_leadership_member_allows_missing_linkedin():

    member = LeadershipMember(
        name="John Doe",
        role="CTO",
    )

    assert member.linkedin_url is None


def test_company_intelligence_defaults_empty_lists():

    intelligence = CompanyIntelligence(
        company_overview=(
            "Example builds software."
        ),
        target_audience=(
            "Software developers."
        ),
    )

    assert intelligence.contact_points == []
    assert intelligence.leadership == []


def test_company_intelligence_with_leadership():

    intelligence = CompanyIntelligence(
        company_overview=(
            "Example builds software."
        ),
        target_audience=(
            "Software developers."
        ),
        contact_points=[
            "hello@example.com"
        ],
        leadership=[
            LeadershipMember(
                name="Jane Doe",
                role="CEO",
            )
        ],
    )

    assert len(
        intelligence.leadership
    ) == 1

    assert (
        intelligence.leadership[0].name
        == "Jane Doe"
    )


def test_company_result_confidence_score():

    result = CompanyResult(
        domain="example.com",
        company_overview=(
            "Example builds software."
        ),
        target_audience=(
            "Software developers."
        ),
        confidence_score=0.9,
    )

    assert result.confidence_score == 0.9


def test_company_result_rejects_invalid_confidence():

    with pytest.raises(
        ValidationError
    ):

        CompanyResult(
            domain="example.com",
            confidence_score=1.5,
        )
