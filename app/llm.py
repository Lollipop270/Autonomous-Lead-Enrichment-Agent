from google import genai

from .config import GEMINI_API_KEY, GEMINI_MODEL
from .schemas import CompanyIntelligence


client = genai.Client(
    api_key=GEMINI_API_KEY
)


SYSTEM_PROMPT = """
You are a business intelligence extraction system.

Your task is to extract structured company intelligence
from CLEANED PUBLIC WEBSITE CONTENT.

IMPORTANT RULES:

1. Use ONLY information supported by the supplied content.

2. Never invent or guess:
   - people
   - job titles
   - email addresses
   - LinkedIn URLs
   - company facts

3. If information is not present or cannot be reliably
   determined from the supplied content, return an empty
   value rather than guessing.

4. company_overview:
   - Write exactly two concise sentences.
   - Explain what the company does and the primary value
     of its product/service.

5. target_audience:
   - Identify the primary ideal customer profile.
   - Base this on explicit website language whenever possible.
   - A reasonable inference is acceptable, but do not invent
     specific customer facts.

6. contact_points:
   - Include ONLY email addresses explicitly present in the
     supplied website content.
   - Do not construct or guess email addresses.
   - Preserve the actual email address found in the content.

7. leadership:
   - Include only people explicitly identified as founders,
     executives, leadership, or notable team members.
   - Do not infer leadership based only on a person's name.

8. linkedin_url:
   - Include a LinkedIn URL ONLY when the URL itself is
     explicitly present in the supplied website content.
   - Never construct a LinkedIn URL from someone's name.
   - LinkedIn URLs may also be added later by the
     separate browser-based LinkedIn enrichment step.

9. Do not use outside knowledge.
   Your answer must be based exclusively on the content
   supplied in this request.

10. The output must strictly follow the provided schema.
"""


def extract_company_intelligence(
    domain: str,
    website_text: str,
) -> CompanyIntelligence:

    user_prompt = f"""
Company domain:
{domain}

The following content was collected from the company's
public website.

--- BEGIN WEBSITE CONTENT ---

{website_text}

--- END WEBSITE CONTENT ---

Extract the requested company intelligence using only
the supplied content.
"""

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=[
            SYSTEM_PROMPT,
            user_prompt,
        ],
        config={
            "response_mime_type": "application/json",
            "response_schema": CompanyIntelligence,
            "temperature": 0,
        },
    )

    if response.parsed is None:
        raise ValueError(
            "Gemini returned no structured result."
        )

    return response.parsed
