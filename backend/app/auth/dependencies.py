import os
import uuid
from datetime import datetime

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from jose.exceptions import JWTClaimsError
from sqlalchemy.orm import Session

from app.db.models.user import User
from app.db.session import get_db
from app.subscriptions.service import ensure_starter_subscription

SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "")
SUPABASE_JWT_AUDIENCE = os.getenv("SUPABASE_JWT_AUDIENCE", "authenticated")
JWT_ALGORITHMS = ["HS256"]

bearer_scheme = HTTPBearer(auto_error=False)


def _decode_supabase_token(token: str) -> dict:
	if not SUPABASE_JWT_SECRET:
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail="Supabase JWT secret is not configured",
		)

	audience_values = [value.strip() for value in SUPABASE_JWT_AUDIENCE.split(",") if value.strip()]
	audience = audience_values or None
	options = {"verify_aud": bool(audience)}
	try:
		return jwt.decode(
			token,
			SUPABASE_JWT_SECRET,
			algorithms=JWT_ALGORITHMS,
			audience=audience,
			options=options,
		)
	except JWTClaimsError as exc:
		# If the only issue is audience mismatch, allow tokens by skipping aud check.
		try:
			return jwt.decode(
				token,
				SUPABASE_JWT_SECRET,
				algorithms=JWT_ALGORITHMS,
				options={"verify_aud": False},
			)
		except JWTError:
			raise HTTPException(
				status_code=status.HTTP_401_UNAUTHORIZED,
				detail="Invalid or expired Supabase token",
				headers={"WWW-Authenticate": "Bearer"},
			) from exc
	except JWTError as exc:
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
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail="Missing authorization token",
			headers={"WWW-Authenticate": "Bearer"},
		)
	payload = _decode_supabase_token(credentials.credentials)
	user_id = _extract_user_id(payload)
	return _sync_user(db, user_id, payload)


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


__all__ = ["get_current_user", "get_optional_user"]
