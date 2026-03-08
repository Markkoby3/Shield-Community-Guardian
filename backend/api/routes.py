from fastapi import APIRouter, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from backend.models import (
    ReportRequest, AnalyzeResponse,
    SafeCircleMessage, MessageResponse, MessagesResponse,
)
from backend.services.pipeline import process_reports
from backend.services.rss_ingestor import ingest_rss_feeds
from backend.core.security import encrypt, decrypt
from backend.api.dependencies import require_api_key
from backend.db.database import (
    save_alert, search_alerts, get_stats,
    save_message, get_messages, get_message_count,
)

limiter = Limiter(key_func=get_remote_address)
router = APIRouter()


# ── Alerts ────────────────────────────────────────────────────────────────────

@router.post("/analyze", response_model=AnalyzeResponse)
@limiter.limit("20/minute")
def analyze(
    request: Request,
    data: ReportRequest,
    _: str = Depends(require_api_key),
) -> AnalyzeResponse:
    response = process_reports(data.reports, data.user_location)
    for alert in response.alerts:
        save_alert(alert.model_dump())
    return response


@router.get("/search")
@limiter.limit("30/minute")
def search(
    request: Request,
    keyword: str,
    limit: int = 50,
    _: str = Depends(require_api_key),
) -> list:
    keyword = keyword.strip()
    if not keyword:
        return []
    return search_alerts(keyword, limit)


@router.get("/stats")
@limiter.limit("30/minute")
def stats(request: Request) -> dict:
    return get_stats()


@router.post("/ingest/rss")
@limiter.limit("5/minute")
def ingest_rss(request: Request, _: str = Depends(require_api_key)) -> dict:
    return ingest_rss_feeds()


# ── Safe Circle ───────────────────────────────────────────────────────────────

@router.post("/safe-circle", response_model=MessageResponse)
@limiter.limit("10/minute")
def send_message(
    request: Request,
    msg: SafeCircleMessage,
    _: str = Depends(require_api_key),
) -> MessageResponse:
    ciphertext = encrypt(msg.message)
    save_message(msg.group_id, ciphertext)
    count = get_message_count(msg.group_id)
    return MessageResponse(status="stored", message_count=count)


@router.get("/safe-circle/{group_id}", response_model=MessagesResponse)
@limiter.limit("10/minute")
def get_circle_messages(
    request: Request,
    group_id: str,
    _: str = Depends(require_api_key),
) -> MessagesResponse:
    raw = get_messages(group_id)
    decrypted = [decrypt(m) for m in raw]
    return MessagesResponse(messages=decrypted, count=len(decrypted), group_id=group_id)
