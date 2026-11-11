"""Curveglass console API (exercise version).

Run:  uvicorn api.main:app --reload --port 8000
Needs curveglass.db  (python scripts/initial_load.py)

Auth is simplified: the console sends the logged-in user id in the X-User header.
Users, role permissions and guardrail settings live in the database (tables users,
role_permissions, guardrail_config), loaded by scripts/initial_load.py.
"""
import sqlite3
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "curveglass.db"
DEFAULT_USER = "ana.souza"

app = FastAPI(title="Curveglass console API (exercise)")


# ---------------------------------------------------------------- data access
def q(sql: str, *args) -> list[dict]:
    if not DB.exists():
        raise HTTPException(500, "curveglass.db not found - run: python scripts/initial_load.py")
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    try:
        return [dict(r) for r in con.execute(sql, args)]
    finally:
        con.close()


# ---------------------------------------------------------------- auth
def current_user(x_user: str | None = Header(default=None)) -> dict:
    rows = q("SELECT id, name, role FROM users WHERE id = ?", x_user or DEFAULT_USER)
    if not rows:
        raise HTTPException(401, f"unknown user {x_user}")
    user = rows[0]
    perms = q("SELECT permission FROM role_permissions WHERE role = ?", user["role"])
    return {**user, "permissions": [p["permission"] for p in perms]}


def require(permission: str):
    def check(user: dict = Depends(current_user)) -> dict:
        if permission not in user["permissions"]:
            raise HTTPException(403, f"{user['id']} ({user['role']}) lacks {permission}")
        return user
    return check


@app.get("/api/me")
def me(user: dict = Depends(current_user)):
    return user


@app.get("/api/users")
def users():
    return q("SELECT id, name, role FROM users ORDER BY name")


# ---------------------------------------------------------------- runs & queue
@app.get("/api/runs", dependencies=[Depends(require("runs:read"))])
def runs():
    return q("SELECT * FROM job_runs ORDER BY run_id DESC")


@app.get("/api/runs/{run_id}/recommendations", dependencies=[Depends(require("queue:read"))])
def run_recommendations(run_id: str, status: str | None = None):
    """The review queue: the winning recommendation per flight for a run."""
    sql = """
        SELECT f.flight_no, f.segment, f.dep_date, r.model_code,
               r.raw_offer_value, r.offer_value, r.guardrail_applied, r.status
        FROM recommendations r JOIN flights f USING (flight_id)
        WHERE r.run_id = ? AND r.winner = 1
    """
    args: list = [run_id]
    if status:
        sql += " AND r.status = ?"
        args.append(status)
    return q(sql + " ORDER BY f.dep_date, f.flight_no", *args)


# ---------------------------------------------------------------- flights
LATEST_SNAPSHOT = """
    SELECT s.* FROM booking_snapshots s
    WHERE s.loaded_at = (SELECT MAX(loaded_at) FROM booking_snapshots x
                         WHERE x.flight_id = s.flight_id AND x.snapshot_date = s.snapshot_date)
"""


@app.get("/api/flights", dependencies=[Depends(require("flights:read"))])
def flights(airline: str | None = None, search: str | None = None):
    sql = f"""
        SELECT f.*, s.snapshot_date, s.seats_sold
        FROM flights f
        LEFT JOIN ({LATEST_SNAPSHOT}) s ON s.flight_id = f.flight_id
         AND s.snapshot_date = (SELECT MAX(snapshot_date) FROM booking_snapshots WHERE flight_id = f.flight_id)
        WHERE 1 = 1
    """
    args: list = []
    if airline:
        sql += " AND f.airline = ?"
        args.append(airline)
    if search:
        sql += " AND (f.flight_no LIKE ? OR f.segment LIKE ?)"
        args += [f"%{search}%", f"%{search}%"]
    return q(sql + " ORDER BY f.dep_date, f.dep_time_local", *args)


@app.get("/api/flights/{flight_no}", dependencies=[Depends(require("flights:read"))])
def flight(flight_no: str):
    rows = q("SELECT * FROM flights WHERE flight_no = ?", flight_no)
    if not rows:
        raise HTTPException(404, f"unknown flight {flight_no}")
    f = rows[0]
    return {
        "flight": f,
        # one row per day: the engine uses the most recently loaded snapshot
        "snapshots": q(f"SELECT snapshot_date, seats_sold, avg_fare FROM ({LATEST_SNAPSHOT}) "
                       "WHERE flight_id = ? ORDER BY snapshot_date", f["flight_id"]),
        # winners only: never expose losing candidates to the client
        "recommendations": q("SELECT run_id, model_code, raw_offer_value, offer_value, guardrail_applied, status, "
                             "seats_sold_at_run, lf_at_run FROM recommendations "
                             "WHERE flight_id = ? AND winner = 1 ORDER BY run_id DESC", f["flight_id"]),
        # what was actually sent to the airline's system
        "publications": q("SELECT run_id, price_change, sent_at FROM publications WHERE flight_id = ? "
                          "ORDER BY run_id DESC", f["flight_id"]),
    }


# ---------------------------------------------------------------- guardrails
@app.get("/api/guardrails", dependencies=[Depends(require("guardrails:read"))])
def guardrails():
    g = q("SELECT * FROM guardrail_config WHERE airline = 'ZZ'")[0]
    return {
        "airline": g["airline"], "version": g["version"], "updated_at": g["updated_at"],
        "updated_by": g["updated_by"], "pct_hard_cap": g["pct_hard_cap"],
        "auto_approve": {"enabled": bool(g["auto_approve_enabled"]),
                         "segments": g["auto_approve_segments"].split(";"),
                         "max_abs_change": g["auto_approve_max_abs_change"]},
        "blackout_dates": g["blackout_dates"].split(";"),
    }
