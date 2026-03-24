import json
from src.models import Intent
from src.config import gemini_client, GEMINI_MODEL



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
        # Use 'gemini_client' and 'GEMINI_MODEL' from your config
        response = gemini_client.models.generate_content(
            model=GEMINI_MODEL,
            contents=AGENT_ACTION
        )
        
        if not response.text:
            raise ValueError("Gemini returned empty response")
            
        # Clean up the string to ensure it's just JSON
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
        return Intent(name="unknown", action="uknown", notes=message_text)
