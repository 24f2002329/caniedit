import os
import secrets
from datetime import datetime, timedelta
from urllib.parse import urlencode

import requests
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from jose import jwt

from app.core.security import (
    TokenDecodeError,
    create_access_token,
    decode_token,
    get_password_hash,
    ALGORITHM,
    SECRET_KEY,
    safe_decode_token,
    verify_password,
)
from app.db import get_db
from app.models.user import User
from app.models.otp_code import OtpCode
from app.models.rate_limit import RateLimit
from app.utils.usage import client_ip, get_usage_counter, usage_key_and_limit
from app.schemas.auth import (
    OTPRequest,
    OTPVerify,
    Token,
    UsageRead,
    UserCreate,
    UserLogin,
    UserRead,
    UserProfileUpdate,
)

router = APIRouter(prefix="/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)
optional_oauth2_scheme = oauth2_scheme
SHOW_OTP_IN_RESPONSE = os.getenv("AUTH_DEBUG_SHOW_OTP", "true").lower() == "true"
OTP_REQUEST_LIMIT_EMAIL = int(os.getenv("AUTH_OTP_REQUEST_LIMIT_EMAIL", "5"))
OTP_REQUEST_LIMIT_IP = int(os.getenv("AUTH_OTP_REQUEST_LIMIT_IP", "15"))
OTP_VERIFY_LIMIT_IP = int(os.getenv("AUTH_OTP_VERIFY_LIMIT_IP", "30"))
OTP_RATE_WINDOW_SECONDS = int(os.getenv("AUTH_OTP_RATE_WINDOW_SECONDS", "900"))  # 15 minutes
TOKEN_COOKIE_ENABLED = os.getenv("AUTH_TOKEN_COOKIE_ENABLED", "true").lower() == "true"
TOKEN_COOKIE_NAME = os.getenv("AUTH_TOKEN_COOKIE_NAME", "cid_access")
TOKEN_COOKIE_SECURE = os.getenv("AUTH_TOKEN_COOKIE_SECURE", "false").lower() == "true"
TOKEN_COOKIE_SAMESITE = os.getenv("AUTH_TOKEN_COOKIE_SAMESITE", "lax").lower()
TOKEN_COOKIE_MAX_AGE = int(os.getenv("AUTH_TOKEN_COOKIE_MAX_AGE", str(60 * 30)))  # default 30 minutes
TOKEN_COOKIE_DOMAIN = os.getenv("AUTH_TOKEN_COOKIE_DOMAIN", "") or None
GOOGLE_OAUTH_ENABLED = os.getenv("GOOGLE_OAUTH_ENABLED", "false").lower() == "true"
GOOGLE_OAUTH_CLIENT_ID = os.getenv("GOOGLE_OAUTH_CLIENT_ID", "")
GOOGLE_OAUTH_CLIENT_SECRET = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "")
GOOGLE_POST_LOGIN_REDIRECT = os.getenv("GOOGLE_POST_LOGIN_REDIRECT", "/")
GOOGLE_SCOPES = ["openid", "email", "profile"]


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _set_access_cookie(response: Response, token: str) -> None:
    if not TOKEN_COOKIE_ENABLED:
        return
    response.set_cookie(
        key=TOKEN_COOKIE_NAME,
        value=token,
        max_age=TOKEN_COOKIE_MAX_AGE,
        httponly=True,
        secure=TOKEN_COOKIE_SECURE,
        samesite=TOKEN_COOKIE_SAMESITE,
        path="/",
        domain=TOKEN_COOKIE_DOMAIN,
    )


def _clear_access_cookie(response: Response) -> None:
    if not TOKEN_COOKIE_ENABLED:
        return
    response.delete_cookie(
        key=TOKEN_COOKIE_NAME,
        httponly=True,
        secure=TOKEN_COOKIE_SECURE,
        samesite=TOKEN_COOKIE_SAMESITE,
        path="/",
        domain=TOKEN_COOKIE_DOMAIN,
    )


def _require_google_config() -> None:
    if not GOOGLE_OAUTH_ENABLED:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Google OAuth is not configured yet.")
    if not GOOGLE_OAUTH_CLIENT_ID or not GOOGLE_OAUTH_CLIENT_SECRET or not GOOGLE_REDIRECT_URI:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Google OAuth client is missing configuration.")


def _create_state_token(redirect_to: str | None = None) -> str:
    payload = {
        "tp": "google_state",
        "redir": redirect_to,
        "nonce": secrets.token_urlsafe(8),
        "exp": datetime.utcnow() + timedelta(minutes=10),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def _decode_state_token(state: str) -> dict:
    try:
        payload = decode_token(state)
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid state") from exc
    if payload.get("tp") != "google_state":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid state")
    return payload


def _build_google_auth_url(state: str) -> str:
    params = {
        "client_id": GOOGLE_OAUTH_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(GOOGLE_SCOPES),
        "state": state,
        "access_type": "online",
        "include_granted_scopes": "true",
        "prompt": "select_account",
    }
    return f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"


def _fetch_google_tokens(code: str) -> dict:
    data = {
        "client_id": GOOGLE_OAUTH_CLIENT_ID,
        "client_secret": GOOGLE_OAUTH_CLIENT_SECRET,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
        "code": code,
    }
    response = requests.post("https://oauth2.googleapis.com/token", data=data, timeout=10)
    if not response.ok:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to exchange Google code")
    return response.json()


def _get_google_profile(tokens: dict) -> dict:
    access_token = tokens.get("access_token")
    id_token = tokens.get("id_token")
    email = None
    name = None

    if id_token:
        try:
            claims = jwt.get_unverified_claims(id_token)
            email = claims.get("email")
            name = claims.get("name") or claims.get("given_name")
        except Exception:
            email = None
            name = None

    if access_token:
        resp = requests.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )
        if resp.ok:
            data = resp.json()
            email = data.get("email") or email
            name = data.get("name") or name

    if not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unable to fetch Google profile email")

    return {"email": email, "full_name": name}


def _bump_rate_limit(
    db: Session,
    key: str,
    limit: int,
    window_seconds: int,
    detail: str,
) -> None:
    now = datetime.utcnow()
    window_end = now + timedelta(seconds=window_seconds)
    record: RateLimit | None = db.query(RateLimit).filter(RateLimit.key == key).first()

    if record and record.window_end > now:
        if record.count >= limit:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=detail)
        record.count += 1
        record.touch(now)
        db.add(record)
        db.commit()
        return

    if record:
        record.count = 1
        record.window_start = now
        record.window_end = window_end
        record.touch(now)
        db.add(record)
    else:
        record = RateLimit(
            key=key,
            count=1,
            window_start=now,
            window_end=window_end,
        )
        db.add(record)
    db.commit()


def _get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def _create_user_if_missing(db: Session, email: str, full_name: str | None = None) -> User:
    user = _get_user_by_email(db, email)
    if user:
        if full_name and not user.full_name:
            user.full_name = full_name
            db.add(user)
            db.commit()
            db.refresh(user)
        return user
    user = User(email=email, full_name=full_name, password_hash=get_password_hash(os.urandom(8).hex()))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_current_user(
    request: Request,
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token_value = token or request.cookies.get(TOKEN_COOKIE_NAME)
    if not token_value:
        raise credentials_error

    try:
        payload = safe_decode_token(token_value)
    except TokenDecodeError as exc:
        raise credentials_error from exc

    user_id = payload.get("sub")
    if not user_id:
        raise credentials_error

    user = db.get(User, int(user_id))
    if not user:
        raise credentials_error

    return user


def get_optional_user(
    request: Request,
    token: str | None = Depends(optional_oauth2_scheme),
    db: Session = Depends(get_db),
) -> User | None:
    token_value = token or request.cookies.get(TOKEN_COOKIE_NAME)
    if not token_value:
        return None
    try:
        payload = safe_decode_token(token_value)
    except TokenDecodeError:
        return None
    user_id = payload.get("sub")
    if not user_id:
        return None
    return db.get(User, int(user_id))


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register_user(payload: UserCreate, db: Session = Depends(get_db)) -> User:
    email = _normalize_email(payload.email)
    existing = _get_user_by_email(db, email)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already exists")

    user = User(
        email=email,
        full_name=payload.full_name,
        password_hash=get_password_hash(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(payload: UserLogin, response: Response, db: Session = Depends(get_db)) -> Token:
    email = _normalize_email(payload.email)
    user = _get_user_by_email(db, email)

    invalid_credentials = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect email or password",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not user or not verify_password(payload.password, user.password_hash):
        raise invalid_credentials

    access_token = create_access_token(subject=user.id)
    _set_access_cookie(response, access_token)
    return Token(access_token=access_token, token_type="bearer")


@router.post("/request-otp", status_code=status.HTTP_200_OK)
def request_otp(payload: OTPRequest, request: Request, db: Session = Depends(get_db)) -> dict:
    email = _normalize_email(payload.email)

    ip = client_ip(request)
    _bump_rate_limit(
        db,
        key=f"otp:req:email:{email}",
        limit=OTP_REQUEST_LIMIT_EMAIL,
        window_seconds=OTP_RATE_WINDOW_SECONDS,
        detail="Too many codes sent. Please try again later.",
    )
    _bump_rate_limit(
        db,
        key=f"otp:req:ip:{ip}",
        limit=OTP_REQUEST_LIMIT_IP,
        window_seconds=OTP_RATE_WINDOW_SECONDS,
        detail="Too many codes sent from this network. Please try again later.",
    )

    db.query(OtpCode).filter(OtpCode.email == email).delete()

    code = OtpCode.generate_code()
    otp = OtpCode(
        email=email,
        code_hash=get_password_hash(code),
        expires_at=OtpCode.expiry_time(),
    )
    db.add(otp)
    db.commit()
    return {"detail": "OTP sent", **({"code": code} if SHOW_OTP_IN_RESPONSE else {})}


@router.post("/verify-otp", response_model=Token, status_code=status.HTTP_200_OK)
def verify_otp(payload: OTPVerify, request: Request, response: Response, db: Session = Depends(get_db)) -> Token:
    email = _normalize_email(payload.email)
    ip = client_ip(request)
    _bump_rate_limit(
        db,
        key=f"otp:verify:ip:{ip}",
        limit=OTP_VERIFY_LIMIT_IP,
        window_seconds=OTP_RATE_WINDOW_SECONDS,
        detail="Too many attempts. Please wait and try again.",
    )
    otp: OtpCode | None = db.query(OtpCode).filter(OtpCode.email == email).first()

    if not otp:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OTP not found. Request a new code.")

    if otp.used:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OTP already used. Request a new code.")

    if otp.attempts >= 5:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many attempts. Request a new code.")

    if datetime.utcnow() > otp.expires_at:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OTP expired. Request a new code.")

    if not verify_password(payload.code, otp.code_hash):
        otp.attempts += 1
        db.add(otp)
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect code")

    otp.used = True
    db.add(otp)

    user = _create_user_if_missing(db, email, payload.full_name)
    access_token = create_access_token(subject=user.id, expires_minutes=30)
    _set_access_cookie(response, access_token)
    db.commit()
    return Token(access_token=access_token, token_type="bearer")


@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(response: Response) -> dict:
    _clear_access_cookie(response)
    return {"detail": "Logged out"}


@router.get("/usage", response_model=UsageRead)
def read_usage(
    request: Request,
    current_user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> UsageRead:
    scope, key, limit = usage_key_and_limit(request, current_user)
    counter = get_usage_counter(db, scope=scope, key=key, limit=limit)
    return UsageRead(scope=scope, limit=counter.limit, used=counter.used)


@router.get("/me", response_model=UserRead)
def read_current_user(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.patch("/me", response_model=UserRead)
def update_current_user(
    payload: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    current_user.full_name = payload.full_name
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.get("/google")
def google_oauth_start(redirect: str | None = None) -> RedirectResponse:
    _require_google_config()
    state = _create_state_token(redirect)
    auth_url = _build_google_auth_url(state)
    return RedirectResponse(url=auth_url, status_code=status.HTTP_302_FOUND)


@router.get("/google/callback")
def google_oauth_callback(code: str | None = None, state: str | None = None, db: Session = Depends(get_db)):
    _require_google_config()
    if not code or not state:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing code or state")

    payload = _decode_state_token(state)
    tokens = _fetch_google_tokens(code)
    profile = _get_google_profile(tokens)

    user = _create_user_if_missing(db, _normalize_email(profile["email"]), profile.get("full_name"))
    access_token = create_access_token(subject=user.id, expires_minutes=30)

    final_redirect = payload.get("redir") or GOOGLE_POST_LOGIN_REDIRECT or "/"
    redirect_response = RedirectResponse(url=final_redirect, status_code=status.HTTP_302_FOUND)
    _set_access_cookie(redirect_response, access_token)
    return redirect_response
