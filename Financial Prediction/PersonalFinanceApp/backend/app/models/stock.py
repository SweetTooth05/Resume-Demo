"""
SQLAlchemy models for stock portfolio management and predictions.
"""

import enum

from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from app.core.database import Base


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------
class PredictionSignal(str, enum.Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class TransactionType(str, enum.Enum):
    BUY = "BUY"
    SELL = "SELL"
    DIVIDEND = "DIVIDEND"


# ---------------------------------------------------------------------------
# ORM models
# ---------------------------------------------------------------------------
class StockHolding(Base):
    __tablename__ = "stock_holdings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    ticker = Column(String(10), nullable=False, index=True)
    shares = Column(Float, nullable=False)
    avg_price = Column(Float, nullable=False)
    current_price = Column(Float, nullable=True)
    last_updated = Column(DateTime(timezone=True), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class StockPrediction(Base):
    __tablename__ = "stock_predictions"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(10), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    prediction = Column(Enum(PredictionSignal), nullable=False)
    confidence = Column(Float, nullable=False)
    current_price = Column(Float, nullable=False)
    predicted_price = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class AsxCsvSnapshot(Base):
    """
    Latest raw official ASX listed-companies CSV (plus banner line) for audit/re-parse.

    Singleton row ``id=1`` updated on each successful sync.
    """

    __tablename__ = "asx_csv_snapshots"

    id = Column(Integer, primary_key=True)
    raw_csv = Column(Text, nullable=False)
    source_url = Column(String(512), nullable=False)
    asx_banner_line = Column(String(512), nullable=True)
    row_count = Column(Integer, nullable=False)
    synced_at = Column(DateTime(timezone=True), nullable=False)


class AsxListedCompany(Base):
    """
    Normalized rows from the official ASX CSV; ``yahoo_ticker`` is ``{ASX code}.AX``.
    """

    __tablename__ = "asx_listed_companies"

    yahoo_ticker = Column(String(16), primary_key=True, index=True)
    asx_code = Column(String(10), nullable=False, index=True)
    company_name = Column(String(512), nullable=False)
    gics_industry_group = Column(String(256), nullable=True)
    synced_at = Column(DateTime(timezone=True), nullable=False)


class StockQuote(Base):
    """
    Last traded price from Yahoo for any ASX symbol we refresh.

    Populated during admin/scheduled refresh so the DB tracks the full listed
    universe even when ``stock_predictions`` only covers a capped subset.
    """

    __tablename__ = "stock_quotes"

    ticker = Column(String(12), primary_key=True, index=True)
    name = Column(String(255), nullable=True)
    last_price = Column(Float, nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)


class TopStockRecommendation(Base):
    __tablename__ = "top_stock_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(10), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    prediction = Column(Enum(PredictionSignal), nullable=False)
    confidence = Column(Float, nullable=False)
    current_price = Column(Float, nullable=False)
    predicted_price = Column(Float, nullable=False)
    change = Column(Float, nullable=False, default=0.0)
    change_percent = Column(Float, nullable=False, default=0.0)
    rank = Column(Integer, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class StockTransaction(Base):
    __tablename__ = "stock_transactions"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(10), nullable=False, index=True)
    transaction_type = Column(Enum(TransactionType), nullable=False)
    shares = Column(Float, nullable=False)
    price_per_share = Column(Float, nullable=False)
    total_amount = Column(Float, nullable=False)
    fees = Column(Float, default=0.0)
    notes = Column(Text, nullable=True)
    holding_id = Column(Integer, ForeignKey("stock_holdings.id"), nullable=True)
    transaction_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
