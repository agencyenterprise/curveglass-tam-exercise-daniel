"""Pricing models. Each returns a suggested price change (signed fraction, 0.18 = +18%) or None."""
from dataclasses import dataclass


@dataclass
class FlightInputs:
    flight_id: int
    flight_no: str
    segment: str
    market: str
    dep_date: str
    capacity: int
    seats_sold: int          # from the snapshot the engine uses for this run
    pickup_7d: int           # seats sold in the last 7 days
    avg_fare: float
    competitor_fare: float | None
    event_uplift: float | None

    @property
    def load_factor(self) -> float:
        return self.seats_sold / self.capacity if self.capacity else 0.0


def event_uplift(f: FlightInputs) -> float | None:
    """A known event in the market on the departure date."""
    return f.event_uplift


def pace_surge(f: FlightInputs) -> float | None:
    """Selling fast and already fairly full: raise the price."""
    if f.load_factor > 0.55 and f.pickup_7d >= 8:
        return round(min(0.20, 0.04 + f.pickup_7d / 200), 2)
    return None


def market_gap(f: FlightInputs) -> float | None:
    """Our fare is far from the competitor's: move half of the gap, within limits."""
    if not f.competitor_fare or not f.avg_fare:
        return None
    gap = (f.competitor_fare - f.avg_fare) / f.avg_fare
    if abs(gap) < 0.05:
        return None
    return round(max(-0.08, min(0.10, gap / 2)), 2)


def low_demand_discount(f: FlightInputs) -> float | None:
    """Very empty flight: discount to stimulate demand."""
    if f.load_factor < 0.20:
        return -0.15
    if f.load_factor < 0.25:
        return -0.08
    return None


MODELS = {
    "EVENT_UPLIFT": event_uplift,
    "PACE_SURGE": pace_surge,
    "MARKET_GAP": market_gap,
    "LOW_DEMAND_DISCOUNT": low_demand_discount,
}
