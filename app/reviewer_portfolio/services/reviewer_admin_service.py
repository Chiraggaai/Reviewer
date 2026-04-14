from __future__ import annotations

from datetime import datetime, timezone

from bson import ObjectId
from fastapi import HTTPException, status

from app.core.database import (
    get_database,
    get_reviewer_projects_collection,
    get_users_collection,
    is_db_connected,
)
from app.reviewer_portfolio.schemas.reviewer_admin import (
    ReviewerListItem,
    ReviewerListResponse,
    ReviewerMutationResponse,
    ReviewerProjectAccessItem,
    ReviewerProjectAccessResponse,
    ReviewerProjectAccessUpdateRequest,
)
from app.reviewer_portfolio.services import mock_store


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _to_object_id(value: str) -> ObjectId:
    try:
        return ObjectId(value)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid reviewer id.") from None


def _ensure_db() -> None:
    if not is_db_connected():
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database unavailable.")


def _derive_status(user: dict) -> str:
    if not bool(user.get("is_active", True)):
        return "inactive"
    if bool(user.get("is_first_login", False)):
        return "invited"
    return "active"


def _display_name(user: dict) -> str:
    first = str(user.get("first_name") or "").strip()
    last = str(user.get("last_name") or "").strip()
    full = f"{first} {last}".strip()
    return full or str(user.get("username") or "Reviewer")


async def list_reviewers() -> ReviewerListResponse:
    _ensure_db()
    col = get_users_collection()
    docs = await col.find({"role": "reviewer"}, {"hashed_password": 0}).sort("created_at", -1).to_list(length=500)

    items: list[ReviewerListItem] = []
    for d in docs:
        items.append(
            ReviewerListItem(
                id=str(d.get("_id")),
                name=_display_name(d),
                email=str(d.get("email") or ""),
                role=str(d.get("role") or "reviewer"),
                status=_derive_status(d),  # type: ignore[arg-type]
                last_active=d.get("last_login_at") or d.get("updated_at"),
            )
        )
    return ReviewerListResponse(items=items, total=len(items))


async def _get_reviewer_by_id(reviewer_id: str) -> dict:
    col = get_users_collection()
    doc = await col.find_one({"_id": _to_object_id(reviewer_id), "role": "reviewer"})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reviewer not found.")
    return doc


async def _load_available_projects() -> list[dict[str, str]]:
    projects: dict[str, str] = {}
    db = get_database()

    # Project master list if present.
    raw_projects = await db["projects"].find(
        {},
        {"_id": 1, "name": 1, "project_name": 1, "project_id": 1, "projectId": 1},
    ).to_list(length=1000)
    for p in raw_projects:
        pid = p.get("project_id") or p.get("projectId") or p.get("_id")
        if pid is None:
            continue
        pid_s = str(pid)
        pname = str(p.get("name") or p.get("project_name") or f"Project {pid_s}")
        projects[pid_s] = pname

    # Fall back to reviewer access mapping history.
    reviewer_project_docs = await get_reviewer_projects_collection().find(
        {},
        {"project_id": 1, "project_name": 1},
    ).to_list(length=1000)
    for p in reviewer_project_docs:
        pid = p.get("project_id")
        if not pid:
            continue
        pid_s = str(pid)
        pname = str(p.get("project_name") or f"Project {pid_s}")
        projects.setdefault(pid_s, pname)

    # Final fallback for local/demo environments.
    for p in mock_store.review_queue_assigned_projects(mock_store.DEMO_REVIEWER_ID):
        pid_s = str(p.get("projectId"))
        if not pid_s:
            continue
        projects.setdefault(pid_s, str(p.get("projectName") or f"Project {pid_s}"))

    rows = [{"project_id": k, "project_name": v} for k, v in projects.items()]
    rows.sort(key=lambda x: x["project_name"].lower())
    return rows


async def get_reviewer_project_access(reviewer_id: str) -> ReviewerProjectAccessResponse:
    _ensure_db()
    reviewer = await _get_reviewer_by_id(reviewer_id)

    mapping_docs = await get_reviewer_projects_collection().find(
        {"reviewer_user_id": reviewer_id},
        {"project_id": 1, "project_name": 1},
    ).to_list(length=1000)
    assigned: dict[str, str] = {}
    for d in mapping_docs:
        pid = d.get("project_id")
        if not pid:
            continue
        pid_s = str(pid)
        assigned[pid_s] = str(d.get("project_name") or f"Project {pid_s}")

    available = await _load_available_projects()
    projects: list[ReviewerProjectAccessItem] = []
    seen: set[str] = set()
    for p in available:
        pid = p["project_id"]
        pname = p["project_name"]
        seen.add(pid)
        projects.append(
            ReviewerProjectAccessItem(
                project_id=pid,
                project_name=pname,
                has_access=pid in assigned,
            )
        )

    for pid, pname in assigned.items():
        if pid in seen:
            continue
        projects.append(
            ReviewerProjectAccessItem(
                project_id=pid,
                project_name=pname,
                has_access=True,
            )
        )

    projects.sort(key=lambda x: x.project_name.lower())
    return ReviewerProjectAccessResponse(
        reviewer_id=reviewer_id,
        reviewer_name=_display_name(reviewer),
        projects=projects,
    )


async def save_reviewer_project_access(
    reviewer_id: str,
    body: ReviewerProjectAccessUpdateRequest,
) -> ReviewerMutationResponse:
    _ensure_db()
    await _get_reviewer_by_id(reviewer_id)

    normalized_ids: list[str] = []
    seen: set[str] = set()
    for pid in body.project_ids:
        pid_s = str(pid).strip()
        if not pid_s or pid_s in seen:
            continue
        seen.add(pid_s)
        normalized_ids.append(pid_s)

    project_name_by_id = {p["project_id"]: p["project_name"] for p in await _load_available_projects()}
    col = get_reviewer_projects_collection()
    await col.delete_many({"reviewer_user_id": reviewer_id})

    if normalized_ids:
        now = _now_utc()
        docs = [
            {
                "reviewer_user_id": reviewer_id,
                "project_id": pid,
                "project_name": project_name_by_id.get(pid, f"Project {pid}"),
                "created_at": now,
                "updated_at": now,
            }
            for pid in normalized_ids
        ]
        await col.insert_many(docs)

    return ReviewerMutationResponse(message="Project access updated.")


async def update_reviewer_status(reviewer_id: str, is_active: bool) -> ReviewerMutationResponse:
    _ensure_db()
    result = await get_users_collection().update_one(
        {"_id": _to_object_id(reviewer_id), "role": "reviewer"},
        {"$set": {"is_active": is_active, "updated_at": _now_utc()}},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reviewer not found.")
    return ReviewerMutationResponse(message="Reviewer status updated.")


async def delete_reviewer(reviewer_id: str) -> ReviewerMutationResponse:
    _ensure_db()
    result = await get_users_collection().delete_one({"_id": _to_object_id(reviewer_id), "role": "reviewer"})
    if result.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reviewer not found.")
    await get_reviewer_projects_collection().delete_many({"reviewer_user_id": reviewer_id})
    return ReviewerMutationResponse(message="Reviewer deleted.")
