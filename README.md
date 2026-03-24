# Linq Meeting Follow-up Agent

An AI assistant you reach through **iMessage** (via [Linq](https://linqapp.com)): you say who to follow up with after a meeting, it looks up the event on **Google Calendar**, drafts a **personalized follow-up email** with **Google Gemini**, shows you the draft in the chat, and only **sends via Gmail** after you confirm.

---

## How it works (end-to-end)

1. **Linq** receives your iMessage and `POST`s JSON to your server’s `/webhook` endpoint.
2. The server ignores messages marked as sent by you (`is_from_me`) to avoid loops.
3. If your message looks like a **confirmation** (e.g. “send it”), the app sends the **pending draft** for that chat via the Gmail API.
4. Otherwise it uses **Gemini** to extract **who** to follow up with and any **notes** from your message.
5. It searches **Google Calendar** (primary calendar, last N days) for a matching attendee or event title (**fuzzy matching**).
6. It asks **Gemini** again to produce **to / subject / body** JSON for the email, with a simple template fallback if parsing fails.
7. The draft is stored **in memory** keyed by Linq `chat_id` and returned as plain text in iMessage.
8. The server **POSTs the reply** to Linq’s Partner API so you see it in the same thread.

```mermaid
flowchart LR
  subgraph imessage [iMessage]
    U[User]
  end
  subgraph linq [Linq]
    L[Bridge]
  end
  subgraph app [This service]
    W[webhook.py]
    I[intent.py]
    A[agent.py]
    C[google_calendar.py]
    G[gmail.py]
  end
  subgraph google [Google]
    Cal[Calendar API]
    Gem[Gemini]
    GM[Gmail API]
  end
  U <--> L
  L -->|POST /webhook| W
  W --> I
  I --> Gem
  W --> A
  A --> C
  C --> Cal
  A --> Gem
  A --> G
  G --> GM
  W -->|POST chat message| L
```

---

## Current scope vs. product wording

| Capability | Status |
|------------|--------|
| iMessage in/out via Linq | Implemented |
| Calendar lookup + fuzzy name match | Implemented |
| Draft email with Gemini (+ notes from your message) | Implemented |
| Send only after explicit confirmation | Implemented |
| Read prior **Gmail thread** for context | **Not implemented** — Gmail is used to **send** (and `create_draft` exists but is unused by the agent). Drafting uses calendar + your iMessage notes + Gemini only. |

---

## Requirements

- Python **3.12+**
- [uv](https://github.com/astral-sh/uv) or another way to install dependencies from `pyproject.toml`
- A Linq Partner setup with **API key** and a **webhook** pointing at your deployed `/webhook` URL
- **Google Cloud** OAuth client (`credentials.json`) with Calendar + Gmail scopes (see `src/auth.py`)
- **Gemini API** key

---

## Configuration

Create a `.env` in the project root (loaded by `src/config.py`):

| Variable | Purpose |
|----------|---------|
| `LINQ_API_KEY` | Bearer token for `https://api.linqapp.com/api/partner/v3/chats/{chat_id}/messages` |
| `LINQ_PHONE_NUMBER` | Required by config validation (used for your Linq / routing setup) |
| `GEMINI_API_KEY` | Google GenAI client |

Place **`credentials.json`** (OAuth client secret JSON) in the **working directory** from which you start the server (usually the repo root). After first auth, **`token.json`** is written alongside it.

`src/config.py` also defines:

- `GEMINI_MODEL` (e.g. `gemini-2.5-flash`)
- `CALENDAR_LOOKBACK_DAYS` (default **7**)
- `FUZZY_MATCH_THRESHOLD` for [thefuzz](https://github.com/seatgeek/thefuzz) partial ratio (default **70**)

---

## Run the server

From the repository root (so `src` imports and relative `token.json` / `credentials.json` paths resolve as expected):

```bash
uv sync
uv run uvicorn src.webhook:app --host 0.0.0.0 --port 8000
```

Expose `https://your-host/webhook` to Linq’s webhook configuration.

`main.py` is a placeholder CLI; the live app is **`src.webhook:app`**.

---

## HTTP contract (Linq)

### Inbound: `POST /webhook`

The handler expects JSON shaped like:

- `data.is_from_me` — if `true`, the handler returns immediately (no reply).
- `data.chat_id` — Linq chat identifier; used for replies and for **pending draft** storage.
- `data.message.parts[0].value` — user text (first text part).

### Outbound reply

The server posts to:

`https://api.linqapp.com/api/partner/v3/chats/{chat_id}/messages`

with header `Authorization: Bearer {LINQ_API_KEY}` and body:

```json
{
  "message": {
    "parts": [{ "type": "text", "value": "<reply string>" }]
  }
}
```

---

## Conversation flow

1. **Follow-up request** — e.g. “Follow up with Alex, great culture fit.”  
   - Gemini extracts `name` + `notes`.  
   - Calendar match → draft → shown in iMessage.  
   - Draft is stored in `pending_drafts[chat_id]` (RAM only; **lost on restart**).

2. **Confirmation** — phrases include: `send it`, `yes send`, `send the email`, `confirm`, `go ahead` (see `CONFIRMATION_PHRASES` in `src/agent.py`).  
   - Matched **before** intent extraction so “send it” does not get parsed as a new person.  
   - Sends the pending `DraftEmail` via Gmail.

3. **Unknown intent** — if extraction yields `name == "unknown"`, the user gets a short clarification prompt.

The bot text mentions **“edit: …”** as a hint for changes; **that path is not implemented** — only confirm-send and new requests are handled in code.

---

## Project layout

| Path | Role |
|------|------|
| `src/webhook.py` | FastAPI app: validates Linq payload, routes to intent vs confirmation, posts reply to Linq. |
| `src/agent.py` | Orchestration: `find_meeting` → `draft_email` (Gemini) → `pending_drafts`; on confirm, `send_email`. |
| `src/intent.py` | Gemini JSON extraction → `Intent(name, action, notes)`. |
| `src/models.py` | Pydantic models: `Intent`, `Meeting`, `DraftEmail`. |
| `src/google_calendar.py` | Calendar API list + fuzzy match on title and attendees → `Meeting` or `None`. |
| `src/gmail.py` | `send_email` (used); `create_draft` (Gmail draft API, **not** wired into the agent). |
| `src/auth.py` | OAuth flow; scopes: calendar read-only, Gmail modify. |
| `src/config.py` | Env loading, Gemini client, tunables. |
| `src/populate_calendar.py` | Test event seeder — **entire file is commented out**; uncomment to run locally as a script. |
| `main.py` | Unused hello-world entrypoint. |

---

## Google OAuth scopes

Defined in `src/auth.py`:

- `https://www.googleapis.com/auth/calendar.readonly`
- `https://www.googleapis.com/auth/gmail.modify`

First run may open a browser for consent; tokens persist in `token.json`.

---

## Dependencies (summary)

See `pyproject.toml` for pinned versions. Notable packages: **FastAPI**, **Uvicorn**, **httpx**, **google-api-python-client**, **google-auth-oauthlib**, **google-genai**, **thefuzz**, **python-dotenv**.

---

## Troubleshooting

- **“Could not find a meeting”** — Name must match an attendee or event title in the lookback window; try full name or check `CALENDAR_LOOKBACK_DAYS` / threshold.
- **No pending draft on confirm** — Server restarted (in-memory store cleared) or different `chat_id`.
- **401 / 429 from Gemini** — API key or quota; see logs in `intent.py` / `agent.py`.
- **`token.json` / path issues** — Run Uvicorn from the directory where `credentials.json` lives, or adjust `auth.py` to absolute paths.

---

## License / ownership

Add your license or internal ownership here if applicable.
