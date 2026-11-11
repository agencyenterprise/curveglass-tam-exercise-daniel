"""First load: build curveglass.db from initial_load/*.csv, then run the pricing engine
for the last three days so the console has recommendations to show.

    python scripts/initial_load.py

Run it once at setup. Running it again wipes the database (including anything an ETL loaded)
and rebuilds it from initial_load/.
"""
import csv
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from engine.run import run_pricing  # noqa: E402

DB = ROOT / "curveglass.db"
SEED = ROOT / "initial_load"
TABLES = ["flights", "booking_snapshots", "competitor_fares", "events",
          "users", "role_permissions", "guardrail_config"]
RUN_DATES = ["2026-10-25", "2026-10-26", "2026-10-27"]


def typed(v):
    for cast in (int, float):
        try:
            return cast(v)
        except ValueError:
            pass
    return v


if DB.exists():
    DB.unlink()
con = sqlite3.connect(DB)
for t in TABLES:
    with open(SEED / f"{t}.csv") as fh:
        rows = list(csv.DictReader(fh))
    cols = list(rows[0].keys())
    con.execute(f"CREATE TABLE {t} ({', '.join(cols)})")
    con.executemany(f"INSERT INTO {t} VALUES ({', '.join('?' * len(cols))})",
                    [[typed(r[c]) for c in cols] for r in rows])
    print(f"{t:20s} {len(rows):5d} rows")

con.executescript("""
    CREATE TABLE recommendations (run_id, flight_id, model_code, flagged, winner, raw_offer_value,
                                  offer_value, guardrail_applied, seats_sold_at_run, lf_at_run, status);
    CREATE TABLE publications (run_id, flight_id, price_change, sent_at);
    CREATE TABLE job_runs (run_id, started_at, finished_at, status, flights_with_recs, recs_written,
                           guardrail_binds);
""")
for d in RUN_DATES:
    print("pricing run", run_pricing(con, d))
print(f"-> {DB.name}")
