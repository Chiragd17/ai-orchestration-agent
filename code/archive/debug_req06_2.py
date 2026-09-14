import sys
import os
import datetime
from decimal import Decimal
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)
from engine.data.state import build_user_state
from engine.reconcile import resolve
from engine.simulate import project_recurring_events

state = build_user_state("user_06")
state.events = resolve(state.events)
req_date = datetime.date(2026, 1, 3)
end_date = req_date + datetime.timedelta(days=90)
proj_events = project_recurring_events(state.events, req_date, end_date)
print("Projected events count:", len(proj_events))
for p in proj_events:
    print(p.date, p.amount, p.description)
