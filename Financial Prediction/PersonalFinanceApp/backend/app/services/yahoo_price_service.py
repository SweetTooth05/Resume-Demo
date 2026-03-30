"""
Fetch last prices from Yahoo Finance and persist them on stock-related rows.

Admin manual refresh and the background scheduler both use this module so
holdings and recommendation tables stay in sync.

ASX symbols and names come from ``asx_listed_companies`` (official CSV sync)
when available; otherwise from bundled ``ASXListedCompanies.csv``.
"""

from __future__ import annotations

import csv
import logging
import random
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.services.yahoo_client import reset_thread_local_session, yfinance_ticker
from app.models.admin import AdminSettings
from app.models.stock import AsxListedCompany, StockHolding, StockPrediction, StockQuote, TopStockRecommendation

logger = logging.getLogger(__name__)


def _asx_csv_paths() -> List[Path]:
    backend_root = Path(__file__).resolve().parent.parent.parent
    repo_root = backend_root.parent
    return [
        repo_root / "StockPredictionModel" / "ASXListedCompanies.csv",
        Path("/StockPredictionModel/ASXListedCompanies.csv"),
    ]


def _load_asx_ticker_names_from_file() -> Dict[str, str]:
    """Map Yahoo symbol (e.g. BHP.AX) -> company name from bundled CSV; {} if missing."""
    for csv_path in _asx_csv_paths():
        if not csv_path.is_file():
            continue
        out: Dict[str, str] = {}
        try:
            with csv_path.open(newline="", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    code = (row.get("ASX code") or row.get("asx code") or "").strip().upper()
                    if not code:
                        continue
                    name = (row.get("Company name") or row.get("company name") or "").strip()
                    sym = f"{code}.AX"
                    out[sym] = name or sym
            if out:
                logger.info("Loaded %s ASX symbols from file %s", len(out), csv_path)
                return out
        except OSError as exc:
            logger.warning("Could not read ASX CSV %s: %s", csv_path, exc)
    return {}


def load_asx_ticker_names(db: Session) -> Dict[str, str]:
    """
    Yahoo symbol -> company name from DB (official sync), else bundled CSV.
    """
    rows = (
        db.query(AsxListedCompany.yahoo_ticker, AsxListedCompany.company_name)
        .order_by(AsxListedCompany.yahoo_ticker)
        .all()
    )
    if rows:
        return {r[0]: r[1] for r in rows}
    return _load_asx_ticker_names_from_file()


def official_asx_yahoo_tickers_ordered(db: Session) -> List[str]:
    """All ``*.AX`` tickers from the official list table, else keys from file CSV."""
    rows = db.query(AsxListedCompany.yahoo_ticker).order_by(AsxListedCompany.yahoo_ticker).all()
    if rows:
        return [r[0] for r in rows]
    return sorted(_load_asx_ticker_names_from_file().keys())


@contextmanager
def _quiet_yfinance_logger(level: int = logging.CRITICAL):
    lg = logging.getLogger("yfinance")
    prev = lg.level
    lg.setLevel(level)
    try:
        yield
    finally:
        lg.setLevel(prev)


def yahoo_last_price(ticker: str) -> Optional[float]:
    """
    Spot price for *ticker* (e.g. ``BHP.AX``) via ``Ticker.history`` with
    ``raise_errors=False`` / ``actions=False`` (see yfinance docs).
    """
    backoff = 0.35
    last_err: Optional[Exception] = None
    for attempt in range(2):
        try:
            t = yfinance_ticker(ticker)
            with _quiet_yfinance_logger():
                hist = t.history(
                    period="5d",
                    interval="1d",
                    auto_adjust=True,
                    actions=False,
                    raise_errors=False,
                    timeout=20,
                )
            if hist is not None and not hist.empty and "Close" in hist.columns:
                last = float(hist["Close"].dropna().iloc[-1])
                if last > 0:
                    return last
        except Exception as exc:
            last_err = exc
            logger.debug("yahoo_last_price attempt %s for %s: %s", attempt + 1, ticker, exc)
            reset_thread_local_session()
            time.sleep(backoff + random.uniform(0, 0.12))
            backoff *= 1.7
    if last_err is not None:
        logger.debug("yahoo_last_price failed for %s: %s", ticker, last_err)
    return None


def distinct_stock_tickers(db: Session) -> List[str]:
    holding = {r[0] for r in db.query(StockHolding.ticker).distinct().all() if r[0]}
    rec = {r[0] for r in db.query(TopStockRecommendation.ticker).distinct().all() if r[0]}
    pred = {r[0] for r in db.query(StockPrediction.ticker).distinct().all() if r[0]}
    quotes = {r[0] for r in db.query(StockQuote.ticker).distinct().all() if r[0]}
    combined: Set[str] = set()
    order: List[str] = []
    for t in list(holding) + list(rec) + list(pred) + list(quotes):
        if t and t not in combined:
            combined.add(t)
            order.append(t)
    return order


def tickers_for_yahoo_refresh(db: Session) -> Tuple[List[str], Dict[str, str]]:
    """
    Tickers to hit on Yahoo, plus display names from the official DB list (or file).

    When ``settings.YAHOO_REFRESH_FULL_ASX`` is true, merges DB-derived symbols
    with every code from ``asx_listed_companies`` (or bundled CSV).
    """
    db_tickers = distinct_stock_tickers(db)
    if not settings.YAHOO_REFRESH_FULL_ASX:
        return db_tickers, load_asx_ticker_names(db) if db_tickers else {}

    asx_map = load_asx_ticker_names(db)
    asx_ordered = official_asx_yahoo_tickers_ordered(db)
    merged: List[str] = []
    seen: Set[str] = set()
    for t in db_tickers + asx_ordered:
        if t and t not in seen:
            seen.add(t)
            merged.append(t)
    return merged, asx_map


def upsert_stock_quote(
    db: Session, ticker: str, price: float, name: Optional[str] = None
) -> None:
    if price <= 0:
        return
    now = datetime.utcnow()
    row = db.get(StockQuote, ticker)
    if row is None:
        db.add(
            StockQuote(
                ticker=ticker,
                name=(name or ticker)[:255],
                last_price=price,
                updated_at=now,
            )
        )
    else:
        row.last_price = price
        row.updated_at = now
        if name:
            row.name = name[:255]


def ticker_last_data_at(db: Session, ticker: str) -> Optional[datetime]:
    """
    Latest timestamp we have for *ticker* across holdings, top recommendations, and predictions.

    Used by the admin refresh stream to show how stale each symbol is before hitting Yahoo.
    """
    candidates: List[datetime] = []
    for col in (StockHolding.updated_at, StockHolding.last_updated):
        v = db.query(func.max(col)).filter(StockHolding.ticker == ticker).scalar()
        if v is not None:
            candidates.append(v)
    v = (
        db.query(func.max(TopStockRecommendation.updated_at))
        .filter(TopStockRecommendation.ticker == ticker)
        .scalar()
    )
    if v is not None:
        candidates.append(v)
    v = (
        db.query(func.max(StockPrediction.updated_at))
        .filter(StockPrediction.ticker == ticker)
        .scalar()
    )
    if v is not None:
        candidates.append(v)
    v = (
        db.query(func.max(StockQuote.updated_at))
        .filter(StockQuote.ticker == ticker)
        .scalar()
    )
    if v is not None:
        candidates.append(v)
    return max(candidates) if candidates else None


def format_last_data_hint(ts: Optional[datetime]) -> str:
    if ts is None:
        return "no row timestamp"
    return ts.strftime("%Y-%m-%d %H:%M UTC")


def apply_price_for_ticker(db: Session, ticker: str, price: float) -> None:
    """Update ``current_price`` (and derived fields) everywhere *ticker* appears."""
    if price <= 0:
        return

    now = datetime.utcnow()
    db.query(StockHolding).filter(StockHolding.ticker == ticker).update(
        {"current_price": price, "updated_at": now, "last_updated": now},
        synchronize_session=False,
    )

    for row in db.query(TopStockRecommendation).filter(TopStockRecommendation.ticker == ticker).all():
        row.current_price = price
        row.updated_at = now
        if row.predicted_price and row.predicted_price > 0:
            row.change = round(row.predicted_price - price, 4)
            row.change_percent = round((row.change / price) * 100, 4) if price else 0.0

    for row in db.query(StockPrediction).filter(StockPrediction.ticker == ticker).all():
        row.current_price = price
        row.updated_at = now


def refresh_all_yahoo_prices(
    db: Session, *, commit: bool = True, stamp_admin_refresh: bool = True
) -> Tuple[int, int]:
    """
    Refresh every ticker from ``tickers_for_yahoo_refresh`` (DB + optional full ASX list).

    Returns ``(tickers_attempted, tickers_updated)``.
    """
    tickers, asx_names = tickers_for_yahoo_refresh(db)
    if not tickers:
        if stamp_admin_refresh:
            stamp_last_data_refresh(db)
        if commit:
            db.commit()
        return (0, 0)

    delay = max(0.0, settings.YAHOO_REQUEST_DELAY_SEC)
    updated = 0
    with _quiet_yfinance_logger():
        for i, ticker in enumerate(tickers):
            if delay > 0 and i > 0:
                time.sleep(delay)
            px = yahoo_last_price(ticker)
            if px is None:
                logger.debug("No Yahoo price for %s", ticker)
                continue
            apply_price_for_ticker(db, ticker, px)
            upsert_stock_quote(db, ticker, px, asx_names.get(ticker))
            updated += 1

    if stamp_admin_refresh:
        stamp_last_data_refresh(db)
    if commit:
        db.commit()
    else:
        db.flush()
    return (len(tickers), updated)


def stamp_last_data_refresh(db: Session) -> None:
    row = db.query(AdminSettings).first()
    if row is None:
        row = AdminSettings()
        db.add(row)
    row.last_data_refresh = datetime.utcnow()
