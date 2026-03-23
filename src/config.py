import os
from dotenv import load_dotenv

load_dotenv()

LINQ_API_KEY = os.getenv("LINQ_API_KEY")
LINQ_PHONE_NUMBER = os.getenv("LINQ_PHONE_NUMBER")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")