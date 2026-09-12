import unittest
import datetime
from decimal import Decimal
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from engine.data.state import Event
from engine.reconcile import resolve, filter_for_forecast

def make_event(event_id, amount, date_str, type="expense", direction="debit", status="pending", linked_id=None, desc="desc"):
    return Event(
        event_id=event_id,
        date=datetime.datetime.strptime(date_str, "%Y-%m-%d").date(),
        amount=Decimal(str(amount)),
        type=type,
        description=desc,
        direction=direction,
        recurring=False,
        interval=None,
        flexible=False,
        status=status,
        linked_event_id=linked_id
    )

class TestReconcile(unittest.TestCase):
    def test_cancellation_wins(self):
        # Scenario 1: explicit cancellation overrides original
        # E1 is original, E2 cancels it.
        e1 = make_event("event_01", 100, "2025-01-01", status="pending")
        e2 = make_event("event_02", 100, "2025-01-01", status="cancelled", linked_id="event_01")
        
        resolved = resolve([e1, e2])
        self.assertEqual(len(resolved), 1)
        self.assertEqual(resolved[0].event_id, "event_02")
        self.assertEqual(resolved[0].status, "cancelled")

    def test_newer_wins(self):
        # Scenario 2: newer record from same source wins (based on event_id suffix if fully ambiguous)
        e1 = make_event("event_01", 100, "2025-01-01", status="pending")
        e2 = make_event("event_02", 100, "2025-01-01", status="pending")
        
        resolved = resolve([e1, e2])
        self.assertEqual(len(resolved), 1)
        self.assertEqual(resolved[0].event_id, "event_02")

    def test_settled_wins(self):
        # Scenario 3: settled wins over estimate
        e1 = make_event("event_01", 100, "2025-01-01", status="settled")
        e2 = make_event("event_02", 100, "2025-01-01", status="pending")
        
        resolved = resolve([e1, e2])
        self.assertEqual(len(resolved), 1)
        self.assertEqual(resolved[0].event_id, "event_01")

    def test_ambiguous_safer_wins(self):
        # Scenario 4: safer interpretation wins
        # Expense of 100 vs Expense of 150 (safer is 150, lower safe-to-spend)
        e1 = make_event("event_01", 100, "2025-01-01", type="expense", direction="debit")
        e2 = make_event("event_02", 150, "2025-01-01", type="expense", direction="debit", linked_id="event_01")
        
        resolved = resolve([e1, e2])
        self.assertEqual(len(resolved), 1)
        self.assertEqual(resolved[0].amount, Decimal("150"))
        
        # Income of 100 vs Income of 50 (safer is 50)
        e3 = make_event("event_03", 100, "2025-01-01", type="income", direction="credit")
        e4 = make_event("event_04", 50, "2025-01-01", type="income", direction="credit", linked_id="event_03")
        
        resolved2 = resolve([e3, e4])
        self.assertEqual(len(resolved2), 1)
        self.assertEqual(resolved2[0].amount, Decimal("50"))

    def test_duplicate_collapse(self):
        # Scenario 5: duplicate collapsing (matching amount+date+desc) without linked_id
        e1 = make_event("event_01", 100, "2025-01-01", desc="Netflix")
        e2 = make_event("event_02", 100, "2025-01-01", desc="Netflix")
        
        resolved = resolve([e1, e2])
        self.assertEqual(len(resolved), 1)
        
    def test_forecast_filter(self):
        e1 = make_event("event_01", 100, "2025-01-01", status="cancelled")
        e2 = make_event("event_02", 100, "2025-01-01", status="failed")
        e3 = make_event("event_03", 100, "2025-01-01", type="income", direction="credit", status="pending")
        e4 = make_event("event_04", 100, "2025-01-01", type="expense", direction="debit", status="pending")
        
        filtered = filter_for_forecast([e1, e2, e3, e4])
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].event_id, "event_04") # expense pending is kept, others removed

if __name__ == '__main__':
    unittest.main()
