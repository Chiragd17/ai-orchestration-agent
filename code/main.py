import os
import sys
import pandas as pd
import datetime
from decimal import Decimal
import json

# Add engine to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'engine'))
# pyrefly: ignore [missing-import]
from simulate_robust import process_messages_and_images, calculate_projected_cashflow
from llm.client import generate_explanation

def load_all_datasets():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    dataset_path = os.path.join(project_root, "dataset")
    
    requests_df = pd.read_csv(os.path.join(dataset_path, "requests.csv"))
    profiles_df = pd.read_csv(os.path.join(dataset_path, "financial_profiles.csv"))
    events_df = pd.read_csv(os.path.join(dataset_path, "financial_events.csv"))
    options_df = pd.read_csv(os.path.join(dataset_path, "request_payment_options.csv"))
    
    # Load optional messages and images if they exist
    messages_df = pd.DataFrame()
    images_df = pd.DataFrame()
    if os.path.exists(os.path.join(dataset_path, "messages.csv")):
        messages_df = pd.read_csv(os.path.join(dataset_path, "messages.csv"))
    if os.path.exists(os.path.join(dataset_path, "images.csv")):
        images_df = pd.read_csv(os.path.join(dataset_path, "images.csv"))
        
    return requests_df, profiles_df, events_df, options_df, messages_df, images_df

def process_single_request(row, profiles_df, processed_events, options_df):
    request_id = row['request_id']
    user_id = row['user_id']
    request_date = pd.to_datetime(row['request_date']).date()
    requested_amount = Decimal(str(row['requested_amount']))
    allows_partial = str(row.get('allows_partial_payment', 'false')).lower() == 'true'
    desired_completion_date_str = row.get('desired_completion_date')
    
    user_profile = profiles_df[profiles_df['user_id'] == user_id].iloc[0]
    user_prefs = str(user_profile.get('payment_preferences', '')).lower()
    
    # Calculate how much free cashflow they have
    end_date = request_date + datetime.timedelta(days=90)
    free_cash, daily_balances = calculate_projected_cashflow(user_id, request_date, end_date, processed_events, user_profile)
    amount_safe_to_pay = min(requested_amount, free_cash)
    
    status = 'not_affordable'
    method = 'not_recommended'
    plan = 'none'
    earliest_date = ''
    explanation = 'Default explanation'
    spending_changes = 'none'
    
    min_bal = Decimal(str(user_profile['minimum_balance_to_keep']))
    
    if amount_safe_to_pay >= requested_amount:
        status = 'affordable_now'
        method = 'full_payment'
        plan = f"{request_date.strftime('%Y-%m-%d')}:{requested_amount}"
        earliest_date = request_date.strftime('%Y-%m-%d')
    else:
        # Check partial
        can_partial = allows_partial and ('partial' in user_prefs or user_prefs == 'none' or pd.isna(user_profile.get('payment_preferences')))
        if can_partial and pd.notna(desired_completion_date_str) and amount_safe_to_pay > 0:
            desired_date = pd.to_datetime(desired_completion_date_str).date()
            if desired_date > request_date:
                rem = requested_amount - amount_safe_to_pay
                future_bals = [daily_balances[d] for d in daily_balances if d >= desired_date]
                if future_bals:
                    m_future = min(future_bals)
                    if m_future - min_bal >= rem:
                        status = 'affordable_with_plan'
                        method = 'partial_payment'
                        plan = f"{request_date.strftime('%Y-%m-%d')}:{amount_safe_to_pay}|{desired_date.strftime('%Y-%m-%d')}:{rem}"
                        earliest_date = desired_date.strftime('%Y-%m-%d')
                    
        # If partial failed, try installments
        if method == 'not_recommended':
            req_options = options_df[options_df['request_id'] == request_id]
            for _, opt in req_options.iterrows():
                if opt['payment_method'] == 'installments':
                    try:
                        months = int(opt.get('number_of_payments', 0))
                        monthly = Decimal(str(opt.get('payment_amount', 0)))
                        freq = int(opt.get('payment_frequency_days', 30))
                        
                        max_months = int(user_profile.get('max_installment_months', 0)) if pd.notna(user_profile.get('max_installment_months')) else 0
                        
                        if months <= max_months and monthly > 0:
                            can_afford = True
                            for i in range(months):
                                inst_date = request_date + datetime.timedelta(days=freq * i)
                                if inst_date > end_date:
                                    can_afford = False
                                    break
                                future_bals = [daily_balances[d] for d in daily_balances if d >= inst_date]
                                if not future_bals:
                                    can_afford = False
                                    break
                                m_future = min(future_bals)
                                if m_future - min_bal < monthly * (i + 1):
                                    can_afford = False
                                    break
                            
                            if can_afford:
                                status = 'affordable_with_plan'
                                method = 'installments'
                                plan_parts = []
                                cur_date = request_date
                                for i in range(months):
                                    plan_parts.append(f"{cur_date.strftime('%Y-%m-%d')}:{monthly}")
                                    cur_date += datetime.timedelta(days=freq)
                                plan = "|".join(plan_parts)
                                earliest_date = (cur_date - datetime.timedelta(days=freq)).strftime('%Y-%m-%d')
                                break
                    except Exception as e:
                        pass
                        
    # Try wait if nothing else worked
    if method == 'not_recommended':
        for d in sorted(daily_balances.keys()):
            if d > request_date:
                future_bals = [daily_balances[fd] for fd in daily_balances if fd >= d]
                if future_bals:
                    m_future = min(future_bals)
                    if m_future - min_bal >= requested_amount:
                        if pd.notna(desired_completion_date_str) and d <= pd.to_datetime(desired_completion_date_str).date():
                            status = 'affordable_later'
                            method = 'wait'
                            plan = f"{d.strftime('%Y-%m-%d')}:{requested_amount}"
                            earliest_date = d.strftime('%Y-%m-%d')
                            break

    # If still not affordable, try spending changes
    if method == 'not_recommended':
        reduce_cats_str = str(user_profile.get('expense_categories_user_is_willing_to_reduce', ''))
        stop_cats_str = str(user_profile.get('expense_categories_user_is_willing_to_stop', ''))
        
        reduce_cats = set(reduce_cats_str.split('|')) if pd.notna(reduce_cats_str) and reduce_cats_str and reduce_cats_str != 'nan' else set()
        stop_cats = set(stop_cats_str.split('|')) if pd.notna(stop_cats_str) and stop_cats_str and stop_cats_str != 'nan' else set()
        
        # Group flexible events by category
        user_events = [e for e in processed_events if str(e['user_id']) == str(user_id) and e['status'] == 'settled' and e['direction'] == 'debit']
        cat_events = {}
        for e in user_events:
            if str(e.get('flexibility')).lower() in ['reducible', 'stoppable', 'reducible_or_stoppable']:
                cat = e['category']
                if cat not in cat_events:
                    cat_events[cat] = []
                cat_events[cat].append(e)
                
        possible_changes = []
        for cat, evts in cat_events.items():
            if cat in reduce_cats or cat in stop_cats:
                # pick the most recent representative event
                evts.sort(key=lambda x: x['event_date'], reverse=True)
                rep_e = evts[0]
                
                amt = Decimal(str(rep_e['amount'])) if pd.notna(rep_e['amount']) else Decimal('0')
                min_amt = Decimal(str(rep_e.get('minimum_allowed_amount', 0))) if pd.notna(rep_e.get('minimum_allowed_amount')) else Decimal('0')
                
                if cat in stop_cats:
                    min_amt = Decimal('0')
                    
                if amt > min_amt:
                    # estimate 3 months of savings (rough approximation for affordability)
                    freq_mult = Decimal('3') if rep_e['event_type'] in ('subscription', 'debt_payment') or cat == 'rent' else Decimal('1') 
                    freq_mult = Decimal('3')
                    
                    possible_changes.append({
                        'id': rep_e['event_id'],
                        'savings_3m': (amt - min_amt) * freq_mult,
                        'min_amt': min_amt,
                        'is_stop': min_amt == Decimal('0')
                    })
                    
        possible_changes.sort(key=lambda x: x['savings_3m'], reverse=True)
        
        changes_made = []
        saved_3m = Decimal('0')
        needed_3m = requested_amount 
        
        for change in possible_changes[:3]:
            if change['is_stop']:
                changes_made.append(f"stop:{change['id']}")
            else:
                changes_made.append(f"reduce_to:{change['id']}:{change['min_amt']}")
            saved_3m += change['savings_3m']
            
            if saved_3m >= needed_3m:
                break
                
        if changes_made:
            status = 'affordable_with_plan'
            method = 'wait'
            plan = f"{end_date.strftime('%Y-%m-%d')}:{requested_amount}"
            earliest_date = end_date.strftime('%Y-%m-%d')
            spending_changes = "|".join(changes_made)
            
    # Generate explanation via LLM
    facts = {
        'amount_safe_to_pay': str(amount_safe_to_pay),
        'requested_amount': str(requested_amount),
        'status': status,
        'method': method
    }
    
    # We use the LLM if configured, otherwise fallback to deterministic strings to bypass timeout delays
    if os.getenv("GROQ_API_KEY"):
        explanation = generate_explanation(facts)
    else:
        if method == 'full_payment':
            explanation = "Full payment is affordable with current projected balance."
        elif method == 'partial_payment':
            explanation = f"Partial payment of {amount_safe_to_pay} now, remainder later."
        elif method == 'installments':
            explanation = "Installment plan fits within projected free cashflow."
        else:
            explanation = "Payment is not affordable due to insufficient projected balance."
    
    return {
        'request_id': request_id,
        'amount_safe_to_pay': float(amount_safe_to_pay),
        'affordability_status': status,
        'recommended_payment_method': method,
        'payment_plan': plan,
        'earliest_date_for_full_payment': earliest_date,
        'spending_changes_needed': spending_changes,
        'decision_explanation': explanation
    }

def main():
    print("Starting robust financial decision engine...")
    requests_df, profiles_df, events_df, options_df, messages_df, images_df = load_all_datasets()
    
    print("Pre-processing events via LLM Vision & Text...")
    processed_events = process_messages_and_images(events_df, messages_df, images_df)
    
    output_rows = []
    print("Evaluating 250 requests...")
    for idx, row in requests_df.iterrows():
        try:
            res = process_single_request(row, profiles_df, processed_events, options_df)
            output_rows.append(res)
        except Exception as e:
            print(f"Error on {row['request_id']}: {e}")
            output_rows.append({
                'request_id': row['request_id'],
                'amount_safe_to_pay': 0.0,
                'affordability_status': 'not_affordable',
                'recommended_payment_method': 'not_recommended',
                'payment_plan': 'none',
                'earliest_date_for_full_payment': '',
                'spending_changes_needed': 'none',
                'decision_explanation': f"Error: {e}"
            })
            
        if (idx+1) % 50 == 0:
            print(f"  Processed {idx+1}/{len(requests_df)} requests.")
            
    out_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "output.csv"))
    pd.DataFrame(output_rows).to_csv(out_path, index=False)
    print(f"Saved predictions to {out_path}")

if __name__ == "__main__":
    main()
