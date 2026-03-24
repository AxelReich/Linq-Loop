import base64
from email.mime.text import MIMEText
from googleapiclient.discovery import build
from src.auth import authenticate_google
from src.models import DraftEmail


def send_email(draft: DraftEmail) -> bool:
    """
    Sends an email via the Gmail API using the authenticated user's account.
    Only call this function after the recruiter has explicitly confirmed
    with 'send it' — never call this automatically.

    Returns True if sent successfully, False otherwise.
    """
    
    try:
        creds = authenticate_google()
        service = build('gmail', 'v1', credentials=creds)

        # Build the MIME message
        message = MIMEText(draft.body)
        message['to'] = draft.to
        message['subject'] = draft.subject

        # Gmail API requires base64 URL-safe encoded raw email
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

        service.users().messages().send(
            userId='me',
            body={'raw': raw}
        ).execute()

        print(f"Email sent to {draft.to}")
        return True

    except Exception as e:
        print(f"Gmail send error: {e}")
        return False


def create_draft(draft: DraftEmail) -> str | None:
    """
    Saves the email as a Gmail draft instead of sending it immediately.
    Useful for double-checking in Gmail before sending.
    Returns the draft ID if successful, None otherwise.
    """

    try:
        creds = authenticate_google()
        service = build('gmail', 'v1', credentials=creds)

        message = MIMEText(draft.body)
        message['to'] = draft.to
        message['subject'] = draft.subject

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

        result = service.users().drafts().create(
            userId='me',
            body={'message': {'raw': raw}}
        ).execute()

        draft_id = result.get('id')
        print(f"Draft saved with ID: {draft_id}")
        return draft_id

    except Exception as e:
        print(f"Gmail draft error: {e}")
        return None