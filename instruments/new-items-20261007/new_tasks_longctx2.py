"""longctx2: a long-context task whose defects are enumerable but independent, so partial fixes split.

`longctx` (one wrong function in 1,800 helpers) has **zero** live checks among competent artifacts
(`census_checks.py`): everyone who can grep finds the one bug, fixes it, and the task stops measuring.
This task keeps the long workspace but plants **nine** frame-length computations across it, each written
differently (`len(text)`, `len(payload)`, `len(s)`, `sum(1 for _ in value)`, ...), all of which agree on
ASCII and therefore pass the public tests. The spec (UTF-8 byte lengths) makes each site a separate
defect, and each site carries its own checks - so a model that finds five of the nine splits the checks
instead of passing or failing as a block.

Workspace: `legacy.py` (~100 KB of helpers plus the frame API), `README.md`, `test_public.py` and a
`solution.py` shim (the relay always scores `workspace/solution.py`).
"""
import ast
import importlib.util
import re
import sys
from pathlib import Path

SEED = 20261008
N_HELPERS = 1200

SPEC = '''Repair a long legacy module: every frame length must be the UTF-8 **byte** length.

`legacy.py` is a production module of ~1200 helpers plus a small frame API used by several services.
The wire format is:

    frame := varint(len(payload_bytes)) || payload_bytes

so the length prefix counts **bytes of the UTF-8 encoding**, not characters. The helpers and the public
tests were written with ASCII payloads, where both agree, so the bug only shows on non-ASCII text.

The frame API in the module:
- `frame_length_NN(text)` for NN in 00..08: return the length to be written for `text`.
- `encode_frame(text) -> bytes`: varint(byte length) || text.encode("utf-8").
- `decode_frame(data) -> str`: read the varint, then that many bytes, and decode them.

Every one of the nine `frame_length_NN` functions must return the UTF-8 byte length of its argument, and
`encode_frame`/`decode_frame` must round-trip any str. Fix all of them: they are written in different
styles, and a fix to one does not fix the others.

Rules: do not rename anything, do not change any helper other than the nine `frame_length_NN` functions,
`encode_frame` and `decode_frame`, and do not modify `README.md` or `test_public.py`.
'''

PUBLIC = '''from legacy import frame_length_00, frame_length_08, encode_frame, decode_frame

assert frame_length_00("abc") == 3
assert frame_length_08("abcd") == 4
assert encode_frame("abc") == b"\\x03abc"
assert decode_frame(encode_frame("hello")) == "hello"
print("public checks passed")
'''

SHIM = 'from legacy import decode_frame, encode_frame\n'

_HEADER = '"""legacy.py - frame helpers for the ingest services. Generated fixture; do not reformat."""\n' \
          'import codecs\nimport json\nimport math\nimport string\n\n\n'

VARINT_CORRECT = '''def _varint(value):
    """Base-128 varint, 7 bits per byte, high bit set except on the last byte."""
    out = bytearray()
    while True:
        byte = value & 0x7F
        value >>= 7
        if value:
            out.append(byte | 0x80)
        else:
            out.append(byte)
            return bytes(out)


def _read_varint(data, offset=0):
    value = 0
    shift = 0
    while True:
        if offset >= len(data):
            raise ValueError("truncated varint")
        byte = data[offset]
        offset += 1
        value |= (byte & 0x7F) << shift
        if not byte & 0x80:
            return value, offset
        shift += 7
        if shift > 63:
            raise ValueError("varint too long")


'''

# nine sites, deliberately different in style so one grep does not find them all.
# (expression, argument name, why the style hides it)
SITES = [
    ('len(text)', 'text', 'plain'),
    ('len(payload)', 'payload', 'different argument name'),
    ('len(s)', 's', 'single-letter argument'),
    ('len(value)', 'value', 'generic name'),
    ('sum(1 for _ in value)', 'value', 'generator expression counts characters'),
    ('len(list(frame))', 'frame', 'argument materialised first'),
    ('len(str(text))', 'text', 'a str() call hides the argument'),
    ('len(frame or "")', 'frame', 'an `or` fallback is present'),
    ('len(text.strip()) + len(text) - len(text.strip())', 'text', 'arithmetic hides the count'),
]


def _site_source(index):
    """One buggy frame_length_NN, in its own style; all agree with the byte length on ASCII."""
    expression, argument, _why = SITES[index]
    return ('def frame_length_%02d(%s):\n'
            '    """Length to write for %s before encoding (see README)."""\n'
            '    return %s\n' % (index, argument, argument, expression))


def _helper_source(index):
    style = index % 6
    name = 'helper_%04d' % index
    if style == 0:
        return 'def %s(value):\n    return value * %d + %d\n' % (name, index % 13 + 1, index % 7)
    if style == 1:
        return ('def %s(text):\n    return sum(1 for ch in str(text) if ch in string.%s)\n'
                % (name, ('ascii_letters', 'digits', 'ascii_lowercase', 'punctuation', 'whitespace', 'ascii_uppercase')[index % 6]))
    if style == 2:
        return 'def %s(items):\n    return [v for v in items if isinstance(v, int) and v %% %d == 0]\n' % (name, index % 9 + 2)
    if style == 3:
        return 'def %s(text):\n    return re.sub(r"\\\\s+", " ", str(text).strip())[:%d]\n' % (name, index % 30 + 6)
    if style == 4:
        return 'def %s(n):\n    step = %d\n    return ((int(n) + step - 1) // step) * step\n' % (name, index % 11 + 2)
    return 'def %s(record):\n    return json.dumps(record, sort_keys=True, separators=(",", ":"))[:%d]\n' % (name, index % 50 + 12)


API_BUGGY = '''def encode_frame(text):
    """Write varint(length) followed by the UTF-8 payload."""
    if not isinstance(text, str):
        raise ValueError("frame payload must be a str")
    raw = text.encode("utf-8")
    return _varint(frame_length_00(text)) + raw


def decode_frame(data):
    """Read a varint length and the payload it describes."""
    length, offset = _read_varint(bytes(data), 0)
    payload = bytes(data)[offset:offset + length]
    if len(payload) != length:
        raise ValueError("truncated frame")
    return payload.decode("utf-8")
'''

API_FIXED = '''def encode_frame(text):
    """Write varint(length) followed by the UTF-8 payload."""
    if not isinstance(text, str):
        raise ValueError("frame payload must be a str")
    raw = text.encode("utf-8")
    return _varint(len(raw)) + raw


def decode_frame(data):
    """Read a varint length and the payload it describes."""
    length, offset = _read_varint(bytes(data), 0)
    payload = bytes(data)[offset:offset + length]
    if len(payload) != length:
        raise ValueError("truncated frame")
    return payload.decode("utf-8")
'''

_FIXED_SITE = 'def frame_length_%02d(%s):\n    """Length to write for %s before encoding (see README)."""\n    return len(%s.encode("utf-8"))\n'


def module_source(buggy=True, helpers=N_HELPERS):
    parts = [_HEADER.replace('import codecs\n', 'import re\nimport codecs\n')]
    parts.append(VARINT_CORRECT)
    for index in range(9):
        parts.append(_site_source(index) if buggy else
                     _FIXED_SITE % (index, SITES[index][1], SITES[index][1], SITES[index][1]))
        parts.append('\n')
    parts.append(API_BUGGY if buggy else API_FIXED)
    parts.append('\n')
    for index in range(helpers):
        parts.append(_helper_source(index))
        parts.append('\n')
    return ''.join(parts)


def _fixed_sites():
    return [_FIXED_SITE % (index, argument, argument, argument)
            for index, (_expression, argument, _why) in enumerate(SITES)]


ASCII = ['', 'a', 'abcd', 'frame one']
NON_ASCII = ['caf\u00e9', '\u4e2d\u6587', '\U0001f600', '\u00e9' * 3, 'x\u00fc' * 4]


def cases(kind='longctx2'):
    out = []
    for index in range(9):
        for payload in ('abc', 'caf\u00e9', '\u4e2d\u6587'):
            out.append(('site%02d/%s' % (index, payload[:1].isascii() and 'ascii' or 'non-ascii'), index, payload))
    for payload in NON_ASCII:
        out.append(('api/roundtrip/%s' % payload[:1], None, payload))
    for payload in ASCII:
        out.append(('api/roundtrip-ascii/%r' % payload[:3], None, payload))
    out.append(('api/varint-length', 'varint', None))
    out.append(('api/truncated-raises', 'truncated', None))
    out.append(('structure/minimal-edit', 'minimal-edit', None))
    out.append(('structure/imports', 'imports', None))
    return out


def _functions(source):
    tree = ast.parse(source)
    lines = source.splitlines()
    out = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out[node.name] = re.sub(r'\s+', ' ', '\n'.join(lines[node.lineno - 1:node.end_lineno])).strip()
    return out


SHIM_DIR = ['.']


def _fresh(work):
    SHIM_DIR[0] = str(work)
    for name in ('legacy', 'solution'):
        sys.modules.pop(name, None)
    sys.path.insert(0, str(work))
    try:
        modules = {}
        for name in ('legacy',):
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
    return modules['legacy']


def evaluate_longctx2(work):
    work = Path(work)
    checks = []
    try:
        legacy = _fresh(work)
        imported = True
    except Exception:
        legacy, imported = None, False
    for label, index, payload in cases('longctx2'):
        if isinstance(index, int):
            passed = False
            if legacy is not None:
                func = getattr(legacy, 'frame_length_%02d' % index, None)
                try:
                    passed = func is not None and func(payload) == len(payload.encode('utf-8'))
                except Exception:
                    passed = False
            checks.append({'case': len(checks), 'pass': bool(passed), 'label': 'site/%s' % label})
        elif index is None:
            passed = False
            if legacy is not None:
                try:
                    passed = legacy.decode_frame(legacy.encode_frame(payload)) == payload
                except Exception:
                    passed = False
            checks.append({'case': len(checks), 'pass': bool(passed), 'label': 'api/%s' % label})
        elif index == 'varint':
            passed = False
            if legacy is not None:
                try:
                    data = legacy.encode_frame('caf\u00e9')
                    passed = data[0] == len('caf\u00e9'.encode('utf-8')) and data[1:].decode('utf-8') == 'caf\u00e9'
                except Exception:
                    passed = False
            checks.append({'case': len(checks), 'pass': bool(passed), 'label': 'api/varint-length'})
        elif index == 'truncated':
            passed = False
            if legacy is not None:
                try:
                    legacy.decode_frame(b'\x05ab')
                except ValueError:
                    passed = True
                except Exception:
                    passed = False
            checks.append({'case': len(checks), 'pass': bool(passed), 'label': 'api/truncated-raises'})
        elif index == 'imports':
            checks.append({'case': len(checks), 'pass': imported, 'label': 'structure/imports'})
        else:  # minimal-edit
            passed = False
            if work.joinpath('legacy.py').exists():
                source = work.joinpath('legacy.py').read_text(encoding='utf-8', errors='replace')
                candidate = _functions(source)
                reference = _functions(module_source(buggy=True))
                changed = [name for name in candidate
                           if name not in reference or reference[name] != candidate[name]]
                allowed = ['frame_length_%02d' % i for i in range(9)] + ['encode_frame', 'decode_frame']
                passed = not [name for name in changed if name not in allowed]
            checks.append({'case': len(checks), 'pass': bool(passed), 'label': 'structure/minimal-edit'})
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
    result = evaluate_longctx2(Path(sys.argv[1]))
    print(json.dumps(result))
    sys.exit(0 if result['passed'] == result['total'] else 1)
