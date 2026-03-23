import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

# API Keys
LINQ_API_KEY = os.getenv("LINQ_API_KEY")
LINQ_PHONE_NUMBER = os.getenv("LINQ_PHONE_NUMBER")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Validation
if not LINQ_API_KEY:
    raise RuntimeError("LINQ_API_KEY not found in .env")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY not found in .env")

# Clients — initialized once, imported everywhere
gemini_client = genai.Client(api_key=GEMINI_API_KEY)

# Agent behavior config
GEMINI_MODEL = "gemini-2.0-flash-001"
CALENDAR_LOOKBACK_DAYS = 7
FUZZY_MATCH_THRESHOLD = 70