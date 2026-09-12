# Dataset Understanding Notes (Phase 0)

## 1. Schema & Data Types

- **exchange_rates.csv**: 134 rows. Columns: `rate_date`, `from_currency`, `to_currency`, `rate`. No nulls.
- **financial_events.csv**: 25,342 rows. Important columns: `event_id`, `user_id`, `event_type`, `amount`, `currency`, `event_date`, `linked_event_id`. Nulls: `amount` (16), `settlement_date` (10), `linked_event_id` (25,284).
- **financial_profiles.csv**: 275 rows. Columns include `home_currency`, `current_available_balance`, `minimum_balance_to_keep`. Some nulls in optional expense categories.
- **images.csv**: 16 rows. Links `image_id` to `related_event_id`.
- **messages.csv**: 215 rows. Columns include `sent_at`, `message_text`.
- **sample_requests.csv**: 25 rows. Includes target outputs: `amount_safe_to_pay`, `affordability_status`, `recommended_payment_method`, `payment_plan`, etc.
- **requests.csv**: 250 rows. 

## 2. Sample User Event Tracing & Blank Amounts

Examined histories for `user_01`, `user_02`, and `user_03`.
- **user_01**: Steady expense events (ZAR), regular subscription deductions, periodic debt payments.
- **user_02**: Very high-value IDR expenses, regular high income. 
- **user_03**: IDR currency. **Flagged**: `event_253` on `2019-08-31` has a `BLANK AMOUNT` (NaN). 
  - Trace: `event_253` matches `related_event_id` in `images.csv`, pointing to `image_01.png`. The actual amount must be extracted from the image.

## 3. Linked Event Chains (Lifecycles)

Found 58 linked events in the dataset. Common patterns:
- `refund` -> `expense`: Reversal or partial refund of a previous expense.
- `investment_valuation` -> `investment_purchase`: Updates to the non-cash value of a previously purchased asset.
- `investment_sale` -> `investment_purchase`: Realizing the cash from an investment.
- `debt_payment` -> `debt_payment`: Adjustments or subsequent payments in a debt chain.
- `expense` -> `expense`: Adjustments or related fee linkages.

## 4. Message Classification

Based on a sample of `messages.csv`:
- **Confirm**: Approvals or finalizations. *e.g., "Gaji pokok yang dikonfirmasi adalah IDR 38760000" (Salary confirmed).*
- **Amend**: Changes to future expected values. *e.g., "Gaji bulanan Anda naik menjadi IDR 42750000" (Salary increased).*
- **Cancel**: End of a stream. *e.g., "Kontrak musiman saat ini telah berakhir" (Seasonal contract ended).*
- **Delay**: Shift in timing. *e.g., "Your refund has been initiated but has not reached your account yet."*
- **Irrelevant**: Informational only, no net cashflow impact. *e.g., "The matching debit and credit came from a transfer between your two accounts."*

## 5. Reasoning for Sample Requests Output

- **Request 01 (user_01, ZAR 25,256, Due: 2024-03-20)**
  - *amount_safe_to_pay*: 25,256
  - *affordability_status*: `affordable_now`
  - *recommended_payment_method*: `full_payment`
  - *payment_plan*: `2024-03-03:25256`
  - *Reasoning*: User has enough current balance + upcoming positive cash flow. Paying the full amount today does not push their 90-day simulated balance below `minimum_balance_to_keep`.

- **Request 02 (user_02, IDR 46,018,000, Due: 2025-10-10)**
  - *amount_safe_to_pay*: 17,229,139.2
  - *affordability_status*: `affordable_with_plan`
  - *recommended_payment_method*: `installments`
  - *payment_plan*: `2025-08-08:15952906.67|2025-09-07:15952906.67|2025-10-07:15952906.67`
  - *Reasoning*: The full amount would breach the minimum balance (only 17.2M is safe to pay today). However, the engine detects that an installment plan (3 payments of ~15.95M) fits within the simulated monthly cash flow bounds, completing before the desired completion date.

- **Request 03 (user_03, IDR 5,491,000, Due: 2019-11-15)**
  - *amount_safe_to_pay*: 873,000
  - *affordability_status*: `affordable_later`
  - *recommended_payment_method*: `wait`
  - *payment_plan*: `2019-11-15:5491000`
  - *Reasoning*: The user can only safely part with 873,000 today. However, based on projected income/expenses, they will accumulate enough cash to pay the full 5.49M on the deadline date (`2019-11-15`) without breaching their minimum balance of 2,668,700.

## 6. Ambiguities & Edge Cases

1. **Valuation vs. Cashflow**: `investment_valuation` events update the "displayed value" (as seen in some messages), but do not generate cash proceeds. The engine must ignore valuations for cashflow simulation and only look at `investment_sale`.
2. **Missing Amounts (Images)**: The engine requires an LLM call to extract the amount from `image_id.png` when `amount` is null. The extracted amount applies to the date of the event.
3. **Message Timestamps**: Messages must only be applied if their `sent_at` is *before or on* the `request_date`. Any future messages technically represent "future knowledge" and shouldn't be used to retroactively simulate the past.
4. **Boundary conditions**: A payment can be scheduled exactly on the `desired_completion_date` (as seen in Request 03 where both are `2019-11-15`).
