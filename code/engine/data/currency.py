import datetime
from decimal import Decimal
from engine.data.loaders import load_exchange_rates

_rates_cache = None

def _get_rates():
    global _rates_cache
    if _rates_cache is None:
        df = load_exchange_rates()
        _rates_cache = {}
        for _, row in df.iterrows():
            _rates_cache[(row['rate_date'], row['from_currency'], row['to_currency'])] = row['rate']
    return _rates_cache

def convert(amount: Decimal, from_currency: str, to_currency: str, on_date: datetime.date) -> Decimal:
    """
    Converts amount from from_currency to to_currency exactly on on_date.
    Assumption per Phase 0 notes: we use the event's exact date (either event_date 
    or settlement_date as passed here), not the request date.
    """
    if amount is None:
        return None
    if from_currency == to_currency:
        return amount
        
    rates = _get_rates()
    
    key = (on_date, from_currency, to_currency)
    if key in rates:
        return amount * rates[key]
        
    inv_key = (on_date, to_currency, from_currency)
    if inv_key in rates:
        return amount / rates[inv_key]
        
    raise ValueError(f"No exchange rate found for {from_currency} to {to_currency} on {on_date}. No silent fallback allowed.")
