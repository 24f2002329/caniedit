from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db.session import get_db
from app.users.service import (
	get_profile,
	get_subscription_summary,
	get_usage_summary,
	request_account_deletion,
	update_profile,
)

router = APIRouter(prefix="/users", tags=["users"])


class ProfileUpdate(BaseModel):
	full_name: str | None = None
	email: EmailStr | None = None


@router.get("/me")
def get_me(
	current_user=Depends(get_current_user),
):
	return get_profile(current_user)


@router.patch("/me")
def update_me(
	payload: ProfileUpdate,
	current_user=Depends(get_current_user),
	db: Session = Depends(get_db),
):
	user = update_profile(db, current_user, full_name=payload.full_name, email=payload.email)
	return get_profile(user)


@router.get("/me/usage")
def get_my_usage(
	current_user=Depends(get_current_user),
	db: Session = Depends(get_db),
):
	return {"usage": get_usage_summary(db, current_user)}


@router.get("/me/subscription")
def get_my_subscription(
	current_user=Depends(get_current_user),
	db: Session = Depends(get_db),
):
	return get_subscription_summary(db, current_user)


@router.post("/me/delete")
def delete_me(
	current_user=Depends(get_current_user),
	db: Session = Depends(get_db),
):
	result = request_account_deletion(db, current_user)
	return {
		"success": True,
		"delete_requested_at": result["delete_requested_at"].isoformat(),
		"delete_at": result["delete_at"].isoformat(),
	}


__all__ = ["router"]
