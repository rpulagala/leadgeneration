import os
import sys
import logging
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

from database import engine, Base
from routes import agencies, scraper, communications, meetings

Base.metadata.create_all(bind=engine)


def seed_if_empty():
    from database import SessionLocal
    from models import Agency, Communication, Meeting
    from datetime import datetime, timedelta

    db = SessionLocal()
    try:
        if db.query(Agency).count() > 0:
            return
        logging.info("Empty database detected — seeding sample data...")

        now = datetime.utcnow()

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

        saved = []
        for data in agencies_data:
            a = Agency(**data)
            db.add(a)
            db.flush()
            saved.append(a)
        db.commit()

        comms = [
            dict(agency=saved[0], direction="sent", days=14,
                 subject="Partnership Opportunity - Streamline Your Care Operations",
                 message="Dear Margaret,\n\nMy name is Alex. We help UK care agencies reduce admin by 70%. Would you be open to a 20-minute call?\n\nBest regards, Alex"),
            dict(agency=saved[0], direction="received", days=11,
                 subject="Re: Partnership Opportunity - Streamline Your Care Operations",
                 message="Hi Alex, thank you for reaching out. We'd be interested in a demo. Kind regards, Margaret"),
            dict(agency=saved[1], direction="sent", days=10,
                 subject="Partnership Opportunity - Streamline Your Care Operations",
                 message="Dear David,\n\nI wanted to reach out about our care management platform.\n\nBest, Alex"),
            dict(agency=saved[1], direction="received", days=8,
                 subject="Re: Partnership Opportunity - Streamline Your Care Operations",
                 message="Hello Alex, this looks very interesting. Let's schedule a call - I'm free next Tuesday.\n\nDavid"),
            dict(agency=saved[1], direction="sent", days=7,
                 subject="Meeting Invitation: Introduction Call - Bloom Home Care",
                 message="Hi David, great! I've sent a calendar invite for Tuesday at 2pm.\n\nAlex"),
            dict(agency=saved[2], direction="sent", days=5,
                 subject="Partnership Opportunity - Streamline Your Care Operations",
                 message="Dear Susan,\n\nI'm reaching out about our CQC compliance tools and scheduling platform.\n\nBest, Alex"),
            dict(agency=saved[3], direction="sent", days=30,
                 subject="Partnership Opportunity - Streamline Your Care Operations",
                 message="Dear James,\n\nI wanted to connect about our care management platform.\n\nBest, Alex"),
            dict(agency=saved[3], direction="received", days=28,
                 subject="Re: Partnership Opportunity",
                 message="Hi Alex, very interested. Let's talk.\n\nJames"),
            dict(agency=saved[3], direction="sent", days=20,
                 subject="Follow-up: Harmony Care Solutions Demo",
                 message="Dear James, thank you for the call. Attaching our proposal as discussed.\n\nAlex"),
            dict(agency=saved[3], direction="received", days=15,
                 subject="Re: Follow-up: Harmony Care Solutions Demo",
                 message="Alex, we're happy to move forward. Please send the contract.\n\nJames"),
            dict(agency=saved[5], direction="sent", days=7,
                 subject="Partnership Opportunity - Streamline Your Care Operations",
                 message="Dear Robert,\n\nI'm reaching out about our care agency platform.\n\nBest, Alex"),
            dict(agency=saved[5], direction="received", days=5,
                 subject="Re: Partnership Opportunity",
                 message="Hi Alex, yes send over more details.\n\nRobert"),
            dict(agency=saved[7], direction="sent", days=3,
                 subject="Partnership Opportunity - Streamline Your Care Operations",
                 message="Dear Andrew,\n\nHope this finds you well. I wanted to introduce our care management platform.\n\nBest, Alex"),
            dict(agency=saved[8], direction="sent", days=9,
                 subject="Partnership Opportunity - Streamline Your Care Operations",
                 message="Dear Claire,\n\nI'm Alex. We help care agencies across Wales and the UK.\n\nBest, Alex"),
            dict(agency=saved[8], direction="received", days=7,
                 subject="Re: Partnership Opportunity",
                 message="Hello Alex, we'd be happy to learn more. Can we arrange a call?\n\nClaire"),
        ]

        for c in comms:
            db.add(Communication(
                agency_id=c["agency"].id, direction=c["direction"],
                subject=c["subject"], message=c["message"],
                email_from="alex@ourcompany.com" if c["direction"] == "sent" else c["agency"].email,
                email_to=c["agency"].email if c["direction"] == "sent" else "alex@ourcompany.com",
                status="sent" if c["direction"] == "sent" else "read",
                date=now - timedelta(days=c["days"]),
            ))
        db.commit()

        meetings_data = [
            dict(agency=saved[1], offset=2, title="Introduction Call - Bloom Home Care",
                 duration=30, location="https://meet.google.com/abc-defg-hij",
                 description="Demo of scheduling module.", status="scheduled", notes=None, outcome=None),
            dict(agency=saved[8], offset=5, title="Discovery Call - TrueBlue Care Ltd",
                 duration=45, location="https://zoom.us/j/123456789",
                 description="Understand pain points and show platform overview.", status="scheduled", notes=None, outcome=None),
            dict(agency=saved[3], offset=-18, title="Demo Call - Harmony Care Solutions",
                 duration=60, location="https://meet.google.com/xyz-abcd-efg",
                 description="Full platform demo.", status="completed",
                 notes="James was impressed with rota management. 45 staff. Wants proposal for 50 users.",
                 outcome="converted"),
            dict(agency=saved[0], offset=-8, title="Intro Call - Sunrise Care Agency",
                 duration=30, location="https://meet.google.com/mno-pqrs-tuv",
                 description="Initial discovery call.", status="completed",
                 notes="Margaret is registered manager. 30 carers. Pain point: paper-based rota. Wants full demo.",
                 outcome="follow_up"),
        ]

        for m in meetings_data:
            sched = (now + timedelta(days=m["offset"])).replace(hour=14, minute=0, second=0, microsecond=0)
            db.add(Meeting(
                agency_id=m["agency"].id, scheduled_date=sched,
                duration_minutes=m["duration"], title=m["title"],
                location=m["location"], description=m["description"],
                status=m["status"], meeting_notes=m["notes"], outcome=m["outcome"],
            ))
        db.commit()
        logging.info("Seed data loaded: 10 agencies, 15 communications, 4 meetings.")
    except Exception as e:
        logging.error(f"Seeding failed: {e}")
        db.rollback()
    finally:
        db.close()


seed_if_empty()

app = FastAPI(title="Lead Generation Platform", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agencies.router)
app.include_router(scraper.router)
app.include_router(communications.router)
app.include_router(meetings.router)

FRONTEND_DIR = Path(os.getenv("FRONTEND_DIR", str(Path(__file__).parent.parent / "frontend")))
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

    @app.get("/")
    def serve_index():
        return FileResponse(str(FRONTEND_DIR / "index.html"))

    @app.get("/{page}.html")
    def serve_page(page: str):
        file_path = FRONTEND_DIR / f"{page}.html"
        if file_path.exists():
            return FileResponse(str(file_path))
        return FileResponse(str(FRONTEND_DIR / "index.html"))


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    reload = os.getenv("RENDER") is None  # no hot-reload on Render
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=reload)
