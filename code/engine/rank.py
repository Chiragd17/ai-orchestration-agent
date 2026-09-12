from typing import List
from engine.candidates import Candidate

def sort_key(c: Candidate):
    # completes_by_deadline: True should come before False
    c1 = not c.completes_by_deadline
    
    # bool(spending_changes): False should come before True (empty list is better)
    c2 = bool(c.spending_changes)
    
    # total_paid: Lower is better
    c3 = c.total_paid
    
    # first_payment_date: Earlier is better
    # If there is no plan, we shouldn't fail on index. Let's use a far future date.
    import datetime
    if c.payment_plan:
        c4 = c.payment_plan[0][0]
    else:
        c4 = datetime.date(9999, 12, 31)
        
    # len(payment_plan): Fewer payments is better
    c5 = len(c.payment_plan)
    
    # payment_option_id: string comparison, or "zzzzzz" if None
    c6 = c.payment_option_id if c.payment_option_id is not None else "zzzzzz"
    
    return (c1, c2, c3, c4, c5, c6)

def rank(candidates: List[Candidate]) -> Candidate:
    if not candidates:
        raise ValueError("Cannot rank an empty candidate list")
    
    # strict lexicographic ordering
    return min(candidates, key=sort_key)

def get_affordability_status(winning_candidate: Candidate) -> str:
    if winning_candidate.method == "full_payment":
        return "affordable_now"
    elif winning_candidate.method in ["partial_payment", "installments"] or bool(winning_candidate.spending_changes):
        return "affordable_with_plan"
    elif winning_candidate.method == "wait":
        return "affordable_later"
    else:
        return "not_affordable"
