"""
Rebuild ``stock_predictions`` and ``top_stock_recommendations`` from the ML predictor.

Used by the admin retrain SSE flow so dashboard users see updated picks after a run.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Tuple

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.stock import PredictionSignal, StockPrediction, TopStockRecommendation
from app.services.yahoo_price_service import distinct_stock_tickers, load_asx_ticker_names, official_asx_yahoo_tickers_ordered

logger = logging.getLogger(__name__)

# When the DB has no tickers yet, score a default ASX set (Yahoo symbols).
DEFAULT_ASX_TICKERS: List[str] = [
    "BHP.AX",
    "CSL.AX",
    "WES.AX",
    "RIO.AX",
    "CBA.AX",
    "ANZ.AX",
    "NAB.AX",
    "WBC.AX",
    "MQG.AX",
    "TLS.AX",
    "WOW.AX",
    "COL.AX",
    "TCL.AX",
    "QBE.AX",
    "IAG.AX",
    "SGP.AX",
    "NCM.AX",
    "WDS.AX",
    "STO.AX",
    "ORG.AX",
]

TOP_RECOMMENDATION_SLOTS = 20


def retrain_ticker_universe(db: Session) -> List[str]:
    tickers = list(distinct_stock_tickers(db))
    if settings.YAHOO_REFRESH_FULL_ASX:
        seen = set(tickers)
        for t in official_asx_yahoo_tickers_ordered(db):
            if t not in seen:
                seen.add(t)
                tickers.append(t)
    if not tickers:
        tickers = list(DEFAULT_ASX_TICKERS)
    cap = max(1, settings.RETRAIN_MAX_TICKERS)
    if len(tickers) > cap:
        logger.warning(
            "Capping retrain universe from %s to %s tickers (set RETRAIN_MAX_TICKERS to raise)",
            len(tickers),
            cap,
        )
        tickers = tickers[:cap]
    return tickers


def prediction_dict_to_signal(pred: Dict[str, Any]) -> PredictionSignal:
    raw = pred.get("prediction")
    rec = str(pred.get("recommendation") or "").upper()
    if isinstance(raw, str) and raw in PredictionSignal.__members__:
        return PredictionSignal[raw]
    if isinstance(raw, int):
        if raw == 1:
            return PredictionSignal.BUY
        if raw == 2:
            return PredictionSignal.SELL
        return PredictionSignal.HOLD
    if "BUY" in rec:
        return PredictionSignal.BUY
    if "SELL" in rec:
        return PredictionSignal.SELL
    return PredictionSignal.HOLD


def _company_name(ticker: str) -> str:
    return f"{ticker} Company"


def order_predictions_for_top_picks(preds: List[StockPrediction]) -> List[StockPrediction]:
    """
    Prefer BUY (highest confidence first), then HOLD, then SELL so UIs that
    highlight buys still see real model output instead of an empty list.
    """
    buys = sorted(
        [p for p in preds if p.prediction == PredictionSignal.BUY],
        key=lambda p: p.confidence,
        reverse=True,
    )
    holds = sorted(
        [p for p in preds if p.prediction == PredictionSignal.HOLD],
        key=lambda p: p.confidence,
        reverse=True,
    )
    sells = sorted(
        [p for p in preds if p.prediction == PredictionSignal.SELL],
        key=lambda p: p.confidence,
        reverse=True,
    )
    return (buys + holds + sells)[:TOP_RECOMMENDATION_SLOTS]


def regenerate_stock_tables(db: Session, predictor: Any) -> Tuple[int, int]:
    """
    Replace all prediction rows and top recommendations using *predictor*.

    Expects Yahoo prices to already be applied on *db* (no commit required before call).
    Does not commit — caller stamps admin metadata and commits.
    """
    tickers = retrain_ticker_universe(db)

    db.query(StockPrediction).delete(synchronize_session=False)
    db.query(TopStockRecommendation).delete(synchronize_session=False)

    now = datetime.utcnow()
    predictions: List[StockPrediction] = []
    asx_names = load_asx_ticker_names(db)
    top_candidates: List[TopStockRecommendation] = []

    for ticker in tickers:
        try:
            pred = predictor.predict_stock(ticker)
        except Exception as exc:
            logger.warning("predict_stock failed for %s: %s", ticker, exc)
            continue
        if not pred:
            continue

        sig = prediction_dict_to_signal(pred)
        cp = float(pred.get("current_price") or 0.0)
        pp = float(pred.get("predicted_price") or cp)
        if cp <= 0:
            logger.warning("Skipping %s: no current price", ticker)
            continue

        conf = float(pred.get("confidence") or 0.0)

        sp = StockPrediction(
            ticker=ticker,
            name=asx_names.get(ticker, ticker),
            prediction=sig,
            confidence=conf,
            current_price=cp,
            predicted_price=pp,
            created_at=now,
            updated_at=now,
        )
        predictions.append(sp)

    ordered = order_predictions_for_top_picks(predictions)
    for i, sp in enumerate(ordered):
        top_candidates.append(
            TopStockRecommendation(
                ticker=sp.ticker,
                name=sp.name,
                prediction=sp.prediction,
                confidence=sp.confidence,
                current_price=sp.current_price,
                predicted_price=sp.predicted_price,
                change=round(sp.predicted_price - sp.current_price, 4),
                change_percent=round(
                    ((sp.predicted_price - sp.current_price) / sp.current_price) * 100, 4
                )
                if sp.current_price
                else 0.0,
                rank=i + 1,
                created_at=now,
                updated_at=now,
            )
        )

    db.add_all(predictions)
    db.add_all(top_candidates)
    db.flush()

    return len(predictions), len(top_candidates)
