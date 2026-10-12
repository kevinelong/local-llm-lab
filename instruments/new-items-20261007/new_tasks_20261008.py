"""New task kinds for 2026-10-08: a finer ledger battery.

Why: the coding screen has saturated. `events` is 76/76 and `paths` is 75/75 at every top-group
configuration, and the frozen ledger's 70 checks concentrate nearly all of their discrimination in
five of them (case 19 = ASCII-only digits fails 14 of 23 top-group samples; 7, 5, 0 and 6 follow).
Ranking the leaders therefore needs *more* of what already discriminates, not more repeats.

`ledger2` keeps the exact `reconcile` specification, the frozen reference implementation, the frozen
70 cases and their indices, and adds 156 checks: Unicode digits that `isdigit()` and `int()` accept,
Unicode and zero-width whitespace in the account, sign/float/fullwidth cents shapes, stricter CSV
quoting shapes, header variants (BOM, trailing space, case) and multi-byte names. Cases 0-69 are
byte-identical to the frozen battery, so a frozen result can be compared check by check.

`extra_cases()` is the single source of truth for the extras, each carrying its trap label.
"""
import copy
import importlib.util
import random
import sys
from pathlib import Path

BASE_SOURCE = Path(r'C:\Users\kevin\ai_bench\completion-20260923-v1\source\staged_tasks_20260922.py')
if str(BASE_SOURCE.parent) not in sys.path:
    sys.path.insert(0, str(BASE_SOURCE.parent))


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


base = _load(BASE_SOURCE, 'frozen_tasks_20260922')

SPEC = base.TASKS['ledger']['spec']
STARTER = base.TASKS['ledger']['code']
PUBLIC = base.TASKS['ledger']['public']

TASKS = {'ledger2': {'spec': SPEC, 'code': STARTER, 'public': PUBLIC}}

# str.isdigit() is True for every one of these and int() accepts most of them, but the
# specification allows only ASCII 0-9.
UNICODE_DIGITS = {
    'arabic-indic-one': '\u0661',
    'extended-arabic-indic-one': '\u06f1',
    'devanagari-one': '\u0967',
    'fullwidth-one': '\uff11',
    'superscript-two': '\u00b2',
    'subscript-zero': '\u2080',
    'circled-one': '\u2460',
}

# NBSP, em space and ideographic space are whitespace for str.strip(); the zero-width characters
# and the BOM are not, so they survive a strip-based check.
UNICODE_SPACES = {
    'nbsp': '\u00a0',
    'em-space': '\u2003',
    'ideographic-space': '\u3000',
    'zero-width-space': '\u200b',
    'zero-width-joiner': '\u200d',
    'bom': '\ufeff',
}

HEADER = 'account,kind,cents'


def _csv(rows):
    import csv
    import io
    out = io.StringIO()
    csv.writer(out, lineterminator='\n').writerows([['account', 'kind', 'cents']] + rows)
    return out.getvalue()


def extra_cases():
    """(label, value) for every extra trap, in a fixed order."""
    out = []

    def add(label, value):
        out.append((label, value))

    for name, digit in UNICODE_DIGITS.items():
        add('unicode-digit/%s/plain' % name, _csv([['a', 'credit', digit]]))
        add('unicode-digit/%s/leading-zero' % name, _csv([['a', 'credit', '0' + digit]]))
        add('unicode-digit/%s/embedded' % name, _csv([['a', 'credit', '1' + digit + '2']]))
    for name, space in UNICODE_SPACES.items():
        add('unicode-space/%s/trailing' % name, _csv([['a' + space, 'credit', '1']]))
        add('unicode-space/%s/leading' % name, _csv([[space + 'a', 'credit', '1']]))
        add('unicode-space/%s/both' % name, _csv([[space + 'a' + space, 'credit', '1']]))
        add('unicode-space/%s/interior' % name, _csv([['a' + space + 'b', 'credit', '1']]))
    for bad in ['+1', '-1', '1.0', '1e3', '0x1', '1_0', ' 1', '1 ', '\t1', '1\t', '1\n',
                '', ' ', '\t', '01x', 'x01', '1,000', '\u0661\u0662']:
        add('cents-shape/%s' % repr(bad), _csv([['a', 'credit', bad]]))
    csv_shapes = [
        ('unclosed-quote', 'account,kind,cents\n"unclosed,credit,2'),
        ('quote-then-char', 'account,kind,cents\n"a"x,credit,3\n'),
        ('quote-space-comma', 'account,kind,cents\n"a" ,credit,3\n'),
        ('space-field', 'account,kind,cents\n ,credit,3\n'),
        ('quote-inside-unquoted', 'account,kind,cents\na"b,credit,3\n'),
        ('newline-inside-quotes', 'account,kind,cents\n"a\nb",credit,3\n'),
        ('crlf-terminators', 'account,kind,cents\r\na,credit,3\r\n'),
        ('lone-cr-terminators', 'account,kind,cents\ra,credit,3\r'),
        ('crlf-then-lf', 'account,kind,cents\r\na,credit,3\n'),
        ('trailing-blank-line', 'account,kind,cents\na,credit,3\n\n'),
        ('whitespace-only-line', 'account,kind,cents\na,credit,3\n   \n'),
        ('comment-line', 'account,kind,cents\na,credit,3\n# comment\n'),
        ('trailing-comma', 'account,kind,cents\na,credit,3,\n'),
        ('leading-empty-field', 'account,kind,cents\n,a,credit,3\n'),
        ('leading-zeros', 'account,kind,cents\na,credit,0003\n'),
        ('embedded-nul', 'account,kind,cents\na,credit,3\u0000\n'),
        ('quoted-comma', 'account,kind,cents\n"a,b",credit,3\n'),
        ('doubled-quote', 'account,kind,cents\n"a""b",credit,3\n'),
        ('same-account-credit-debit', 'account,kind,cents\na,credit,3\na,debit,3\n'),
        ('three-zero-rows', 'account,kind,cents\nz,debit,0\nz,credit,0\nz,debit,0\n'),
    ]
    for label, value in csv_shapes:
        add('csv-shape/%s' % label, value)
    header_shapes = [
        ('bom-prefix', '\ufeff' + HEADER + '\na,credit,3\n'),
        ('header-trailing-space', HEADER + ' \na,credit,3\n'),
        ('header-case', 'Account,kind,cents\na,credit,3\n'),
        ('header-crlf-only', 'account,kind,cents\r\n'),
        ('header-alone', HEADER),
        ('header-newline', HEADER + '\n'),
        ('empty-text', ''),
        ('newline-only', '\n'),
        ('space-newline', ' \n'),
        ('header-extra-lines', 'account,kind,cents\nextra\n\n'),
    ]
    for label, value in header_shapes:
        add('header/%s' % label, value)
    name_shapes = [
        ('accented', _csv([['caf\u00e9', 'credit', '5'], ['caf\u00e9', 'debit', '2']])),
        ('combining-accent', _csv([['\u00e9\u0301', 'credit', '1']])),
        ('emoji', _csv([['\U0001f600', 'credit', '7']])),
        ('zero-width-inside', _csv([['a\u200bb', 'credit', '7']])),
        ('tab-inside', _csv([['tab\there', 'credit', '7']])),
        ('quote-inside', _csv([['quote"here', 'credit', '7']])),
        ('comma-inside', _csv([['comma,here', 'credit', '7']])),
        ('300-chars', _csv([['a' * 300, 'credit', '7']])),
        ('name-is-cents', _csv([['cents', 'credit', '7']])),
    ]
    for label, value in name_shapes:
        add('name/%s' % label, value)
    accumulation = [
        ('huge-credit', _csv([['a', 'credit', '1'], ['a', 'credit', '999999999999999999999999']])),
        ('huge-debit-then-one', _csv([['a', 'debit', '999999999999999999999999'], ['a', 'credit', '1']])),
        ('forty-zeros-then-one', _csv([['a', 'credit', '0' * 40 + '1']])),
        ('three-accounts', _csv([['a', 'credit', '1'], ['b', 'debit', '1'], ['c', 'credit', '1']])),
    ]
    for label, value in accumulation:
        add('accumulation/%s' % label, value)
    return out


def extra_values():
    return [value for _label, value in extra_cases()]


def cases(kind):
    if kind != 'ledger2':
        return base.cases(kind)
    rng = random.Random(20261008)
    values = list(base.cases('ledger'))
    values.extend(extra_values())
    for _ in range(50):
        rows = [[rng.choice(['a', 'z', 'two words', 'quoted,"name', 'caf\u00e9', '\U0001f600']),
                 rng.choice(['credit', 'debit']), str(rng.randrange(100000))]
                for _ in range(rng.randrange(25))]
        values.append(_csv(rows))
    return values


def evaluate(kind, path):
    if kind != 'ledger2':
        return base.evaluate(kind, path)
    values = cases(kind)
    spec = importlib.util.spec_from_file_location('candidate', path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    func = getattr(module, 'reconcile')
    checks = []
    for index, value in enumerate(values):
        original = copy.deepcopy(value)
        try:
            expected = base.reference_ledger(copy.deepcopy(value))
            invalid = False
        except ValueError:
            expected, invalid = None, True
        try:
            actual = func(value)
            passed = (not invalid and base.same_value(actual, expected)
                      and base.same_value(value, original))
            passed = passed and type(actual) is list
            if passed:
                passed = all(type(item) is tuple for item in actual)
        except ValueError:
            passed = invalid and base.same_value(value, original)
        except Exception:
            passed = False
        checks.append({'case': index, 'pass': bool(passed)})
    return {'passed': sum(c['pass'] for c in checks), 'total': len(checks), 'checks': checks}


def case_labels():
    """Index -> label for every case, frozen ones included."""
    labels = {i: 'frozen/%d' % i for i in range(len(base.cases('ledger')))}
    offset = len(labels)
    for i, (label, _value) in enumerate(extra_cases()):
        labels[offset + i] = label
    for i in range(len(labels), len(cases('ledger2'))):
        labels[i] = 'random-valid/%d' % (i - offset - len(extra_cases()))
    return labels


if __name__ == '__main__':
    import json
    result = evaluate('ledger2', Path(sys.argv[1]))
    print(json.dumps(result))
    sys.exit(0 if result['passed'] == result['total'] else 1)
