import base64
import json
import logging
import os
import threading
import time
import uuid
from datetime import datetime
from urllib.parse import urlparse
from urllib.request import Request as UrlRequest
from urllib.request import urlopen

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from jose.exceptions import JWTClaimsError
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from app.db.models.user import User
from app.db.session import get_db
from app.subscriptions.service import ensure_starter_subscription

load_dotenv()

SUPABASE_JWT_AUDIENCE = os.getenv("SUPABASE_JWT_AUDIENCE", "authenticated")
SUPABASE_PROJECT_REF = os.getenv("SUPABASE_PROJECT_REF", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_DATABASE_URL = os.getenv("SUPABASE_DATABASE_URL", "")
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "")
SUPABASE_JWKS_TTL_SECONDS = int(os.getenv("SUPABASE_JWKS_TTL_SECONDS", "3600"))
JWT_ALGORITHMS = ["ES256", "HS256"]
DEBUG_AUTH = os.getenv("DEBUG_AUTH", "").lower() in {"1", "true", "yes"} or os.getenv("ENV", "local").lower() == "local"

logger = logging.getLogger("app.auth")

bearer_scheme = HTTPBearer(auto_error=False)


_jwks_cache: dict = {"keys": [], "expires_at": 0.0}
_jwks_lock = threading.Lock()


def _extract_project_ref_from_url(url: str) -> str:
	if not url:
		return ""
	parsed = urlparse(url)
	host = parsed.netloc or parsed.path
	if not host:
		return ""
	return host.split(".")[0]


def _extract_project_ref_from_db_url(db_url: str) -> str:
	if not db_url:
		return ""
	parsed = urlparse(db_url)
	userinfo = parsed.netloc.split("@", 1)[0] if "@" in parsed.netloc else ""
	username = userinfo.split(":", 1)[0] if userinfo else ""
	if username.startswith("postgres."):
		return username.split("postgres.", 1)[1]
	return ""


def _get_supabase_project_ref() -> str:
	if SUPABASE_PROJECT_REF:
		return SUPABASE_PROJECT_REF
	ref = _extract_project_ref_from_url(SUPABASE_URL)
	if ref:
		return ref
	return _extract_project_ref_from_db_url(SUPABASE_DATABASE_URL)


def _jwks_url() -> str:
	project_ref = _get_supabase_project_ref()
	if not project_ref:
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail="Supabase project reference is not configured",
		)
	return f"https://{project_ref}.supabase.co/auth/v1/.well-known/jwks.json"


def _fetch_jwks() -> list[dict]:
	request = UrlRequest(_jwks_url(), headers={"Accept": "application/json"})
	with urlopen(request, timeout=5) as response:
		payload = response.read()
	data = json.loads(payload.decode("utf-8"))
	keys = data.get("keys", []) if isinstance(data, dict) else []
	if not isinstance(keys, list):
		return []
	if DEBUG_AUTH:
		logger.info("Loaded JWKS keys: %s", [key.get("kid") for key in keys if isinstance(key, dict)])
	return keys


def _get_jwks(force_refresh: bool = False) -> list[dict]:
	now = time.time()
	with _jwks_lock:
		if not force_refresh and _jwks_cache["keys"] and now < _jwks_cache["expires_at"]:
			return _jwks_cache["keys"]
		keys = _fetch_jwks()
		ttl = max(SUPABASE_JWKS_TTL_SECONDS, 60)
		_jwks_cache.update({"keys": keys, "expires_at": now + ttl})
		return keys


def _get_signing_key(kid: str) -> dict:
	keys = _get_jwks()
	for key in keys:
		if key.get("kid") == kid:
			return key
	if DEBUG_AUTH:
		logger.warning("Supabase JWKS kid not found: %s", kid)
	# Key rotation: refresh once and retry
	keys = _get_jwks(force_refresh=True)
	for key in keys:
		if key.get("kid") == kid:
			return key
	raise HTTPException(
		status_code=status.HTTP_401_UNAUTHORIZED,
		detail="Invalid or expired Supabase token",
		headers={"WWW-Authenticate": "Bearer"},
	)


def _decode_supabase_token(token: str) -> dict:
	try:
		header = jwt.get_unverified_header(token)
	except JWTError as exc:
		if DEBUG_AUTH:
			logger.warning("Supabase token header invalid")
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail="Invalid or expired Supabase token",
			headers={"WWW-Authenticate": "Bearer"},
		) from exc

	alg = header.get("alg")
	if alg not in JWT_ALGORITHMS:
		if DEBUG_AUTH:
			logger.warning("Supabase token has unsupported alg: %s", alg)
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail="Invalid or expired Supabase token",
			headers={"WWW-Authenticate": "Bearer"},
		)

	audience_values = [value.strip() for value in SUPABASE_JWT_AUDIENCE.split(",") if value.strip()]
	audience = audience_values[0] if len(audience_values) == 1 else None
	base_issuer = f"https://{_get_supabase_project_ref()}.supabase.co"
	issuer_candidates = [f"{base_issuer}/auth/v1", base_issuer]
	options = {"verify_aud": bool(audience), "verify_iss": True}

	try:
		if alg == "HS256":
			if not SUPABASE_JWT_SECRET:
				raise HTTPException(
					status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
					detail="Supabase JWT secret is not configured",
				)

			secret_candidates: list[bytes | str] = [SUPABASE_JWT_SECRET]
			try:
				secret_candidates.append(base64.b64decode(SUPABASE_JWT_SECRET))
			except Exception:
				pass
			try:
				padded = SUPABASE_JWT_SECRET + "=" * (-len(SUPABASE_JWT_SECRET) % 4)
				secret_candidates.append(base64.urlsafe_b64decode(padded))
			except Exception:
				pass

			for secret in secret_candidates:
				for issuer in issuer_candidates:
					try:
						return jwt.decode(
							token,
							secret,
							algorithms=["HS256"],
							audience=audience,
							issuer=issuer,
							options=options,
						)
					except JWTClaimsError:
						pass
					except JWTError:
						pass
			raise JWTClaimsError("Invalid issuer")

		kid = header.get("kid")
		if not kid:
			raise HTTPException(
				status_code=status.HTTP_401_UNAUTHORIZED,
				detail="Invalid or expired Supabase token",
				headers={"WWW-Authenticate": "Bearer"},
			)

		signing_key = _get_signing_key(kid)
		for issuer in issuer_candidates:
			try:
				return jwt.decode(
					token,
					signing_key,
					algorithms=["ES256"],
					audience=audience,
					issuer=issuer,
					options=options,
				)
			except JWTClaimsError:
				pass
		raise JWTClaimsError("Invalid issuer")
	except JWTClaimsError as exc:
		if DEBUG_AUTH:
			try:
				claims = jwt.get_unverified_claims(token)
				header = jwt.get_unverified_header(token)
				logger.warning(
					"Supabase token rejected (claims error). alg=%s kid=%s iss=%s aud=%s exp=%s",
					header.get("alg"),
					header.get("kid"),
					claims.get("iss"),
					claims.get("aud"),
					claims.get("exp"),
				)
			except Exception:
				logger.warning("Supabase token rejected (claims error).")
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail="Invalid or expired Supabase token",
			headers={"WWW-Authenticate": "Bearer"},
		) from exc
	except JWTError as exc:
		if DEBUG_AUTH:
			try:
				claims = jwt.get_unverified_claims(token)
				header = jwt.get_unverified_header(token)
				logger.warning(
					"Supabase token rejected (jwt error). alg=%s kid=%s iss=%s aud=%s exp=%s error=%s",
					header.get("alg"),
					header.get("kid"),
					claims.get("iss"),
					claims.get("aud"),
					claims.get("exp"),
					exc,
				)
			except Exception:
				logger.warning("Supabase token rejected (jwt error).")
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail="Invalid or expired Supabase token",
			headers={"WWW-Authenticate": "Bearer"},
		) from exc


def _extract_user_id(payload: dict) -> uuid.UUID:
	subject = payload.get("sub")
	if not subject:
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail="Supabase token missing subject",
			headers={"WWW-Authenticate": "Bearer"},
		)
	try:
		return uuid.UUID(str(subject))
	except ValueError as exc:
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail="Supabase token subject is invalid",
			headers={"WWW-Authenticate": "Bearer"},
		) from exc


def _sync_user(db: Session, user_id: uuid.UUID, payload: dict) -> User:
	email = payload.get("email")
	metadata = payload.get("user_metadata") or {}
	full_name = metadata.get("full_name") or metadata.get("name")
	now = datetime.utcnow()

	user = db.get(User, user_id)
	if not user:
		user = User(id=user_id, email=email, full_name=full_name)
		db.add(user)
		db.commit()
		db.refresh(user)
		ensure_starter_subscription(db, user)
		return user

	updated = False
	if email and user.email != email:
		user.email = email
		updated = True
	if full_name and user.full_name != full_name:
		user.full_name = full_name
		updated = True
	if updated:
		user.touch(now)
		db.add(user)
		db.commit()
		db.refresh(user)

	ensure_starter_subscription(db, user)
	return user


def get_current_user(
	credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
	db: Session = Depends(get_db),
) -> User:
	if not credentials:
		if DEBUG_AUTH:
			logger.warning("Missing authorization token")
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail="Missing authorization token",
			headers={"WWW-Authenticate": "Bearer"},
		)
	payload = _decode_supabase_token(credentials.credentials)
	user_id = _extract_user_id(payload)
	return _sync_user(db, user_id, payload)


def get_current_claims(
	credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict:
	if not credentials:
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail="Missing authorization token",
			headers={"WWW-Authenticate": "Bearer"},
		)
	payload = _decode_supabase_token(credentials.credentials)
	return {
		"sub": payload.get("sub"),
		"email": payload.get("email"),
		"role": payload.get("role"),
	}


def get_optional_user(
	credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
	db: Session = Depends(get_db),
) -> User | None:
	if not credentials:
		return None
	try:
		payload = _decode_supabase_token(credentials.credentials)
		user_id = _extract_user_id(payload)
		return _sync_user(db, user_id, payload)
	except HTTPException as exc:
		if exc.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN):
			return None
		raise


__all__ = ["get_current_user", "get_optional_user", "get_current_claims"]
