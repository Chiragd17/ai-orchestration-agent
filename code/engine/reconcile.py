import copy
from decimal import Decimal
from typing import List, Dict
from engine.data.state import Event

def apply_image_amounts(events: List[Event], image_facts: dict) -> List[Event]:
    out = []
    for e in events:
        new_e = copy.deepcopy(e)
        if new_e.amount is None and new_e.event_id in image_facts:
            new_e.amount = Decimal(str(image_facts[new_e.event_id]))
        out.append(new_e)
    return out

def apply_message_effects(events: List[Event], message_facts: dict) -> List[Event]:
    # Pass-through stub for now, structure allows fact application
    # message_facts maps message_id to a dict of effects
    # We apply them deterministically
    out = []
    event_map = {e.event_id: copy.deepcopy(e) for e in events}
    
    for msg_id, fact in message_facts.items():
        rel_id = fact.get("related_event_id")
        if rel_id and rel_id in event_map:
            ev = event_map[rel_id]
            effect = fact.get("effect")
            if effect == "amend":
                if fact.get("new_amount") is not None:
                    ev.amount = Decimal(str(fact["new_amount"]))
                # We could apply date changes here if needed
            elif effect == "cancel":
                ev.status = "cancelled"
            elif effect == "delay":
                # date change
                pass
            elif effect == "confirm":
                ev.status = "confirmed"
    
    return list(event_map.values())

def tag_flexible(events: List[Event], spending_preferences: dict) -> List[Event]:
    # spending_preferences = {'protect': '...', 'reduce': '...', 'stop': '...'}
    out = []
    for e in events:
        new_e = copy.deepcopy(e)
        if new_e.recurring and new_e.type == 'expense':
            # Note: category is not currently in Event, we should add it if we want to match exact preferences, 
            # or rely on description matching. For now, assuming flexible=True if willing to reduce/stop.
            # (In a real implementation, we'd check if the category matches)
            # Default to whatever state.py had unless overridden here.
            pass
        out.append(new_e)
    return out

def filter_for_forecast(events: List[Event]) -> List[Event]:
    """
    Excludes pending credits, failed transactions, cancelled transactions, 
    duplicates, and unrealized investment valuations FOR FORECASTING PURPOSES ONLY.
    """
    out = []
    for e in events:
        if e.status in ['cancelled', 'failed']:
            continue
        if e.type == 'investment_valuation' and e.status == 'unrealized':
            continue
        # Pending credits: income or refund that is pending
        if e.status == 'pending' and e.direction == 'credit':
            continue
        # Wait, direction might not be set perfectly, also check type
        if e.status == 'pending' and e.type in ['income', 'refund']:
            continue
        out.append(e)
    return out

def resolve(events: List[Event]) -> List[Event]:
    """
    4-tier conflict resolution + duplicate collapsing.
    """
    # 1. Build components
    parent = {}
    def find(i):
        if parent[i] == i: return i
        parent[i] = find(parent[i])
        return parent[i]
    def union(i, j):
        root_i = find(i)
        root_j = find(j)
        if root_i != root_j:
            parent[root_i] = root_j

    for e in events:
        parent[e.event_id] = e.event_id

    # Add edges
    for i, e1 in enumerate(events):
        for j, e2 in enumerate(events):
            if i >= j: continue
            conflict = False
            # Explicit link
            if e1.linked_event_id == e2.event_id or e2.linked_event_id == e1.event_id:
                conflict = True
            # Implicit duplicate
            elif e1.amount is not None and e1.amount == e2.amount and \
                 e1.date == e2.date and e1.description == e2.description:
                conflict = True
            
            if conflict:
                union(e1.event_id, e2.event_id)

    groups = {}
    for e in events:
        root = find(e.event_id)
        if root not in groups:
            groups[root] = []
        groups[root].append(e)

    resolved_events = []
    
    def extract_id_num(ev_id):
        try:
            return int(ev_id.split('_')[1])
        except:
            return 0

    for root, group in groups.items():
        if len(group) == 1:
            resolved_events.append(group[0])
            continue
            
        # We have a conflict group. Pick a winner.
        winner = group[0]
        for candidate in group[1:]:
            # Priority 1: Explicit cancellation, settlement, or amendment overrides the modified.
            # If candidate links to winner, candidate is the modifier.
            if candidate.linked_event_id == winner.event_id:
                winner = candidate
                continue
            elif winner.linked_event_id == candidate.event_id:
                continue # winner is already the modifier
            
            # Priority 3: Settled wins over estimate
            if candidate.status == 'settled' and winner.status != 'settled':
                winner = candidate
                continue
            elif winner.status == 'settled' and candidate.status != 'settled':
                continue
                
            # Priority 2: Newer record wins. (Higher event_id implies newer)
            w_num = extract_id_num(winner.event_id)
            c_num = extract_id_num(candidate.event_id)
            
            # Wait, if they are exactly the same in status, maybe just pick newer
            # But let's check Priority 4 first if they are truly ambiguous
            
            # Priority 4: Financially safer interpretation
            if winner.amount != candidate.amount and winner.amount is not None and candidate.amount is not None:
                # Safer means lower safe-to-spend. 
                # For expenses (direction=debit), safer = higher amount
                # For income (direction=credit), safer = lower amount
                w_is_credit = winner.type in ['income', 'refund'] or winner.direction == 'credit'
                if w_is_credit:
                    if candidate.amount < winner.amount:
                        winner = candidate
                        continue
                else:
                    if candidate.amount > winner.amount:
                        winner = candidate
                        continue
            
            # If all else fails, pick newer
            if c_num > w_num:
                winner = candidate
                
        resolved_events.append(winner)

    return resolved_events
