import pandas as pd
from decimal import Decimal
import os
import datetime

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "dataset"))

def parse_date(date_str):
    if pd.isna(date_str) or str(date_str).strip() == "":
        return None
    return datetime.datetime.strptime(str(date_str).strip(), "%Y-%m-%d").date()

def parse_decimal(val):
    if pd.isna(val) or str(val).strip() == "":
        return None
    return Decimal(str(val).strip())

def load_exchange_rates():
    df = pd.read_csv(os.path.join(DATA_DIR, "exchange_rates.csv"))
    df['rate_date'] = df['rate_date'].apply(parse_date)
    df['rate'] = df['rate'].apply(parse_decimal)
    return df

def load_financial_events():
    df = pd.read_csv(os.path.join(DATA_DIR, "financial_events.csv"))
    df['event_date'] = df['event_date'].apply(parse_date)
    df['settlement_date'] = df['settlement_date'].apply(parse_date)
    df['amount'] = df['amount'].apply(parse_decimal)
    df['minimum_allowed_amount'] = df['minimum_allowed_amount'].apply(parse_decimal)
    return df

def load_financial_profiles():
    df = pd.read_csv(os.path.join(DATA_DIR, "financial_profiles.csv"))
    df['current_available_balance'] = df['current_available_balance'].apply(parse_decimal)
    df['minimum_balance_to_keep'] = df['minimum_balance_to_keep'].apply(parse_decimal)
    return df
