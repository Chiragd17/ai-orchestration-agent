import datetime
from decimal import Decimal
from dataclasses import dataclass, field
from typing import List, Optional
import pandas as pd
from engine.data.loaders import load_financial_profiles, load_financial_events
from engine.data.currency import convert

@dataclass
class Event:
    event_id: str
    date: datetime.date
    amount: Optional[Decimal]
    type: str
    category: str
    description: str
    direction: str
    recurring: bool
    interval: Optional[str]
    flexibility: str
    minimum_allowed_amount: Optional[Decimal]
    raw_minimum_allowed_amount: Optional[str]
    status: str
    linked_event_id: Optional[str]

@dataclass
class UserState:
    user_id: str
    home_currency: str
    available_balance: Decimal
    minimum_balance_to_keep: Decimal
    financial_priorities: str
    payment_methods_user_will_consider: str
    spending_preferences: str
    protected_categories: set = field(default_factory=set)
    reduce_categories: set = field(default_factory=set)
    stop_categories: set = field(default_factory=set)
    events: List[Event] = field(default_factory=list)

def build_user_state(user_id: str) -> UserState:
    profiles = load_financial_profiles()
    events_df = load_financial_events()
    
    user_profile = profiles[profiles['user_id'] == user_id]
    if user_profile.empty:
        raise ValueError(f"User {user_id} not found in profiles.")
        
    p = user_profile.iloc[0]
    home_currency = p['home_currency']
    
    fp = p['financial_priorities'] if pd.notna(p['financial_priorities']) else ""
    pm = p['payment_methods_user_will_consider'] if pd.notna(p['payment_methods_user_will_consider']) else ""
    # Combine expense preferences into one string
    sp_protect = p.get('expense_categories_to_protect', '')
    sp_reduce = p.get('expense_categories_user_is_willing_to_reduce', '')
    sp_stop = p.get('expense_categories_user_is_willing_to_stop', '')
    sp = f"Protect: {sp_protect} | Reduce: {sp_reduce} | Stop: {sp_stop}"
    
    prot_cats = set(str(sp_protect).split('|')) if pd.notna(sp_protect) and str(sp_protect).strip() else set()
    reduce_cats = set(str(sp_reduce).split('|')) if pd.notna(sp_reduce) and str(sp_reduce).strip() else set()
    stop_cats = set(str(sp_stop).split('|')) if pd.notna(sp_stop) and str(sp_stop).strip() else set()
    
    state = UserState(
        user_id=user_id,
        home_currency=home_currency,
        available_balance=p['current_available_balance'],
        minimum_balance_to_keep=p['minimum_balance_to_keep'],
        financial_priorities=str(fp),
        payment_methods_user_will_consider=str(pm),
        spending_preferences=str(sp),
        protected_categories=prot_cats,
        reduce_categories=reduce_cats,
        stop_categories=stop_cats
    )
    
    user_events = events_df[events_df['user_id'] == user_id]
    for _, ev in user_events.iterrows():
        # Phase 0 notes: use settlement_date if foreign/applicable. We'll use settlement_date if not null.
        ev_date = ev['settlement_date'] if pd.notna(ev['settlement_date']) else ev['event_date']
        
        raw_amt = ev['amount'] if pd.notna(ev['amount']) else None
        ev_currency = ev['currency']
        
        converted_amt = None
        if raw_amt is not None:
            converted_amt = convert(raw_amt, ev_currency, home_currency, ev_date)
            
        raw_min_amt = ev['minimum_allowed_amount'] if pd.notna(ev['minimum_allowed_amount']) else None
        converted_min_amt = None
        if raw_min_amt is not None:
            converted_min_amt = convert(raw_min_amt, ev_currency, home_currency, ev_date)
            
        category = ev['category']
        ev_type = ev['event_type']
        
        recurring_categories = ['salary', 'rent', 'subscription', 'utilities', 'debt_repayment']
        is_recurring = (category in recurring_categories)
        
        # If it's a subscription type, it's also recurring
        if ev_type == 'subscription':
            is_recurring = True
            
        # Detect recurrence dynamically for other essential categories if history supports it
        # We will do this in build_user_state after loading all events by counting descriptions

                
        interval = 'monthly' if is_recurring else None
        
        flexibility = str(ev['flexibility']).strip().lower() if pd.notna(ev['flexibility']) else "fixed"
        
        e = Event(
            event_id=ev['event_id'],
            date=ev_date,
            amount=converted_amt,
            type=ev_type,
            category=category,
            description=str(ev['description']) if pd.notna(ev['description']) else "",
            direction=str(ev['direction']) if pd.notna(ev['direction']) else "",
            recurring=is_recurring,
            interval=interval,
            flexibility=flexibility,
            minimum_allowed_amount=converted_min_amt,
            raw_minimum_allowed_amount=str(ev['minimum_allowed_amount']).strip() if pd.notna(ev['minimum_allowed_amount']) else None,
            status=ev['status'],
            linked_event_id=ev['linked_event_id'] if pd.notna(ev['linked_event_id']) else None
        )
        state.events.append(e)
        
    # Detect recurrence for non-explicitly recurring events
    # Only if history supports it (appears > 1 time)
    desc_counts = {}
    for e in state.events:
        desc_counts[e.description] = desc_counts.get(e.description, 0) + 1
        
    for e in state.events:
        if not e.recurring and e.category in ['groceries', 'transport', 'education', 'healthcare', 'housing', 'insurance'] + list(prot_cats):
            if desc_counts.get(e.description, 0) > 1:
                e.recurring = True
                e.interval = 'monthly' # Default assumption for recurring variable expenses
        
    return state
