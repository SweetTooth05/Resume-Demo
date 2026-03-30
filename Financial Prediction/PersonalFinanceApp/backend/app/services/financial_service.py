"""
Financial service layer — all calculations scoped per authenticated user.
"""

from __future__ import annotations

import calendar
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from dateutil.relativedelta import relativedelta
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.recurrence import amount_to_monthly
from app.models.financial import Asset, AssetCategory, Debt, Expense, Income, RecurrenceFrequency
from app.models.stock import StockHolding
from app.schemas.financial import (
    AssetCreate,
    AssetUpdate,
    DebtCreate,
    DebtUpdate,
    ExpenseCreate,
    ExpenseUpdate,
    IncomeCreate,
    IncomeUpdate,
)
from app.services import portfolio_service

logger = logging.getLogger(__name__)


def _raise_not_found(entity: str, entity_id: int) -> None:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"{entity} with id {entity_id} not found",
    )


def _serialize_income(i: Income) -> Dict[str, Any]:
    return {
        "id": i.id,
        "name": i.name,
        "amount": i.amount,
        "category": str(i.category),
        "recurrence_frequency": i.recurrence_frequency.value
        if hasattr(i.recurrence_frequency, "value")
        else str(i.recurrence_frequency),
        "recurrence_note": i.recurrence_note,
    }


def _serialize_expense(e: Expense) -> Dict[str, Any]:
    return {
        "id": e.id,
        "name": e.name,
        "amount": e.amount,
        "category": str(e.category),
        "recurrence_frequency": e.recurrence_frequency.value
        if hasattr(e.recurrence_frequency, "value")
        else str(e.recurrence_frequency),
        "recurrence_note": e.recurrence_note,
    }


def _serialize_debt(d: Debt) -> Dict[str, Any]:
    pf = d.payment_frequency
    return {
        "id": d.id,
        "name": d.name,
        "amount": d.amount,
        "category": str(d.category),
        "payment_amount": d.payment_amount,
        "payment_frequency": pf.value if pf is not None and hasattr(pf, "value") else (str(pf) if pf else None),
        "payment_note": d.payment_note,
    }


def get_financial_summary(db: Session, user_id: int) -> Dict[str, Any]:
    incomes = db.query(Income).filter(Income.user_id == user_id).all()
    expenses = db.query(Expense).filter(Expense.user_id == user_id).all()
    assets = db.query(Asset).filter(Asset.user_id == user_id).all()
    debts = db.query(Debt).filter(Debt.user_id == user_id).all()

    total_income_monthly = sum(
        amount_to_monthly(i.amount, i.recurrence_frequency) for i in incomes
    )
    total_expenses_monthly = sum(
        amount_to_monthly(e.amount, e.recurrence_frequency) for e in expenses
    )
    monthly_debt_payments = 0.0
    for d in debts:
        if d.payment_amount and d.payment_amount > 0:
            pf = d.payment_frequency or RecurrenceFrequency.MONTHLY
            monthly_debt_payments += amount_to_monthly(d.payment_amount, pf)

    total_property_assets = sum(a.amount for a in assets)
    total_debts_balance = sum(d.amount for d in debts)
    stocks_value = portfolio_service.total_market_value(db, user_id)

    cash_on_hand = sum(a.amount for a in assets if a.category == AssetCategory.CASH)
    real_estate = sum(a.amount for a in assets if a.category == AssetCategory.REAL_ESTATE)
    vehicles = sum(a.amount for a in assets if a.category == AssetCategory.VEHICLES)
    investments_book = sum(a.amount for a in assets if a.category == AssetCategory.INVESTMENTS)
    other_assets = sum(a.amount for a in assets if a.category == AssetCategory.OTHER)

    total_assets_combined = total_property_assets + stocks_value
    net_worth = total_assets_combined - total_debts_balance
    monthly_outflows = total_expenses_monthly + monthly_debt_payments
    monthly_savings = total_income_monthly - monthly_outflows

    expense_by_category: Dict[str, float] = {}
    for expense in expenses:
        key = str(expense.category)
        expense_by_category[key] = expense_by_category.get(key, 0.0) + amount_to_monthly(
            expense.amount, expense.recurrence_frequency
        )

    return {
        "summary": {
            "total_income": round(total_income_monthly, 2),
            "total_expenses": round(total_expenses_monthly, 2),
            "total_assets": round(total_assets_combined, 2),
            "total_property_assets": round(total_property_assets, 2),
            "total_stocks_value": round(stocks_value, 2),
            "total_debts": round(total_debts_balance, 2),
            "monthly_debt_payments": round(monthly_debt_payments, 2),
            "net_worth": round(net_worth, 2),
            "monthly_savings": round(monthly_savings, 2),
            "cash_on_hand": round(cash_on_hand, 2),
        },
        "asset_breakdown": {
            "cash": round(cash_on_hand, 2),
            "stocks": round(stocks_value, 2),
            "real_estate": round(real_estate, 2),
            "vehicles": round(vehicles, 2),
            "investments": round(investments_book, 2),
            "other": round(other_assets, 2),
        },
        "expense_breakdown": [
            {"name": cat, "value": round(amt, 2)} for cat, amt in expense_by_category.items()
        ],
        "items": {
            "incomes": [_serialize_income(i) for i in incomes],
            "expenses": [_serialize_expense(e) for e in expenses],
            "assets": [
                {"id": a.id, "name": a.name, "amount": a.amount, "category": str(a.category)}
                for a in assets
            ],
            "debts": [_serialize_debt(d) for d in debts],
        },
    }


def get_financial_items(db: Session, user_id: int) -> Dict[str, Any]:
    """Return all financial line items for the given user without computing aggregates."""
    incomes = db.query(Income).filter(Income.user_id == user_id).all()
    expenses = db.query(Expense).filter(Expense.user_id == user_id).all()
    assets = db.query(Asset).filter(Asset.user_id == user_id).all()
    debts = db.query(Debt).filter(Debt.user_id == user_id).all()
    return {
        "items": {
            "incomes": [_serialize_income(i) for i in incomes],
            "expenses": [_serialize_expense(e) for e in expenses],
            "assets": [
                {"id": a.id, "name": a.name, "amount": a.amount, "category": str(a.category)}
                for a in assets
            ],
            "debts": [_serialize_debt(d) for d in debts],
        }
    }


def compute_financial_health_score(db: Session, user_id: int) -> Dict[str, Any]:
    summary = get_financial_summary(db, user_id)["summary"]
    total_income = summary["total_income"]
    if total_income <= 0:
        return {"score": None}

    total_expenses = summary["total_expenses"] + summary["monthly_debt_payments"]
    total_assets = summary["total_assets"]
    total_debts = summary["total_debts"]

    savings_rate = (total_income - total_expenses) / total_income * 100
    debt_to_income = total_debts / total_income if total_income else 0
    asset_to_debt = total_assets / total_debts if total_debts > 0 else 3.0

    score = 0
    if savings_rate >= 20:
        score = 40
    elif savings_rate >= 15:
        score = 35
    elif savings_rate >= 10:
        score = 30
    elif savings_rate >= 5:
        score = 20
    else:
        score = 10

    if debt_to_income <= 0.3:
        score += 30
    elif debt_to_income <= 0.5:
        score += 25
    elif debt_to_income <= 0.7:
        score += 20
    elif debt_to_income <= 1.0:
        score += 15
    else:
        score += 10

    if asset_to_debt >= 3:
        score += 30
    elif asset_to_debt >= 2:
        score += 25
    elif asset_to_debt >= 1.5:
        score += 20
    elif asset_to_debt >= 1:
        score += 15
    else:
        score += 10

    return {"score": min(100, max(0, score))}


def get_expense_breakdown(db: Session, user_id: int) -> Dict[str, Any]:
    expenses = db.query(Expense).filter(Expense.user_id == user_id).all()
    breakdown: Dict[str, float] = {}
    for expense in expenses:
        key = str(expense.category)
        breakdown[key] = breakdown.get(key, 0.0) + amount_to_monthly(
            expense.amount, expense.recurrence_frequency
        )
    return {
        "breakdown": [
            {"category": cat, "amount": round(amt, 2)} for cat, amt in breakdown.items()
        ]
    }


def _dt_utc(dt: Any) -> Optional[datetime]:
    if dt is None:
        return None
    if getattr(dt, "tzinfo", None) is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def get_net_worth_history(db: Session, user_id: int, months: int = 12) -> Dict[str, Any]:
    """
    Approximate month-end net worth:

    * Book **assets** and **debts** (cash, property, loans, mortgages, etc.) count toward
      a month only after their ``created_at`` (when the row was added).
    * **Portfolio** value uses *today's* prices and is included from the month of the
      earliest holding onward (we do not store historical marks).
    """
    assets = db.query(Asset).filter(Asset.user_id == user_id).all()
    debts = db.query(Debt).filter(Debt.user_id == user_id).all()
    holdings = db.query(StockHolding).filter(StockHolding.user_id == user_id).all()

    stocks_now = portfolio_service.total_market_value(db, user_id)
    first_holding_utc: Optional[datetime] = None
    if holdings:
        times = [_dt_utc(h.created_at) for h in holdings if h.created_at]
        if times:
            first_holding_utc = min(t for t in times if t is not None)

    now = datetime.now(timezone.utc)
    history: List[Dict[str, Any]] = []

    for i in range(months):
        anchor = now - relativedelta(months=(months - 1 - i))
        y, m = anchor.year, anchor.month
        last_day = calendar.monthrange(y, m)[1]
        month_end = datetime(y, m, last_day, 23, 59, 59, tzinfo=timezone.utc)

        assets_total = 0.0
        for a in assets:
            t = _dt_utc(a.created_at)
            if t and t <= month_end:
                assets_total += float(a.amount or 0)

        debts_total = 0.0
        for d in debts:
            t = _dt_utc(d.created_at)
            if t and t <= month_end:
                debts_total += float(d.amount or 0)

        stock_component = 0.0
        if first_holding_utc is not None and month_end >= first_holding_utc:
            stock_component = stocks_now

        net = round(assets_total + stock_component - debts_total, 2)
        history.append({"month": anchor.strftime("%b %Y"), "netWorth": net})

    return {"history": history}


# ---------------------------------------------------------------------------
# Income CRUD
# ---------------------------------------------------------------------------
def create_income(db: Session, user_id: int, payload: IncomeCreate) -> Income:
    data = payload.model_dump()
    obj = Income(**data, user_id=user_id)
    db.add(obj)
    db.flush()
    db.refresh(obj)
    return obj


def update_income(db: Session, user_id: int, income_id: int, payload: IncomeUpdate) -> Income:
    obj = (
        db.query(Income)
        .filter(Income.id == income_id, Income.user_id == user_id)
        .first()
    )
    if obj is None:
        _raise_not_found("Income", income_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)
    db.flush()
    db.refresh(obj)
    return obj


def delete_income(db: Session, user_id: int, income_id: int) -> None:
    obj = (
        db.query(Income)
        .filter(Income.id == income_id, Income.user_id == user_id)
        .first()
    )
    if obj is None:
        _raise_not_found("Income", income_id)
    db.delete(obj)
    db.flush()


# ---------------------------------------------------------------------------
# Expense CRUD
# ---------------------------------------------------------------------------
def create_expense(db: Session, user_id: int, payload: ExpenseCreate) -> Expense:
    obj = Expense(**payload.model_dump(), user_id=user_id)
    db.add(obj)
    db.flush()
    db.refresh(obj)
    return obj


def update_expense(db: Session, user_id: int, expense_id: int, payload: ExpenseUpdate) -> Expense:
    obj = (
        db.query(Expense)
        .filter(Expense.id == expense_id, Expense.user_id == user_id)
        .first()
    )
    if obj is None:
        _raise_not_found("Expense", expense_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)
    db.flush()
    db.refresh(obj)
    return obj


def delete_expense(db: Session, user_id: int, expense_id: int) -> None:
    obj = (
        db.query(Expense)
        .filter(Expense.id == expense_id, Expense.user_id == user_id)
        .first()
    )
    if obj is None:
        _raise_not_found("Expense", expense_id)
    db.delete(obj)
    db.flush()


# ---------------------------------------------------------------------------
# Asset CRUD
# ---------------------------------------------------------------------------
def create_asset(db: Session, user_id: int, payload: AssetCreate) -> Asset:
    obj = Asset(**payload.model_dump(), user_id=user_id)
    db.add(obj)
    db.flush()
    db.refresh(obj)
    return obj


def update_asset(db: Session, user_id: int, asset_id: int, payload: AssetUpdate) -> Asset:
    obj = (
        db.query(Asset)
        .filter(Asset.id == asset_id, Asset.user_id == user_id)
        .first()
    )
    if obj is None:
        _raise_not_found("Asset", asset_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)
    db.flush()
    db.refresh(obj)
    return obj


def delete_asset(db: Session, user_id: int, asset_id: int) -> None:
    obj = (
        db.query(Asset)
        .filter(Asset.id == asset_id, Asset.user_id == user_id)
        .first()
    )
    if obj is None:
        _raise_not_found("Asset", asset_id)
    db.delete(obj)
    db.flush()


# ---------------------------------------------------------------------------
# Debt CRUD
# ---------------------------------------------------------------------------
def create_debt(db: Session, user_id: int, payload: DebtCreate) -> Debt:
    obj = Debt(**payload.model_dump(), user_id=user_id)
    db.add(obj)
    db.flush()
    db.refresh(obj)
    return obj


def update_debt(db: Session, user_id: int, debt_id: int, payload: DebtUpdate) -> Debt:
    obj = (
        db.query(Debt).filter(Debt.id == debt_id, Debt.user_id == user_id).first()
    )
    if obj is None:
        _raise_not_found("Debt", debt_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)
    db.flush()
    db.refresh(obj)
    return obj


def delete_debt(db: Session, user_id: int, debt_id: int) -> None:
    obj = (
        db.query(Debt).filter(Debt.id == debt_id, Debt.user_id == user_id).first()
    )
    if obj is None:
        _raise_not_found("Debt", debt_id)
    db.delete(obj)
    db.flush()
