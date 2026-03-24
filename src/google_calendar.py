from thefuzz import fuzz
from googleapiclient.discovery import build
from datetime import datetime, timedelta, timezone
from src.models import Meeting
from src.auth import authenticate_google
from src.config import CALENDAR_LOOKBACK_DAYS, FUZZY_MATCH_THRESHOLD


def find_meeting(name: str, days: int = CALENDAR_LOOKBACK_DAYS) -> Meeting | None:
    """
    Searches Google Calendar for a meeting with the given attendee name
    in the last N days. Uses fuzzy matching so 'Jon' matches 'Jonathan'.
    Returns None if no match found.
    """
    creds = authenticate_google()
    service = build('calendar', 'v3', credentials=creds)

    now = datetime.now(timezone.utc)
    lookback = (now - timedelta(days=days)).isoformat()

    events_result = service.events().list(
        calendarId='primary',
        timeMin=lookback,
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    events = events_result.get('items', [])

    for event in events:
        # Also check if the name matches the event title itself
        event_title = event.get('summary', '')
        if fuzz.partial_ratio(name.lower(), event_title.lower()) > FUZZY_MATCH_THRESHOLD:
            attendees = event.get('attendees', [])
            # Get first non-organizer attendee
            for attendee in attendees:
                if not attendee.get('organizer'):
                    return Meeting(
                        summary=event_title,
                        start_time=event['start'].get('dateTime', ''),
                        attendee_name=attendee.get('displayName', ''),
                        attendee_email=attendee.get('email', '')
                    )

        # Also search by attendee name/email
        attendees = event.get('attendees', [])
        for attendee in attendees:
            display_name = attendee.get('displayName', '').lower()
            email = attendee.get('email', '').lower()
            name_lower = name.lower()

            if name_lower in display_name \
            or name_lower in email \
            or fuzz.partial_ratio(name_lower, display_name) > FUZZY_MATCH_THRESHOLD:
                return Meeting(
                    summary=event_title,
                    start_time=event['start'].get('dateTime', ''),
                    attendee_name=attendee.get('displayName', ''),
                    attendee_email=attendee.get('email', '')
                )

    return None