"""
Database models package.

Import all ORM models here so that SQLAlchemy's metadata is fully populated
when Base.metadata.create_all() is called.
"""

from app.core.database import Base
from app.models.financial import Asset, Debt, Expense, Income
from app.models.stock import (
    AsxCsvSnapshot,
    AsxListedCompany,
    StockHolding,
    StockPrediction,
    StockQuote,
    StockTransaction,
    TopStockRecommendation,
)
from app.models.user import User

__all__ = [
    "Base",
    "User",
    "Income",
    "Expense",
    "Asset",
    "Debt",
    "StockHolding",
    "StockPrediction",
    "StockTransaction",
    "TopStockRecommendation",
    "StockQuote",
    "AsxCsvSnapshot",
    "AsxListedCompany",
]
