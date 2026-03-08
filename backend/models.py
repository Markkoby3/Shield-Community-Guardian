from pydantic import BaseModel, Field
from typing import Literal


# ── Input models ──────────────────────────────────────────────────────────────

class Report(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)
    location: str = Field(..., min_length=1, max_length=100)


class ReportRequest(BaseModel):
    reports: list[Report] = Field(..., max_length=50)
    user_location: str = Field(..., min_length=1, max_length=100)


class SafeCircleMessage(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    group_id: str = Field(..., min_length=1, max_length=50, description="Circle group identifier")


# ── Digest — structured checklist ─────────────────────────────────────────────

class DigestContent(BaseModel):
    summary: str
    steps: list[str] = Field(..., max_length=5)


# ── Output models ─────────────────────────────────────────────────────────────

class AlertResult(BaseModel):
    alert: str
    location: str
    category: str
    severity: Literal["high", "medium", "low"]
    digest: DigestContent
    method: Literal["AI", "fallback"]


class AnalyzeResponse(BaseModel):
    alerts: list[AlertResult]
    processed: int
    filtered_out: int


class MessageResponse(BaseModel):
    status: Literal["stored"]
    message_count: int


class MessagesResponse(BaseModel):
    messages: list[str]
    count: int
    group_id: str
