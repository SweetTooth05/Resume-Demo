"""
Personal Finance App — FastAPI application entry point.
"""

import asyncio
import logging
import logging.config
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.database import Base, engine
from app.core.schema_migrations import apply_schema_migrations
import app.models.user  # noqa: F401 — register models with Base
import app.models.financial  # noqa: F401
import app.models.stock  # noqa: F401
import app.models.admin  # noqa: F401

# ---------------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------------
logging.config.dictConfig(
    {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                "datefmt": "%Y-%m-%dT%H:%M:%S",
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
            }
        },
        "root": {"level": "INFO", "handlers": ["console"]},
    }
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Application lifespan (replaces deprecated startup/shutdown events)
# ---------------------------------------------------------------------------
async def _scheduled_yahoo_price_refresh_loop() -> None:
    """Periodically sync Yahoo spot prices for all tickers (holdings + recommendations)."""
    from app.core.database import SessionLocal
    from app.services.yahoo_price_service import refresh_all_yahoo_prices

    await asyncio.sleep(90)
    interval_sec = max(3600, int(settings.STOCK_UPDATE_INTERVAL) * 3600)
    while True:
        try:

            def _run_refresh() -> None:
                db = SessionLocal()
                try:
                    from app.services.asx_official_list import sync_official_asx_list

                    n_asx, err = sync_official_asx_list(db, commit=True)
                    if err:
                        logger.warning("Scheduled run: ASX list sync failed: %s", err)
                    elif n_asx:
                        logger.debug("Scheduled run: ASX list synced (%s companies).", n_asx)
                    attempted, updated = refresh_all_yahoo_prices(
                        db, commit=True, stamp_admin_refresh=True
                    )
                    logger.info(
                        "Scheduled Yahoo price refresh: %s tickers, %s updated",
                        attempted,
                        updated,
                    )
                except Exception:
                    logger.exception("Scheduled Yahoo price refresh failed")
                    db.rollback()
                finally:
                    db.close()

            await asyncio.to_thread(_run_refresh)
        except asyncio.CancelledError:
            break
        except Exception:
            logger.exception("Yahoo refresh loop error")
        await asyncio.sleep(interval_sec)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up %s (v%s)", settings.PROJECT_NAME, "1.0.0")
    Base.metadata.create_all(bind=engine)
    apply_schema_migrations()
    logger.info("Database tables ensured.")

    def _bootstrap_asx() -> None:
        from app.core.database import SessionLocal
        from app.services.asx_official_list import sync_official_asx_list

        db = SessionLocal()
        try:
            n, err = sync_official_asx_list(db, commit=True)
            if err:
                logger.warning("ASX official list sync failed: %s", err)
            else:
                logger.info("ASX official company list synced (%s rows).", n)
        except Exception:
            logger.exception("ASX official list bootstrap failed")
            db.rollback()
        finally:
            db.close()

    await asyncio.to_thread(_bootstrap_asx)
    bg_task: Optional[asyncio.Task] = None
    if settings.ENABLE_BACKGROUND_TASKS:
        bg_task = asyncio.create_task(_scheduled_yahoo_price_refresh_loop())
        logger.info(
            "Yahoo price auto-refresh enabled (every %s h).",
            settings.STOCK_UPDATE_INTERVAL,
        )
    yield
    if bg_task is not None:
        bg_task.cancel()
        try:
            await bg_task
        except asyncio.CancelledError:
            pass
    logger.info("Shutting down %s", settings.PROJECT_NAME)


# ---------------------------------------------------------------------------
# Application instance
# ---------------------------------------------------------------------------
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "A comprehensive personal finance management API with AI-powered "
        "stock predictions."
    ),
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

# ---------------------------------------------------------------------------
# Global exception handler
# ---------------------------------------------------------------------------
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catch-all for unhandled exceptions.

    Logs the full traceback server-side but returns a generic message to the
    caller so internal implementation details are never leaked.
    """
    logger.exception(
        "Unhandled exception on %s %s", request.method, request.url.path
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please try again later."},
    )

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(api_router, prefix=settings.API_V1_STR)

# ---------------------------------------------------------------------------
# Static files (optional — do not fail when directory is absent)
# ---------------------------------------------------------------------------
_static_dir = Path(__file__).resolve().parent.parent / "static"
if _static_dir.is_dir():
    app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")

# ---------------------------------------------------------------------------
# Root / meta endpoints
# ---------------------------------------------------------------------------
@app.get("/", include_in_schema=False)
async def root():
    return {
        "message": settings.PROJECT_NAME,
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get("/health", include_in_schema=False)
async def health_check():
    return {"status": "healthy", "message": "API is running"}


# ---------------------------------------------------------------------------
# Dev entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
