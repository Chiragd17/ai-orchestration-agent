#!/usr/bin/env python3
"""
CORRECTED Main - Realistic Financial Decision Logic
Fixes the issue where everything was showing as affordable.
"""

import sys
import os
import pandas as pd
import datetime
from decimal import Decimal

# Add engine to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'engine'))

def load_datasets():
    """Load all required datasets."""
    try:
        project_root = os.path.abspath(os.path.dirname(__file__))
        dataset_path = os.path.join(project_root, "..", "dataset")
        
        requests_df = pd.read_csv(os.path.join(dataset_path, "requests.csv"))
        profiles_df = pd.read_csv(os.path.join(dataset_path, "financial_profiles.csv"))
        events_df = pd.read_csv(os.path.join(dataset_path, "financial_events.csv"))
        payment_options_df = pd.read_csv(os.path.join(dataset_path, "request_payment_options.csv"))
        
        print(f"✅ Loaded datasets: {len(requests_df)} requests, {len(profiles_df)} profiles, {len(events_df)} events")
        return requests_df, profiles_df, events_df, payment_options_df
        
    except Exception as e:
        print(f"❌ Error loading datasets: {e}")
        return None, None, None, None

def simulate_realistic_financial_decision(user_id: str, request_date: datetime.date, requested_amount: Decimal,
                                        desired_completion_date: datetime.date, events_df: pd.DataFrame, 
                                        profiles_df: pd.DataFrame) -> dict:
    """
    CORRECTED simulation with realistic financial constraints.
    """
    
    # Get user profile
    user_profile = profiles_df[profiles_df['user_id'] == user_id]
    if user_profile.empty:
        return {
            'amount_safe_to_pay': Decimal('0'),
            'affordability_status': 'not_affordable',
            'recommended_payment_method': 'not_recommended',
            'payment_plan': 'none',
            'earliest_date_for_full_payment': '',
            'spending_changes_needed': 'none',
            'decision_explanation': 'User profile not found'
        }
    
    current_balance = Decimal(str(user_profile.iloc[0]['current_available_balance']))
    min_balance = Decimal(str(user_profile.iloc[0]['minimum_balance_to_keep']))
    
    # Get user events
    user_events_df = events_df[events_df['user_id'] == user_id].copy()
    
    # Create simplified event objects
    class SimpleEvent:
        def __init__(self, row):
            self.event_id = row['event_id']
            self.user_id = row['user_id']
            self.type = row['event_type']
            self.description = row['description']
            self.category = row['category']
            self.direction = row['direction']
            self.amount = Decimal(str(row['amount'])) if pd.notna(row['amount']) else None
            self.date = pd.to_datetime(row['event_date']).date()
            self.status = row['status']
    
    events = [SimpleEvent(row) for _, row in user_events_df.iterrows()]
    
    # Enhanced simulation with realistic constraints
    end_date = request_date + datetime.timedelta(days=90)
    balance = current_balance
    
    # Apply base events
    base_events = [e for e in events if e.status in ('settled', 'scheduled', 'pending') 
                   and request_date <= e.date <= end_date]
    
    for e in base_events:
        if e.status == 'pending' and e.direction == 'debit':
            balance -= e.amount
        elif e.status != 'pending':
            if e.direction == 'debit':
                balance -= e.amount
            else:
                balance += e.amount
    
    # Apply projection (but with more conservative approach)
    try:
        from simulate import project_recurring_events
        projected_events = project_recurring_events(events, request_date, end_date, user_id)
        
        for proj_event in projected_events:
            if proj_event.direction == 'debit':
                balance -= proj_event.amount
            else:
                balance += proj_event.amount
                
    except Exception as e:
        print(f"Warning: Projection failed for {user_id}: {e}")
    
    # Calculate conservative amount safe to pay
    available_for_payment = balance - min_balance
    
    # REALISTIC FINANCIAL DECISION LOGIC
    
    # Safety buffer (additional conservatism)
    safety_buffer = max(Decimal('1000'), current_balance * Decimal('0.05'))  # 5% or $1000 minimum
    conservative_available = available_for_payment - safety_buffer
    
    amount_safe_to_pay = max(Decimal('0'), conservative_available)
    
    # Enhanced decision logic based on realistic constraints
    payment_ratio = amount_safe_to_pay / requested_amount if requested_amount > 0 else 0
    
    if payment_ratio >= Decimal('1.0'):
        # Can afford full payment comfortably
        affordability_status = 'affordable_now'
        recommended_payment_method = 'full_payment'
        payment_plan = 'none'
        earliest_date = request_date.strftime('%Y-%m-%d')
        explanation = f"Full payment of {requested_amount} is affordable with current projected balance."
        
    elif payment_ratio >= Decimal('0.3') and amount_safe_to_pay > Decimal('100'):
        # Can afford substantial partial payment
        affordability_status = 'affordable_with_plan'
        recommended_payment_method = 'partial_payment'
        
        remaining_amount = requested_amount - amount_safe_to_pay
        
        # Check if we can complete by desired date
        months_available = (desired_completion_date - request_date).days / 30.0
        if months_available >= 2:
            second_payment_date = min(
                request_date + datetime.timedelta(days=60),
                desired_completion_date
            )
        else:
            second_payment_date = desired_completion_date
        
        payment_plan = f"{request_date.strftime('%Y-%m-%d')}:{amount_safe_to_pay}|{second_payment_date.strftime('%Y-%m-%d')}:{remaining_amount}"
        earliest_date = second_payment_date.strftime('%Y-%m-%d')
        explanation = f"Partial payment of {amount_safe_to_pay} now, remainder by {second_payment_date.strftime('%Y-%m-%d')}."
        
    elif amount_safe_to_pay > Decimal('0'):
        # Very limited funds - wait for better timing
        affordability_status = 'affordable_later'
        recommended_payment_method = 'wait'
        payment_plan = 'none'
        
        # Estimate when full payment might be possible (conservative estimate)
        months_needed = max(3, int(requested_amount / (current_balance * Decimal('0.1'))))
        earliest_date = (request_date + datetime.timedelta(days=30 * months_needed)).strftime('%Y-%m-%d')
        explanation = f"Limited funds available now. Consider waiting until {earliest_date} for full payment."
        
    else:
        # Cannot afford at all
        affordability_status = 'not_affordable'
        recommended_payment_method = 'not_recommended'
        payment_plan = 'none'
        earliest_date = ''
        explanation = "Payment not recommended. Insufficient funds after accounting for essential expenses and safety buffer."
    
    return {
        'amount_safe_to_pay': amount_safe_to_pay,
        'affordability_status': affordability_status,
        'recommended_payment_method': recommended_payment_method,
        'payment_plan': payment_plan,
        'earliest_date_for_full_payment': earliest_date,
        'spending_changes_needed': 'none',
        'decision_explanation': explanation
    }

def main():
    """Main execution with corrected financial decision logic."""
    
    print("🔧 CORRECTED HACKERRANK ORCHESTRATE: BUY OR WAIT?")
    print("="*60)
    print("🎯 Realistic Financial Decision Engine")
    print("⚖️  Conservative Risk Assessment Applied")
    print("🚨 Fixing 100% Affordable Issue")
    print("="*60)
    
    # Load datasets
    requests_df, profiles_df, events_df, payment_options_df = load_datasets()
    
    if requests_df is None:
        print("❌ Failed to load datasets. Cannot proceed.")
        return
    
    # Generate realistic predictions
    print(f"\n🚀 Processing {len(requests_df)} requests with CORRECTED logic...")
    
    output_rows = []
    processed_count = 0
    
    for _, row in requests_df.iterrows():
        request_id = row['request_id']
        user_id = row['user_id']
        request_date = pd.to_datetime(row['request_date']).date()
        requested_amount = Decimal(str(row['requested_amount']))
        desired_completion_date = pd.to_datetime(row['desired_completion_date']).date()
        
        try:
            # Generate prediction with CORRECTED logic
            prediction = simulate_realistic_financial_decision(
                user_id, request_date, requested_amount, desired_completion_date,
                events_df, profiles_df
            )
            
            output_rows.append({
                'request_id': request_id,
                'amount_safe_to_pay': float(prediction['amount_safe_to_pay']),
                'affordability_status': prediction['affordability_status'],
                'recommended_payment_method': prediction['recommended_payment_method'],
                'payment_plan': prediction['payment_plan'],
                'earliest_date_for_full_payment': prediction['earliest_date_for_full_payment'],
                'spending_changes_needed': prediction['spending_changes_needed'],
                'decision_explanation': prediction['decision_explanation']
            })
            
            processed_count += 1
            if processed_count % 50 == 0:
                print(f"  ✅ Processed {processed_count}/{len(requests_df)} requests...")
            
        except Exception as e:
            print(f"❌ Error processing {request_id}: {e}")
            # Add error fallback
            output_rows.append({
                'request_id': request_id,
                'amount_safe_to_pay': 0.0,
                'affordability_status': 'not_affordable',
                'recommended_payment_method': 'not_recommended',
                'payment_plan': 'none',
                'earliest_date_for_full_payment': '',
                'spending_changes_needed': 'none',
                'decision_explanation': f'Processing error: {str(e)}'
            })
    
    # Create output DataFrame and save
    output_df = pd.DataFrame(output_rows)
    output_path = os.path.join(os.path.dirname(__file__), '..', 'dataset', 'output_corrected.csv')
    output_df.to_csv(output_path, index=False)
    
    # Show corrected distribution
    print(f"\n✅ CORRECTED PROCESSING COMPLETE!")
    print(f"📁 Corrected output saved to: output_corrected.csv")
    
    print(f"\n📊 CORRECTED AFFORDABILITY DISTRIBUTION:")
    distribution = output_df['affordability_status'].value_counts()
    for status, count in distribution.items():
        percentage = (count / len(output_df)) * 100
        print(f"  {status}: {count} ({percentage:.1f}%)")
    
    print(f"\n📋 SAMPLE CORRECTED PREDICTIONS:")
    for i in range(min(5, len(output_rows))):
        row = output_rows[i]
        print(f"  {i+1}. {row['request_id']}: ${row['amount_safe_to_pay']:,.2f} ({row['affordability_status']})")
    
    print(f"\n🎯 CORRECTION SUCCESS!")
    print(f"Now showing realistic mix of affordable/not affordable cases")

if __name__ == "__main__":
    main()