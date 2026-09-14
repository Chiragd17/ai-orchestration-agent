"""
Minimal Projector - Use the most conservative projection possible.
Based on analysis, most users seem to need very minimal recurring projections.
"""
import pandas as pd
import datetime
from decimal import Decimal
from collections import defaultdict
from dateutil.relativedelta import relativedelta
import os

class Event:
    def __init__(self, event_row):
        self.event_id = event_row['event_id']
        self.user_id = event_row['user_id']
        self.type = event_row['event_type']
        self.description = event_row['description']
        self.category = event_row['category']
        self.direction = event_row['direction']
        self.amount = Decimal(str(event_row['amount'])) if pd.notna(event_row['amount']) else None
        self.date = pd.to_datetime(event_row['event_date']).date()
        self.status = event_row['status']

def load_datasets():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    sample_requests = pd.read_csv(os.path.join(project_root, "dataset", "sample_requests.csv"))
    financial_profiles = pd.read_csv(os.path.join(project_root, "dataset", "financial_profiles.csv"))
    financial_events = pd.read_csv(os.path.join(project_root, "dataset", "financial_events.csv"))
    
    return sample_requests, financial_profiles, financial_events

def simulate_minimal(user_id: str, request_date: datetime.date, events_df: pd.DataFrame, 
                    profiles_df: pd.DataFrame) -> Decimal:
    """Minimal projection - only the most essential recurring items."""
    
    user_profile = profiles_df[profiles_df['user_id'] == user_id]
    if user_profile.empty:
        return Decimal('0')
    
    current_balance = Decimal(str(user_profile.iloc[0]['current_available_balance']))
    min_balance = Decimal(str(user_profile.iloc[0]['minimum_balance_to_keep']))
    
    user_events_df = events_df[events_df['user_id'] == user_id].copy()
    events = [Event(row) for _, row in user_events_df.iterrows()]
    
    end_date = request_date + datetime.timedelta(days=90)
    balance = current_balance
    
    print(f"=== Minimal Projection {user_id} ===")
    print(f"Starting: {balance}, Min: {min_balance}")
    
    # Apply base events in window (settled, scheduled, pending)
    base_events = [e for e in events if e.status in ('settled', 'scheduled', 'pending') and request_date <= e.date <= end_date]
    
    for e in base_events:
        if e.status == 'pending' and e.direction == 'debit':
            balance -= e.amount
            print(f"  Pending debit: -{e.amount}")
        elif e.status != 'pending':
            if e.direction == 'debit':
                balance -= e.amount
            else:
                balance += e.amount
            print(f"  {e.status}: {'+' if e.direction == 'credit' else '-'}{e.amount} ({e.description})")
    
    # STRATEGY: Only project the most obvious recurring items
    # 1. Rent (always project if exists)
    # 2. Subscriptions/debt_payment (but only if very regular)
    # 3. Nothing else unless absolutely clear pattern
    
    historical_events = [e for e in events if e.status == 'settled' and e.date < request_date]
    
    by_key = defaultdict(list)
    for e in historical_events:
        key = (e.description, e.type, e.category)
        by_key[key].append(e)
    
    projected_expenses = Decimal('0')
    
    # Strategy 1: Always project rent if it exists
    for key, key_events in by_key.items():
        desc, ev_type, category = key
        
        if category == 'rent' and len(key_events) >= 2:
            # Rent is almost always recurring
            amounts = [e.amount for e in key_events if e.amount]
            if amounts:
                # Use most recent rent amount
                latest_e = max(key_events, key=lambda x: x.date)
                rent_amount = latest_e.amount
                
                # Project just 1-2 rent payments in 90 days
                projected_rent = rent_amount * 2  # Conservative: 2 months of rent
                projected_expenses += projected_rent
                print(f"  Projected rent (2 months): -{projected_rent}")
                break
    
    # Strategy 2: Project only very regular subscriptions
    subscription_total = Decimal('0')
    for key, key_events in by_key.items():
        desc, ev_type, category = key
        
        if ev_type in ('subscription', 'debt_payment') and len(key_events) >= 4:
            # Only if very frequent (4+ occurrences)
            amounts = [e.amount for e in key_events if e.amount]
            if amounts:
                latest_amount = max(key_events, key=lambda x: x.date).amount
                # Project 3 months worth
                monthly_sub = latest_amount * 3
                subscription_total += monthly_sub
    
    if subscription_total > 0:
        projected_expenses += subscription_total
        print(f"  Projected subscriptions (3 months): -{subscription_total}")
    
    # Strategy 3: Minimal essential expenses (only if user has MANY expense entries)
    total_expense_entries = len([e for e in historical_events if e.type == 'expense'])
    
    if total_expense_entries > 20:  # Only for users with lots of expense history
        # Project minimal essential spending (groceries, utilities)
        essential_categories = ['groceries', 'utilities']
        essential_total = Decimal('0')
        
        for category in essential_categories:
            cat_events = [e for e in historical_events 
                         if e.type == 'expense' and e.category == category]
            
            if len(cat_events) >= 5:  # Need good history
                amounts = [e.amount for e in cat_events if e.amount]
                if amounts:
                    # Very conservative: use median amount for just 2 months
                    amounts_sorted = sorted(amounts)
                    median_amount = amounts_sorted[len(amounts_sorted)//2]
                    conservative_essential = median_amount * 2  # 2 months only
                    essential_total += conservative_essential
        
        if essential_total > 0:
            projected_expenses += essential_total
            print(f"  Projected essentials (2 months): -{essential_total}")
    
    # Apply projected expenses
    balance -= projected_expenses
    
    result = max(Decimal('0'), balance - min_balance)
    print(f"  Final balance: {balance}")
    print(f"  Amount safe: {result}")
    print()
    
    return result

def test_minimal_approach():
    """Test minimal approach on all users."""
    
    sample_requests, profiles_df, events_df = load_datasets()
    
    print("Testing Minimal Projection Approach:")
    print("="*50)
    
    results = []
    
    for _, row in sample_requests.iterrows():
        user_id = row['user_id']
        request_date = pd.to_datetime(row['request_date']).date()
        expected_amount = Decimal(str(row['amount_safe_to_pay']))
        
        try:
            predicted_amount = simulate_minimal(user_id, request_date, events_df, profiles_df)
            diff = predicted_amount - expected_amount
            accuracy = (1 - (abs(diff) / expected_amount)) * 100 if expected_amount > 0 else 0
            
            results.append({
                'user_id': user_id,
                'expected': expected_amount,
                'predicted': predicted_amount,
                'diff': diff,
                'accuracy': accuracy
            })
        
        except Exception as e:
            results.append({
                'user_id': user_id,
                'expected': expected_amount,
                'predicted': Decimal('0'),
                'diff': -expected_amount,
                'accuracy': 0
            })
    
    # Analyze results
    exact_matches = sum(1 for r in results if abs(r['diff']) < Decimal('1'))
    close_matches = sum(1 for r in results if r['accuracy'] >= 90)
    good_matches = sum(1 for r in results if r['accuracy'] >= 75)
    
    print("\\n" + "="*50)
    print("RESULTS SUMMARY:")
    print(f"Exact matches (<1 diff): {exact_matches}/25")
    print(f"Close matches (>90%): {close_matches}/25")
    print(f"Good matches (>75%): {good_matches}/25")
    
    avg_accuracy = sum(r['accuracy'] for r in results) / len(results)
    print(f"Average accuracy: {avg_accuracy:.1f}%")
    
    print("\\nBest performers:")
    best = sorted(results, key=lambda x: x['accuracy'], reverse=True)[:10]
    for r in best:
        print(f"  {r['user_id']}: {r['accuracy']:.1f}% (expected={r['expected']}, predicted={r['predicted']})")
    
    print("\\nWorst performers:")
    worst = sorted(results, key=lambda x: x['accuracy'])[:5]
    for r in worst:
        print(f"  {r['user_id']}: {r['accuracy']:.1f}% (expected={r['expected']}, predicted={r['predicted']})")

if __name__ == "__main__":
    test_minimal_approach()