from datetime import datetime, timedelta
import os
import secrets

from sqlalchemy import Column, DateTime, Integer, String, Boolean

from app.db import Base


def _default_expiry_minutes() -> int:
    try:
        return int(os.getenv("AUTH_OTP_EXPIRES_MINUTES", "5"))
    except ValueError:
        return 5


class OtpCode(Base):
    __tablename__ = "otp_codes"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), index=True, nullable=False)
    code_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    attempts = Column(Integer, default=0, nullable=False)
    used = Column(Boolean, default=False, nullable=False)

    @staticmethod
    def expiry_time() -> datetime:
        return datetime.utcnow() + timedelta(minutes=_default_expiry_minutes())

    @staticmethod
    def generate_code() -> str:
        # 6-digit numeric code
        return f"{secrets.randbelow(1_000_000):06d}"
