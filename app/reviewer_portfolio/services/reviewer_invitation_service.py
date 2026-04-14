from __future__ import annotations

import secrets
from datetime import datetime, timezone

from fastapi import HTTPException, status
from pymongo.errors import DuplicateKeyError

from app.core.database import get_users_collection, is_db_connected
from app.core.email_service import send_reviewer_invitation_email
from app.core.security import get_password_hash
from app.reviewer_portfolio.schemas.reviewer_invitation import (
    ReviewerInvitationCreate,
    ReviewerInvitationResponse,
)


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


async def create_reviewer_invitation(
    payload: ReviewerInvitationCreate,
    *,
    invited_by_user_id: str,
) -> ReviewerInvitationResponse:
    if not is_db_connected():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable.",
        )

    col = get_users_collection()
    email_norm = str(payload.email).strip().lower()
    username_norm = payload.username.strip()

    existing = await col.find_one(
        {"$or": [{"email": email_norm}, {"username": username_norm}]},
        projection={"_id": 1, "email": 1, "username": 1},
    )
    if existing:
        if str(existing.get("email", "")).lower() == email_norm:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this email already exists.",
            )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This username is already taken.",
        )

    plain_password = secrets.token_urlsafe(14)
    hashed = get_password_hash(plain_password)

    role = str(payload.role or "reviewer").strip().lower() or "reviewer"
    if role != "reviewer":
        role = "reviewer"

    doc = {
        "first_name": payload.first_name.strip(),
        "last_name": payload.last_name.strip(),
        "email": email_norm,
        "username": username_norm,
        "hashed_password": hashed,
        "role": role,
        "designation": payload.designation.strip(),
        "department": payload.department.strip(),
        "language": payload.language.strip(),
        "timezone": payload.timezone.strip(),
        "is_active": payload.status.value == "active",
        "requires_password_change": True,
        "is_first_login": True,
        "mfa_enabled": False,
        "invited_at": _now_utc(),
        "invited_by": invited_by_user_id,
        "created_at": _now_utc(),
        "updated_at": _now_utc(),
    }

    try:
        result = await col.insert_one(doc)
    except DuplicateKeyError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email or username already exists.",
        ) from None

    recipient_name = f"{doc['first_name']} {doc['last_name']}".strip()
    email_status = "sent"
    message = "Invitation recorded and email sent."
    try:
        email_status = send_reviewer_invitation_email(
            to_email=email_norm,
            recipient_name=recipient_name or username_norm,
            username=username_norm,
            plain_password=plain_password,
        )
        if email_status == "dry_run":
            message = "Invitation recorded. Email dry-run is enabled, so no real email was sent."
    except Exception:
        await col.delete_one({"_id": result.inserted_id})
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="User was not created because the invitation email could not be sent.",
        ) from None

    return ReviewerInvitationResponse(
        id=str(result.inserted_id),
        email=payload.email,
        username=username_norm,
        temporary_password=plain_password,
        email_status=email_status,
        message=message,
        created_at=doc["created_at"],
    )
