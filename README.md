# Autonomous Lead Enrichment Agent

A Python-based autonomous web intelligence pipeline that accepts company domains, crawls their public websites using headless browser automation, preprocesses the retrieved content, and uses Google Gemini with Pydantic structured outputs to generate company intelligence.

The pipeline is designed to be modular, resilient, token-efficient, and suitable for downstream lead-enrichment workflows.

---

## Features

- Headless browser crawling using Playwright
- JavaScript-rendered page support
- Automatic discovery of relevant internal pages
- Domain-restricted crawling
- HTML-to-clean-text preprocessing
- Removal of scripts, CSS, SVGs, iframes, navigation, and footer boilerplate
- Google Gemini LLM integration
- Strict Pydantic structured outputs
- Public email extraction using deterministic regex matching
- Leadership/team member extraction
- LinkedIn URL extraction when explicitly present in website content
- Confidence scoring
- Timeout and page-failure handling
- Per-domain error isolation
- Retry and resilience utilities
- Approximate token and API cost tracking
- JSON output suitable for downstream lead-enrichment workflows
- Automated test suite

---

# AI Lead Enrichment Agent

## Architecture

```text
Company Domains
      |
      v
Playwright Browser
      |
      v
Homepage Retrieval
      |
      v
Relevant Page Discovery
      |
      +--> About
      +--> About Us
      +--> Company
      +--> Team
      +--> Contact
      +--> Pricing
      +--> Leadership
      |
      v
HTML Cleaning
      |
      v
Clean, Bounded Text
      |
      +--> Deterministic Email Extraction
      |
      v
Google Gemini
      |
      v
Pydantic Structured Output
      |
      v
Confidence Scoring
      |
      v
output/output.json
```


---

## Project Structure

```text
ai-lead-enrichment/
├── app/
│   ├── __init__.py
│   ├── main.py                 # CLI entry point
│   ├── config.py               # Environment/configuration
│   ├── crawler.py              # Playwright browser + page discovery
│   ├── extractor.py            # HTML → clean text
│   ├── llm.py                  # Gemini + structured output
│   ├── schemas.py              # Pydantic models
│   ├── resilience.py           # Retry/error-handling utilities
│   └── cost_tracker.py         # Token/cost estimation
├── output/
│   └── output.json
├── tests/
│   ├── test_crawler.py
│   ├── test_extractor.py
│   ├── test_resilience.py
│   └── test_schemas.py
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Requirements

- Python 3.10+
- Google Gemini API key
- Internet connection
- Chromium / Playwright
- The application uses Google Gemini for LLM-based structured extraction.

---

## Installation

1. Clone the repository
git clone <your-github-repository-url>
cd ai-lead-enrichment

2. Create a virtual environment
Windows
python -m venv .venv

macOS/Linux
python3 -m venv .venv

3. Activate the virtual environment
Windows PowerShell
.venv\Scripts\activate

macOS/Linux
source .venv/bin/activate

After activation, the terminal should show something similar to:

(.venv)

4. Install Python dependencies
python -m pip install -r requirements.txt

5. Install Playwright Chromium
playwright install chromium

---

## Environment Variables

Create a .env file in the project root.

Example:

GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-3.6-flash

MAX_PAGES_PER_DOMAIN=8
PAGE_TIMEOUT_MS=20000
MAX_CONTENT_CHARS=60000

The Gemini API key can be created using Google AI Studio.

Never commit .env to the repository.

The repository should contain .env.example, but not the actual .env file.

---

## Running the Agent

The application accepts one or more company domains from the command line.

For example:

python -m app.main postman.com

For the complete assignment test:

python -m app.main postman.com supabase.com vapi.ai

The three required test targets are:

postman.com
supabase.com
vapi.ai

The generated results are stored at:

output/output.json

##Assignment Requirements Covered
This project is designed to address the core requirements of the Autonomous Lead Enrichment Agent assignment.

Step 1: Automated Browsing & Content Retrieval
The crawler uses Playwright with Chromium in headless mode.

For each company domain, the crawler:

Opens the company homepage.
Waits for the page to load.
Supports JavaScript-rendered content through browser automation.
Extracts internal links from the rendered page.
Restricts discovered links to the target domain and its subdomains.
Normalizes discovered URLs.
Removes duplicate URLs.
Prioritizes relevant company pages.
Crawls pages until the configured page limit is reached.
Relevant paths include:

/about
/about-us
/company
/team
/contact
/contact-us
/pricing
/leadership

This allows the pipeline to find useful company information without crawling an uncontrolled number of pages.

Step 2: Context Pre-Processing & Token Optimization
Raw HTML is never directly sent to Gemini.

Before LLM processing, the HTML is parsed using BeautifulSoup.

The preprocessing pipeline removes unnecessary DOM elements including:

script
style
svg
noscript
iframe
canvas
template
nav
footer

The remaining content is converted into clean text and excessive whitespace is removed.

The resulting text is also bounded using:

MAX_CONTENT_CHARS

This reduces unnecessary LLM input, latency, and API cost.

Public email addresses are additionally extracted deterministically using a regular expression.

This provides an independent extraction mechanism for an important lead-enrichment field.

Step 3: LLM Structured Extraction
The project uses Google Gemini for structured information extraction.

The LLM receives:

Company domain
Cleaned website content
Relevant page content
The output is validated against Pydantic models.

The primary extraction schema contains:

Company Overview
Target Audience / ICP
Contact Points
Leadership / Team Members
Company Overview
A concise two-sentence description of what the company does.

Target Audience / ICP
The likely primary customer or user group based only on the supplied website content.

Contact Points
Public or generic email addresses explicitly found in the website content.

Leadership / Team Members
People explicitly identified on the website as founders, executives, leaders, or notable team members.

Where available, the system records LinkedIn profile URLs that are explicitly present in the supplied website content.

The model is instructed not to invent information that is not supported by the supplied website content.

Pydantic Structured Validation
Pydantic provides an explicit schema for the LLM response.

This makes the output predictable and easier to consume downstream.

The structured extraction model includes fields such as:

company_overview
target_audience
contact_points
leadership

The final company result additionally contains:

domain
confidence_score
pages_scraped
errors
estimated_input_tokens
estimated_output_tokens
estimated_cost_usd

This ensures that the final JSON output follows a consistent structure even when some information is unavailable.

Step 4: Fallback & Resilience
The application is designed so that failure on one website does not terminate the entire run.

Common failure conditions include:

Page timeouts
404 pages
Empty pages
Failed page navigation
Link discovery failures
Missing page elements
JavaScript rendering issues
Websites returning unusable content
LLM extraction failures
Errors are captured in the corresponding company's errors array.

For example:

{
  "domain": "example.com",
  "confidence_score": 0.0,
  "pages_scraped": [],
  "errors": [
    "Homepage could not be retrieved."
  ]
}

The application then continues processing the remaining domains.

Retry and resilience functionality is separated into:

app/resilience.py

This keeps retry behavior independent from the crawling and extraction logic.

Confidence Scoring
The confidence score is calculated from observable extraction signals rather than being arbitrarily generated by the LLM.

Signals include:

Company overview successfully extracted
Target audience identified
Public contact email found
Leadership identified
LinkedIn profile discovered
Multiple relevant pages successfully crawled
The final score is normalized to a range of:

0.0 - 1.0

A higher score indicates that more of the expected company intelligence was successfully identified.

The score is intended as an estimate of extraction completeness and quality rather than a guarantee that every extracted fact is correct.

Token & Cost Tracking
The project includes approximate token and API cost tracking as an optional bonus feature.

The system records:

estimated_input_tokens
estimated_output_tokens
estimated_cost_usd

Token counts are approximate and are intended for monitoring rather than billing-grade accounting.

Cost configuration is maintained separately in:

app/cost_tracker.py

Model pricing should be verified against the current Gemini API pricing before using the values for financial or billing purposes.

---

## Design Decisions

Why Playwright?
Playwright provides reliable headless browser automation and supports JavaScript-rendered websites that may not expose useful content through a simple HTTP request.

This is particularly useful for modern company websites where important content is rendered dynamically in the browser.

Why BeautifulSoup?
BeautifulSoup is used to parse the rendered HTML and remove unnecessary DOM elements before the content reaches the LLM.

This reduces token usage and improves extraction quality.

Why Gemini?
Google Gemini provides structured output capabilities that can be validated against Pydantic models.

The LLM provider is isolated inside:

app/llm.py

This keeps the rest of the application independent of the specific model provider and makes future provider changes easier.

Why Pydantic?
Pydantic provides explicit schemas and validation for the LLM response.

This reduces malformed outputs and makes downstream processing predictable.

Why deterministic email extraction?
Emails are extracted using a deterministic regular expression in addition to LLM extraction.

This provides an independent extraction mechanism for an important lead-enrichment field and reduces dependence on the LLM for straightforward pattern-based data.

Why domain-restricted crawling?
The agent is intended to enrich company information from the company's own public web presence.

Restricting crawling to the target domain prevents uncontrolled traversal and reduces unnecessary requests.

---

## Output

Each processed company produces structured information containing:

Company overview
Target audience / ICP
Public contact emails
Leadership/team members
LinkedIn URLs when explicitly discoverable from website content
Confidence score
Successfully scraped pages
Errors encountered
Estimated input tokens
Estimated output tokens
Estimated API cost
Example:

{
  "domain": "example.com",
  "company_overview": "Example provides software solutions for modern engineering teams. Its platform helps teams build and manage their technical workflows.",
  "target_audience": "Developers and engineering teams",
  "contact_points": [
    "support@example.com"
  ],
  "leadership": [
    {
      "name": "Jane Doe",
      "role": "Co-Founder & CEO",
      "linkedin_url": "https://www.linkedin.com/in/janedoe"
    }
  ],
  "confidence_score": 0.9,
  "pages_scraped": [
    "https://example.com",
    "https://example.com/about"
  ],
  "errors": [],
  "estimated_input_tokens": 4500,
  "estimated_output_tokens": 300,
  "estimated_cost_usd": 0.0009
}

The actual output values depend on the content returned by each website and should be generated by running the application rather than manually fabricated.

---

## Testing

The project includes tests under:

tests/

Current test coverage includes:

Same-domain URL validation
Subdomain handling
External-domain rejection
URL normalization
Relevant-page ranking
Duplicate link handling
URL scoring
Email extraction
Email deduplication
Email case normalization
HTML cleaning
Async retry behavior
Retry exhaustion
Non-retryable error handling
Invalid retry configuration
Pydantic schema validation
Optional LinkedIn fields
Default list values
Confidence score validation
Run the complete test suite from the repository root:

python -m pytest -v

Expected result:

21 passed

The exact number may change if additional tests are added.

Example Test Output
A successful test run should look similar to:

===================================== test session starts =====================================

platform win32 -- Python ...
plugins: ...
collected 21 items

tests/test_crawler.py ... PASSED
tests/test_extractor.py ... PASSED
tests/test_resilience.py ... PASSED
tests/test_schemas.py ... PASSED

====================================== 21 passed ==============================================

---

## Error Isolation

The pipeline processes domains independently.

For example, if three domains are provided:

python -m app.main postman.com supabase.com vapi.ai

and one website fails because of a timeout or blocking mechanism, the other domains can still be processed.

A failed domain is represented in the output rather than terminating the complete program.

This design is important for batch lead-enrichment workflows where one problematic website should not prevent the remaining companies from being processed.

---

## Rate Limits

The crawler uses configurable page limits and timeouts to prevent uncontrolled crawling.

###Relevant settings include:

MAX_PAGES_PER_DOMAIN=8
PAGE_TIMEOUT_MS=20000
MAX_CONTENT_CHARS=60000

These values can be adjusted depending on the desired balance between coverage, latency, and cost.

---

## Troubleshooting

ModuleNotFoundError
If Python reports that a package is missing, make sure the virtual environment is activated:

.venv\Scripts\activate

Then reinstall dependencies:

python -m pip install -r requirements.txt

pytest is not recognized on Windows
Instead of:

pytest -v

use:

python -m pytest -v

This ensures that pytest is executed from the currently active Python environment.

Gemini API Key Error
If you see:

GEMINI_API_KEY is missing

check that:

.env exists in the project root.
The variable is named exactly GEMINI_API_KEY.
The API key is valid.
The virtual environment is active.
Example:

GEMINI_API_KEY=your_gemini_api_key_here

Playwright Browser Error
If Playwright reports that Chromium is missing, run:

playwright install chromium

Website Timeout
If a website takes too long to load, the crawler records the failure and continues processing other domains.

The timeout can be adjusted using:

PAGE_TIMEOUT_MS=20000

Empty or Incomplete Website Content
Some websites may return limited content because of:

Bot protection
Client-side rendering
Rate limiting
Temporary network problems
Geo-specific content
Website changes
The pipeline records errors where possible and continues processing the remaining domains.

---

## Assignment Test Targets

The implementation was designed to run against the three domains specified in the assignment:

postman.com
supabase.com
vapi.ai

Run them together using:

python -m app.main postman.com supabase.com vapi.ai

After completion, inspect:

output/output.json

The output should contain one result object per requested domain.

---

## Sample Output File

The repository should include:

output/output.json

This file should be generated by actually running the application against:

postman.com
supabase.com
vapi.ai


