def format_spending_changes(changes: list[dict]) -> str:
    """
    Formats a list of spending changes into the required string format:
    stop:<event_id>|reduce_to:<event_id>:<amount>
    Returns 'none' if empty.
    """
    if not changes:
        return "none"
    
    parts = []
    for c in changes:
        if c["type"] == "stop":
            parts.append(f"stop:{c['event_id']}")
        elif c["type"] == "reduce":
            amt = float(c['amount'])
            amt_str = str(int(amt)) if amt.is_integer() else str(amt)
            parts.append(f"reduce_to:{c['event_id']}:{amt_str}")
            
    return "|".join(parts)


def format_payment_plan(plan_entries: list[tuple]) -> str:
    """
    Formats a list of (date, amount) tuples into the required string format:
    YYYY-MM-DD:amount|YYYY-MM-DD:amount
    Returns 'none' if empty.
    """
    if not plan_entries:
        return "none"
        
    parts = []
    for dt, amt in plan_entries:
        date_str = dt.isoformat() if hasattr(dt, "isoformat") else str(dt)
        f_amt = float(amt)
        amt_str = str(int(f_amt)) if f_amt.is_integer() else str(f_amt)
        parts.append(f"{date_str}:{amt_str}")
        
    return "|".join(parts)
