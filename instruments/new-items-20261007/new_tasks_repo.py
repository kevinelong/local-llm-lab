"""A multi-file repair task: cross-module bug, public tests that pass with it.

Why: after `ledger2` the ledger ranks models, but every task so far is one file with one function.
This task makes the agent carry a wire format across two modules and keeps the public tests green
with the bug present, so the hidden checks are the only signal.

Workspace (four files, all written by the runner):
  README.md      the wire format and the API contract
  varint.py      base-128 varint encode/decode            (starter: buggy)
  store.py       record store built on varint + zigzag    (starter: buggy)
  test_public.py three assertions that pass with the bug present

Hidden checks (~60) cover the varint boundaries, decode at offsets, concatenated buffers, non-ASCII
account names (the length prefix is bytes, not characters), negative cents (zigzag), reopen from
bytes, ordering, truncation errors, and the public API contract. The evaluator imports the
candidate's own two modules, so a fix in one file only counts when the other agrees.
"""
import importlib.util
import json
import shutil
import sys
from pathlib import Path

REFERENCE_VARINT = '''"""Base-128 varint: unsigned integers, 7 bits per byte, MSB set on every byte but the last."""
def encode(value):
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError('varint.encode takes a non-negative int')
    out = bytearray()
    while True:
        byte = value & 0x7F
        value >>= 7
        if value:
            out.append(byte | 0x80)
        else:
            out.append(byte)
            return bytes(out)
def decode(buffer, offset=0):
    value = 0
    shift = 0
    index = offset
    while True:
        if index >= len(buffer):
            raise ValueError('truncated varint')
        byte = buffer[index]
        index += 1
        value |= (byte & 0x7F) << shift
        if not byte & 0x80:
            return value, index
        shift += 7
        if shift > 63:
            raise ValueError('varint too long')
'''

STARTER_VARINT = '''"""Base-128 varint: unsigned integers, 7 bits per byte, MSB set on every byte but the last."""
def encode(value):
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError('varint.encode takes a non-negative int')
    return bytes([value & 0x7F])
def decode(buffer, offset=0):
    if offset >= len(buffer):
        raise ValueError('truncated varint')
    return buffer[offset] & 0x7F, offset + 1
'''

REFERENCE_STORE = '''"""Append-only record store: varint(len(account bytes)) + account bytes + zigzag varint(cents)."""
import varint
def zigzag_encode(value):
    return (value << 1) ^ (value >> 63) if value < 0 else value << 1
def zigzag_decode(value):
    return -((value >> 1) + 1) if value & 1 else value >> 1
class Ledger:
    def __init__(self):
        self._data = bytearray()
        self._records = []
    def append(self, account, cents):
        if not isinstance(account, str) or not account or account != account.strip():
            raise ValueError('invalid account')
        if not isinstance(cents, int) or isinstance(cents, bool):
            raise ValueError('invalid cents')
        raw = account.encode('utf-8')
        self._data += varint.encode(len(raw))
        self._data += raw
        self._data += varint.encode(zigzag_encode(cents))
        self._records.append((account, cents))
        return self
    def read_all(self):
        return list(self._records)
    def to_bytes(self):
        return bytes(self._data)
    @classmethod
    def from_bytes(cls, data):
        data = bytes(data)
        ledger = cls()
        offset = 0
        while offset < len(data):
            length, offset = varint.decode(data, offset)
            if offset + length > len(data):
                raise ValueError('truncated record')
            account = data[offset:offset + length].decode('utf-8')
            offset += length
            value, offset = varint.decode(data, offset)
            ledger._data += varint.encode(len(account.encode('utf-8')))
            ledger._data += account.encode('utf-8')
            ledger._data += varint.encode(zigzag_encode(zigzag_decode(value)))
            ledger._records.append((account, zigzag_decode(value)))
        return ledger
'''

STARTER_STORE = '''"""Append-only record store: varint(len(account bytes)) + account bytes + zigzag varint(cents)."""
import varint
def zigzag_encode(value):
    return value
def zigzag_decode(value):
    return value
class Ledger:
    def __init__(self):
        self._data = bytearray()
        self._records = []
    def append(self, account, cents):
        if not isinstance(account, str) or not account or account != account.strip():
            raise ValueError('invalid account')
        if not isinstance(cents, int) or isinstance(cents, bool):
            raise ValueError('invalid cents')
        self._data += varint.encode(len(account))
        self._data += account.encode('utf-8', 'replace')
        self._data += varint.encode(cents)
        self._records.append((account, cents))
        return self
    def read_all(self):
        return list(self._records)
    def to_bytes(self):
        return bytes(self._data)
    @classmethod
    def from_bytes(cls, data):
        raise NotImplementedError('from_bytes is not implemented yet')
'''

SPEC = '''Repair a two-module record store.

`varint.py` implements a base-128 varint: unsigned integers, 7 bits per byte, the high bit set on
every byte except the last. `encode(value) -> bytes` must reject anything that is not a non-negative
int. `decode(buffer, offset=0) -> (value, next_offset)` must raise ValueError when the buffer ends
inside a varint, and must reject an encoding longer than 10 bytes.

`store.py` implements `Ledger` on top of it. A record is
`varint(len(account_utf_8_bytes)) + account_utf_8_bytes + varint(zigzag(cents))`, where zigzag maps
a signed integer to an unsigned one as `n >= 0 -> 2n` and `n < 0 -> -2n - 1`. `append(account, cents)`
appends and returns self; it must reject an account that is not a non-empty string, not equal to its
stripped form, or a cents that is not an int (bools are not ints). `read_all()` returns the appended
`(account, cents)` tuples in order. `to_bytes()` returns the serialized buffer.
`Ledger.from_bytes(data)` rebuilds a ledger from that buffer and must raise ValueError when the
buffer ends in the middle of a record. Everything must survive a round trip through `to_bytes()`
and `from_bytes()`, including multi-byte varints, non-ASCII account names and negative cents.

Do not change the public names or signatures, do not modify test_public.py or README.md, and use only
the Python standard library. `solution.py` re-exports the public names for the harness
(`encode`, `decode`, `Ledger`); keep that working.
'''

SHIM = 'from varint import encode, decode\nfrom store import Ledger\n'

PUBLIC = '''from varint import encode, decode
from store import Ledger

assert encode(5) == b"\\x05"
assert decode(b"\\x05") == (5, 1)
ledger = Ledger().append("a", 7).append("b", -3)
assert ledger.read_all() == [("a", 7), ("b", -3)]
assert Ledger.from_bytes(ledger.to_bytes()).read_all() == [("a", 7), ("b", -3)]
print("public checks passed")
'''

FILES = {'README.md': SPEC, 'solution.py': SHIM, 'varint.py': STARTER_VARINT, 'store.py': STARTER_STORE,
         'test_public.py': PUBLIC}
REFERENCE = {'varint.py': REFERENCE_VARINT, 'store.py': REFERENCE_STORE}

BOUNDARIES = [0, 1, 126, 127, 128, 255, 16383, 16384, 2097151, 2097152, 2 ** 28 - 1, 2 ** 35 - 1, 2 ** 62 - 1]
ZIGZAG_VALUES = [0, 1, -1, 2, -2, 63, 64, -64, -65, 8191, -8192, 2 ** 31 - 1, -(2 ** 31)]
ACCOUNTS = ['a', 'ab', 'caf\u00e9', '\u4e2d\u6587', '\U0001f600', 'x' * 200, 'account with spaces']


def _fresh(work):
    """Import the candidate's varint and store from `work`, bypassing any cached module."""
    _SHIM_DIR[0] = str(work)
    for name in ('varint', 'store', 'candidate_varint', 'candidate_store'):
        sys.modules.pop(name, None)
    sys.path.insert(0, str(work))
    try:
        spec = importlib.util.spec_from_file_location('varint', Path(work) / 'varint.py')
        varint = importlib.util.module_from_spec(spec)
        sys.modules['varint'] = varint
        spec.loader.exec_module(varint)
        spec = importlib.util.spec_from_file_location('store', Path(work) / 'store.py')
        store = importlib.util.module_from_spec(spec)
        sys.modules['store'] = store
        spec.loader.exec_module(store)
    finally:
        sys.path.remove(str(work))
    return varint, store


def cases(kind='repo'):
    """(label, callable) where the callable takes (varint, store) and returns True on success."""
    out = []

    def add(label, func):
        out.append((label, func))

    for value in BOUNDARIES:
        add('varint/roundtrip/%d' % value,
            lambda v, s, value=value: v.decode(v.encode(value)) == (value, len(v.encode(value))))
        add('varint/length/%d' % value,
            lambda v, s, value=value: len(v.encode(value)) == max(1, (value.bit_length() + 6) // 7))
    for value in BOUNDARIES[:6]:
        add('varint/offset/%d' % value,
            lambda v, s, value=value: v.decode(b'\x00' * 3 + v.encode(value), 3) == (value, 3 + len(v.encode(value))))
    add('varint/concatenated', lambda v, s: [v.decode(v.encode(x) + v.encode(y))[0] for x, y in [(1, 2)]] == [1])
    add('varint/sequential', lambda v, s: _sequential(v))
    add('varint/reject/negative', lambda v, s: _raises(ValueError, lambda: v.encode(-1)))
    add('varint/reject/float', lambda v, s: _raises(ValueError, lambda: v.encode(1.5)))
    add('varint/reject/str', lambda v, s: _raises(ValueError, lambda: v.encode('7')))
    add('varint/reject/bool', lambda v, s: _raises(ValueError, lambda: v.encode(True)))
    add('varint/reject/truncated', lambda v, s: _raises(ValueError, lambda: v.decode(b'\x80')))
    add('varint/reject/truncated-mid', lambda v, s: _raises(ValueError, lambda: v.decode(b'\xff\xff\x80')))
    add('varint/reject/empty', lambda v, s: _raises(ValueError, lambda: v.decode(b'')))
    for value in ZIGZAG_VALUES:
        add('store/cents/%d' % value,
            lambda v, s, value=value: s.Ledger().append('a', value).read_all() == [('a', value)])
    for account in ACCOUNTS:
        add('store/account/%s' % account[:12].replace(' ', '_'),
            lambda v, s, account=account: s.Ledger().append(account, 1).read_all() == [(account, 1)])
    add('store/order', lambda v, s: s.Ledger().append('z', 1).append('a', 2).append('z', 3).read_all()
        == [('z', 1), ('a', 2), ('z', 3)])
    add('store/reopen/empty', lambda v, s: s.Ledger.from_bytes(s.Ledger().to_bytes()).read_all() == [])
    add('store/reopen/multi-byte', lambda v, s: s.Ledger.from_bytes(
        s.Ledger().append('x' * 300, 2 ** 20).append('caf\u00e9', -7).to_bytes()).read_all()
        == [('x' * 300, 2 ** 20), ('caf\u00e9', -7)])
    add('store/reopen/unicode', lambda v, s: s.Ledger.from_bytes(
        s.Ledger().append('\U0001f600', -1).to_bytes()).read_all() == [('\U0001f600', -1)])
    add('store/length-prefix-is-bytes', lambda v, s: s.Ledger().append('caf\u00e9', 1).to_bytes()[0] == 5)
    add('store/reject/empty-account', lambda v, s: _raises(ValueError, lambda: s.Ledger().append('', 1)))
    add('store/reject/space-account', lambda v, s: _raises(ValueError, lambda: s.Ledger().append(' a', 1)))
    add('store/reject/trailing-space', lambda v, s: _raises(ValueError, lambda: s.Ledger().append('a ', 1)))
    add('store/reject/float-cents', lambda v, s: _raises(ValueError, lambda: s.Ledger().append('a', 1.5)))
    add('store/reject/bool-cents', lambda v, s: _raises(ValueError, lambda: s.Ledger().append('a', True)))
    add('store/reject/truncated-tail', lambda v, s: _raises(ValueError, lambda: s.Ledger.from_bytes(
        s.Ledger().append('abc', 5).to_bytes()[:-1])))
    add('store/reject/bad-length', lambda v, s: _raises(ValueError, lambda: s.Ledger.from_bytes(b'\x05ab')))
    add('store/append-returns-self', lambda v, s: s.Ledger().append('a', 1) is not None)
    add('store/read-all-copy', lambda v, s: (lambda l: (l.read_all().append('x'), l.read_all() == [('a', 1)]))
        (s.Ledger().append('a', 1)))
    add('contract/varint-names', lambda v, s: all(hasattr(v, n) for n in ('encode', 'decode')))
    add('contract/store-names', lambda v, s: all(hasattr(s.Ledger, n) for n in ('append', 'read_all', 'to_bytes', 'from_bytes')))
    add('contract/shim', lambda v, s: _shim_works())
    return out


def _shim_works():
    """solution.py must keep re-exporting the public names from the repaired modules."""
    path = Path(_SHIM_DIR[0]) / 'solution.py'
    if not path.exists():
        return False
    spec = importlib.util.spec_from_file_location('solution', path)
    if spec is None:
        return False
    module = importlib.util.module_from_spec(spec)
    try:
        sys.modules['solution'] = module
        spec.loader.exec_module(module)
    except Exception:
        return False
    finally:
        sys.modules.pop('solution', None)
    return all(hasattr(module, n) for n in ('encode', 'decode', 'Ledger'))


_SHIM_DIR = ['.']


def _offsets(v, buffer):
    offsets, offset = [], 0
    while offset < len(buffer):
        _value, offset = v.decode(buffer, offset)
        offsets.append(offset)
    return offsets


def _sequential(v):
    buffer = b''.join(v.encode(x) for x in (0, 127, 128, 300, 2 ** 20))
    seen, offset = [], 0
    while offset < len(buffer):
        value, offset = v.decode(buffer, offset)
        seen.append(value)
    return seen == [0, 127, 128, 300, 2 ** 20]


def _raises(kind, func):
    try:
        func()
    except kind:
        return True
    except Exception:
        return False
    return False


def evaluate_repo(work):
    """Score a workspace directory; returns the same {'passed','total','checks'} shape as a task."""
    checks = []
    for index, (label, func) in enumerate(cases('repo')):
        try:
            varint, store = _fresh(work)
            passed = bool(func(varint, store))
        except Exception:
            passed = False
        checks.append({'case': index, 'pass': passed, 'label': label})
    # Labels ride along in the checks (the relay reads passed/total; extra keys are ignored).
    return {'passed': sum(c['pass'] for c in checks), 'total': len(checks), 'checks': checks}


def materialize(work, source):
    """Write the workspace for this task from `source` ('starter' or 'reference')."""
    work = Path(work)
    work.mkdir(parents=True, exist_ok=True)
    files = dict(FILES)
    if source == 'reference':
        files.update(REFERENCE)
    for name, text in files.items():
        (work / name).write_text(text, encoding='utf-8')
    return work


if __name__ == '__main__':
    target = Path(sys.argv[1])
    result = evaluate_repo(target)
    print(json.dumps(result))
    sys.exit(0 if result['passed'] == result['total'] else 1)
