"""Item 3 mitigation: does a thinking budget (or the close-retry) stop the ledger from dying?

Evidence behind it: every model-side ledger failure ends with the engine's own diagnostic -
"the reply reached max tokens while still thinking, so it has no answer" - and the harness
message shows stopReason=length with no tool call, which is what ends the agent loop. The
engine documents two fixes, both opt-in and both set in strata-<model>.json:

  A  "reasoning_budget_tokens": N  - caps the thinking at N tokens; at the cap the server ends
     the thinking with a wrap-up line and </think>, so the model answers from there. Guarantees
     output room for an action.
  B  "reasoning_close_retry": true - for a reply that ended inside its thinking with no answer
     and no tool call, closes the thinking once and continues.

Baseline: the same template at the same 12 GiB resident budget, ledger read 70/70, 70/70,
7/70 (and one guard-stop), i.e. 3/4 complete.

Usage: python ledger_budget.py [A|B ...]
"""
import importlib.util
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

BASE = Path(r'C:\Users\kevin\ai_bench')
DRIVER = BASE / 'new-items-20261007'
TEMPLATE = BASE / 'strata-20261007-v15-1'
ARMS = {
    'A': ('strata-20261007-v19', 'reasoning_budget_tokens', 6144),
    'B': ('strata-20261007-v20', 'reasoning_close_retry', True),
}
ANCHOR = "    path.write_text(json.dumps(cfg, indent=1), encoding='utf-8')"


def build(arm, root):
    name, key, value = ARMS[arm]
    (root / 'evidence').mkdir(parents=True)
    text = (TEMPLATE / 'run.py').read_text(encoding='utf-8')
    assert text.count(ANCHOR) == 1
    extra = ("    # 2026-10-08 DECLARED, item 3 mitigation (%s): the ledger failures are replies cut\n"
             "    # while still thinking (engine: \"reached max tokens while still thinking\"), so give the\n"
             "    # thinking a bound and the answer room.\n"
             "    cfg[%r] = %r\n" % (arm, key, value))
    text = text.replace(ANCHOR, extra + ANCHOR)
    (root / 'run.py').write_text(text, encoding='utf-8')
    (root / 'README.md').write_text(
        '# %s: ledger with %s = %r (item 3 mitigation, arm %s)\n\n'
        'Template `strata-20261007-v15-1`, one declared change (see run.py configure). Baseline at the\n'
        'same budget: 70/70, 70/70, 7/70. Evidence: failures show the engine diagnostic "reached max\n'
        'tokens while still thinking" and stopReason=length with no tool call.\n' % (root.name, key, value, arm),
        encoding='ascii')


def main():
    want = set(sys.argv[1:])
    out = {}
    for arm, (prefix, key, value) in ARMS.items():
        if want and arm not in want:
            continue
        for index in range(1, 4):
            root = BASE / ('%s-%d' % (prefix, index))
            if root.exists():
                print('skip existing', root, flush=True)
                continue
            build(arm, root)
            began = time.monotonic()
            with (root / 'evidence' / 'run.log').open('w', encoding='utf8') as handle:
                subprocess.run([sys.executable, str(root / 'run.py'), 'configure'], cwd=str(root),
                               stdout=handle, stderr=subprocess.STDOUT, timeout=1800)
                subprocess.run([sys.executable, str(root / 'run.py'), 'screen', 'ledger'], cwd=str(root),
                               stdout=handle, stderr=subprocess.STDOUT, timeout=14400)
            entry = {'arm': arm, key: value, 'root': root.name, 'wall_seconds': round(time.monotonic() - began, 1)}
            folder = root / 'runs' / 'oms-ledger'
            if (folder / 'result.json').exists():
                result = json.loads((folder / 'result.json').read_text(encoding='utf-8'))
                evaluation = result.get('evaluation') or {}
                entry.update({'passed': evaluation.get('passed'), 'total': evaluation.get('total'),
                              'clean': result.get('clean_finish'), 'correct': result.get('correct'),
                              'exit': result.get('exit_code'), 'seconds': round(result.get('seconds') or 0, 1),
                              'tokens': result.get('completion_tokens'), 'quota': result.get('quota_failure')})
                stop = None
                lengths = []
                for line in (folder / 'events.jsonl').read_text(encoding='utf-8').splitlines():
                    try:
                        event = json.loads(line)
                    except ValueError:
                        continue
                    if event.get('type') == 'message_end' and (event.get('message') or {}).get('role') == 'assistant':
                        message = event['message']
                        stop = message.get('stopReason')
                        content = message.get('content')
                        if isinstance(content, list):
                            for part in content:
                                if isinstance(part, dict) and part.get('type') == 'thinking':
                                    lengths.append(len(part.get('thinking') or ''))
                entry['last_stop'] = stop
                entry['thinking_chars'] = lengths
                log = root / 'oms-ledger' / 'strata-server.log'
                if log.exists():
                    text = log.read_text(encoding='utf-8', errors='replace')
                    entry['engine_truncation_diagnostic'] = text.count('reached max tokens while still thinking')
            out[root.name] = entry
            (DRIVER / 'ledger-budget.json').write_text(json.dumps(out, indent=2), encoding='ascii')
            print(json.dumps(entry), flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
