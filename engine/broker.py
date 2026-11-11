"""Pick one winning suggestion per flight."""

# Highest priority first.
PRIORITY = ["EVENT_UPLIFT", "PACE_SURGE", "MARKET_GAP", "LOW_DEMAND_DISCOUNT"]


def rank(candidates: dict[str, float]) -> list[tuple[str, float]]:
    """Candidates ordered by model priority; the first one is the winner."""
    return sorted(candidates.items(), key=lambda kv: PRIORITY.index(kv[0]))
