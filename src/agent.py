import json
from src.config import gemini_client, GEMINI_MODEL
from src.models import Intent, Meeting, DraftEmail
from src.google_calendar import find_meeting
from src.gmail import send_email

pending_drafts: dict[str, DraftEmail] = {}

CONFIRMATION_PHRASES = ["send it", "yes send", "send the email", "confirm", "go ahead", "send it"]


def draft_email(meeting: Meeting, notes: str) -> DraftEmail:
    """
    Calls Gemini to generate a personalized follow-up email based on
    the meeting details and recruiter notes. Falls back to a simple
    template if Gemini fails.
    """
    SYSTEM_PROMPT = f"""
    You are a professional recruiting assistant.
    Draft a warm, concise follow-up email based on the meeting and recruiter notes.
    Return ONLY valid JSON, no markdown, no explanation.

    Return this structure:
    {{
        "to": "{meeting.attendee_email}",
        "subject": "short relevant subject line",
        "body": "full email body, professional and personalized. Sign off as 'The Recruiting Team'"
    }}

    Meeting title: {meeting.summary}
    Candidate name: {meeting.attendee_name or meeting.attendee_email}
    Recruiter notes: {notes}
    """
    try:
        response = gemini_client.models.generate_content(
            model=GEMINI_MODEL,
            contents=SYSTEM_PROMPT
        )
        if not response.text:
            raise ValueError("Gemini returned empty response")

        raw = response.text.strip().replace("```json", "").replace("```", "")
        data = json.loads(raw)
        return DraftEmail(**data)

    except Exception as e:
        print(f"Draft email error: {e}")
        return DraftEmail(
            to=meeting.attendee_email,
            subject=f"Following up - {meeting.summary}",
            body=f"Hi {meeting.attendee_name or 'there'},\n\nIt was great speaking with you. {notes}\n\nBest regards,\nThe Recruiting Team"
        )


async def handle_message(chat_id: str, intent: Intent | None, raw_message: str) -> str:
    """
    Main orchestrator. Takes the parsed intent from the recruiter's message
    and decides what to do - find a meeting, draft an email, or send a
    confirmed draft. Never sends email without explicit recruiter approval.
    """

    # Handle confirmation — check this first before anything else
    if any(phrase in raw_message.lower() for phrase in CONFIRMATION_PHRASES):
        draft = pending_drafts.get(chat_id)
        if not draft:
            return "No pending draft found. Try sending a follow-up request first."

        success = send_email(draft)
        if success:
            del pending_drafts[chat_id]
            return f"Email sent to {draft.to}."
        else:
            return "Something went wrong sending the email. Try again."

    # Should not happen but guard against None intent
    if intent is None:
        return "I could not understand that. Try: 'Follow up with Juan, he was great.'"

    # Find the meeting
    meeting = find_meeting(intent.name)
    if not meeting:
        return f"I could not find a meeting with '{intent.name}' in the last 7 days. Did you mean someone else?"

    # Draft the email
    draft = draft_email(meeting, intent.notes)
    pending_drafts[chat_id] = draft

    return (
        f"Here is your draft:\n\n"
        f"To: {draft.to}\n"
        f"Subject: {draft.subject}\n\n"
        f"{draft.body}\n\n"
        f"Reply 'send it' to send or 'edit: ...' to make changes."
    )