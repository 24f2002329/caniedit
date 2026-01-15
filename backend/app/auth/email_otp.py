"""Email OTP helpers (re-exported from router for now)."""

from app.auth.router import request_otp, verify_otp

__all__ = ["request_otp", "verify_otp"]
