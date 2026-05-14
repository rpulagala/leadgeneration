import os
import uuid
from datetime import datetime, timedelta
from typing import Optional
from icalendar import Calendar, Event, vCalAddress, vText
import pytz

COMPANY_NAME = os.getenv("COMPANY_NAME", "Our Company")
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS", "")
SENDER_NAME = os.getenv("SENDER_NAME", "")


def create_ical_invite(
    title: str,
    start_dt: datetime,
    duration_minutes: int,
    description: str,
    location: str,
    organizer_email: str,
    organizer_name: str,
    attendee_email: str,
    attendee_name: str,
    uid: Optional[str] = None,
) -> bytes:
    """Generate an ICS calendar invite as bytes."""
    cal = Calendar()
    cal.add("prodid", f"-//{COMPANY_NAME}//Lead Generation//EN")
    cal.add("version", "2.0")
    cal.add("method", "REQUEST")

    event = Event()
    event.add("summary", title)
    event.add("dtstart", start_dt)
    event.add("dtend", start_dt + timedelta(minutes=duration_minutes))
    event.add("dtstamp", datetime.utcnow())
    event.add("uid", uid or str(uuid.uuid4()))
    event.add("description", description or "")
    event.add("location", location or "")
    event.add("status", "CONFIRMED")
    event.add("sequence", 0)

    org = vCalAddress(f"MAILTO:{organizer_email}")
    org.params["cn"] = vText(organizer_name)
    org.params["role"] = vText("REQ-PARTICIPANT")
    event.add("organizer", org)

    att = vCalAddress(f"MAILTO:{attendee_email}")
    att.params["cn"] = vText(attendee_name)
    att.params["role"] = vText("REQ-PARTICIPANT")
    att.params["rsvp"] = vText("TRUE")
    event.add("attendee", att, encode=0)

    cal.add_component(event)
    return cal.to_ical()


def build_meeting_invite(meeting_data: dict, agency_data: dict) -> bytes:
    """Convenience wrapper that builds an ICS invite from DB row dicts."""
    start = meeting_data["scheduled_date"]
    if isinstance(start, str):
        start = datetime.fromisoformat(start)

    return create_ical_invite(
        title=meeting_data.get("title", "Meeting"),
        start_dt=start,
        duration_minutes=meeting_data.get("duration_minutes", 60),
        description=meeting_data.get("description", ""),
        location=meeting_data.get("location", ""),
        organizer_email=EMAIL_ADDRESS,
        organizer_name=SENDER_NAME or COMPANY_NAME,
        attendee_email=agency_data.get("email", ""),
        attendee_name=agency_data.get("contact_person") or agency_data.get("name", ""),
    )
