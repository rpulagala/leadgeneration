from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class AgencyBase(BaseModel):
    name: str
    address: Optional[str] = None
    phone: Optional[str] = None
    contact_person: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    status: Optional[str] = "new"
    notes: Optional[str] = None
    cqc_id: Optional[str] = None


class AgencyCreate(AgencyBase):
    pass


class AgencyUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    contact_person: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class AgencyResponse(AgencyBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class CommunicationBase(BaseModel):
    agency_id: int
    direction: str
    subject: str
    message: str
    email_from: Optional[str] = None
    email_to: Optional[str] = None


class CommunicationCreate(CommunicationBase):
    pass


class CommunicationResponse(CommunicationBase):
    id: int
    date: datetime
    status: str
    message_id: Optional[str] = None

    model_config = {"from_attributes": True}


class MeetingBase(BaseModel):
    agency_id: int
    scheduled_date: datetime
    duration_minutes: Optional[int] = 60
    title: str
    description: Optional[str] = None
    location: Optional[str] = None


class MeetingCreate(MeetingBase):
    pass


class MeetingUpdate(BaseModel):
    scheduled_date: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    title: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    status: Optional[str] = None
    meeting_notes: Optional[str] = None
    outcome: Optional[str] = None


class MeetingResponse(MeetingBase):
    id: int
    status: str
    meeting_notes: Optional[str] = None
    outcome: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class EmailSendRequest(BaseModel):
    agency_id: int
    subject: str
    message: str
    use_template: Optional[bool] = False


class ScrapeRequest(BaseModel):
    query: Optional[str] = "UK care agencies"
    max_results: Optional[int] = 50
    page: Optional[int] = 1


class DashboardStats(BaseModel):
    total_agencies: int
    emails_sent: int
    emails_received: int
    meetings_scheduled: int
    meetings_completed: int
    conversions: int
    recent_activity: List[dict]
