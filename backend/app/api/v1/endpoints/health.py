from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db

router = APIRouter()


@router.get("/health")
def health_check():
    return {"status": "ok", "service": "StudyMate AI API"}


@router.get("/health/db")
def health_check_db(db: Session = Depends(get_db)):
    """Confirms the API can actually reach Postgres, not just that the process is alive."""
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}
