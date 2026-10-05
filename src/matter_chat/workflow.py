from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Protocol

from pydantic import AwareDatetime, BaseModel, Field


class RealtimePort(Protocol):
    def create_channel(self, channel: str, idempotency_key: str) -> dict[str, Any]:
        pass

    def issue_token(self, client_id: str, channel: str) -> dict[str, Any]:
        pass

    def publish(
        self,
        channel: str,
        event: str,
        data: dict[str, Any],
        account_id: str,
        idempotency_key: str,
    ) -> dict[str, Any]:
        pass


class Urgency(str, Enum):
    routine = "routine"
    follow_up_due = "follow_up_due"
    overdue = "overdue"


class MatterIntake(BaseModel):
    matter_id: str = Field(min_length=1, pattern=r"^[A-Za-z0-9_-]+$")
    client_id: str = Field(min_length=1)
    account_id: str = Field(min_length=1)
    summary: str = Field(min_length=1, max_length=500)
    deadline_at: AwareDatetime


class SignedDocumentDelivery(BaseModel):
    matter_id: str = Field(min_length=1, pattern=r"^[A-Za-z0-9_-]+$")
    account_id: str = Field(min_length=1)
    document_id: str = Field(min_length=1)
    download_url: str = Field(pattern=r"^https://")
    expires_at: AwareDatetime


class DeadlineCheck(BaseModel):
    matter_id: str = Field(min_length=1, pattern=r"^[A-Za-z0-9_-]+$")
    account_id: str = Field(min_length=1)
    deadline_at: AwareDatetime
    checked_at: AwareDatetime


class IntakeResult(BaseModel):
    channel: str
    token: str


class FollowUpResult(BaseModel):
    urgency: Urgency
    notification_sent: bool


def matter_channel(matter_id: str) -> str:
    return f"matter-{matter_id}"


def deadline_urgency(deadline_at: datetime, checked_at: datetime) -> Urgency:
    deadline = deadline_at.astimezone(timezone.utc)
    checked = checked_at.astimezone(timezone.utc)
    seconds_left = (deadline - checked).total_seconds()
    if seconds_left <= 0:
        return Urgency.overdue
    if seconds_left <= 48 * 60 * 60:
        return Urgency.follow_up_due
    return Urgency.routine


class MatterWorkflow:
    def __init__(self, realtime: RealtimePort) -> None:
        self.realtime = realtime

    def intake(self, request: MatterIntake) -> IntakeResult:
        channel = matter_channel(request.matter_id)
        self.realtime.create_channel(channel, f"matter-create:{request.matter_id}")
        token_data = self.realtime.issue_token(request.client_id, channel)
        self.realtime.publish(
            channel,
            "matter.intake_received",
            {"matter_id": request.matter_id, "summary": request.summary},
            request.account_id,
            f"matter-intake:{request.matter_id}",
        )
        return IntakeResult(channel=channel, token=str(token_data["token"]))

    def deliver_signed_document(self, request: SignedDocumentDelivery) -> None:
        self.realtime.publish(
            matter_channel(request.matter_id),
            "document.signed_ready",
            {
                "document_id": request.document_id,
                "download_url": request.download_url,
                "expires_at": request.expires_at.isoformat(),
            },
            request.account_id,
            f"signed-document:{request.matter_id}:{request.document_id}",
        )

    def check_deadline(self, request: DeadlineCheck) -> FollowUpResult:
        urgency = deadline_urgency(request.deadline_at, request.checked_at)
        should_notify = urgency is not Urgency.routine
        if should_notify:
            self.realtime.publish(
                matter_channel(request.matter_id),
                "deadline.follow_up_due",
                {"deadline_at": request.deadline_at.isoformat(), "urgency": urgency.value},
                request.account_id,
                f"deadline:{request.matter_id}:{request.deadline_at.isoformat()}:{urgency.value}",
            )
        return FollowUpResult(urgency=urgency, notification_sent=should_notify)
