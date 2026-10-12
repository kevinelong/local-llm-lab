"""Bespoke public decision suite (3,880 human-labelled records) over llama-server /v1/systemone.

Actions: preflight, screen MODEL [SUBSET ...], audit.

Reuses the declared model/server configuration and the resource monitor from
decisions-20261005-v3, so the same per-model batch/slot settings, the same 8 GiB
worker-private cap for this GPU track, and the same 3/2/0.5 GiB floors apply. The wall
deadline is raised to 7200 s because the suite is 3,880 records, not 18.

No gate is changed here; the cap and floors are inherited from the v3 declaration.
"""
import importlib.util, json, os, subprocess, sys, time, urllib.request
from pathlib import Path

BASE = Path('C:/Users/kevin/ai_bench')
ROOT = Path(__file__).resolve().parent
E = ROOT / 'evidence'
DATA = BASE / 'staged-bespoke-20261005' / 'data' / 'public'
SOURCE = BASE / 'completion-20260923-v1/source'
PORT = 18096
WALL_SECONDS = 7200
sys.path.insert(0, str(SOURCE))
from owned_process_20260922 import spawn


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


mon = module('suite_monitor', BASE / 'local-decisions-20260925-v1/run.py')
v3 = module('decision_v3', BASE / 'decisions-20261005-v3/run.py')
mon.ROOT = ROOT
mon.EVIDENCE = E
save = mon.save


def wait_health(deadline):
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen('http://127.0.0.1:%d/health' % PORT, timeout=3) as response:
                if response.status == 200:
                    return json.load(response)
        except Exception:
            time.sleep(1)
    raise RuntimeError('llama-server did not become healthy on port %d' % PORT)


def screen(name, subsets, resuming=False):
    v3.verify_staged()
    spec = v3.model_spec(name)
    folder = E / (name + '-suite')
    if resuming:
        if not (folder / 'runs').exists():
            raise SystemExit('Nothing to resume: ' + str(folder))
    else:
        if folder.exists():
            raise SystemExit('Preserve previous run: ' + str(folder))
        folder.mkdir(parents=True)
    save(folder / 'preflight.json', mon.preflight())
    lock = ROOT / 'RUNNING.lock'
    with lock.open('x') as handle:
        handle.write(str(os.getpid()))
    server = None
    paging = None
    samples = []
    error = None
    try:
        paging = mon.Paging()
        command = [str(v3.RUNTIME / 'llama-server.exe'), '-m', spec['path'], '--host', '127.0.0.1',
                   '--port', str(PORT), '-c', '4096', '-ngl', '99'] + v3.server_args(name)
        save(folder / 'command.json', {'command': command})
        with (folder / 'server.log').open('w', encoding='utf8') as log:
            server = spawn(command, stdout=log, stderr=subprocess.STDOUT, env=v3.server_env(),
                           creationflags=subprocess.CREATE_NO_WINDOW)
            save(folder / 'health.json', wait_health(time.monotonic() + 300))
            with (folder / 'worker.log').open('a' if resuming else 'x', encoding='utf8') as worker_log:
                worker = subprocess.Popen([sys.executable, str(ROOT / 'suite_worker.py'),
                                           'http://127.0.0.1:%d' % PORT, str(DATA),
                                           str(folder / 'runs')] + subsets,
                                          stdout=worker_log, stderr=subprocess.STDOUT, env=v3.server_env(),
                                          creationflags=subprocess.CREATE_NO_WINDOW)
                deadline = time.monotonic() + WALL_SECONDS
                pressure = 0
                while worker.poll() is None:
                    sample = {**mon.memory(), **mon.gpu(), **mon.tree_memory(server),
                              'hard_pages_input_per_sec_system': paging.sample(), 'at': time.time()}
                    samples.append(sample)
                    pressure = pressure + 1 if sample['physical_available_gib'] < 4 and (sample['hard_pages_input_per_sec_system'] or 0) > 512 else 0
                    if mon.danger(sample) or pressure >= 10 \
                            or sample.get('server_private_gib', 0) > v3.WORKER_PRIVATE_CAP_GIB \
                            or time.monotonic() > deadline or (ROOT / 'STOP').exists():
                        error = 'resource_paging_deadline_or_STOP'
                        worker.terminate()
                        break
                    time.sleep(0.5)
                worker.wait(timeout=60)
                if worker.returncode:
                    error = error or 'worker_exit_' + str(worker.returncode)
    finally:
        if server is not None and server.poll() is None:
            mon.stop_tree(server)
            server.wait(timeout=30)
        if paging:
            paging.close()
        save(folder / 'resources.json', samples)
        save(folder / 'status.json', {'error': error, 'after': mon.memory()})
        lock.unlink(missing_ok=True)
    suite = folder / 'runs' / 'suite.json'
    if suite.exists():
        save(folder / 'suite.json', json.loads(suite.read_text()))
    print(json.dumps({'model': name, 'error': error, 'samples': len(samples),
                      'suite': json.loads(suite.read_text()) if suite.exists() else None}, indent=2), flush=True)
    if error:
        raise SystemExit(1)


def audit():
    state = mon.preflight()
    save(E / 'final-audit.json', {'preflight': state, 'lock_absent': not (ROOT / 'RUNNING.lock').exists(),
                                  'reboot': False, 'staged_files': v3.verify_staged()})
    print('audit ok: no run lock, %d staged files verified' % v3.verify_staged())


if __name__ == '__main__':
    E.mkdir(exist_ok=True)
    args = sys.argv[1:]
    if args == ['preflight']:
        print(json.dumps(mon.preflight(), indent=2))
    elif args == ['audit']:
        audit()
    elif len(args) >= 2 and args[0] in ('screen', 'resume') and args[1] in v3.model_names():
        screen(args[1], args[2:], resuming=args[0] == 'resume')
    else:
        raise SystemExit('Expected preflight, screen|resume MODEL [SUBSET ...] or audit (%s)'
                         % ', '.join(v3.model_names()))
