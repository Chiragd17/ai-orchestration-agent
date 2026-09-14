"""
Debug Simulator - Understand the exact data structure and simulation logic.
"""
import pandas as pd
import datetime
from decimal import Decimal
from collections import defaultdict
import os

def debug_user_data(user_id: str):
    """Debug a specific user's data structure."""
    
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    sample_requests = pd.read_csv(os.path.join(project_root, "dataset", "sample_requests.csv"))
    financial_profiles = pd.read_csv(os.path.join(project_root, "dataset", "financial_profiles.csv"))
    financial_events = pd.read_csv(os.path.join(project_root, "dataset", "financial_events.csv"))
    
    # Get user's sample request
    user_request = sample_requests[sample_requests['user_id'] == user_id].iloc[0]
    request_date = pd.to_datetime(user_request['request_date']).date()
    expected_amount = Decimal(str(user_request['amount_safe_to_pay']))
    
    print(f"=== USER {user_id} DEBUG ===")
    print(f"Request Date: {request_date}")
    print(f"Expected Amount Safe: {expected_amount}")
    print(f"Requested Amount: {user_request['requested_amount']}")
    print()
    
    # Get user profile
    user_profile = financial_profiles[financial_profiles['user_id'] == user_id].iloc[0]
    current_balance = Decimal(str(user_profile['current_available_balance']))
    min_balance = Decimal(str(user_profile['minimum_balance_to_keep']))
    protected_cats = str(user_profile['expense_categories_to_protect']).split('|') if pd.notna(user_profile['expense_categories_to_protect']) else []
    
    print(f"Current Balance: {current_balance}")
    print(f"Minimum Balance: {min_balance}")
    print(f"Protected Categories: {protected_cats}")
    print()
    
    # Get user events
    user_events = financial_events[financial_events['user_id'] == user_id]
    
    print(f"Total Events: {len(user_events)}")
    
    # Analyze events by status and date relationship to request
    print(f"\nEvents by Status:")
    status_counts = user_events['status'].value_counts()
    for status, count in status_counts.items():
        print(f"  {status}: {count}")
    
    # Events before, during, and after request date
    events_before = user_events[pd.to_datetime(user_events['event_date']) < pd.to_datetime(request_date)]
    events_in_window = user_events[
        (pd.to_datetime(user_events['event_date']) >= pd.to_datetime(request_date)) &
        (pd.to_datetime(user_events['event_date']) <= pd.to_datetime(request_date + datetime.timedelta(days=90)))
    ]
    
    print(f"\nEvent Timeline:")
    print(f"  Before request date: {len(events_before)}")
    print(f"  In 90-day window: {len(events_in_window)}")
    
    # Show latest historical events
    print(f"\nLatest Historical Events (last 5):")
    latest_hist = events_before.sort_values('event_date').tail(5)
    for _, row in latest_hist.iterrows():
        print(f"  {row['event_date']}: {row['event_type']} - {row['description']} - {row['direction']} {row['amount']} ({row['status']})")
    
    # Show events in simulation window
    if len(events_in_window) > 0:
        print(f"\nEvents in 90-day window:")
        for _, row in events_in_window.iterrows():
            print(f"  {row['event_date']}: {row['event_type']} - {row['description']} - {row['direction']} {row['amount']} ({row['status']})")
    else:
        print(f"\nNo events in 90-day window")
    
    # Check for data gaps
    if len(events_before) > 0:
        latest_event_date = pd.to_datetime(events_before['event_date']).max().date()
        gap_days = (request_date - latest_event_date).days
        print(f"\nData Gap: {gap_days} days from latest event to request ({latest_event_date} to {request_date})")
        
        if gap_days > 180:  # 6 months
            print("  → This is a DATA GAP user (>6 months)")
    
    # Analyze recurring patterns
    print(f"\nRecurring Pattern Analysis:")
    
    # Group by description
    by_desc = defaultdict(list)
    for _, row in events_before.iterrows():
        if row['status'] == 'settled':
            key = (row['description'], row['event_type'], row['category'])
            by_desc[key].append((pd.to_datetime(row['event_date']).date(), row['amount']))
    
    recurring_candidates = []
    for key, events_list in by_desc.items():
        desc, ev_type, category = key
        if len(events_list) >= 2:  # At least 2 occurrences
            dates = [dt for dt, amt in events_list]
            amounts = [amt for dt, amt in events_list]
            
            # Calculate gaps
            dates = sorted(dates)
            gaps = [(dates[i+1] - dates[i]).days for i in range(len(dates)-1)]
            avg_gap = sum(gaps) / len(gaps) if gaps else 0
            
            recurring_candidates.append({
                'description': desc,
                'type': ev_type,
                'category': category,
                'occurrences': len(events_list),
                'avg_gap_days': avg_gap,
                'amounts': amounts,
                'latest_date': max(dates),
                'latest_amount': amounts[dates.index(max(dates))]
            })
    
    # Sort by number of occurrences
    recurring_candidates.sort(key=lambda x: x['occurrences'], reverse=True)
    
    print(f"  Top recurring patterns:")
    for rc in recurring_candidates[:10]:
        print(f"    {rc['type']} - {rc['description']} ({rc['category']}): {rc['occurrences']} times, avg gap {rc['avg_gap_days']:.1f} days, latest amount {rc['latest_amount']}")
    
    print(f"\n" + "="*80 + "\n")

def simple_balance_calculation(user_id: str):
    """Simple balance calculation to understand the math."""
    
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    sample_requests = pd.read_csv(os.path.join(project_root, "dataset", "sample_requests.csv"))
    financial_profiles = pd.read_csv(os.path.join(project_root, "dataset", "financial_profiles.csv"))
    financial_events = pd.read_csv(os.path.join(project_root, "dataset", "financial_events.csv"))
    
    user_request = sample_requests[sample_requests['user_id'] == user_id].iloc[0]
    request_date = pd.to_datetime(user_request['request_date']).date()
    expected_amount = Decimal(str(user_request['amount_safe_to_pay']))
    
    user_profile = financial_profiles[financial_profiles['user_id'] == user_id].iloc[0]
    current_balance = Decimal(str(user_profile['current_available_balance']))
    min_balance = Decimal(str(user_profile['minimum_balance_to_keep']))
    
    print(f"=== SIMPLE CALCULATION FOR {user_id} ===")
    print(f"Starting balance: {current_balance}")
    print(f"Minimum balance: {min_balance}")
    print(f"Maximum spendable (no projection): {current_balance - min_balance}")
    print(f"Expected amount_safe_to_pay: {expected_amount}")
    print()
    
    # If expected is less than max spendable, there must be projected expenses
    if expected_amount < (current_balance - min_balance):
        projected_expenses_needed = (current_balance - min_balance) - expected_amount
        print(f"Projected expenses needed: {projected_expenses_needed}")
        print(f"This suggests {projected_expenses_needed} in expenses will be projected over 90 days")
    
    print()

if __name__ == "__main__":
    # Debug a few representative users
    test_users = ['user_01', 'user_05', 'user_13', 'user_14', 'user_22']
    
    for user_id in test_users:
        debug_user_data(user_id)
        simple_balance_calculation(user_id)