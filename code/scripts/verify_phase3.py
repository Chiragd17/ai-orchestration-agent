import sys
import os
import datetime
import pandas as pd
from decimal import Decimal

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)

from engine.data.state import build_user_state
from engine.reconcile import resolve
from engine.simulate import calculate_amount_safe_to_pay
from engine.candidates import generate_candidates
from engine.rank import rank, get_affordability_status

def run_verification():
    DATA_DIR = os.path.join(project_root, "..", "dataset")
    requests = pd.read_csv(os.path.join(DATA_DIR, "sample_requests.csv"))
    options = pd.read_csv(os.path.join(DATA_DIR, "request_payment_options.csv"))
    
    out = ["# Phase 3: Candidate Generation & Ranking\n"]
    out.append("| Request ID | Expected Status | Predicted Status | Match | Expected Method | Predicted Method |")
    out.append("|---|---|---|---|---|---|")
    
    match_count = 0
    total_count = 0
    
    for _, req in requests.iterrows():
        # Skip spending-change samples for this phase
        expected_changes = str(req['spending_changes_needed'])
        if expected_changes.lower() != 'none' and str(expected_changes) != 'nan':
            continue
            
        total_count += 1
        req_id = req['request_id']
        user_id = req['user_id']
        req_date = datetime.datetime.strptime(str(req['request_date']), "%Y-%m-%d").date()
        req_amt = Decimal(str(req['requested_amount']))
        comp_date = datetime.datetime.strptime(str(req['desired_completion_date']), "%Y-%m-%d").date()
        allows_partial = str(req['allows_partial_payment']).strip().lower() == 'true'
        
        expected_status = req['affordability_status']
        expected_method = req['recommended_payment_method']
        
        # Build state
        state = build_user_state(user_id)
        
        state.events = resolve(state.events)
        
        candidates = generate_candidates(
            user_state=state,
            request_id=req_id,
            request_date=req_date,
            requested_amount=req_amt,
            desired_completion_date=comp_date,
            allows_partial_payment=allows_partial,
            payment_options_df=options
        )
        
        winning_candidate = rank(candidates)
        pred_status = get_affordability_status(winning_candidate)
        pred_method = winning_candidate.method
        
        match = (pred_status == expected_status and pred_method == expected_method)
        if match:
            match_count += 1
            
        out.append(f"| {req_id} | {expected_status} | {pred_status} | {'✅' if match else '❌'} | {expected_method} | {pred_method} |")
        
    out.append(f"\n**Total Matches (No Spending Changes): {match_count} / {total_count}**")
    
    with open(os.path.join(project_root, "notes", "phase3_comparison.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    print("Table generated in notes/phase3_comparison.md")

if __name__ == "__main__":
    run_verification()
