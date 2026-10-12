"""strata_warmcache.py - does a representative warm-up raise Strata's decode speed?

The question: three independent sources say the expert cache is the lever, not the engine. Colibri fills its
GPU tier "from the experts your past conversations used" and measured a first run going from ~6 to 11 tok/s
once the tier was pre-filled (#1919). The llama.cpp SSD proposal measured a calibrated hot set at a 42 % hit
rate against 6 % for an uncalibrated one. Our own Strata already ships `--expert-profile`
(`data/expert-profile.bin`) and `--expert-cache auto`, so the mechanism exists in the engine we already run -
the open question is whether *our* workload matches what the profile knows.

Design, holding the load and the declaration fixed in one engine process:
  1. COLD    - a fixed probe prompt, three times, immediately after load.
  2. WARM-UP - eight prompts drawn from the same domain as the probe (our own frozen knowledge material),
               so the hot experts they touch should overlap the probe's.
  3. WARM    - the same probe, three times again.
Reported: decode tokens/second per phase, time to first byte, whether the three outputs in a phase agree
(a placement/output check, since we already know this engine is not seed-stable at temperature 0), and the
expert-profile file's size and mtime before and after, which tells us whether the engine rewrites it.

This starts and stops the engine itself. One inference workload at a time; nothing else may be resident.

Usage: python strata_warmcache.py [--probe-repeats 3] [--warmup 8]
"""
import argparse
import json
import os
import socket
import statistics
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

BASE = Path(r'C:\Users\kevin\ai_bench')
ROOT = BASE / 'staged-strata-20261007' / 'engine-src-v0.1.40.3'
PY = ROOT / '.venv' / 'Scripts' / 'python.exe'
SERVER = ROOT / 'serve' / 'server.py'
CONFIG = ROOT / 'strata-q2_0.json'
PROFILE = ROOT / 'data' / 'expert-profile.bin'
PORT = 8080
KNOWLEDGE = BASE / 'new-items-20261007' / 'knowledge-items-20261009.jsonl'
NO_WINDOW = getattr(subprocess, 'CREATE_NO_WINDOW', 0)

# The probe: one fixed astronomy item, long enough to decode meaningfully. Same text every phase.
PROBE = ('Explain in detail how the inverse-square law of light governs the apparent brightness of a star '
         'as seen from Earth, and what astronomers can infer about a star\u2019s intrinsic luminosity from '
         'its spectrum and distance. Be precise about the physics and the units.')


def port_open(port, host='127.0.0.1'):
    with socket.socket() as sock:
        return sock.connect_ex((host, port)) == 0


def wait_health(deadline_seconds):
    deadline = time.monotonic() + deadline_seconds
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen('http://127.0.0.1:%d/health' % PORT, timeout=5):
                return True
        except Exception:
            time.sleep(2)
    return False


def warmup_prompts(count):
    """Prompts from the same domain as the probe, so their hot experts overlap it."""
    prompts = []
    if KNOWLEDGE.exists():
        for line in KNOWLEDGE.read_text(encoding='ascii').splitlines():
            if not line.strip():
                continue
            item = json.loads(line)
            if item.get('subject') == 'astronomy' and item.get('prompt'):
                prompts.append('Answer carefully and explain: ' + item['prompt'][:400])
            if len(prompts) >= count:
                break
    return prompts[:count]


def chunk(url, payload, timeout=600):
    """One streaming request; returns (text, ttfb_ms, total_ms, tokens_reported)."""
    request = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'),
                                     headers={'Content-Type': 'application/json'})
    started = time.monotonic()
    first = None
    text, usage = [], None
    with urllib.request.urlopen(request, timeout=timeout) as response:
        for raw in response:
            if first is None:
                first = time.monotonic()
            line = raw.decode('utf-8', 'replace').strip()
            if not line.startswith('data:'):
                continue
            body = line[5:].strip()
            if body == '[DONE]':
                break
            try:
                event = json.loads(body)
            except Exception:
                continue
            if event.get('usage'):
                usage = event['usage']
            for choice in event.get('choices', []):
                delta = choice.get('delta') or {}
                piece = delta.get('content') or ''
                # This engine puts everything in reasoning_content at low max_tokens (a lab-recorded
                # behaviour), so collect both or the output check is comparing empty strings.
                piece += delta.get('reasoning_content') or ''
                piece += delta.get('reasoning') or ''
                if piece:
                    text.append(piece)
    total = time.monotonic() - started
    tokens = (usage or {}).get('completion_tokens')
    return ''.join(text), (first - started) * 1000.0 if first else None, total * 1000.0, tokens


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--probe-repeats', type=int, default=3)
    parser.add_argument('--warmup', type=int, default=8)
    parser.add_argument('--max-tokens', type=int, default=160)
    args = parser.parse_args()

    if port_open(PORT):
        sys.exit('port %d already occupied - refusing to start a second engine' % PORT)
    if not CONFIG.exists():
        sys.exit('config missing: %s' % CONFIG)
    before = {'exists': PROFILE.exists(),
              'size': PROFILE.stat().st_size if PROFILE.exists() else None,
              'mtime': PROFILE.stat().st_mtime if PROFILE.exists() else None}

    log = (Path(__file__).resolve().parent / 'strata-warmcache-server.log').open('w', encoding='utf8')
    server = subprocess.Popen([str(PY), str(SERVER), '--engine', 'strata', '--config', str(CONFIG),
                               '--port', str(PORT)], stdout=log, stderr=subprocess.STDOUT,
                              creationflags=NO_WINDOW)
    url = 'http://127.0.0.1:%d/v1/chat/completions' % PORT
    result = {'probe_repeats': args.probe_repeats, 'warmup_requests': args.warmup,
              'config': str(CONFIG), 'profile_before': before, 'phases': {}}
    try:
        if not wait_health(1200):
            sys.exit('engine did not come up')
        print('engine up', flush=True)

        def run_probe(label, count):
            rows = []
            for index in range(count):
                payload = {'model': 'qwen3.8-flash-next-q2_0', 'stream': True, 'temperature': 0,
                           'max_tokens': args.max_tokens,
                           'messages': [{'role': 'user', 'content': PROBE}]}
                text, ttfb, total, tokens = chunk(url, payload)
                rows.append({'i': index, 'ttfb_ms': round(ttfb, 1) if ttfb else None,
                             'total_ms': round(total, 1), 'tokens_reported': tokens,
                             'chars': len(text), 'head': text[:120]})
                print('  %-5s #%d  ttfb %.0f ms  total %.0f ms  chars %d'
                      % (label, index, ttfb or -1, total, len(text)), flush=True)
            result['phases'][label] = rows
            return rows

        cold = run_probe('cold', args.probe_repeats)

        prompts = warmup_prompts(args.warmup)
        print('warm-up: %d prompts from the same domain' % len(prompts), flush=True)
        for index, prompt in enumerate(prompts):
            payload = {'model': 'qwen3.8-flash-next-q2_0', 'stream': True, 'temperature': 0,
                       'max_tokens': 96, 'messages': [{'role': 'user', 'content': prompt}]}
            _, ttfb, total, _ = chunk(url, payload)
            print('  warm #%d  total %.0f ms' % (index, total), flush=True)

        warm = run_probe('warm', args.probe_repeats)
        result['profile_after'] = {'exists': PROFILE.exists(),
                                   'size': PROFILE.stat().st_size if PROFILE.exists() else None,
                                   'mtime': PROFILE.stat().st_mtime if PROFILE.exists() else None}

        def rate(rows):
            reported = [(r['tokens_reported'], r['total_ms']) for r in rows if r.get('tokens_reported')]
            if reported:
                return [1000.0 * t / ms for t, ms in reported]
            return None

        for label in ('cold', 'warm'):
            rows = result['phases'][label]
            rates = rate(rows)
            totals = [r['total_ms'] for r in rows]
            ttfbs = [r['ttfb_ms'] for r in rows if r['ttfb_ms']]
            same = len({r['head'] for r in rows}) == 1
            result['phases'][label + '_summary'] = {
                'median_total_ms': statistics.median(totals),
                'median_ttfb_ms': statistics.median(ttfbs) if ttfbs else None,
                'tok_per_s_reported': [round(x, 2) for x in rates] if rates else None,
                'identical_outputs': same,
            }
            print('%-5s median total %.0f ms  ttfb %.0f ms  tok/s %s  identical outputs: %s'
                  % (label, statistics.median(totals), statistics.median(ttfbs) if ttfbs else -1,
                     ('%.2f' % statistics.median(rates)) if rates else 'not reported', same))
        out = Path(__file__).resolve().parent / 'strata-warmcache.json'
        out.write_text(json.dumps(result, indent=1), encoding='utf-8')
        print('wrote %s' % out)
        return 0
    finally:
        server.terminate()
        try:
            server.wait(60)
        except subprocess.TimeoutExpired:
            server.kill()
        log.close()


if __name__ == '__main__':
    sys.exit(main())
