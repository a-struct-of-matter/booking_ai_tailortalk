from datetime import datetime, timedelta, timezone
from google.oauth2 import service_account
from googleapiclient.discovery import build
import os
import json
import base64
from google.auth.transport.requests import Request
from dateutil.parser import parse
# Globals
SCOPES = ['https://www.googleapis.com/auth/calendar']
CAL_ID = os.getenv(
    "GOOGLE_CALENDAR_ID",
    'e699a00a92f6b1a2bc12455c667f28b71feb0b1b6a8ccfe556bd2810ac430f63@group.calendar.google.com'
)

#to check available slots

def get_free_slots_for_day(date_string: str) -> list[str]:
    try:
        service = get_calendar_service()
        local_tz = datetime.now(timezone.utc).astimezone().tzinfo


        if date_string.lower().strip() == "today":
            date_obj = datetime.now(local_tz).date()
        elif date_string.lower().strip() == "tomorrow":
            date_obj = (datetime.now(local_tz) + timedelta(days=1)).date()
        else:
            date_obj = parse(date_string).date()

        start_of_day = datetime.combine(date_obj, datetime.min.time(), tzinfo=local_tz).replace(hour=9)
        end_of_day = datetime.combine(date_obj, datetime.min.time(), tzinfo=local_tz).replace(hour=17)

        events_result = service.events().list(
            calendarId=CAL_ID,
            timeMin=start_of_day.isoformat(),
            timeMax=end_of_day.isoformat(),
            singleEvents=True,
            orderBy='startTime',
        ).execute()

        busy_slots = []
        for event in events_result.get("items", []):
            start = parse(event["start"].get("dateTime"))
            end = parse(event["end"].get("dateTime"))
            busy_slots.append((start, end))

        free_slots = []
        current = start_of_day
        while current < end_of_day:
            next_slot = current + timedelta(minutes=30)
            if all(not (b[0] < next_slot and current < b[1]) for b in busy_slots):
                free_slots.append(f"{current.strftime('%I:%M %p')} to {next_slot.strftime('%I:%M %p')}")
            current = next_slot

        return free_slots
    except Exception as e:
        return [f"Error: {str(e)}"]


# retrieve calendar services from google cloud service using credentials via environment
def get_calendar_service():
    try:
        sa_b64 = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
        if not sa_b64:
            raise ValueError("Missing GOOGLE_SERVICE_ACCOUNT_JSON environment variable.")

        service_account_info = json.loads(base64.b64decode(sa_b64).decode("utf-8"))
        credentials = service_account.Credentials.from_service_account_info(service_account_info, scopes=SCOPES)

        if credentials.valid and not credentials.expired and credentials.token:
            service = build('calendar', 'v3', credentials=credentials)
        else:
            credentials.refresh(Request())
            service = build('calendar', 'v3', credentials=credentials)

        print("Calendar Service Created Successfully")
        return service
    except Exception as e:
        error_msg = f"ERROR: Unable to create Google Calendar service: {e}"
        print(error_msg)
        raise ConnectionError(error_msg)


# checking slot using time and date
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


# Book event using time and date using LLM output
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


