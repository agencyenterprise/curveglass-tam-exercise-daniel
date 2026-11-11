"""Skyreach -> Curveglass ETL.

Skyreach (airline code SR) is a new client. Their daily export is a CSV in etl/incoming/.
Your job: implement `transform` so their flights load into Curveglass and show up in the console.

    python -m etl.skyreach etl/incoming/skyreach_export_2026-10-27.csv
    pytest tests/test_skyreach_etl.py

`load` appends: running the ETL twice duplicates snapshots, and a fixed transform won't
overwrite flights loaded by an earlier, buggy run. To reload from a clean database:

    python scripts/initial_load.py && python -m etl.skyreach etl/incoming/skyreach_export_2026-10-27.csv

Target tables (see initial_load/flights.csv and initial_load/booking_snapshots.csv for real examples):

  flights            airline, flight_no, segment, market, dep_date, dep_time_local, equipment, capacity
  booking_snapshots  flight_no*, dep_date*, snapshot_date, seats_sold, avg_fare, loaded_at
                     (* used by `load` to find the flight_id; not stored)

Rules from the Curveglass data contract:
  - segment is directional ("FLN-GRU"); market is the two airports sorted alphabetically ("FLN-GRU")
  - money is in major units (389.90), not cents
  - dates are ISO "YYYY-MM-DD"; times "HH:MM" local
  - v1 prices the economy cabin (Y) only: skip other cabins silently (they're out of scope, not errors)
  - exact duplicate lines in an export are skipped silently
  - rejects are only for in-scope rows that can't be priced, e.g. capacity 0 -> reject it with a reason
  - one flight row per (airline, flight_no, dep_date); one snapshot per flight per snapshot_date
"""
import csv
import sqlite3
import sys
from pathlib import Path

DB = Path(__file__).resolve().parent.parent / "curveglass.db"


def transform(rows: list[dict]) -> tuple[list[dict], list[dict], list[dict]]:
    """Raw export rows -> (flights, snapshots, rejects).

    rejects: [{"row": <raw row>, "reason": "<short_reason>"}]
    """
    flights: list[dict] = []
    snapshots: list[dict] = []
    rejects: list[dict] = []
    # TODO: implement
    return flights, snapshots, rejects


# ----------------------------------------------------------------------------
# Below this line is done for you.
def load(flights: list[dict], snapshots: list[dict], db: Path = DB) -> None:
    con = sqlite3.connect(db)
    next_id = (con.execute("SELECT MAX(flight_id) FROM flights").fetchone()[0] or 0) + 1
    ids = {}
    for f in flights:
        key = (f["flight_no"], f["dep_date"])
        existing = con.execute("SELECT flight_id FROM flights WHERE flight_no = ? AND dep_date = ?", key).fetchone()
        if existing:
            ids[key] = existing[0]
            continue
        ids[key] = next_id
        con.execute("INSERT INTO flights (flight_id, airline, flight_no, segment, market, dep_date, dep_time_local,"
                    " equipment, capacity) VALUES (?,?,?,?,?,?,?,?,?)",
                    (next_id, f["airline"], f["flight_no"], f["segment"], f["market"], f["dep_date"],
                     f["dep_time_local"], f["equipment"], f["capacity"]))
        next_id += 1
    for s in snapshots:
        con.execute("INSERT INTO booking_snapshots (flight_id, snapshot_date, seats_sold, avg_fare, loaded_at)"
                    " VALUES (?,?,?,?,?)",
                    (ids[(s["flight_no"], s["dep_date"])], s["snapshot_date"], s["seats_sold"], s["avg_fare"],
                     s["loaded_at"]))
    con.commit()


def main(path: str) -> None:
    with open(path, newline="") as fh:
        rows = list(csv.DictReader(fh))
    flights, snapshots, rejects = transform(rows)
    load(flights, snapshots)
    print(f"read {len(rows)} rows -> {len(flights)} flights, {len(snapshots)} snapshots, {len(rejects)} rejects")
    for r in rejects:
        print("  rejected:", r["reason"], r["row"])


if __name__ == "__main__":
    main(sys.argv[1])
