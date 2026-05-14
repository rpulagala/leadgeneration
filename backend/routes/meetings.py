from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models import Agency, Meeting
from schemas import MeetingCreate, MeetingUpdate, MeetingResponse
from services import calendar_service, email_service
from datetime import datetime
import logging

router = APIRouter(prefix="/api/meetings", tags=["meetings"])
logger = logging.getLogger(__name__)


@router.get("", response_model=List[MeetingResponse])
def list_meetings(
    agency_id: Optional[int] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    q = db.query(Meeting)
    if agency_id:
        q = q.filter(Meeting.agency_id == agency_id)
    if status:
        q = q.filter(Meeting.status == status)
    return q.order_by(Meeting.scheduled_date.desc()).offset(skip).limit(limit).all()


@router.get("/{meeting_id}", response_model=MeetingResponse)
def get_meeting(meeting_id: int, db: Session = Depends(get_db)):
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return meeting


@router.post("", response_model=MeetingResponse, status_code=201)
def create_meeting(payload: MeetingCreate, send_invite: bool = True, db: Session = Depends(get_db)):
    agency = db.query(Agency).filter(Agency.id == payload.agency_id).first()
    if not agency:
        raise HTTPException(status_code=404, detail="Agency not found")

    meeting = Meeting(**payload.model_dump())
    db.add(meeting)
    db.commit()
    db.refresh(meeting)

    if send_invite and agency.email:
        try:
            ics_bytes = calendar_service.build_meeting_invite(
                {
                    "scheduled_date": meeting.scheduled_date,
                    "duration_minutes": meeting.duration_minutes,
                    "title": meeting.title,
                    "description": meeting.description,
                    "location": meeting.location,
                },
                {"email": agency.email, "contact_person": agency.contact_person, "name": agency.name},
            )
            ics_path = f"/tmp/invite_{meeting.id}.ics"
            with open(ics_path, "wb") as f:
                f.write(ics_bytes)

            invite_body = f"""
            <p>Dear {agency.contact_person or 'Care Team'},</p>
            <p>Please find attached a calendar invite for our meeting: <strong>{meeting.title}</strong></p>
            <p><strong>Date:</strong> {meeting.scheduled_date.strftime('%A, %d %B %Y at %H:%M')}</p>
            <p><strong>Duration:</strong> {meeting.duration_minutes} minutes</p>
            <p><strong>Location:</strong> {meeting.location or 'TBD'}</p>
            <p>We look forward to speaking with you.</p>
            <p>Best regards,<br>{email_service.SENDER_NAME}<br>{email_service.COMPANY_NAME}</p>
            """
            email_service.send_email(
                to_address=agency.email,
                subject=f"Meeting Invitation: {meeting.title}",
                html_body=invite_body,
                attachment_path=ics_path,
            )
        except Exception as e:
            logger.warning(f"Could not send calendar invite: {e}")

    if agency.status in ("new", "contacted", "responded"):
        agency.status = "meeting_scheduled"
    db.commit()

    return meeting


@router.put("/{meeting_id}", response_model=MeetingResponse)
def update_meeting(meeting_id: int, payload: MeetingUpdate, db: Session = Depends(get_db)):
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(meeting, field, value)

    # Update agency status on conversion
    if payload.outcome == "converted":
        agency = db.query(Agency).filter(Agency.id == meeting.agency_id).first()
        if agency:
            agency.status = "converted"

    db.commit()
    db.refresh(meeting)
    return meeting


@router.get("/{meeting_id}/ical")
def download_ical(meeting_id: int, db: Session = Depends(get_db)):
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    agency = db.query(Agency).filter(Agency.id == meeting.agency_id).first()

    ics_bytes = calendar_service.build_meeting_invite(
        {
            "scheduled_date": meeting.scheduled_date,
            "duration_minutes": meeting.duration_minutes,
            "title": meeting.title,
            "description": meeting.description,
            "location": meeting.location,
        },
        {
            "email": agency.email if agency else "",
            "contact_person": agency.contact_person if agency else "",
            "name": agency.name if agency else "",
        },
    )
    return Response(
        content=ics_bytes,
        media_type="text/calendar",
        headers={"Content-Disposition": f"attachment; filename=meeting_{meeting_id}.ics"},
    )


@router.delete("/{meeting_id}", status_code=204)
def delete_meeting(meeting_id: int, db: Session = Depends(get_db)):
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    db.delete(meeting)
    db.commit()
