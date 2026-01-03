import os
from dotenv import load_dotenv

load_dotenv()

FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")

if not FIRECRAWL_API_KEY:
    raise ValueError("FIRECRAWL_API_KEY not found in .env file")
