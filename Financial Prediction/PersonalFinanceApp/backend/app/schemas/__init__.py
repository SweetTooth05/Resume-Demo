"""
Pydantic schemas for API request/response validation.
"""

# User schemas
from app.schemas.user import Token, UserBase, UserCreate, UserLogin, UserResponse, UserUpdate

# Financial schemas
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

# Stock schemas
from app.schemas.stock import (
    StockHoldingCreate,
    StockHoldingResponse,
    StockHoldingUpdate,
    StockPredictionCreate,
    StockPredictionResponse,
    StockPredictionUpdate,
    StockTransactionCreate,
    StockTransactionResponse,
    StockTransactionUpdate,
)

# Dashboard schemas
from app.schemas.dashboard import DashboardResponse, FinancialSummary, StockRecommendation

__all__ = [
    # User
    "UserBase", "UserCreate", "UserUpdate", "UserLogin", "Token", "UserResponse",
    # Financial
    "IncomeCreate", "IncomeUpdate", "IncomeResponse",
    "ExpenseCreate", "ExpenseUpdate", "ExpenseResponse",
    "AssetCreate", "AssetUpdate", "AssetResponse",
    "DebtCreate", "DebtUpdate", "DebtResponse",
    # Stock
    "StockHoldingCreate", "StockHoldingUpdate", "StockHoldingResponse",
    "StockPredictionCreate", "StockPredictionUpdate", "StockPredictionResponse",
    "StockTransactionCreate", "StockTransactionUpdate", "StockTransactionResponse",
    # Dashboard
    "FinancialSummary", "StockRecommendation", "DashboardResponse",
]
