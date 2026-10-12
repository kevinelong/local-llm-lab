"""Every Strata ledger sample on disk, with the declaration it ran under and how it ended.

Purpose: item 3 of the new queue. A ledger score is only interpretable next to (a) the engine
version and declared budget, (b) whether the session completed and (c) whether the failure was
the model's (finish_reason=length, i.e. output cut before it could act) or the harness's (a
resource guard SIGTERM). Read-only.
"""
import json
import re
from pathlib import Path

BASE = Path(r'C:\Users\kevin\ai_bench')


def last_stop_reason(events):
    reason = None
    for line in events:
        try:
            e = json.loads(line)
        except ValueError:
            continue
        if e.get('type') != 'message_end':
            continue
        m = e.get('message') or {}
        if m.get('role') == 'assistant':
            reason = m.get('stopReason')
    return reason


def main():
    print('%-24s %-9s %-8s %-8s %-7s %-6s %-7s %-6s %-9s %-9s %s' % (
        'root', 'engine', 'budget', 'reserve', 'score', 'clean', 'exit', 'secs', 'ended', 'trunc_diag', ''))
    for root in sorted(BASE.glob('strata-2026*')):
        run = root / 'run.py'
        if not run.exists():
            continue
        text = run.read_text(encoding='utf-8', errors='replace')
        engine = re.search(r"engine-src-v([\d.]+)", text)
        budget = re.search(r'RESIDENT_BUDGET_GIB = (\d+)', text)
        reserve = re.search(r'VRAM_RESERVE_MIB = (\d+)', text)
        for label in ('oms-ledger',):
            folder = root / 'runs' / label
            result_path = folder / 'result.json'
            if not result_path.exists():
                continue
            result = json.loads(result_path.read_text(encoding='utf-8'))
            evaluation = result.get('evaluation') or {}
            events_path = folder / 'events.jsonl'
            stop = last_stop_reason(events_path.read_text(encoding='utf-8').splitlines()) if events_path.exists() else None
            log = root / label / 'strata-server.log'
            diag = log.read_text(encoding='utf-8', errors='replace').count('reached max tokens while still thinking') if log.exists() else -1
            print('%-24s %-9s %-8s %-8s %-7s %-6s %-7s %-6s %-9s %-9s %s' % (
                root.name, engine.group(1) if engine else '?', budget.group(1) if budget else '?',
                reserve.group(1) if reserve else '?',
                '%s/%s' % (evaluation.get('passed'), evaluation.get('total')),
                result.get('clean_finish'), result.get('exit_code'),
                round(result.get('seconds') or 0, 1), stop, diag, ''))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
