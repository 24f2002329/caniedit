from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db.session import get_db
from app.subscriptions.service import ensure_starter_subscription

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


@router.post("/starter")
def create_starter_subscription(
	current_user=Depends(get_current_user),
	db: Session = Depends(get_db),
):
	subscription = ensure_starter_subscription(db, current_user)
	return {
		"success": True,
		"subscription": {
			"id": str(subscription.id),
			"status": subscription.status,
			"plan_id": str(subscription.plan_id),
		},
	}


__all__ = ["router"]
