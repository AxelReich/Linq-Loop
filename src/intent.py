import json
import os
from src.config import GEMINI_API_KEY
from google import genai
from pydantic import BaseModel

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY not found in .env")

client = genai.Client(api_key=GEMINI_API_KEY)
print("GEMINI KEY IN USE:", GEMINI_API_KEY[:8])


class Intent(BaseModel):
    name: str
    action: str
    notes: str

def extract_intent(message_text: str)-> Intent:
    AGENT_ACTION = f"""
    You are a data extraction assistant.
    Parse through the response and extract the following: 
    Extract intent from recruiter messages and return ONLY valid JSON.
    No explanation, no markdown, just JSON.

    Return this structure:
    {{
        "name": "person to follow up with",
        "action": "what to do", 
        "notes": "any additional context"
    }}

    Request: {message_text}
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=AGENT_ACTION
        )
        if not response.text:
            raise ValueError("Gemini returned empty response")
            
        raw = response.text.strip().replace("```json", "").replace("```", "")
        data = json.loads(raw)
        return Intent(**data)

    except Exception as e:
        error_str = str(e)
        if "429" in error_str:
            print("Rate limit hit — try a new API key or wait")
        elif "401" in error_str or "403" in error_str:
            print("Invalid API key")
        else:
            print(f"Gemini error: {e}")
        return Intent(name="unknown", action="Miscelanous", notes=message_text)
