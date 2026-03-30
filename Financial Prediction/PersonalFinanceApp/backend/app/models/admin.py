"""
SQLAlchemy model for admin portal settings.

Stores the single-row admin configuration: TOTP secret, password hash,
setup state, and timestamps for the last data refresh and model retrain.
"""

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.sql import func

from app.core.database import Base


class AdminSettings(Base):
    __tablename__ = "admin_settings"

    id = Column(Integer, primary_key=True, index=True)
    totp_secret = Column(String(64), nullable=True)
    setup_complete = Column(Boolean, default=False, nullable=False)
    admin_password_hash = Column(String(255), nullable=True)
    last_data_refresh = Column(DateTime, nullable=True)
    last_model_trained = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now(), nullable=True)
