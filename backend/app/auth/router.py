"""Deprecated auth router.

Authentication is now handled entirely by Supabase Auth on the frontend.
The backend only validates Supabase JWTs via dependencies in app.auth.dependencies.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["auth"])
