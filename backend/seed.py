"""Populate the database with realistic sample data."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from database import SessionLocal, engine, Base
from models import Agency, Communication, Meeting
from datetime import datetime, timedelta

Base.metadata.create_all(bind=engine)
db = SessionLocal()

# ── Agencies ──────────────────────────────────────────────────────────────────
agencies_data = [
    dict(name="Sunrise Care Agency Ltd", address="14 Victoria Road, Birmingham, B12 9HS",
         phone="0121 456 7890", contact_person="Margaret Hollis", email="margaret@sunrisecare.co.uk",
         website="https://sunrisecare.co.uk", status="responded", cqc_id="1-101001001"),
    dict(name="Bloom Home Care Services", address="37 High Street, Manchester, M4 1AE",
         phone="0161 234 5678", contact_person="David Okafor", email="david@bloomhomecare.co.uk",
         website="https://bloomhomecare.co.uk", status="meeting_scheduled", cqc_id="1-101001002"),
    dict(name="CareFirst UK", address="5 Castle Lane, Leeds, LS1 4DP",
         phone="0113 987 6543", contact_person="Susan Patel", email="susan@carefirstuk.co.uk",
         website="https://carefirstuk.co.uk", status="contacted", cqc_id="1-101001003"),
    dict(name="Harmony Care Solutions", address="22 Park View, Bristol, BS1 5LN",
         phone="0117 333 2211", contact_person="James Whitfield", email="james@harmonycare.co.uk",
         website="https://harmonycare.co.uk", status="converted", cqc_id="1-101001004"),
    dict(name="Golden Years Home Care", address="9 Elm Street, Liverpool, L1 8JQ",
         phone="0151 600 4400", contact_person="Patricia Nguyen", email="patricia@goldenyears.co.uk",
         website="https://goldenyearscare.co.uk", status="new", cqc_id="1-101001005"),
    dict(name="Prestige Nursing & Care", address="88 Queen's Road, Sheffield, S2 4DW",
         phone="0114 276 5500", contact_person="Robert Singh", email="robert@prestigenursing.co.uk",
         website="https://prestigenursing.co.uk", status="responded", cqc_id="1-101001006"),
    dict(name="Heartfelt Care Agency", address="3 Maple Avenue, Nottingham, NG1 2HT",
         phone="0115 841 7700", contact_person="Linda Osei", email="linda@heartfeltcare.co.uk",
         website="https://heartfeltcare.co.uk", status="new", cqc_id="1-101001007"),
    dict(name="Pinnacle Home Support", address="61 Bridge Street, Leicester, LE1 4RQ",
         phone="0116 255 8833", contact_person="Andrew Morris", email="andrew@pinnaclesupport.co.uk",
         website="https://pinnaclesupport.co.uk", status="contacted", cqc_id="1-101001008"),
    dict(name="TrueBlue Care Ltd", address="17 Station Road, Cardiff, CF10 1GH",
         phone="029 2099 1122", contact_person="Claire Evans", email="claire@truebluecare.co.uk",
         website="https://truebluecare.co.uk", status="meeting_scheduled", cqc_id="1-101001009"),
    dict(name="Compassion First Care", address="45 Westgate, Newcastle, NE1 5XA",
         phone="0191 477 3300", contact_person="Michael Brown", email="michael@compassionfirst.co.uk",
         website="https://compassionfirst.co.uk", status="new", cqc_id="1-101001010"),
]

saved_agencies = []
for data in agencies_data:
    existing = db.query(Agency).filter(Agency.cqc_id == data["cqc_id"]).first()
    if existing:
        saved_agencies.append(existing)
    else:
        a = Agency(**data)
        db.add(a)
        db.flush()
        saved_agencies.append(a)

db.commit()
print(f"[OK] {len(saved_agencies)} agencies added")

# ── Communications ────────────────────────────────────────────────────────────
now = datetime.utcnow()

comms_data = [
    # Sunrise Care - responded
    dict(agency=saved_agencies[0], direction="sent", days_ago=14,
         subject="Partnership Opportunity – Streamline Your Care Operations",
         message="Dear Margaret,\n\nMy name is Alex from LeadGen. We help UK care agencies reduce admin by 70% with our scheduling and compliance platform. Would you be open to a 20-minute call?\n\nBest regards,\nAlex"),
    dict(agency=saved_agencies[0], direction="received", days_ago=11,
         subject="Re: Partnership Opportunity – Streamline Your Care Operations",
         message="Hi Alex,\n\nThank you for reaching out. We are always looking at ways to improve our processes. Could you send me some more information? We'd be interested in a demo.\n\nKind regards,\nMargaret"),
    # Bloom - meeting scheduled
    dict(agency=saved_agencies[1], direction="sent", days_ago=10,
         subject="Partnership Opportunity – Streamline Your Care Operations",
         message="Dear David,\n\nI wanted to reach out about our care management platform. We've helped agencies like yours cut admin time significantly.\n\nBest,\nAlex"),
    dict(agency=saved_agencies[1], direction="received", days_ago=8,
         subject="Re: Partnership Opportunity – Streamline Your Care Operations",
         message="Hello Alex,\n\nThis looks very interesting. We're currently reviewing our systems. Let's schedule a call — I'm free next Tuesday afternoon.\n\nDavid"),
    dict(agency=saved_agencies[1], direction="sent", days_ago=7,
         subject="Meeting Invitation: Introduction Call – Bloom Home Care",
         message="Hi David,\n\nGreat! I've sent a calendar invite for Tuesday at 2pm. Looking forward to speaking with you.\n\nAlex"),
    # CareFirst - contacted
    dict(agency=saved_agencies[2], direction="sent", days_ago=5,
         subject="Partnership Opportunity – Streamline Your Care Operations",
         message="Dear Susan,\n\nI'm reaching out from LeadGen. We specialise in CQC compliance tools and scheduling for care agencies across the UK.\n\nWould you be open to a quick call?\n\nBest,\nAlex"),
    # Harmony - converted
    dict(agency=saved_agencies[3], direction="sent", days_ago=30,
         subject="Partnership Opportunity – Streamline Your Care Operations",
         message="Dear James,\n\nI wanted to connect about our care management platform.\n\nBest,\nAlex"),
    dict(agency=saved_agencies[3], direction="received", days_ago=28,
         subject="Re: Partnership Opportunity",
         message="Hi Alex, very interested. Let's talk.\n\nJames"),
    dict(agency=saved_agencies[3], direction="sent", days_ago=20,
         subject="Follow-up: Harmony Care Solutions Demo",
         message="Dear James,\n\nThank you for the call last week. Attaching our proposal as discussed.\n\nAlex"),
    dict(agency=saved_agencies[3], direction="received", days_ago=15,
         subject="Re: Follow-up: Harmony Care Solutions Demo",
         message="Alex, we've reviewed the proposal and we're happy to move forward. Please send the contract.\n\nJames"),
    # Prestige - responded
    dict(agency=saved_agencies[5], direction="sent", days_ago=7,
         subject="Partnership Opportunity – Streamline Your Care Operations",
         message="Dear Robert,\n\nI'm reaching out about our care agency platform. Could we schedule a brief call?\n\nBest,\nAlex"),
    dict(agency=saved_agencies[5], direction="received", days_ago=5,
         subject="Re: Partnership Opportunity",
         message="Hi Alex, yes send over more details and we can take it from there.\n\nRobert"),
    # Pinnacle - contacted
    dict(agency=saved_agencies[7], direction="sent", days_ago=3,
         subject="Partnership Opportunity – Streamline Your Care Operations",
         message="Dear Andrew,\n\nHope this finds you well. I wanted to introduce our care management platform.\n\nBest,\nAlex"),
    # TrueBlue - meeting scheduled
    dict(agency=saved_agencies[8], direction="sent", days_ago=9,
         subject="Partnership Opportunity – Streamline Your Care Operations",
         message="Dear Claire,\n\nI'm Alex from LeadGen. We help care agencies across Wales and the UK.\n\nBest,\nAlex"),
    dict(agency=saved_agencies[8], direction="received", days_ago=7,
         subject="Re: Partnership Opportunity",
         message="Hello Alex,\n\nWe'd be happy to learn more. Can we arrange a call for next week?\n\nClaire"),
]

comm_count = 0
for c in comms_data:
    agency = c["agency"]
    date = now - timedelta(days=c["days_ago"])
    comm = Communication(
        agency_id=agency.id,
        direction=c["direction"],
        subject=c["subject"],
        message=c["message"],
        email_from="alex@ourcompany.com" if c["direction"] == "sent" else agency.email,
        email_to=agency.email if c["direction"] == "sent" else "alex@ourcompany.com",
        status="sent" if c["direction"] == "sent" else "read",
        date=date,
    )
    db.add(comm)
    comm_count += 1

db.commit()
print(f"[OK] {comm_count} communications added")

# ── Meetings ──────────────────────────────────────────────────────────────────
meetings_data = [
    dict(agency=saved_agencies[1], days_offset=2,
         title="Introduction Call – Bloom Home Care", duration_minutes=30,
         location="https://meet.google.com/abc-defg-hij",
         description="Demo of scheduling module and CQC compliance tracking.",
         status="scheduled", meeting_notes=None, outcome=None),
    dict(agency=saved_agencies[8], days_offset=5,
         title="Discovery Call – TrueBlue Care Ltd", duration_minutes=45,
         location="https://zoom.us/j/123456789",
         description="Understand their current pain points and show platform overview.",
         status="scheduled", meeting_notes=None, outcome=None),
    dict(agency=saved_agencies[3], days_ago=18,
         title="Demo Call – Harmony Care Solutions", duration_minutes=60,
         location="https://meet.google.com/xyz-abcd-efg",
         description="Full platform demo including care planning and reporting.",
         status="completed",
         meeting_notes="James was very impressed with the rota management feature. Mentioned they have 45 staff. Asked for a proposal with pricing for 50 users. Follow-up: send proposal by Friday.",
         outcome="converted"),
    dict(agency=saved_agencies[0], days_ago=8,
         title="Intro Call – Sunrise Care Agency", duration_minutes=30,
         location="https://meet.google.com/mno-pqrs-tuv",
         description="Initial discovery call.",
         status="completed",
         meeting_notes="Margaret is the registered manager. They have 30 carers. Main pain point is paper-based rota and CQC compliance logs. Interested in a full demo. Schedule follow-up demo.",
         outcome="follow_up"),
]

meeting_count = 0
for m in meetings_data:
    agency = m["agency"]
    if "days_offset" in m:
        sched = now + timedelta(days=m["days_offset"])
    else:
        sched = now - timedelta(days=m["days_ago"])
    sched = sched.replace(hour=14, minute=0, second=0, microsecond=0)

    meeting = Meeting(
        agency_id=agency.id,
        scheduled_date=sched,
        duration_minutes=m["duration_minutes"],
        title=m["title"],
        location=m["location"],
        description=m["description"],
        status=m["status"],
        meeting_notes=m.get("meeting_notes"),
        outcome=m.get("outcome"),
    )
    db.add(meeting)
    meeting_count += 1

db.commit()
print(f"[OK] {meeting_count} meetings added")
print("\nSample data loaded successfully!")
db.close()
