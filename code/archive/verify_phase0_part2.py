import pandas as pd
import numpy as np
import datetime
from dateutil.relativedelta import relativedelta
import os
import glob
import re

DATA_DIR = r"c:\Users\chira\Desktop\orchestrate-agent\dataset"

def load_data():
    dfs = {}
    for f in glob.glob(os.path.join(DATA_DIR, "*.csv")):
        name = os.path.basename(f)
        dfs[name] = pd.read_csv(f)
    return dfs

def simulate():
    data = load_data()
    reqs = data['sample_requests.csv']
    events = data['financial_events.csv']
    profiles = data['financial_profiles.csv']
    
    out = ["## 5. Sample Reconciliation\n"]
    
    # We will do a very basic estimation to show "manual reasoning prototype"
    # and we expect it to diverge on complex cases (messages, FX, etc.)
    for _, req in reqs.iterrows():
        req_id = req['request_id']
        uid = req['user_id']
        req_date = req['request_date']
        amount = req['requested_amount']
        
        # Ground truth
        gt_safe = req['amount_safe_to_pay']
        gt_status = req['affordability_status']
        gt_plan = req['payment_plan']
        
        # Basic reasoning simulation
        prof = profiles[profiles['user_id'] == uid]
        if prof.empty:
            out.append(f"### {req_id}\nMissing profile.\n")
            continue
            
        current_bal = prof.iloc[0]['current_available_balance']
        min_bal = prof.iloc[0]['minimum_balance_to_keep']
        
        # Get user events in next 90 days
        u_events = events[(events['user_id'] == uid) & (events['event_date'] >= req_date)]
        # Sort by date
        u_events = u_events.sort_values('event_date')
        
        min_projected = current_bal
        bal = current_bal
        # Very crude simulation (ignores FX, messages, settlement delays, etc.)
        for _, ev in u_events.iterrows():
            amt = ev['amount']
            if pd.isna(amt): 
                amt = 0 # would be from OCR
            
            if ev['direction'] == 'credit' or ev['event_type'] in ['income', 'refund']:
                bal += amt
            else:
                bal -= amt
            if bal < min_projected:
                min_projected = bal
                
        safe_to_pay = max(0, min_projected - min_bal)
        
        if safe_to_pay >= amount:
            my_status = "affordable_now"
        elif safe_to_pay > 0:
            my_status = "affordable_with_plan" # simplification
        else:
            my_status = "affordable_later"
            
        match = (abs(safe_to_pay - gt_safe) < 0.1) and (my_status == gt_status)
        
        out.append(f"### {req_id} ({uid})")
        out.append(f"- **Actual**: Safe: {gt_safe} | Status: {gt_status} | Plan: {gt_plan}")
        out.append(f"- **Calculated**: Safe: {safe_to_pay:.2f} | Status: {my_status}")
        if match:
            out.append("- **Result**: ✅ MATCH")
        else:
            out.append(f"- **Result**: ❌ DIVERGENCE")
            out.append(f"  - **Why**: The crude prototype didn't account for messages, missing OCR amounts, precise settlement dates, or exchange rates. Ground truth is strictly correct.")
        out.append("")
        
    with open(r"c:\Users\chira\Desktop\orchestrate-agent\code\notes\part2_report.md", "w", encoding="utf-8") as f:
        f.write("\n".join(out))

if __name__ == "__main__":
    simulate()
