"""
Admin portal endpoints.

Provides setup (TOTP QR generation + completion), login, platform metrics,
and SSE-streamed data-refresh / model-retrain operations.

All endpoints that mutate or read sensitive data (except setup and login) are
protected by the ``get_admin_user`` dependency which validates a Bearer JWT
that carries ``{"role": "admin"}``.
"""

import asyncio
import io
import json
import logging
from datetime import datetime
from typing import AsyncGenerator, Optional

import pyotp
import qrcode
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from jose import JWTError, jwt
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import text
from sqlalchemy.orm import Session
from sse_starlette.sse import EventSourceResponse

from app.core.auth import create_access_token, get_password_hash, verify_password
from app.core.config import settings
from app.core.database import get_db, SessionLocal
from app.models.admin import AdminSettings
from app.models.financial import Asset, Debt, Expense, Income
from app.models.stock import StockHolding
from app.services.asx_official_list import sync_official_asx_list
from app.services.recommendation_regen_service import regenerate_stock_tables
from app.services.yahoo_price_service import (
    apply_price_for_ticker,
    format_last_data_hint,
    refresh_all_yahoo_prices,
    stamp_last_data_refresh,
    ticker_last_data_at,
    tickers_for_yahoo_refresh,
    upsert_stock_quote,
    yahoo_last_price,
)
from app.models.user import User
from app.schemas.admin import (
    AdminLoginRequest,
    AdminMetrics,
    AdminSetupVerifyRequest,
    AdminToken,
)

logger = logging.getLogger(__name__)

router = APIRouter()
_bearer = HTTPBearer()

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_or_create_admin_settings(db: Session) -> AdminSettings:
    """Return the single AdminSettings row, creating it if absent."""
    row = db.query(AdminSettings).first()
    if row is None:
        row = AdminSettings()
        db.add(row)
        db.flush()  # assign PK without committing
    return row


def _get_admin_settings_or_404(db: Session) -> AdminSettings:
    """Return the AdminSettings row or raise 404 if it does not exist."""
    row = db.query(AdminSettings).first()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin settings not found. Run setup first.",
        )
    return row


# ---------------------------------------------------------------------------
# Admin JWT dependency
# ---------------------------------------------------------------------------

def get_admin_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> dict:
    """
    FastAPI dependency — decode the Bearer token and verify role == 'admin'.

    Raises HTTP 401 on any failure.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate admin credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        role: Optional[str] = payload.get("role")
        if role != "admin":
            raise credentials_exception
        return payload
    except JWTError:
        raise credentials_exception


# ---------------------------------------------------------------------------
# Setup endpoints
# ---------------------------------------------------------------------------

@router.get("/setup/status", summary="Return whether admin setup has been completed")
def setup_status(db: Session = Depends(get_db)) -> dict:
    """Return ``{"setup_complete": bool}``."""
    row = db.query(AdminSettings).first()
    complete = bool(row and row.setup_complete)
    return {"setup_complete": complete}


@router.get(
    "/setup/qr",
    summary="Generate a TOTP QR code for the admin authenticator app",
    response_class=StreamingResponse,
)
def setup_qr(db: Session = Depends(get_db)) -> StreamingResponse:
    """
    Only callable when setup is NOT yet complete.

    Generates a fresh TOTP secret, stores it in ``AdminSettings``, builds
    a provisioning URI, renders a QR code PNG, and returns it as a streaming
    image response so the admin can scan it with their authenticator app.
    """
    row = _get_or_create_admin_settings(db)

    if row.setup_complete:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin setup is already complete.",
        )

    # Generate a new TOTP secret and persist it immediately so the verify
    # step can look it up regardless of which process handled the QR request.
    secret = pyotp.random_base32()
    row.totp_secret = secret
    db.commit()

    # Build the provisioning URI shown in the QR code.
    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(
        name=settings.ADMIN_EMAIL,
        issuer_name="FinanceApp Admin",
    )

    # Render to PNG in-memory.
    img = qrcode.make(uri)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    return StreamingResponse(buf, media_type="image/png")


@router.post("/setup/complete", summary="Complete admin setup by verifying TOTP and setting password")
def setup_complete(
    body: AdminSetupVerifyRequest,
    db: Session = Depends(get_db),
) -> dict:
    """
    Verify the TOTP code against the stored secret.  If valid, hash and
    persist the password and mark setup as complete.

    Returns ``{"success": true}`` on success, HTTP 400 on bad TOTP.
    """
    row = _get_or_create_admin_settings(db)

    if row.setup_complete:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin setup is already complete.",
        )

    if not row.totp_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="TOTP secret not found. Request the QR code first.",
        )

    totp = pyotp.TOTP(row.totp_secret)
    if not totp.verify(body.totp_code, valid_window=1):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid TOTP code.",
        )

    row.admin_password_hash = get_password_hash(body.password)
    row.setup_complete = True
    db.commit()

    return {"success": True}


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

@router.post("/login", response_model=AdminToken, summary="Authenticate as admin")
def admin_login(
    body: AdminLoginRequest,
    db: Session = Depends(get_db),
) -> AdminToken:
    """
    Three-factor authentication:
    1. Email must match ``settings.ADMIN_EMAIL``.
    2. Password must verify against the stored bcrypt hash.
    3. TOTP code must be valid (Microsoft Authenticator → Add account → Other,
       scan QR at setup, then enter the 6-digit code here).

    On success, issues a short-lived JWT with ``role=admin`` in the payload.
    """
    invalid_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if body.email != settings.ADMIN_EMAIL:
        raise invalid_exc

    row = db.query(AdminSettings).first()
    if row is None or not row.setup_complete:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin setup has not been completed.",
        )

    if not row.admin_password_hash or not verify_password(body.password, row.admin_password_hash):
        raise invalid_exc

    totp = pyotp.TOTP(row.totp_secret)
    if not totp.verify(body.totp_code, valid_window=1):
        raise invalid_exc

    token = create_access_token(data={"sub": "admin", "role": "admin"})
    return AdminToken(access_token=token)


# ---------------------------------------------------------------------------
# Metrics (protected)
# ---------------------------------------------------------------------------

@router.get("/metrics", response_model=AdminMetrics, summary="Return platform-wide metrics")
def admin_metrics(
    _: dict = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> AdminMetrics:
    """Return aggregate counts for all major tables plus DB size and refresh timestamps."""
    total_users = db.query(User).count()
    total_incomes = db.query(Income).count()
    total_expenses = db.query(Expense).count()
    total_assets = db.query(Asset).count()
    total_debts = db.query(Debt).count()
    total_holdings = db.query(StockHolding).count()

    # DB size — works on PostgreSQL; falls back gracefully on SQLite.
    db_size_mb = 0.0
    try:
        result = db.execute(text("SELECT pg_database_size(current_database())")).scalar()
        if result is not None:
            db_size_mb = round(result / (1024 * 1024), 2)
    except Exception:
        pass

    # Refresh / retrain timestamps from admin settings.
    row = db.query(AdminSettings).first()
    last_data_refresh = row.last_data_refresh if row else None
    last_model_trained = row.last_model_trained if row else None

    return AdminMetrics(
        total_users=total_users,
        total_incomes=total_incomes,
        total_expenses=total_expenses,
        total_assets=total_assets,
        total_debts=total_debts,
        total_holdings=total_holdings,
        db_size_mb=db_size_mb,
        last_data_refresh=last_data_refresh,
        last_model_trained=last_model_trained,
    )


# ---------------------------------------------------------------------------
# SSE helpers
# ---------------------------------------------------------------------------

def _sse_event(step: str, progress: int, message: str) -> dict:
    """Build a dict that sse-starlette will serialise as a ``data:`` SSE line."""
    return {"data": json.dumps({"step": step, "progress": progress, "message": message})}


# ---------------------------------------------------------------------------
# Data refresh (SSE, protected)
# ---------------------------------------------------------------------------

def _verify_admin_token_param(token: str) -> dict:
    """Validate an admin JWT passed as a query parameter (required for EventSource)."""
    exc = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin token")
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("role") != "admin":
            raise exc
        return payload
    except JWTError:
        raise exc


@router.get("/refresh/stream", summary="Stream Yahoo Finance data refresh progress via SSE")
async def refresh_stream(
    token: str = Query(..., description="Admin JWT (passed as query param for EventSource compatibility)"),
) -> EventSourceResponse:
    """
    Server-Sent Events endpoint that drives a live Yahoo Finance price refresh.

    Each event ``data`` field is JSON: ``{"step", "progress", "message"}``.
    Per-ticker messages include the latest row timestamps from the DB before Yahoo is queried.
    """
    _verify_admin_token_param(token)

    async def _generate() -> AsyncGenerator[dict, None]:
        yield _sse_event("starting", 0, "Starting Yahoo Finance data refresh...")
        await asyncio.sleep(0)

        db: Session = SessionLocal()
        try:
            yield _sse_event("asx_sync", 3, "Downloading official ASX listed-companies CSV…")
            await asyncio.sleep(0)

            n_asx, asx_err = sync_official_asx_list(db, commit=False)
            if asx_err:
                yield _sse_event(
                    "asx_sync",
                    5,
                    f"ASX CSV sync skipped or failed ({asx_err}); using existing DB or file fallback.",
                )
            else:
                db.commit()
                yield _sse_event(
                    "asx_sync",
                    8,
                    f"ASX official list updated ({n_asx} companies).",
                )

            tickers, asx_names = tickers_for_yahoo_refresh(db)

            if not tickers:
                yield _sse_event(
                    "done",
                    100,
                    "No tickers to refresh — add holdings or run ASX sync successfully.",
                )
                return

            delay = max(0.0, settings.YAHOO_REQUEST_DELAY_SEC)
            total = len(tickers)
            for idx, ticker in enumerate(tickers):
                progress = int((idx / max(total - 1, 1)) * 90) if total > 1 else 0
                last_at = ticker_last_data_at(db, ticker)
                hint = format_last_data_hint(last_at)
                yield _sse_event(
                    "fetching",
                    progress,
                    f"{ticker} — DB last data: {hint} — fetching Yahoo…",
                )
                await asyncio.sleep(0)

                try:
                    price = await asyncio.to_thread(yahoo_last_price, ticker)
                    if price is not None:
                        apply_price_for_ticker(db, ticker, price)
                        upsert_stock_quote(db, ticker, price, asx_names.get(ticker))
                        db.flush()
                    else:
                        logger.warning("Could not refresh %s: no price from Yahoo", ticker)
                except Exception as exc:
                    logger.warning("Could not refresh %s: %s", ticker, exc)

                if delay > 0:
                    await asyncio.sleep(delay)

            stamp_last_data_refresh(db)
            db.commit()

            yield _sse_event("done", 100, "Refresh complete.")

        except Exception as exc:
            logger.exception("Error during data refresh stream")
            yield _sse_event("error", 0, f"Refresh failed: {exc}")
            db.rollback()
        finally:
            db.close()

    return EventSourceResponse(_generate())


# ---------------------------------------------------------------------------
# Model retrain (SSE, protected)
# ---------------------------------------------------------------------------

@router.get("/retrain/stream", summary="Stream ML model retraining progress via SSE")
async def retrain_stream(
    token: str = Query(..., description="Admin JWT (passed as query param for EventSource compatibility)"),
) -> EventSourceResponse:
    """
    Reload ensemble artifacts, refresh Yahoo prices, re-run predictions (sentiment + prices),
    and replace ``stock_predictions`` / ``top_stock_recommendations`` so dashboards update.

    Full offline training is not run here; that remains a separate StockPredictionModel workflow.
    """
    _verify_admin_token_param(token)

    async def _generate() -> AsyncGenerator[dict, None]:
        yield _sse_event("starting", 0, "Starting model refresh and prediction pipeline…")
        await asyncio.sleep(0)

        db: Session = SessionLocal()
        try:
            from app.ml.stock_predictor import stock_predictor

            yield _sse_event("loading", 15, "Reloading ensemble model from disk…")
            await asyncio.sleep(0)
            await asyncio.to_thread(stock_predictor._load_enhanced_model)

            yield _sse_event("asx_sync", 30, "Syncing official ASX company list…")
            await asyncio.sleep(0)

            n_asx, asx_err = sync_official_asx_list(db, commit=False)
            if asx_err:
                yield _sse_event(
                    "asx_sync",
                    32,
                    f"ASX CSV sync failed ({asx_err}); continuing with existing list.",
                )
            else:
                yield _sse_event("asx_sync", 32, f"ASX list updated ({n_asx} companies).")

            yield _sse_event("loading", 35, "Refreshing Yahoo Finance prices for all tracked tickers…")
            await asyncio.sleep(0)
            await asyncio.to_thread(
                refresh_all_yahoo_prices,
                db,
                commit=False,
                stamp_admin_refresh=False,
            )

            yield _sse_event(
                "training",
                55,
                "Running predictions (Yahoo + sentiment pipeline) and rebuilding top picks…",
            )
            await asyncio.sleep(0)

            yield _sse_event("saving", 88, "Writing recommendations to the database…")
            await asyncio.sleep(0)
            n_pred, n_top = await asyncio.to_thread(
                regenerate_stock_tables, db, stock_predictor
            )

            row = db.query(AdminSettings).first()
            if row is None:
                row = AdminSettings()
                db.add(row)
            row.last_model_trained = datetime.utcnow()
            stamp_last_data_refresh(db)
            db.commit()

            yield _sse_event(
                "done",
                100,
                f"Complete — {n_pred} predictions, {n_top} top picks saved.",
            )

        except Exception as exc:
            logger.exception("Error during retrain stream")
            yield _sse_event("error", 0, f"Retrain failed: {exc}")
            db.rollback()
        finally:
            db.close()

    return EventSourceResponse(_generate())
