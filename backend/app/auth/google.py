"""Google OAuth helpers (re-exported from router for now)."""

from app.auth.router import (
    GOOGLE_OAUTH_CLIENT_ID,
    GOOGLE_OAUTH_CLIENT_SECRET,
    GOOGLE_OAUTH_ENABLED,
    GOOGLE_POST_LOGIN_REDIRECT,
    GOOGLE_REDIRECT_URI,
    GOOGLE_SCOPES,
    _build_google_auth_url,
    _create_state_token,
    _decode_state_token,
    _fetch_google_tokens,
    _get_google_profile,
    _require_google_config,
)

__all__ = [
    "GOOGLE_OAUTH_CLIENT_ID",
    "GOOGLE_OAUTH_CLIENT_SECRET",
    "GOOGLE_OAUTH_ENABLED",
    "GOOGLE_POST_LOGIN_REDIRECT",
    "GOOGLE_REDIRECT_URI",
    "GOOGLE_SCOPES",
    "_build_google_auth_url",
    "_create_state_token",
    "_decode_state_token",
    "_fetch_google_tokens",
    "_get_google_profile",
    "_require_google_config",
]
