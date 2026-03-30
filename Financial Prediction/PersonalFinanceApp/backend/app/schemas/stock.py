"""
Pydantic schemas for stock holdings, predictions, and transactions.

Field names match the ORM model column names exactly so that
``Model(**schema.model_dump())`` works without manual key mapping.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.models.stock import PredictionSignal, TransactionType


# ---------------------------------------------------------------------------
# Stock Holding
# ---------------------------------------------------------------------------
class StockHoldingBase(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=10, description="Stock ticker symbol")
    shares: float = Field(..., gt=0, description="Number of shares owned")
    avg_price: float = Field(..., gt=0, description="Average cost per share")

    @field_validator("ticker")
    @classmethod
    def ticker_uppercase(cls, v: str) -> str:
        return v.strip().upper()


class StockHoldingCreate(StockHoldingBase):
    pass


class StockHoldingUpdate(BaseModel):
    shares: Optional[float] = Field(None, gt=0)
    avg_price: Optional[float] = Field(None, gt=0)
    current_price: Optional[float] = Field(None, gt=0)


class StockHoldingResponse(StockHoldingBase):
    id: int
    current_price: Optional[float] = None
    last_updated: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Stock Prediction
# ---------------------------------------------------------------------------
class StockPredictionBase(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=10, description="Stock ticker symbol")
    prediction: PredictionSignal = Field(..., description="Prediction signal")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score [0, 1]")
    current_price: float = Field(..., gt=0, description="Current stock price")
    predicted_price: float = Field(..., gt=0, description="Predicted stock price")

    @field_validator("ticker")
    @classmethod
    def ticker_uppercase(cls, v: str) -> str:
        return v.strip().upper()


class StockPredictionCreate(StockPredictionBase):
    pass


class StockPredictionUpdate(BaseModel):
    prediction: Optional[PredictionSignal] = None
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    current_price: Optional[float] = Field(None, gt=0)
    predicted_price: Optional[float] = Field(None, gt=0)


class StockPredictionResponse(StockPredictionBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Stock Transaction
# ---------------------------------------------------------------------------
class StockTransactionBase(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=10, description="Stock ticker symbol")
    transaction_type: TransactionType = Field(..., description="Type of transaction")
    shares: float = Field(..., gt=0, description="Number of shares")
    price_per_share: float = Field(..., gt=0, description="Price per share")
    total_amount: float = Field(..., gt=0, description="Total transaction amount")
    fees: float = Field(0.0, ge=0, description="Transaction fees")
    notes: Optional[str] = Field(None, max_length=1000, description="Transaction notes")

    @field_validator("ticker")
    @classmethod
    def ticker_uppercase(cls, v: str) -> str:
        return v.strip().upper()


class StockTransactionCreate(StockTransactionBase):
    pass


class StockTransactionUpdate(BaseModel):
    shares: Optional[float] = Field(None, gt=0)
    price_per_share: Optional[float] = Field(None, gt=0)
    total_amount: Optional[float] = Field(None, gt=0)
    fees: Optional[float] = Field(None, ge=0)
    notes: Optional[str] = Field(None, max_length=1000)


class StockTransactionResponse(StockTransactionBase):
    id: int
    holding_id: Optional[int] = None
    transaction_date: datetime
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
