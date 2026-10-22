"""gguf_tensors.py - read a GGUF header and report the quantisation type of chosen tensors.

Answers NEWS-2026-10-22 §8 item 1: are the routed experts' **down** projections Q4_K or Q6_K in our staged
Qwen3.6-35B-A3B Q4_K_M? Issue #3699 says the qwen36 path refuses Q4_K down projections, and Unsloth's UD files
"skirt" the case - so the type in our file decides whether that refusal can ever bite us.

Read-only: parses the header, never loads weights, needs no engine.

    python gguf_tensors.py FILE [substring ...]
"""
import struct
import sys
from collections import Counter
from pathlib import Path

GGML = {0: 'F32', 1: 'F16', 2: 'Q4_0', 3: 'Q4_1', 6: 'Q5_0', 7: 'Q5_1', 8: 'Q8_0', 9: 'Q8_1',
        10: 'Q2_K', 11: 'Q3_K', 12: 'Q4_K', 13: 'Q5_K', 14: 'Q6_K', 15: 'Q8_K',
        16: 'IQ2_XXS', 17: 'IQ2_XS', 18: 'IQ3_XXS', 19: 'IQ1_S', 20: 'IQ4_NL', 21: 'IQ3_S',
        22: 'IQ2_S', 23: 'IQ4_XS', 24: 'I8', 25: 'I16', 26: 'I32', 27: 'I64', 28: 'F64',
        29: 'IQ1_M', 30: 'BF16', 34: 'TQ1_0', 35: 'TQ2_0', 39: 'MXFP4'}
SCALAR = {0: ('<B', 1), 1: ('<b', 1), 2: ('<H', 2), 3: ('<h', 2), 4: ('<I', 4), 5: ('<i', 4),
          6: ('<f', 4), 7: ('<?', 1), 10: ('<Q', 8), 11: ('<q', 8), 12: ('<d', 8)}
T_STRING, T_ARRAY = 8, 9


class Reader:
    def __init__(self, fh):
        self.fh = fh

    def read(self, n):
        b = self.fh.read(n)
        if len(b) != n:
            raise EOFError('short read')
        return b

    def u32(self):
        return struct.unpack('<I', self.read(4))[0]

    def u64(self):
        return struct.unpack('<Q', self.read(8))[0]

    def string(self):
        n = self.u64()
        return self.read(n).decode('utf-8', 'replace')

    def skip_value(self, vtype):
        if vtype == T_STRING:
            self.read(self.u64())
            return ''
        if vtype == T_ARRAY:
            inner = self.u32()
            count = self.u64()
            if inner in SCALAR:                       # fixed width: one seek
                fmt, size = SCALAR[inner]
                self.fh.seek(count * size, 1)
            elif inner == T_STRING:                   # variable: walk the length prefixes
                for _ in range(count):
                    self.fh.seek(self.u64(), 1)
            else:
                raise ValueError('array of arrays')
            return ''
        fmt, size = SCALAR[vtype]
        raw = self.read(size)
        if size <= 8 and vtype in (4, 5, 10, 11):
            return struct.unpack(fmt, raw)[0]
        return ''


def main(argv):
    path = Path(argv[0])
    needles = argv[1:] or ['ffn_down_exps', 'ffn_up_exps', 'ffn_gate_exps', 'token_embd', 'output']
    with open(path, 'rb') as fh:
        r = Reader(fh)
        magic = fh.read(4)
        if magic != b'GGUF':
            print('not a GGUF file (magic %r)' % magic)
            return 2
        version = r.u32()
        n_tensors = r.u64()
        n_kv = r.u64()
        meta = {}
        for _ in range(n_kv):
            key = r.string()
            vtype = r.u32()
            value = r.skip_value(vtype)
            if key in ('general.architecture', 'general.name', 'general.file_type',
                       'split.no', 'split.count'):
                meta[key] = value
        print('%s: GGUF v%d, %d tensors, %d metadata keys' % (path.name, version, n_tensors, n_kv))
        for k, v in meta.items():
            print('  %-26s %s' % (k, v))

        rows = []
        for _ in range(n_tensors):
            name = r.string()
            n_dims = r.u32()
            dims = [r.u64() for _ in range(n_dims)]
            ttype = r.u32()
            r.u64()                                   # offset
            rows.append((name, dims, ttype))

    print('\ntensor types overall:')
    for t, c in Counter(GGML.get(x, 'type-%d' % x) for _, _, x in rows).most_common():
        print('  %-8s %d' % (t, c))

    print('\ntensors of interest:')
    for needle in needles:
        hit = [(n, d, t) for n, d, t in rows if needle in n]
        if not hit:
            print('  %-16s none' % needle)
            continue
        types = Counter(GGML.get(t, 'type-%d' % t) for _, _, t in hit)
        print('  %-16s %3d tensors  %s' % (needle, len(hit), dict(types)))
        for n, d, t in hit[:2]:
            print('      %-42s %s %s' % (n, dims_str := 'x'.join(str(v) for v in d), GGML.get(t, t)))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
