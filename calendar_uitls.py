from datetime import datetime, timedelta, timezone
from google.oauth2 import service_account
from googleapiclient.discovery import build
import os

from google.auth.transport.requests import Request

SERVICE_ACCOUNT_FILE = os.getenv(
    "GOOGLE_SERVICE_ACCOUNT_FILE",
    "C:/Users/revan/PycharmProjects/Booking_agent/utilities/booking-464615-53561ef0a4d9.json"
)
SCOPES = ['https://www.googleapis.com/auth/calendar']
CAL_ID = os.getenv(
    "GOOGLE_CALENDAR_ID",
    'e699a00a92f6b1a2bc12455c667f28b71feb0b1b6a8ccfe556bd2810ac430f63@group.calendar.google.com'
)


def get_calendar_service():
    try:
        credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)

        if credentials.valid and not credentials.expired and credentials.token:
            service = build('calendar', 'v3', credentials=credentials)
        else:
            credentials.refresh(Request())
            service = build('calendar', 'v3', credentials=credentials)

        print("Calendar Service Created Successfully")
        return service
    except FileNotFoundError:
        error_msg = f"ERROR: Service account file not found at {SERVICE_ACCOUNT_FILE}. Please check the path."
        print(error_msg)
        raise FileNotFoundError(error_msg)
    except Exception as e:
        error_msg = f"ERROR: Unable to create Google Calendar service: {e}"
        print(error_msg)
        raise ConnectionError(error_msg)


def check_slot(start_time_iso: str, end_time_iso: str) -> bool:
    service = None
    try:
        service = get_calendar_service()
    except Exception as e:
        print(f"Failed to get calendar service for check_slot: {e}")
        return False

    try:
        events_result = service.events().list(
            calendarId=CAL_ID,
            timeMin=start_time_iso,
            timeMax=end_time_iso,
            singleEvents=True,
            orderBy='startTime',
        ).execute()

        events = events_result.get('items', [])
        return len(events) == 0
    except Exception as e:
        print(f"ERROR: Failed to check slot for {start_time_iso} to {end_time_iso}: {e}")
        return False


def book_event(summary: str, start_time_iso: str, end_time_iso: str, desc="Booking done through agent") -> dict:
    service = None
    try:
        service = get_calendar_service()
    except Exception as e:
        print(f"Failed to get calendar service for book_event: {e}")
        return {
            'eventLink': None,
            'start': start_time_iso,
            'end': end_time_iso,
            'summary': summary,
            'status': 'failed',
            'error_message': f"Could not get calendar service: {e}"
        }

    event_body = {
        'summary': summary,
        'description': desc,
        'start': {
            'dateTime': start_time_iso,
            'timeZone': 'Asia/Kolkata'
        },
        'end': {
            'dateTime': end_time_iso,
            'timeZone': 'Asia/Kolkata'
        },
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'email', 'minutes': 24 * 60},
                {'method': 'popup', 'minutes': 10},
            ],
        },
    }

    try:
        created_event = service.events().insert(calendarId=CAL_ID, body=event_body).execute()

        return {
            'eventLink': created_event.get('htmlLink'),
            'start': start_time_iso,
            'end': end_time_iso,
            'summary': summary,
            'status': 'success'
        }
    except Exception as e:
        print(f"ERROR: Failed to book event '{summary}' from {start_time_iso} to {end_time_iso}: {e}")
        return {
            'eventLink': None,
            'start': start_time_iso,
            'end': end_time_iso,
            'summary': summary,
            'status': 'failed',
            'error_message': str(e)
        }
