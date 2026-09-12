# Phase 3: Candidate Generation & Ranking

| Request ID | Expected Status | Predicted Status | Match | Expected Method | Predicted Method |
|---|---|---|---|---|---|
| request_01 | affordable_now | affordable_now | ✅ | full_payment | full_payment |
| request_02 | affordable_with_plan | affordable_with_plan | ✅ | installments | installments |
| request_03 | affordable_later | affordable_later | ✅ | wait | wait |
| request_04 | affordable_later | affordable_now | ❌ | wait | full_payment |
| request_05 | not_affordable | affordable_now | ❌ | not_recommended | full_payment |
| request_07 | affordable_with_plan | affordable_with_plan | ✅ | installments | installments |
| request_08 | affordable_later | not_affordable | ❌ | wait | not_recommended |
| request_09 | affordable_now | affordable_now | ✅ | full_payment | full_payment |
| request_10 | not_affordable | not_affordable | ✅ | not_recommended | not_recommended |
| request_12 | affordable_with_plan | affordable_with_plan | ✅ | installments | installments |
| request_13 | affordable_later | affordable_now | ❌ | wait | full_payment |
| request_14 | not_affordable | affordable_with_plan | ❌ | not_recommended | partial_payment |
| request_15 | not_affordable | not_affordable | ✅ | not_recommended | not_recommended |
| request_16 | affordable_now | affordable_now | ✅ | full_payment | full_payment |
| request_17 | affordable_with_plan | affordable_with_plan | ✅ | installments | installments |
| request_18 | affordable_later | affordable_later | ✅ | wait | wait |
| request_19 | affordable_with_plan | affordable_with_plan | ❌ | partial_payment | installments |
| request_20 | not_affordable | not_affordable | ✅ | not_recommended | not_recommended |
| request_22 | affordable_with_plan | affordable_with_plan | ✅ | installments | installments |
| request_23 | affordable_later | affordable_later | ✅ | wait | wait |
| request_24 | not_affordable | not_affordable | ✅ | not_recommended | not_recommended |
| request_25 | not_affordable | affordable_later | ❌ | not_recommended | wait |

**Total Matches (No Spending Changes): 15 / 22**