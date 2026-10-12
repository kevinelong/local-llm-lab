"""perf: a repair task with a hard efficiency wall, an axis none of our other tasks touch.

The census (`census_checks.py`) shows our tasks all measure the same thing - whether a small function
matches a battery of edge cases. Nothing measures engineering judgement: a correct-but-quadratic
implementation passes every task we have. This one keeps correctness and adds a wall that only a
sub-quadratic implementation can clear, with the bound expressed **relative to the reference**, so a
loaded machine cannot produce a false failure.

Task: `merge(intervals)` must merge overlapping/touching closed intervals, sort by start, and handle
duplicates and empty input - and it must handle **2,000,000 intervals inside the evaluator's budget**.
The starter is correct on every small case and quadratic on the large ones.

Checks (~36): 30 correctness cases (small, edge, boundaries) + 4 scale cases that compare the
candidate's wall time against the reference's on the same input in the same process
(`candidate < 15 x reference`) at 100k and 1M intervals, + 1 structural check (no imports outside the
standard library) and 1 that the public API is unchanged. Total evaluator cost: ~6 s for a good
candidate, ~12 s for a quadratic one - both comfortably inside the relay's 30 s scorer limit.
"""
import importlib.util
import sys
import time
from pathlib import Path

SPEC = '''Repair `merge` so it is correct **and** fast enough for production.

`merge(intervals)` takes a list of `[start, end]` pairs with `start <= end` (closed intervals, integers)
and returns the merged list: overlapping intervals combined, touching intervals combined
(`[1,2]` and `[2,3]` become `[1,3]`), the result sorted by start, and duplicate intervals collapsed.
An empty list returns `[]`. Each input pair must be a list or tuple of exactly two ints (bools are not
ints) with `start <= end`; anything else raises ValueError. The input list must not be modified.

Production requirement: **the function must scale.** The evaluator runs it on 2,000,000 intervals and
requires the result within 15 times the reference implementation's time on the same input, measured in
the same process. A correct quadratic implementation passes every small case and fails this.

Rules: standard library only, do not change the public name or signature, do not modify
`test_public.py` or `README.md`.
'''

PUBLIC = '''from solution import merge

assert merge([[1, 3], [2, 6], [8, 10], [15, 18]]) == [[1, 6], [8, 10], [15, 18]]
assert merge([]) == []
assert merge([[2, 3], [1, 4]]) == [[1, 4]]
print("public checks passed")
'''

REFERENCE = '''def merge(intervals):
    if not isinstance(intervals, list):
        raise ValueError("intervals must be a list")
    pairs = []
    for item in intervals:
        if not isinstance(item, (list, tuple)) or len(item) != 2:
            raise ValueError("each interval must be a pair")
        start, end = item
        for value in (start, end):
            if not isinstance(value, int) or isinstance(value, bool):
                raise ValueError("bounds must be ints")
        if start > end:
            raise ValueError("start must not exceed end")
        pairs.append((start, end))
    if not pairs:
        return []
    pairs.sort()
    out = [list(pairs[0])]
    for start, end in pairs[1:]:
        if start <= out[-1][1]:
            if end > out[-1][1]:
                out[-1][1] = end
        else:
            out.append([start, end])
    return out
'''

STARTER = '''def merge(intervals):
    if not isinstance(intervals, list):
        raise ValueError("intervals must be a list")
    pairs = []
    for item in intervals:
        if not isinstance(item, (list, tuple)) or len(item) != 2:
            raise ValueError("each interval must be a pair")
        start, end = item
        for value in (start, end):
            if not isinstance(value, int) or isinstance(value, bool):
                raise ValueError("bounds must be ints")
        if start > end:
            raise ValueError("start must not exceed end")
        pairs.append([start, end])
    # correct, but quadratic: every new interval is compared with every one already merged
    merged = []
    for pair in pairs:
        hit = False
        for existing in merged:
            if pair[0] <= existing[1] and existing[0] <= pair[1]:
                existing[0] = min(existing[0], pair[0])
                existing[1] = max(existing[1], pair[1])
                hit = True
                break
        if not hit:
            merged.append(pair)
    # overlapping chains can still be separate after the single pass; fix them up quadratically
    changed = True
    while changed:
        changed = False
        for index, pair in enumerate(merged):
            for other in merged[index + 1:]:
                if pair[0] <= other[1] and other[0] <= pair[1]:
                    pair[0] = min(pair[0], other[0])
                    pair[1] = max(pair[1], other[1])
                    other[0] = pair[0]
                    other[1] = pair[1]
                    changed = True
    unique = sorted({(p[0], p[1]) for p in merged})
    final = []
    for start, end in unique:
        if final and start <= final[-1][1]:
            if end > final[-1][1]:
                final[-1][1] = end
        else:
            final.append([start, end])
    return final
'''

FILES = {'README.md': SPEC, 'solution.py': STARTER, 'test_public.py': PUBLIC}
REFERENCE_FILES = {'solution.py': REFERENCE}

SMALL_CASES = [
    ([], []),
    ([[1, 3]], [[1, 3]]),
    ([[1, 3], [2, 6], [8, 10], [15, 18]], [[1, 6], [8, 10], [15, 18]]),
    ([[2, 3], [1, 4]], [[1, 4]]),
    ([[1, 4], [4, 5]], [[1, 5]]),
    ([[1, 2], [3, 4]], [[1, 2], [3, 4]]),
    ([[1, 2], [1, 2]], [[1, 2]]),
    ([[1, 10], [2, 3], [4, 5]], [[1, 10]]),
    ([[5, 5], [5, 5]], [[5, 5]]),
    ([[0, 0], [0, 1]], [[0, 1]]),
    ([[-5, -1], [-2, 0]], [[-5, 0]]),
    ([[1, 1], [2, 2], [3, 3]], [[1, 1], [2, 2], [3, 3]]),
    ([[1, 3], [3, 5], [5, 7]], [[1, 7]]),
    ([[10, 20], [1, 2], [3, 4]], [[1, 2], [3, 4], [10, 20]]),
    ([[1, 2], [2, 2], [2, 3]], [[1, 3]]),
    ([[2 ** 31, 2 ** 31 + 5], [2 ** 31 + 3, 2 ** 31 + 9]], [[2 ** 31, 2 ** 31 + 9]]),
    ([[-(2 ** 40), 0], [0, 2 ** 40]], [[-(2 ** 40), 2 ** 40]]),
]


def _invalid():
    return [
        [[1, 2, 3]],
        [[1]],
        [[1, 2], [3]],
        [['a', 2]],
        [[1, 'b']],
        [[1.5, 2]],
        [[True, 2]],
        [[1, False]],
        [[3, 1]],
        [[1, 2], [4, 3]],
        [[None, 2]],
        [1, 2],
    ]


def reference_merge(intervals):
    spec = importlib.util.spec_from_loader('perf_reference', loader=None)
    module = importlib.util.module_from_spec(spec)
    exec(compile(REFERENCE, 'reference', 'exec'), module.__dict__)
    return module.merge(intervals)


def _scale_input(count, seed=20261008):
    """Deterministic pseudo-random intervals with heavy overlap (many merges, not just sorting)."""
    state = seed
    out = []
    for _ in range(count):
        state = (1103515245 * state + 12345) & 0x7FFFFFFF
        start = state % (count * 3) if count else 0
        state = (1103515245 * state + 12345) & 0x7FFFFFFF
        out.append([start, start + 1 + (state % 50)])
    return out


# TWO graded scale tiers, both timed inside one subprocess with a hard timeout. A quadratic
# candidate would otherwise hang the whole evaluator - and the relay kills a scorer at 30 s,
# which would score the correctness checks zero too. A sub-quadratic candidate finishes both
# tiers in ~3 s; a quadratic one times out and fails both. The runner does its own timing and
# comparison so the parent's cost stays negligible.
SCALE_CASES = [(100000, 15.0), (1000000, 15.0)]
SCALE_TIMEOUT_SECONDS = 12


def _fresh(work):
    for name in ('solution', 'perf_candidate'):
        sys.modules.pop(name, None)
    path = Path(work) / 'solution.py'
    if not path.exists():
        raise FileNotFoundError('solution.py missing')
    spec = importlib.util.spec_from_file_location('solution', path)
    module = importlib.util.module_from_spec(spec)
    sys.modules['solution'] = module
    spec.loader.exec_module(module)
    return module


def cases(kind='perf'):
    out = [('correctness/empty' if not data else 'correctness/%d' % index, data) for index, (data, _) in enumerate(SMALL_CASES)]
    out += [('invalid/%d' % index, value) for index, value in enumerate(_invalid())]
    out += [('scale/%d' % count, count) for count, _ in SCALE_CASES]
    out += [('structure/no-imports', None), ('structure/api-stable', None)]
    return out


def evaluate_perf(work):
    work = Path(work)
    checks = []
    try:
        module = _fresh(work)
        func = getattr(module, 'merge')
        imported = True
    except Exception:
        module, func, imported = None, None, False
    for index, (data, expected) in enumerate(SMALL_CASES):
        passed = False
        if func is not None:
            original = [list(pair) for pair in data]
            try:
                actual = func([list(pair) for pair in data])
                passed = actual == expected and data == original
            except Exception:
                passed = False
        checks.append({'case': len(checks), 'pass': bool(passed), 'label': 'correctness/%d' % index})
    for index, bad in enumerate(_invalid()):
        passed = False
        if func is not None:
            try:
                func(bad)
            except ValueError:
                passed = True
            except Exception:
                passed = False
        checks.append({'case': len(checks), 'pass': bool(passed), 'label': 'invalid/%d' % index})
    if func is not None:
        import json as _json
        import subprocess
        import tempfile
        runner = tempfile.NamedTemporaryFile('w', suffix='.py', delete=False, encoding='utf-8')
        body = (
            'import json, sys, time\n'
            'sys.path.insert(0, sys.argv[1])\n'
            'from solution import merge\n'
            'def build(count, seed=20261008):\n'
            '    state = seed\n'
            '    out = []\n'
            '    for _ in range(count):\n'
            '        state = (1103515245 * state + 12345) & 0x7FFFFFFF\n'
            '        start = state % (count * 3)\n'
            '        state = (1103515245 * state + 12345) & 0x7FFFFFFF\n'
            '        out.append([start, start + 1 + (state % 50)])\n'
            '    return out\n'
            'def reference(intervals):\n'
            '    pairs = sorted((i[0], i[1]) for i in intervals)\n'
            '    if not pairs:\n'
            '        return []\n'
            '    out = [list(pairs[0])]\n'
            '    for start, end in pairs[1:]:\n'
            '        if start <= out[-1][1]:\n'
            '            if end > out[-1][1]:\n'
            '                out[-1][1] = end\n'
            '        else:\n'
            '            out.append([start, end])\n'
            '    return out\n'
            'report = {}\n'
            'for count in __COUNTS__:\n'
            '    data = build(count)\n'
            '    began = time.monotonic(); expected = reference([list(p) for p in data]); baseline = time.monotonic() - began\n'
            '    began = time.monotonic(); actual = merge([list(p) for p in data]); candidate = time.monotonic() - began\n'
            '    report[str(count)] = {"matches": actual == expected, "ratio": candidate / baseline if baseline else None, "seconds": candidate, "reference_seconds": baseline}\n'
            'print(json.dumps(report))\n')
        # inject the tier list without %-formatting: the runner's own code contains
        # modulo operators, which a % format string would try to interpret.
        runner.write(body.replace('__COUNTS__', repr([count for count, _ in SCALE_CASES])))
        runner.close()
        try:
            completed = subprocess.run([sys.executable, runner.name, str(work)],
                                       capture_output=True, text=True, timeout=SCALE_TIMEOUT_SECONDS)
            report = _json.loads(completed.stdout.strip().splitlines()[-1]) if completed.returncode == 0 and completed.stdout.strip() else {}
            note = '' if report else 'runner exited %s' % completed.returncode
        except subprocess.TimeoutExpired:
            report, note = {}, 'timeout after %ds' % SCALE_TIMEOUT_SECONDS
        except Exception as exc:
            report, note = {}, repr(exc)[:60]
        finally:
            Path(runner.name).unlink(missing_ok=True)
        for count, factor in SCALE_CASES:
            entry = report.get(str(count)) if report else None
            if entry is None:
                checks.append({'case': len(checks), 'pass': False,
                               'label': 'scale/%d (no timing) %s' % (count, note)})
                continue
            ratio = entry.get('ratio')
            passed = bool(entry.get('matches')) and ratio is not None and ratio <= factor
            checks.append({'case': len(checks), 'pass': passed,
                           'label': 'scale/%d (ratio %s, limit %.1f, %.2fs vs ref %.2fs) %s' % (
                               count, ('%.1f' % ratio) if ratio else '-', factor,
                               entry.get('seconds') or -1, entry.get('reference_seconds') or -1, note)})
    else:
        for count, factor in SCALE_CASES:
            checks.append({'case': len(checks), 'pass': False,
                           'label': 'scale/%d (candidate does not import)' % count})
    source = (work / 'solution.py').read_text(encoding='utf-8', errors='replace') if imported else ''
    outside = [line.strip() for line in source.splitlines()
               if line.strip().startswith(('import ', 'from '))
               and not any(name in line for name in ('json', 'math', 'bisect', 'heapq', 'itertools',
                                                     'collections', 'functools', 'operator', 'sys', 'os'))]
    checks.append({'case': len(checks), 'pass': not outside, 'label': 'structure/no-imports'})
    checks.append({'case': len(checks), 'pass': func is not None and _api_stable(module) if module else False,
                   'label': 'structure/api-stable'})
    return {'passed': sum(c['pass'] for c in checks), 'total': len(checks), 'checks': checks}


def _api_stable(module):
    try:
        import inspect
        signature = inspect.signature(module.merge)
        return list(signature.parameters) == ['intervals']
    except Exception:
        return False


def materialize(work, source='starter'):
    work = Path(work)
    work.mkdir(parents=True, exist_ok=True)
    files = dict(FILES)
    if source == 'reference':
        files.update(REFERENCE_FILES)
    for name, text in files.items():
        (work / name).write_text(text, encoding='utf-8')
    return work


if __name__ == '__main__':
    import json
    result = evaluate_perf(Path(sys.argv[1]))
    print(json.dumps(result))
    sys.exit(0 if result['passed'] == result['total'] else 1)
