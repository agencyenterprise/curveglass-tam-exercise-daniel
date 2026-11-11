# Curveglass TAM pairing exercise

You're a Technical Account Manager for **Curveglass**, a dynamic-pricing engine for airlines.
In this 90-minute session you'll work through five tasks a TAM handles in a normal week. We care about
how you work: reading unfamiliar code and data, asking good questions, checking your own results.
Use any tools you like (docs, AI assistants, your own scripts). Please think out loud.

All data is synthetic. Airlines, flights and numbers are made up.

## How Curveglass works

```
airline export ──► ETL ──► database ──► pricing engine (daily run) ──► recommendations ──► console / airline's system
                                          several models score each       one winner per flight;
                                          flight; guardrails cap them     some auto-published
```

* A **run** scores every future flight once a day (06:00 local). The engine is in `engine/`.
* Each **model** can suggest a price change for a flight (a signed fraction: `0.18` = +18%, `-0.15` = -15%).
  The highest-priority model wins: `EVENT_UPLIFT > PACE_SURGE > MARKET_GAP > LOW_DEMAND_DISCOUNT`.
* **Guardrails** limit the winner, e.g. no change bigger than ±25%. `raw_offer_value` is what the model asked for;
  `offer_value` is what we recommend after guardrails.
* **Auto-approval** sends recommendations straight to the airline's system on some segments; every message sent is
  logged in the `publications` table. The rest wait in the console's review queue for an analyst.

| Term | Meaning |
| --- | --- |
| segment | Directional origin-destination: `POA-GRU` ≠ `GRU-POA` |
| market | Non-directional, airports sorted alphabetically: `GRU-POA` |
| load factor (LF) | seats sold ÷ capacity |
| snapshot | The airline's daily count of seats sold and average fare per flight |
| console | The Curveglass web UI (`web/`), on http://localhost:3000 once running |

## What's in here

| Path | What it is |
| --- | --- |
| `initial_load/` | Seed data, **used only by the first load**: client ZZ's flights and booking snapshots, competitor fares, events, users, role permissions, guardrail settings. After the first load, everything lives in the database |
| `scripts/initial_load.py` | The first load: builds `curveglass.db` from `initial_load/` and runs the pricing engine for 25, 26 and 27 Oct. Running it again wipes the database and starts over |
| `engine/` | The pricing engine: inputs, models, broker, guardrails, approval and publishing. Re-run one day with `python -m engine.run 2026-10-27` |
| `etl/` | ETL for a new client, **Skyreach (SR)**, and their first raw export in `etl/incoming/` |
| `api/main.py` | FastAPI service the console reads from (users and permissions included) |
| `web/` | The analyst console (Next.js) |
| `tests/` | Tests for the ETL |

For SQL use whatever you like: `sqlite3 curveglass.db`, DuckDB, DBeaver, pandas.

---

# Tasks

Work through them in order. Your interviewer will tell you when to move on; finishing everything is not the goal.

## Task 0 — Get it running (10 min)

Get the API and the console running on your machine. Needs Python 3.11+ and Node 18.18+.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python scripts/initial_load.py                # first load: database + three pricing runs

uvicorn api.main:app --reload --port 8000     # terminal 1, from the repo root: API
cd web && npm install && npm run dev          # terminal 2: console on http://localhost:3000
```

Done when http://localhost:3000 shows the list of pricing runs. If port 8000 is taken, run the API on another port
and start the console with `API_URL=http://localhost:<port> npm run dev`.

## Task 1 — Load Skyreach's first export (25 min)

Skyreach just sent their first daily export: `etl/incoming/skyreach_export_2026-10-27.csv`.
Implement `transform` in `etl/skyreach.py` so their flights load into Curveglass.

Done when `pytest` passes and Skyreach's flights show up on the console's Flights page (filter: SR).
The rules for this export (duplicates, other cabins, rows with no capacity, units) were already agreed with
Skyreach and are documented in the data contract at the top of `etl/skyreach.py`.

## Task 2 — "Which number is right?" (20 min)

Message from ZZ's revenue analyst:

> The console says ZZ1234 got +38%, but our reservation system received +25%. Which one is right,
> and why are they different?

Find out, explain it, and fix it.

## Task 3 — "Explain this recommendation" (20 min)

Message from ZZ's Head of Pricing:

> ZZ1517 GRU-SSA on 3 Nov is one of our best sellers. Your 26 Oct run recommended +17%; the 27 Oct run says
> -15% because of low demand. Explain.

Use the console and the database. You don't have to fix anything: tell us what happened and what you'd do next.

## Task 4 — Hide Guardrails from analysts (12 min)

ZZ wants only admins to see guardrail settings. Make sure analysts can no longer see the Guardrails page:
not in the menu, and not by typing the URL. Admins keep access. Use the user switcher in the header to test.
