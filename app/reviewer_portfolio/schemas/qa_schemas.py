"""
Workroom Q&A (WRK-001) — API contracts for module 8.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class QandaAuthorRole(str, Enum):
    CONTRIBUTOR = "contributor"
    REVIEWER = "reviewer"
    CLIENT_TEAM = "client_team"
    GLIMMORA_SUPPORT = "glimmora_support"


def qanda_display_label(role: QandaAuthorRole) -> str:
    return {
        QandaAuthorRole.CONTRIBUTOR: "Contributor",
        QandaAuthorRole.REVIEWER: "Reviewer",
        QandaAuthorRole.CLIENT_TEAM: "Client Team",
        QandaAuthorRole.GLIMMORA_SUPPORT: "Glimmora Support",
    }[role]


MAX_ATTACHMENT_BYTES = 10 * 1024 * 1024


class QaAttachmentMeta(BaseModel):
    model_config = {"populate_by_name": True}

    filename: str = Field(min_length=1)
    size_bytes: int = Field(ge=1, serialization_alias="sizeBytes")
    content_type: Optional[str] = Field(default=None, serialization_alias="contentType")

    @field_validator("size_bytes")
    @classmethod
    def _cap_size(cls, v: int) -> int:
        if v > MAX_ATTACHMENT_BYTES:
            raise ValueError(f"Each attachment must be at most {MAX_ATTACHMENT_BYTES} bytes (demo cap).")
        return v


class WorkroomQandaMessage(BaseModel):
    model_config = {"populate_by_name": True}

    message_id: str = Field(serialization_alias="messageId")
    evidence_id: str = Field(serialization_alias="evidenceId")
    author_role: QandaAuthorRole = Field(serialization_alias="authorRole")
    display_label: str = Field(serialization_alias="displayLabel")
    body: str
    flagged_about_feedback: bool = Field(default=False, serialization_alias="flaggedAboutFeedback")
    is_change_request: bool = Field(default=False, serialization_alias="isChangeRequest")
    created_at: datetime = Field(serialization_alias="createdAt")
    attachments: list[QaAttachmentMeta] = Field(default_factory=list)


class WorkroomPageContext(BaseModel):
    model_config = {"populate_by_name": True}

    evidence_id: str = Field(serialization_alias="evidenceId")
    task_name: str = Field(serialization_alias="taskName")
    project_name: str = Field(serialization_alias="projectName")
    contributor_display: str = Field(
        default="Contributor (anonymized)",
        serialization_alias="contributorDisplay",
    )
    participants_note: str = Field(
        default="WRK-001: Messages show role labels only, never personal names.",
        serialization_alias="participantsNote",
    )
    evidence_pack_api_path: str = Field(serialization_alias="evidencePackApiPath")
    qa_messages_api_path: str = Field(serialization_alias="qaMessagesApiPath")


class WorkroomMessagesPage(BaseModel):
    model_config = {"populate_by_name": True}

    messages: list[WorkroomQandaMessage]
    search_applied: bool = Field(default=False, serialization_alias="searchApplied")


class QaReviewerPostRequest(BaseModel):
    model_config = {"populate_by_name": True}

    body: str = Field(min_length=1)
    flag_question_about_feedback: bool = Field(
        default=False,
        validation_alias="flagQuestionAboutFeedback",
        serialization_alias="flagQuestionAboutFeedback",
    )
    attachments: list[QaAttachmentMeta] = Field(default_factory=list)


class QaContributorPostRequest(BaseModel):
    model_config = {"populate_by_name": True}

    body: str = Field(min_length=1)
    flag_question_about_feedback: bool = Field(
        default=False,
        validation_alias="flagQuestionAboutFeedback",
        serialization_alias="flagQuestionAboutFeedback",
    )
    attachments: list[QaAttachmentMeta] = Field(default_factory=list)
