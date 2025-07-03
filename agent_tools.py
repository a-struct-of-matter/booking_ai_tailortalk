from datetime import datetime, timedelta, timezone
from calendar_uitls import check_slot, book_event, get_free_slots_for_day
from dateutil.parser import parse
from pydantic import BaseModel, Field

# Model to resolve the input message
class BookSlotInput(BaseModel):
    summary: str = Field(..., description="Title or description of the calendar event")
    start_time: str = Field(..., description="Natural language time, e.g., 'today at 4pm'")
    end_time: str | None = Field(None, description="Optional natural language end time")

#checking available slot tool

def get_today_free_slots(date_string: str) -> str:
    slots = get_free_slots_for_day(date_string)
    if isinstance(slots, list) and slots:
        return "\n".join(slots)
    return "No free slots available today."


# checking availability of slot in calendar
def check_availability(datetime_string: str) -> str:
    """Checks if the given time slot is available."""
    try:
        start_dt = parse(datetime_string, fuzzy=True, dayfirst=False, yearfirst=False)
        local_timezone = datetime.now(timezone.utc).astimezone().tzinfo
        start_dt_aware = start_dt.replace(tzinfo=local_timezone) if start_dt.tzinfo is None else start_dt
        end_dt_aware = start_dt_aware + timedelta(minutes=30)
        start_iso = start_dt_aware.isoformat()
        end_iso = end_dt_aware.isoformat()

        available = check_slot(start_iso, end_iso)

        if isinstance(available, bool):
            return "Slot is available." if available else "Slot is not available."
        else:
            return f"Received unexpected response from calendar check: {available}"
    except Exception as e:
        return f"Failed to process your request for availability: {str(e)}"

# booking slot
def book_slot_event(summary: str, start_time: str, end_time: str = None) -> str:
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

        if not check_slot(start_iso, end_iso):
            return f" That time slot is already booked. Please try another time."

        event_result = book_event(summary, start_iso, end_iso)

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
        return f"An unexpected error occurred while trying to book the event: {str(e)}"
