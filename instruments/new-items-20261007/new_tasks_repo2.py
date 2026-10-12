"""repo2: a four-defect multi-file repair, built because the census showed repo splits on one class.

`census_checks.py` found that across five top-group artifacts only three checks split in `repo` - all of
them the UTF-8 byte-length class - so one fixed bug ends the task's discriminative power. This task keeps
that class and adds three independent ones, each with its own labelled checks, so the census can say
*which* class separates models:

  1. byte-length accounting   - a frame header stores characters, not UTF-8 bytes
  2. default-argument aliasing - a shared mutable default leaks between instances
  3. buffer aliasing          - `from_bytes` keeps a reference, so later writes change old frames
  4. swallowed errors         - a malformed varint returns a wrong value instead of raising

Workspace: `codec.py`, `frames.py`, `registry.py` (the buggy modules), `solution.py` (a re-export shim,
because the relay always scores `workspace/solution.py`), `README.md` and `test_public.py` (assertions
that pass with all four bugs present). The evaluator imports the candidate's own modules, so a fix in one
file only counts when the others agree.
"""
import importlib.util
import re
import sys
from pathlib import Path

SPEC = '''Repair a three-module frame codec.

`codec.py` implements a base-128 varint. `encode(value) -> bytes` accepts a non-negative int only.
`decode(buffer, offset=0) -> (value, next_offset)` must raise ValueError when the buffer ends inside a
varint; it must never return a value for malformed input.

`frames.py` implements `FrameLog`, a append-only log of text frames:
- `append(text)` stores `varint(len(text.encode("utf-8"))) + text.encode("utf-8")` and returns self.
  `text` must be a str.
- `read_all() -> list[str]` returns the appended frames in order.
- `to_bytes() -> bytes` returns the serialized log.
- `FrameLog.from_bytes(data)` rebuilds a log from that buffer. It must **copy** the bytes it is given:
  a source buffer mutated afterwards must not change the decoded log.
- `filter(kind)` returns the frames whose prefix before the first `:` equals `kind`.

`registry.py` implements `Registry`:
- `register(kind, handler=None)` records a kind and returns the handler used for it.
- `handlers()` returns the mapping of kind -> handler, built fresh each call.
- A `Registry` must never share state with another `Registry`: registering `"a"` on one must not appear
  on another, and a handler registered on one must not be callable through another.

Rules: fix the four defects (byte-length accounting, the shared default, the buffer reference, and the
swallowed ValueError). Do not change the public names or signatures, do not modify `test_public.py` or
`README.md`, and use only the Python standard library.
'''

SHIM = 'from codec import decode, encode\nfrom frames import FrameLog\nfrom registry import Registry\n'

PUBLIC = '''from codec import encode, decode
from frames import FrameLog
from registry import Registry

assert encode(5) == b"\\x05"
assert decode(b"\\x05") == (5, 1)
log = FrameLog().append("alpha:1").append("beta:2")
assert log.read_all() == ["alpha:1", "beta:2"]
assert FrameLog.from_bytes(log.to_bytes()).read_all() == ["alpha:1", "beta:2"]
assert log.filter("alpha") == ["alpha:1"]
first = Registry()
second = Registry()
first.register("a")
assert second.handlers() == {}
print("public checks passed")
'''

README_NAME = 'README.md'
TEST_NAME = 'test_public.py'

REFERENCE_CODEC = '''"""Base-128 varint plus the frame header helpers."""
KINDS = ("credit", "debit")
def encode(value):
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError("varint.encode takes a non-negative int")
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
            raise ValueError("truncated varint")
        byte = buffer[index]
        index += 1
        value |= (byte & 0x7F) << shift
        if not byte & 0x80:
            return value, index
        shift += 7
        if shift > 63:
            raise ValueError("varint too long")
'''

STARTER_CODEC = '''"""Base-128 varint plus the frame header helpers."""
KINDS = ("credit", "debit")
def encode(value):
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError("varint.encode takes a non-negative int")
    return bytes([value & 0x7F])
def decode(buffer, offset=0):
    try:
        return buffer[offset] & 0x7F, offset + 1
    except Exception:
        return 0, offset + 1
'''

REFERENCE_FRAMES = '''"""Append-only frame log: varint(len(utf8 bytes)) + utf8 bytes."""
import codec
class FrameLog:
    def __init__(self):
        self._data = bytearray()
        self._frames = []
    def append(self, text):
        if not isinstance(text, str):
            raise ValueError("frame text must be a str")
        raw = text.encode("utf-8")
        self._data += codec.encode(len(raw))
        self._data += raw
        self._frames.append(text)
        return self
    def read_all(self):
        return list(self._frames)
    def to_bytes(self):
        return bytes(self._data)
    def filter(self, kind):
        return [frame for frame in self._frames if frame.split(":", 1)[0] == kind]
    @classmethod
    def from_bytes(cls, data):
        data = bytes(data)
        log = cls()
        offset = 0
        while offset < len(data):
            length, offset = codec.decode(data, offset)
            if offset + length > len(data):
                raise ValueError("truncated frame")
            text = data[offset:offset + length].decode("utf-8")
            offset += length
            log._frames.append(text)
            log._data += codec.encode(len(text.encode("utf-8"))) + text.encode("utf-8")
        return log
'''

STARTER_FRAMES = '''"""Append-only frame log: varint(len(utf8 bytes)) + utf8 bytes."""
import codec
class FrameLog:
    def __init__(self):
        self._data = bytearray()
        self._frames = []
    def append(self, text):
        if not isinstance(text, str):
            raise ValueError("frame text must be a str")
        self._data += codec.encode(len(text))
        self._data += text.encode("utf-8", "replace")
        self._frames.append(text)
        return self
    def read_all(self):
        return list(self._frames)
    def to_bytes(self):
        return bytes(self._data)
    def filter(self, kind):
        return [frame for frame in self._frames if frame.startswith(kind)]
    @classmethod
    def from_bytes(cls, data):
        log = cls()
        log._data = data
        offset = 0
        while offset < len(log._data):
            length, offset = codec.decode(log._data, offset)
            text = bytes(log._data[offset:offset + length]).decode("utf-8", "replace")
            offset += length
            log._frames.append(text)
        return log
'''

REFERENCE_REGISTRY = '''"""Kind registry: handlers looked up per kind, state per instance."""
import codec
class Registry:
    def __init__(self):
        self._handlers = {}
    def register(self, kind, handler=None):
        if kind not in codec.KINDS and kind != "custom":
            raise ValueError("unknown kind: %r" % (kind,))
        if handler is None:
            handler = lambda value: value
        self._handlers[kind] = handler
        return handler
    def handlers(self):
        return dict(self._handlers)
'''

STARTER_REGISTRY = '''"""Kind registry: handlers looked up per kind, state per instance."""
import codec
class Registry:
    # BUG (class 2): class-level state, so every instance shares one handler map.
    _handlers = {}
    def __init__(self):
        pass
    def register(self, kind, handler=None, _cache={}):
        if kind not in codec.KINDS and kind != "custom":
            raise ValueError("unknown kind: %r" % (kind,))
        if handler is None:
            handler = _cache.setdefault(kind, lambda value: value)
        Registry._handlers[kind] = handler
        return handler
    def handlers(self):
        return self._handlers
'''

FILES = {'README.md': SPEC, 'solution.py': SHIM, 'test_public.py': PUBLIC,
         'codec.py': STARTER_CODEC, 'frames.py': STARTER_FRAMES, 'registry.py': STARTER_REGISTRY}
REFERENCE = {'codec.py': REFERENCE_CODEC, 'frames.py': REFERENCE_FRAMES, 'registry.py': REFERENCE_REGISTRY}

ASCII = ['a', 'frame one', 'alpha:1', 'x' * 40, 'k:v']
UNICODE = ['caf\u00e9', '\u4e2d\u6587', '\U0001f600', 'caf\u00e9:1', 'x' * 30 + '\u00e9']
BOUNDARIES = [0, 1, 126, 127, 128, 255, 16383, 16384, 2097151]


def cases(kind='repo2'):
    """(label, callable) where the callable takes (codec, frames, registry) and returns True on success."""
    out = []

    def add(label, func):
        out.append((label, func))

    # class 1: byte-length accounting
    for text in ASCII + UNICODE:
        add('class1/roundtrip/%s' % text[:10].replace(' ', '_'),
            lambda c, f, r, text=text: f.FrameLog().append(text).read_all() == [text])
        add('class1/header-bytes/%s' % text[:10].replace(' ', '_'),
            lambda c, f, r, text=text: f.FrameLog().append(text).to_bytes()[:1] == bytes([len(text.encode('utf-8'))]))
    add('class1/reopen-unicode', lambda c, f, r: f.FrameLog.from_bytes(
        f.FrameLog().append('caf\u00e9').append('ok').to_bytes()).read_all() == ['caf\u00e9', 'ok'])
    add('class1/serialized-length', lambda c, f, r: len(f.FrameLog().append('\u4e2d\u6587').to_bytes()) == 1 + 6)
    # class 2: default-argument aliasing between instances
    add('class2/two-registries', lambda c, f, r: _two_registries(r))
    add('class2/handler-not-shared', lambda c, f, r: _handler_not_shared(r))
    add('class2/handlers-copy', lambda c, f, r: _handlers_copy(r))
    add('class2/handler-identity', lambda c, f, r: _handler_identity(r))
    add('class2/register-returns-handler', lambda c, f, r: callable(r.Registry().register('custom')))
    add('class2/unknown-kind-raises', lambda c, f, r: _raises(ValueError, lambda: r.Registry().register('nope')))
    # class 3: buffer aliasing
    add('class3/source-mutation', lambda c, f, r: _source_mutation(f))
    add('class3/source-bytearray', lambda c, f, r: _source_bytearray(f))
    add('class3/reopen-empty', lambda c, f, r: f.FrameLog.from_bytes(b'').read_all() == [])
    add('class3/reopen-many', lambda c, f, r: f.FrameLog.from_bytes(
        f.FrameLog().append('a').append('bb').append('ccc').to_bytes()).read_all() == ['a', 'bb', 'ccc'])
    add('class3/append-after-reopen', lambda c, f, r: _append_after_reopen(f))
    # class 4: swallowed errors
    add('class4/truncated-raises', lambda c, f, r: _raises(ValueError, lambda: c.decode(b'\x80')))
    add('class4/truncated-mid', lambda c, f, r: _raises(ValueError, lambda: c.decode(b'\xff\xff\x80')))
    add('class4/empty-raises', lambda c, f, r: _raises(ValueError, lambda: c.decode(b'')))
    add('class4/offset-past-end', lambda c, f, r: _raises(ValueError, lambda: c.decode(b'\x01', 5)))
    add('class4/reject-negative', lambda c, f, r: _raises(ValueError, lambda: c.encode(-1)))
    add('class4/reject-float', lambda c, f, r: _raises(ValueError, lambda: c.encode(1.5)))
    add('class4/reject-bool', lambda c, f, r: _raises(ValueError, lambda: c.encode(True)))
    # extra behaviour that any fix must not break
    for value in BOUNDARIES:
        add('extra/varint/%d' % value, lambda c, f, r, value=value: c.decode(c.encode(value)) == (value, len(c.encode(value))))
    add('extra/filter-kind', lambda c, f, r: f.FrameLog().append('a:1').append('b:2').append('a:3').filter('a') == ['a:1', 'a:3'])
    add('extra/filter-missing', lambda c, f, r: f.FrameLog().append('a:1').filter('z') == [])
    add('extra/read-all-copy', lambda c, f, r: _read_all_copy(f))
    add('extra/append-returns-self', lambda c, f, r: f.FrameLog().append('a') is not None)
    add('extra/reject-non-str', lambda c, f, r: _raises(ValueError, lambda: f.FrameLog().append(7)))
    add('extra/shim-exports', lambda c, f, r: _shim_exports())
    return out


def _two_registries(registry):
    first, second = registry.Registry(), registry.Registry()
    first.register('custom')
    return second.handlers() == {}


def _handler_not_shared(registry):
    first, second = registry.Registry(), registry.Registry()
    sentinel = lambda value: 'first'
    first.register('custom', sentinel)
    return second.handlers() == {} and first.handlers()['custom'] is sentinel


def _handler_identity(registry):
    first, second = registry.Registry(), registry.Registry()
    return first.register('custom') is not second.register('custom')


def _handlers_copy(registry):
    obj = registry.Registry()
    obj.register('custom')
    snapshot = obj.handlers()
    snapshot['injected'] = lambda value: value
    return 'injected' not in obj.handlers()


def _source_mutation(frames):
    data = bytearray(frames.FrameLog().append('hello').to_bytes())
    log = frames.FrameLog.from_bytes(data)
    before = bytes(log.to_bytes())
    data[0] = 0
    data[1] = ord('X')
    # the decoded log must not follow the caller's buffer
    return bytes(log.to_bytes()) == before and log.read_all() == ['hello']


def _source_bytearray(frames):
    log = frames.FrameLog().append('abc')
    data = bytearray(log.to_bytes())
    reopened = frames.FrameLog.from_bytes(data)
    before = bytes(reopened.to_bytes())
    for index in range(len(data)):
        data[index] = 0
    return reopened.read_all() == ['abc'] and bytes(reopened.to_bytes()) == before


def _append_after_reopen(frames):
    log = frames.FrameLog.from_bytes(frames.FrameLog().append('one').to_bytes())
    log.append('two')
    return log.read_all() == ['one', 'two'] and frames.FrameLog.from_bytes(log.to_bytes()).read_all() == ['one', 'two']


def _read_all_copy(frames):
    log = frames.FrameLog().append('a')
    listed = log.read_all()
    listed.append('injected')
    return log.read_all() == ['a']


def _raises(kind, func):
    try:
        func()
    except kind:
        return True
    except Exception:
        return False
    return False


SHIM_DIR = ['.']


def _shim_exports():
    path = Path(SHIM_DIR[0]) / 'solution.py'
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
    return all(hasattr(module, name) for name in ('encode', 'decode', 'FrameLog', 'Registry'))


def _fresh(work):
    SHIM_DIR[0] = str(work)
    for name in ('codec', 'frames', 'registry', 'solution'):
        sys.modules.pop(name, None)
    sys.path.insert(0, str(work))
    try:
        modules = {}
        for name in ('codec', 'frames', 'registry'):
            path = Path(work) / (name + '.py')
            if not path.exists():
                raise FileNotFoundError('%s.py missing' % name)
            spec = importlib.util.spec_from_file_location(name, path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[name] = module
            spec.loader.exec_module(module)
            modules[name] = module
    finally:
        sys.path.remove(str(work))
    return modules['codec'], modules['frames'], modules['registry']


def evaluate_repo2(work):
    work = Path(work)
    checks = []
    for index, (label, func) in enumerate(cases('repo2')):
        try:
            codec, frames, registry = _fresh(work)
            passed = bool(func(codec, frames, registry))
        except Exception:
            passed = False
        checks.append({'case': index, 'pass': passed, 'label': label})
    return {'passed': sum(c['pass'] for c in checks), 'total': len(checks), 'checks': checks}


def materialize(work, source='starter'):
    work = Path(work)
    work.mkdir(parents=True, exist_ok=True)
    files = dict(FILES)
    if source == 'reference':
        files.update(REFERENCE)
    for name, text in files.items():
        (work / name).write_text(text, encoding='utf-8')
    return work


if __name__ == '__main__':
    import json
    result = evaluate_repo2(Path(sys.argv[1]))
    print(json.dumps(result))
    sys.exit(0 if result['passed'] == result['total'] else 1)
