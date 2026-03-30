"""
Portfolio service layer.

All stock-holding business logic is centralised here.
Endpoints remain thin HTTP adapters that call into this service.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.stock import StockHolding
from app.schemas.stock import StockHoldingCreate, StockHoldingUpdate

logger = logging.getLogger(__name__)


def _raise_not_found(holding_id: int) -> None:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Stock holding with id {holding_id} not found",
    )


def _format_holding(holding: StockHolding, current_price: Optional[float] = None) -> Dict[str, Any]:
    """
    Serialise a StockHolding row into the API response shape.

    If *current_price* is not available we fall back to the stored value or
    the average purchase price — never to a ``hash()``-based mock.
    """
    price = current_price or holding.current_price or holding.avg_price
    change = price - holding.avg_price
    change_pct = (change / holding.avg_price * 100) if holding.avg_price else 0.0

    return {
        "id": holding.id,
        "ticker": holding.ticker,
        "shares": holding.shares,
        "avg_price": holding.avg_price,
        "current_price": round(price, 4),
        "change": round(change, 4),
        "change_percent": round(change_pct, 4),
    }


def total_market_value(db: Session, user_id: int) -> float:
    """Sum of shares × current (or avg) price for the user's holdings."""
    holdings = db.query(StockHolding).filter(StockHolding.user_id == user_id).all()
    total = 0.0
    for h in holdings:
        price = h.current_price or h.avg_price
        total += float(h.shares) * float(price)
    return total


def get_all_holdings(db: Session, user_id: int) -> List[Dict[str, Any]]:
    holdings = (
        db.query(StockHolding).filter(StockHolding.user_id == user_id).all()
    )
    return [_format_holding(h) for h in holdings]


def get_holding(db: Session, user_id: int, holding_id: int) -> Dict[str, Any]:
    holding = (
        db.query(StockHolding)
        .filter(StockHolding.id == holding_id, StockHolding.user_id == user_id)
        .first()
    )
    if holding is None:
        _raise_not_found(holding_id)
    return _format_holding(holding)


def create_holding(db: Session, user_id: int, payload: StockHoldingCreate) -> StockHolding:
    obj = StockHolding(**payload.model_dump(), user_id=user_id)
    db.add(obj)
    db.flush()
    db.refresh(obj)
    return obj


def update_holding(
    db: Session,
    user_id: int,
    holding_id: int,
    payload: StockHoldingUpdate,
) -> StockHolding:
    obj = (
        db.query(StockHolding)
        .filter(StockHolding.id == holding_id, StockHolding.user_id == user_id)
        .first()
    )
    if obj is None:
        _raise_not_found(holding_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)
    db.flush()
    db.refresh(obj)
    return obj


def delete_holding(db: Session, user_id: int, holding_id: int) -> None:
    obj = (
        db.query(StockHolding)
        .filter(StockHolding.id == holding_id, StockHolding.user_id == user_id)
        .first()
    )
    if obj is None:
        _raise_not_found(holding_id)
    db.delete(obj)
    db.flush()
