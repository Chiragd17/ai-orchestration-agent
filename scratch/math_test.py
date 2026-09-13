import sys, os, datetime
from decimal import Decimal
sys.path.append(os.path.abspath('code'))
from engine.data.state import build_user_state

def test_var_expense():
    state = build_user_state('user_04')
    
    # Calculate var max monthly
    var_events = [e for e in state.events if not e.recurring and e.direction == 'debit' and e.status not in ['cancelled', 'failed'] and e.type != 'investment']
    
    import collections
    monthly_spend = collections.defaultdict(Decimal)
    for e in var_events:
        monthly_spend[(e.date.year, e.date.month)] += (e.amount or Decimal(0))
        
    max_monthly = max(monthly_spend.values())
    print("Max monthly var:", max_monthly)
    
    # Base fixed expenses before June 15
    fixed = Decimal('1027900.0') + Decimal('332500.0') + Decimal('377150.0') + Decimal('1704300.0')
    print("Fixed before June 15:", fixed)
    
    # We want min_bal = 45355100? No, we want safe_to_pay = 8401800
    # min_bal = safe_to_pay + 30686600 = 39088400
    # min_bal = 52206950 - fixed - var
    # var = 52206950 - 39088400 - 3441850 = 9676700
    
    expected_var_deduction = Decimal('52206950') - Decimal('39088400') - fixed
    print("Expected var deduction before June 15:", expected_var_deduction)
    
    # Let's compare expected_var_deduction with max_monthly
    print("Ratio expected / max_monthly:", expected_var_deduction / max_monthly)
    
if __name__ == '__main__':
    test_var_expense()
