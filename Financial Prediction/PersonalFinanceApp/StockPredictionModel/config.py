"""
Configuration settings for Stock Prediction Model
"""

import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "processed_finance_data"
RAW_DATA_DIR = DATA_DIR / "raw_data"
PROCESSED_DATA_DIR = DATA_DIR / "processed_data"
MODELS_DIR = DATA_DIR / "models"
SCALERS_DIR = DATA_DIR / "scalers"
FEATURES_DIR = DATA_DIR / "features"

# ASX Data Sources
ASX_DATA_SOURCES = {
    "primary": "https://www.asxlistedcompanies.com/",
    "csv_download": "https://www.asxlistedcompanies.com/download",  # Updated link
    "backup": "https://www.asx.com.au/asx/research/listedCompanies.do"
}

# Model Configuration
MODEL_CONFIG = {
    "model_type": "xgboost",
    "random_state": 42,
    "test_size": 0.2,
    "validation_size": 0.1,
    "n_jobs": -1,
    "early_stopping_rounds": 50,
    "eval_metric": "logloss"
}

# Feature Engineering
FEATURE_CONFIG = {
    "technical_indicators": [
        "RSI", "MACD", "Bollinger_Bands", "Moving_Averages", 
        "Stochastic", "Williams_R", "ATR", "CCI", "MFI", "PSAR"
    ],
    "price_features": ["Returns", "Log_Returns", "Volatility", "Momentum"],
    "volume_features": ["Volume_MA", "Volume_Ratio", "OBV"],
    "time_features": ["DayOfWeek", "Month", "Quarter", "Year"]
}

# Sentiment Analysis
SENTIMENT_CONFIG = {
    "sources": {
        "news": [
            "https://www.afr.com/",
            "https://www.smh.com.au/business",
            "https://www.theaustralian.com.au/business",
            "https://www.news.com.au/finance"
        ],
        "reddit": [
            "https://www.reddit.com/r/ausfinance/",
            "https://www.reddit.com/r/ASX_Bets/",
            "https://www.reddit.com/r/AusStocks/"
        ],
        "social_media": [
            "https://twitter.com/search?q=ASX",
            "https://www.linkedin.com/company/australian-securities-exchange"
        ]
    },
    "keywords": [
        "ASX", "Australian stocks", "Aussie market", "Australian shares",
        "ASX 200", "Australian Securities Exchange", "Aussie finance"
    ],
    "update_frequency_hours": 6
}

# Data Processing
DATA_CONFIG = {
    "min_data_points": 252,  # Minimum 1 year of data
    "max_missing_ratio": 0.1,  # Maximum 10% missing data
    "outlier_threshold": 3.0,  # Standard deviations for outlier detection
    "feature_selection_threshold": 0.01  # Minimum feature importance
}

# Database Configuration
DATABASE_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "database": os.getenv("DB_NAME", "finance_app"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres"),
    "pool_size": 10,
    "max_overflow": 20
}

# Logging Configuration
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": BASE_DIR / "logs" / "stock_prediction.log",
    "max_size": "10MB",
    "backup_count": 5
}

# API Configuration
API_CONFIG = {
    "host": "0.0.0.0",
    "port": 8000,
    "reload": True,
    "workers": 4
}

# Performance Monitoring
MONITORING_CONFIG = {
    "enable_metrics": True,
    "prediction_cache_ttl": 3600,  # 1 hour
    "model_performance_threshold": 0.55,  # Minimum accuracy
    "retrain_threshold": 0.50  # Retrain if accuracy drops below 50%
}

# Create directories if they don't exist
for directory in [DATA_DIR, RAW_DATA_DIR, PROCESSED_DATA_DIR, MODELS_DIR, SCALERS_DIR, FEATURES_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Logs directory
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True) 