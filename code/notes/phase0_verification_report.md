## 1. Schema Check

### exchange_rates.csv
- **Shape**: (134, 4)
- **Columns, Dtypes, and Nulls**:

| Column | Dtype | Null Count |
|---|---|---|
| rate_date | str | 0 |
| from_currency | str | 0 |
| to_currency | str | 0 |
| rate | float64 | 0 |


### financial_events.csv
- **Shape**: (25342, 14)
- **Columns, Dtypes, and Nulls**:

| Column | Dtype | Null Count |
|---|---|---|
| event_id | str | 0 |
| user_id | str | 0 |
| event_type | str | 0 |
| description | str | 0 |
| category | str | 0 |
| direction | str | 0 |
| amount | float64 | 16 |
| currency | str | 0 |
| event_date | str | 0 |
| settlement_date | str | 10 |
| status | str | 0 |
| linked_event_id | str | 25284 |
| flexibility | str | 0 |
| minimum_allowed_amount | float64 | 22435 |


### financial_profiles.csv
- **Shape**: (275, 10)
- **Columns, Dtypes, and Nulls**:

| Column | Dtype | Null Count |
|---|---|---|
| user_id | str | 0 |
| home_currency | str | 0 |
| current_available_balance | float64 | 0 |
| minimum_balance_to_keep | int64 | 0 |
| financial_priorities | str | 0 |
| expense_categories_to_protect | str | 0 |
| expense_categories_user_is_willing_to_reduce | str | 39 |
| expense_categories_user_is_willing_to_stop | str | 62 |
| payment_methods_user_will_consider | str | 0 |
| max_installment_months | float64 | 119 |


### images.csv
- **Shape**: (16, 4)
- **Columns, Dtypes, and Nulls**:

| Column | Dtype | Null Count |
|---|---|---|
| image_id | str | 0 |
| user_id | str | 0 |
| request_id | str | 0 |
| related_event_id | str | 0 |


### messages.csv
- **Shape**: (215, 7)
- **Columns, Dtypes, and Nulls**:

| Column | Dtype | Null Count |
|---|---|---|
| message_id | str | 0 |
| user_id | str | 0 |
| request_id | str | 87 |
| related_event_id | str | 176 |
| sent_at | str | 0 |
| source_type | str | 0 |
| message_text | str | 0 |


### output.csv
- **Shape**: (250, 8)
- **Columns, Dtypes, and Nulls**:

| Column | Dtype | Null Count |
|---|---|---|
| request_id | str | 0 |
| amount_safe_to_pay | float64 | 250 |
| affordability_status | float64 | 250 |
| recommended_payment_method | float64 | 250 |
| payment_plan | float64 | 250 |
| earliest_date_for_full_payment | float64 | 250 |
| spending_changes_needed | float64 | 250 |
| decision_explanation | float64 | 250 |


### request_payment_options.csv
- **Shape**: (790, 9)
- **Columns, Dtypes, and Nulls**:

| Column | Dtype | Null Count |
|---|---|---|
| payment_option_id | str | 0 |
| request_id | str | 0 |
| payment_method | str | 0 |
| payment_amount | float64 | 0 |
| number_of_payments | int64 | 0 |
| first_payment_date | str | 0 |
| payment_frequency_days | float64 | 275 |
| financing_fee | float64 | 0 |
| total_payable_amount | float64 | 0 |


### requests.csv
- **Shape**: (250, 8)
- **Columns, Dtypes, and Nulls**:

| Column | Dtype | Null Count |
|---|---|---|
| request_id | str | 0 |
| user_id | str | 0 |
| request_date | str | 0 |
| request_type | str | 0 |
| requested_amount | float64 | 0 |
| desired_completion_date | str | 0 |
| allows_partial_payment | bool | 0 |
| request_text | str | 0 |


### sample_requests.csv
- **Shape**: (25, 15)
- **Columns, Dtypes, and Nulls**:

| Column | Dtype | Null Count |
|---|---|---|
| request_id | str | 0 |
| user_id | str | 0 |
| request_date | str | 0 |
| request_type | str | 0 |
| requested_amount | float64 | 0 |
| desired_completion_date | str | 0 |
| allows_partial_payment | bool | 0 |
| request_text | str | 0 |
| amount_safe_to_pay | float64 | 0 |
| affordability_status | str | 0 |
| recommended_payment_method | str | 0 |
| payment_plan | str | 0 |
| earliest_date_for_full_payment | str | 7 |
| spending_changes_needed | str | 0 |
| decision_explanation | str | 0 |


## 2. Blank-Amount Resolution

- **event_253**: âŒ Traced to `image_01.png`, but OCR failed: 404 NOT_FOUND. {'error': {'code': 404, 'message': 'This model models/gemini-2.5-flash is no longer available to new users. Please update your code to use models/gemini-3.6-flash for the latest features and improvements. We recommend you to use the Interactions API.', 'status': 'NOT_FOUND'}}
- **event_1442**: âŒ Traced to `image_02.png`, but OCR failed: 404 NOT_FOUND. {'error': {'code': 404, 'message': 'This model models/gemini-2.5-flash is no longer available to new users. Please update your code to use models/gemini-3.6-flash for the latest features and improvements. We recommend you to use the Interactions API.', 'status': 'NOT_FOUND'}}
- **event_1545**: âŒ Traced to `image_03.png`, but OCR failed: 404 NOT_FOUND. {'error': {'code': 404, 'message': 'This model models/gemini-2.5-flash is no longer available to new users. Please update your code to use models/gemini-3.6-flash for the latest features and improvements. We recommend you to use the Interactions API.', 'status': 'NOT_FOUND'}}
- **event_1700**: âŒ Traced to `image_04.png`, but OCR failed: 404 NOT_FOUND. {'error': {'code': 404, 'message': 'This model models/gemini-2.5-flash is no longer available to new users. Please update your code to use models/gemini-3.6-flash for the latest features and improvements. We recommend you to use the Interactions API.', 'status': 'NOT_FOUND'}}
- **event_1786**: âŒ Traced to `image_05.png`, but OCR failed: 404 NOT_FOUND. {'error': {'code': 404, 'message': 'This model models/gemini-2.5-flash is no longer available to new users. Please update your code to use models/gemini-3.6-flash for the latest features and improvements. We recommend you to use the Interactions API.', 'status': 'NOT_FOUND'}}
- **event_3051**: âŒ Traced to `image_06.png`, but OCR failed: 404 NOT_FOUND. {'error': {'code': 404, 'message': 'This model models/gemini-2.5-flash is no longer available to new users. Please update your code to use models/gemini-3.6-flash for the latest features and improvements. We recommend you to use the Interactions API.', 'status': 'NOT_FOUND'}}
- **event_3231**: âŒ Traced to `image_07.png`, but OCR failed: 404 NOT_FOUND. {'error': {'code': 404, 'message': 'This model models/gemini-2.5-flash is no longer available to new users. Please update your code to use models/gemini-3.6-flash for the latest features and improvements. We recommend you to use the Interactions API.', 'status': 'NOT_FOUND'}}
- **event_4535**: âŒ Traced to `image_08.png`, but OCR failed: 404 NOT_FOUND. {'error': {'code': 404, 'message': 'This model models/gemini-2.5-flash is no longer available to new users. Please update your code to use models/gemini-3.6-flash for the latest features and improvements. We recommend you to use the Interactions API.', 'status': 'NOT_FOUND'}}
- **event_5170**: âŒ Traced to `image_09.png`, but OCR failed: 404 NOT_FOUND. {'error': {'code': 404, 'message': 'This model models/gemini-2.5-flash is no longer available to new users. Please update your code to use models/gemini-3.6-flash for the latest features and improvements. We recommend you to use the Interactions API.', 'status': 'NOT_FOUND'}}
- **event_6033**: âŒ Traced to `image_10.png`, but OCR failed: 404 NOT_FOUND. {'error': {'code': 404, 'message': 'This model models/gemini-2.5-flash is no longer available to new users. Please update your code to use models/gemini-3.6-flash for the latest features and improvements. We recommend you to use the Interactions API.', 'status': 'NOT_FOUND'}}
- **event_6859**: âŒ Traced to `image_11.png`, but OCR failed: 404 NOT_FOUND. {'error': {'code': 404, 'message': 'This model models/gemini-2.5-flash is no longer available to new users. Please update your code to use models/gemini-3.6-flash for the latest features and improvements. We recommend you to use the Interactions API.', 'status': 'NOT_FOUND'}}
- **event_7307**: âŒ Traced to `image_12.png`, but OCR failed: 404 NOT_FOUND. {'error': {'code': 404, 'message': 'This model models/gemini-2.5-flash is no longer available to new users. Please update your code to use models/gemini-3.6-flash for the latest features and improvements. We recommend you to use the Interactions API.', 'status': 'NOT_FOUND'}}
- **event_7941**: âŒ Traced to `image_13.png`, but OCR failed: 404 NOT_FOUND. {'error': {'code': 404, 'message': 'This model models/gemini-2.5-flash is no longer available to new users. Please update your code to use models/gemini-3.6-flash for the latest features and improvements. We recommend you to use the Interactions API.', 'status': 'NOT_FOUND'}}
- **event_9421**: âŒ Traced to `image_14.png`, but OCR failed: 404 NOT_FOUND. {'error': {'code': 404, 'message': 'This model models/gemini-2.5-flash is no longer available to new users. Please update your code to use models/gemini-3.6-flash for the latest features and improvements. We recommend you to use the Interactions API.', 'status': 'NOT_FOUND'}}
- **event_9806**: âŒ Traced to `image_15.png`, but OCR failed: 404 NOT_FOUND. {'error': {'code': 404, 'message': 'This model models/gemini-2.5-flash is no longer available to new users. Please update your code to use models/gemini-3.6-flash for the latest features and improvements. We recommend you to use the Interactions API.', 'status': 'NOT_FOUND'}}
- **event_10521**: âŒ Traced to `image_16.png`, but OCR failed: 404 NOT_FOUND. {'error': {'code': 404, 'message': 'This model models/gemini-2.5-flash is no longer available to new users. Please update your code to use models/gemini-3.6-flash for the latest features and improvements. We recommend you to use the Interactions API.', 'status': 'NOT_FOUND'}}


## 3. Linked-Event Chains

- event_99 (refund) -> event_98 (expense): partial or full reversal
- event_101 (expense) -> event_100 (expense): subsequent fee or adjustment
- event_1544 (refund) -> event_1543 (expense): partial or full reversal
- event_1785 (refund) -> event_1784 (expense): partial or full reversal
- event_1856 (investment_valuation) -> event_1855 (investment_purchase): unrealized market value update
- event_1960 (investment_valuation) -> event_1959 (investment_purchase): unrealized market value update
- event_2361 (refund) -> event_2360 (expense): partial or full reversal
- event_2363 (expense) -> event_2362 (expense): subsequent fee or adjustment
- event_3230 (refund) -> event_3229 (expense): partial or full reversal
- event_4994 (refund) -> event_4993 (expense): partial or full reversal
- event_5169 (debt_payment) -> event_5168 (debt_payment): subsequent installment or fee
- event_6290 (expense) -> event_6289 (expense): subsequent fee or adjustment
- event_6532 (investment_valuation) -> event_6531 (investment_purchase): unrealized market value update
- event_6858 (refund) -> event_6857 (expense): partial or full reversal
- event_7186 (refund) -> event_7185 (expense): partial or full reversal
- event_7306 (investment_sale) -> event_7305 (investment_purchase): realized sale proceeds
- event_8576 (debt_payment) -> event_8575 (debt_payment): subsequent installment or fee
- event_9805 (investment_valuation) -> event_9804 (investment_purchase): unrealized market value update
- event_10043 (expense) -> event_10042 (expense): subsequent fee or adjustment
- event_10802 (refund) -> event_10801 (expense): partial or full reversal
- event_11127 (refund) -> event_11126 (expense): partial or full reversal
- event_11129 (investment_sale) -> event_11128 (investment_purchase): realized sale proceeds
- event_12382 (investment_sale) -> event_12381 (investment_purchase): realized sale proceeds
- event_12709 (expense) -> event_12708 (expense): subsequent fee or adjustment
- event_12809 (debt_payment) -> event_12808 (debt_payment): subsequent installment or fee
- event_13032 (investment_sale) -> event_13031 (investment_purchase): realized sale proceeds
- event_13492 (refund) -> event_13491 (expense): partial or full reversal
- event_13663 (investment_sale) -> event_13662 (investment_purchase): realized sale proceeds
- event_13745 (refund) -> event_13744 (expense): partial or full reversal
- event_13747 (expense) -> event_13746 (expense): subsequent fee or adjustment
- event_14026 (refund) -> event_14025 (expense): partial or full reversal
- event_14399 (expense) -> event_14398 (expense): subsequent fee or adjustment
- event_15327 (refund) -> event_15326 (expense): partial or full reversal
- event_16691 (debt_payment) -> event_16690 (debt_payment): subsequent installment or fee
- event_17401 (refund) -> event_17400 (expense): partial or full reversal
- event_17579 (expense) -> event_17578 (expense): subsequent fee or adjustment
- event_17662 (refund) -> event_17661 (expense): partial or full reversal
- event_18269 (expense) -> event_18268 (expense): subsequent fee or adjustment
- event_19182 (investment_valuation) -> event_19181 (investment_purchase): unrealized market value update
- event_19334 (expense) -> event_19333 (expense): subsequent fee or adjustment
- event_19753 (refund) -> event_19752 (expense): partial or full reversal
- event_20129 (refund) -> event_20128 (expense): partial or full reversal
- event_20379 (refund) -> event_20378 (expense): partial or full reversal
- event_20615 (refund) -> event_20614 (expense): partial or full reversal
- event_21102 (debt_payment) -> event_21101 (debt_payment): subsequent installment or fee
- event_21307 (expense) -> event_21306 (expense): subsequent fee or adjustment
- event_21309 (investment_valuation) -> event_21308 (investment_purchase): unrealized market value update
- event_21582 (expense) -> event_21581 (expense): subsequent fee or adjustment
- event_21785 (investment_valuation) -> event_21784 (investment_purchase): unrealized market value update
- event_22361 (investment_valuation) -> event_22360 (investment_purchase): unrealized market value update
- event_23203 (expense) -> event_23202 (expense): subsequent fee or adjustment
- event_23307 (debt_payment) -> event_23306 (debt_payment): subsequent installment or fee
- event_23856 (debt_payment) -> event_23855 (debt_payment): subsequent installment or fee
- event_24056 (refund) -> event_24055 (expense): partial or full reversal
- event_24352 (investment_valuation) -> event_24351 (investment_purchase): unrealized market value update
- event_24534 (investment_valuation) -> event_24533 (investment_purchase): unrealized market value update
- event_25074 (expense) -> event_25073 (expense): subsequent fee or adjustment
- event_25342 (refund) -> event_25341 (expense): partial or full reversal


## 4. Message Classification

Failed to classify chunk starting at 0: 404 NOT_FOUND. {'error': {'code': 404, 'message': 'This model models/gemini-2.5-flash is no longer available to new users. Please update your code to use models/gemini-3.6-flash for the latest features and improvements. We recommend you to use the Interactions API.', 'status': 'NOT_FOUND'}}
Failed to classify chunk starting at 50: 404 NOT_FOUND. {'error': {'code': 404, 'message': 'This model models/gemini-2.5-flash is no longer available to new users. Please update your code to use models/gemini-3.6-flash for the latest features and improvements. We recommend you to use the Interactions API.', 'status': 'NOT_FOUND'}}
Failed to classify chunk starting at 100: 404 NOT_FOUND. {'error': {'code': 404, 'message': 'This model models/gemini-2.5-flash is no longer available to new users. Please update your code to use models/gemini-3.6-flash for the latest features and improvements. We recommend you to use the Interactions API.', 'status': 'NOT_FOUND'}}
Failed to classify chunk starting at 150: 404 NOT_FOUND. {'error': {'code': 404, 'message': 'This model models/gemini-2.5-flash is no longer available to new users. Please update your code to use models/gemini-3.6-flash for the latest features and improvements. We recommend you to use the Interactions API.', 'status': 'NOT_FOUND'}}
Failed to classify chunk starting at 200: 404 NOT_FOUND. {'error': {'code': 404, 'message': 'This model models/gemini-2.5-flash is no longer available to new users. Please update your code to use models/gemini-3.6-flash for the latest features and improvements. We recommend you to use the Interactions API.', 'status': 'NOT_FOUND'}}
## 5. Sample Reconciliation

### request_01 (user_01)
- **Actual**: Safe: 25256.0 | Status: affordable_now | Plan: 2024-03-03:25256
- **Calculated**: Safe: 40481.10 | Status: affordable_now
- **Result**: âŒ DIVERGENCE
  - **Why**: The crude prototype didn't account for messages, missing OCR amounts, precise settlement dates, or exchange rates. Ground truth is strictly correct.

### request_02 (user_02)
- **Actual**: Safe: 17229139.2 | Status: affordable_with_plan | Plan: 2025-08-08:15952906.67|2025-09-07:15952906.67|2025-10-07:15952906.67
- **Calculated**: Safe: 31225489.20 | Status: affordable_with_plan
- **Result**: âŒ DIVERGENCE
  - **Why**: The crude prototype didn't account for messages, missing OCR amounts, precise settlement dates, or exchange rates. Ground truth is strictly correct.

### request_03 (user_03)
- **Actual**: Safe: 873000.0 | Status: affordable_later | Plan: 2019-11-15:5491000
- **Calculated**: Safe: 3141600.00 | Status: affordable_with_plan
- **Result**: âŒ DIVERGENCE
  - **Why**: The crude prototype didn't account for messages, missing OCR amounts, precise settlement dates, or exchange rates. Ground truth is strictly correct.

### request_04 (user_04)
- **Actual**: Safe: 8401800.0 | Status: affordable_later | Plan: 2024-06-15:12693000
- **Calculated**: Safe: 19816050.00 | Status: affordable_now
- **Result**: âŒ DIVERGENCE
  - **Why**: The crude prototype didn't account for messages, missing OCR amounts, precise settlement dates, or exchange rates. Ground truth is strictly correct.

### request_05 (user_05)
- **Actual**: Safe: 737.0 | Status: not_affordable | Plan: none
- **Calculated**: Safe: 33375.10 | Status: affordable_now
- **Result**: âŒ DIVERGENCE
  - **Why**: The crude prototype didn't account for messages, missing OCR amounts, precise settlement dates, or exchange rates. Ground truth is strictly correct.

### request_06 (user_06)
- **Actual**: Safe: 603.3 | Status: affordable_with_plan | Plan: 2026-01-03:620.40
- **Calculated**: Safe: 1142.40 | Status: affordable_now
- **Result**: âŒ DIVERGENCE
  - **Why**: The crude prototype didn't account for messages, missing OCR amounts, precise settlement dates, or exchange rates. Ground truth is strictly correct.

### request_07 (user_07)
- **Actual**: Safe: 87170.56 | Status: affordable_with_plan | Plan: 2024-09-12:68432|2024-10-10:68432|2024-11-07:68432
- **Calculated**: Safe: 125945.56 | Status: affordable_with_plan
- **Result**: âŒ DIVERGENCE
  - **Why**: The crude prototype didn't account for messages, missing OCR amounts, precise settlement dates, or exchange rates. Ground truth is strictly correct.

### request_08 (user_08)
- **Actual**: Safe: 284.57 | Status: affordable_later | Plan: 2025-04-15:996.60
- **Calculated**: Safe: 736.57 | Status: affordable_with_plan
- **Result**: âŒ DIVERGENCE
  - **Why**: The crude prototype didn't account for messages, missing OCR amounts, precise settlement dates, or exchange rates. Ground truth is strictly correct.

### request_09 (user_09)
- **Actual**: Safe: 166.61 | Status: affordable_now | Plan: 2026-07-04:166.61
- **Calculated**: Safe: 1631.10 | Status: affordable_now
- **Result**: âŒ DIVERGENCE
  - **Why**: The crude prototype didn't account for messages, missing OCR amounts, precise settlement dates, or exchange rates. Ground truth is strictly correct.

### request_10 (user_10)
- **Actual**: Safe: 12700.0 | Status: not_affordable | Plan: none
- **Calculated**: Safe: 524755.00 | Status: affordable_now
- **Result**: âŒ DIVERGENCE
  - **Why**: The crude prototype didn't account for messages, missing OCR amounts, precise settlement dates, or exchange rates. Ground truth is strictly correct.

### request_11 (user_11)
- **Actual**: Safe: 12510645.0 | Status: affordable_with_plan | Plan: 2025-05-03:13110000
- **Calculated**: Safe: 29391195.00 | Status: affordable_now
- **Result**: âŒ DIVERGENCE
  - **Why**: The crude prototype didn't account for messages, missing OCR amounts, precise settlement dates, or exchange rates. Ground truth is strictly correct.

### request_12 (user_12)
- **Actual**: Safe: 65164.0 | Status: affordable_with_plan | Plan: 2026-04-19:22590.19|2026-05-20:22590.19|2026-06-20:22590.19
- **Calculated**: Safe: 149889.89 | Status: affordable_now
- **Result**: âŒ DIVERGENCE
  - **Why**: The crude prototype didn't account for messages, missing OCR amounts, precise settlement dates, or exchange rates. Ground truth is strictly correct.

### request_13 (user_13)
- **Actual**: Safe: 433.4 | Status: affordable_later | Plan: 2024-05-15:941.60
- **Calculated**: Safe: 1489.52 | Status: affordable_now
- **Result**: âŒ DIVERGENCE
  - **Why**: The crude prototype didn't account for messages, missing OCR amounts, precise settlement dates, or exchange rates. Ground truth is strictly correct.

### request_14 (user_14)
- **Actual**: Safe: 597.74 | Status: not_affordable | Plan: none
- **Calculated**: Safe: 1731.74 | Status: affordable_with_plan
- **Result**: âŒ DIVERGENCE
  - **Why**: The crude prototype didn't account for messages, missing OCR amounts, precise settlement dates, or exchange rates. Ground truth is strictly correct.

### request_15 (user_15)
- **Actual**: Safe: 83.05 | Status: not_affordable | Plan: none
- **Calculated**: Safe: 570.05 | Status: affordable_with_plan
- **Result**: âŒ DIVERGENCE
  - **Why**: The crude prototype didn't account for messages, missing OCR amounts, precise settlement dates, or exchange rates. Ground truth is strictly correct.

### request_16 (user_16)
- **Actual**: Safe: 122500.0 | Status: affordable_now | Plan: 2023-08-12:122500
- **Calculated**: Safe: 239970.00 | Status: affordable_now
- **Result**: âŒ DIVERGENCE
  - **Why**: The crude prototype didn't account for messages, missing OCR amounts, precise settlement dates, or exchange rates. Ground truth is strictly correct.

### request_17 (user_17)
- **Actual**: Safe: 243849.58 | Status: affordable_with_plan | Plan: 2026-03-01:95194.67|2026-03-31:95194.67|2026-04-30:95194.67
- **Calculated**: Safe: 384279.58 | Status: affordable_now
- **Result**: âŒ DIVERGENCE
  - **Why**: The crude prototype didn't account for messages, missing OCR amounts, precise settlement dates, or exchange rates. Ground truth is strictly correct.

### request_18 (user_18)
- **Actual**: Safe: 462.0 | Status: affordable_later | Plan: 2026-09-15:3246.10
- **Calculated**: Safe: 1086.00 | Status: affordable_with_plan
- **Result**: âŒ DIVERGENCE
  - **Why**: The crude prototype didn't account for messages, missing OCR amounts, precise settlement dates, or exchange rates. Ground truth is strictly correct.

### request_19 (user_19)
- **Actual**: Safe: 28820.0 | Status: affordable_with_plan | Plan: 2024-09-04:28820|2024-09-15:10840
- **Calculated**: Safe: 106745.00 | Status: affordable_now
- **Result**: âŒ DIVERGENCE
  - **Why**: The crude prototype didn't account for messages, missing OCR amounts, precise settlement dates, or exchange rates. Ground truth is strictly correct.

### request_20 (user_20)
- **Actual**: Safe: 5400.0 | Status: not_affordable | Plan: none
- **Calculated**: Safe: 38109.05 | Status: affordable_with_plan
- **Result**: âŒ DIVERGENCE
  - **Why**: The crude prototype didn't account for messages, missing OCR amounts, precise settlement dates, or exchange rates. Ground truth is strictly correct.

### request_21 (user_21)
- **Actual**: Safe: 1543.35 | Status: affordable_with_plan | Plan: 2026-04-03:1574.40
- **Calculated**: Safe: 2111.35 | Status: affordable_now
- **Result**: âŒ DIVERGENCE
  - **Why**: The crude prototype didn't account for messages, missing OCR amounts, precise settlement dates, or exchange rates. Ground truth is strictly correct.

### request_22 (user_22)
- **Actual**: Safe: 475.46 | Status: affordable_with_plan | Plan: 2024-12-08:253.59|2025-01-05:253.59|2025-02-02:253.59
- **Calculated**: Safe: 632.46 | Status: affordable_with_plan
- **Result**: âŒ DIVERGENCE
  - **Why**: The crude prototype didn't account for messages, missing OCR amounts, precise settlement dates, or exchange rates. Ground truth is strictly correct.

### request_23 (user_23)
- **Actual**: Safe: 9152.0 | Status: affordable_later | Plan: 2025-07-15:38016
- **Calculated**: Safe: 24957.90 | Status: affordable_with_plan
- **Result**: âŒ DIVERGENCE
  - **Why**: The crude prototype didn't account for messages, missing OCR amounts, precise settlement dates, or exchange rates. Ground truth is strictly correct.

### request_24 (user_24)
- **Actual**: Safe: 13420.0 | Status: not_affordable | Plan: none
- **Calculated**: Safe: 32215.00 | Status: affordable_with_plan
- **Result**: âŒ DIVERGENCE
  - **Why**: The crude prototype didn't account for messages, missing OCR amounts, precise settlement dates, or exchange rates. Ground truth is strictly correct.

### request_25 (user_25)
- **Actual**: Safe: 1425000.0 | Status: not_affordable | Plan: none
- **Calculated**: Safe: 8683950.00 | Status: affordable_with_plan
- **Result**: âŒ DIVERGENCE
  - **Why**: The crude prototype didn't account for messages, missing OCR amounts, precise settlement dates, or exchange rates. Ground truth is strictly correct.
