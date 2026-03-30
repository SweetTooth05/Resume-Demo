"""
SQLAlchemy models for income, expenses, assets, and debts.
"""

import enum

from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.sql import func

from app.core.database import Base


# ---------------------------------------------------------------------------
# Category enumerations
# ---------------------------------------------------------------------------
class RecurrenceFrequency(str, enum.Enum):
    """How often the *amount* for income/expense occurs; NONE = monthly budget line."""

    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"
    FORTNIGHTLY = "fortnightly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


class IncomeCategory(str, enum.Enum):
    SALARY = "Salary"
    FREELANCE = "Freelance"
    INVESTMENT = "Investment"
    BUSINESS = "Business"
    OTHER = "Other"


class ExpenseCategory(str, enum.Enum):
    HOUSING = "Housing"
    TRANSPORTATION = "Transportation"
    FOOD = "Food"
    UTILITIES = "Utilities"
    ENTERTAINMENT = "Entertainment"
    HEALTHCARE = "Healthcare"
    OTHER = "Other"


class AssetCategory(str, enum.Enum):
    CASH = "Cash"
    INVESTMENTS = "Investments"
    REAL_ESTATE = "Real Estate"
    VEHICLES = "Vehicles"
    OTHER = "Other"


class DebtCategory(str, enum.Enum):
    CREDIT_CARD = "Credit Card"
    STUDENT_LOAN = "Student Loan"
    MORTGAGE = "Mortgage"
    CAR_LOAN = "Car Loan"
    PERSONAL_LOAN = "Personal Loan"
    OTHER = "Other"


# ---------------------------------------------------------------------------
# ORM models
# ---------------------------------------------------------------------------
class Income(Base):
    __tablename__ = "incomes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    amount = Column(Float, nullable=False)
    category = Column(Enum(IncomeCategory), nullable=False)
    recurrence_frequency = Column(
        Enum(
            RecurrenceFrequency,
            values_callable=lambda obj: [e.value for e in obj],
            native_enum=False,
            length=20,
        ),
        nullable=False,
        default=RecurrenceFrequency.MONTHLY,
    )
    recurrence_note = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    amount = Column(Float, nullable=False)
    category = Column(Enum(ExpenseCategory), nullable=False)
    recurrence_frequency = Column(
        Enum(
            RecurrenceFrequency,
            values_callable=lambda obj: [e.value for e in obj],
            native_enum=False,
            length=20,
        ),
        nullable=False,
        default=RecurrenceFrequency.MONTHLY,
    )
    recurrence_note = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    amount = Column(Float, nullable=False)
    category = Column(Enum(AssetCategory), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Debt(Base):
    __tablename__ = "debts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    amount = Column(Float, nullable=False)
    category = Column(Enum(DebtCategory), nullable=False)
    payment_amount = Column(Float, nullable=True)
    payment_frequency = Column(
        Enum(
            RecurrenceFrequency,
            values_callable=lambda obj: [e.value for e in obj],
            native_enum=False,
            length=20,
        ),
        nullable=True,
    )
    payment_note = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
