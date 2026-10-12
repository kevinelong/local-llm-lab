"""knowledge_ab.py - run the pinned knowledge instrument on both stacks, one at a time.

Arms:
  qwen36  - llama.cpp on the RTX 5070, the same declaration the new-task roots use (Qwen3.6-35B-A3B
            Q4_K_M, context 131,072), launched here because the harness normally owns that server.
  strata  - the Strata engine with its own pinned config (Qwen3.8-Flash-Next Q2_0, context 65,536,
            4 GiB resident), started and stopped around the run.

Sampling is pinned per request inside knowledge_run.py (temperature 0, seed 20261009); the Strata config
declares no seed, which this instrument therefore supplies itself. Each arm is a separate inference
workload: they run serially, and the server is torn down between them.

Usage: python knowledge_ab.py [--arms qwen36,strata] [--limit N] [--timeout S]
"""
import argparse
import json
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

BASE = Path(r'C:\Users\kevin\ai_bench')
HERE = BASE / 'new-items-20261007'
NINE = BASE / 'newtasks-ext-20261009-v12'          # the nine-task root: same model + declaration
LLAMA = BASE / 'staged-27b-20261007' / 'llamacpp-b11461' / 'llama-server.exe'
STRATA_PY = BASE / 'staged-strata-20261007' / 'engine-src-v0.1.40.3' / '.venv' / 'Scripts' / 'python.exe'
STRATA_SERVER = BASE / 'staged-strata-20261007' / 'engine-src-v0.1.40.3' / 'serve' / 'server.py'
STRATA_CONFIG = BASE / 'staged-strata-20261007' / 'engine-src-v0.1.40.3' / 'strata-q2_0.json'
NO_WINDOW = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
LLAMA_PORT = 11436
STRATA_PORT = 8080


def port_open(port, host='127.0.0.1'):
    with socket.socket() as sock:
        return sock.connect_ex((host, port)) == 0


def wait_health(url, deadline_seconds, label):
    deadline = time.monotonic() + deadline_seconds
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url + '/health', timeout=5):
                print('   %s is up' % label, flush=True)
                return True
        except Exception:
            time.sleep(2)
    print('   %s did NOT come up within %ds' % (label, deadline_seconds), flush=True)
    return False


def run_instrument(label, url, model, limit, timeout, script='knowledge_run.py', extra=None):
    command = [sys.executable, str(HERE / script), '--url', url, '--model', model,
               '--label', label, '--timeout', str(timeout)]
    if limit:
        command += ['--limit', str(limit)]
    if extra:
        command += extra
    print('   %s --label %s --url %s' % (script, label, url), flush=True)
    return subprocess.call(command, cwd=str(HERE))


def arm_qwen36(limit, timeout, script='knowledge_run.py', extra=None, suffix=''):
    model_file = next((NINE / 'models' / 'qwen36-35b-a3b').glob('*.gguf'))
    # faithful to the declaration the scored nine-task root used (_parsers' status.json), so the
    # knowledge run is the same configuration as the suite: MoE experts on CPU, 12 GB card for the rest.
    args = [str(LLAMA), '-m', str(model_file), '--host', '127.0.0.1', '--port', str(LLAMA_PORT),
            '-c', '131072', '-np', '1', '-ngl', '99', '-t', '8', '--jinja',
            '--chat-template-kwargs', '{"reasoning_effort":"low"}', '--reasoning-format', 'deepseek',
            '--reasoning-budget', '6144', '--reasoning-budget-message',
            'Stop thinking and act now: run the check you intended, or make the edit you intended.',
            '--alias', 'qwen36-35b-a3b-q8-local', '--cpu-moe', '--load-mode', 'none',
            '--temp', '1', '--top-p', '.95', '--top-k', '0', '--min-p', '0', '--repeat-penalty', '1',
            '--seed', '20260929']
    print('arm qwen36: launching %s' % model_file.name, flush=True)
    log = (HERE / 'knowledge-qwen36-server.log').open('w', encoding='utf8')
    server = subprocess.Popen(args, stdout=log, stderr=subprocess.STDOUT, creationflags=NO_WINDOW)
    try:
        if not wait_health('http://127.0.0.1:%d' % LLAMA_PORT, 600, 'llama-server'):
            return 2
        label = 'qwen36-131072' if script == 'knowledge_run.py' else 'qwen36-deep' + suffix
        return run_instrument(label, 'http://127.0.0.1:%d' % LLAMA_PORT, 'qwen36-35b-a3b',
                              limit, timeout, script, extra)
    finally:
        # terminate() alone left six orphaned servers holding ~9 GiB after the first full run: on
        # Windows llama-server survives a plain terminate, so kill the tree by pid.
        subprocess.run(['taskkill', '/F', '/T', '/PID', str(server.pid)], capture_output=True,
                       creationflags=NO_WINDOW)
        try:
            server.wait(30)
        except subprocess.TimeoutExpired:
            server.kill()
        log.close()


def arm_strata(limit, timeout, script='knowledge_run.py', extra=None, suffix=''):
    if port_open(STRATA_PORT):
        print('arm strata: port %d already occupied - refusing to start a second engine' % STRATA_PORT)
        return 2
    args = [str(STRATA_PY), str(STRATA_SERVER), '--engine', 'strata', '--config', str(STRATA_CONFIG),
            '--port', str(STRATA_PORT)]
    print('arm strata: launching the engine', flush=True)
    log = (HERE / 'knowledge-strata-server.log').open('w', encoding='utf8')
    server = subprocess.Popen(args, stdout=log, stderr=subprocess.STDOUT, creationflags=NO_WINDOW)
    try:
        if not wait_health('http://127.0.0.1:%d' % STRATA_PORT, 1500, 'strata'):
            return 2
        label = 'strata-q2_0-65536' if script == 'knowledge_run.py' else 'strata-deep' + suffix
        return run_instrument(label, 'http://127.0.0.1:%d' % STRATA_PORT,
                              'strata-coder', limit, timeout, script, extra)
    finally:
        server.terminate()
        try:
            server.wait(60)
        except subprocess.TimeoutExpired:
            server.kill()
        log.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--arms', default='qwen36,strata')
    parser.add_argument('--limit', type=int, default=0)
    parser.add_argument('--timeout', type=int, default=240)
    parser.add_argument('--script', default='knowledge_run.py')
    parser.add_argument('--forms', default='reason,facts,paper')
    parser.add_argument('--seeds', type=int, default=3)
    parser.add_argument('--pool', default='mars')
    parser.add_argument('--suffix', default='')
    args = parser.parse_args()

    extra = (['--forms', args.forms, '--seeds', str(args.seeds), '--pool', args.pool]
             if args.script != 'knowledge_run.py' else None)
    codes = {}
    for arm in args.arms.split(','):
        if arm == 'qwen36':
            codes[arm] = arm_qwen36(args.limit, args.timeout, args.script, extra, args.suffix)
        elif arm == 'strata':
            codes[arm] = arm_strata(args.limit, args.timeout, args.script, extra, args.suffix)
        else:
            print('unknown arm:', arm)
    print(json.dumps({'arm_exit_codes': codes}))
    return 0


if __name__ == '__main__':
    sys.exit(main())
