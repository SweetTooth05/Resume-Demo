"""
Stock prediction API endpoints.

These are thin HTTP adapters.  Prediction logic and database queries live in
app.services.stock_service.
"""

import logging

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.auth import get_current_active_user
from app.core.database import get_db
from app.models.stock import StockHolding, StockPrediction
from app.models.user import User
from app.services import stock_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/predict/{ticker}", summary="Predict a single stock")
def predict_stock(ticker: str, db: Session = Depends(get_db)):
    """
    Return an ML prediction for the given ticker symbol.

    The ticker is validated and normalised (e.g. ``bhp`` -> ``BHP.AX``).
    Returns HTTP 404 when no prediction is available and HTTP 422 when the
    ticker format is invalid.
    """
    return stock_service.get_prediction(ticker)


@router.get("/recommendations", summary="Top stock recommendations")
def get_stock_recommendations(db: Session = Depends(get_db)):
    """
    Return up to 20 BUY recommendations sorted by confidence.

    Live database records are preferred; static fallback data is returned when
    the ``top_stock_recommendations`` table is empty.
    """
    recommendations = stock_service.get_recommendations(db)
    return {"recommendations": recommendations}


@router.get("/search/{query}", summary="Search stocks by ticker or name")
def search_stocks(
    query: str,
    db: Session = Depends(get_db),
    limit: int = Query(10, ge=1, le=50, description="Maximum results to return"),
):
    """
    Search for stocks matching the query string.

    The search covers ticker symbols and company names.  Results are sorted by
    confidence score descending.
    """
    results = stock_service.search_stocks(query, db, limit=limit)
    return {"predictions": results}


@router.get("/model/info", summary="ML model metadata")
def get_model_info():
    """Return information about the currently loaded stock prediction model."""
    return stock_service.get_model_info()


@router.get("/portfolio/predictions", summary="Predictions for portfolio holdings")
def get_portfolio_predictions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Return ML predictions for every stock the current user holds."""
    tickers = [
        h.ticker
        for h in db.query(StockHolding).filter_by(user_id=current_user.id).all()
    ]
    if not tickers:
        return {"predictions": []}
    preds = db.query(StockPrediction).filter(StockPrediction.ticker.in_(tickers)).all()
    return {"predictions": [stock_service.serialize_prediction(p) for p in preds]}
