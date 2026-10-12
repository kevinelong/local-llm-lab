"""probe_kolibri.py - why does Kolibri's community runtime fail to launch here?

`hob-b11434` (Seraphiel102/llama.cpp 0.5.0-dev build 11434 + kolibri1-llama.cpp.patch), the only runtime that
loads the kolibri1 architecture, died at model load with:

    E CUDA error: shared object initialization failed
    E   current device: 0, in function launch_fattn at ggml-cuda/fattn-common.cuh:1137

i.e. a CUDA kernel launch in the flash-attention path, with the same flags the frozen nine-task root declares
(`--cpu-moe -fa on -ctk q8_0 -ctv q8_0 --load-mode none`). This tries the cheap workarounds in order and
stops at the first that comes up and answers a chat request, printing the reason each time.

Evidence only: it starts and kills its own server on port 11436, changes nothing, and writes one log per
variant under logs/.
"""
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SERVER = r'C:\Users\kevin\ai_bench\staged-kolibri-20261007\hob-b11434\llama-server.exe'
GGUF = r'C:\Users\kevin\ai_bench\staged-kolibri-20261007\Kolibri-1-Q3_K_M.gguf'
PORT = 11436


def base(ngl='99'):
    return [SERVER, '-m', GGUF, '--host', '127.0.0.1', '--port', str(PORT), '-c', '4096', '-np', '1',
            '-ngl', ngl, '-t', '8', '--jinja', '--alias', 'kolibri-1', '--cpu-moe', '--load-mode', 'none']


VARIANTS = {
    'fa-off': base() + ['-fa', 'off'],
    'no-warmup': base() + ['--no-warmup'],
    'fa-off-no-warmup': base() + ['-fa', 'off', '--no-warmup'],
    'ngl0-fa-off': base('0') + ['-fa', 'off'],
    'kv-f16-fa-on': base() + ['-fa', 'on', '-ctk', 'f16', '-ctv', 'f16'],
    'no-jinja': [a for a in base() + ['-fa', 'off'] if a != '--jinja'],
}


def main():
    (ROOT / 'logs').mkdir(exist_ok=True)
    for name, args in VARIANTS.items():
        print('--- %s' % name, flush=True)
        log_path = ROOT / 'logs' / ('probe-%s.log' % name)
        with log_path.open('w', encoding='utf-8') as log:
            process = subprocess.Popen(args, stdout=log, stderr=subprocess.STDOUT)
            up, deadline = False, time.monotonic() + 300
            while time.monotonic() < deadline:
                try:
                    with urllib.request.urlopen('http://127.0.0.1:%d/health' % PORT, timeout=5):
                        up = True
                        break
                except Exception:
                    if process.poll() is not None:
                        break
                    time.sleep(5)
            answered = False
            if up:
                body = (b'{"model":"kolibri-1","messages":[{"role":"user","content":"What is 2+2? '
                        b'Answer with one digit."}],"max_tokens":16,"temperature":0}')
                try:
                    request = urllib.request.Request('http://127.0.0.1:%d/v1/chat/completions' % PORT, data=body,
                                                     headers={'Content-Type': 'application/json'})
                    with urllib.request.urlopen(request, timeout=180) as response:
                        text = response.read().decode('utf-8', 'replace')
                    answered = True
                    print('   health ok, chat ok: %s' % text[:140], flush=True)
                except Exception as exc:
                    print('   health ok, chat failed: %s' % exc, flush=True)
            else:
                print('   never became healthy (exit %s)' % process.poll(), flush=True)
            subprocess.run(['taskkill', '/F', '/T', '/PID', str(process.pid)], capture_output=True)
            try:
                process.wait(30)
            except subprocess.TimeoutExpired:
                process.kill()
        tail = log_path.read_text(encoding='utf-8', errors='replace').strip().splitlines()[-4:]
        for line in tail:
            print('   | %s' % line[:160], flush=True)
        if answered:
            print('VERDICT: variant "%s" loads AND answers; use it for the knowledge item.' % name)
            return 0
    print('VERDICT: none of the variants worked; the runtime cannot launch on this driver state.')
    return 1


if __name__ == '__main__':
    sys.exit(main())
