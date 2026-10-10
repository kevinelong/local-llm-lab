"""Validate controls and selected faults; run only outside timed inference.

Usage: python benchmarks/validate_staged_tasks_20260922.py
Returns JSON and exits nonzero on any failed validation assertion. This is
finite fault sensitivity, not proof of full correctness or equal difficulty.
"""
import json
from pathlib import Path
import subprocess
import sys
import tempfile

import staged_tasks_20260922 as suite


def changed(source, before, after):
    if before not in source:
        raise AssertionError('mutation anchor missing: ' + before)
    return source.replace(before, after, 1)


def mutants(kind):
    code = suite.REFERENCE_CODE[kind]
    if kind == 'graph':
        return {
            'reversed_priority': changed(code, "(-nodes[i]['priority'],i)", "(nodes[i]['priority'],i)"),
            'input_mutation': code + '\n_original = plan\ndef plan(tasks):\n    result = _original(tasks)\n    tasks.reverse()\n    return result\n',
        }
    if kind == 'intervals':
        return {
            'touching_merges': changed(code, 'a<out[-1][1]', 'a<=out[-1][1]'),
            'nested_shrinks': changed(code, 'max(b,out[-1][1])', 'b'),
            'bool_accepted': changed(code, 'type(a)!=int or type(b)!=int', 'not isinstance(a,int) or not isinstance(b,int)'),
        }
    if kind == 'ledger':
        return {
            'debit_adds': changed(code, "int(s) if k == 'credit' else -int(s)", 'int(s)'),
            'count_reset': changed(code, 'count + 1', '1'),
            'unicode_digits': changed(code, 'not s.isascii() or ', ''),
            'blank_records_skipped': changed(code, "if any(len(row) != 3 for row in list(csv.reader(io.StringIO(text), strict=True))[1:]):", 'if False:'),
        }
    if kind == 'events':
        return {
            'overdraft_allowed': changed(code, "if n > balance: raise ValueError('overdraft')", 'if False: raise ValueError("overdraft")'),
            'closed_reopened': changed(code, "if a in states: raise ValueError('duplicate')", "if a in states and states[a][1] != 'closed': raise ValueError('duplicate')"),
            'nonzero_close': changed(code, "elif balance != 0: raise ValueError('nonzero')", 'elif False: raise ValueError("nonzero")'),
            'bool_accepted': changed(code, 'type(n) is not int', 'not isinstance(n, int)'),
        }
    return {
        'escape_collapsed': changed(code, "if depth < 0: raise ValueError('escape')", 'if False: raise ValueError("escape")'),
        'ancestor_allowed': changed(code, "if any('/'.join(parts[:i]) in result for i in range(1, len(parts))):", 'if False:'),
        'adjacent_only_ancestor': changed(code,
            "if any('/'.join(parts[:i]) in result for i in range(1, len(parts))):",
            "if any(b.startswith(a + '/') for a,b in zip(sorted(result), sorted(result)[1:])):"),
        'input_mutation': code + '\n_original = normalize\ndef normalize(entries):\n    result = _original(entries)\n    entries.reverse()\n    return result\n',
    }


def validate():
    assert not suite.same_value([True], [1])
    assert not suite.same_value([{'a': 1.0}], [{'a': 1}])
    assert suite.same_value([{'a': [1, 'x']}], [{'a': [1, 'x']}])
    if set(suite.TASKS) != {'graph', 'intervals', 'ledger', 'events', 'paths'}:
        raise AssertionError('exactly five tasks required')
    # Lock down historical fixture reuse, not merely equivalent descriptions.
    for kind in ('graph', 'intervals'):
        if suite.TASKS[kind] != suite.old.TASKS[kind] or suite.cases(kind) != suite.old.cases(kind):
            raise AssertionError('historical fixture changed')
    records = []
    with tempfile.TemporaryDirectory(prefix='staged-validator-') as temp:
        root = Path(temp)
        for kind, task in suite.TASKS.items():
            work = root / kind
            work.mkdir()
            control = work / 'solution.py'
            control.write_text(suite.REFERENCE_CODE[kind], encoding='ascii')
            reference = suite.evaluate(kind, control)
            if reference['passed'] != reference['total']:
                raise AssertionError((kind, 'reference failed', reference))
            if kind == 'paths':
                decorated = work / 'decorated_control.py'
                decorated.write_text('from __future__ import annotations\nfrom dataclasses import dataclass\n@dataclass\nclass Record:\n    value: int\n' + suite.REFERENCE_CODE[kind], encoding='ascii')
                result = suite.evaluate(kind, decorated)
                if result['passed'] != result['total']:
                    raise AssertionError('valid standard-library decorator rejected')
            public = work / 'test_public.py'
            public.write_text(task['public'], encoding='ascii')
            completed = subprocess.run([sys.executable, '-B', str(public)], cwd=work,
                                       capture_output=True, text=True, timeout=5)
            if completed.returncode != 0 or 'public checks passed' not in completed.stdout:
                raise AssertionError((kind, 'public control', completed.stdout, completed.stderr))
            seeded = work / 'seeded.py'
            seeded.write_text(task['code'], encoding='ascii')
            seed_result = suite.evaluate(kind, seeded)
            if seed_result['total'] - seed_result['passed'] < 2:
                raise AssertionError((kind, 'seed insufficiently detected', seed_result))
            fault_records = {}
            faults = mutants(kind)
            faults['always_crashes'] = 'def ' + suite.FUNCTIONS[kind] + '(value):\n    raise RuntimeError("crash")\n'
            faults['always_empty'] = 'def ' + suite.FUNCTIONS[kind] + '(value):\n    return []\n'
            # Verify mutation checking on an exception path, not just success.
            if kind != 'ledger':
                faults['mutates_then_rejects'] = ('def ' + suite.FUNCTIONS[kind] + '(value):\n'
                                                 '    value.append(None)\n    raise ValueError("bad")\n')
            for index, (name, source) in enumerate(faults.items()):
                path = work / ('mutant_' + str(index) + '.py')
                path.write_text(source, encoding='ascii')
                result = suite.evaluate(kind, path)
                if result['passed'] == result['total']:
                    raise AssertionError((kind, 'undetected fault', name))
                if name in ('always_crashes', 'mutates_then_rejects') and result['passed'] != 0:
                    raise AssertionError((kind, 'invalid program received credit', name, result))
                fault_records[name] = result
            records.append({'task': kind, 'reference': reference, 'seeded': seed_result,
                            'public_control': 'passed', 'mutants': fault_records})
    return {'valid': True, 'tasks': records,
            'limitations': ['Finite deterministic cases; no adversarial-code isolation.',
                            'Graph and intervals retain historical cases and reference algorithms.',
                            'New domain control implementations use distinct algorithms from scoring oracles.',
                            'Task difficulty is intended to be comparable but is not empirically calibrated.']}


if __name__ == '__main__':
    try:
        print(json.dumps(validate(), indent=2))
    except Exception as exc:
        print(json.dumps({'valid': False, 'error': str(exc)}, indent=2))
        sys.exit(1)
