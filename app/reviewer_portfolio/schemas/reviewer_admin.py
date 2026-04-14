from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


ReviewerMemberStatus = Literal["active", "inactive", "invited"]


class ReviewerListItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    name: str
    email: str
    role: str
    status: ReviewerMemberStatus
    last_active: datetime | None = Field(default=None, serialization_alias="lastActive")


class ReviewerListResponse(BaseModel):
    items: list[ReviewerListItem]
    total: int


class ReviewerProjectAccessItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    project_id: str = Field(serialization_alias="projectId")
    project_name: str = Field(serialization_alias="projectName")
    has_access: bool = Field(serialization_alias="hasAccess")


class ReviewerProjectAccessResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    reviewer_id: str = Field(serialization_alias="reviewerId")
    reviewer_name: str = Field(serialization_alias="reviewerName")
    projects: list[ReviewerProjectAccessItem]


class ReviewerProjectAccessUpdateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    project_ids: list[str] = Field(default_factory=list, alias="projectIds")


class ReviewerStatusUpdateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    is_active: bool = Field(alias="isActive")


class ReviewerMutationResponse(BaseModel):
    message: str
