import sys
import os

# Add project root to python path to import engine
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)

from engine.data.state import build_user_state

def main():
    test_users = ['user_01', 'user_02', 'user_03']
    
    for uid in test_users:
        print(f"\n{'='*50}")
        print(f"Building state for {uid}...")
        try:
            state = build_user_state(uid)
            print(f"User: {state.user_id}")
            print(f"Home Currency: {state.home_currency}")
            print(f"Available Balance: {state.available_balance}")
            print(f"Minimum Balance: {state.minimum_balance_to_keep}")
            print(f"Events loaded: {len(state.events)}")
            
            # Print a few events
            print("\nSample Events:")
            for e in state.events[:3]: # First 3
                print(f"  - [{e.date}] {e.event_id}: {e.type} | Amount: {e.amount} | Status: {e.status} | Rec: {e.recurring} | Flex: {e.flexible}")
            
            # Print upcoming salary specifically if any exists
            salaries = [e for e in state.events if e.type == 'income' and e.recurring and e.status in ['scheduled', 'pending', 'confirmed']]
            if salaries:
                print("\nConfirmed Salary Events:")
                for e in salaries[:2]:
                    print(f"  - [{e.date}] {e.event_id}: {e.type} | Amount: {e.amount} | Status: {e.status} | Rec: {e.recurring} | Linked: {e.linked_event_id}")
            else:
                print("\nNo confirmed salary events found (might be categorized under generic income).")
                
            # Check for missing amounts
            missing_amounts = [e for e in state.events if e.amount is None]
            if missing_amounts:
                print(f"\nFound {len(missing_amounts)} events with missing amounts (None).")
                print(f"  Example: {missing_amounts[0].event_id}")
                
        except Exception as ex:
            print(f"ERROR while building {uid}: {ex}")

if __name__ == "__main__":
    main()
