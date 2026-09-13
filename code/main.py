import os
import sys
import pandas as pd
import datetime
from decimal import Decimal
from pathlib import Path

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)

from engine.data.state import build_user_state
from engine.data.loaders import load_exchange_rates
from llm.enrichment import apply_image_amounts, apply_message_effects
from engine.reconcile import resolve
from engine.simulate import calculate_amount_safe_to_pay, calculate_earliest_full_payment_date
from engine.candidates import generate_candidates
from engine.rank import rank, get_affordability_status
from llm.client import generate_explanation, usage_tracker
from output.validator import validate_row
from output.format import format_spending_changes, format_payment_plan
from evaluation.usage_report import generate_usage_report

def run_pipeline(requests_csv_name="requests.csv", target_request_id=None, out_path="dataset/output.csv"):
    dataset_dir = os.path.join(project_root, "dataset")
    requests_path = os.path.join(dataset_dir, requests_csv_name)
    output_path = os.path.join(project_root, out_path) if out_path == "dataset/output.csv" else os.path.abspath(out_path)
    
    print(f"Loading data from {dataset_dir}...")
    requests_df = pd.read_csv(requests_path)
    
    if target_request_id:
        requests_df = requests_df[requests_df['request_id'] == target_request_id]
        if requests_df.empty:
            print(f"Error: Could not find request {target_request_id} in {requests_csv_name}")
            return
            
    images_df = pd.read_csv(os.path.join(dataset_dir, "images.csv"))
    messages_df = pd.read_csv(os.path.join(dataset_dir, "messages.csv"))
    payment_options_df = pd.read_csv(os.path.join(dataset_dir, "request_payment_options.csv"))
    exchange_rates_df = load_exchange_rates()
    profiles_df = pd.read_csv(os.path.join(dataset_dir, "financial_profiles.csv"))
    
    results = []
    total = len(requests_df)
    
    print(f"Starting processing of {total} requests...")
    for idx, req in requests_df.iterrows():
        req_id = req["request_id"]
        user_id = req["user_id"]
        req_date = datetime.datetime.strptime(str(req["request_date"]), "%Y-%m-%d").date()
        req_amount = Decimal(str(req["requested_amount"]))
        req_completion = datetime.datetime.strptime(str(req["desired_completion_date"]), "%Y-%m-%d").date()
        req_partial = bool(req["allows_partial_payment"])
        req_text = str(req["request_text"])
        req_type = str(req["request_type"])
        
        print(f"[{idx+1}/{total}] Processing {req_id} for {user_id}...")
        
        # 1. Build initial state
        state = build_user_state(user_id)
        
        # 2. Enrich events via LLM (OCR + Messages)
        enriched_events = apply_image_amounts(state.events, images_df)
        enriched_events = apply_message_effects(enriched_events, messages_df, req_id)
        
        # 3. Resolve conflicts
        # We need to manually inject profile for safe interpretation tie-breaker if needed
        # Wait, resolve doesn't take profile or exchange_rates. It takes only events!
        # Ah, in our implementation, resolve() just takes List[Event].
        resolved_events = resolve(enriched_events)
        
        # Re-inject resolved events into state
        state.events = resolved_events
        
        # 4. Generate candidates and rank
        candidates = generate_candidates(
            user_state=state,
            request_id=req_id,
            request_date=req_date,
            requested_amount=req_amount,
            desired_completion_date=req_completion,
            allows_partial_payment=req_partial,
            payment_options_df=payment_options_df
        )
        
        best = rank(candidates)
        
        # 5. Extract core facts for output
        safe_to_pay = calculate_amount_safe_to_pay(state, req_date, req_amount)
        status = get_affordability_status(best)
        earliest_full = calculate_earliest_full_payment_date(state, req_amount, req_date)
        
        # Format strings for the row
        plan_str = format_payment_plan(best.payment_plan)
        
        # Wait, best.spending_changes is a list of string instructions (e.g. "stop:event_01")
        # format_spending_changes expects dicts? Let's check format.py
        # Ah, earlier in candidates.py I did: `base_actions.append(f"stop:{e.event_id}")`
        # So spending_changes is already a list of strings!
        changes_str = "|".join(best.spending_changes) if best.spending_changes else "none"
        
        earliest_str = earliest_full.isoformat() if earliest_full else ""
        if status == "not_affordable":
            earliest_str = "" # enforce blank
            
        # 6. Generate Explanation
        facts = {
            "requested_amount": float(req_amount),
            "amount_safe_to_pay": float(safe_to_pay),
            "status": status,
            "method": best.method,
            "spending_changes": changes_str,
            "earliest_date": earliest_str,
            "request_text": req_text,
            "request_type": req_type,
            "completes_by_deadline": best.completes_by_deadline
        }
        explanation = generate_explanation(facts)
        
        # 7. Construct Row
        row = {
            "request_id": req_id,
            "amount_safe_to_pay": f"{safe_to_pay:.2f}" if safe_to_pay == int(safe_to_pay) else str(safe_to_pay), # Keep safe formatting
            "affordability_status": status,
            "recommended_payment_method": best.method,
            "payment_plan": plan_str,
            "earliest_date_for_full_payment": earliest_str,
            "spending_changes_needed": changes_str,
            "decision_explanation": explanation
        }
        
        # Wait, amount_safe_to_pay formatting needs to not have trailing zeroes if not required, but Decimal stringification is usually fine.
        row["amount_safe_to_pay"] = str(safe_to_pay.normalize()) if '.' in str(safe_to_pay) else str(safe_to_pay)
        
        # 8. Validate
        options_dicts = payment_options_df[payment_options_df['request_id'] == req_id].to_dict('records')
        
        # Fix format for options_dicts schedule_str to pass validation
        for o in options_dicts:
            if o.get('payment_method') == 'installments':
                start = datetime.datetime.strptime(str(o['first_payment_date']), "%Y-%m-%d").date()
                num = int(o['number_of_payments'])
                freq = int(o['payment_frequency_days'])
                amt = Decimal(str(o['payment_amount']))
                p = []
                for i in range(num):
                    p.append((start + datetime.timedelta(days=i*freq), amt))
                o['schedule_str'] = format_payment_plan(p)
            
        errs = validate_row(row, req_date.isoformat(), req_amount, options_dicts)
        if errs:
            print(f"WARNING: Validation failed for {req_id}: {errs}")
            
        results.append(row)
        
    print("Writing output.csv...")
    df_out = pd.DataFrame(results, columns=[
        "request_id", "amount_safe_to_pay", "affordability_status", "recommended_payment_method",
        "payment_plan", "earliest_date_for_full_payment", "spending_changes_needed", "decision_explanation"
    ])
    df_out.to_csv(output_path, index=False)
    
    print("Generating usage report...")
    generate_usage_report(usage_tracker, os.path.join(project_root, "evaluation", "usage_report.md"), total)
    print("Pipeline finished successfully.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run the Orchestrate pipeline.")
    parser.add_argument("--sample", action="store_true", help="Run against sample_requests.csv instead of requests.csv")
    parser.add_argument("--request", type=str, help="Run for only a specific request_id (e.g. request_26)")
    parser.add_argument("--output", type=str, help="Custom output CSV path to avoid overwriting dataset/output.csv", default="dataset/output.csv")
    args = parser.parse_args()
    
    csv_name = "sample_requests.csv" if args.sample else "requests.csv"
    run_pipeline(csv_name, target_request_id=args.request, out_path=args.output)
