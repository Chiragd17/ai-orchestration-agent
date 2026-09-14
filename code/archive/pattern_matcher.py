"""
Pattern Matcher - Use different projection strategies based on user patterns.
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

def classify_user_pattern(user_id: str, events_df: pd.DataFrame, profiles_df: pd.DataFrame, request_date: datetime.date) -> str:
    """Classify user into projection pattern based on their data."""
    
    user_events_df = events_df[events_df['user_id'] == user_id].copy()
    events = [Event(row) for _, row in user_events_df.iterrows()]
    
    # Check for scheduled income
    end_date = request_date + datetime.timedelta(days=90)
    has_scheduled_income = any(e.type == 'income' and e.status == 'scheduled' and 
                              request_date <= e.date <= end_date for e in events)
    
    # Count historical events
    historical_events = [e for e in events if e.status == 'settled' and e.date < request_date]
    
    # Check for data gaps
    if historical_events:
        latest_event_date = max(e.date for e in historical_events)
        gap_days = (request_date - latest_event_date).days
        is_data_gap = gap_days > 180  # 6 months
    else:
        is_data_gap = True
    
    # Count event types
    subscription_count = len([e for e in historical_events if e.type == 'subscription'])
    debt_payment_count = len([e for e in historical_events if e.type == 'debt_payment'])
    expense_count = len([e for e in historical_events if e.type == 'expense'])
    
    # Classification logic
    if is_data_gap:
        return "data_gap"
    elif has_scheduled_income:
        return "scheduled_income"
    elif subscription_count + debt_payment_count >= 10:  # Lots of fixed recurring
        return "fixed_heavy"
    elif expense_count > 30:  # Lots of variable expenses
        return "variable_heavy" 
    else:
        return "simple"

def project_by_pattern(user_id: str, pattern: str, request_date: datetime.date, 
                      events_df: pd.DataFrame, profiles_df: pd.DataFrame) -> Decimal:
    """Project based on classified pattern."""
    
    user_profile = profiles_df[profiles_df['user_id'] == user_id]
    current_balance = Decimal(str(user_profile.iloc[0]['current_available_balance']))
    min_balance = Decimal(str(user_profile.iloc[0]['minimum_balance_to_keep']))
    
    user_events_df = events_df[events_df['user_id'] == user_id].copy()
    events = [Event(row) for _, row in user_events_df.iterrows()]
    
    end_date = request_date + datetime.timedelta(days=90)
    balance = current_balance
    
    # Apply base events
    base_events = [e for e in events if e.status in ('settled', 'scheduled', 'pending') and request_date <= e.date <= end_date]
    
    for e in base_events:
        if e.status == 'pending' and e.direction == 'debit':
            balance -= e.amount
        elif e.status != 'pending':
            if e.direction == 'debit':
                balance -= e.amount
            else:
                balance += e.amount
    
    # Pattern-specific projection
    if pattern == "data_gap":
        # For data gap users: assume current_balance is accurate, minimal projection
        projected_expenses = Decimal('1000')  # Minimal buffer
    
    elif pattern == "scheduled_income":
        # Users with scheduled income: minimal fixed costs only
        historical_events = [e for e in events if e.status == 'settled' and e.date < request_date]
        by_key = defaultdict(list)
        for e in historical_events:
            key = (e.description, e.type)
            by_key[key].append(e)
        
        projected_expenses = Decimal('0')
        
        # Only project very clear fixed recurring
        for key, key_events in by_key.items():
            desc, ev_type = key
            if ev_type in ('subscription', 'debt_payment') and len(key_events) >= 3:
                latest_amount = max(key_events, key=lambda x: x.date).amount
                projected_expenses += latest_amount * 2  # 2 months
    
    elif pattern == "simple":
        # Simple users: basic rent + subscriptions only
        historical_events = [e for e in events if e.status == 'settled' and e.date < request_date]
        by_key = defaultdict(list)
        for e in historical_events:
            key = (e.description, e.type, e.category)
            by_key[key].append(e)
        
        projected_expenses = Decimal('0')
        
        # Project rent
        for key, key_events in by_key.items():
            desc, ev_type, category = key
            if category == 'rent' and len(key_events) >= 2:
                latest_amount = max(key_events, key=lambda x: x.date).amount
                projected_expenses += latest_amount * 2
                break
        
        # Project subscriptions (limited)
        sub_total = Decimal('0')
        for key, key_events in by_key.items():
            desc, ev_type, category = key
            if ev_type == 'subscription' and len(key_events) >= 2:
                latest_amount = max(key_events, key=lambda x: x.date).amount
                sub_total += latest_amount
        
        projected_expenses += sub_total * 2  # 2 months of subs
    
    elif pattern == "fixed_heavy":
        # Users with lots of fixed costs
        historical_events = [e for e in events if e.status == 'settled' and e.date < request_date]
        by_key = defaultdict(list)
        for e in historical_events:
            key = (e.description, e.type, e.category)
            by_key[key].append(e)
        
        projected_expenses = Decimal('0')
        
        # Project all fixed recurring
        for key, key_events in by_key.items():
            desc, ev_type, category = key
            if ev_type in ('subscription', 'debt_payment') and len(key_events) >= 2:
                latest_amount = max(key_events, key=lambda x: x.date).amount
                projected_expenses += latest_amount * 2
        
        # Add rent
        for key, key_events in by_key.items():
            desc, ev_type, category = key
            if category == 'rent' and len(key_events) >= 2:
                latest_amount = max(key_events, key=lambda x: x.date).amount
                projected_expenses += latest_amount * 2
                break
    
    elif pattern == "variable_heavy":
        # Users with lots of variable expenses: use conservative aggregation
        historical_events = [e for e in events if e.status == 'settled' and e.date < request_date]
        
        # Get protected categories
        protected_cats = str(user_profile.iloc[0]['expense_categories_to_protect']).split('|') if pd.notna(user_profile.iloc[0]['expense_categories_to_protect']) else []
        
        projected_expenses = Decimal('0')
        
        # Aggregate by protected category (conservative)
        for category in protected_cats:
            cat_events = [e for e in historical_events 
                         if e.type == 'expense' and e.category == category]
            
            if len(cat_events) >= 3:
                amounts = [e.amount for e in cat_events if e.amount]
                if amounts:
                    # Use median amount for 1.5 months only
                    median_amount = sorted(amounts)[len(amounts)//2]
                    projected_expenses += median_amount * Decimal('1.5')
    
    else:
        projected_expenses = Decimal('0')
    
    balance -= projected_expenses
    return max(Decimal('0'), balance - min_balance)

def test_pattern_matching():
    """Test pattern matching approach."""
    
    sample_requests, profiles_df, events_df = load_datasets()
    
    print("Pattern Matching Approach:")
    print("="*40)
    
    results = []
    pattern_counts = defaultdict(int)
    
    for _, row in sample_requests.iterrows():
        user_id = row['user_id']
        request_date = pd.to_datetime(row['request_date']).date()
        expected_amount = Decimal(str(row['amount_safe_to_pay']))
        
        # Classify user pattern
        pattern = classify_user_pattern(user_id, events_df, profiles_df, request_date)
        pattern_counts[pattern] += 1
        
        # Project based on pattern
        try:
            predicted_amount = project_by_pattern(user_id, pattern, request_date, events_df, profiles_df)
            diff = predicted_amount - expected_amount
            accuracy = (1 - (abs(diff) / expected_amount)) * 100 if expected_amount > 0 else 0
            
            status = "✓" if accuracy >= 90 else "±" if accuracy >= 70 else "✗"
            
            print(f"{status} {user_id} [{pattern}]: expected={expected_amount}, predicted={predicted_amount}")
            print(f"    diff={diff}, accuracy={accuracy:.1f}%")
            
            results.append({
                'user_id': user_id,
                'pattern': pattern,
                'expected': expected_amount,
                'predicted': predicted_amount,
                'accuracy': accuracy
            })
        
        except Exception as e:
            print(f"✗ {user_id} [{pattern}]: ERROR - {e}")
            results.append({
                'user_id': user_id,
                'pattern': pattern,
                'expected': expected_amount,
                'predicted': Decimal('0'),
                'accuracy': 0
            })
    
    # Summary
    good_results = sum(1 for r in results if r['accuracy'] >= 70)
    avg_accuracy = sum(r['accuracy'] for r in results) / len(results)
    
    print(f"\\nSummary:")
    print(f"Good results (>70%): {good_results}/25")
    print(f"Average accuracy: {avg_accuracy:.1f}%")
    print(f"\\nPattern distribution:")
    for pattern, count in pattern_counts.items():
        print(f"  {pattern}: {count} users")
    
    return results

if __name__ == "__main__":
    test_pattern_matching()