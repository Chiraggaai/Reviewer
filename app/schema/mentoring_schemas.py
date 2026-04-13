"""
Mentoring Log — reviewer notes for student contributors (demo store).
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class MentoringContributorCard(BaseModel):
    model_config = {"populate_by_name": True}

    contributor_id: str = Field(
        serialization_alias="contributorId",
        description="Stable id for note APIs (path param).",
    )
    display_label: str = Field(
        serialization_alias="displayLabel",
        description="Anonymized handle, e.g. Contributor-E5L.",
    )
    is_student: bool = Field(default=True, serialization_alias="isStudent")
    tasks_completed_count: int = Field(serialization_alias="tasksCompletedCount")
    acceptance_rate_percent: float = Field(serialization_alias="acceptanceRatePercent")
    note_count: int = Field(serialization_alias="noteCount")


class MentoringNote(BaseModel):
    model_config = {"populate_by_name": True}

    note_id: str = Field(serialization_alias="noteId")
    category: str
    body: str
    created_at: datetime = Field(serialization_alias="createdAt")


class MentoringNotesPayload(BaseModel):
    model_config = {"populate_by_name": True}

    contributor_id: str = Field(serialization_alias="contributorId")
    display_label: str = Field(serialization_alias="displayLabel")
    notes: list[MentoringNote]


class MentoringContributorsPayload(BaseModel):
    model_config = {"populate_by_name": True}

    contributors: list[MentoringContributorCard]
    category_suggestions: list[str] = Field(
        default_factory=list,
        serialization_alias="categorySuggestions",
        description="Optional dropdown values for the Add Note form.",
    )


class MentoringNoteCreateRequest(BaseModel):
    model_config = {"populate_by_name": True}

    category: str = Field(min_length=1, description="e.g. General mentoring, Biometric authentication")
    body: str = Field(
        min_length=20,
        description="Mentoring note text (min 20 characters).",
    )


class MentoringNoteCreatedPayload(BaseModel):
    model_config = {"populate_by_name": True}

    note: MentoringNote
