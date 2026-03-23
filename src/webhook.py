import httpx
import os
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from src.intent import extract_intent

load_dotenv()
LINQ_API_KEY = os.getenv("LINQ_API_KEY")

if not LINQ_API_KEY:
    raise RuntimeError("LINQ_API_KEY not found in .env")


app = FastAPI()

@app.post("/webhook")
async def receive_message(request: Request):
    body = await request.json()
    print("PAYLOAD:", body)

    # Echo it back to yourself for now


    # Stop the loop 
    if body["data"]["is_from_me"]:
        return {"status": "ok"}

    message_text = body["data"]["message"]["parts"][0]["value"]
    print(f"Message from user: {message_text}")
    chat_id = body["data"]["chat_id"]

    try: 
        intent = extract_intent(message_text)
        print("INTENT:", intent)
        reply = f"I understood: {intent}"
    except RuntimeError: 
        reply = "Sorry I could not understand. Try somehting like: 'Follow up with Juan, moving to the next round'"




    if not chat_id:
        print("chatId not found in payload")
        return {"status": "ok"}

    # Reply back
    url = f"https://api.linqapp.com/api/partner/v3/chats/{chat_id}/messages"
    payload = {
        "message": {
            "parts": [
                {
                    "type": "text",
                    "value": reply
                }
            ]
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