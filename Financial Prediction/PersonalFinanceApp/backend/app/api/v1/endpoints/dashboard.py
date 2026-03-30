"""
Dashboard API endpoints — scoped to the authenticated user.
"""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import get_current_active_user
from app.core.database import get_db
from app.models.user import User
from app.services import financial_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", summary="Dashboard overview")
def get_dashboard_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Return totals, asset breakdown, and line items for the main dashboard."""
    summary_data = financial_service.get_financial_summary(db, current_user.id)
    totals = summary_data["summary"]
    return {
        "totals": {
            "income": totals["total_income"],
            "expenses": totals["total_expenses"],
            "assets": totals["total_assets"],
            "propertyAssets": totals["total_property_assets"],
            "stocksValue": totals["total_stocks_value"],
            "debts": totals["total_debts"],
            "netWorth": totals["net_worth"],
            "monthlySavings": totals["monthly_savings"],
            "monthlyDebtPayments": totals["monthly_debt_payments"],
            "cashOnHand": totals["cash_on_hand"],
        },
        "asset_breakdown": summary_data["asset_breakdown"],
        "expense_breakdown": summary_data["expense_breakdown"],
        "items": summary_data["items"],
    }


@router.get("/financial-health", summary="Financial health score")
def get_financial_health(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Return a 0–100 composite financial health score."""
    return financial_service.compute_financial_health_score(db, current_user.id)


@router.get("/expense-breakdown", summary="Expense breakdown by category")
def get_expense_breakdown(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Return expenses grouped by category (monthly equivalents)."""
    return financial_service.get_expense_breakdown(db, current_user.id)


@router.get("/net-worth-history", summary="Net worth history (last 12 months)")
def get_net_worth_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Month-end net worth from book assets & debts (by row ``created_at``) plus portfolio
    value at today's prices from the first holding month onward.
    """
    return financial_service.get_net_worth_history(db, current_user.id, months=12)
