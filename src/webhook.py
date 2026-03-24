import httpx
from fastapi import FastAPI, Request
from src.intent import extract_intent
from src.config import LINQ_API_KEY
from src.agent import handle_message, CONFIRMATION_PHRASES

app = FastAPI()

@app.post("/webhook")
async def receive_message(request: Request):
    body = await request.json()
    print("PAYLOAD:", body)

    if body["data"]["is_from_me"]:
        return {"status": "ok"}

    message_text = body["data"]["message"]["parts"][0]["value"].strip()
    chat_id = body["data"]["chat_id"]
    print(f"Message from user: {message_text}")

    try:
        # Check for confirmation FIRST before calling Gemini
        if any(phrase in message_text.lower() for phrase in CONFIRMATION_PHRASES):
            reply = await handle_message(chat_id, None, message_text)
        else:
            intent = extract_intent(message_text)
            print("INTENT:", intent)

            if intent.name == "unknown":
                reply = "I couldn't quite catch who you want to follow up with. Could you provide a name?"
            else:
                reply = await handle_message(chat_id, intent, message_text)

    except Exception as e:
        print(f"Workflow Error: {e}")
        reply = "Something went wrong. Please try again."

    url = f"https://api.linqapp.com/api/partner/v3/chats/{chat_id}/messages"
    payload = {
        "message": {
            "parts": [{"type": "text", "value": reply}]
        }
    }
    headers = {
        "Authorization": f"Bearer {LINQ_API_KEY}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)
        print("LINQ RESPONSE:", response.status_code, response.json())

    return {"status": "ok"}