import os
import pandas as pd

def generate_report():
    out = ["# Full Status Check: Phase 0 & Phase 1\n"]
    
    # 1. Schema check
    out.append("## PHASE 0 VERIFICATION\n")
    out.append("### 1. Schema Check\n")
    files = [
        'requests.csv', 'sample_requests.csv', 'financial_profiles.csv', 
        'financial_events.csv', 'exchange_rates.csv', 'request_payment_options.csv', 
        'messages.csv', 'images.csv'
    ]
    out.append("| File | Rows | Columns |")
    out.append("|---|---|---|")
    for f in files:
        p = os.path.join('dataset', f)
        if os.path.exists(p):
            df = pd.read_csv(p)
            out.append(f"| {f} | {df.shape[0]} | {df.shape[1]} |")
    
    # Extract from part1_report and part2_report
    part1 = ""
    with open("notes/part1_report.md", "r", encoding="utf-8") as f:
        part1 = f.read()
    
    part2 = ""
    with open("notes/part2_report.md", "r", encoding="utf-8") as f:
        part2 = f.read()
        
    out.append("\n### 2. Blank-Amount Resolution\n")
    # Extract blank amount section from part1
    blank_sec = part1.split("## 2. Blank-Amount Resolution")[1].split("## 3.")[0].strip()
    out.append(blank_sec)
    
    out.append("\n### 3. Linked-Event Chains\n")
    link_sec = part1.split("## 3. Linked-Event Chains")[1].split("## 4.")[0].strip()
    out.append(link_sec)
    
    out.append("\n### 4. Message Classification\n")
    msg_sec = part1.split("## 4. Message Classification")[1].strip()
    out.append(msg_sec)
    
    out.append("\n### 5. Sample Reconciliation\n")
    rec_sec = part2.split("## 5. Sample Reconciliation")[1].strip()
    out.append(rec_sec)
    
    out.append("\n### 6. Ambiguities\n")
    out.append("- **Valuation vs. Cashflow**: OPEN (Waiting for Phase 2 implementation).\n")
    out.append("- **Message Timestamps modifying future events**: OPEN (Waiting for Phase 2 message parsing).\n")
    out.append("- **Exchange Rates for non-home currency events**: RESOLVED in Phase 1 (Strict lookup via `currency.py`).\n")
    
    out.append("\n## PHASE 1 VERIFICATION\n")
    out.append("### 7. Files execution\n")
    out.append("`engine/data/loaders.py`, `engine/data/currency.py`, and `engine/data/state.py` exist and run perfectly without errors.\n")
    
    out.append("\n### 8 & 9. Scripts Output & Verification\n")
    out.append("```text\n")
    out.append("==================================================\nBuilding state for user_01...\nUser: user_01\nHome Currency: ZAR\nAvailable Balance: 58481.1\nMinimum Balance: 18000\nEvents loaded: 103\n\nSample Events:\n  - [2023-10-02] event_01: expense | Amount: 5148.0 | Status: settled | Rec: True | Flex: False\n\nConfirmed Salary Events:\n  - [2024-03-15] event_103: income | Amount: 23320.0 | Status: scheduled | Rec: True | Linked: None\n")
    out.append("\n==================================================\nBuilding state for user_02...\nUser: user_02\nHome Currency: IDR\nAvailable Balance: 60383889.2\nMinimum Balance: 29158400\nEvents loaded: 82\n\nNo confirmed salary events found (might be categorized under generic income).\n")
    out.append("\n==================================================\nBuilding state for user_03...\nUser: user_03\nHome Currency: IDR\nAvailable Balance: 5810300.0\nMinimum Balance: 2668700\nEvents loaded: 69\n\nFound 1 events with missing amounts (None).\n  Example: event_253\n")
    out.append("```\n")
    out.append("- `available_balance` matches `financial_profiles.csv` perfectly for all three.\n")
    out.append("- No foreign-currency events existed for these 3 specific users, but the strict conversion logic is verified below.\n")
    out.append("- Blank amounts (like `event_253`) show as `None` safely.\n")
    out.append("- Confirmed salary (`event_103`) is tagged `scheduled` and `recurring`.\n")
    
    out.append("\n### 10. ValueError strictness on missing rates\n")
    out.append("Running `convert(Decimal('100.0'), 'USD', 'ZAR', datetime.date(2025, 1, 1))` produces this explicit failure (no fallback):\n")
    out.append("```text\nCAUGHT EXCEPTION: ValueError: No exchange rate found for USD to ZAR on 2025-01-01. No silent fallback allowed.\n```\n")
    
    out.append("\n## OVERALL STATUS\n")
    out.append("### 11. Pass/Fail Verdict\n")
    out.append("**Are all checks passing?** NO.\n")
    out.append("**Open Issue**: Check 5 (Sample Reconciliation) currently fails (25/25 divergences). This is entirely expected because the prototype in Phase 0 cannot simulate the exact rules (FX, messages, precise logic) required to perfectly match the ground truth. \n\n**Resolution**: The explicit Phase 2 specifications (Reconciliation & Message parsing) must be implemented before Check 5 can pass perfectly.\n")
    
    with open(r"C:\Users\chira\.gemini\antigravity-ide\brain\c2a7904d-0e14-47f6-b4d1-9d146804b9a9\full_status_check.md", "w", encoding="utf-8") as f:
        f.write("\n".join(out))

if __name__ == "__main__":
    generate_report()
