"""Test the per-response cap hypothesis: does giving the reply room remove the truncation class?

Evidence behind it: the whole-history census (census-20261008.txt) classifies 178 sessions - 94
perfect, 44 genuine model errors, 23 TRUNCATED_TURN (stopReason=length with no tool call, which
ends the agent loop before it acts) and 17 EXTERNAL_KILL. MiniCPM5-2B carries the most truncations,
and its witness cases ended at or just past the harness's per-response cap (12288 tokens).

One declared change per root: the Budget subclass raises the per-response cap 12288 -> 32768 and the
session quota 24000 -> 48000, so a long thinking block no longer uses up the whole reply. Wall stays
720 s per task, sampling and runtime unchanged.

Usage: python cap_test.py [minicpm gpt-oss-20b ...]
"""
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

BASE = Path(r'C:\Users\kevin\ai_bench')
DRIVER = BASE / 'new-items-20261007'
SPECS = {
    'minicpm': {'template': 'candidates-20261007-v13-2', 'prefix': 'truncation-20261008-v1'},
    'gpt-oss-20b': {'template': 'candidates-20261007-v18-1', 'prefix': 'truncation-20261008-v2'},
}
SIBLINGS = ('staged_tasks_20260922.py', 'owned_process_20260922.py', 'night_tasks_20260916.py',
            'test_compare_staging_20260922.py', 'validate_staged_tasks_20260922.py')
OLD_BUDGET = " class Budget24000(fresh.Budget):\n  def __init__(self,quota=24000,cap=12288):super().__init__(quota=24000,cap=cap)\n fresh.Budget=Budget24000"
NEW_BUDGET = (" # 2026-10-08 DECLARED, truncation-recovery arm: the census classifies 23 of 84 sub-perfect\n"
              " # sessions as a reply cut inside its thinking (stopReason=length, no tool call, which ends the\n"
              " # agent loop before it acts). One change: give the reply room.\n"
              " class Budget48000(fresh.Budget):\n"
              "  def __init__(self,quota=48000,cap=32768):super().__init__(quota=48000,cap=cap)\n"
              " fresh.Budget=Budget48000")


def build(name, spec):
    template = BASE / spec['template']
    root = BASE / spec['prefix']
    root.mkdir(parents=True, exist_ok=True)
    (root / 'evidence').mkdir(exist_ok=True)
    text = (template / 'run.py').read_text(encoding='utf-8')
    if NEW_BUDGET not in text:
        assert text.count(OLD_BUDGET) == 1, 'budget anchor not found once'
        text = text.replace(OLD_BUDGET, NEW_BUDGET)
    (root / 'run.py').write_text(text, encoding='utf-8')
    # verify() re-hashes the frozen protocol manifest, which lists absolute paths of shared lab
    # files; the template's copy is the right one, and it never lists the running root.
    for extra_name in ('manifest.json', 'protocol.json'):
        target = root / extra_name
        if not target.exists():
            shutil.copyfile(template / extra_name, target)
    (root / 'source').mkdir(exist_ok=True)
    for extra in SIBLINGS:
        target = root / 'source' / extra
        if not target.exists():
            shutil.copyfile(template / 'source' / extra, target)
    (root / 'models' / name).mkdir(parents=True, exist_ok=True)
    for model in (template / 'models' / name).iterdir():
        link = root / 'models' / name / model.name
        if not link.exists():
            os.link(model, link)
    (root / 'README.md').write_text(
        '# %s: %s at a raised per-response cap (truncation-recovery arm)\n\n'
        'Template `%s`, one declared change: `Budget(quota=48000, cap=32768)` instead of\n'
        '`(24000, 12288)`. Wall stays 720 s per task; sampling, runtime and tasks unchanged.\n\n'
        'Question: the census classifies 23 of 84 sub-perfect sessions as a reply truncated inside its\n'
        'thinking (stopReason=length, no tool call). If the cap is the cause, this arm completes instead\n'
        'of collapsing. Baseline for this model is its historical per-task distribution.\n' % (
            root.name, name, spec['template']), encoding='ascii')
    return root


def main():
    wanted = [a for a in sys.argv[1:]] or list(SPECS)
    out = {}
    for name in wanted:
        spec = SPECS[name]
        root = build(name, spec)
        began = time.monotonic()
        with (root / 'evidence' / (name + '-run.log')).open('w', encoding='utf8') as handle:
            proc = subprocess.run([sys.executable, str(root / 'run.py'), 'coding', name], cwd=str(root),
                                  stdout=handle, stderr=subprocess.STDOUT, timeout=14400)
        entry = {'model': name, 'root': root.name, 'returncode': proc.returncode,
                 'wall_seconds': round(time.monotonic() - began, 1)}
        evidence = root / 'evidence' / (name + '-coding.json')
        if evidence.exists():
            data = json.loads(evidence.read_text())
            entry['error'] = data.get('error')
            entry['tasks'] = []
            for task in data.get('tasks', []):
                folder = root / (name + '-' + task.get('task')) / 'trial'
                turns, last_stop, last_has_call = 0, None, None
                events = folder / 'events.jsonl'
                if events.exists():
                    for line in events.read_text(encoding='utf-8', errors='replace').splitlines():
                        if not line.strip():
                            continue
                        try:
                            event = json.loads(line)
                        except ValueError:
                            continue
                        if event.get('type') == 'message_end' and (event.get('message') or {}).get('role') == 'assistant':
                            message = event['message']
                            turns += 1
                            last_stop = message.get('stopReason')
                            last_has_call = any(isinstance(p, dict) and p.get('type') == 'toolCall'
                                                for p in (message.get('content') or []))
                entry['tasks'].append({'task': task.get('task'),
                                       'passed': (task.get('evaluation') or {}).get('passed'),
                                       'total': (task.get('evaluation') or {}).get('total'),
                                       'clean': task.get('clean_finish'), 'correct': task.get('correct'),
                                       'seconds': round(task.get('seconds') or 0, 1),
                                       'tokens': task.get('completion_tokens'),
                                       'quota': task.get('quota_failure'),
                                       'turns': turns, 'last_stop': last_stop, 'last_turn_called_tool': last_has_call})
        out[root.name] = entry
        (DRIVER / 'cap-test.json').write_text(json.dumps(out, indent=2), encoding='ascii')
        print(json.dumps(entry), flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
