"""
Multiplier Tuner - Find exact multipliers for protected category projections.
"""
import pandas as pd
import datetime
from decimal import Decimal
from collections import defaultdict
import copy
from dateutil.relativedelta import relativedelta
import os
import statistics
import itertools

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

def load_datasets():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    sample_requests = pd.read_csv(os.path.join(project_root, "dataset", "sample_requests.csv"))
    financial_profiles = pd.read_csv(os.path.join(project_root, "dataset", "financial_profiles.csv"))
    financial_events = pd.read_csv(os.path.join(project_root, "dataset", "financial_events.csv"))
    
    return sample_requests, financial_profiles, financial_events

def simulate_with_multipliers(user_id: str, request_date: datetime.date, events_df: pd.DataFrame, 
                             profiles_df: pd.DataFrame, multipliers: dict) -> Decimal:
    """Simulate with given multipliers for different components."""
    
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
    
    # Apply base events in the window
    base_events = [e for e in events if e.status in ('settled', 'scheduled', 'pending') and request_date <= e.date <= end_date]
    
    for e in base_events:
        if e.status == 'pending' and e.direction == 'debit':
            balance -= e.amount
        elif e.status != 'pending':
            if e.direction == 'debit':
                balance -= e.amount
            else:
                balance += e.amount
    
    # Project recurring events
    historical_events = [e for e in events if e.status == 'settled' and e.date < request_date]
    
    # Group by (description, type, category)
    by_key = defaultdict(list)
    for e in historical_events:
        key = (e.description, e.type, e.category)
        by_key[key].append(e)
    
    # 1. Fixed recurring (subscriptions/debt) with multiplier
    for key, key_events in by_key.items():
        desc, ev_type, category = key
        if ev_type in ('subscription', 'debt_payment') and len(key_events) >= 2:
            latest_e = max(key_events, key=lambda x: x.date)
            projected_amount = latest_e.amount * Decimal(str(multipliers.get('fixed_multiplier', 1.0)))
            
            # Project monthly
            curr_date = latest_e.date
            for _ in range(int(multipliers.get('projection_months', 3))):
                curr_date += relativedelta(months=1)
                if curr_date > end_date:
                    break
                if curr_date >= request_date:
                    balance -= projected_amount
    
    # 2. Income projections (if no scheduled income)
    has_scheduled_income = any(e.type == 'income' and e.status == 'scheduled' and 
                              request_date <= e.date <= end_date for e in events)
    
    if not has_scheduled_income and multipliers.get('project_income', True):
        for key, key_events in by_key.items():
            desc, ev_type, category = key
            if ev_type == 'income' and len(key_events) >= 3:
                amounts = [e.amount for e in key_events if e.amount]
                if amounts:
                    projected_amount = min(amounts) * Decimal(str(multipliers.get('income_multiplier', 1.0)))
                    latest_e = max(key_events, key=lambda x: x.date)
                    
                    curr_date = latest_e.date
                    for _ in range(int(multipliers.get('projection_months', 3))):
                        curr_date += relativedelta(months=1)
                        if curr_date > end_date:
                            break
                        if curr_date >= request_date:
                            balance += projected_amount
    
    # 3. Protected category aggregated projections
    for protected_cat in protected_cats:
        cat_events = [e for e in historical_events 
                     if e.type == 'expense' and e.direction == 'debit' and e.category == protected_cat]
        
        if len(cat_events) >= multipliers.get('min_category_events', 3):
            dates = [e.date for e in cat_events]
            amounts = [e.amount for e in cat_events if e.amount]
            
            if dates and amounts:
                first_date = min(dates)
                last_date = max(dates)
                months_span = max(1.0, (last_date - first_date).days / 30.0)
                
                total_spend = sum(amounts)
                monthly_avg = total_spend / Decimal(str(months_span))
                
                # Apply category-specific multiplier
                cat_multiplier_key = f'{protected_cat}_multiplier'
                cat_multiplier = multipliers.get(cat_multiplier_key, multipliers.get('protected_multiplier', 0.5))
                projected_monthly = monthly_avg * Decimal(str(cat_multiplier))
                
                # Project for specified months
                for month in range(1, int(multipliers.get('projection_months', 3)) + 1):
                    proj_date = request_date + relativedelta(months=month-1, day=15)
                    if proj_date <= end_date:
                        balance -= projected_monthly
    
    return max(Decimal('0'), balance - min_balance)

def tune_single_user(user_id: str):
    """Tune multipliers for a single user to find exact match."""
    
    sample_requests, profiles_df, events_df = load_datasets()
    
    user_request = sample_requests[sample_requests['user_id'] == user_id].iloc[0]
    request_date = pd.to_datetime(user_request['request_date']).date()
    expected_amount = Decimal(str(user_request['amount_safe_to_pay']))
    
    print(f"=== Tuning {user_id} ===")
    print(f"Target: {expected_amount}")
    
    # Test different multiplier combinations
    best_diff = float('inf')
    best_multipliers = None
    best_prediction = None
    
    # Parameter ranges to test
    multipliers_to_test = {
        'fixed_multiplier': [0.5, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2],
        'protected_multiplier': [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8],
        'projection_months': [1, 2, 3, 4],
        'min_category_events': [2, 3, 4, 5]
    }
    
    # Try combinations
    keys = list(multipliers_to_test.keys())
    values = list(multipliers_to_test.values())
    
    for combination in itertools.product(*values):
        multipliers = dict(zip(keys, combination))
        
        try:
            predicted = simulate_with_multipliers(user_id, request_date, events_df, profiles_df, multipliers)
            diff = abs(predicted - expected_amount)
            
            if diff < best_diff:
                best_diff = diff
                best_multipliers = multipliers.copy()
                best_prediction = predicted
                
                if diff < Decimal('1'):  # Very close
                    print(f"  Excellent match! diff={diff}")
                    print(f"  Multipliers: {best_multipliers}")
                    print(f"  Predicted: {predicted}")
                    break
        
        except Exception as e:
            continue
    
    print(f"Best result for {user_id}:")
    print(f"  Expected: {expected_amount}")
    print(f"  Predicted: {best_prediction}")
    print(f"  Diff: {best_diff}")
    print(f"  Multipliers: {best_multipliers}")
    print()
    
    return best_multipliers, best_diff

def test_multiplier_approach():
    """Test the multiplier tuning approach on key users."""
    
    print("Multiplier Tuning Approach:")
    print("="*40)
    
    # Test on users that were close in previous attempts
    test_users = ['user_01', 'user_12', 'user_13', 'user_22']
    
    all_results = {}
    
    for user_id in test_users:
        best_multipliers, best_diff = tune_single_user(user_id)
        all_results[user_id] = {
            'multipliers': best_multipliers,
            'diff': best_diff
        }
    
    print("Summary:")
    for user_id, result in all_results.items():
        print(f"{user_id}: diff={result['diff']}")
        for key, value in result['multipliers'].items():
            print(f"  {key}: {value}")
        print()

if __name__ == "__main__":
    test_multiplier_approach()