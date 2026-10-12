"""A long-context repair task: one wrong function among ~700 in a single large module.

Why: every task so far fits a 9-10k-token prompt, so the screen has never measured the window the RAM
upgrade bought - and the census shows six sessions that died because their transcript filled a 32,768
window. This task makes the workspace itself long: `legacy.py` is a deterministic ~224 KB module
(~64k tokens) of correct helpers with exactly one defective function, and the agent must locate it with
grep/read and fix only that function.

Checks (~29): the target function's behaviour on 25 cases; that the module still imports; that every
other top-level function's source is unchanged (normalised); that no functions were added or removed;
and that ten sampled helpers still return the reference values. The minimal-edit guards are what make
this different from `repo`: a wholesale rewrite of a 250 KB file fails even if the fix is right.

Reference and candidate come from the same generator, so the evaluation needs no extra file.
"""
import ast
import importlib.util
import random
import re
import sys
from pathlib import Path

SEED = 20261008
N_HELPERS = 1800

SPEC = '''Repair one function in a large legacy module.

`legacy.py` is a production module of ~1800 small helpers. Exactly one function is wrong:
`reconcile_batch(records)`.

Specification of `reconcile_batch(records)`:
- `records` is a list of `(account, cents)` pairs, processed in order.
- `account` must be a nonempty string equal to its own `strip()`; anything else raises ValueError.
- `cents` must be an int (bool is not an int) and must be >= 0; anything else raises ValueError.
- Return a list of `(account, total, count)` tuples sorted by account, where `total` is the sum of that
  account's cents and `count` is how many records that account had. Every record counts, including
  zero-cent records. An empty list returns `[]`.

Rules:
- Fix `reconcile_batch` only. **Every other function in `legacy.py` must keep its exact source.**
- Do not add or remove functions, do not modify `README.md` or `test_public.py`, and use only the
  Python standard library.
- Run the public tests, then audit the cases they do not cover. Finish with a brief summary.
'''

PUBLIC = '''from legacy import reconcile_batch
from solution import reconcile_batch as shimmed

assert shimmed is not None
assert reconcile_batch([("a", 10), ("a", 0)]) == [("a", 10, 2)]
assert reconcile_batch([]) == []
assert reconcile_batch([("b", 1), ("a", 2)]) == [("a", 2, 1), ("b", 1, 1)]
print("public checks passed")
'''

SHIM = 'from legacy import reconcile_batch\n'

TARGET = 'reconcile_batch'

BUGGY_TARGET = '''def reconcile_batch(records):
    """Total the cents per account, in account order.

    records: list of (account, cents) pairs. Returns [(account, total, count)] sorted by account.
    """
    totals = {}
    counts = {}
    for account, cents in records[:-1]:
        if not isinstance(account, str) or account != account.strip() or not account:
            raise ValueError('invalid account')
        if not isinstance(cents, int) or isinstance(cents, bool) or cents < 0:
            raise ValueError('invalid cents')
        totals[account] = totals.get(account, 0) + cents
        counts[account] = counts.get(account, 0) + 1
    return sorted((a, totals[a], counts[a]) for a in totals)
'''

FIXED_TARGET = '''def reconcile_batch(records):
    """Total the cents per account, in account order.

    records: list of (account, cents) pairs. Returns [(account, total, count)] sorted by account.
    """
    totals = {}
    counts = {}
    for account, cents in records:
        if not isinstance(account, str) or account != account.strip() or not account:
            raise ValueError('invalid account')
        if not isinstance(cents, int) or isinstance(cents, bool) or cents < 0:
            raise ValueError('invalid cents')
        totals[account] = totals.get(account, 0) + cents
        counts[account] = counts.get(account, 0) + 1
    return sorted((a, totals[a], counts[a]) for a in totals)
'''

_HEADER = ('"""legacy.py - long-lived account helpers. Generated fixture; do not reformat."""\n'
           'import json\nimport math\nimport re\nimport string\n\n')


def helper_name(index):
    return 'helper_%04d' % index


def helper_source(index):
    """A deterministic, correct, small function; varied enough that the file is real text."""
    style = index % 7
    name = helper_name(index)
    if style == 0:
        return 'def %s(value):\n    """Scale an integer by a fixed factor."""\n    return value * %d + %d\n' % (name, index % 17 + 1, index % 5)
    if style == 1:
        return 'def %s(text):\n    """Count a fixed character class in a string."""\n    return sum(1 for ch in str(text) if ch in string.%s)\n' % (name, ('ascii_letters', 'digits', 'ascii_lowercase', 'ascii_uppercase', 'punctuation', 'whitespace')[index % 6])
    if style == 2:
        return 'def %s(items):\n    """Keep the values that satisfy a modular test."""\n    return [v for v in items if isinstance(v, int) and v %% %d == %d]\n' % (name, index % 9 + 2, index % 9 + 2 - 1)
    if style == 3:
        return 'def %s(text):\n    """Normalise internal spacing."""\n    return re.sub(r"\\\\s+", " ", str(text).strip())[:%d]\n' % (name, index % 40 + 8)
    if style == 4:
        return 'def %s(n):\n    """Round up to the next multiple."""\n    step = %d\n    return ((int(n) + step - 1) // step) * step\n' % (name, index % 11 + 2)
    if style == 5:
        return 'def %s(record):\n    """Render a record as compact JSON."""\n    return json.dumps(record, sort_keys=True, separators=(",", ":"))[:%d]\n' % (name, index % 60 + 16)
    return 'def %s(value):\n    """A bounded logarithm helper."""\n    return round(math.log1p(abs(value) + %d), %d)\n' % (name, index % 7, index % 4 + 2)


def module_source(buggy=True):
    """The whole module: header, helpers in order, then the target function last."""
    parts = [_HEADER]
    for index in range(N_HELPERS):
        parts.append(helper_source(index))
        parts.append('\n')
    parts.append(BUGGY_TARGET if buggy else FIXED_TARGET)
    return ''.join(parts)


def _reference_reconcile(records):
    totals, counts = {}, {}
    for account, cents in records:
        if not isinstance(account, str) or account != account.strip() or not account:
            raise ValueError('invalid account')
        if not isinstance(cents, int) or isinstance(cents, bool) or cents < 0:
            raise ValueError('invalid cents')
        totals[account] = totals.get(account, 0) + cents
        counts[account] = counts.get(account, 0) + 1
    return sorted((a, totals[a], counts[a]) for a in totals)


def _cases():
    rng = random.Random(SEED)
    out = []
    out.append(('empty', []))
    out.append(('single', [('a', 5)]))
    out.append(('zero-only', [('a', 0)]))
    out.append(('trailing-zero', [('a', 5), ('a', 0)]))
    out.append(('leading-zero', [('a', 0), ('a', 5)]))
    out.append(('accumulate', [('a', 3), ('a', 4), ('a', 5)]))
    out.append(('two-accounts', [('b', 1), ('a', 2)]))
    out.append(('interleaved', [('b', 1), ('a', 2), ('b', 3), ('a', 4)]))
    out.append(('zero-account', [('a', 0), ('b', 0)]))
    out.append(('big', [('a', 10 ** 9)]))
    out.append(('unicode-account', [('caf\u00e9', 3), ('caf\u00e9', 4)]))
    out.append(('spaces-inside', [('two words', 2), ('two words', 2)]))
    out.append(('comma-inside', [('a,b', 1)]))
    for label, bad in (('bad-account-empty', ('', 1)), ('bad-account-space', (' a', 1)),
                       ('bad-account-trailing', ('a ', 1)), ('bad-cents-negative', ('a', -1)),
                       ('bad-cents-float', ('a', 1.5)), ('bad-cents-bool', ('a', True)),
                       ('bad-cents-str', ('a', '1')), ('bad-account-int', (3, 1)),
                       ('bad-cents-none', ('a', None))):
        out.append((label, [('ok', 1), bad]))
    for index in range(4):
        records = []
        for _ in range(rng.randrange(1, 25)):
            records.append((rng.choice(['a', 'b', 'zz', 'two words', 'caf\u00e9', 'Q']), rng.choice([0, 0, rng.randrange(500)])))
        out.append(('random-%d' % index, records))
    return out


def cases(kind='longctx'):
    """(label, records, expected or 'raise') for the target function."""
    out = []
    for label, records in _cases():
        try:
            expected = _reference_reconcile([tuple(r) for r in records])
        except ValueError:
            expected = 'raise'
        out.append((label, records, expected))
    return out


def _fresh_module(work):
    """Import the candidate's legacy module from `work` (and solution.py for the shim check)."""
    work = str(work)
    for name in ('legacy', 'solution'):
        sys.modules.pop(name, None)
    sys.path.insert(0, work)
    try:
        for name in ('legacy', 'solution'):
            path = Path(work) / (name + '.py')
            if not path.exists():
                raise FileNotFoundError('%s.py missing' % name)
            spec = importlib.util.spec_from_file_location(name, path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[name] = module
            spec.loader.exec_module(module)
    finally:
        sys.path.remove(work)
    return sys.modules['legacy'], sys.modules['solution']


def _functions(source):
    """name -> normalised source for every top-level function.

    Slices a pre-split line list instead of ast.get_source_segment, which re-splits the whole file per
    call (1800 functions x 7500 lines made this take ~60 s, and the relay kills a scorer at 30 s).
    """
    tree = ast.parse(source)
    lines = source.splitlines()
    out = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            segment = '\n'.join(lines[node.lineno - 1:node.end_lineno])
            out[node.name] = re.sub(r'\s+', ' ', segment).strip()
    return out


def evaluate_longctx(work):
    work = Path(work)
    checks = []
    legacy_source = (work / 'legacy.py').read_text(encoding='utf-8', errors='replace') if (work / 'legacy.py').exists() else ''
    reference_source = module_source(buggy=False)
    candidate_functions = _functions(legacy_source) if legacy_source else {}
    reference_functions = _functions(reference_source)

    # 1. behaviour of the target function
    try:
        legacy, shim = _fresh_module(work)
        import_ok, shim_ok = True, hasattr(shim, TARGET)
        func = getattr(legacy, TARGET, None)
    except Exception:
        import_ok, shim_ok, func = False, False, None
    for label, records, expected in cases('longctx'):
        passed = False
        if func is not None:
            try:
                actual = func([tuple(r) for r in records])
                passed = expected != 'raise' and actual == expected
            except ValueError:
                passed = expected == 'raise'
            except Exception:
                passed = False
        checks.append({'case': len(checks), 'pass': bool(passed), 'label': 'behaviour/%s' % label})

    # 2. module imports and the shim still re-exports the target
    checks.append({'case': len(checks), 'pass': import_ok, 'label': 'module/imports'})
    checks.append({'case': len(checks), 'pass': shim_ok, 'label': 'module/shim-reexports'})

    # 3. only the target function changed; no function added or removed
    changed = sorted(name for name, body in candidate_functions.items()
                     if name != TARGET and reference_functions.get(name) != body)
    added = sorted(set(candidate_functions) - set(reference_functions))
    removed = sorted(set(reference_functions) - set(candidate_functions))
    checks.append({'case': len(checks), 'pass': not changed, 'label': 'minimal-edit/others-unchanged (%d changed)' % len(changed)})
    checks.append({'case': len(checks), 'pass': not added and not removed,
                   'label': 'minimal-edit/structure (+%d/-%d)' % (len(added), len(removed))})

    # 4. sampled helpers still behave as the reference does
    rng = random.Random(SEED)
    sample = rng.sample(range(N_HELPERS), 10)
    namespace = {}
    try:
        exec(compile(reference_source, 'reference', 'exec'), namespace)
    except Exception:
        namespace = {}
    for index in sample:
        name = helper_name(index)
        ok = False
        if import_ok and name in namespace and hasattr(legacy, name):
            probes = [(7,), ('a1 B2',), ([1, 2, 3, 4, 5, 6],), (12.5,), ('   spaced   ',), (0,), ('', )]
            compared = 0
            ok = True
            for probe in probes:
                try:
                    expected = namespace[name](*probe)
                except Exception:
                    continue
                compared += 1
                try:
                    actual = getattr(legacy, name)(*probe)
                except Exception:
                    ok = False
                    break
                if actual != expected or type(actual) is not type(expected):
                    ok = False
                    break
            ok = ok and compared > 0
        checks.append({'case': len(checks), 'pass': bool(ok), 'label': 'helper/%s' % name})

    return {'passed': sum(c['pass'] for c in checks), 'total': len(checks), 'checks': checks}


def materialize(work, source='starter'):
    work = Path(work)
    work.mkdir(parents=True, exist_ok=True)
    (work / 'README.md').write_text(SPEC, encoding='utf-8')
    (work / 'solution.py').write_text(SHIM, encoding='utf-8')
    (work / 'test_public.py').write_text(PUBLIC, encoding='utf-8')
    (work / 'legacy.py').write_text(module_source(buggy=(source != 'reference')), encoding='utf-8')
    return work


if __name__ == '__main__':
    import json
    result = evaluate_longctx(Path(sys.argv[1]))
    print(json.dumps(result))
    sys.exit(0 if result['passed'] == result['total'] else 1)
