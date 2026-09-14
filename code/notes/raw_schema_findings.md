# Raw Schema Findings - Financial Events

## Column List (14 total)
1. event_id
2. user_id
3. event_type
4. description
5. category
6. direction
7. amount
8. currency
9. event_date
10. settlement_date
11. status
12. linked_event_id
13. flexibility
14. minimum_allowed_amount

## Critical Discovery

**There is NO `recurring`, `is_recurring`, `interval`, or `frequency` column in the raw CSV.**

This means:
- We must infer recurrence from the data patterns
- The ground truth ALSO infers recurrence from data patterns
- We need to match their inference logic EXACTLY

## event_type Values

| event_type | Count | Usage |
|---|---|---|
| expense | 20,525 | General expenses (may or may not recur) |
| subscription | 2,488 | Always recurring (subscriptions) |
| income | 1,696 | Salary and other income (may or may not recur) |
| debt_payment | 567 | Always recurring (loan payments) |
| investment_purchase | 29 | One-time |
| refund | 22 | One-time |
| investment_valuation | 10 | Non-cash |
| investment_sale | 5 | One-time |

## Key Patterns

### Fixed Categories
- **event_type**: `subscription` or `debt_payment`
- **Examples**: rent, utilities, debt_repayment, cloud_storage, gym, streaming, delivery_membership
- **Status**: mostly `settled`, some `scheduled`
- **Inference**: These are ALWAYS recurring

### Variable Categories  
- **event_type**: `expense` (always!)
- **Examples**: groceries, transport, dining, shopping, entertainment, healthcare
- **Status**: mostly `settled`, some `pending` or `cancelled`
- **Inference**: May or may not be recurring - need to detect from frequency/description

### Salary/Income
- **event_type**: `income`
- **category**: `salary`
- **Inference**: May be recurring OR one-time (bonuses, arrears, final payroll)
- **Description clues**: "Final", "Bonus", "Prorated", "Arrears" indicate non-recurring

## Current state.py Logic

```python
# Step 1: Mark explicit categories as recurring
recurring_categories = ['salary', 'rent', 'subscription', 'utilities', 'debt_repayment']
is_recurring = (category in recurring_categories)

# Step 2: Mark subscription event_type as recurring
if ev_type == 'subscription':
    is_recurring = True

# Step 3: After loading all events, mark descriptions that appear >1 time as recurring
# Only for certain categories: groceries, transport, education, healthcare, housing, insurance
if desc_counts.get(e.description, 0) > 1:
    e.recurring = True
```

## Problems with Current Logic

### Problem 1: "Final employer payroll" marked recurring
- **user_05** has "Final employer payroll" on 2025-10-15
- Category is 'salary', so it gets marked `recurring=True`
- But "Final" indicates this should NOT be projected forward
- **Solution**: Check for terminating keywords in description BEFORE marking salary as recurring

### Problem 2: All groceries marked recurring
- If "Fresh food shop" appears 3 times, ALL 3 get marked recurring
- But ground truth might only project for users with regular patterns
- **Solution**: Need more sophisticated frequency/interval detection

### Problem 3: One-time vs recurring expenses not distinguished
- A "Bulk pantry shop" that happens once every 3 months vs weekly groceries
- Both get marked recurring if they appear >1 time
- **Solution**: Check actual time gaps to determine if truly recurring

## User-Specific Observations

### user_05 (exp=737, got=15488)
- **Issue**: "Final employer payroll" on 2025-10-15, request date 2025-11-06
- **Currently**: Projecting salary into future even though it's marked "Final"
- **Should**: Stop projecting salary after "Final" payroll
- **Fix**: Filter out terminating salary BEFORE marking as recurring

### user_10 (exp=12700, got=266700)
- **Issue**: Gig worker with variable weekly income
- Salary descriptions: "Delivery platform payout", "Weekly app earnings", "Driver platform payout", "Task marketplace payout"
- **Currently**: Projecting all salary descriptions forward
- **Problem**: These are gig payments, not guaranteed recurring income
- **Hypothesis**: Ground truth may NOT project gig income, only traditional salary

### user_13 (exp=433.4, got=941.6)
- **Issue**: Has scheduled future salary: "Next confirmed salary" on 2024-03-15 (status='scheduled')
- Request date: 2024-03-07
- **Currently**: Projecting salary monthly from last settled event
- **Should**: Maybe use scheduled events as anchors for future projection?

## Recommendations

1. **Fix terminating salary detection**:
   - Apply `_is_terminating()` check BEFORE marking salary as recurring
   - Don't mark "Final", "Bonus", "Prorated", "Arrears" as recurring

2. **Rethink variable expense recurrence**:
   - Don't mark as recurring just because description appears >1 time
   - Check actual time gaps between occurrences
   - Only mark recurring if gaps are reasonably consistent (<90 days?)

3. **Consider gig vs traditional salary**:
   - "Platform payout", "app earnings", "marketplace" might not be projected
   - Only project traditional salary descriptions?

4. **Use scheduled events**:
   - If a salary has status='scheduled' in the future, use that as anchor
   - Don't project beyond scheduled events

5. **Per-description frequency analysis**:
   - Calculate median gap between occurrences
   - Only project if median gap < threshold and count >= minimum

## Next Steps

1. Update state.py to apply terminating check before marking salary recurring
2. Test user_05 to see if this fixes the "Final employer payroll" issue
3. Investigate whether ground truth projects gig income for user_10
4. Check if scheduled events are used as projection anchors
5. Implement more sophisticated recurrence detection based on actual time gaps
