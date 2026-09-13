import re
from datetime import datetime
from decimal import Decimal

def validate_row(
    row: dict,
    request_date_str: str,
    requested_amount: Decimal,
    available_payment_options: list[dict] = None
) -> list[str]:
    """
    Validates a generated prediction row against all rules in Phase 6.
    Returns a list of error strings. Empty list means the row is fully valid.
    """
    errors = []
    if available_payment_options is None:
        available_payment_options = []

    # Safe amount boundaries
    safe_amt = row.get("amount_safe_to_pay")
    try:
        safe_amt_d = Decimal(str(safe_amt))
        if not (0 <= safe_amt_d <= requested_amount):
            errors.append(f"amount_safe_to_pay {safe_amt_d} must be between 0 and {requested_amount}")
    except Exception:
        errors.append(f"Invalid amount_safe_to_pay: {safe_amt}")

    status = str(row.get("affordability_status", ""))
    method = str(row.get("recommended_payment_method", ""))
    plan_str = str(row.get("payment_plan", ""))
    earliest_date = str(row.get("earliest_date_for_full_payment", ""))
    changes_str = str(row.get("spending_changes_needed", ""))

    # 1. Payment Plan Format & Chronological Dates
    entries = []
    if plan_str.lower() != "none" and plan_str != "":
        plan_regex = r'^\d{4}-\d{2}-\d{2}:[0-9.]+$'
        parts = plan_str.split('|')
        prev_date = None
        for p in parts:
            if not re.match(plan_regex, p):
                errors.append(f"payment_plan entry '{p}' does not match <YYYY-MM-DD>:<amount>")
                continue
            d_str, a_str = p.split(':')
            try:
                dt = datetime.strptime(d_str, "%Y-%m-%d").date()
                amt = Decimal(a_str)
                entries.append((dt, amt))
                if prev_date and dt < prev_date:
                    errors.append("payment_plan dates are not in chronological order")
                prev_date = dt
            except Exception:
                errors.append(f"Invalid date/amount in payment_plan entry: {p}")

    # 2. Partial Payment Rules
    if method == "partial_payment":
        if len(entries) != 2:
            errors.append("partial_payment plan must have exactly 2 entries")
        else:
            total_plan_amt = sum(amt for _, amt in entries)
            if total_plan_amt != requested_amount:
                errors.append(f"partial_payment entries sum to {total_plan_amt}, but requested_amount is {requested_amount}")

    # 3. Affordable Now rule
    if status == "affordable_now":
        if earliest_date != request_date_str:
            errors.append(f"affordable_now requires earliest_date_for_full_payment to equal request_date ({request_date_str})")

    # 4. Non-safe-within-horizon rule
    # If not affordable at all, earliest_date should be blank.
    if status == "not_affordable":
        if earliest_date.strip() != "" and earliest_date.lower() != "none":
            errors.append("not_affordable rows must have earliest_date_for_full_payment blank")

    # 5. Spending Changes Needed formatting and logic
    if changes_str.lower() != "none" and changes_str != "":
        changes = changes_str.split('|')
        if len(changes) > 3:
            errors.append("spending_changes_needed has more than 3 entries")
        
        stopped = set()
        reduced = set()
        
        for c in changes:
            if c.startswith("stop:"):
                eid = c.split("stop:")[1]
                stopped.add(eid)
            elif c.startswith("reduce_to:"):
                parts = c.split(":")
                if len(parts) == 3:
                    eid = parts[1]
                    reduced.add(eid)
                else:
                    errors.append(f"Invalid reduce_to format: {c}")
            else:
                errors.append(f"Invalid spending_change format: {c}")
                
        intersection = stopped.intersection(reduced)
        if intersection:
            errors.append(f"spending_changes_needed has both stop and reduce_to for the same event(s): {intersection}")

    # 6. Installments rule
    if method == "installments":
        # Check if the generated plan matches any of the available_payment_options
        match_found = False
        generated_plan_str = plan_str
        for opt in available_payment_options:
            # Assume option dict has a pre-formatted 'schedule_str' we can compare against
            if opt.get("schedule_str") == generated_plan_str:
                match_found = True
                break
        
        # If no strict exact match but options were provided
        if not match_found and available_payment_options:
            errors.append(f"installments plan '{generated_plan_str}' does not exactly match any provided payment option schedule")

    return errors
