"""
Dashboard schemas for API responses
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class FinancialSummary(BaseModel):
    """Financial summary for dashboard"""
    total_income: float = 0.0
    total_expenses: float = 0.0
    total_assets: float = 0.0
    total_debts: float = 0.0
    net_worth: float = 0.0
    monthly_savings: float = 0.0


class StockRecommendation(BaseModel):
    """Stock recommendation for dashboard"""
    ticker: str
    name: str
    current_price: float
    prediction: str
    confidence: float
    recommendation: str


class DashboardResponse(BaseModel):
    """Dashboard response model"""
    model_config = ConfigDict(from_attributes=True)

    financial_summary: FinancialSummary
    top_stock_recommendations: List[StockRecommendation] = []
    recent_transactions: List[Dict[str, Any]] = []
    last_updated: datetime = Field(default_factory=datetime.utcnow)