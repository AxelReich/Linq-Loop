import datetime
import random
from googleapiclient.discovery import build
from auth import authenticate_google

def create_test_event(summary, email, start_time_iso):
    creds = authenticate_google()
    service = build('calendar', 'v3', credentials=creds)

    # Lazy end time: just replace the hour digit for a 1-hour meeting
    end_time_iso = start_time_iso.replace("T14", "T15").replace("T10", "T11")

    event = {
        'summary': summary,
        'attendees': [{'email': email}],
        'start': {'dateTime': start_time_iso, 'timeZone': 'UTC'},
        'end': {'dateTime': end_time_iso, 'timeZone': 'UTC'},
    }

    try:
        service.events().insert(calendarId='primary', body=event).execute()
        print(f"Created: {summary} with {email}")
    except Exception as e:
        print(f"Failed to create {summary}: {e}")

if __name__ == '__main__':
    # List of test data
    test_meetings = [
        ("Interview with Juan", "juan.tester@notreal.com", "2026-03-22T14:00:00Z"),
        ("Sync with Maria", "m.garcia99@fake.net", "2026-03-22T10:00:00Z"),
        ("Coffee Chat: Peter", "peter.pan@neverland.io", "2026-03-21T14:00:00Z"),
        ("Interview with Juan Silva", "jsilva@random.co", "2026-03-20T14:00:00Z"),
        ("Interview with Axel", "axreich@gmail.com", "2026-03-20T16:00:00Z")
    ]

    print("Populating calendar with test data...")
    for summary, email, start in test_meetings:
        create_test_event(summary, email, start)
    print("Done!")