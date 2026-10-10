"""Prepare, validate and launch a frozen, bounded local overnight research queue."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

LAB = Path('C:/Users/kevin/local-llm-lab')
BENCH = Path('C:/Users/kevin/ai_bench')
DEFAULT_ROOT = BENCH / 'overnight-followup-20260922'
NO_WINDOW = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
SOURCES = ['compare_staging_20260922.py', 'staged_tasks_20260922.py', 'night_tasks_20260916.py',
           'validate_staged_tasks_20260922.py', 'test_compare_staging_20260922.py',
           'repeat_guard_20260922.mjs', 'test_repeat_guard_20260922.mjs',
           'test_pi_guard_runtime_20260922.py', 'check_owned_cleanup_20260922.py',
           'guarded_study_20260922.py', 'compare_bonsai_packing_20260922.py',
           'test_compare_bonsai_packing_20260922.py', 'overnight_research_20260922.py']
SOURCES += ['owned_process_20260922.py', 'test_guarded_study_20260922.py']


def save(path, data):
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(data, indent=2), encoding='ascii')
    os.replace(temporary, path)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(root):
    pinned = json.loads((root / 'manifest.json').read_text())
    for path, expected in pinned.items():
        if digest(Path(path)) != expected:
            raise RuntimeError('Pinned input changed: ' + path)


def report(root, state):
    lines = ['# Overnight follow-up, September 22', '', f"Queue status: {state['status']}.",
             f"Updated UTC: {datetime.datetime.now(datetime.timezone.utc).isoformat()}.", '',
             'STOP: create a file named STOP in this directory. Only this queue\'s jobs will be stopped.', '',
             '| Job | Status | Exit |', '|---|---|---:|']
    for job in state.get('jobs', []):
        lines.append(f"| {job['name']} | {job['status']} | {job.get('exit_code', '')} |")
    lines += ['', f"Guarded staging gate: {state.get('staging_gate', 'not evaluated')}.", '']
    for folder in sorted((root / 'staging').glob('*')) if (root / 'staging').exists() else []:
        path = folder / 'results.json'
        if not path.exists():
            continue
        try:
            rows = json.loads(path.read_text())
        except json.JSONDecodeError:
            continue  # Child may be replacing its latest result; retry next poll.
        lines += [f'## {folder.name}', '', f'{len(rows)} recorded trials. See staging/{folder.name}/REPORT.md.', '',
                  '| Treatment / guard mode | Runs | Correct | Clean | Success |', '|---|---:|---:|---:|---:|']
        groups = {}
        for row in rows:
            groups.setdefault((row['treatment'], row['loop_mode']), []).append(row)
        for key, values in groups.items():
            lines.append(f"| {' / '.join(key)} | {len(values)} | {sum(bool(r.get('correct')) for r in values)} | {sum(bool(r.get('clean_finish')) for r in values)} | {sum(bool(r.get('success')) for r in values)} |")
        lines += ['', 'These totals are descriptive; compare paired outcomes within task. Technical repeats are not independent tasks.', '']
    lines += ['Smoke is diagnostic only and never pooled. A guard-forced stop is failure, even if the artifact is correct.',
              'The original unguarded 30-run staging comparison is still held. Any staging batch here is a new guarded treatment.',
              'CPU runs use 600-second socket limits and separate labels; do not pool with the earlier 120-second attempts.', '']
    (root / 'REPORT.md').write_text('\n'.join(lines), encoding='ascii')


def prepare(root):
    root.mkdir(parents=True, exist_ok=False)
    source = root / 'source'
    source.mkdir()
    for name in SOURCES:
        shutil.copy2(LAB / 'benchmarks' / name, source / name)
    shutil.copy2(LAB / 'OVERNIGHT-PLAN-2026-09-22.md', root / 'PROTOCOL.md')
    paths = list(source.iterdir()) + [root / 'PROTOCOL.md', BENCH / 'pi-lab-0861/node_modules/@earendil-works/pi-coding-agent/dist/bundle/cli.js']
    save(root / 'manifest.json', {str(p): digest(p) for p in paths})
    save(root / 'status.json', {'status': 'prepared', 'jobs': [], 'max_hours': 8})
    report(root, {'status': 'prepared', 'jobs': []})
    print(str(root))


def validate(root):
    verify(root)
    source = root / 'source'
    checks = [
        ['node', str(source / 'test_repeat_guard_20260922.mjs')],
        [sys.executable, '-m', 'unittest', 'discover', '-s', str(source), '-p', 'test_compare_staging_20260922.py'],
        [sys.executable, '-m', 'unittest', 'discover', '-s', str(source), '-p', 'test_compare_bonsai_packing_20260922.py'],
        [sys.executable, '-m', 'unittest', 'discover', '-s', str(source), '-p', 'test_guarded_study_20260922.py'],
        [sys.executable, str(source / 'validate_staged_tasks_20260922.py')],
        [sys.executable, str(source / 'test_pi_guard_runtime_20260922.py')],
        [sys.executable, str(source / 'check_owned_cleanup_20260922.py')],
    ]
    results = []
    for index, command in enumerate(checks):
        with (root / f'validation-{index}.log').open('w', encoding='utf-8') as out:
            process = subprocess.Popen(command, cwd=source, stdout=out, stderr=subprocess.STDOUT, creationflags=NO_WINDOW)
            try:
                code = process.wait(timeout=180)
            except subprocess.TimeoutExpired:
                subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'], capture_output=True, creationflags=NO_WINDOW)
                raise
        results.append({'command': command, 'exit_code': code})
        save(root / 'validation.json', {'passed': False, 'checks': results})
        if code:
            raise RuntimeError(f'Validation {index} failed; inspect its log')
    verify(root)
    save(root / 'validation.json', {'passed': True, 'checks': results, 'manifest_sha256': digest(root / 'manifest.json')})
    print('All offline and actual-Pi/owned-tree integration controls passed.', flush=True)


def worker(root):
    sys.path.insert(0, str(root / 'source'))
    import compare_staging_20260922 as base
    import compare_bonsai_packing_20260922 as packing
    base.OWNED_JOBS = True
    verify(root)
    validation = json.loads((root / 'validation.json').read_text())
    if not validation['passed'] or validation['manifest_sha256'] != digest(root / 'manifest.json'):
        raise RuntimeError('Matching validation required')
    lock = root / 'RUNNING.lock'
    with lock.open('x') as handle:
        handle.write(json.dumps({'pid': os.getpid()}))
    state = {'status': 'running', 'pid': os.getpid(), 'started': time.time(), 'jobs': [], 'max_hours': 8}
    deadline = time.monotonic() + 8 * 3600
    source = root / 'source'

    def record():
        save(root / 'status.json', state)
        report(root, state)

    def run(name, command, output, max_seconds, cpu=False):
        verify(root)
        if (root / 'STOP').exists() or time.monotonic() >= deadline:
            raise InterruptedError('Overnight STOP or eight-hour limit')
        # Global advisory locks and live resources are checked before every job.
        go_locks = list((LAB / 'goproverbs/results').glob('**/RUNNING.lock'))
        if go_locks:
            raise RuntimeError('Go workload lock(s) present: ' + str(go_locks))
        packing.preflight()
        base.preflight()
        row = {'name': name, 'status': 'running', 'command': command, 'output': str(output), 'started': time.time()}
        state['jobs'].append(row)
        record()
        with (root / f'{name}.log').open('w', encoding='utf-8') as log:
            process = base.spawn_owned(command, cwd=source, stdout=log, stderr=subprocess.STDOUT, creationflags=NO_WINDOW)
            row['pid'] = process.pid
            record()
            start = time.monotonic()
            cancel_at = None
            try:
                while process.poll() is None:
                    cancel = (root / 'STOP').exists() or time.monotonic() >= deadline or time.monotonic()-start > max_seconds
                    if cancel and cancel_at is None:
                        cancel_at = time.monotonic()
                        output.mkdir(parents=True, exist_ok=True)
                        (output / 'STOP').touch()
                    if cancel_at is not None and time.monotonic()-cancel_at > 75:
                        row['forced_cleanup'] = base.stop_owned(process)
                        if not cpu:
                            row['emergency_unload'] = base.api('/api/generate', {'model': base.MODEL, 'keep_alive': 0}, timeout=30)
                        break
                    record()
                    time.sleep(3)
            finally:
                if process.poll() is None:
                    row['exception_cleanup'] = base.stop_owned(process)
                    if not cpu:
                        row['emergency_unload'] = base.api('/api/generate', {'model': base.MODEL, 'keep_alive': 0}, timeout=30)
                row['owned_tree'] = base.finish_owned(process)
        row.update(exit_code=process.poll(), status='complete' if process.returncode == 0 else 'failed', seconds=time.monotonic()-start)
        record()
        if row['owned_tree']['returncode'] != 0 or (row['owned_tree']['active_before'] and cancel_at is None):
            raise RuntimeError('Job exited with unclean descendant lifecycle')
        if cancel_at is not None:
            raise InterruptedError('Job stopped or exceeded time allowance')
        verify(root)
        if cpu and process.returncode:
            records = [json.loads(p.read_text()) for p in output.glob('*/result.json')]
            allowed = len(records) == 1 and records[0].get('owned_server_exited') and 'TimeoutError' in records[0].get('error', '')
            if allowed:
                packing.preflight()
                row['status'] = 'bounded_control_timeout'
                record()
                return
        if process.returncode:
            raise RuntimeError(name + ' failed; stopping unattended work')

    try:
        record()
        for suite, limit in [('smoke', 1000), ('ablation', 6000)]:
            run(suite, [sys.executable, str(source / 'guarded_study_20260922.py'), '--root', str(root), '--suite', suite], root / 'staging' / suite, limit)
            if suite == 'smoke':
                rows = json.loads((root / 'staging/smoke/results.json').read_text())
                passed = len(rows) == 2 and all(r.get('clean_finish') and r.get('completion_tokens_complete') and r.get('completion_tokens', 0) > 0 and r.get('inputs_unchanged') and not base.infrastructure_failure(r) for r in rows)
                state['staging_gate'] = 'passed' if passed else 'held: smoke did not finish cleanly'
                record()
        if state['staging_gate'] == 'passed':
            run('staging', [sys.executable, str(source / 'guarded_study_20260922.py'), '--root', str(root), '--suite', 'staging'], root / 'staging/staging', 14000)
        for model in ('PTQ1', 'PQ2'):
            label = 'overnight-' + model.lower() + '-600s-v1'
            output = BENCH / 'packing-20260922' / label
            run('cpu-' + model, [sys.executable, str(source / 'compare_bonsai_packing_20260922.py'), '--label', label,
                '--run', '--cpu', '--only', f'{model}-ctx8192-ngl0', '--request-timeout', '600'], output, 3600, cpu=True)
        state['status'] = 'complete'
    except InterruptedError as exc:
        state.update(status='stopped', error=repr(exc))
    except BaseException as exc:
        state.update(status='failed', error=repr(exc))
    finally:
        state['finished'] = time.time()
        try:
            state['final_models'] = base.api('/api/ps')
            state['final_model_processes'] = packing.active_processes()
            if state['final_models'].get('models') or state['final_model_processes']:
                state.update(status='failed', cleanup_error='Model resources remain; inspect before further inference')
        except Exception as exc:
            state.update(status='failed', cleanup_error=repr(exc))
        lock.unlink()
        record()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'validate', 'launch', 'worker'))
    parser.add_argument('--root', type=Path, default=DEFAULT_ROOT)
    args = parser.parse_args()
    root = args.root.resolve()
    root.relative_to(BENCH.resolve())
    if args.action == 'prepare':
        prepare(root)
    elif args.action == 'validate':
        validate(root)
    elif args.action == 'worker':
        worker(root)
    else:
        verify(root)
        if (root / 'RUNNING.lock').exists() or (root / 'launched.json').exists():
            raise RuntimeError('Refusing duplicate launch')
        if not json.loads((root / 'validation.json').read_text())['passed']:
            raise RuntimeError('Run validation first')
        with (root / 'worker.log').open('w', encoding='utf-8') as log:
            command = [sys.executable, str(root / 'source/overnight_research_20260922.py'), 'worker', '--root', str(root)]
            process = subprocess.Popen(command, cwd=root / 'source', stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                                       creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP)
        save(root / 'launched.json', {'pid': process.pid, 'command': command, 'time': time.time()})
        print(json.dumps({'pid': process.pid, 'root': str(root)}))


if __name__ == '__main__':
    main()
