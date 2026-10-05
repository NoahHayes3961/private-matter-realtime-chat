from datetime import datetime, timezone

from matter_chat.workflow import DeadlineCheck, MatterWorkflow, Urgency


class RecordingRealtime:
    def __init__(self) -> None:
        self.published: list[dict[str, object]] = []

    def publish(
        self,
        channel: str,
        event: str,
        data: dict[str, object],
        account_id: str,
        idempotency_key: str,
    ) -> dict[str, object]:
        self.published.append(
            {
                "channel": channel,
                "event": event,
                "data": data,
                "account_id": account_id,
                "idempotency_key": idempotency_key,
            }
        )
        return {}


def test_deadline_inside_48_hours_notifies_the_matter_room() -> None:
    realtime = RecordingRealtime()
    service = MatterWorkflow(realtime)
    request = DeadlineCheck(
        matter_id="M-1042",
        account_id="firm-7",
        checked_at=datetime(2026, 9, 5, 9, 0, tzinfo=timezone.utc),
        deadline_at=datetime(2026, 9, 7, 8, 59, tzinfo=timezone.utc),
    )

    result = service.check_deadline(request)

    assert result.urgency is Urgency.follow_up_due
    assert result.notification_sent is True
    assert realtime.published[0]["channel"] == "matter-M-1042"
    assert realtime.published[0]["event"] == "deadline.follow_up_due"


def test_deadline_beyond_48_hours_stays_quiet() -> None:
    realtime = RecordingRealtime()
    service = MatterWorkflow(realtime)
    request = DeadlineCheck(
        matter_id="M-1042",
        account_id="firm-7",
        checked_at=datetime(2026, 9, 5, 9, 0, tzinfo=timezone.utc),
        deadline_at=datetime(2026, 9, 7, 9, 1, tzinfo=timezone.utc),
    )

    result = service.check_deadline(request)

    assert result.urgency is Urgency.routine
    assert result.notification_sent is False
    assert realtime.published == []
