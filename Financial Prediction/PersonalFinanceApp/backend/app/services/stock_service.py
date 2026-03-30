"""
Stock service layer.

Wraps the ML predictor and database queries for stock recommendations and
search.  Endpoints call this service; they never touch the predictor or ORM
directly.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.stock import StockPrediction, TopStockRecommendation
from app.ml.stock_predictor import stock_predictor
from app.services.recommendation_regen_service import order_predictions_for_top_picks

logger = logging.getLogger(__name__)

# Allowed characters in a ticker: letters, digits, and a single dot
_TICKER_RE = re.compile(r"^[A-Z0-9]{1,6}(\.[A-Z]{1,4})?$")

# Static fallback recommendations (used when DB is empty).
# Defined once here so they are never duplicated across endpoint files.
_FALLBACK_RECOMMENDATIONS: List[Dict[str, Any]] = [
    {"ticker": "BHP.AX", "name": "BHP Group Limited",                       "prediction": "BUY", "confidence": 0.92, "current_price": 48.75,  "predicted_price": 52.50,  "change": 3.25, "change_percent": 7.14},
    {"ticker": "CSL.AX", "name": "CSL Limited",                             "prediction": "BUY", "confidence": 0.89, "current_price": 245.80, "predicted_price": 260.00, "change": 5.20, "change_percent": 2.16},
    {"ticker": "WES.AX", "name": "Wesfarmers Limited",                      "prediction": "BUY", "confidence": 0.87, "current_price": 52.40,  "predicted_price": 56.00,  "change": 1.80, "change_percent": 3.55},
    {"ticker": "RIO.AX", "name": "Rio Tinto Limited",                       "prediction": "BUY", "confidence": 0.85, "current_price": 120.50, "predicted_price": 128.00, "change": 2.10, "change_percent": 4.20},
    {"ticker": "CBA.AX", "name": "Commonwealth Bank of Australia",          "prediction": "BUY", "confidence": 0.83, "current_price": 95.20,  "predicted_price": 98.50,  "change": 1.50, "change_percent": 1.65},
    {"ticker": "ANZ.AX", "name": "ANZ Banking Group",                       "prediction": "BUY", "confidence": 0.81, "current_price": 28.50,  "predicted_price": 29.85,  "change": 0.85, "change_percent": 3.08},
    {"ticker": "NAB.AX", "name": "National Australia Bank",                 "prediction": "BUY", "confidence": 0.79, "current_price": 32.80,  "predicted_price": 34.50,  "change": 0.95, "change_percent": 2.98},
    {"ticker": "WBC.AX", "name": "Westpac Banking Corporation",             "prediction": "BUY", "confidence": 0.77, "current_price": 24.20,  "predicted_price": 25.50,  "change": 0.65, "change_percent": 2.76},
    {"ticker": "MQG.AX", "name": "Macquarie Group Limited",                 "prediction": "BUY", "confidence": 0.75, "current_price": 185.30, "predicted_price": 195.00, "change": 3.20, "change_percent": 1.76},
    {"ticker": "TLS.AX", "name": "Telstra Group Limited",                   "prediction": "BUY", "confidence": 0.73, "current_price": 4.15,   "predicted_price": 4.35,   "change": 0.05, "change_percent": 1.19},
    {"ticker": "WOW.AX", "name": "Woolworths Group Limited",                "prediction": "BUY", "confidence": 0.71, "current_price": 35.80,  "predicted_price": 37.20,  "change": 0.90, "change_percent": 2.51},
    {"ticker": "COL.AX", "name": "Coles Group Limited",                     "prediction": "BUY", "confidence": 0.69, "current_price": 16.45,  "predicted_price": 17.10,  "change": 0.35, "change_percent": 2.13},
    {"ticker": "TCL.AX", "name": "Transurban Group",                        "prediction": "BUY", "confidence": 0.67, "current_price": 13.20,  "predicted_price": 13.85,  "change": 0.25, "change_percent": 1.89},
    {"ticker": "QBE.AX", "name": "QBE Insurance Group Limited",             "prediction": "BUY", "confidence": 0.65, "current_price": 15.80,  "predicted_price": 16.45,  "change": 0.30, "change_percent": 1.90},
    {"ticker": "IAG.AX", "name": "Insurance Australia Group Limited",       "prediction": "BUY", "confidence": 0.63, "current_price": 5.95,   "predicted_price": 6.20,   "change": 0.15, "change_percent": 2.52},
    {"ticker": "SGP.AX", "name": "Stockland Corporation Limited",           "prediction": "BUY", "confidence": 0.61, "current_price": 4.25,   "predicted_price": 4.45,   "change": 0.10, "change_percent": 2.35},
    {"ticker": "GMG.AX", "name": "Goodman Group",                           "prediction": "BUY", "confidence": 0.59, "current_price": 28.90,  "predicted_price": 30.15,  "change": 0.60, "change_percent": 2.08},
    {"ticker": "REA.AX", "name": "REA Group Limited",                       "prediction": "BUY", "confidence": 0.57, "current_price": 165.40, "predicted_price": 172.00, "change": 2.80, "change_percent": 1.69},
    {"ticker": "CAR.AX", "name": "Carsales.com Limited",                    "prediction": "BUY", "confidence": 0.55, "current_price": 32.15,  "predicted_price": 33.50,  "change": 0.65, "change_percent": 2.02},
    {"ticker": "NCM.AX", "name": "Newcrest Mining Limited",                 "prediction": "BUY", "confidence": 0.53, "current_price": 28.75,  "predicted_price": 30.20,  "change": 0.85, "change_percent": 2.96},
]


def _sanitise_ticker(raw: str) -> str:
    """Upper-case and strip a ticker string.  Raises 422 if invalid."""
    ticker = raw.strip().upper()
    if not _TICKER_RE.match(ticker):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid ticker symbol: '{raw}'",
        )
    return ticker


def get_prediction(ticker: str) -> Dict[str, Any]:
    """Return a prediction dict for the given ticker."""
    clean_ticker = _sanitise_ticker(ticker)
    prediction = stock_predictor.predict_stock(clean_ticker)
    if not prediction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No prediction available for {clean_ticker}",
        )
    return prediction


def serialize_prediction(p: StockPrediction) -> Dict[str, Any]:
    pred = p.prediction
    if hasattr(pred, "value"):
        pred = pred.value
    change = 0.0
    change_pct = 0.0
    if p.predicted_price and p.current_price and p.current_price > 0:
        change = round(p.predicted_price - p.current_price, 4)
        change_pct = round((change / p.current_price) * 100, 4)
    return {
        "ticker": p.ticker,
        "name": p.name,
        "prediction": pred,
        "confidence": p.confidence,
        "current_price": p.current_price,
        "predicted_price": p.predicted_price,
        "change": change,
        "change_percent": change_pct,
    }


def _rec_to_dict(r: TopStockRecommendation) -> Dict[str, Any]:
    pred = r.prediction
    if hasattr(pred, "value"):
        pred = pred.value
    return {
        "ticker": r.ticker,
        "name": r.name,
        "prediction": pred,
        "confidence": r.confidence,
        "current_price": r.current_price,
        "predicted_price": r.predicted_price,
        "change": r.change,
        "change_percent": r.change_percent,
    }


def get_recommendations(db: Session) -> List[Dict[str, Any]]:
    """
    Return top stock recommendations.

    Prefers ``top_stock_recommendations``; if that table was cleared but
    ``stock_predictions`` still has rows, derives a ranked list so the API does
    not silently fall back to static placeholder prices.
    """
    db_recs = (
        db.query(TopStockRecommendation)
        .order_by(TopStockRecommendation.rank)
        .limit(20)
        .all()
    )

    if db_recs:
        return [_rec_to_dict(r) for r in db_recs]

    preds = db.query(StockPrediction).all()
    if preds:
        ordered = order_predictions_for_top_picks(preds)
        return [
            {
                "ticker": p.ticker,
                "name": p.name,
                "prediction": p.prediction.value if hasattr(p.prediction, "value") else p.prediction,
                "confidence": p.confidence,
                "current_price": p.current_price,
                "predicted_price": p.predicted_price,
                "change": round(p.predicted_price - p.current_price, 4),
                "change_percent": round(
                    ((p.predicted_price - p.current_price) / p.current_price) * 100, 4
                )
                if p.current_price
                else 0.0,
            }
            for p in ordered
        ]

    return _FALLBACK_RECOMMENDATIONS


def search_stocks(query: str, db: Session, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Search for stocks by ticker or company name fragment.

    Queries the predictions table first; fills with fallback data that matches
    the query string.  The fallback lookup is keyword-based and deterministic.
    """
    if not query or not query.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Search query must not be empty",
        )

    clean_query = query.strip()
    query_upper = clean_query.upper()

    # 1. Database results
    db_results: List[Dict[str, Any]] = []
    db_preds = (
        db.query(StockPrediction)
        .filter(StockPrediction.ticker.ilike(f"%{clean_query}%"))
        .limit(limit)
        .all()
    )
    for pred in db_preds:
        change = 0.0
        change_pct = 0.0
        if pred.predicted_price and pred.current_price and pred.current_price > 0:
            change = pred.predicted_price - pred.current_price
            change_pct = change / pred.current_price * 100
        db_results.append({
            "ticker": pred.ticker,
            "name": pred.name,
            "prediction": pred.prediction,
            "confidence": pred.confidence,
            "current_price": pred.current_price,
            "predicted_price": pred.predicted_price,
            "change": round(change, 4),
            "change_percent": round(change_pct, 4),
        })

    # 2. Keyword-based fallback from static list
    keyword_map = {
        "BHP": ["BHP", "MINING"],
        "CSL": ["CSL", "HEALTH"],
        "CBA": ["CBA", "BANK", "FINANCIAL"],
        "ANZ": ["ANZ", "BANK", "FINANCIAL"],
        "NAB": ["NAB", "BANK", "FINANCIAL"],
        "WBC": ["WBC", "BANK", "FINANCIAL"],
        "TLS": ["TLS", "TELCO", "TELECOM"],
        "WOW": ["WOW", "RETAIL", "SUPERMARKET"],
        "COL": ["COL", "COLES", "RETAIL", "SUPERMARKET"],
    }

    seen_tickers = {r["ticker"] for r in db_results}
    fallback_results: List[Dict[str, Any]] = []
    for rec in _FALLBACK_RECOMMENDATIONS:
        if rec["ticker"] in seen_tickers:
            continue
        ticker_stem = rec["ticker"].split(".")[0]
        keywords = keyword_map.get(ticker_stem, [ticker_stem])
        if any(kw in query_upper for kw in keywords) or query_upper in rec["name"].upper():
            fallback_results.append(rec)
            seen_tickers.add(rec["ticker"])

    combined = db_results + fallback_results
    combined.sort(key=lambda x: x["confidence"], reverse=True)
    return combined[:limit]


def get_model_info() -> Dict[str, Any]:
    """Return metadata about the loaded ML model."""
    return stock_predictor.get_model_info()
