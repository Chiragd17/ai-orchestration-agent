"""
Refined Solver - Fix over-projection by being more selective about recurring patterns.
"""
import pandas as pd
import datetime
from decimal import Decimal
from collections import defaultdict
import copy
from dateutil.relativedelta import relativedelta
import os
import statistics

class Event:
    def __init__(self, event_row):
        self.event_id = event_row['event_id']
        self.user_id = event_row['user_id']
        self.type = event_row['event_type']
        self.description = event_row['description']
        self.category = event_row['category']
        self.direction = event_row['direction']
        self.amount = Decimal(str(event_row['amount'])) if pd.notna(event_row['amount']) else None
        self.currency = event_row['currency']
        self.date = pd.to_datetime(event_row['event_date']).date()
        self.settlement_date = pd.to_datetime(event_row['settlement_date']).date() if pd.notna(event_row['settlement_date']) else self.date
        self.status = event_row['status']
        self.linked_event_id = event_row['linked_event_id'] if pd.notna(event_row['linked_event_id']) else None

def load_datasets():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    sample_requests = pd.read_csv(os.path.join(project_root, "dataset", "sample_requests.csv"))
    financial_profiles = pd.read_csv(os.path.join(project_root, "dataset", "financial_profiles.csv"))
    financial_events = pd.read_csv(os.path.join(project_root, "dataset", "financial_events.csv"))
    
    return sample_requests, financial_profiles, financial_events

def is_terminating(desc: str) -> bool:
    if pd.isna(desc):
        return False
    kw = ['final', 'last', 'closing', 'terminal', 'one-time', 'exit', 'severance', 
          'temporary', 'seasonal', 'bonus', 'retainer', 'prorated', 'arrears']
    desc_lower = str(desc).lower()
    return any(k in desc_lower for k in kw)

def simulate_refined(user_id: str, request_date: datetime.date, events_df: pd.DataFrame, 
                    profiles_df: pd.DataFrame) -> Decimal:
    """Refined simulation - more conservative recurring detection."""
    
    # Get user profile
    user_profile = profiles_df[profiles_df['user_id'] == user_id]
    if user_profile.empty:
        return Decimal('0')
    
    current_balance = Decimal(str(user_profile.iloc[0]['current_available_balance']))
    min_balance = Decimal(str(user_profile.iloc[0]['minimum_balance_to_keep']))
    protected_cats = str(user_profile.iloc[0]['expense_categories_to_protect']).split('|') if pd.notna(user_profile.iloc[0]['expense_categories_to_protect']) else []
    
    # Get events for this user
    user_events_df = events_df[events_df['user_id'] == user_id].copy()
    events = [Event(row) for _, row in user_events_df.iterrows()]
    
    # Simulation period
    end_date = request_date + datetime.timedelta(days=90)
    balance = current_balance
    
    print(f"=== Refined Simulation {user_id} ===")
    print(f"Starting balance: {balance}")
    print(f"Minimum balance: {min_balance}")
    print(f"Protected categories: {protected_cats}")
    
    # Step 1: Apply base events in the window
    base_events = [e for e in events if e.status in ('settled', 'scheduled', 'pending') and request_date <= e.date <= end_date]
    
    for e in base_events:
        if e.status == 'pending' and e.direction == 'debit':
            balance -= e.amount
            print(f"  Reserved pending: -{e.amount}")
        elif e.status != 'pending':
            if e.direction == 'debit':
                balance -= e.amount
            else:
                balance += e.amount
            print(f"  Applied {e.status}: {'+' if e.direction == 'credit' else '-'}{e.amount} ({e.description})")
    
    # Step 2: Project recurring events (MORE CONSERVATIVE)
    historical_events = [e for e in events if e.status == 'settled' and e.date < request_date]
    
    # Group by (description, type, category)
    by_key = defaultdict(list)
    for e in historical_events:
        key = (e.description, e.type, e.category)
        by_key[key].append(e)
    
    # STRATEGY 1: Always project subscription/debt_payment
    subscriptions_debt = []
    for key, key_events in by_key.items():
        desc, ev_type, category = key
        if ev_type in ('subscription', 'debt_payment') and len(key_events) >= 2:
            latest_e = max(key_events, key=lambda x: x.date)
            subscriptions_debt.append((latest_e, 'Fixed recurring'))
    
    # STRATEGY 2: Project income only if scheduled doesn't exist
    has_scheduled_income = any(e.type == 'income' and e.status == 'scheduled' and 
                              request_date <= e.date <= end_date for e in events)
    
    income_projections = []
    if not has_scheduled_income:
        for key, key_events in by_key.items():
            desc, ev_type, category = key
            if ev_type == 'income' and len(key_events) >= 3 and not is_terminating(desc):
                dates = [e.date for e in key_events]
                # Check pattern consistency and recency
                gaps = [(dates[i+1] - dates[i]).days for i in range(len(dates)-1)]
                avg_gap = sum(gaps) / len(gaps)
                gap_variance = statistics.stdev(gaps) if len(gaps) > 1 else 0
                
                # Only project if consistent and recent
                if gap_variance <= avg_gap * 0.3:  # Low variance
                    latest_date = max(dates)
                    days_since_last = (request_date - latest_date).days
                    if days_since_last <= avg_gap * 1.5:  # Not lapsed
                        latest_e = max(key_events, key=lambda x: x.date)
                        amounts = [e.amount for e in key_events if e.amount]
                        conservative_amount = min(amounts)  # Conservative
                        income_projections.append((latest_e, conservative_amount, 'Historical income'))
    
    # STRATEGY 3: Project protected categories by AGGREGATED monthly total (not individual descriptions)
    protected_projections = []
    
    # Aggregate all expenses by protected category
    for protected_cat in protected_cats:
        cat_events = [e for e in historical_events 
                     if e.type == 'expense' and e.direction == 'debit' and e.category == protected_cat]
        
        if len(cat_events) >= 3:  # Need reasonable history
            # Calculate total monthly spend for this category
            dates = [e.date for e in cat_events]
            amounts = [e.amount for e in cat_events if e.amount]
            
            if dates and amounts:
                first_date = min(dates)
                last_date = max(dates)
                months_span = max(1.0, (last_date - first_date).days / 30.0)
                
                total_spend = sum(amounts)
                monthly_avg = total_spend / Decimal(str(months_span))
                
                # Use a conservative multiplier (e.g., 0.8x average)
                conservative_monthly = monthly_avg * Decimal('0.8')
                
                protected_projections.append((protected_cat, conservative_monthly))
    
    # Apply projections
    print(f"\\nProjecting recurring events:")
    
    # 1. Fixed recurring (subscriptions/debt)
    for base_event, reason in subscriptions_debt:
        print(f"  {reason}: {base_event.description} = {base_event.amount}")
        
        # Project monthly from latest occurrence
        curr_date = base_event.date
        for _ in range(3):  # Max 3 projections
            curr_date += relativedelta(months=1)
            if curr_date > end_date:
                break
            if curr_date >= request_date:
                balance -= base_event.amount
                print(f"    -> {curr_date}: -{base_event.amount}")
    
    # 2. Income projections
    for base_event, amount, reason in income_projections:
        print(f"  {reason}: {base_event.description} = {amount}")
        
        curr_date = base_event.date
        for _ in range(3):  # Max 3 projections
            curr_date += relativedelta(months=1)
            if curr_date > end_date:
                break
            if curr_date >= request_date:
                balance += amount
                print(f"    -> {curr_date}: +{amount}")
    
    # 3. Protected category aggregated projections
    for category, monthly_amount in protected_projections:
        print(f"  Protected category {category}: {monthly_amount}/month")
        
        # Project 3 months of this category
        for month in [1, 2, 3]:
            proj_date = request_date + relativedelta(months=month-1, day=15)
            if proj_date <= end_date:
                balance -= monthly_amount
                print(f"    -> {proj_date}: -{monthly_amount}")
    
    # Final calculation
    safe_amount = max(Decimal('0'), balance - min_balance)
    
    print(f"\\nFinal balance: {balance}")
    print(f"Amount safe to pay: {safe_amount}")
    print()
    
    return safe_amount

def test_refined_simulation():
    """Test refined simulation."""
    
    sample_requests, profiles_df, events_df = load_datasets()
    
    print("Testing Refined Simulation:")
    print("="*50)
    
    # Test key users
    test_users = ['user_01', 'user_13', 'user_22', 'user_05']
    
    for user_id in test_users:
        user_request = sample_requests[sample_requests['user_id'] == user_id].iloc[0]
        request_date = pd.to_datetime(user_request['request_date']).date()
        expected_amount = Decimal(str(user_request['amount_safe_to_pay']))
        
        predicted_amount = simulate_refined(user_id, request_date, events_df, profiles_df)
        
        is_exact = abs(predicted_amount - expected_amount) < Decimal('1')
        diff = predicted_amount - expected_amount
        
        status = "✓" if is_exact else "✗"
        print(f"RESULT {status} {user_id}: expected={expected_amount}, predicted={predicted_amount}, diff={diff}")
        print()

# Test some simple cases first to see if the logic is working
def test_simple_cases():
    """Test users with known patterns."""
    
    sample_requests, profiles_df, events_df = load_datasets()
    
    # Test users with different complexity levels
    simple_users = [
        'user_01',  # Has scheduled income + regular expenses
        'user_09',  # Likely simple case  
        'user_16',  # Another potentially simple case
        'user_12'   # Check this one too
    ]
    
    print("Testing Simple Cases:")
    print("="*30)
    
    for user_id in simple_users:
        user_request = sample_requests[sample_requests['user_id'] == user_id].iloc[0]
        request_date = pd.to_datetime(user_request['request_date']).date()
        expected_amount = Decimal(str(user_request['amount_safe_to_pay']))
        
        predicted_amount = simulate_refined(user_id, request_date, events_df, profiles_df)
        
        diff = predicted_amount - expected_amount
        accuracy = abs(diff) / expected_amount * 100 if expected_amount > 0 else 0
        
        print(f"{user_id}: expected={expected_amount}, predicted={predicted_amount}")
        print(f"  Diff: {diff} (accuracy: {100-accuracy:.1f}%)")
        print()

if __name__ == "__main__":
    test_simple_cases()