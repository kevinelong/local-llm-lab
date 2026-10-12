import importlib.util, sys
from pathlib import Path
spec = importlib.util.spec_from_file_location('frozen', r'C:\Users\kevin\ai_bench\completion-20260923-v1\source\staged_tasks_20260922.py')
m = importlib.util.module_from_spec(spec); sys.modules['frozen'] = m; spec.loader.exec_module(m)
def reconcile(text):
    return m.reference_ledger(text)
