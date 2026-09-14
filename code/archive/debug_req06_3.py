import sys
import os
import datetime
from decimal import Decimal
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)
from engine.data.state import build_user_state

state = build_user_state("user_06")
print(f"Start balance: {state.available_balance}")
