"""Five repair tasks. Keep this file OUTSIDE candidate workspaces.

Only TASKS[kind]'s spec/code/public belong in a candidate workspace. This
finite evaluator is for reviewed lab code, not a sandbox. Parent runners must
enforce an evaluation timeout. Historical graph/interval fixtures are reused.
"""
import copy
import csv
import importlib.util
import inspect
import io
import json
from pathlib import Path
import random
import sys

import night_tasks_20260916 as old

TASKS = copy.deepcopy(old.TASKS)
TASKS.update({
    'ledger': {
        'spec': 'Repair solution.py: reconcile(text) reads CSV from a string and returns sorted (account, balance, transaction_count) tuples, ordered by account. Header must be exactly account,kind,cents in that order. Each subsequent CSV record must have exactly three fields. account is a nonempty string with no leading/trailing whitespace; internal whitespace and commas are allowed. kind is exactly credit or debit. cents is one or more ASCII digits, with optional leading zeros, representing a nonnegative integer. credit adds cents, debit subtracts it; negative balances are allowed. Include accounts with zero balance and count zero-value transactions. Empty text, malformed CSV quoting under csv.reader(strict=True), wrong header, blank records, wrong field counts, or invalid fields raise ValueError. A header alone returns []. Do not strip or reinterpret field contents. Input is always a string. Python 3.11, standard library only.',
        'code': 'import csv, io\ndef reconcile(text):\n    balances = {}\n    for row in csv.DictReader(io.StringIO(text)):\n        balances[row["account"]] = int(row["cents"])\n    return sorted((a, b, 1) for a, b in balances.items())\n',
        'public': 'from solution import reconcile\nassert reconcile("account,kind,cents\\na,credit,10\\na,debit,4\\n") == [("a",6,2)]\nassert reconcile("account,kind,cents\\n") == []\ntry:\n    reconcile("account,kind,cents\\na,fee,3\\n")\nexcept ValueError:\n    pass\nelse:\n    raise AssertionError("invalid kind accepted")\nprint("public checks passed")\n',
    },
    'events': {
        'spec': 'Repair solution.py: replay(events) processes a list of dictionaries in input order. Every dictionary has exactly keys account, action, amount. account is a nonempty string with no leading/trailing whitespace. action is open, deposit, withdraw, or close. amount must be an int excluding bool. open and close require amount == 0; deposit and withdraw require amount > 0. An account must be opened exactly once before any other action; open creates balance zero. Withdrawal cannot exceed its balance. close requires zero balance; any action after close, including open, is invalid. Return tuples (account, balance, status), sorted by account; status is open or closed. Retain closed accounts. Empty input returns []. Invalid record shape, fields, or transition raises ValueError. Do not mutate input even when raising. The outer input is always a list. Python 3.11, standard library only.',
        'code': 'def replay(events):\n    accounts = {}\n    for event in events:\n        a = event["account"]\n        accounts.setdefault(a, 0)\n        if event["action"] == "deposit":\n            accounts[a] += event["amount"]\n        elif event["action"] == "withdraw":\n            accounts[a] -= event["amount"]\n    return [(a,b,"open") for a,b in sorted(accounts.items())]\n',
        'public': 'from solution import replay\ndef e(a,k,n=0): return dict(account=a,action=k,amount=n)\nassert replay([e("a","open"),e("a","deposit",5),e("a","withdraw",5),e("a","close")]) == [("a",0,"closed")]\ntry:\n    replay([e("a","withdraw",1)])\nexcept ValueError:\n    pass\nelse:\n    raise AssertionError("unopened account accepted")\nprint("public checks passed")\n',
    },
    'paths': {
        'spec': 'Repair solution.py: normalize(entries) accepts a list of relative POSIX file-path strings and returns unique normalized paths sorted lexicographically. A path must be a nonempty string, cannot start with /, and cannot contain backslash or a NUL character. Split on /; ignore empty and . components; .. pops one preceding component and is invalid if no component is available at that point. Reject paths that normalize to empty. Other components are literal, case-sensitive names, including spaces and colons; no filesystem access or URL decoding. Duplicate normalized paths collapse. Reject a manifest if one normalized file path is an ancestor of another (for example a and a/b); a and ab do not conflict. All invalid paths, invalid element types, and file/descendant conflicts raise ValueError. The outer input is always a list. Do not mutate it, including on errors. Empty input returns []. Python 3.11, standard library only.',
        'code': 'def normalize(entries):\n    entries.sort()\n    return sorted(set(p.replace("./", "").strip("/") for p in entries))\n',
        'public': 'from solution import normalize\nassert normalize(["a/../b", "b", "./c//d"]) == ["b", "c/d"]\nfor paths in [["../a"], ["a", "a/b"]]:\n    try:\n        normalize(paths)\n    except ValueError:\n        pass\n    else:\n        raise AssertionError("invalid manifest accepted")\nprint("public checks passed")\n',
    },
})


def reference_ledger(text):
    try:
        rows = list(csv.reader(io.StringIO(text), strict=True))
    except csv.Error as exc:
        raise ValueError('csv') from exc
    if not rows or rows[0] != ['account', 'kind', 'cents']:
        raise ValueError('header')
    transactions = []
    for row in rows[1:]:
        if len(row) != 3:
            raise ValueError('columns')
        name, kind, cents = row
        if not name or name != name.strip() or kind not in ('credit', 'debit'):
            raise ValueError('field')
        if not cents or any(c not in '0123456789' for c in cents):
            raise ValueError('cents')
        transactions.append((name, int(cents) * (1 if kind == 'credit' else -1)))
    return [(name, sum(v for a, v in transactions if a == name),
             sum(a == name for a, _ in transactions))
            for name in sorted({a for a, _ in transactions})]


def reference_events(events):
    # Group histories after schema validation, then check each prefix's balance.
    histories = {}
    for event in events:
        if not isinstance(event, dict) or set(event) != {'account', 'action', 'amount'}:
            raise ValueError('record')
        a, k, n = event['account'], event['action'], event['amount']
        if not isinstance(a, str) or not a or a.strip() != a:
            raise ValueError('account')
        if k not in ('open', 'deposit', 'withdraw', 'close') or type(n) is not int:
            raise ValueError('operation')
        if (k in ('open', 'close') and n != 0) or (k in ('deposit', 'withdraw') and n <= 0):
            raise ValueError('amount')
        histories.setdefault(a, []).append((k, n))
    result = []
    for a, history in sorted(histories.items()):
        actions = [k for k, _ in history]
        if actions[0] != 'open' or actions.count('open') != 1:
            raise ValueError('open')
        if 'close' in actions and (actions[-1] != 'close' or actions.count('close') != 1):
            raise ValueError('closed')
        deltas = [n if k == 'deposit' else -n if k == 'withdraw' else 0 for k, n in history]
        balances = [sum(deltas[:i]) for i in range(1, len(deltas) + 1)]
        if min(balances) < 0 or (actions[-1] == 'close' and balances[-1] != 0):
            raise ValueError('balance')
        result.append((a, balances[-1], 'closed' if actions[-1] == 'close' else 'open'))
    return result


def reference_paths(entries):
    paths = set()
    for path in entries:
        if not isinstance(path, str) or not path or path.startswith('/') or '\\' in path or '\0' in path:
            raise ValueError('path')
        parts = []
        for part in path.split('/'):
            if part in ('', '.'):
                continue
            if part == '..':
                if not parts:
                    raise ValueError('escape')
                parts.pop()
            else:
                parts.append(part)
        if not parts:
            raise ValueError('empty')
        paths.add('/'.join(parts))
    if any(b.startswith(a + '/') for a in paths for b in paths if a != b):
        raise ValueError('ancestor')
    return sorted(paths)


REFERENCE_CODE = {
    'graph': inspect.getsource(old.reference_graph).replace('reference_graph', 'plan', 1),
    'intervals': inspect.getsource(old.reference_intervals).replace('reference_intervals', 'merge', 1),
    'ledger': '''import csv, io
def reconcile(text):
    try:
        reader = csv.DictReader(io.StringIO(text), strict=True)
        if reader.fieldnames != ['account', 'kind', 'cents']:
            raise ValueError('header')
        # DictReader skips blank records, so verify the raw record shapes too.
        if any(len(row) != 3 for row in list(csv.reader(io.StringIO(text), strict=True))[1:]):
            raise ValueError('columns')
        totals = {}
        for row in reader:
            a, k, s = row['account'], row['kind'], row['cents']
            if not a or a.strip() != a or k not in ('credit', 'debit'):
                raise ValueError('field')
            if not s or not s.isascii() or not s.isdecimal():
                raise ValueError('cents')
            balance, count = totals.get(a, (0, 0))
            totals[a] = (balance + (int(s) if k == 'credit' else -int(s)), count + 1)
    except csv.Error as exc:
        raise ValueError('csv') from exc
    return [(a, *totals[a]) for a in sorted(totals)]
''',
    'events': '''def replay(events):
    states = {}
    for e in events:
        if not isinstance(e, dict) or set(e) != {'account','action','amount'}:
            raise ValueError('record')
        a, k, n = e['account'], e['action'], e['amount']
        if not isinstance(a, str) or not a or a.strip() != a or type(n) is not int:
            raise ValueError('field')
        if k not in ('open','close','deposit','withdraw'):
            raise ValueError('action')
        if k in ('open','close'):
            if n != 0: raise ValueError('amount')
        elif n <= 0: raise ValueError('amount')
        if k == 'open':
            if a in states: raise ValueError('duplicate')
            states[a] = (0, 'open')
            continue
        if a not in states or states[a][1] == 'closed':
            raise ValueError('inactive')
        balance = states[a][0]
        if k == 'deposit': balance += n
        elif k == 'withdraw':
            if n > balance: raise ValueError('overdraft')
            balance -= n
        elif balance != 0: raise ValueError('nonzero')
        states[a] = (balance, 'closed' if k == 'close' else 'open')
    return [(a, *states[a]) for a in sorted(states)]
''',
    'paths': '''import posixpath
def normalize(entries):
    result = set()
    for path in entries:
        if not isinstance(path, str) or not path or path.startswith('/') or '\\\\' in path or '\\0' in path:
            raise ValueError('path')
        depth = 0
        for component in path.split('/'):
            if component == '..': depth -= 1
            elif component not in ('', '.'): depth += 1
            if depth < 0: raise ValueError('escape')
        normalized = posixpath.normpath(path)
        if normalized == '.': raise ValueError('empty')
        result.add(normalized)
    for path in result:
        parts = path.split('/')
        if any('/'.join(parts[:i]) in result for i in range(1, len(parts))):
            raise ValueError('ancestor')
    return sorted(result)
''',
}


def _event(account, action, amount=0):
    return dict(account=account, action=action, amount=amount)


def _csv(rows):
    out = io.StringIO()
    csv.writer(out, lineterminator='\n').writerows([['account', 'kind', 'cents']] + rows)
    return out.getvalue()


def cases(kind):
    if kind in old.TASKS:
        return old.cases(kind)
    rng = random.Random(20260922)
    if kind == 'ledger':
        values = ['', 'wrong,kind,cents\n', _csv([]), _csv([['a', 'credit', '0'], ['a', 'debit', '0']]),
                  _csv([['z', 'debit', '0007'], ['a,b', 'credit', '3'], ['a,b', 'credit', '4']]),
                  'account,kind,cents\n"unclosed,credit,2', 'account,kind,cents\n\n',
                  'account,kind,cents\n"a"x,credit,3\n']
        for row in [['a', 'credit'], ['a', 'credit', '2', 'extra'], ['', 'credit', '1'],
                    [' a', 'credit', '1'], ['a ', 'credit', '1'], ['a', 'fee', '1'],
                    ['a', 'credit', '-1'], ['a', 'credit', '+1'], ['a', 'credit', '1.0'],
                    ['a', 'credit', ''], ['a', 'credit', ' 1'], ['a', 'credit', '\u0661']]:
            values.append(_csv([['ok', 'credit', '4'], row]))
        for _ in range(50):
            rows = [[rng.choice(['a', 'z', 'two words', 'quoted,"name']),
                     rng.choice(['credit', 'debit']), str(rng.randrange(10000))]
                    for _ in range(rng.randrange(20))]
            values.append(_csv(rows))
        return values
    if kind == 'events':
        e = _event
        values = [[], [e('a', 'open')], [e('a', 'open'), e('a', 'close')],
                  [e('a', 'deposit', 1)], [e('a', 'open'), e('a', 'open')],
                  [e('a', 'open'), e('a', 'withdraw', 1)],
                  [e('a', 'open'), e('a', 'deposit', 1), e('a', 'close')],
                  [e('a', 'open'), e('a', 'deposit', True)],
                  [e('a', 'open', False)],
                  [e('a', 'open'), e('a', 'close'), e('a', 'open')],
                  [e('a', 'open'), e('a', 'close'), e('a', 'deposit', 1)]]
        bad = [None, [], {}, {'account': 'a', 'action': 'open'},
               dict(e('a', 'open'), extra=1), e('', 'open'), e(' a', 'open'),
               e(3, 'open'), e('a', 'unknown'), e('a', 'open', True),
               e('a', 'open', 1), e('a', 'deposit', 0), e('a', 'withdraw', -1),
               e('a', 'deposit', 1.5), e('a', 'close', 1)]
        values.extend([[e('z', 'open'), item] for item in bad])
        for _ in range(50):
            events = [e(a, 'open') for a in ['z', 'a', 'middle']]
            balances = dict.fromkeys(['z', 'a', 'middle'], 0)
            for _ in range(15):
                a = rng.choice(list(balances))
                if balances[a] and rng.random() < .5:
                    n = rng.randint(1, balances[a]); balances[a] -= n
                    events.append(e(a, 'withdraw', n))
                else:
                    n = rng.randint(1, 50); balances[a] += n
                    events.append(e(a, 'deposit', n))
            a = rng.choice(list(balances))
            if balances[a]: events.append(e(a, 'withdraw', balances[a]))
            events.append(e(a, 'close'))
            values.append(events)
        return values
    if kind == 'paths':
        values = [[], ['b', 'a', 'b'], ['./a//b/', 'a/b'], ['a/../b'], ['a', 'ab'],
                  ['A', 'a'], ['name with spaces', 'C:literal'], ['a/..hidden'],
                  ['a/b', 'a'], ['a/../x', 'x/y'], ['a/b/c', 'a/b'], ['a/..'],
                  ['.'], [''], ['/a'], ['../a'], ['a/../../b'], ['a\\b'], ['a\0b'],
                  [None], [3], ['z', '../x'], ['a/../../x/../b'],
                  ['a', 'a-', 'a/b'], ['a', 'a.b', 'a/b/c']]
        for _ in range(50):
            items = []
            for _ in range(rng.randrange(15)):
                base = rng.choice(['a', 'b', 'c'])
                leaf = str(rng.randrange(8))
                items.append(rng.choice([f'{base}/{leaf}', f'./{base}//{leaf}',
                                         f'tmp/../{base}/{leaf}', f'{base}/x/../{leaf}']))
            values.append(items)
        return values
    raise ValueError('unknown task: ' + str(kind))


FUNCTIONS = {'graph': 'plan', 'intervals': 'merge', 'ledger': 'reconcile', 'events': 'replay', 'paths': 'normalize'}
REFERENCES = {'graph': old.reference_graph, 'intervals': old.reference_intervals,
              'ledger': reference_ledger, 'events': reference_events, 'paths': reference_paths}


def same_value(left, right):
    """Compare structure and types, so bool/float cannot masquerade as int."""
    if type(left) is not type(right):
        return False
    if isinstance(left, (list, tuple)):
        return len(left) == len(right) and all(same_value(a, b) for a, b in zip(left, right))
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(same_value(left[k], right[k]) for k in left)
    return left == right


def evaluate(kind, path):
    values = cases(kind)
    spec = importlib.util.spec_from_file_location('candidate', path)
    module = importlib.util.module_from_spec(spec)
    # Standard decorators such as dataclass resolve annotations via sys.modules.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    func = getattr(module, FUNCTIONS[kind])
    checks = []
    for index, value in enumerate(values):
        original = copy.deepcopy(value)
        try:
            expected = REFERENCES[kind](copy.deepcopy(value)); invalid = False
        except ValueError:
            expected = None; invalid = True
        try:
            actual = func(value)
            passed = not invalid and same_value(actual, expected) and same_value(value, original)
            # Graph and paths return strings; the other tasks return tuples.
            passed = passed and type(actual) is list
            if kind in ('intervals', 'ledger', 'events') and passed:
                passed = all(type(item) is tuple for item in actual)
        except ValueError:
            passed = invalid and same_value(value, original)
        except Exception:
            passed = False
        checks.append({'case': index, 'pass': bool(passed)})
    return {'passed': sum(c['pass'] for c in checks), 'total': len(checks), 'checks': checks}


if __name__ == '__main__':
    try:
        result = evaluate(sys.argv[1], Path(sys.argv[2]))
    except Exception as exc:
        result = {'passed': 0, 'total': len(cases(sys.argv[1])), 'error': str(exc)}
    print(json.dumps(result))
    sys.exit(0 if result['passed'] == result['total'] else 1)
