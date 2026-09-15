"""Supplemental black-box checks for spec2; keeps the historical scorer unchanged."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

source = Path(sys.argv[1]).resolve() / 'tasks.py'
results = []

def run(work, *args):
    p = subprocess.run([sys.executable, 'tasks.py', *args], cwd=work, capture_output=True,
                       text=True, encoding='utf-8', errors='replace', timeout=15)
    return p.returncode, p.stdout + p.stderr

def listing_id(text, marker):
    lines = [line for line in text.splitlines() if marker in line]
    if len(lines) != 1:
        raise ValueError('Expected one task line')
    line = lines[0]
    # Spec requires showing id. Accept JSON records and common tabular id-first output.
    try:
        value = json.loads(line)
        if isinstance(value, dict): return int(value['id'])
    except (ValueError, KeyError):
        pass
    return int(re.search(r'\d+', line).group())

def check(name, test):
    try:
        with tempfile.TemporaryDirectory(prefix='lab_extra_') as directory:
            work = Path(directory)
            shutil.copy2(source, work / 'tasks.py')
            ok = bool(test(work))
            results.append({'name': name, 'pass': ok})
    except Exception as exc:
        results.append({'name': name, 'pass': False, 'error': str(exc)})

def no_id_reuse(w):
    run(w, 'add', 'KEEP_A')
    run(w, 'add', 'REMOVE_B')
    _, before = run(w, 'list')
    removed_id = listing_id(before, 'REMOVE_B')
    if run(w, 'rm', str(removed_id))[0] != 0: return False
    if run(w, 'add', 'NEW_C')[0] != 0: return False
    _, after = run(w, 'list')
    return listing_id(after, 'NEW_C') > removed_id

def priority_order(w):
    for title, priority in [('LOW_P','1'),('HIGH_P','5'),('MID_P','3')]:
        if run(w, 'add', title, '--priority', priority)[0] != 0: return False
    code, text = run(w, 'plan')
    return code == 0 and text.index('HIGH_P') < text.index('MID_P') < text.index('LOW_P')

def selftest_preserves(w):
    run(w, 'add', 'PRESERVE_ME')
    path = w / 'tasks.json'
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    code, _ = run(w, 'test')
    return code == 0 and hashlib.sha256(path.read_bytes()).hexdigest() == before

def stats_depth(w):
    run(w, 'add', 'ROOT_X')
    for number in range(1, 4):
        run(w, 'add', 'CHAIN_' + str(number), '--dep', str(number))
    code, text = run(w, 'stats')
    match = re.search(r'depth[^\d]*(\d+)', text, re.I)
    # The spec does not state edges versus vertices; accept either convention.
    return code == 0 and match is not None and int(match.group(1)) in (3, 4)

check('ids_never_reused', no_id_reuse)
check('plan_priority_ties', priority_order)
check('selftest_preserves_data', selftest_preserves)
check('stats_chain_depth', stats_depth)
print(json.dumps({'checks': results, 'passed': sum(r['pass'] for r in results), 'total': len(results)}, indent=2))
