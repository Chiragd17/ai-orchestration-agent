import unittest
from decimal import Decimal
import datetime

from engine.candidates import Candidate
from engine.rank import rank

class TestRank(unittest.TestCase):
    def test_completes_by_deadline_wins(self):
        # A plan completing on time MUST beat a cheaper plan that completes late
        c_late = Candidate(
            method="wait",
            payment_plan=[(datetime.date(2026, 12, 1), Decimal("100"))],
            total_paid=Decimal("100"),
            completes_by_deadline=False
        )
        c_on_time = Candidate(
            method="installments",
            payment_plan=[(datetime.date(2026, 10, 1), Decimal("60")), (datetime.date(2026, 11, 1), Decimal("60"))],
            total_paid=Decimal("120"), # Costs more
            completes_by_deadline=True
        )
        winner = rank([c_late, c_on_time])
        self.assertEqual(winner.method, "installments")

    def test_no_spending_changes_wins(self):
        # Even if cheaper, a plan with spending changes loses to a plan without them (assuming both complete on time)
        c_changes = Candidate(
            method="full_payment",
            payment_plan=[(datetime.date(2026, 10, 1), Decimal("100"))],
            total_paid=Decimal("100"),
            spending_changes=["stop:sub"],
            completes_by_deadline=True
        )
        c_no_changes = Candidate(
            method="installments",
            payment_plan=[(datetime.date(2026, 10, 1), Decimal("60")), (datetime.date(2026, 11, 1), Decimal("60"))],
            total_paid=Decimal("120"), # Costs more
            spending_changes=[],
            completes_by_deadline=True
        )
        winner = rank([c_changes, c_no_changes])
        self.assertEqual(winner.method, "installments")

    def test_total_paid_wins(self):
        c_expensive = Candidate(
            method="installments",
            payment_plan=[(datetime.date(2026, 10, 1), Decimal("60")), (datetime.date(2026, 11, 1), Decimal("60"))],
            total_paid=Decimal("120"),
            completes_by_deadline=True
        )
        c_cheap = Candidate(
            method="full_payment",
            payment_plan=[(datetime.date(2026, 10, 1), Decimal("100"))],
            total_paid=Decimal("100"),
            completes_by_deadline=True
        )
        winner = rank([c_expensive, c_cheap])
        self.assertEqual(winner.method, "full_payment")

    def test_first_payment_date_wins(self):
        # Both cost 100, but one starts earlier
        c_later = Candidate(
            method="wait",
            payment_plan=[(datetime.date(2026, 10, 5), Decimal("100"))],
            total_paid=Decimal("100"),
            completes_by_deadline=True
        )
        c_earlier = Candidate(
            method="partial_payment",
            payment_plan=[(datetime.date(2026, 10, 1), Decimal("50")), (datetime.date(2026, 10, 5), Decimal("50"))],
            total_paid=Decimal("100"),
            completes_by_deadline=True
        )
        winner = rank([c_later, c_earlier])
        self.assertEqual(winner.method, "partial_payment")

    def test_len_payment_plan_wins(self):
        # Both start on same date and cost same, but fewer payments is better
        c_many = Candidate(
            method="installments",
            payment_plan=[(datetime.date(2026, 10, 1), Decimal("50")), (datetime.date(2026, 10, 2), Decimal("50"))],
            total_paid=Decimal("100"),
            completes_by_deadline=True
        )
        c_few = Candidate(
            method="full_payment",
            payment_plan=[(datetime.date(2026, 10, 1), Decimal("100"))],
            total_paid=Decimal("100"),
            completes_by_deadline=True
        )
        winner = rank([c_many, c_few])
        self.assertEqual(winner.method, "full_payment")

if __name__ == '__main__':
    unittest.main()
