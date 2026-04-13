from fastapi import APIRouter, HTTPException, Query

from app.service import mock_store
from app.schema.schemas import InboxThread, InboxThreadsResponse, MarkReadResponse, UnreadCountResponse

router = APIRouter(prefix="/inbox", tags=["inbox"])


@router.get(
    "/unread-count",
    response_model=UnreadCountResponse,
    response_model_by_alias=True,
)
def get_unread_count() -> UnreadCountResponse:
    """Badge total; same aggregate as dashboard unreadMessages when in sync."""
    return UnreadCountResponse(unread_messages=mock_store.total_unread_messages())


@router.get(
    "/threads",
    response_model=InboxThreadsResponse,
    response_model_by_alias=True,
)
def get_threads(
    unread_only: bool = Query(default=False, alias="unreadOnly"),
) -> InboxThreadsResponse:
    """Q&A Inbox thread list."""
    raw = mock_store.inbox_threads(unread_only=unread_only)
    items = [InboxThread.model_validate(x) for x in raw]
    return InboxThreadsResponse(items=items, total=len(items))


@router.post(
    "/threads/{thread_id}/read",
    response_model=MarkReadResponse,
    response_model_by_alias=True,
)
def mark_thread_read(thread_id: str) -> MarkReadResponse:
    """Mark thread read; updates global unread aggregate for demo store."""
    threads = mock_store.inbox_threads(unread_only=False)
    if not any(t["threadId"] == thread_id for t in threads):
        raise HTTPException(status_code=404, detail="Thread not found")
    total = mock_store.mark_thread_read(thread_id)
    return MarkReadResponse(thread_id=thread_id, unread_messages=total)
