"""
Portfolio API endpoints — holdings are per authenticated user.
"""

import logging

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_active_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.stock import StockHoldingCreate, StockHoldingResponse, StockHoldingUpdate
from app.services import portfolio_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", summary="Get all portfolio holdings")
def get_portfolio(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Return the current user's stock holdings."""
    holdings = portfolio_service.get_all_holdings(db, current_user.id)
    return {"holdings": holdings}


@router.post(
    "/stocks",
    response_model=StockHoldingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add stock to portfolio",
)
def add_stock(
    payload: StockHoldingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return portfolio_service.create_holding(db, current_user.id, payload)


@router.put(
    "/stocks/{holding_id}",
    response_model=StockHoldingResponse,
    summary="Update stock holding",
)
def update_stock(
    holding_id: int,
    payload: StockHoldingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return portfolio_service.update_holding(db, current_user.id, holding_id, payload)


@router.delete(
    "/stocks/{holding_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove stock from portfolio",
)
def remove_stock(
    holding_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    portfolio_service.delete_holding(db, current_user.id, holding_id)
