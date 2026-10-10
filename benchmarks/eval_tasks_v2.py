"""Versioned external behavioral checks for examples/spec2-tasks.md.

Each group uses a fresh workspace. Setup must succeed. Expected rejections must
exit 1 with a diagnostic and no traceback. CSV provides a schema-neutral view
of persisted task state. Never changes the historical scorer or candidate.
"""
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time

VERSION = '2.0.0'
CHECKS = []

class Candidate:
    def __init__(self, work, timeout=5):
        self.work, self.timeout, self.commands = Path(work), timeout, []

    def call(self, *args, expected=0):
        command = [sys.executable, 'tasks.py', *map(str, args)]
        p = subprocess.run(command, cwd=self.work, capture_output=True, text=True,
                           encoding='utf-8', errors='replace', timeout=self.timeout,
                           env=dict(os.environ, PYTHONIOENCODING='utf-8'))
        text = p.stdout + p.stderr
        self.commands.append(dict(args=list(map(str, args)), exit=p.returncode,
                                  stdout=p.stdout, stderr=p.stderr))
        assert 'Traceback (most recent call last)' not in text, 'uncaught exception'
        assert p.returncode == expected, f'{args}: expected exit {expected}, got {p.returncode}: {text[:300]}'
        if expected: assert text.strip(), 'rejection without diagnostic'
        return text

    def rows(self):
        self.call('export', '_evaluation.csv')
        with (self.work / '_evaluation.csv').open(encoding='utf-8-sig', newline='') as f:
            reader = csv.DictReader(f)
            assert reader.fieldnames == ['id', 'title', 'priority', 'status', 'deps'], 'CSV columns'
            rows = [dict(id=int(r['id']), title=r['title'], priority=int(r['priority']),
                         status=r['status'], deps=sorted(int(v.strip()) for v in r['deps'].split(';') if v.strip()))
                    for r in reader]
        assert len({r['id'] for r in rows}) == len(rows), 'duplicate IDs'
        return sorted(rows, key=lambda r: r['id'])

    def add(self, title, priority=None, deps=()):
        args = ['add', title]
        if priority is not None: args += ['--priority', priority]
        for dep in deps: args += ['--dep', dep]
        self.call(*args)
        matches = [r for r in self.rows() if r['title'] == title]
        assert len(matches) == 1, 'add did not persist unique task'
        return matches[0]['id']

    def ordered(self, text, items):
        # A plan may print names or IDs; priority numbers are not task IDs.
        if all(title in text for _, title in items):
            found = sorted(items, key=lambda item: text.index(item[1]))
            assert found == items, 'wrong output order'
            for _, title in items: assert text.count(title) == 1, 'duplicate task'
        else:
            ids = {i for i, _ in items}
            observed = []
            for line in text.splitlines():
                match = re.match(r'^\s*[\[({#]*\s*(\d+)\b', line)
                if match and int(match[1]) in ids: observed.append(int(match[1]))
            assert observed == [i for i, _ in items], f'unrecognized or incorrect order: {text}'

def check(function):
    CHECKS.append(function)
    return function

@check
def add_defaults_persistence(c):
    i = c.add('V2_ALPHA')
    assert c.rows() == [dict(id=i, title='V2_ALPHA', priority=3, status='open', deps=[])]
    assert 'V2_ALPHA' in c.call('list')
    data = json.loads((c.work / 'tasks.json').read_text(encoding='utf-8-sig'))
    def contains_created(obj):
        if isinstance(obj, dict): return ('created' in obj and obj['created'] is not None) or any(contains_created(v) for v in obj.values())
        if isinstance(obj, list): return any(contains_created(v) for v in obj)
        return False
    assert contains_created(data), 'missing created timestamp'

@check
def invalid_dependency_is_atomic(c):
    a = c.add('V2_KEEP')
    before = c.rows()
    c.call('add', 'V2_BAD', '--dep', a, '--dep', a + 999, expected=1)
    assert c.rows() == before, 'invalid add mutated state'

@check
def priorities_validate(c):
    c.add('V2_KEEP')
    before = c.rows()
    for priority in ('0', '6', 'abc'):
        c.call('add', 'V2_BAD', '--priority', priority, expected=1)
        assert c.rows() == before

@check
def list_status_and_fields(c):
    a = c.add('V2_OPEN', 5)
    b = c.add('V2_DONE', 1)
    c.call('done', b)
    for flag, included, excluded in [('open', 'V2_OPEN', 'V2_DONE'), ('done', 'V2_DONE', 'V2_OPEN')]:
        text = c.call('list', '--status', flag)
        assert included in text and excluded not in text
    text = c.call('list', '--status', 'all')
    assert all(x in text for x in ('V2_OPEN', 'V2_DONE', str(a), str(b), '5'))

@check
def dependencies_validate(c):
    a = c.add('V2_A')
    b = c.add('V2_B')
    before = c.rows()
    for source, target in [(a, a), (a, a + 999), (a + 999, a)]:
        c.call('dep', source, '--on', target, expected=1)
        assert c.rows() == before
    c.call('dep', b, '--on', a)
    assert next(r for r in c.rows() if r['id'] == b)['deps'] == [a]

@check
def done_blocks_and_unblocks(c):
    a = c.add('V2_A')
    b = c.add('V2_B', deps=[a])
    text = c.call('done', b, expected=1).lower()
    assert f'cannot complete: blocked by open dependency {a}' in text
    assert all(r['status'] == 'open' for r in c.rows())
    c.call('done', a)
    c.call('done', b)
    assert all(r['status'] == 'done' for r in c.rows())

@check
def ready_filter_and_order(c):
    low = c.add('V2_LOW', 1)
    first = c.add('V2_FIRST', 5)
    second = c.add('V2_SECOND', 5)
    blocked = c.add('V2_BLOCKED', 5, [low])
    text = c.call('ready')
    assert 'V2_BLOCKED' not in text
    c.ordered(text, [(first,'V2_FIRST'), (second,'V2_SECOND'), (low,'V2_LOW')])
    c.call('done', low)
    text = c.call('ready')
    assert 'V2_LOW' not in text and 'V2_BLOCKED' in text

@check
def plan_dynamic_priority(c):
    a = c.add('V2_ROOT', 4)
    b = c.add('V2_OTHER', 3)
    child = c.add('V2_CHILD', 5, [a])
    c.ordered(c.call('plan'), [(a,'V2_ROOT'), (child,'V2_CHILD'), (b,'V2_OTHER')])
    c.call('done', a)
    text = c.call('plan')
    assert 'V2_ROOT' not in text
    c.ordered(text, [(child,'V2_CHILD'), (b,'V2_OTHER')])

@check
def plan_cycle_exit(c):
    a = c.add('V2_A')
    b = c.add('V2_B')
    c.call('dep', a, '--on', b)
    c.call('dep', b, '--on', a)
    text = c.call('plan', expected=1).lower()
    assert 'cycle detected' in text and str(a) in text and str(b) in text

@check
def rm_guard_and_force_cleanup(c):
    a = c.add('V2_A')
    b = c.add('V2_B', deps=[a])
    before = c.rows()
    c.call('rm', a, expected=1)
    assert c.rows() == before
    c.call('rm', a, '--force')
    assert c.rows() == [dict(id=b, title='V2_B', priority=3, status='open', deps=[])]
    assert 'V2_B' in c.call('ready')

@check
def ids_never_reused(c):
    a = c.add('V2_A')
    b = c.add('V2_B')
    c.call('rm', b)
    n = c.add('V2_C')
    assert n > b > a
    c.call('rm', a)
    c.call('rm', n)
    assert c.add('V2_D') > n, 'ID reused after deleting all tasks'

@check
def block_only_open_dependencies(c):
    a = c.add('V2_OPEN')
    b = c.add('V2_DONE')
    child = c.add('V2_CHILD', deps=[a,b])
    c.call('done', b)
    text = c.call('block', child)
    assert ('V2_OPEN' in text or re.search(rf'\b{a}\b', text))
    # Ignore the subject ID but the completed dependency must not be listed.
    assert 'V2_DONE' not in text and not re.search(rf'\b{b}\b', text)

@check
def graph_reverse_edges(c):
    a = c.add('V2_ROOT')
    b = c.add('V2_CHILD', deps=[a])
    text = c.call('graph')
    lines = text.splitlines()
    starts = [i for i,line in enumerate(lines) if 'V2_ROOT' in line or re.match(rf'^\s*{a}\b', line)]
    assert starts, 'root absent from graph'
    start = starts[0]
    end = next((i for i in range(start+1,len(lines)) if re.match(rf'^\s*[\[#]*{b}\b',lines[i]) and 'V2_CHILD' in lines[i]),len(lines))
    block = '\n'.join(lines[start:end])
    assert 'V2_CHILD' in block or re.search(rf'\b{b}\b',block), 'reverse dependent absent'

@check
def search_case_insensitive(c):
    c.add('V2_MiXeD_Alpha')
    c.add('V2_OTHER')
    text = c.call('search', 'mixed')
    assert 'V2_MiXeD_Alpha' in text and 'V2_OTHER' not in text

@check
def stats_counts_and_depth(c):
    a = c.add('V2_ROOT')
    b = c.add('V2_MIDDLE', deps=[a])
    c.add('V2_LEAF', deps=[b])
    c.add('V2_FREE')
    c.call('done', a)
    text = c.call('stats').lower()
    for label, expected in [('total',4), ('open',3), ('done',1), ('ready',2), ('blocked',1)]:
        m = re.search(rf'\b{label}\b[^\d\n]*(\d+)', text)
        assert m and int(m[1]) == expected, f'wrong {label}: {text}'
    m = re.search(r'\bdepth\b[^\d\n]*(\d+)', text)
    assert m and int(m[1]) in (2,3), 'depth accepts edge or vertex convention'

@check
def csv_roundtrip_state(c):
    a = c.add('V2_TITLE, "quoted"', 5)
    c.add('V2_CHILD', 2, [a])
    c.call('done', a)
    before = c.rows()
    c.call('export', 'roundtrip.csv')
    c.add('V2_EXTRA')
    c.call('import', 'roundtrip.csv')
    assert c.rows() == before, 'roundtrip state differs or import failed to replace'

@check
def csv_missing_dep_rejected(c):
    c.add('V2_KEEP')
    before = c.rows()
    (c.work/'invalid.csv').write_text('id,title,priority,status,deps\n40,BAD,3,open,999\n', encoding='ascii')
    c.call('import', 'invalid.csv', expected=1)
    assert c.rows() == before, 'failed import mutated previous state'

@check
def empty_and_corrupt_storage(c):
    for content in (None, '', 'not valid json {{{'):
        path = c.work / 'tasks.json'
        if content is None:
            if path.exists(): path.unlink()
        else: path.write_text(content, encoding='ascii')
        c.call('list')
        assert c.rows() == []

@check
def selftest_preserves_existing(c):
    c.add('V2_PRESERVE')
    path = c.work/'tasks.json'
    before = path.read_bytes()
    text = c.call('test')
    assert 'all tests passed' in text.lower()
    assert path.read_bytes() == before, 'self-test changed real data'
    assert 'V2_PRESERVE' in c.call('list')

@check
def selftest_no_real_file(c):
    text = c.call('test')
    assert 'all tests passed' in text.lower()
    assert not (c.work/'tasks.json').exists(), 'self-test created real data file'

@check
def invalid_commands_and_arguments(c):
    c.add('V2_KEEP')
    before = c.rows()
    for args in [[], ['bogus'], ['add'], ['done'], ['done','abc'], ['dep','1'],
                 ['rm'], ['block'], ['search'], ['export'], ['import'], ['list','--status','bogus']]:
        c.call(*args, expected=1)
        assert c.rows() == before, f'invalid arguments changed state: {args}'

def evaluate(source, timeout=5):
    source = Path(source).resolve()
    if source.is_dir(): source /= 'tasks.py'
    result = dict(evaluator=VERSION, evaluator_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  source=str(source), checks=[], total=len(CHECKS))
    if source.exists(): result['source_sha256'] = hashlib.sha256(source.read_bytes()).hexdigest()
    start = time.monotonic()
    for test in CHECKS:
        entry = dict(name=test.__name__, passed=False)
        with tempfile.TemporaryDirectory(prefix='tasks_v2_') as directory:
            c = Candidate(directory, timeout)
            try:
                shutil.copy2(source, c.work/'tasks.py')
                test(c)
                entry['passed'] = True
            except subprocess.TimeoutExpired as exc:
                entry.update(failure_type='timeout', error=str(exc))
            except Exception as exc:
                entry.update(failure_type=type(exc).__name__, error=str(exc))
            entry['commands'] = c.commands
        result['checks'].append(entry)
    result.update(passed=sum(c['passed'] for c in result['checks']), seconds=time.monotonic()-start)
    result['success'] = result['passed'] == result['total']
    return result

if __name__ == '__main__':
    result = evaluate(sys.argv[1])
    print(json.dumps(result, indent=2))
    sys.exit(0 if result['success'] else 1)
