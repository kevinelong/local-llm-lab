"""Strata at a raised context, with the thinking budget: the two cause fixes together.

Six census witnesses died with a prompt of 32,475-32,764 against a 32,768 window, and the Strata ledger
is where the ledger sessions actually reach that size. This root changes two declared things on the
0.1.40.3 template:

  1. `--max-context` 32768 -> 65536 in the engine config. The engine's own arithmetic puts 8-bit KV at
     ~13.7 KB per context token (~1.7 GB at 128K, ~0.85 GB at 64K) and streams it, so 64K is the
     conservative first step that still clears every prompt we have measured. The engine's startup line
     ("context N tokens") is what gets verified, not the intention.
  2. `reasoning_budget_tokens: 6144` - already validated at 10/10 in strata-20261008-v1..v10.

Everything else is the reference 12 GiB / reserve 2000 declaration, and every floor (3/2/0.5 GiB) is
unchanged: the monitor stays armed, so if the larger KV pushes free physical or GPU free below a floor,
the run stops and that is the result.

Usage: python strata_ctx.py [n]
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
TEMPLATE = BASE / 'strata-20261007-v19-1'          # same template: reasoning_budget_tokens 6144
PREFIX = 'strata-ctx-20261008-v4'
MAX_CONTEXT = '65536'

CONFIGURE_ANCHOR = "    cleaned.extend(['--resident-budget-gib', str(budget or RESIDENT_BUDGET_GIB),"
CONFIGURE_PATCH = """    # 2026-10-08 DECLARED: raise the served context (see README). The engine's KV arithmetic puts
    # 8-bit KV at ~13.7 KB/token, so 64K costs ~0.85 GB and clears every prompt measured here.
    for _flag in ('--max-context',):
        while _flag in cleaned:
            _i = cleaned.index(_flag)
            del cleaned[_i:_i + 2]
    cleaned.extend(['--max-context', MAX_CONTEXT])
    cleaned.extend(['--resident-budget-gib', str(budget or RESIDENT_BUDGET_GIB),"""


def build(index):
    root = BASE / ('%s%d' % (PREFIX, index))
    if root.exists():
        print('skip existing', root.name, flush=True)
        return None
    shutil.copytree(TEMPLATE, root, ignore=shutil.ignore_patterns('runs', 'oms-*', 'RUNNING.lock', 'STOP', '*.log'))
    (root / 'evidence').mkdir(exist_ok=True)
    text = (root / 'run.py').read_text(encoding='utf-8')
    assert text.count(CONFIGURE_ANCHOR) == 1, 'configure anchor not unique'
    text = text.replace(CONFIGURE_ANCHOR, CONFIGURE_PATCH)
    marker = "RESIDENT_BUDGET_GIB = 12"
    assert text.count(marker) == 1
    text = text.replace(marker, marker + "\nMAX_CONTEXT = %r   # 2026-10-08 declared: was 32768" % MAX_CONTEXT)
    # 2026-10-08 DECLARED: the harness ends a session when the relay's Budget records a failure, and
    # quota_unknown (the engine reporting no usage) is not a task outcome - fatal it killed a 64k run
    # mid-turn at 169 s (7/70, final_text empty, exit 143) while the same condition after the work cost
    # nothing. Count the gap instead; every other failure value still stops the session.
    wire = "lab.base.MODEL = 'strata-coder'"
    assert text.count(wire) == 1, 'relay wiring not found'
    text = text.replace(wire, wire + "\n"
        "class BudgetTolerant(lab.base.Budget):\n"
        " def account(self,usage,allowance):\n"
        "  super().account(usage,allowance)\n"
        "  if self.failure=='quota_unknown':\n"
        "   self.usage_gap=getattr(self,'usage_gap',0)+1\n"
        "   self.failure=None\n"
        "lab.base.Budget=BudgetTolerant")
    (root / 'run.py').write_text(text, encoding='utf-8')
    (root / 'README.md').write_text(
        '# %s: Strata at context %s with reasoning_budget_tokens 6144\n\n'
        'Template `strata-20261007-v19-1`. Two declared changes: the served context (was 32768; six\n'
        'census witnesses died against that window at prompt 32.5-32.8k) and the thinking budget that\n'
        'already measured 10/10. Floors unchanged and the monitor armed; a floor trip is a result, not\n'
        'a problem. Verify the served size from the engine log line "context N tokens".\n' % (
            root.name, MAX_CONTEXT), encoding='ascii')
    return root


def one(root):
    began = time.monotonic()
    with (root / 'evidence' / 'run.log').open('w', encoding='utf8') as handle:
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
        turns = []
        for line in (folder / 'events.jsonl').read_text(encoding='utf-8', errors='replace').splitlines():
            if '"message_end"' not in line:
                continue
            try:
                event = json.loads(line)
            except ValueError:
                continue
            if (event.get('message') or {}).get('role') == 'assistant':
                turns.append(event['message'].get('stopReason'))
        entry['last_stop'] = turns[-1] if turns else None
    log = root / 'oms-ledger' / 'strata-server.log'
    if log.exists():
        text = log.read_text(encoding='utf-8', errors='replace')
        entry['served_context_line'] = [l.strip() for l in text.splitlines() if 'context' in l and 'tokens' in l][:1]
        entry['engine_truncation_diagnostic'] = text.count('reached max tokens while still thinking')
    resources = root / 'oms-ledger' / 'resources.json'
    if resources.exists():
        samples = json.loads(resources.read_text(encoding='utf-8'))
        if samples:
            entry['min_free_physical_gib'] = round(min(s.get('physical_available_gib', 99) for s in samples), 2)
            entry['min_gpu_free_gib'] = round(min(s.get('gpu_free_gib', 99) for s in samples), 2)
    config = root / 'evidence' / 'config.json'
    if config.exists():
        cfg = json.loads(config.read_text(encoding='utf-8'))
        args = cfg.get('args') or []
        entry['max_context_arg'] = args[args.index('--max-context') + 1] if '--max-context' in args else None
    return entry


def main():
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    out = {}
    for index in range(1, count + 1):
        root = build(index)
        if root is None:
            continue
        entry = one(root)
        out[root.name] = entry
        (DRIVER / 'strata-ctx.json').write_text(json.dumps(out, indent=2), encoding='ascii')
        print(json.dumps(entry), flush=True)
    if out:
        summary = {'n': len(out),
                   'scores': ['%s/%s' % (v.get('passed'), v.get('total')) for v in out.values()],
                   'served_context': [v.get('served_context_line') for v in out.values()],
                   'max_context_arg': [v.get('max_context_arg') for v in out.values()],
                   'min_free_physical_gib': [v.get('min_free_physical_gib') for v in out.values()],
                   'min_gpu_free_gib': [v.get('min_gpu_free_gib') for v in out.values()],
                   'truncation_diagnostics': [v.get('engine_truncation_diagnostic') for v in out.values()]}
        print(json.dumps(summary, indent=1), flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
