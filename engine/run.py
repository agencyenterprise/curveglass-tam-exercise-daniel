"""One pricing run: score every future flight as of `run_date` and store the recommendations.

    python -m engine.run 2026-10-27

Re-running a date replaces that run's recommendations. Publications are a log of messages
actually sent to the airline, so a re-run that publishes sends (and logs) them again.
"""
import sqlite3
import sys
from dataclasses import asdict, dataclass
from datetime import date, timedelta
from pathlib import Path

from engine.approval import approval_status, publish
from engine.broker import rank
from engine.guardrails import apply_guardrails, load_config
from engine.models import MODELS, FlightInputs

DB = Path(__file__).resolve().parent.parent / "curveglass.db"


@dataclass
class Recommendation:
    run_id: str
    flight_id: int
    model_code: str
    flagged: int
    winner: int
    raw_offer_value: float      # what the model asked for
    offer_value: float          # what we recommend, after guardrails
    guardrail_applied: str
    seats_sold_at_run: int
    lf_at_run: float
    status: str


# The engine uses the most recently loaded snapshot for each flight and day.
SNAPSHOT_SQL = """
    SELECT seats_sold, avg_fare FROM booking_snapshots
    WHERE flight_id = ? AND snapshot_date = ?
    ORDER BY loaded_at DESC LIMIT 1
"""


def load_inputs(con, run_date: str) -> list[FlightInputs]:
    week_ago = (date.fromisoformat(run_date) - timedelta(days=7)).isoformat()
    out = []
    for fid, no, seg, mkt, dep, cap in con.execute(
            "SELECT flight_id, flight_no, segment, market, dep_date, capacity FROM flights "
            "WHERE airline = 'ZZ' AND dep_date > ? ORDER BY flight_id", (run_date,)).fetchall():
        today = con.execute(SNAPSHOT_SQL, (fid, run_date)).fetchone()
        before = con.execute(SNAPSHOT_SQL, (fid, week_ago)).fetchone()
        if not today:
            continue
        comp = con.execute("SELECT competitor_fare FROM competitor_fares WHERE flight_id = ?", (fid,)).fetchone()
        event = con.execute("SELECT MAX(uplift) FROM events WHERE market = ? AND ? BETWEEN date_from AND date_to",
                            (mkt, dep)).fetchone()
        out.append(FlightInputs(fid, no, seg, mkt, dep, cap, today[0], today[0] - (before[0] if before else 0),
                                today[1], comp[0] if comp else None, event[0]))
    return out


def run_pricing(con, run_date: str) -> str:
    run_id = f"R-{run_date.replace('-', '')}-0600"
    con.execute("DELETE FROM recommendations WHERE run_id = ?", (run_id,))
    con.execute("DELETE FROM job_runs WHERE run_id = ?", (run_id,))
    cfg = load_config(con)
    recs: list[Recommendation] = []
    flights_with_recs = binds = 0

    for f in load_inputs(con, run_date):
        candidates = {code: v for code, model in MODELS.items() if (v := model(f)) is not None}
        if not candidates:
            continue
        flights_with_recs += 1
        for i, (code, value) in enumerate(rank(candidates)):
            rec = Recommendation(run_id, f.flight_id, code, 1, int(i == 0), value, value, "",
                                 f.seats_sold, round(f.load_factor, 3), "")
            if rec.winner:
                final = apply_guardrails(rec, cfg)
                rec.offer_value = final
                binds += bool(rec.guardrail_applied)
                rec.status = approval_status(f.segment, final, cfg)
                if rec.status == "published":
                    publish(con, run_id, f.flight_id, final)
            recs.append(rec)

    con.executemany("INSERT INTO recommendations VALUES (:run_id, :flight_id, :model_code, :flagged, :winner, "
                    ":raw_offer_value, :offer_value, :guardrail_applied, :seats_sold_at_run, :lf_at_run, :status)",
                    [asdict(r) for r in recs])
    con.execute("INSERT INTO job_runs VALUES (?,?,?,?,?,?,?)",
                (run_id, f"{run_date}T09:00:00Z", f"{run_date}T09:14:00Z", "success",
                 flights_with_recs, len(recs), binds))
    con.commit()
    return run_id


if __name__ == "__main__":
    con = sqlite3.connect(DB)
    print("wrote", run_pricing(con, sys.argv[1]))
