"""
Accurate Simulator - Implement correct 90-day projection logic.
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

def detect_interval_days(dates: list) -> int:
    """Detect average interval in days."""
    if len(dates) < 2:
        return 30  # Default to monthly
    
    dates = sorted(dates)
    gaps = [(dates[i+1] - dates[i]).days for i in range(len(dates)-1)]
    
    return int(sum(gaps) / len(gaps)) if gaps else 30

def simulate_accurate(user_id: str, request_date: datetime.date, events_df: pd.DataFrame, 
                     profiles_df: pd.DataFrame) -> Decimal:
    """Accurate 90-day simulation."""
    
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
    
    print(f"=== Simulating {user_id} ===")
    print(f"Starting balance: {balance}")
    print(f"Minimum balance: {min_balance}")
    
    # Step 1: Apply base events in the window (settled, scheduled, pending)
    base_events = [e for e in events if e.status in ('settled', 'scheduled', 'pending') and request_date <= e.date <= end_date]
    
    print(f"Base events in window: {len(base_events)}")
    for e in base_events:
        if e.status == 'pending' and e.direction == 'debit':
            # Reserve pending debits immediately
            balance -= e.amount
            print(f"  Reserved pending debit: -{e.amount} ({e.description})")
        elif e.status != 'pending':
            if e.direction == 'debit':
                balance -= e.amount
                print(f"  Applied {e.status} debit: -{e.amount} ({e.description} on {e.date})")
            else:
                balance += e.amount
                print(f"  Applied {e.status} credit: +{e.amount} ({e.description} on {e.date})")
    
    # Step 2: Project recurring events
    # Group historical events by (description, type, category, direction)
    historical_events = [e for e in events if e.status == 'settled' and e.date < request_date]
    
    by_key = defaultdict(list)
    for e in historical_events:
        key = (e.description, e.type, e.category, e.direction)
        by_key[key].append(e)
    
    # Find recurring patterns
    recurring_projections = []
    
    for key, key_events in by_key.items():
        desc, ev_type, category, direction = key
        
        if len(key_events) < 2:
            continue  # Need at least 2 occurrences for recurrence
        
        # Check for specific recurring types
        if ev_type in ('subscription', 'debt_payment'):
            # Always recurring - project monthly
            latest_e = max(key_events, key=lambda x: x.date)
            recurring_projections.append(('monthly', latest_e, latest_e.amount, f"Fixed {ev_type}"))
            
        elif ev_type == 'income' and not is_terminating(desc):
            # Income: project if consistent and not lapsed
            dates = [e.date for e in key_events]
            avg_interval = detect_interval_days(dates)
            
            # Check if pattern is still active (last occurrence not too far back)
            latest_date = max(dates)
            gap_to_request = (request_date - latest_date).days
            
            if gap_to_request <= avg_interval * 1.5:  # Pattern still active
                # Check for scheduled income first - if exists, don't project historical
                has_scheduled = any(e.type == 'income' and e.status == 'scheduled' and 
                                  request_date <= e.date <= end_date for e in events)
                
                if not has_scheduled:
                    latest_e = max(key_events, key=lambda x: x.date)
                    amounts = [e.amount for e in key_events if e.amount is not None]
                    conservative_amount = min(amounts)  # Conservative income projection
                    
                    interval = 'monthly' if avg_interval >= 28 else 'biweekly' if avg_interval >= 12 else 'weekly'
                    recurring_projections.append((interval, latest_e, conservative_amount, f"Historical income"))
        
        elif ev_type == 'expense':
            # Expense: project if frequent enough and in protected categories OR high frequency
            dates = [e.date for e in key_events]
            avg_interval = detect_interval_days(dates)
            
            # Project if:
            # 1. In protected categories (rent, utilities, groceries, etc.)
            # 2. OR has many occurrences (5+) with reasonable frequency
            should_project = (
                category in protected_cats or 
                (len(key_events) >= 3 and avg_interval <= 45)
            )
            
            if should_project:
                latest_e = max(key_events, key=lambda x: x.date)
                amounts = [e.amount for e in key_events if e.amount is not None]
                
                # Use maximum amount for conservative expense projection
                proj_amount = max(amounts)
                
                interval = 'monthly' if avg_interval >= 28 else 'biweekly' if avg_interval >= 12 else 'weekly'
                reason = f"Protected expense ({category})" if category in protected_cats else f"Frequent expense"
                recurring_projections.append((interval, latest_e, proj_amount, reason))
    
    # Apply recurring projections
    print(f"\\nProjecting {len(recurring_projections)} recurring patterns:")
    
    for interval, base_event, amount, reason in recurring_projections:
        print(f"  {reason}: {base_event.description} - {interval} {amount}")
        
        # Project forward from the base event's date
        curr_date = base_event.date
        projections_applied = 0
        
        while projections_applied < 10:  # Safety limit
            # Calculate next occurrence
            if interval == 'weekly':
                curr_date += datetime.timedelta(days=7)
            elif interval == 'biweekly':
                curr_date += datetime.timedelta(days=14)
            elif interval == 'monthly':
                curr_date += relativedelta(months=1)
            else:
                curr_date += relativedelta(months=1)
            
            if curr_date > end_date:
                break
            
            if curr_date >= request_date:
                if base_event.direction == 'debit':
                    balance -= amount
                    print(f"    Projected expense on {curr_date}: -{amount}")
                else:
                    balance += amount
                    print(f"    Projected income on {curr_date}: +{amount}")
                
                projections_applied += 1
    
    # Final calculation
    safe_amount = balance - min_balance
    safe_amount = max(Decimal('0'), safe_amount)
    
    print(f"\\nFinal balance: {balance}")
    print(f"Amount safe to pay: {safe_amount}")
    print()
    
    return safe_amount

def test_accurate_simulation():
    """Test the accurate simulation."""
    
    sample_requests, profiles_df, events_df = load_datasets()
    
    print("Testing Accurate Simulation:")
    print("="*50)
    
    exact_matches = 0
    results = []
    
    # Test on a subset first
    test_users = ['user_01', 'user_05', 'user_13', 'user_22']
    
    for user_id in test_users:
        user_request = sample_requests[sample_requests['user_id'] == user_id].iloc[0]
        request_date = pd.to_datetime(user_request['request_date']).date()
        expected_amount = Decimal(str(user_request['amount_safe_to_pay']))
        
        predicted_amount = simulate_accurate(user_id, request_date, events_df, profiles_df)
        
        is_exact = abs(predicted_amount - expected_amount) < Decimal('0.01')
        if is_exact:
            exact_matches += 1
        
        results.append({
            'user_id': user_id,
            'expected': expected_amount,
            'predicted': predicted_amount,
            'exact_match': is_exact,
            'diff': predicted_amount - expected_amount
        })
    
    print(f"\\n\\nRESULTS:")
    print(f"Exact matches: {exact_matches}/{len(test_users)}")
    
    for r in results:
        status = "✓" if r['exact_match'] else "✗"
        print(f"{status} {r['user_id']}: expected={r['expected']}, predicted={r['predicted']}, diff={r['diff']}")

if __name__ == "__main__":
    test_accurate_simulation()