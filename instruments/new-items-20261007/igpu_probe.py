"""igpu_probe.py - price the Intel Arc iGPU (and the NPU question) against the RTX 5070, honestly.

Why a probe and not a benchmark: the lab's measured evidence is CUDA on the discrete card, and its
runtime (`llama-server --list-devices`) sees only `CUDA0`. Ollama 0.40.0 has no NPU backend at all - its
own log lists CUDA plus an opt-in Vulkan path for the iGPU (`dropping integrated GPU; to enable, set
OLLAMA_IGPU_ENABLE=1`) - so the only reachable Intel device is the iGPU, and the only fair question is
what it costs: tokens per second, on the same small model and the same prompts.

Two arms, both with the discrete card hidden so the comparison is device-for-device:

  arm A  cuda   - CUDA_VISIBLE_DEVICES unset, OLLAMA_IGPU_ENABLE unset (iGPU dropped by default)
  arm B  igpu   - CUDA_VISIBLE_DEVICES='' (hides the 5070), OLLAMA_IGPU_ENABLE=1 (Vulkan on the Arc)

Each arm restarts the Ollama server with its environment, runs the fixed prompt set, and reads the
rate from Ollama's own response timings. The previous server state is restored at the end.

This is a hardware probe, not a suite measurement: it changes an execution provider mid-series, so its
numbers never mix with the frozen screens. Run it only when nothing else is using the GPU (one inference
workload at a time), and expect the iGPU arm to lose badly - it shares DDR5 while the 5070 has ~7x the
bandwidth - so the value is the measured ratio and the "it cannot do X" boundary, not speed.

Usage:
  python igpu_probe.py --list                 # what Ollama has pulled (no inference)
  python igpu_probe.py --model qwen3:1.7b     # run both arms and write igpu-probe-<model>.json
"""
import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
API = 'http://127.0.0.1:11434'
PROMPTS = [
    'Write the numbers from 1 to 20, separated by commas.',
    'Explain in three sentences why the sky is blue.',
    'List five European capitals and the country each belongs to.',
    'Rewrite this sentence in the passive voice: The engineer fixed the bug overnight.',
    'What is 17 * 23? Show the arithmetic.',
]
MAX_TOKENS = 128
NO_WINDOW = getattr(subprocess, 'CREATE_NO_WINDOW', 0)


def api(path, body=None, timeout=900):
    request = urllib.request.Request(API + path,
                                     data=None if body is None else json.dumps(body).encode('utf-8'),
                                     headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


def server_up(timeout=25):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            api('/api/tags', timeout=5)
            return True
        except Exception:
            time.sleep(1)
    return False


def stop_server():
    """Stop only the Ollama server processes this probe is allowed to touch (the tray app stays)."""
    subprocess.run(['taskkill', '/IM', 'ollama.exe', '/F'], capture_output=True, creationflags=NO_WINDOW)
    time.sleep(2)


def start_server(env, log_path=None):
    handle = open(log_path, 'w', encoding='utf8') if log_path else subprocess.DEVNULL
    subprocess.Popen(['ollama', 'serve'], env=env, stdout=handle, stderr=subprocess.STDOUT,
                     creationflags=NO_WINDOW)
    return server_up()


def device_lines(log_path):
    """Ollama names the compute it will use in its own log; that is the arm's attribution."""
    if not log_path or not Path(log_path).exists():
        return []
    keep = []
    for line in Path(log_path).read_text(encoding='utf-8', errors='replace').splitlines():
        if 'inference compute' in line or 'dropping integrated GPU' in line or 'unsupported' in line:
            keep.append(line[-190:])
    return keep


def ps_line():
    out = subprocess.run(['ollama', 'ps'], capture_output=True, text=True, creationflags=NO_WINDOW)
    return (out.stdout or '').strip().splitlines()[-1:] or []


def arm_env(name):
    env = os.environ.copy()
    if name == 'cuda':
        env.pop('OLLAMA_IGPU_ENABLE', None)
        env.pop('CUDA_VISIBLE_DEVICES', None)
    else:
        env['OLLAMA_IGPU_ENABLE'] = '1'
        # `''` is treated as unset by CUDA tooling - the first run of this probe proved it: both arms
        # reported `100% GPU` on the 5070 and identical rates. `-1` is the canonical "no device".
        env['CUDA_VISIBLE_DEVICES'] = '-1'
    return env


def measure(model, label):
    env = arm_env(label)
    stop_server()
    log = HERE / ('igpu-server-%s.log' % label)
    if not start_server(env, log):
        return {'arm': label, 'error': 'server did not come up'}
    rows, started = [], time.monotonic()
    for prompt in PROMPTS:
        began = time.monotonic()
        reply = api('/api/chat', {'model': model, 'stream': False, 'options': {'temperature': 0, 'seed': 20261009},
                                 'messages': [{'role': 'user', 'content': prompt}]})
        wall = time.monotonic() - began
        eval_count = reply.get('eval_count') or 0
        eval_ns = reply.get('eval_duration') or 0
        rows.append({'seconds': round(wall, 2),
                     'eval_tokens': eval_count,
                     'tok_per_s': round(eval_count / (eval_ns / 1e9), 2) if eval_ns else None,
                     'load_ms': round((reply.get('load_duration') or 0) / 1e6, 1),
                     'prompt_tokens': reply.get('prompt_eval_count'),
                     'eval_ms': round(eval_ns / 1e6, 1),
                     'reply_head': (reply.get('message') or {}).get('content', '')[:80]})
    total_tokens = sum(r['eval_tokens'] for r in rows)
    rates = [r['tok_per_s'] for r in rows if r['tok_per_s']]
    return {'arm': label, 'model': model, 'prompts': len(PROMPTS), 'wall_seconds': round(time.monotonic() - started, 1),
            'device_lines': device_lines(log), 'ollama_ps': ps_line(),
            'eval_tokens': total_tokens,
            'median_tok_per_s': round(sorted(rates)[len(rates) // 2], 2) if rates else None,
            'rows': rows,
            'env': {k: env.get(k) for k in ('OLLAMA_IGPU_ENABLE', 'CUDA_VISIBLE_DEVICES')}}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--list', action='store_true')
    parser.add_argument('--model', default='')
    parser.add_argument('--arms', default='cuda,igpu')
    args = parser.parse_args()

    if args.list or not args.model:
        if not server_up(timeout=10):
            print('ollama server is not answering on', API)
            return 1
        models = [m['name'] for m in api('/api/tags').get('models', [])]
        print('pulled models:', models or '(none)')
        print('pass --model <name> to run the arms')
        return 0

    results = []
    for label in args.arms.split(','):
        print('arm %-5s starting ...' % label, flush=True)
        result = measure(args.model, label)
        results.append(result)
        print('arm %-5s median tok/s %-7s tokens %-5s wall %ss %s' % (
            label, result.get('median_tok_per_s'), result.get('eval_tokens'),
            result.get('wall_seconds'), result.get('error') or ''), flush=True)

    # restore the default server (iGPU dropped, CUDA visible)
    stop_server()
    start_server(os.environ.copy())
    target = HERE / ('igpu-probe-%s.json' % args.model.replace(':', '-').replace('/', '-'))
    target.write_text(json.dumps({'prompts': PROMPTS, 'max_tokens': MAX_TOKENS, 'arms': results,
                                  'declared': 'hardware probe - execution provider changes between arms; '
                                              'never mixed with the frozen suite'}, indent=1), encoding='ascii')
    print('written:', target.name)
    return 0


if __name__ == '__main__':
    sys.exit(main())
