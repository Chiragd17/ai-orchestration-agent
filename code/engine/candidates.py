import datetime
from decimal import Decimal
from dataclasses import dataclass, field
from typing import List, Tuple, Optional
import pandas as pd
import itertools

from engine.data.state import UserState, Event
from engine.simulate import is_safe, calculate_amount_safe_to_pay, calculate_earliest_full_payment_date

@dataclass
class Candidate:
    method: str
    payment_plan: List[Tuple[datetime.date, Decimal]]
    total_paid: Decimal
    spending_changes: list = field(default_factory=list)
    payment_option_id: Optional[str] = None
    completes_by_deadline: bool = False

def generate_candidates(
    user_state: UserState,
    request_id: str,
    request_date: datetime.date,
    requested_amount: Decimal,
    desired_completion_date: datetime.date,
    allows_partial_payment: bool,
    payment_options_df: pd.DataFrame
) -> List[Candidate]:
    
    candidates = []
    
    amount_safe_to_pay = calculate_amount_safe_to_pay(user_state, request_date, requested_amount)
    earliest_full_date = calculate_earliest_full_payment_date(user_state, requested_amount, request_date)
    
    # Pre-compute valid spending change combinations
    latest_recs = {}
    for e in user_state.events:
        key = (e.description, e.direction)
        if key not in latest_recs or e.date > latest_recs[key].date:
            latest_recs[key] = e
            
    base_actions = []
    for e in latest_recs.values():
        if e.category not in user_state.protected_categories:
            if e.flexibility == 'stoppable' and e.category in user_state.stop_categories:
                base_actions.append(f"stop:{e.event_id}")
            elif e.flexibility == 'reducible' and e.category in user_state.reduce_categories and e.raw_minimum_allowed_amount is not None:
                base_actions.append(f"reduce_to:{e.event_id}:{e.raw_minimum_allowed_amount}")
                
    valid_change_combinations = [[]] # Always try without changes first
    for k in range(1, min(4, len(base_actions) + 1)):
        for combo in itertools.combinations(base_actions, k):
            # Enforce mutual exclusivity: never both stop and reduce_to on same event.
            # But since an event is strictly EITHER stoppable OR reducible in our data model (flexibility column), 
            # we will naturally never generate both for the exact same event. 
            valid_change_combinations.append(list(combo))
    
    # 1. full_payment
    if "full_payment" in user_state.payment_methods_user_will_consider:
        # Check if full amount is safe exactly on request_date
        test_e = Event(
            event_id="test_full_payment",
            date=request_date,
            amount=requested_amount,
            type="expense",
            category="theoretical",
            description="Theoretical full payment",
            direction="debit",
            recurring=False,
            interval=None,
            flexibility="fixed",
            minimum_allowed_amount=None,
            raw_minimum_allowed_amount=None,
            status="scheduled",
            linked_event_id=None
        )
        for changes in valid_change_combinations:
            if is_safe(user_state, request_date, [test_e], spending_changes=changes):
                candidates.append(Candidate(
                    method="full_payment",
                    payment_plan=[(request_date, requested_amount)],
                    total_paid=requested_amount,
                    spending_changes=changes,
                    payment_option_id=None,
                    completes_by_deadline=request_date <= desired_completion_date
                ))
                break # First safe combination is best (ordered by fewer changes)
            
    # 2. partial_payment
    if allows_partial_payment and "partial_payment" in user_state.payment_methods_user_will_consider:
        if Decimal('0') < amount_safe_to_pay < requested_amount and earliest_full_date is not None:
            if earliest_full_date <= desired_completion_date:
                p1 = amount_safe_to_pay
                p2 = requested_amount - p1
                # Ensure they exactly sum
                assert p1 + p2 == requested_amount
                candidates.append(Candidate(
                    method="partial_payment",
                    payment_plan=[(request_date, p1), (earliest_full_date, p2)],
                    total_paid=requested_amount,
                    spending_changes=[],
                    payment_option_id=None,
                    completes_by_deadline=True # Due to the if statement above
                ))
                
    # 3. installments
    # request_payment_options.csv row contains: request_id, payment_option_id, total_payable_amount, payment_start_date, number_of_payments, days_between_payments, explicit_financing_fee
    req_options = payment_options_df[payment_options_df['request_id'] == request_id]
    for _, opt in req_options.iterrows():
        if opt['payment_method'] != 'installments':
            continue
        opt_id = opt['payment_option_id']
        total_payable = Decimal(str(opt['total_payable_amount']))
        start_date_str = opt['first_payment_date']
        start_date = datetime.datetime.strptime(str(start_date_str), "%Y-%m-%d").date()
        num_payments = int(opt['number_of_payments'])
        days_between = int(opt['payment_frequency_days'])
        payment_amt = Decimal(str(opt['payment_amount']))
        
        # Exact schedule construction
        plan = []
        for i in range(num_payments):
            d = start_date + datetime.timedelta(days=i * days_between)
            plan.append((d, payment_amt))
            
        # Test if this exact schedule is safe
        events_to_test = []
        for i, (d, amt) in enumerate(plan):
            events_to_test.append(Event(
                event_id=f"test_install_{opt_id}_{i}",
                date=d,
                amount=amt,
                type="expense",
                category="theoretical",
                description="Theoretical installment",
                direction="debit",
                recurring=False,
                interval=None,
                flexibility="fixed",
                minimum_allowed_amount=None,
                raw_minimum_allowed_amount=None,
                status="scheduled",
                linked_event_id=None
            ))
            
        for changes in valid_change_combinations:
            if is_safe(user_state, request_date, events_to_test, spending_changes=changes):
                completes_by = plan[-1][0] <= desired_completion_date if plan else False
                candidates.append(Candidate(
                    method="installments",
                    payment_plan=plan,
                    total_paid=total_payable,
                    spending_changes=changes,
                    payment_option_id=opt_id,
                    completes_by_deadline=completes_by
                ))
                break # First safe combination is best
            
    # 4. wait
    if "full_payment" in user_state.payment_methods_user_will_consider:
        if earliest_full_date is not None and earliest_full_date > request_date:
            candidates.append(Candidate(
                method="wait",
                payment_plan=[(earliest_full_date, requested_amount)],
                total_paid=requested_amount,
                spending_changes=[],
                payment_option_id=None,
                completes_by_deadline=earliest_full_date <= desired_completion_date
            ))
            
    # 5. not_recommended (fallback)
    candidates.append(Candidate(
        method="not_recommended",
        payment_plan=[],
        total_paid=Decimal('0'),
        spending_changes=[],
        payment_option_id=None,
        completes_by_deadline=False
    ))
    
    return candidates
