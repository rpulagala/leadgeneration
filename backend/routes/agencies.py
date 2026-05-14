from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from database import get_db
from models import Agency, Communication, Meeting
from schemas import AgencyCreate, AgencyUpdate, AgencyResponse, DashboardStats
from datetime import datetime

router = APIRouter(prefix="/api/agencies", tags=["agencies"])


@router.get("/stats", response_model=DashboardStats)
def get_stats(db: Session = Depends(get_db)):
    total_agencies = db.query(Agency).count()
    emails_sent = db.query(Communication).filter(Communication.direction == "sent").count()
    emails_received = db.query(Communication).filter(Communication.direction == "received").count()
    meetings_scheduled = db.query(Meeting).count()
    meetings_completed = db.query(Meeting).filter(Meeting.status == "completed").count()
    conversions = db.query(Agency).filter(Agency.status == "converted").count()

    # Recent activity: last 10 comms + meetings combined
    recent_comms = db.query(Communication).order_by(Communication.date.desc()).limit(5).all()
    recent_meetings = db.query(Meeting).order_by(Meeting.created_at.desc()).limit(5).all()

    activity = []
    for c in recent_comms:
        agency = db.query(Agency).filter(Agency.id == c.agency_id).first()
        activity.append({
            "type": "email",
            "direction": c.direction,
            "date": c.date.isoformat(),
            "agency": agency.name if agency else "Unknown",
            "subject": c.subject,
        })
    for m in recent_meetings:
        agency = db.query(Agency).filter(Agency.id == m.agency_id).first()
        activity.append({
            "type": "meeting",
            "status": m.status,
            "date": m.scheduled_date.isoformat(),
            "agency": agency.name if agency else "Unknown",
            "title": m.title,
        })

    activity.sort(key=lambda x: x["date"], reverse=True)

    return DashboardStats(
        total_agencies=total_agencies,
        emails_sent=emails_sent,
        emails_received=emails_received,
        meetings_scheduled=meetings_scheduled,
        meetings_completed=meetings_completed,
        conversions=conversions,
        recent_activity=activity[:10],
    )


@router.get("", response_model=List[AgencyResponse])
def list_agencies(
    status: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    q = db.query(Agency)
    if status:
        q = q.filter(Agency.status == status)
    if search:
        q = q.filter(Agency.name.ilike(f"%{search}%"))
    return q.order_by(Agency.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/{agency_id}", response_model=AgencyResponse)
def get_agency(agency_id: int, db: Session = Depends(get_db)):
    agency = db.query(Agency).filter(Agency.id == agency_id).first()
    if not agency:
        raise HTTPException(status_code=404, detail="Agency not found")
    return agency


@router.post("", response_model=AgencyResponse, status_code=201)
def create_agency(payload: AgencyCreate, db: Session = Depends(get_db)):
    if payload.cqc_id:
        existing = db.query(Agency).filter(Agency.cqc_id == payload.cqc_id).first()
        if existing:
            return existing
    agency = Agency(**payload.model_dump())
    db.add(agency)
    db.commit()
    db.refresh(agency)
    return agency


@router.put("/{agency_id}", response_model=AgencyResponse)
def update_agency(agency_id: int, payload: AgencyUpdate, db: Session = Depends(get_db)):
    agency = db.query(Agency).filter(Agency.id == agency_id).first()
    if not agency:
        raise HTTPException(status_code=404, detail="Agency not found")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(agency, field, value)
    agency.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(agency)
    return agency


@router.delete("/{agency_id}", status_code=204)
def delete_agency(agency_id: int, db: Session = Depends(get_db)):
    agency = db.query(Agency).filter(Agency.id == agency_id).first()
    if not agency:
        raise HTTPException(status_code=404, detail="Agency not found")
    db.delete(agency)
    db.commit()
