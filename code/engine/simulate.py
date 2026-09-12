import datetime
from decimal import Decimal
import pandas as pd
from engine.data.state import UserState
import os

from dateutil.relativedelta import relativedelta
import copy

def project_recurring_events(events: list, start_date: datetime.date, end_date: datetime.date) -> list:
    projected = []
    # Group by description and direction to find the latest occurrence
    latest_recs = {}
    for e in events:
        if e.recurring:
            key = (e.description, e.direction)
            if key not in latest_recs or e.date > latest_recs[key].date:
                latest_recs[key] = e
                
    for key, latest_e in latest_recs.items():
        if latest_e.status in ['cancelled', 'failed']:
            continue
            
        interval_type = latest_e.interval or 'monthly'
        curr_date = latest_e.date
        
        while True:
            if interval_type == 'monthly':
                curr_date = curr_date + relativedelta(months=1)
            elif interval_type == 'weekly':
                curr_date = curr_date + relativedelta(weeks=1)
            elif interval_type == 'yearly':
                curr_date = curr_date + relativedelta(years=1)
            else:
                curr_date = curr_date + relativedelta(months=1)
                
            if curr_date > end_date:
                break
                
            # If the projected date is after the request start_date, include it in the window
            if curr_date >= start_date:
                new_e = copy.deepcopy(latest_e)
                new_e.date = curr_date
                new_e.event_id = f"proj_{new_e.event_id}_{curr_date.strftime('%Y%m%d')}"
                new_e.status = 'projected'
                projected.append(new_e)
                
    return projected

def simulate(state: UserState, start_date: datetime.date, days: int = 90, spending_changes: list = None):
    end_date = start_date + datetime.timedelta(days=days)
    
    if spending_changes is None:
        spending_changes = []
        
    change_map = {}
    for sc in spending_changes:
        if sc.startswith("stop:"):
            change_map[sc.split(":")[1]] = "stop"
        elif sc.startswith("reduce_to:"):
            change_map[sc.split(":")[1]] = "reduce"
    
    base_events = [e for e in state.events if e.date >= start_date and e.date <= end_date]
    proj_events = project_recurring_events(state.events, start_date, end_date)
    
    window_events = base_events + proj_events
    window_events.sort(key=lambda x: x.date)
    
    current_bal = state.available_balance
    min_bal = current_bal
    
    for e in window_events:
        # Extract base event ID if this is a projected event
        base_id = e.event_id
        if base_id.startswith("proj_"):
            parts = base_id.split("_")
            base_id = f"{parts[1]}_{parts[2]}"
            
        amt = e.amount if e.amount is not None else Decimal('0')
        
        # Apply spending changes
        if base_id in change_map:
            action = change_map[base_id]
            if action == "stop":
                amt = Decimal('0')
            elif action == "reduce" and e.minimum_allowed_amount is not None:
                amt = e.minimum_allowed_amount
                
        if e.type in ['income', 'refund', 'investment_sale']:
            current_bal += amt
        else: 
            current_bal -= amt
            
        if current_bal < min_bal:
            min_bal = current_bal
            
    return min_bal

def calculate_amount_safe_to_pay(state: UserState, request_date: datetime.date, requested_amount: Decimal = None) -> Decimal:
    min_bal = simulate(state, request_date, 90)
    safe = min_bal - state.minimum_balance_to_keep
    safe_to_pay = max(Decimal('0'), safe)
    if requested_amount is not None:
        safe_to_pay = min(safe_to_pay, requested_amount)
    return safe_to_pay

def is_safe(state: UserState, request_date: datetime.date, payment_plan_events: list, spending_changes: list = None) -> bool:
    # A generic function to check if applying a list of theoretical payment events is safe
    temp_state = UserState(
        user_id=state.user_id,
        home_currency=state.home_currency,
        available_balance=state.available_balance,
        minimum_balance_to_keep=state.minimum_balance_to_keep,
        financial_priorities=state.financial_priorities,
        payment_methods_user_will_consider=state.payment_methods_user_will_consider,
        spending_preferences=state.spending_preferences,
        protected_categories=state.protected_categories,
        reduce_categories=state.reduce_categories,
        stop_categories=state.stop_categories,
        events=state.events + payment_plan_events
    )
    min_bal = simulate(temp_state, request_date, 90, spending_changes)
    return min_bal >= state.minimum_balance_to_keep

def calculate_earliest_full_payment_date(user_state: UserState, requested_amount: Decimal, request_date: datetime.date, forecast_horizon: int = 90) -> datetime.date:
    # Iterate day by day for 90 days to find the first day where a full payment doesn't breach the minimum
    from engine.data.state import Event
    for day_offset in range(forecast_horizon + 1):
        test_date = request_date + datetime.timedelta(days=day_offset)
        # Create a theoretical payment event on that day
        e = Event(
            event_id="theoretical_payment",
            date=test_date,
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
        if is_safe(user_state, request_date, [e]):
            return test_date
    return None
