from pydantic import BaseModel, Field


class LeadershipMember(BaseModel):
    name: str = Field(
        description="Full name of the person."
    )

    role: str = Field(
        description="Job title or role."
    )

    linkedin_url: str | None = Field(
        default=None,
        description=(
            "LinkedIn profile URL if explicitly "
            "found in the supplied website content."
        )
    )


class CompanyIntelligence(BaseModel):
    company_overview: str = Field(
        description=(
            "Concise two-sentence description of what "
            "the company does."
        )
    )

    target_audience: str = Field(
        description=(
            "Primary ideal customer profile or target "
            "audience for the company's product."
        )
    )

    contact_points: list[str] = Field(
        default_factory=list,
        description=(
            "Public email addresses explicitly found "
            "in the supplied website content."
        )
    )

    leadership: list[LeadershipMember] = Field(
        default_factory=list,
        description=(
            "Leadership or notable team members explicitly "
            "identified in the supplied website content."
        )
    )


class CompanyResult(BaseModel):
    domain: str

    company_overview: str = ""

    target_audience: str = ""

    contact_points: list[str] = Field(
        default_factory=list
    )

    leadership: list[LeadershipMember] = Field(
        default_factory=list
    )

    confidence_score: float = Field(
        ge=0.0,
        le=1.0
    )

    pages_scraped: list[str] = Field(
        default_factory=list
    )

    errors: list[str] = Field(
        default_factory=list
    )

    estimated_input_tokens: int = 0

    estimated_output_tokens: int = 0

    estimated_cost_usd: float = 0.0
