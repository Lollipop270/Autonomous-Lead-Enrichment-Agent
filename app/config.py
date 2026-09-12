import os

from dotenv import load_dotenv


load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.6-flash"
)

if not GEMINI_API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY is missing. "
        "Add it to your .env file."
    )

MAX_PAGES_PER_DOMAIN = int(
    os.getenv("MAX_PAGES_PER_DOMAIN", "8")
)

PAGE_TIMEOUT_MS = int(
    os.getenv("PAGE_TIMEOUT_MS", "20000")
)

MAX_CONTENT_CHARS = int(
    os.getenv("MAX_CONTENT_CHARS", "60000")
)



