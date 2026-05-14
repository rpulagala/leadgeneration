from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from database import get_db
from models import Agency
from schemas import ScrapeRequest
from services.scraper_service import scrape_uk_care_agencies
import logging

router = APIRouter(prefix="/api/scrape", tags=["scraper"])
logger = logging.getLogger(__name__)

scrape_status = {"running": False, "last_count": 0, "last_run": None, "message": ""}


@router.get("/status")
def get_scrape_status():
    return scrape_status


def _run_scrape(max_results: int, page: int, db_url: str):
    from database import SessionLocal
    scrape_status["running"] = True
    scrape_status["message"] = "Fetching agencies from CQC registry..."
    db = SessionLocal()
    try:
        agencies = scrape_uk_care_agencies(max_results=max_results, page=page)
        added = 0
        for data in agencies:
            cqc_id = data.get("cqc_id")
            if cqc_id:
                existing = db.query(Agency).filter(Agency.cqc_id == cqc_id).first()
                if existing:
                    continue
            agency = Agency(**data)
            db.add(agency)
            added += 1
        db.commit()
        scrape_status["last_count"] = added
        scrape_status["message"] = f"Done. Added {added} new agencies."
        logger.info(f"Scrape complete: {added} agencies added")
    except Exception as e:
        scrape_status["message"] = f"Error: {str(e)}"
        logger.error(f"Scrape error: {e}")
    finally:
        db.close()
        scrape_status["running"] = False


@router.post("")
def trigger_scrape(
    payload: ScrapeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    if scrape_status["running"]:
        return {"message": "Scrape already running", "status": scrape_status}

    from database import DATABASE_URL
    background_tasks.add_task(
        _run_scrape,
        payload.max_results,
        payload.page,
        DATABASE_URL,
    )
    return {"message": "Scrape started in background", "status": scrape_status}
