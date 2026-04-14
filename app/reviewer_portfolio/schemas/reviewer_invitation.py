from datetime import datetime
from enum import Enum

from pydantic import BaseModel, EmailStr, Field


class ReviewerInviteStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class ReviewerInvitationCreate(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=120)
    last_name: str = Field(..., min_length=1, max_length=120)
    email: EmailStr
    role: str = Field(default="reviewer", max_length=64)
    designation: str = Field(..., min_length=1, max_length=200)
    department: str = Field(..., min_length=1, max_length=200)
    username: str = Field(..., min_length=1, max_length=120, pattern=r"^[a-zA-Z0-9._-]+$")
    status: ReviewerInviteStatus = ReviewerInviteStatus.ACTIVE
    language: str = Field(..., min_length=1, max_length=32)
    timezone: str = Field(..., min_length=1, max_length=64)


class ReviewerInvitationResponse(BaseModel):
    id: str
    email: EmailStr
    username: str
    temporary_password: str
    email_status: str
    message: str = "Invitation recorded and email sent."
    created_at: datetime
