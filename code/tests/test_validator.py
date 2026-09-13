from decimal import Decimal
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from output.validator import validate_row

def test_validator():
    print("Testing output validator...")
    
    # 1. Valid row (affordable_now)
    valid_row_1 = {
        "amount_safe_to_pay": "100.00",
        "affordability_status": "affordable_now",
        "recommended_payment_method": "full_payment",
        "payment_plan": "2026-09-12:100.00",
        "earliest_date_for_full_payment": "2026-09-12",
        "spending_changes_needed": "none"
    }
    errs = validate_row(valid_row_1, "2026-09-12", Decimal("100.00"))
    assert not errs, f"Expected 0 errors, got {errs}"

    # 2. Valid row (partial_payment)
    valid_row_2 = {
        "amount_safe_to_pay": "40.00",
        "affordability_status": "affordable_with_plan",
        "recommended_payment_method": "partial_payment",
        "payment_plan": "2026-09-12:40.00|2026-10-12:60.00",
        "earliest_date_for_full_payment": "2026-10-12",
        "spending_changes_needed": "stop:event_10|reduce_to:event_11:50"
    }
    errs = validate_row(valid_row_2, "2026-09-12", Decimal("100.00"))
    assert not errs, f"Expected 0 errors, got {errs}"

    # 3. Deliberately broken row (multiple violations)
    broken_row = {
        "amount_safe_to_pay": "150.00", # > requested amount
        "affordability_status": "affordable_now",
        "recommended_payment_method": "partial_payment",
        "payment_plan": "2026-09-12:40.00|2026-08-12:60.00|2026-11-12:50.00", # not chronological, partial has 3 entries
        "earliest_date_for_full_payment": "2026-10-12", # != request_date
        "spending_changes_needed": "stop:event_10|reduce_to:event_10:50|stop:event_12|stop:event_13" # overlap event_10, > 3 entries
    }
    
    errs = validate_row(broken_row, "2026-09-12", Decimal("100.00"))
    assert len(errs) > 0, "Expected multiple errors, got 0"
    
    print(f"Validation caught {len(errs)} errors in the broken row:")
    for e in errs:
        print(f" - {e}")
        
    print("Validator test PASS")

if __name__ == "__main__":
    test_validator()
