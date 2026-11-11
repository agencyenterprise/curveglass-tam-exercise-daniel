"""Guardrails limit the winning recommendation before anyone sees it."""
from dataclasses import dataclass


@dataclass
class GuardrailConfig:
    pct_hard_cap: float
    auto_approve_enabled: bool
    auto_approve_segments: list[str]
    auto_approve_max_abs_change: float
    blackout_dates: list[str]


def load_config(con, airline: str = "ZZ") -> GuardrailConfig:
    row = con.execute("SELECT pct_hard_cap, auto_approve_enabled, auto_approve_segments, "
                      "auto_approve_max_abs_change, blackout_dates FROM guardrail_config WHERE airline = ?",
                      (airline,)).fetchone()
    return GuardrailConfig(row[0], bool(row[1]), row[2].split(";"), row[3], row[4].split(";"))


def apply_guardrails(rec, cfg: GuardrailConfig) -> float:
    """Return the price change after guardrails, and record which guardrail applied (if any)."""
    value = rec.raw_offer_value
    if abs(value) > cfg.pct_hard_cap:
        rec.guardrail_applied = "pct_cap"
        value = cfg.pct_hard_cap if value > 0 else -cfg.pct_hard_cap
    return value
