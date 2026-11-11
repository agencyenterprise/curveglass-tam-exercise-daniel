"""Curveglass pricing engine (exercise version).

    python -m engine.run 2026-10-27        # price every future flight as of that day

Flow for one run (engine/run.py):
  1. inputs     latest booking snapshot per flight, 7-day pickup, competitor fare, events
  2. models     each model may suggest a price change for a flight        (engine/models.py)
  3. broker     the highest-priority suggestion wins                       (engine/broker.py)
  4. guardrails cap the winner's change                                    (engine/guardrails.py)
  5. approval   auto-approve on configured segments, else pending review   (engine/approval.py)
  6. publish    approved changes are sent to the airline's system          (engine/approval.py)
  7. save       every suggestion is stored in `recommendations`
"""
