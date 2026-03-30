"""
Financial API endpoints — all routes require an authenticated user.
"""

import logging

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_active_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.financial import (
    AssetCreate,
    AssetResponse,
    AssetUpdate,
    DebtCreate,
    DebtResponse,
    DebtUpdate,
    ExpenseCreate,
    ExpenseResponse,
    ExpenseUpdate,
    IncomeCreate,
    IncomeResponse,
    IncomeUpdate,
)
from app.services import financial_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/items", summary="All financial items")
def get_all_items(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Return all financial line items (incomes, expenses, assets, debts) for the current user."""
    return financial_service.get_financial_items(db, current_user.id)


@router.get("/summary", summary="Financial summary")
def get_financial_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Return aggregated totals, asset breakdown, and line items for the current user."""
    return financial_service.get_financial_summary(db, current_user.id)


@router.post(
    "/income",
    response_model=IncomeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create income entry",
)
def create_income(
    payload: IncomeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return financial_service.create_income(db, current_user.id, payload)


@router.put(
    "/income/{income_id}",
    response_model=IncomeResponse,
    summary="Update income entry",
)
def update_income(
    income_id: int,
    payload: IncomeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return financial_service.update_income(db, current_user.id, income_id, payload)


@router.delete(
    "/income/{income_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete income entry",
)
def delete_income(
    income_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    financial_service.delete_income(db, current_user.id, income_id)


@router.post(
    "/expense",
    response_model=ExpenseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create expense entry",
)
def create_expense(
    payload: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return financial_service.create_expense(db, current_user.id, payload)


@router.put(
    "/expense/{expense_id}",
    response_model=ExpenseResponse,
    summary="Update expense entry",
)
def update_expense(
    expense_id: int,
    payload: ExpenseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return financial_service.update_expense(db, current_user.id, expense_id, payload)


@router.delete(
    "/expense/{expense_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete expense entry",
)
def delete_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    financial_service.delete_expense(db, current_user.id, expense_id)


@router.post(
    "/asset",
    response_model=AssetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create asset entry",
)
def create_asset(
    payload: AssetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return financial_service.create_asset(db, current_user.id, payload)


@router.put(
    "/asset/{asset_id}",
    response_model=AssetResponse,
    summary="Update asset entry",
)
def update_asset(
    asset_id: int,
    payload: AssetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return financial_service.update_asset(db, current_user.id, asset_id, payload)


@router.delete(
    "/asset/{asset_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete asset entry",
)
def delete_asset(
    asset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    financial_service.delete_asset(db, current_user.id, asset_id)


@router.post(
    "/debt",
    response_model=DebtResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create debt entry",
)
def create_debt(
    payload: DebtCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return financial_service.create_debt(db, current_user.id, payload)


@router.put(
    "/debt/{debt_id}",
    response_model=DebtResponse,
    summary="Update debt entry",
)
def update_debt(
    debt_id: int,
    payload: DebtUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return financial_service.update_debt(db, current_user.id, debt_id, payload)


@router.delete(
    "/debt/{debt_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete debt entry",
)
def delete_debt(
    debt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    financial_service.delete_debt(db, current_user.id, debt_id)
