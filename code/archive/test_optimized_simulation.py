"""
Test the optimized simulation engine directly without LLM dependencies.
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

import pandas as pd
import datetime
from decimal import Decimal
from engine.data.state import UserState
from engine.data.loaders import load_financial_data
from engine.simulate import project_recurring_events

def test_sample_users():
    """Test our optimized simulation on sample users."""
    
    print("Testing Optimized Simulation Engine")
    print("="*50)
    
    # Load datasets
    project_root = os.path.dirname(__file__).replace('code', '')
    sample_requests = pd.read_csv(os.path.join(project_root, "dataset", "sample_requests.csv"))
    
    # Test specific users
    test_users = ['user_01', 'user_06', 'user_18', 'user_13', 'user_02']
    
    for user_id in test_users:
        print(f"\\n--- Testing {user_id} ---")
        
        # Get user request data
        user_request = sample_requests[sample_requests['user_id'] == user_id].iloc[0]
        request_date = pd.to_datetime(user_request['request_date']).date()
        expected_amount = Decimal(str(user_request['amount_safe_to_pay']))
        
        try:
            # Load user state
            user_state = UserState(user_id)
            load_financial_data(user_state, request_date)
            
            # Simulate 90 days
            end_date = request_date + datetime.timedelta(days=90)
            
            # Get current balance and minimum
            current_balance = user_state.get_balance()
            min_balance = user_state.get_minimum_balance()
            
            print(f"Starting balance: {current_balance}")
            print(f"Minimum balance: {min_balance}")
            
            # Apply base events (pending, scheduled, settled in window)
            balance = current_balance
            base_events_applied = 0
            
            for event in user_state.events:
                if (event.status in ('settled', 'scheduled', 'pending') and 
                    request_date <= event.date <= end_date):
                    
                    if event.status == 'pending' and event.direction == 'debit':
                        balance -= event.amount
                        base_events_applied += 1
                    elif event.status != 'pending':
                        if event.direction == 'debit':
                            balance -= event.amount
                        else:
                            balance += event.amount
                        base_events_applied += 1
            
            print(f"Base events applied: {base_events_applied}")
            
            # Project recurring events using our optimized function
            projected_events = project_recurring_events(user_state.events, request_date, end_date, user_id)
            
            print(f"Projected events: {len(projected_events)}")
            
            # Apply projected events
            for proj_event in projected_events:
                if proj_event.direction == 'debit':
                    balance -= proj_event.amount
                    print(f"  Projected expense: -{proj_event.amount} ({proj_event.description})")
                else:
                    balance += proj_event.amount
                    print(f"  Projected income: +{proj_event.amount} ({proj_event.description})")
            
            # Calculate amount safe to pay
            predicted_amount = max(Decimal('0'), balance - min_balance)
            
            # Compare with expected
            diff = predicted_amount - expected_amount
            accuracy = (1 - (abs(diff) / expected_amount)) * 100 if expected_amount > 0 else 0
            
            print(f"Final balance: {balance}")
            print(f"Expected: {expected_amount}")
            print(f"Predicted: {predicted_amount}")
            print(f"Difference: {diff}")
            print(f"Accuracy: {accuracy:.1f}%")
            
            if accuracy >= 95:
                print("✅ EXCELLENT match!")
            elif accuracy >= 80:
                print("✓ Good match")
            else:
                print("✗ Needs improvement")
        
        except Exception as e:
            print(f"❌ Error testing {user_id}: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\\n" + "="*50)
    print("Test completed!")

if __name__ == "__main__":
    test_sample_users()