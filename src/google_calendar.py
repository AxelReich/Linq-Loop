from thefuzz import fuzz
from pydantic import BaseModel
from auth import authenticate_google
from googleapiclient.discovery import build
from datetime import datetime, timedelta, timezone
from models import Meeting


def find_meeting(name: str) -> Meeting | None:
    creds = authenticate_google()
    service = build('calendar', 'v3', credentials=creds)

    # 1. Set time range — last 7 days
    now = datetime.now(timezone.utc)
    seven_days_ago = (now - timedelta(days=7)).isoformat()

    # 2. Fetch events
    events_result = service.events().list(
        calendarId='primary',
        timeMin=seven_days_ago,
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    events = events_result.get('items', [])

    # 3. Loop through events and find attendee matching name
    for event in events:
        attendees = event.get('attendees', [])
        for attendee in attendees:
            if name.lower() in attendee.get('displayName', '').lower() \
            or name.lower() in attendee.get('email', '').lower() \
            or fuzz.partial_ratio(name.lower(), attendee.get('displayName', '').lower()) > 70:
                return Meeting(
                    summary=event.get('summary', 'No title'),
                    start_time=event['start'].get('dateTime', ''),
                    attendee_name=attendee.get('displayName', ''),
                    attendee_email=attendee.get('email', '')
                )
    return None


if __name__ == '__main__':
    meeting = find_meeting("Juan")
    print(meeting)
