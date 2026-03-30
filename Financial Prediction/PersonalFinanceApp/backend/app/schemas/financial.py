"""
Pydantic schemas for income, expenses, assets, and debts.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.models.financial import (
    AssetCategory,
    DebtCategory,
    ExpenseCategory,
    IncomeCategory,
    RecurrenceFrequency,
)


# ---------------------------------------------------------------------------
# Income
# ---------------------------------------------------------------------------
class IncomeBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Income source name")
    amount: float = Field(
        ...,
        gt=0,
        description="Amount per recurrence period (e.g. per fortnight) or monthly if frequency is none/monthly",
    )
    category: IncomeCategory = Field(..., description="Income category")
    recurrence_frequency: RecurrenceFrequency = Field(
        RecurrenceFrequency.MONTHLY,
        description="How often the amount occurs; 'none' = enter as a monthly budget line",
    )
    recurrence_note: Optional[str] = Field(
        None,
        max_length=255,
        description="Optional note, e.g. paid every second Tuesday",
    )

    @field_validator("name")
    @classmethod
    def name_stripped(cls, v: str) -> str:
        return v.strip()

    @field_validator("recurrence_note")
    @classmethod
    def note_stripped(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        s = v.strip()
        return s or None


class IncomeCreate(IncomeBase):
    pass


class IncomeUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    amount: Optional[float] = Field(None, gt=0)
    category: Optional[IncomeCategory] = None
    recurrence_frequency: Optional[RecurrenceFrequency] = None
    recurrence_note: Optional[str] = Field(None, max_length=255)

    @field_validator("recurrence_note")
    @classmethod
    def note_stripped_u(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        s = v.strip()
        return s or None


class IncomeResponse(IncomeBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Expense
# ---------------------------------------------------------------------------
class ExpenseBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Expense name")
    amount: float = Field(..., gt=0, description="Amount per period (see recurrence)")
    category: ExpenseCategory = Field(..., description="Expense category")
    recurrence_frequency: RecurrenceFrequency = Field(
        RecurrenceFrequency.MONTHLY,
        description="How often this expense occurs",
    )
    recurrence_note: Optional[str] = Field(None, max_length=255)

    @field_validator("name")
    @classmethod
    def name_stripped(cls, v: str) -> str:
        return v.strip()

    @field_validator("recurrence_note")
    @classmethod
    def note_stripped_e(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        s = v.strip()
        return s or None


class ExpenseCreate(ExpenseBase):
    pass


class ExpenseUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    amount: Optional[float] = Field(None, gt=0)
    category: Optional[ExpenseCategory] = None
    recurrence_frequency: Optional[RecurrenceFrequency] = None
    recurrence_note: Optional[str] = Field(None, max_length=255)


class ExpenseResponse(ExpenseBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Asset
# ---------------------------------------------------------------------------
class AssetBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Asset name")
    amount: float = Field(..., gt=0, description="Asset value (must be positive)")
    category: AssetCategory = Field(..., description="Asset category")

    @field_validator("name")
    @classmethod
    def name_stripped(cls, v: str) -> str:
        return v.strip()


class AssetCreate(AssetBase):
    pass


class AssetUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    amount: Optional[float] = Field(None, gt=0)
    category: Optional[AssetCategory] = None


class AssetResponse(AssetBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Debt
# ---------------------------------------------------------------------------
class DebtBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Debt name")
    amount: float = Field(..., gt=0, description="Outstanding balance")
    category: DebtCategory = Field(..., description="Debt category")
    payment_amount: Optional[float] = Field(
        None,
        description="Recurring payment amount per payment_frequency (optional)",
    )
    payment_frequency: Optional[RecurrenceFrequency] = Field(
        None,
        description="How often you pay (weekly, monthly, etc.)",
    )
    payment_note: Optional[str] = Field(None, max_length=255)

    @field_validator("name")
    @classmethod
    def name_stripped(cls, v: str) -> str:
        return v.strip()

    @field_validator("payment_note")
    @classmethod
    def pay_note_stripped(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        s = v.strip()
        return s or None

    @field_validator("payment_amount")
    @classmethod
    def payment_positive(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v <= 0:
            raise ValueError("payment_amount must be positive when set")
        return v


class DebtCreate(DebtBase):
    pass


class DebtUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    amount: Optional[float] = Field(None, gt=0)
    category: Optional[DebtCategory] = None
    payment_amount: Optional[float] = None
    payment_frequency: Optional[RecurrenceFrequency] = None
    payment_note: Optional[str] = Field(None, max_length=255)


class DebtResponse(DebtBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
