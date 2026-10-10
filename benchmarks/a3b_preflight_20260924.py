"""Read GGUF headers and estimate A3B placements without loading model tensors."""
import argparse
import ctypes
import csv
import datetime
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import urllib.request
import urllib.error

GIB = 1024 ** 3
BASE = Path('C:/Users/kevin')
MODEL_ROOT = BASE / '.ollama/models'
RUNTIME = BASE / 'ai_bench/a3b-offload-20260924-v1/runtime/llama-server.exe'
FORMATS = {0:'B', 1:'b', 2:'H', 3:'h', 4:'I', 5:'i', 6:'f', 7:'?', 10:'Q', 11:'q', 12:'d'}


def process_inventory():
    raw = subprocess.check_output(['tasklist.exe', '/FO', 'CSV', '/NH'], text=True, timeout=20)
    rows = list(csv.reader(raw.splitlines()))
    if len(rows) < 5 or any(len(row) < 2 or not row[1].isdigit() for row in rows):
        raise RuntimeError('Cannot verify system process inventory')
    return [{'name': row[0], 'pid': int(row[1])} for row in rows]


def ollama_state(processes):
    try:
        with urllib.request.urlopen('http://127.0.0.1:11434/api/ps', timeout=3) as response:
            state = json.load(response)
        if not isinstance(state.get('models'), list):
            raise ValueError('Invalid Ollama state response')
        return state
    except (urllib.error.URLError, TimeoutError) as exc:
        if any(p['name'].lower().startswith('ollama') for p in processes):
            raise RuntimeError('Ollama endpoint unavailable but Ollama process exists') from exc
        return {'models': [], 'status': 'offline_process_absence_verified', 'process_count_checked': len(processes)}


def memory():
    class Memory(ctypes.Structure):
        _fields_ = [('length', ctypes.c_ulong), ('load', ctypes.c_ulong)] + [
            (n, ctypes.c_ulonglong) for n in ('total', 'available', 'page_total',
            'page_available', 'virtual_total', 'virtual_available', 'extended')]
    m = Memory()
    m.length = ctypes.sizeof(m)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m)):
        raise OSError('Memory query failed')
    return {'physical_available_gib': m.available/GIB,
            'physical_total_gib': m.total/GIB, 'commit_headroom_gib': m.page_available/GIB}


def inspect(path):
    size = path.stat().st_size
    with path.open('rb') as f:
        def read(fmt):
            n = struct.calcsize('<' + fmt)
            b = f.read(n)
            if len(b) != n:
                raise ValueError('Truncated GGUF')
            return struct.unpack('<' + fmt, b)[0]

        def string(keep=True):
            n = read('Q')
            if n > size-f.tell():
                raise ValueError('Invalid string length')
            if keep:
                return f.read(n).decode('utf8')
            f.seek(n, 1)

        def value(kind, keep=True):
            if kind in FORMATS:
                return read(FORMATS[kind])
            if kind == 8:
                return string(keep)
            if kind == 9:
                subtype, count = read('I'), read('Q')
                if count > 10000000:
                    raise ValueError('Invalid array count')
                if subtype in FORMATS:
                    n = count * struct.calcsize('<' + FORMATS[subtype])
                    if n > size-f.tell():
                        raise ValueError('Truncated array')
                    f.seek(n, 1)
                else:
                    for _ in range(count):
                        value(subtype, False)
                return {'array_length': count, 'element_type': subtype}
            raise ValueError('Unknown metadata type: ' + str(kind))

        if f.read(4) != b'GGUF' or read('I') not in (2, 3):
            raise ValueError('Unsupported GGUF')
        nt, nk = read('Q'), read('Q')
        if nt > 100000 or nk > 100000:
            raise ValueError('Implausible GGUF counts')
        metadata = {}
        for _ in range(nk):
            key = string()
            val = value(read('I'), not key.startswith('tokenizer.'))
            if not key.startswith('tokenizer.'):
                metadata[key] = val
        tensors = []
        for _ in range(nt):
            name, nd = string(), read('I')
            if nd > 4:
                raise ValueError('Invalid tensor dimensions')
            dims = [read('Q') for _ in range(nd)]
            tensors.append({'name': name, 'dimensions': dims, 'type': read('I'), 'offset': read('Q')})
        alignment = metadata.get('general.alignment', 32)
        if not tensors or alignment <= 0 or alignment & (alignment-1):
            raise ValueError('Invalid tensor count or alignment')
        start = (f.tell() + alignment - 1) // alignment * alignment
        tensors.sort(key=lambda t: t['offset'])
        if tensors[0]['offset'] != 0:
            raise ValueError('Unexpected initial tensor offset')
        for i, t in enumerate(tensors):
            end = tensors[i+1]['offset'] if i+1 < len(tensors) else size-start
            t['padded_bytes'] = end-t['offset']
            if t['padded_bytes'] <= 0:
                raise ValueError('Invalid tensor extent')
        assert start + sum(t['padded_bytes'] for t in tensors) == size
    return {'file_bytes': size, 'header_bytes': start, 'metadata': metadata, 'tensors': tensors}


def placements(info, available, gpu_free):
    meta, tensors = info['metadata'], info['tensors']
    arch = meta['general.architecture']
    layers = meta[arch+'.block_count']
    experts = []
    for t in tensors:
        match = re.fullmatch(r'blk\.(\d+)\.ffn_(?:up|gate|down)_exps\.weight', t['name'])
        if match:
            experts.append((int(match[1]), t['padded_bytes']))
    if len(experts) != layers*3:
        raise ValueError('Unsupported expert layout; inspect before planning')
    total = sum(t['padded_bytes'] for t in tensors)/GIB
    all_experts = sum(size for _, size in experts)/GIB
    # This estimator supports the installed Qwen3 MoE attention layout only.
    if arch != 'qwen3moe':
        raise ValueError('KV estimator needs an architecture-specific implementation')
    head_dim = meta[arch+'.embedding_length']/meta[arch+'.attention.head_count']
    key_dim = meta.get(arch+'.attention.key_length', head_dim)
    val_dim = meta.get(arch+'.attention.value_length', head_dim)
    kv = layers*meta[arch+'.attention.head_count_kv']*(key_dim+val_dim)*8192*2/GIB
    rows = []
    for n in (0, 16, 24, 28, 32, 36, 40, 48):
        cpu = sum(size for layer, size in experts if layer < n)/GIB
        gpu = total-cpu
        # Planning reserves, not measured runtime allocations: 1 GiB GPU scratch,
        # 1.5 GiB GPU margin, 1 GiB host scratch and 3 GiB physical/commit margin.
        need_ram, need_gpu = cpu+4, gpu+kv+2.5
        rows.append({'cpu_expert_layers': n, 'cpu_weight_gib': cpu,
                     'gpu_weight_upper_bound_gib': gpu, 'f16_kv_8k_gib': kv,
                     'required_free_ram_estimate_gib': need_ram,
                     'required_free_vram_estimate_gib': need_gpu,
                     'fits_estimated_ram': need_ram <= available['physical_available_gib'],
                     'fits_estimated_commit': need_ram <= available['commit_headroom_gib'],
                     'fits_estimated_vram': need_gpu <= gpu_free})
    return {'total_weight_gib': total, 'routed_expert_weight_gib': all_experts,
            'non_expert_weight_gib': total-all_experts, 'placements': rows,
            'caveat': 'Padded tensor spans; excludes loader duplication and runtime-specific repacking. '
                      'GPU estimate conservatively places all non-expert weights on GPU. '
                      'Cache designs retaining the full expert backing in RAM need more host RAM.'}


def eligibility(row, resident, locks):
    reasons = []
    for key in ('ram', 'commit', 'vram'):
        if not row['fits_estimated_'+key]:
            reasons.append('insufficient_'+key)
    if resident.get('models'):
        reasons.append('ollama_model_resident')
    if locks:
        reasons.append('existing_run_lock')
    return reasons


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit('Refusing to overwrite an existing evidence file')
    mem = memory()
    gpu_raw = subprocess.check_output(['nvidia-smi', '--query-gpu=memory.free,memory.total',
        '--format=csv,noheader,nounits'], text=True, timeout=20)
    free, total = [float(v.strip())/1024 for v in gpu_raw.splitlines()[0].split(',')]
    processes = process_inventory()
    resident = ollama_state(processes)
    competing = [p for p in processes if p['name'].lower().startswith(('llama-server', 'llama-cli', 'llama-bench', 'vllm', 'kobold'))]
    locks = [str(p) for p in (BASE/'ai_bench').rglob('RUNNING.lock')]
    models = []
    for name, tag in [('qwen3-coder','30b'), ('qwen3','30b-a3b')]:
        manifest_path = MODEL_ROOT/'manifests/registry.ollama.ai/library'/name/tag
        manifest = json.loads(manifest_path.read_text())
        layer = next(x for x in manifest['layers'] if x['mediaType'] == 'application/vnd.ollama.image.model')
        path = MODEL_ROOT/'blobs'/layer['digest'].replace(':','-')
        info = inspect(path)
        if info['file_bytes'] != layer['size']:
            raise ValueError('Manifest size mismatch')
        plan = placements(info, mem, free)
        rows = plan['placements']
        for row in rows:
            row['hold_reasons'] = eligibility(row, resident, locks)
            if competing:
                row['hold_reasons'].append('competing_inference_process')
        ready = [x for x in rows if not x['hold_reasons']]
        models.append({'ollama_name': name+':'+tag, 'path': str(path),
            'manifest_digest_not_rehashed': layer['digest'],
            'manifest_sha256': hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
            'file_bytes': info['file_bytes'], 'metadata': info['metadata'],
            'tensor_count': len(info['tensors']), 'plan': plan,
            'estimated_feasible_count': len(ready)})
    evidence = {'time_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'phase': 'metadata_and_resource_preflight_no_model_loaded', 'memory': mem,
        'gpu_free_gib': free, 'gpu_total_gib': total, 'resident_ollama': resident,
        'competing_inference_processes': competing,
        'run_locks': locks, 'models': models, 'runtime': str(RUNTIME),
        'runtime_exists': RUNTIME.exists(),
        'eligibility_scope': 'Resource screening only; verify runtime, competing processes, '
                             'load peaks and actual placement before inference.',
        'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(evidence, indent=2), encoding='ascii')
    print(json.dumps({'output': str(args.output), 'memory': mem, 'gpu_free_gib': free,
        'models': [{k:m[k] for k in ('ollama_name','estimated_feasible_count')} for m in models]}, indent=2))


if __name__ == '__main__':
    main()
