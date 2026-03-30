"""
Health check endpoints.
"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", summary="Basic health check")
def health_check():
    """Return service liveness status."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "Personal Finance App API",
    }


@router.get("/db", summary="Database connectivity check")
def db_health_check(db: Session = Depends(get_db)):
    """
    Verify that the application can reach the database.

    Returns ``{"status": "healthy"}`` on success or ``{"status": "unhealthy"}``
    with an error message if the database is unreachable.
    """
    try:
        db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as exc:
        # Do not surface raw exception text to the caller — log it server-side
        logger.error("Database health check failed: %s", exc)
        return {"status": "unhealthy", "database": "unreachable"}
