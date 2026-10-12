"""Turn the Strata thinking-budget mitigation into a rate: the ledger, ten fresh roots.

The 6/6 at 70/70 with zero engine truncation diagnostics is not a rate. This runs arm A's declared
change (`reasoning_budget_tokens: 6144`, the one recommended by the engine's own log line) ten times
on the same 12 GiB template, and reports each session's score, ending and the engine's truncation
diagnostic, against the 13-session pre-change baseline (3 truncation failures, all sub-70).

Usage: python ledger_rate.py [n]
"""
import importlib.util
import json
import sys
import time
from pathlib import Path

BASE = Path(r'C:\Users\kevin\ai_bench')
DRIVER = BASE / 'new-items-20261007'
TEMPLATE = BASE / 'strata-20261007-v19-1'          # arm A: reasoning_budget_tokens 6144
PREFIX = 'strata-20261008-v'


def load_ledger_budget():
    spec = importlib.util.spec_from_file_location('lb', DRIVER / 'ledger_budget.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    lb = load_ledger_budget()
    out = {}
    for index in range(1, count + 1):
        root = BASE / ('%s%d' % (PREFIX, index))
        if root.exists():
            print('skip existing', root.name, flush=True)
            continue
        # copy the arm-A template, keeping its declared knob
        import shutil
        shutil.copytree(TEMPLATE, root, ignore=shutil.ignore_patterns('runs', 'oms-*', 'RUNNING.lock', 'STOP', '*.log'))
        (root / 'evidence').mkdir(exist_ok=True)
        began = time.monotonic()
        with (root / 'evidence' / 'run.log').open('w', encoding='utf8') as handle:
            import subprocess
            subprocess.run([sys.executable, str(root / 'run.py'), 'configure'], cwd=str(root),
                           stdout=handle, stderr=subprocess.STDOUT, timeout=1800)
            subprocess.run([sys.executable, str(root / 'run.py'), 'screen', 'ledger'], cwd=str(root),
                           stdout=handle, stderr=subprocess.STDOUT, timeout=14400)
        entry = {'root': root.name, 'wall_seconds': round(time.monotonic() - began, 1)}
        folder = root / 'runs' / 'oms-ledger'
        if (folder / 'result.json').exists():
            result = json.loads((folder / 'result.json').read_text(encoding='utf-8'))
            evaluation = result.get('evaluation') or {}
            entry.update({'passed': evaluation.get('passed'), 'total': evaluation.get('total'),
                          'clean': result.get('clean_finish'), 'correct': result.get('correct'),
                          'exit': result.get('exit_code'), 'seconds': round(result.get('seconds') or 0, 1),
                          'tokens': result.get('completion_tokens')})
            stop = None
            for line in (folder / 'events.jsonl').read_text(encoding='utf-8', errors='replace').splitlines():
                if not line.strip():
                    continue
                try:
                    event = json.loads(line)
                except ValueError:
                    continue
                if event.get('type') == 'message_end' and (event.get('message') or {}).get('role') == 'assistant':
                    stop = event['message'].get('stopReason')
            entry['last_stop'] = stop
        log = root / 'oms-ledger' / 'strata-server.log'
        entry['engine_truncation_diagnostic'] = (log.read_text(encoding='utf-8', errors='replace')
                                                 .count('reached max tokens while still thinking')) if log.exists() else None
        config = root / 'evidence' / 'config.json'
        if config.exists():
            entry['reasoning_budget_tokens'] = json.loads(config.read_text(encoding='utf-8')).get('reasoning_budget_tokens')
        out[root.name] = entry
        (DRIVER / 'ledger-rate.json').write_text(json.dumps(out, indent=2), encoding='ascii')
        print(json.dumps(entry), flush=True)
    scores = [v['passed'] for v in out.values() if v.get('passed') is not None]
    diagnostics = [v['engine_truncation_diagnostic'] for v in out.values()]
    if scores:
        print(json.dumps({'n': len(scores), 'scores': scores,
                          'perfect': sum(1 for s in scores if s == 70),
                          'engine_truncation_diagnostics': diagnostics,
                          'baseline': '13 pre-change sessions: 3 truncation failures, all sub-70'}, indent=1))
    return 0


if __name__ == '__main__':
    sys.exit(main())
