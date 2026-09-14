import os
import sys
import unittest

project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)

def check():
    out = []
    out.append("## Phase 1 & Phase 2 System Check")
    
    # Check Phase 1
    out.append("### Phase 1: Data Layer")
    try:
        from engine.data.loaders import load_csv
        out.append("✅ `engine/data/loaders.py` exists and is loadable.")
    except Exception as e:
        out.append(f"❌ `engine/data/loaders.py` failed: {e}")
        
    try:
        from engine.data.currency import convert
        out.append("✅ `engine/data/currency.py` exists and is loadable.")
    except Exception as e:
        out.append(f"❌ `engine/data/currency.py` failed: {e}")
        
    try:
        from engine.data.state import UserState, Event
        out.append("✅ `engine/data/state.py` exists (UserState, Event dataclasses).")
    except Exception as e:
        out.append(f"❌ `engine/data/state.py` failed: {e}")

    # Check Phase 2
    out.append("\n### Phase 2: Reconciliation & Simulation")
    try:
        from engine.reconcile import resolve, filter_for_forecast, tag_flexible, apply_image_amounts, apply_message_effects
        out.append("✅ `engine/reconcile.py` exists with all required functions (resolve, filter_for_forecast, tag_flexible, apply_*).")
    except Exception as e:
        out.append(f"❌ `engine/reconcile.py` missing functions: {e}")
        
    try:
        from engine.simulate import simulate, calculate_amount_safe_to_pay, project_recurring_events
        out.append("✅ `engine/simulate.py` exists with simulation and projection logic.")
    except Exception as e:
        out.append(f"❌ `engine/simulate.py` missing functions: {e}")
        
    # Run tests
    out.append("\n### Unit Tests (Phase 2)")
    test_result = os.popen(f"{sys.executable} -m unittest tests/test_reconcile.py").read()
    # unittest prints to stderr usually
    import subprocess
    res = subprocess.run([sys.executable, "-m", "unittest", "tests/test_reconcile.py"], capture_output=True, text=True)
    if res.returncode == 0:
        out.append("✅ All 5 conflict scenario tests + filter test passed.")
        out.append("```text\n" + res.stderr.strip() + "\n```")
    else:
        out.append("❌ Tests failed.")
        out.append("```text\n" + res.stderr.strip() + "\n```")
        
    with open("notes/phase_check.md", "w") as f:
        f.write("\n".join(out))

if __name__ == '__main__':
    check()
