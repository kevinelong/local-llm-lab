"""shared.py - engine launch/stop and guard helpers for the overnight queue.

Every item script uses this so the rules are in one place: one inference workload at a time (each script
starts and stops its own engine in a try/finally), the lab's resource floors checked before a load, the
declared launch flags reused rather than invented, and an owned-tree kill on the way out.

Nothing here writes outside the overnight root.
"""
import json
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

BASE = Path(r'C:\Users\kevin\ai_bench')
ROOT = Path(__file__).resolve().parent
LOGS = ROOT / 'logs'
NO_WINDOW = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
LLAMA_SERVER = BASE / 'staged-27b-20261007' / 'llamacpp-b11461' / 'llama-server.exe'
KOLIBRI_SERVER = BASE / 'staged-kolibri-20261007' / 'hob-b11434' / 'llama-server.exe'
STRATA_PY = BASE / 'staged-strata-20261007' / 'engine-src-v0.1.40.3' / '.venv' / 'Scripts' / 'python.exe'
STRATA_SERVER = BASE / 'staged-strata-20261007' / 'engine-src-v0.1.40.3' / 'serve' / 'server.py'
STRATA_CONFIG = BASE / 'staged-strata-20261007' / 'engine-src-v0.1.40.3' / 'strata-q2_0.json'
COLIBRI = BASE / 'staged-colibri-20261011' / 'coli.cmd'
COLIBRI_MODELS = Path(r'D:\ai_bench-staged\colibri-models')
LLAMA_PORT = 11436
STRATA_PORT = 8080
COLIBRI_PORT = 8000


def log(name, message):
    LOGS.mkdir(exist_ok=True)
    line = '%s  %s' % (time.strftime('%Y-%m-%d %H:%M:%S'), message)
    print(line, flush=True)
    with (LOGS / (name + '.log')).open('a', encoding='utf-8') as handle:
        handle.write(line + '\n')


def port_open(port, host='127.0.0.1'):
    with socket.socket() as sock:
        return sock.connect_ex((host, port)) == 0


def wait_health(url, seconds, label):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url + '/health', timeout=5):
                return True
        except Exception:
            time.sleep(3)
    log(label, 'did NOT become healthy within %ds' % seconds)
    return False


def resources():
    """The lab's gates: initial 9/8/7.5 GiB, floors 3/2/0.5 GiB. We need free physical and commit headroom."""
    out = subprocess.run(['powershell.exe', '-NoProfile', '-Command',
                          '"free=" + [math]::Round((Get-Counter \'\\Memory\\Available MBytes\').CounterSamples[0].CookedValue/1024,2)'
                          ' + " commit=" + [math]::Round((Get-Counter \'\\Memory\\Committed Bytes\').CounterSamples[0].CookedValue/1GB,2)'
                          ' + " commitLimit=" + [math]::Round((Get-Counter \'\\Memory\\Commit Limit\').CounterSamples[0].CookedValue/1GB,2)'],
                         capture_output=True, text=True)
    values = {}
    for token in out.stdout.split():
        if '=' in token:
            key, _, value = token.partition('=')
            try:
                values[key] = float(value)
            except ValueError:
                pass
    values['commit_headroom'] = values.get('commitLimit', 0) - values.get('commit', 0)
    return values


def guard_ok(min_free=9.0, min_headroom=8.0):
    r = resources()
    ok = r.get('free', 0) >= min_free and r.get('commit_headroom', 0) >= min_headroom
    log('guard', 'free=%.2f GiB commit_headroom=%.2f GiB -> %s' % (r.get('free', -1), r.get('commit_headroom', -1),
                                                                  'OK' if ok else 'BLOCKED'))
    return ok, r


def kill_port(port, name):
    """Kill whatever owns a port (our own engines only; Ollama is never on these ports)."""
    if not port_open(port):
        return False
    subprocess.run(['powershell.exe', '-NoProfile', '-Command',
                    "Get-NetTCPConnection -State Listen -LocalPort %d -ErrorAction SilentlyContinue | "
                    "ForEach-Object { taskkill /F /T /PID $_.OwningProcess }" % port],
                   capture_output=True, text=True, creationflags=NO_WINDOW)
    time.sleep(3)
    log(name, 'port %d cleared' % port)
    return True


class Engine:
    """Start an engine, wait for health, stop it on the way out. One at a time by construction."""

    def __init__(self, name, args, port, cwd=None, env=None):
        self.name = name
        self.args = [str(a) for a in args]
        self.port = port
        self.cwd = str(cwd) if cwd else None
        self.env = env
        self.process = None
        self.logfile = None

    def __enter__(self):
        if port_open(self.port):
            raise RuntimeError('%s: port %d already occupied' % (self.name, self.port))
        LOGS.mkdir(exist_ok=True)
        self.logfile = (LOGS / ('engine-%s.log' % self.name)).open('a', encoding='utf-8')
        self.logfile.write('\n=== %s\n%s\n' % (time.strftime('%F %T'), ' '.join(self.args)))
        self.logfile.flush()
        self.process = subprocess.Popen(self.args, stdout=self.logfile, stderr=subprocess.STDOUT,
                                        cwd=self.cwd, env=self.env, creationflags=NO_WINDOW)
        if not wait_health('http://127.0.0.1:%d' % self.port, 1800, self.name):
            self.__exit__(None, None, None)
            raise RuntimeError('%s failed to come up' % self.name)
        log(self.name, 'healthy')
        return self

    def __exit__(self, kind, value, traceback):
        if self.process is not None:
            subprocess.run(['taskkill', '/F', '/T', '/PID', str(self.process.pid)],
                           capture_output=True, creationflags=NO_WINDOW)
            try:
                self.process.wait(60)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.process = None
        kill_port(self.port, self.name)
        if self.logfile:
            self.logfile.close()
            self.logfile = None


def llama_engine(name, model_paths, extra, port=LLAMA_PORT, cwd=None):
    """A llama-server with the lab's declared sampling and a resident MoE placement."""
    args = [LLAMA_SERVER, '-m', model_paths[0], '--host', '127.0.0.1', '--port', str(port),
            '-c', '131072', '-np', '1', '-ngl', '99', '-t', '8', '--jinja', '--alias', name]
    args += extra
    args += ['--temp', '0', '--seed', '20260929']
    return Engine(name, args, port, cwd=cwd)


def strata_engine(name, config, port=STRATA_PORT):
    return Engine(name, [STRATA_PY, STRATA_SERVER, '--engine', 'strata', '--config', str(config),
                         '--port', str(port)], port)


def colibri_engine(name, model_dir, port=COLIBRI_PORT, env=None):
    return Engine(name, [COLIBRI, 'serve', '--model', str(model_dir)], port, cwd=str(COLIBRI.parent), env=env)


def write_result(name, payload):
    path = ROOT / ('result-%s.json' % name)
    path.write_text(json.dumps(payload, indent=1), encoding='utf-8')
    log(name, 'wrote %s' % path.name)
    return path
