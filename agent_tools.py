from datetime import datetime, timedelta, timezone
from langchain.tools import tool
from calendar_uitls import check_slot, book_event
from dateutil.parser import parse

#checking availability of slot in calendar
@tool
def check_availability(datetime_string: str) -> str:
    """Checks if the given time slot is available."""
    print(f"Checking availability for: '{datetime_string}'")
    try:
        start_dt = parse(datetime_string, fuzzy=True, dayfirst=False, yearfirst=False)
        #parsing datetime...
        local_timezone = datetime.now(timezone.utc).astimezone().tzinfo

        start_dt_aware = start_dt.replace(tzinfo=local_timezone) if start_dt.tzinfo is None else start_dt

        end_dt = start_dt_aware + timedelta(minutes=30)
        end_dt_aware = end_dt.replace(tzinfo=local_timezone) if end_dt.tzinfo is None else end_dt

        start_iso = start_dt_aware.isoformat()
        end_iso = end_dt_aware.isoformat()

        print(f"Parsed start time: {start_dt_aware}")
        print(f"Parsed end time: {end_dt_aware}")
        print(f"Calling calendar service to check slot from '{start_iso}' to '{end_iso}'")

        available = check_slot(start_iso, end_iso)

        print(f"Calendar check returned: {available}")

        if isinstance(available, bool):
            return "Slot is available." if available else "Slot is not available."
        else:
            return f"Received unexpected response from calendar check: {available}"

    except Exception as e:
        error_message = f"Failed to process your request for availability: {str(e)}"
        print(f"Error in availability check: {error_message}")
        return error_message


#booking slot
@tool
def book_slot_event(summary: str, start_time: str, end_time: str = None) -> str:
    """Books an event on the calendar with a title and time range."""  # <--- ADDED DOCSTRING
    print(f"Attempting to book event: '{summary}' starting at '{start_time}' (ending '{end_time}')")
    try:
        start_dt = parse(start_time, fuzzy=True, dayfirst=False, yearfirst=False)

        local_timezone = datetime.now(timezone.utc).astimezone().tzinfo

        start_dt_aware = start_dt.replace(tzinfo=local_timezone) if start_dt.tzinfo is None else start_dt

        if end_time is None:
            end_dt_aware = start_dt_aware + timedelta(minutes=30)
        else:
            end_dt = parse(end_time, fuzzy=True, dayfirst=False, yearfirst=False)
            end_dt_aware = end_dt.replace(tzinfo=local_timezone) if end_dt.tzinfo is None else end_dt

        start_iso = start_dt_aware.isoformat()
        end_iso = end_dt_aware.isoformat()

        print(f"Calling calendar service to book event from '{start_iso}' to '{end_iso}'")

        event_result = book_event(summary, start_iso, end_iso)

        print(f"Calendar booking returned: {event_result}")

        if event_result and event_result.get('status') == 'success':
            return (
                f"Event **'{summary}'** has been successfully booked!\n"
                f"It's scheduled from: `{event_result.get('start', start_iso)}`\n"
                f"To: `{event_result.get('end', end_iso)}`\n"
                f"You can view it here: {event_result.get('eventLink', 'Link N/A')}"
            )
        elif event_result and event_result.get('status') == 'failed':
            return f"Sorry, I couldn't book the event: {event_result.get('error_message', 'An unknown booking error occurred.')}"
        else:
            return f"Failed to book event: Received an unexpected response from the calendar service: {event_result}"
    except Exception as e:
        error_message = f"An unexpected error occurred while trying to book the event: {str(e)}"
        print(f"Error in event booking: {error_message}")
        return error_message