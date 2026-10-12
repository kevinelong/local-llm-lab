"""Items 1 and 2 of the new queue: n = 3 per MTP arm, which is also the Qwen3.6 rate set.

Item 1 - MTP versus plain on the coding protocol: the first pair (plain `-v24` 219/221 in 569 s,
MTP `-v25` 220/221 in 785 s) cannot separate the head's effect from run variance at temperature 1.0,
so each arm gets two more samples.
Item 2 - rate sets for the best configurations: Kolibri (3 sweeps) and Nemotron (3 sweeps) already
meet the convention; Qwen3.6 is completed by these same runs.

Templates carry the whole declaration: `candidates-20261007-v24` for the plain arm and
`candidates-20261007-v25` for the MTP arm. Nothing else changes.

Usage: python mtp_arms.py [plain|mtp ...]
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
NAME = 'qwen36-35b-a3b'
MODEL = BASE / 'staged-qwen36-20261007/Qwen3.6-35B-A3B-Q4_K_M.gguf'
SIBLINGS = ('staged_tasks_20260922.py', 'owned_process_20260922.py', 'night_tasks_20260916.py',
            'test_compare_staging_20260922.py', 'validate_staged_tasks_20260922.py')
SPECS = [
    ('plain', 'candidates-20261007-v24', 'candidates-20261007-v26', 2),
    ('mtp', 'candidates-20261007-v25', 'candidates-20261007-v27', 2),
]


def build(template, root):
    (root / 'evidence').mkdir(parents=True)
    (root / 'source').mkdir()
    (root / 'models' / NAME).mkdir(parents=True)
    shutil.copyfile(template / 'run.py', root / 'run.py')
    for name in ('manifest.json', 'protocol.json'):
        shutil.copyfile(template / name, root / name)
    for name in SIBLINGS:
        shutil.copyfile(template / 'source' / name, root / 'source' / name)
    os.link(MODEL, root / 'models' / NAME / MODEL.name)
    (root / 'README.md').write_text(
        '# %s: Qwen3.6-35B-A3B, %s arm, rate sample\n\n'
        'Template `%s` (identical declaration). Purpose: reach n = 3 for the MTP-versus-plain comparison\n'
        'and the Qwen3.6 rate set. The first pair is `-v24` (plain, 219/221 in 569 s) and `-v25`\n'
        '(MTP, 220/221 in 785 s).\n' % (root.name, template.name, template.name), encoding='ascii')


def main():
    want = set(sys.argv[1:])
    out = {}
    for arm, template_name, prefix, repeats in SPECS:
        if want and arm not in want:
            continue
        for index in range(1, repeats + 1):
            root = BASE / ('%s-%d' % (prefix, index))
            if root.exists():
                print('skip existing', root, flush=True)
                continue
            build(BASE / template_name, root)
            began = time.monotonic()
            with (root / 'evidence' / ('%s-run.log' % NAME)).open('w', encoding='utf8') as handle:
                proc = subprocess.run([sys.executable, str(root / 'run.py'), 'coding', NAME], cwd=str(root),
                                      stdout=handle, stderr=subprocess.STDOUT, timeout=14400)
            entry = {'arm': arm, 'root': root.name, 'returncode': proc.returncode,
                     'wall_seconds': round(time.monotonic() - began, 1)}
            evidence = root / 'evidence' / (NAME + '-coding.json')
            if evidence.exists():
                data = json.loads(evidence.read_text())
                entry.update({'parser_passed': data.get('parser_passed'), 'host_passed': data.get('host_passed'),
                              'error': data.get('error')})
                entry['tasks'] = [{'task': t.get('task'),
                                   'passed': (t.get('evaluation') or {}).get('passed'),
                                   'total': (t.get('evaluation') or {}).get('total'),
                                   'clean': t.get('clean_finish'), 'correct': t.get('correct'),
                                   'seconds': t.get('seconds'), 'tokens': t.get('completion_tokens'),
                                   'quota': t.get('quota_failure')} for t in data.get('tasks', [])]
                got = sum(t['passed'] or 0 for t in entry['tasks'])
                tot = sum(t['total'] or 0 for t in entry['tasks'])
                secs = sum(t['seconds'] or 0 for t in entry['tasks'])
                toks = sum(t['tokens'] or 0 for t in entry['tasks'])
                entry.update({'checks': '%d/%d' % (got, tot), 'agent_seconds': round(secs, 1),
                              'tokens': toks, 'effective_tok_s': round(toks / secs, 1) if secs else None})
            out[root.name] = entry
            (DRIVER / 'mtp-arms.json').write_text(json.dumps(out, indent=2), encoding='ascii')
            print(json.dumps(entry), flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
