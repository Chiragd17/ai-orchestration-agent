import os
import sys
import json
import time
import datetime
from decimal import Decimal
import pandas as pd
from dotenv import load_dotenv

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
code_root = os.path.join(project_root, "code")
sys.path.insert(0, code_root)
load_dotenv(os.path.join(code_root, ".env"))

from groq import Groq
from engine.data.state import build_user_state

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
client = Groq(api_key=GROQ_API_KEY)
MODEL = "qwen/qwen3.8-27b"

SYSTEM_PROMPT = """You are an expert financial advisor AI for the "Buy or Wait?" challenge.
Your job is to determine if a user can afford a requested purchase/payment based on their financial profile, past/future events, and available payment options.

RULES:
1. 90-Day Forecast: You must project cash flow for 90 days starting from `request_date`.
2. Minimum Balance: The user's available balance must NEVER fall below `minimum_balance_to_keep` at any point in the 90-day window after paying essential bills.
3. Essential Expenses: recurring bills (rent, utilities, subscriptions, debt_repayment, salary) happen monthly. You must account for them. Also account for average variable essential spending (groceries, transport) if they occur frequently.
4. Payment Options: You can only recommend 'full_payment', 'partial_payment', 'installments', 'wait', or 'not_recommended'.
   - 'full_payment': Pay entire amount today.
   - 'partial_payment': Only if `allows_partial_payment` is true. Pay `amount_safe_to_pay` today, and the rest on `earliest_date_for_full_payment` (must be <= `desired_completion_date`).
   - 'installments': Only if an installment option is provided in the available options and the user hasn't opted out.
   - 'wait': Wait until `earliest_date_for_full_payment` and pay in full (must be <= `desired_completion_date`).
   - 'not_recommended': If none of the above keep the minimum balance safe.
5. Spending Changes: If needed to afford it, you can recommend up to 3 `stop:<event_id>` or `reduce_to:<event_id>:<new_amount>` actions for non-protected, flexible events.
6. amount_safe_to_pay: The amount they can safely pay on `request_date` without violating the minimum balance over the next 90 days (ignoring spending changes).

OUTPUT FORMAT (JSON):
Respond ONLY with a valid JSON object matching this schema exactly. Provide NO other text.
{
  "amount_safe_to_pay": "number as string (e.g. 1000.50)",
  "affordability_status": "affordable_now" | "affordable_with_plan" | "affordable_later" | "not_affordable",
  "recommended_payment_method": "full_payment" | "partial_payment" | "installments" | "wait" | "not_recommended",
  "payment_plan": "YYYY-MM-DD:AMOUNT|YYYY-MM-DD:AMOUNT" or "none",
  "earliest_date_for_full_payment": "YYYY-MM-DD" or "",
  "spending_changes_needed": "stop:event_1|reduce_to:event_2:50" or "none",
  "decision_explanation": "Concise 1-2 sentence explanation grounding the decision in numbers."
}
"""

def process_request_with_llm(req_row, payment_options):
    req_id = req_row["request_id"]
    user_id = req_row["user_id"]
    req_date = str(req_row["request_date"])
    req_amt = str(req_row["requested_amount"])
    deadline = str(req_row["desired_completion_date"])
    
    try:
        state = build_user_state(user_id)
    except Exception as e:
        print(f"Error building state for {user_id}: {e}")
        return None

    events_str = ""
    for ev in sorted(state.events, key=lambda x: str(x.date)):
        events_str += f"- [{ev.date}] {ev.event_id} ({ev.type}, {ev.category}): {ev.amount} {state.home_currency} ({ev.direction}) | Recurring: {ev.recurring} | Flex: {ev.flexibility}\n"

    opts_str = ""
    for opt in payment_options:
        opts_str += f"- {opt['payment_method']}: "
        if opt['payment_method'] == 'installments':
            opts_str += f"{opt['number_of_payments']} payments of {opt['payment_amount']} starting {opt['first_payment_date']} every {opt['payment_frequency_days']} days\n"
        else:
            opts_str += "\n"

    user_prompt = f"""
REQUEST DETAILS:
Request ID: {req_id}
Date: {req_date}
Amount Requested: {req_amt} {state.home_currency}
Type: {req_row["request_type"]}
Deadline: {deadline}
Allows Partial: {req_row["allows_partial_payment"]}
Text: {req_row["request_text"]}

AVAILABLE PAYMENT OPTIONS:
{opts_str if opts_str else "None"}

USER PROFILE:
Home Currency: {state.home_currency}
Current Balance (on request date): {state.available_balance}
Minimum Balance to Keep: {state.minimum_balance_to_keep}
Priorities: {state.financial_priorities}
Payment Prefs: {state.payment_methods_user_will_consider}
Spending Prefs: {state.spending_preferences}

FINANCIAL EVENTS (Past & Scheduled):
{events_str}

Analyze the data and output the JSON decision.
"""

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt}
    ]

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.0,
            max_tokens=200
        )
        content = response.choices[0].message.content
        return json.loads(content)
    except Exception as e:
        print(f"LLM Error for {req_id}: {e}")
        return None

if __name__ == "__main__":
    sample_df = pd.read_csv(os.path.join(project_root, "dataset", "sample_requests.csv"))
    options_df = pd.read_csv(os.path.join(project_root, "dataset", "request_payment_options.csv"))
    
    print(f"Testing LLM ({MODEL}) on 5 sample requests...")
    results = []
    
    for idx, row in sample_df.iterrows():
        print(f"Processing {row['request_id']}...")
        opts = options_df[options_df['request_id'] == row['request_id']].to_dict('records')
        res = process_request_with_llm(row, opts)
        
        expected_amt = float(row['amount_safe_to_pay'])
        got_amt = float(res['amount_safe_to_pay']) if res and res.get('amount_safe_to_pay') else 0.0
        diff = abs(expected_amt - got_amt)
        match = diff < 1.0
        
        print(f"  -> Expected: {expected_amt:,.2f}")
        print(f"  -> Got     : {got_amt:,.2f} [{'OK' if match else 'XX'}]")
        print(f"  -> Status  : {res.get('affordability_status') if res else 'N/A'}")
        print(f"  -> Method  : {res.get('recommended_payment_method') if res else 'N/A'}\n")
        
        time.sleep(12)
