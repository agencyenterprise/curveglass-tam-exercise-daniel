"""Approval and publishing to the airline's system."""
from datetime import datetime, timezone

from engine.guardrails import GuardrailConfig


def approval_status(segment: str, change: float, cfg: GuardrailConfig) -> str:
    if cfg.auto_approve_enabled and segment in cfg.auto_approve_segments \
            and abs(change) <= cfg.auto_approve_max_abs_change:
        return "published"
    return "pending_review"


def publish(con, run_id: str, flight_id: int, change: float) -> None:
    """Send an approved price change to the airline. Every message sent is logged in `publications`."""
    con.execute("INSERT INTO publications (run_id, flight_id, price_change, sent_at) VALUES (?,?,?,?)",
                (run_id, flight_id, change, datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")))
