"""
Application configuration settings.

Loads from environment variables / .env file via pydantic-settings.
All secrets must be provided externally — never rely on insecure defaults
in production.
"""

import logging
import os
from typing import List, Optional
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    # ---------------------------------------------------------------------------
    # API
    # ---------------------------------------------------------------------------
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Personal Finance App"

    # ---------------------------------------------------------------------------
    # CORS
    # ---------------------------------------------------------------------------
    ALLOWED_HOSTS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://finance.kevinhe.pro",
    ]

    # ---------------------------------------------------------------------------
    # Admin portal
    # ---------------------------------------------------------------------------
    ADMIN_EMAIL: str = "kevilyfe@hotmail.com"
    ADMIN_PASSWORD_HASH: str = ""   # Set via env var after first setup
    ADMIN_TOTP_SECRET: str = ""     # Set via env var after first setup

    # ---------------------------------------------------------------------------
    # Database
    # ---------------------------------------------------------------------------
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/finance_app"

    # ---------------------------------------------------------------------------
    # JWT / Auth
    # ---------------------------------------------------------------------------
    SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Google Sign-In (OAuth 2.0 client ID from Google Cloud Console → Web application).
    # Used to verify the ID token from the frontend. Leave empty to disable /auth/google.
    GOOGLE_OAUTH_CLIENT_ID: str = ""

    # ---------------------------------------------------------------------------
    # External services
    # ---------------------------------------------------------------------------
    YAHOO_FINANCE_API_KEY: Optional[str] = None

    # ---------------------------------------------------------------------------
    # ML model
    # ---------------------------------------------------------------------------
    MODEL_PATH: str = (
        "../../FinanceApp/processed_finance_data/models/xgboost_stock_predictor.pkl"
    )

    # ---------------------------------------------------------------------------
    # Redis / background tasks
    # ---------------------------------------------------------------------------
    REDIS_URL: str = "redis://localhost:6379/0"
    ENABLE_BACKGROUND_TASKS: bool = True
    STOCK_UPDATE_INTERVAL: int = 24  # hours

    # Official ASX CSV (browser fetch; stored in DB on sync / startup).
    ASX_OFFICIAL_CSV_URL: str = "https://www.asx.com.au/asx/research/ASXListedCompanies.csv"

    # Yahoo refresh: merge all DB-synced ASX tickers (falls back to bundled CSV if table empty).
    YAHOO_REFRESH_FULL_ASX: bool = True
    # Cap ML retrain/predict loop (full ASX is ~2k; each ticker runs heavy pipeline).
    RETRAIN_MAX_TICKERS: int = 500
    # Gentle pacing when hitting Yahoo for many symbols (seconds; 0 to disable).
    YAHOO_REQUEST_DELAY_SEC: float = 0.08
    # Optional egress rotation for Yahoo (comma-separated http(s):// URLs). Synced to os.environ for yahoo_http.
    YAHOO_HTTP_PROXIES: str = ""
    # Single proxy URL (optional); also accepts standard HTTPS_PROXY in the environment.
    YAHOO_HTTPS_PROXY: str = ""

    # ---------------------------------------------------------------------------
    # Validators
    # ---------------------------------------------------------------------------
    @field_validator("SECRET_KEY")
    @classmethod
    def secret_key_must_be_set(cls, v: str) -> str:
        if v == "CHANGE_ME_IN_PRODUCTION":
            import os
            if os.getenv("ENVIRONMENT", "development").lower() == "production":
                raise ValueError(
                    "SECRET_KEY must be overridden via environment variable in production."
                )
        if len(v) < 32:
            logging.getLogger(__name__).warning(
                "SECRET_KEY is shorter than 32 characters — use a long random value."
            )
        return v

    @field_validator("ACCESS_TOKEN_EXPIRE_MINUTES")
    @classmethod
    def token_expiry_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("ACCESS_TOKEN_EXPIRE_MINUTES must be a positive integer.")
        return v


settings = Settings()

# yfinance helpers in StockPredictionModel read os.environ; mirror .env-loaded settings.
if settings.YAHOO_HTTP_PROXIES.strip():
    os.environ["YAHOO_HTTP_PROXIES"] = settings.YAHOO_HTTP_PROXIES.strip()
if settings.YAHOO_HTTPS_PROXY.strip():
    os.environ["YAHOO_HTTPS_PROXY"] = settings.YAHOO_HTTPS_PROXY.strip()
