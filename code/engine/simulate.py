import datetime
from decimal import Decimal
import pandas as pd
from engine.data.state import UserState
import os

from dateutil.relativedelta import relativedelta
import copy

def _is_terminating(desc: str) -> bool:
    kw = ['final', 'last', 'closing', 'terminal', 'one-time', 'exit', 'severance', 'temporary', 'seasonal', 'bonus', 'retainer', 'prorated']
    desc_lower = str(desc).lower()
    return any(k in desc_lower for k in kw)

def project_recurring_events(events: list, start_date: datetime.date, end_date: datetime.date) -> list:
    projected = []
    latest_recs = {}
    counts = {}
    history_amounts = {}
    
    for e in events:
        if getattr(e, 'recurring', False):
            if e.category == 'salary':
                key = ('__salary__', e.direction)
            else:
                key = (e.description, e.direction)
            if key not in latest_recs or e.date > latest_recs[key].date:
                latest_recs[key] = e
            counts[key] = counts.get(key, 0) + 1
            
            amt = e.amount if e.amount is not None else Decimal('0')
            if key not in history_amounts:
                history_amounts[key] = []
            history_amounts[key].append(amt)
                
    for key, latest_e in latest_recs.items():
        if latest_e.category == 'salary' and _is_terminating(latest_e.description):
            continue
            
        is_fixed = latest_e.category in {
            'rent', 'utilities', 'debt_repayment', 'education', 'family_support', 
            'insurance', 'salary', 'childcare', 'cloud_storage', 'subscription', 
            'delivery_membership', 'music_subscription', 'gym_membership'
        }
        if not is_fixed and counts[key] < 3:
            continue
            
        interval = latest_e.interval or 'monthly'
        curr_date = latest_e.date
        
        if latest_e.direction == 'debit':
            proj_amt = max(history_amounts[key])
        else:
            proj_amt = min(history_amounts[key])
            
        while True:
            if interval == 'monthly':
                curr_date += relativedelta(months=1)
            elif interval == 'weekly':
                curr_date += relativedelta(weeks=1)
            elif interval == 'yearly':
                curr_date += relativedelta(years=1)
            else:
                curr_date += relativedelta(months=1)
                
            if curr_date > end_date:
                break
                
            if curr_date >= start_date:
                new_e = copy.deepcopy(latest_e)
                new_e.date = curr_date
                new_e.amount = proj_amt
                new_e.event_id = f"proj_{latest_e.event_id}_{curr_date.strftime('%Y%m%d')}"
                new_e.status = 'projected'
                projected.append(new_e)

    return projected

def simulate(state: UserState, start_date: datetime.date, days: int = 90, spending_changes: list = None):
    end_date = start_date + datetime.timedelta(days=days)

    if spending_changes is None:
        spending_changes = []

    change_map = {}
    change_reduce_amounts = {}
    for sc in spending_changes:
        if isinstance(sc, str):
            if sc.startswith("stop:"):
                change_map[sc.split(":")[1]] = "stop"
            elif sc.startswith("reduce_to:"):
                parts = sc.split(":")
                change_map[parts[1]] = "reduce"
                if len(parts) > 2:
                    try:
                        change_reduce_amounts[parts[1]] = Decimal(parts[2])
                    except Exception:
                        pass
        elif isinstance(sc, dict):
            if sc.get("type") == "stop":
                change_map[sc["event_id"]] = "stop"
            elif sc.get("type") == "reduce":
                change_map[sc["event_id"]] = "reduce"
                if "amount" in sc:
                    try:
                        change_reduce_amounts[sc["event_id"]] = Decimal(str(sc["amount"]))
                    except Exception:
                        pass

    base_events = []
    for e in state.events:
        if start_date <= e.date <= end_date:
            if e.status == 'pending' and e.direction in ('credit',):
                continue
            if e.status == 'pending' and e.type in ('income', 'refund', 'salary'):
                continue
            if e.status in ('cancelled', 'failed'):
                continue
            if e.type == 'investment_valuation':
                continue
            base_events.append(e)

    proj_events = project_recurring_events(state.events, start_date, end_date)
    window_events = base_events + proj_events
    window_events.sort(key=lambda x: x.date)

    current_bal = state.available_balance
    min_bal = current_bal

    for e in window_events:
        base_id = e.event_id
        if base_id.startswith("proj_"):
            parts = base_id.split("_")
            if len(parts) >= 4:
                base_id = f"{parts[1]}_{parts[2]}"
            else:
                base_id = "_".join(parts[1:-1])

        amt = e.amount if e.amount is not None else Decimal('0')

        if base_id in change_map:
            action = change_map[base_id]
            if action == "stop":
                amt = Decimal('0')
            elif action == "reduce":
                if base_id in change_reduce_amounts:
                    amt = change_reduce_amounts[base_id]
                elif e.minimum_allowed_amount is not None:
                    amt = e.minimum_allowed_amount

        is_credit = (e.direction == 'credit') or (e.type in ('income', 'refund', 'salary'))
        if is_credit:
            current_bal += amt
        else:
            current_bal -= amt

        if current_bal < min_bal:
            min_bal = current_bal

    return min_bal

def calculate_amount_safe_to_pay(state: UserState, request_date: datetime.date, requested_amount: Decimal = None) -> Decimal:
    min_bal = simulate(state, request_date, 90)
    safe = min_bal - state.minimum_balance_to_keep
    if safe < Decimal('0'):
        safe = Decimal('0')
    if requested_amount is not None and safe > requested_amount:
        safe = requested_amount
    return safe
