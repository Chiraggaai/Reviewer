"""
Glimmora-Team-Project ``app/dependencies/reviewer.py`` — same stack as ``app/routers/reviewer/*``.
"""

from fastapi import Depends

from app.core.reviewer_auth_service import (
    ensure_reviewer_access,
    ensure_reviewer_admin_access,
)
from app.core.security import get_current_user


async def require_reviewer_user(current_user: dict = Depends(get_current_user)) -> dict:
    ensure_reviewer_access(current_user)
    return current_user


async def require_reviewer_admin_user(current_user: dict = Depends(get_current_user)) -> dict:
    ensure_reviewer_admin_access(current_user)
    return current_user
