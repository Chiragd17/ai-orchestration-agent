import sys

with open('code/main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    
# Find the start and end of the block to replace
start_idx = -1
end_idx = -1

for i, line in enumerate(lines):
    if '# Calculate how much free cashflow they have' in line:
        start_idx = i
        
    if '# If still not affordable, try spending changes' in line:
        end_idx = i
        break

if start_idx != -1 and end_idx != -1:
    new_block = \"\"\"    # Calculate how much free cashflow they have
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
        plan = 'none'
        earliest_date = request_date.strftime('%Y-%m-%d')
    elif amount_safe_to_pay > Decimal('0'):
        # Check partial
        can_partial = allows_partial and ('partial' in user_prefs or user_prefs == 'none' or pd.isna(user_profile.get('payment_preferences')))
        if can_partial and pd.notna(desired_completion_date_str):
            desired_date = pd.to_datetime(desired_completion_date_str).date()
            if desired_date > request_date:
                # Can we afford the rest on desired_date?
                rem = requested_amount - amount_safe_to_pay
                min_future = min([daily_balances[d] for d in daily_balances if d >= desired_date] + [Decimal('0')])
                if min_future - min_bal >= rem:
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
                                    break
                                m_future = min([daily_balances[d] for d in daily_balances if d >= inst_date] + [Decimal('0')])
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
                m_future = min([daily_balances[fd] for fd in daily_balances if fd >= d] + [Decimal('0')])
                if m_future - min_bal >= requested_amount:
                    if pd.notna(desired_completion_date_str) and d <= pd.to_datetime(desired_completion_date_str).date():
                        status = 'affordable_later'
                        method = 'wait'
                        plan = 'none'
                        earliest_date = d.strftime('%Y-%m-%d')
                        break
                        
    \"\"\"
    
    with open('code/main.py', 'w', encoding='utf-8') as f:
        f.writelines(lines[:start_idx])
        f.write(new_block)
        f.writelines(lines[end_idx:])
        
    print("Patched main.py successfully")
else:
    print("Could not find blocks in main.py")
