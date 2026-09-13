# HackerRank Orchestrate: Buy or Wait? - Problem Statement

## Challenge Overview
Build an AI-powered financial agent that analyzes users' financial situations and makes recommendations for purchase or payment requests. For every request, decide whether the user should:
- Pay in full immediately
- Pay partially with a plan  
- Wait for better timing
- Not proceed with the payment

## Input Data Structure

### Core Files
- **`requests.csv`**: 250 evaluation requests requiring predictions
- **`financial_profiles.csv`**: User financial profiles with balances and preferences
- **`financial_events.csv`**: Historical and future financial transactions
- **`request_payment_options.csv`**: Available payment methods per request
- **`exchange_rates.csv`**: Currency conversion rates for multi-currency events

### Supporting Data
- **`sample_requests.csv`**: 25 solved examples for reference
- **`messages.csv`**: Optional text messages providing context
- **`images.csv`**: Optional financial documents (receipts, statements)

## Required Output Format

Generate `output.csv` with these exact columns:

```csv
request_id,amount_safe_to_pay,affordability_status,recommended_payment_method,payment_plan,earliest_date_for_full_payment,spending_changes_needed,decision_explanation
```

### Column Specifications
- **`amount_safe_to_pay`**: Amount safe to pay on request date (0 to requested_amount)
- **`affordability_status`**: One of `affordable_now`, `affordable_with_plan`, `affordable_later`, `not_affordable`
- **`recommended_payment_method`**: One of `full_payment`, `partial_payment`, `installments`, `wait`, `not_recommended`
- **`payment_plan`**: Chronological payments as `YYYY-MM-DD:amount` separated by `|`, or `none`
- **`earliest_date_for_full_payment`**: First safe date for full payment, or empty if not possible
- **`spending_changes_needed`**: Required spending adjustments, or `none`
- **`decision_explanation`**: Concise explanation of the recommendation

## Financial Decision Rules

### Core Principles
1. **User safety first**: Never recommend payments that would put users at financial risk
2. **Respect minimum balance**: Account for the user's required minimum balance to keep
3. **Consider essential expenses**: Project recurring bills, rent, debt payments
4. **Account for pending transactions**: Reserve funds for scheduled debits
5. **Respect user preferences**: Honor payment preferences and protected spending categories

### Projection Logic
- **Income**: Only count confirmed, settled income; be conservative with projections
- **Expenses**: Project essential recurring costs (subscriptions, rent, debt payments)
- **Variable expenses**: Use historical patterns for protected spending categories
- **Currency handling**: Apply exchange rates for foreign currency transactions
- **Time horizon**: Typically project 90 days from request date

### Risk Assessment
- **Conservative approach**: Better to recommend waiting than cause financial stress
- **Safety buffers**: Account for unexpected expenses or income delays
- **Data quality**: Handle gaps in historical data appropriately
- **Message integration**: Use optional messages to clarify or amend financial facts

## Evaluation Criteria
Solutions are evaluated on accuracy of financial recommendations, particularly:
- **Mathematical precision** in amount_safe_to_pay calculations
- **Realistic affordability assessments** that protect user financial health
- **Appropriate timing recommendations** for payment scheduling
- **Sound financial reasoning** in decision explanations

## Success Metrics
- Accuracy on amount_safe_to_pay predictions
- Realistic distribution of affordability statuses
- Conservative risk management approach
- Clear, actionable financial guidance