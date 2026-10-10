"""Prepare (default) or explicitly --run a serial, paired staging experiment.

Run with a NEW --label. Preparation never contacts models. --run both prepares
and executes; prepared labels cannot be resumed or overwritten. Transcript and
scorer isolation is an experimental convention, not a security sandbox. Windows
only for execution. No installation, alias creation, or unrelated process kill.
"""
import argparse
import datetime
import hashlib
import http.server
import json
import os
from pathlib import Path
import random
import re
import shutil
import subprocess
import sys
import threading
import time
import urllib.request
import uuid

HERE = Path(__file__).resolve().parent
BENCH = Path('C:/Users/kevin/ai_bench')
ROOT = BENCH / 'staging-20260922'
PI = BENCH / 'pi-lab-0861/node_modules/@earendil-works/pi-coding-agent/dist/bundle/cli.js'
MODEL = 'night-20260916-omni-32768'
BASE = 'http://127.0.0.1:11434'
CAP = 12288
QUOTA = 16000
WALL = 180
NO_WINDOW = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
OWNED_JOBS = False  # Enabled only by the separately labeled overnight treatment.
COMMON = ('Read README.md. Use Python standard library only. Work only in this '
          'directory; no network, installations, other agents, or outside files. '
          'Do not modify test_public.py or README.md. Keep edits incremental. ')
PROMPTS = {
    'one-shot': COMMON + 'Repair solution.py to satisfy every requirement. Run public tests and audit edge cases. Finish with a brief summary.',
    'plan': COMMON + 'Read solution.py and test_public.py. Produce a concise implementation plan covering every requirement and edge case. Do not write files or run commands.',
    'implement': COMMON + 'Repair solution.py using the plan below. Run public tests and fix failures. Finish with a brief summary.\nPLAN:\n',
    'audit': COMMON + 'Audit solution.py against every requirement, including edge cases. Fix remaining defects and run public tests. Finish with a brief summary.',
}


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=True), encoding='ascii')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def api(route, body=None, timeout=30):
    request = urllib.request.Request(BASE + route, data=None if body is None else json.dumps(body).encode(),
                                     headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


def schedule(tasks, seed=20260922):
    rng = random.Random(seed)
    blocks = [(name, repeat) for name in sorted(tasks) for repeat in range(1, 4)]
    rng.shuffle(blocks)
    result = []
    for name, repeat in blocks:
        treatments = ['one-shot', 'staged']
        rng.shuffle(treatments)
        result.extend(dict(task=name, repeat=repeat, treatment=t,
                           label=f'{name}-{repeat}-{t}') for t in treatments)
    return result


class Budget:
    """Serial reservations; backend overrun is detected, never called a hard cap."""
    def __init__(self, quota=QUOTA, cap=CAP):
        self.quota, self.cap, self.used = quota, cap, 0
        self.failure = None

    def allowance(self):
        if self.failure:
            raise RuntimeError(self.failure)
        remaining = self.quota - self.used
        if remaining <= 0:
            self.failure = 'quota_exhausted'
            raise RuntimeError(self.failure)
        return min(self.cap, remaining)

    def account(self, usage, allowance):
        value = (usage or {}).get('completion_tokens')
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            self.failure = 'quota_unknown'
        else:
            self.used += value
            if value > allowance or self.used > self.quota:
                self.failure = 'backend_quota_overrun'


class Relay(http.server.BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_POST(self):
        server = self.server
        if self.path != '/v1/chat/completions':
            self.send_error(404)
            return
        # Single HTTPServer serializes reservations, including retries.
        info, usage, allowance, sent = {}, None, None, False
        wire = server.folder / 'wire' / uuid.uuid4().hex
        wire.parent.mkdir(exist_ok=True)
        try:
            if server.stop.exists() or time.monotonic() >= server.deadline:
                raise RuntimeError('stop_or_deadline')
            allowance = server.budget.allowance()
            body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            body.update(model=MODEL, max_tokens=allowance, stream=True,
                        stream_options={'include_usage': True}, temperature=0)
            body.pop('max_completion_tokens', None)
            save(wire.with_suffix('.request.json'), body)
            info['allowance'] = allowance
            request = urllib.request.Request(BASE + self.path, data=json.dumps(body).encode(),
                                             headers={'Content-Type': 'application/json'})
            timeout = max(0.1, min(30, server.deadline - time.monotonic()))
            with urllib.request.urlopen(request, timeout=timeout) as upstream, wire.with_suffix('.sse').open('wb') as raw:
                self.send_response(200)
                self.send_header('Content-Type', 'text/event-stream')
                self.end_headers()
                sent = True
                for line in upstream:
                    if server.stop.exists() or time.monotonic() >= server.deadline:
                        raise TimeoutError('stop_or_deadline')
                    raw.write(line)
                    if line.startswith(b'data:'):
                        data = line[5:].strip()
                        if data == b'[DONE]':
                            info['done'] = True
                        else:
                            event = json.loads(data)
                            if event.get('usage'):
                                usage = event['usage']
                    self.wfile.write(line)
                    self.wfile.flush()
        except Exception as exc:
            info['error'] = repr(exc)
            if not sent:
                self.send_error(503, 'Experiment quota or upstream unavailable')
        finally:
            if allowance is not None:
                server.budget.account(usage, allowance)
            save(wire.with_suffix('.summary.json'), dict(info, usage=usage,
                 quota_failure=server.budget.failure, cumulative_tokens=server.budget.used))


def stop_owned(process):
    if OWNED_JOBS:
        return process._lab_job.terminate(process)
    result = {}
    try:
        killed = subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'],
                                capture_output=True, text=True, timeout=15, creationflags=NO_WINDOW)
        result.update(returncode=killed.returncode, stdout=killed.stdout, stderr=killed.stderr)
    except subprocess.TimeoutExpired:
        result['tree_kill_timed_out'] = True
    if process.poll() is None:
        process.kill()
    process.wait(timeout=5)
    return result


def spawn_owned(command, **kwargs):
    if OWNED_JOBS:
        from owned_process_20260922 import spawn
        return spawn(command, **kwargs)
    return subprocess.Popen(command, **kwargs)


def finish_owned(process):
    return process._lab_job.finish(process) if OWNED_JOBS else None


def preflight():
    locks = [BENCH / d / 'RUNNING.lock' for d in ('round-20260920', 'overnight-20260916')]
    locks += list((HERE.parent / 'goproverbs/results').glob('**/RUNNING.lock'))
    present = [str(p) for p in locks if p.exists()]
    if present:
        raise RuntimeError('Other workload locks: ' + ', '.join(present))
    loaded = api('/api/ps')
    if loaded.get('models'):
        raise RuntimeError('Resident model detected; root must inspect before unloading')
    gpu = subprocess.run(['nvidia-smi', '--query-gpu=memory.used,memory.free', '--format=csv,noheader,nounits'],
                         capture_output=True, text=True, timeout=15, check=True, creationflags=NO_WINDOW).stdout
    if int(gpu.splitlines()[0].split(',')[1]) < 7500:
        raise RuntimeError('Less than 7500 MiB free VRAM; preserving other work')
    process_cmd = "$ErrorActionPreference = 'Stop'; Get-Process | Where-Object { $_.ProcessName -match '^(katago|llama-server|llama-cli)$' } | Select-Object Id,ProcessName | ConvertTo-Json -Compress"
    processes = subprocess.run(['powershell.exe', '-NoProfile', '-Command', process_cmd],
                               capture_output=True, text=True, timeout=20, check=True, creationflags=NO_WINDOW).stdout.strip()
    if processes:
        raise RuntimeError('Potential competing inference process: ' + processes)
    import ctypes
    class Memory(ctypes.Structure):
        _fields_ = [('length', ctypes.c_ulong), ('load', ctypes.c_ulong)] + [
            (name, ctypes.c_ulonglong) for name in ('total', 'available', 'page_total',
             'page_available', 'virtual_total', 'virtual_available', 'extended')]
    memory = Memory()
    memory.length = ctypes.sizeof(memory)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(memory)):
        raise RuntimeError('Cannot inspect available physical memory')
    if memory.available < 4 * 1024**3:
        raise RuntimeError('Less than 4 GiB available physical memory')
    return dict(gpu=gpu, resident=loaded, competing_processes=processes,
                available_ram_bytes=memory.available, ollama_version=api('/api/version'))


def prepare(label, tasks, root=ROOT, smoke=False):
    if not re.fullmatch(r'[a-zA-Z0-9_-]+', label):
        raise ValueError('Label must contain only letters, digits, underscore or hyphen')
    if len(tasks) != 5:
        raise ValueError('Exactly five tasks are required')
    folder = root / label
    folder.mkdir(parents=True, exist_ok=False)
    entries = schedule(tasks)
    if smoke:
        entries = [entry for entry in entries if entry['task'] == 'graph' and entry['repeat'] == 1]
    save(folder / 'protocol.json', dict(model=MODEL, context=32768, per_call_cap=CAP,
         completion_quota=QUOTA, wall_seconds=WALL, seed=20260922, schedule=entries,
         warmup='one 1-token native request before each run; outside measured budget',
         staging='three separate Pi contexts: read-only plan, implement with plan, audit',
         quota_contract='Reserve remaining quota per request; missing usage stops; overruns are failures',
         prompts=PROMPTS, tasks=tasks, smoke_only=smoke))
    for entry in entries:
        work = folder / 'runs' / entry['label'] / 'workspace'
        work.mkdir(parents=True)
        fixture = tasks[entry['task']]
        for filename, key in [('README.md', 'spec'), ('solution.py', 'code'), ('test_public.py', 'public')]:
            (work / filename).write_text(fixture[key], encoding='ascii')
    return folder, entries


def assistant_text(events):
    texts = []
    messages = []
    for line in events.read_text(encoding='utf-8', errors='replace').splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        message = event.get('message', {})
        if event.get('type') == 'message_end' and message.get('role') == 'assistant':
            messages.append(message)
            texts.extend(c.get('text', '') for c in message.get('content', []) if c.get('type') == 'text')
    return '\n'.join(texts), bool(messages and messages[-1].get('stopReason') == 'stop')


def infrastructure_failure(result):
    quota = result.get('quota_failure')
    cleanups = [phase[key] for phase in result.get('phases', []) for key in ('cleanup', 'owned_tree') if phase.get(key) is not None]
    for key in ('cleanup', 'owned_tree'):
        evaluation_cleanup = result.get('evaluation', {}).get(key)
        if evaluation_cleanup is not None:
            cleanups.append(evaluation_cleanup)
    # A terminated parent does not establish that its descendants exited.
    # Fail closed when Windows denied or timed out process-tree cleanup.
    unverified_tree = any(item.get('returncode') != 0 for item in cleanups)
    return bool(result.get('error') or result.get('cleanup_error')
                or unverified_tree
                or not result.get('inputs_unchanged', True)
                or quota == 'backend_quota_overrun'
                or (quota == 'quota_unknown' and not (result.get('timed_out') or result.get('stopped'))))


def clean_run(phases, expected, timed_out, stopped, quota_failure):
    return (len(phases) == expected and all(p['clean_finish'] for p in phases)
            and not timed_out and not stopped and not quota_failure)


def score_artifact(task, artifact, work, env):
    command = [sys.executable, str(HERE / 'staged_tasks_20260922.py'), task, str(artifact)]
    process = spawn_owned(command, cwd=work, env=env, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, text=True, creationflags=NO_WINDOW)
    try:
        stdout, stderr = process.communicate(timeout=30)
    except subprocess.TimeoutExpired:
        cleanup = stop_owned(process)
        stdout, stderr = process.communicate(timeout=5)
        from staged_tasks_20260922 import cases
        evaluation = {'passed': 0, 'total': len(cases(task)), 'evaluation_timeout': True,
                      'cleanup': cleanup}
        code = 1
    else:
        try:
            evaluation = json.loads(stdout.strip().splitlines()[-1])
            if not isinstance(evaluation, dict) or not {'passed', 'total'} <= evaluation.keys():
                raise ValueError('missing scorer result fields')
            code = process.returncode
        except (ValueError, IndexError):
            # A generated module can call sys.exit/argparse during import.
            # The scorer was validated before inference; preserve this trial's
            # abnormal evaluator exit as a program failure and continue.
            from staged_tasks_20260922 import cases
            evaluation = {'passed': 0, 'total': len(cases(task)),
                          'abnormal_evaluator_exit': process.returncode}
            code = 1
    if OWNED_JOBS:
        evaluation['owned_tree'] = finish_owned(process)
        # Artifact correctness must not be replaced by a cleanup outcome.
        # The caller records lifecycle failure separately from scorer exit code.
    (work / 'evaluation-output.txt').write_text(stdout + stderr, encoding='utf-8')
    return code, evaluation


def execute_run(folder, entry):
    work = folder / 'runs' / entry['label']
    workspace = work / 'workspace'
    result = dict(entry, phases=[], started=datetime.datetime.now(datetime.timezone.utc).isoformat())
    budget = Budget()
    server = http.server.HTTPServer(('127.0.0.1', 0), Relay)
    server.folder, server.budget, server.stop = work, budget, folder / 'STOP'
    server.deadline = float('inf')
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        result['preflight'] = preflight()
        frozen = json.loads((folder / 'model.json').read_text())['tag']['digest']
        current = [m for m in api('/api/tags')['models'] if m['name'].split(':')[0] == MODEL]
        if len(current) != 1 or current[0]['digest'] != frozen:
            raise RuntimeError('Pinned model digest changed')
        warm = time.monotonic()
        result['warmup'] = api('/api/generate', {'model': MODEL, 'prompt': 'Reply OK.', 'stream': False,
             'think': False, 'keep_alive': '5m', 'options': {'num_ctx': 32768, 'num_predict': 1}}, timeout=120)
        result['warmup_seconds'] = time.monotonic() - warm
        result['placement'] = api('/api/ps')
        config = {'providers': {'lab': {'baseUrl': f'http://127.0.0.1:{server.server_port}/v1',
            'api': 'openai-completions', 'apiKey': 'local-only',
            'compat': {'supportsDeveloperRole': False, 'supportsReasoningEffort': False,
                       'maxTokensField': 'max_tokens', 'supportsStore': False},
            'models': [{'id': MODEL, 'contextWindow': 32768, 'maxTokens': CAP, 'reasoning': False,
                        'samplingParams': {'temperature': 0, 'max_tokens': CAP, 'reasoning_effort': 'none'}}]}}}
        save(work / 'config/models.json', config)
        save(work / 'config/settings.json', {'cacheWarming': 'off', 'compaction': {'enabled': True,
             'reserveTokens': CAP, 'keepRecentTokens': 4096}, 'retry': {'enabled': False}})
        result['config_sha256'] = {p.name: sha(p) for p in (work / 'config').iterdir()}
        env = {k: v for k, v in os.environ.items() if not any(s in k.upper() for s in ('API_KEY', 'AUTH_TOKEN', 'OAUTH_TOKEN'))}
        env.update(PI_CODING_AGENT_DIR=str(work / 'config'), PI_OFFLINE='1', PI_TELEMETRY='0', PYTHONIOENCODING='utf-8')
        if entry.get('loop_mode'):
            extension = work / 'config/repeat_guard.mjs'
            shutil.copy2(HERE / 'repeat_guard_20260922.mjs', extension)
            result['config_sha256'][extension.name] = sha(extension)
            env['LAB_LOOP_MODE'] = entry['loop_mode']
        start = time.monotonic()
        server.deadline = start + WALL
        initial_hash = sha(workspace / 'solution.py')
        plan = ''
        for phase in (['one-shot'] if entry['treatment'] == 'one-shot' else ['plan', 'implement', 'audit']):
            if budget.failure or time.monotonic() >= server.deadline or server.stop.exists():
                break
            prompt = PROMPTS[phase] + (plan if phase == 'implement' else '')
            (work / f'{phase}-prompt.txt').write_text(prompt, encoding='utf-8')
            command = ['node', str(PI), '--offline', '--no-extensions', '--no-skills', '--no-context-files',
                       '--no-prompt-templates', '--no-themes', '--no-session', '--provider', 'lab', '--model', MODEL,
                       '--tools', 'read' if phase == 'plan' else 'read,write,edit,powershell', '--mode', 'json', '-p', prompt]
            if entry.get('loop_mode'):
                command += ['--extension', str(extension)]
                env['LAB_LOOP_LOG'] = str(work / f'{phase}-guard.jsonl')
            events = work / f'{phase}-events.jsonl'
            outcome = {'phase': phase}
            with events.open('w', encoding='utf-8') as out, (work / f'{phase}-stderr.txt').open('w', encoding='utf-8') as err:
                process = spawn_owned(command, cwd=workspace, env=env, stdout=out, stderr=err, stdin=subprocess.DEVNULL, creationflags=NO_WINDOW)
                save(work / f'{phase}-process.json', {'pid': process.pid, 'command': command})
                try:
                    while process.poll() is None:
                        if budget.failure or server.stop.exists() or time.monotonic() >= server.deadline:
                            outcome['interrupted'] = budget.failure or ('stop' if server.stop.exists() else 'timeout')
                            outcome['cleanup'] = stop_owned(process)
                            break
                        artifact = workspace / 'solution.py'
                        if artifact.exists() and not (work / 'first-artifact.py').exists() and sha(artifact) != initial_hash:
                            shutil.copy2(artifact, work / 'first-artifact.py')
                        time.sleep(0.2)
                finally:
                    if process.poll() is None:
                        outcome['cleanup'] = stop_owned(process)
                outcome['exit_code'] = process.returncode
                if OWNED_JOBS:
                    outcome['owned_tree'] = finish_owned(process)
            text, clean = assistant_text(events)
            outcome['clean_finish'] = clean and process.returncode == 0 and not outcome.get('interrupted')
            if outcome.get('owned_tree', {}).get('active_before'):
                outcome['clean_finish'] = False
            if entry.get('loop_mode'):
                guard_path = work / f'{phase}-guard.jsonl'
                guard_events = [json.loads(line) for line in guard_path.read_text().splitlines()] if guard_path.exists() else []
                if not any(e.get('event') == 'ready' and e.get('mode') == entry['loop_mode'] for e in guard_events):
                    raise RuntimeError('Required repeat-guard extension did not initialize')
                outcome['guard_blocks'] = sum(bool(e.get('block')) for e in guard_events)
                outcome['guard_terminated'] = any(e.get('terminate') for e in guard_events)
                outcome['clean_finish'] = outcome['clean_finish'] and not outcome['guard_terminated']
            result['phases'].append(outcome)
            if phase == 'plan':
                plan = text
            if not outcome['clean_finish']:
                break
        result['seconds'] = time.monotonic() - start
        result['timed_out'] = any(p.get('interrupted') == 'timeout' for p in result['phases']) or time.monotonic() >= server.deadline
        result['stopped'] = server.stop.exists()
        artifact = workspace / 'solution.py'
        if artifact.exists():
            shutil.copy2(artifact, work / 'final-artifact.py')
            if not (work / 'first-artifact.py').exists() and sha(artifact) != initial_hash:
                shutil.copy2(artifact, work / 'first-artifact.py')
                result['first_artifact_observed_at_final'] = True
        score_code, evaluation = score_artifact(entry['task'], artifact, work, env)
        save(work / 'evaluation.json', evaluation)
        result['evaluation'] = evaluation
        result['clean_finish'] = clean_run(result['phases'], 1 if entry['treatment'] == 'one-shot' else 3,
                                          result['timed_out'], result['stopped'], budget.failure)
        if evaluation.get('owned_tree', {}).get('active_before') or evaluation.get('owned_tree', {}).get('returncode', 0) != 0:
            result['clean_finish'] = False
        result['correct'] = score_code == 0 and evaluation['passed'] == evaluation['total']
        result['success'] = result['clean_finish'] and result['correct']
    except Exception as exc:
        result['error'] = repr(exc)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=35)
        result.update(completion_tokens=budget.used, quota_failure=budget.failure)
        result['completion_tokens_complete'] = budget.failure != 'quota_unknown'
        if budget.failure:
            result['clean_finish'] = False
            result['success'] = False
        # Only our alias, and only if this run reached warmup, may be unloaded.
        if 'preflight' in result:
            try:
                result['unload'] = api('/api/generate', {'model': MODEL, 'keep_alive': 0}, timeout=30)
                result['remaining_models'] = api('/api/ps')
                if result['remaining_models'].get('models'):
                    result['cleanup_error'] = 'Model remains resident; stop before another run'
            except Exception as exc:
                result['cleanup_error'] = repr(exc)
        save(work / 'result.json', result)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--label', required=True)
    parser.add_argument('--run', action='store_true', help='Execute inference; default only prepares')
    parser.add_argument('--smoke', action='store_true', help='Only the graph repeat-1 pair; diagnostic, excluded from full results')
    args = parser.parse_args(argv)
    from staged_tasks_20260922 import TASKS
    folder, entries = prepare(args.label, TASKS, smoke=args.smoke)
    sources = [Path(__file__), HERE / 'staged_tasks_20260922.py', HERE / 'night_tasks_20260916.py',
               HERE / 'validate_staged_tasks_20260922.py', HERE / 'test_compare_staging_20260922.py']
    (folder / 'source').mkdir()
    for path in sources:
        shutil.copy2(path, folder / 'source' / path.name)
    identity = {str(p): sha(p) for p in sources + [folder / 'protocol.json']}
    if PI.exists():
        identity[str(PI)] = sha(PI)
    save(folder / 'identity.json', {'files': identity,
         'pi_sha256': sha(PI) if PI.exists() else None, 'python': sys.version})
    if not args.run:
        print(json.dumps({'prepared': str(folder), 'runs': len(entries), 'inference': False}))
        return
    # Run protocol regressions before loading a model; this is also the serial
    # queue's integration gate after any ongoing Go timing work has completed.
    validation = subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', str(HERE),
                                 '-p', 'test_compare_staging_20260922.py'], capture_output=True, text=True, timeout=60, creationflags=NO_WINDOW)
    (folder / 'protocol-tests.txt').write_text(validation.stdout + validation.stderr, encoding='utf-8')
    if validation.returncode:
        raise RuntimeError('Protocol regression failed before inference')
    validation = subprocess.run([sys.executable, str(HERE / 'validate_staged_tasks_20260922.py')],
                                capture_output=True, text=True, timeout=60, creationflags=NO_WINDOW)
    (folder / 'scorer-validation.json').write_text(validation.stdout, encoding='utf-8')
    if validation.returncode:
        raise RuntimeError('Scorer control failed before inference: ' + validation.stderr)
    if os.name != 'nt' or not PI.exists():
        raise RuntimeError('Execution requires Windows and the existing isolated Pi 0.86.1 install')
    lock = ROOT / 'RUNNING.lock'
    with lock.open('x', encoding='ascii') as stream:
        stream.write(json.dumps({'pid': os.getpid(), 'folder': str(folder)}))
    try:
        save(folder / 'preflight.json', preflight())
        tags = api('/api/tags')
        matches = [m for m in tags['models'] if m['name'].split(':')[0] == MODEL]
        if len(matches) != 1:
            raise RuntimeError('Pinned alias must already exist uniquely')
        save(folder / 'model.json', {'tag': matches[0], 'show': api('/api/show', {'model': MODEL})})
        results = []
        for entry in entries:
            if (folder / 'STOP').exists():
                break
            if any(sha(Path(path)) != expected for path, expected in identity.items()):
                raise RuntimeError('Pinned experiment input changed before run')
            print('Starting', entry['label'], flush=True)
            result = execute_run(folder, entry)
            result['inputs_unchanged'] = all(sha(Path(path)) == expected for path, expected in identity.items())
            results.append(result)
            save(folder / 'results.json', results)
            print(entry['label'], 'success=', result.get('success'), 'score=',
                  result.get('evaluation', {}).get('passed'), '/', result.get('evaluation', {}).get('total'),
                  'tokens=', result.get('completion_tokens'), 'seconds=', result.get('seconds'), flush=True)
            save(folder / 'status.json', {'last_run': entry['label'], 'result': result})
            if infrastructure_failure(result):
                break
    finally:
        lock.unlink()


if __name__ == '__main__':
    main()
