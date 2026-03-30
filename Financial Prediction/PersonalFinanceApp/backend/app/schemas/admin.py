"""
Pydantic schemas for the admin portal endpoints.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class AdminLoginRequest(BaseModel):
    """Request body for the admin login endpoint."""

    email: EmailStr
    password: str
    totp_code: str


class AdminSetupVerifyRequest(BaseModel):
    """Request body for completing the initial admin setup."""

    password: str
    totp_code: str


class AdminToken(BaseModel):
    """Response schema for a successful admin authentication."""

    access_token: str
    token_type: str = "bearer"


class AdminMetrics(BaseModel):
    """Aggregated platform metrics returned by the admin metrics endpoint."""

    total_users: int
    total_incomes: int
    total_expenses: int
    total_assets: int
    total_debts: int
    total_holdings: int
    db_size_mb: float
    last_data_refresh: Optional[datetime]
    last_model_trained: Optional[datetime]
