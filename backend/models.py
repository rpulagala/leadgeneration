from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime


class Agency(Base):
    __tablename__ = "agencies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    address = Column(Text)
    phone = Column(String(50))
    contact_person = Column(String(255))
    email = Column(String(255))
    website = Column(String(500))
    cqc_id = Column(String(100), unique=True, nullable=True)
    status = Column(String(50), default="new")  # new, contacted, responded, meeting_scheduled, converted
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    communications = relationship("Communication", back_populates="agency", cascade="all, delete-orphan")
    meetings = relationship("Meeting", back_populates="agency", cascade="all, delete-orphan")


class Communication(Base):
    __tablename__ = "communications"

    id = Column(Integer, primary_key=True, index=True)
    agency_id = Column(Integer, ForeignKey("agencies.id"), nullable=False)
    date = Column(DateTime, default=datetime.utcnow)
    direction = Column(String(10))  # sent | received
    subject = Column(String(500))
    message = Column(Text)
    status = Column(String(50), default="sent")  # sent | delivered | read | replied
    email_from = Column(String(255))
    email_to = Column(String(255))
    message_id = Column(String(500))  # IMAP message ID for deduplication

    agency = relationship("Agency", back_populates="communications")


class Meeting(Base):
    __tablename__ = "meetings"

    id = Column(Integer, primary_key=True, index=True)
    agency_id = Column(Integer, ForeignKey("agencies.id"), nullable=False)
    scheduled_date = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, default=60)
    title = Column(String(500))
    description = Column(Text)
    location = Column(String(500))
    status = Column(String(50), default="scheduled")  # scheduled | completed | cancelled | no_show
    meeting_notes = Column(Text)
    outcome = Column(String(100))  # interested | not_interested | follow_up | converted
    created_at = Column(DateTime, default=datetime.utcnow)

    agency = relationship("Agency", back_populates="meetings")
