import pandas as pd
import datetime
from decimal import Decimal
from collections import defaultdict
from dateutil.relativedelta import relativedelta
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from llm.client import extract_image_amount, classify_message, generate_explanation

def process_messages_and_images(events_df, messages_df, images_df):
    events = events_df.to_dict('records')
    event_map = {str(e['event_id']): e for e in events}
    
    for _, img_row in images_df.iterrows():
        rel_id = str(img_row.get('related_event_id', ''))
        if rel_id in event_map:
            e = event_map[rel_id]
            if pd.isna(e.get('amount')) or e.get('amount') is None:
                img_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "dataset", "media", "images", f"{img_row['image_id']}.png"))
                extracted = extract_image_amount(img_path, img_row['image_id'])
                if extracted is not None:
                    e['amount'] = extracted
                    
    for _, msg_row in messages_df.iterrows():
        rel_id = str(msg_row.get('related_event_id', ''))
        if rel_id in event_map:
            e = event_map[rel_id]
            classification = classify_message(msg_row['message_text'], msg_row['message_id'], str(e))
            effect = classification.get('effect')
            if effect == 'cancel':
                e['status'] = 'cancelled'
            elif effect == 'amend':
                if classification.get('new_amount') is not None:
                    e['amount'] = classification['new_amount']
                if classification.get('new_date') is not None:
                    e['event_date'] = classification['new_date']
            elif effect == 'delay':
                if classification.get('new_date') is not None:
                    e['event_date'] = classification['new_date']
                    
    return events

def calculate_projected_cashflow(user_id, request_date, end_date, events, user_profile):
    """
    Returns (safe_amount_today, dict_of_daily_safe_balances)
    """
    balance = Decimal(str(user_profile['current_available_balance']))
    min_balance = Decimal(str(user_profile['minimum_balance_to_keep']))
    
    protected_str = user_profile.get('expense_categories_to_protect', '')
    protected_cats = set(str(protected_str).split('|')) if pd.notna(protected_str) and protected_str else set()
    
    user_events = [e for e in events if str(e['user_id']) == str(user_id)]
    
    historical = [e for e in user_events if e['status'] == 'settled' and pd.to_datetime(e['event_date']).date() < request_date]
    
    recurring_totals = defaultdict(list)
    variable_totals = defaultdict(list)
    salary_totals = defaultdict(list)
    
    for e in historical:
        if e['direction'] == 'debit':
            amt = Decimal(str(e['amount'])) if pd.notna(e['amount']) else Decimal('0')
            if e['event_type'] in ('subscription', 'debt_payment') or e['category'] == 'rent':
                key = (e['description'], e['category'])
                recurring_totals[key].append(amt)
            elif e['category'] in protected_cats:
                variable_totals[e['category']].append(amt)
        elif e['direction'] == 'credit' and e['category'] == 'salary':
            amt = Decimal(str(e['amount'])) if pd.notna(e['amount']) else Decimal('0')
            salary_totals['salary'].append(amt)
            
    daily_changes = defaultdict(Decimal)
    
    # Add pending/scheduled
    for e in user_events:
        if e['status'] in ('pending', 'scheduled') and e.get('event_date'):
            ev_date = pd.to_datetime(e['event_date']).date()
            if request_date <= ev_date <= end_date:
                amt = Decimal(str(e['amount'])) if pd.notna(e['amount']) else Decimal('0')
                if e['direction'] == 'debit':
                    daily_changes[ev_date] -= amt
                elif e['direction'] == 'credit' and (e['category'] == 'salary' or e['status'] == 'settled'): 
                    daily_changes[ev_date] += amt
                        
    total_monthly_expense = Decimal('0')
    for cat, amts in recurring_totals.items():
        if len(amts) >= 2:
            total_monthly_expense += sorted(amts)[len(amts)//2]
    for cat, amts in variable_totals.items():
        if len(amts) >= 2:
            total_monthly_expense += sorted(amts)[len(amts)//2]
            
    total_monthly_income = Decimal('0')
    for cat, amts in salary_totals.items():
        if len(amts) >= 2:
            total_monthly_income += sorted(amts)[len(amts)//2]
            
    # Apply monthly recurring on the same day next month
    cur_d = request_date + datetime.timedelta(days=30)
    while cur_d <= end_date:
        daily_changes[cur_d] -= total_monthly_expense
        daily_changes[cur_d] += total_monthly_income
        cur_d += datetime.timedelta(days=30)
        
    current_balance = balance
    min_future_balance = current_balance
    daily_balances = {}
    
    cur_date = request_date
    while cur_date <= end_date:
        current_balance += daily_changes[cur_date]
        min_future_balance = min(min_future_balance, current_balance)
        daily_balances[cur_date] = current_balance
        cur_date += datetime.timedelta(days=1)
        
    safe_amount_today = max(Decimal('0'), min_future_balance - min_balance)
    return safe_amount_today, daily_balances
