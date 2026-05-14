from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models import Agency, Communication
from schemas import CommunicationResponse, EmailSendRequest
from services import email_service
from datetime import datetime
import logging

router = APIRouter(prefix="/api/communications", tags=["communications"])
logger = logging.getLogger(__name__)


@router.get("", response_model=List[CommunicationResponse])
def list_communications(
    agency_id: Optional[int] = None,
    direction: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    q = db.query(Communication)
    if agency_id:
        q = q.filter(Communication.agency_id == agency_id)
    if direction:
        q = q.filter(Communication.direction == direction)
    return q.order_by(Communication.date.desc()).offset(skip).limit(limit).all()


@router.post("/send", response_model=CommunicationResponse, status_code=201)
def send_email(payload: EmailSendRequest, db: Session = Depends(get_db)):
    agency = db.query(Agency).filter(Agency.id == payload.agency_id).first()
    if not agency:
        raise HTTPException(status_code=404, detail="Agency not found")
    if not agency.email:
        raise HTTPException(status_code=400, detail="Agency has no email address")

    body = payload.message
    if payload.use_template:
        body = email_service.render_outreach_email(
            agency_name=agency.name,
            contact_person=agency.contact_person,
        )

    success = email_service.send_email(
        to_address=agency.email,
        subject=payload.subject,
        html_body=body,
    )

    comm = Communication(
        agency_id=payload.agency_id,
        direction="sent",
        subject=payload.subject,
        message=body,
        email_from=email_service.EMAIL_ADDRESS,
        email_to=agency.email,
        status="sent" if success else "failed",
        date=datetime.utcnow(),
    )
    db.add(comm)

    if success and agency.status == "new":
        agency.status = "contacted"

    db.commit()
    db.refresh(comm)
    return comm


@router.post("/fetch-inbox")
def fetch_inbox(db: Session = Depends(get_db)):
    """Pull new emails from IMAP and store any that match known agency emails."""
    emails = email_service.fetch_inbox(max_emails=100)
    if not emails:
        return {"message": "No emails fetched (check credentials or inbox)", "count": 0}

    agency_email_map = {
        a.email.lower(): a for a in db.query(Agency).all() if a.email
    }

    saved = 0
    for em in emails:
        msg_id = em.get("message_id", "")
        if msg_id:
            existing = db.query(Communication).filter(Communication.message_id == msg_id).first()
            if existing:
                continue

        from_addr = em.get("email_from", "")
        matched_email = next(
            (addr for addr in agency_email_map if addr in from_addr.lower()), None
        )

        if not matched_email:
            continue

        agency = agency_email_map[matched_email]
        date = datetime.fromisoformat(em["date"]) if isinstance(em["date"], str) else em["date"]

        comm = Communication(
            agency_id=agency.id,
            direction="received",
            subject=em.get("subject", ""),
            message=em.get("message", ""),
            email_from=from_addr,
            email_to=email_service.EMAIL_ADDRESS,
            status="read",
            date=date,
            message_id=msg_id,
        )
        db.add(comm)

        if agency.status == "contacted":
            agency.status = "responded"

        saved += 1

    db.commit()
    return {"message": f"Saved {saved} new email(s) from known agencies", "count": saved}


@router.delete("/{comm_id}", status_code=204)
def delete_communication(comm_id: int, db: Session = Depends(get_db)):
    comm = db.query(Communication).filter(Communication.id == comm_id).first()
    if not comm:
        raise HTTPException(status_code=404, detail="Communication not found")
    db.delete(comm)
    db.commit()
