"""Serial continuation queue with saved evidence and explicit acceptance gates.

Run only after the replacement Go smoke and local validation finish. Each child
owns a new output directory. STOP in this queue directory is checked between
jobs; use the active child's STOP for cancellation within a job.
"""
import json
from pathlib import Path
import subprocess
import sys
import time

LAB = Path(__file__).resolve().parents[1]
GO = LAB / 'goproverbs'
BENCH = Path.home() / 'ai_bench'
QUEUE = BENCH / 'continuation-20260922'
FROZEN = GO / 'results/direct-20260922/source-v2'
RUNTIME = BENCH / 'katago'


def save(path, value):
    path.write_text(json.dumps(value, indent=2), encoding='ascii')


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def arena_gate(path, expected):
    record = read(path / 'manifest.json')
    assert record['status'] == 'complete' and record['hashes_unchanged'], path
    assert len(record['games']) == expected and all(g['finished'] for g in record['games']), path
    assert not record['broker']['errors'], record['broker']
    for game in record['games']:
        for role in ('policy', 'search'):
            if role in game['roles']:
                assert game['roles'][role]['fallbacks'] == 0, (path, role)
    return record


def main():
    smoke = arena_gate(GO / 'results/direct-20260922/smoke-v2', 6)
    nn = [g['roles']['NN'] for g in smoke['games'] if 'NN' in g['roles']]
    retention = sum(r['external_complete_rounds'] for r in nn) / sum(r['decisions'] for r in nn)
    matchups = ['NH:policy', 'NH:search']
    if retention >= .8:
        matchups.insert(0, 'NH:NN')
    QUEUE.mkdir(parents=True, exist_ok=False)
    state = {'status': 'running', 'nn_smoke_retention': retention,
             'eligible_matchups': matchups, 'jobs': []}
    save(QUEUE / 'status.json', state)
    with (QUEUE / 'RUNNING.lock').open('x', encoding='ascii') as lock:
        import os
        lock.write(str(os.getpid()))

    def run(name, command, cwd, output):
        if (QUEUE / 'STOP').exists():
            raise InterruptedError('queue STOP requested')
        row = {'name': name, 'command': [str(c) for c in command], 'cwd': str(cwd),
               'output': str(output), 'status': 'running', 'started': time.time()}
        state['jobs'].append(row)
        save(QUEUE / 'status.json', state)
        print('QUEUE starting', name, flush=True)
        started = time.perf_counter()
        with (QUEUE / (name + '.log')).open('w', encoding='utf-8') as log:
            process = subprocess.Popen(row['command'], cwd=cwd, stdout=log, stderr=subprocess.STDOUT)
            row['pid'] = process.pid
            save(QUEUE / 'status.json', state)
            code = process.wait()
        row.update(status='complete' if code == 0 else 'failed', exit_code=code,
                   seconds=time.perf_counter() - started)
        save(QUEUE / 'status.json', state)
        print('QUEUE finished', name, 'exit', code, flush=True)
        if code:
            raise RuntimeError(f'{name} failed; inspect its saved log')

    def arena(name, cpu=False, pairs=10, selected=matchups):
        output = GO / 'results/direct-20260922' / name
        run(name, [sys.executable, FROZEN / 'benchmarks/direct_arena.py',
            '--katago', RUNTIME / ('eigenavx2-1.18.1' if cpu else 'opencl-1.18.1') / 'katago.exe',
            '--model', RUNTIME / ('lionffen_b6c64_3x3_v10.txt.gz' if cpu else 'kata1-b10c128-s919229184-d169515535.txt.gz'),
            '--exe', FROZEN / 'goproverbs.exe', '--profile', FROZEN / 'profiles/baseline.weights',
            '--openings', GO / 'results/direct-20260922' / ('cpu-openings.json' if cpu else 'expansion-openings.json'),
            '--pairs', str(pairs), '--output', output, '--matchups', *selected,
            *(['--cpu'] if cpu else [])], GO, output)
        arena_gate(output, pairs * len(selected) * 2)

    try:
        arena('expansion-v2')
        arena('cpu-small-v2', cpu=True, pairs=2, selected=['NH:HH'])
        for budget in (50, 100, 200, 400):
            output = GO / 'results/direct-20260922' / f'budget-{budget}-v2'
            run(f'budget-{budget}', [sys.executable, FROZEN / 'benchmarks/roadmap.py', 'probe',
                '--katago', RUNTIME / 'opencl-1.18.1/katago.exe',
                '--model', RUNTIME / 'kata1-b10c128-s919229184-d169515535.txt.gz',
                '--exe', FROZEN / 'goproverbs.exe', '--profile', FROZEN / 'profiles/baseline.weights',
                '--corpus', GO / 'results/roadmap-20260921/corpus/positions.json',
                '--openings', GO / 'results/direct-20260922/smoke-openings.json',
                '--output', output, '--positions', '8', '--modes', 'NH', 'NN', '--time-ms', str(budget)], GO, output)
            result = read(output / 'manifest.json')
            assert result['status'] == 'complete' and not result['broker_errors'], output
        for label, diagnostic in [('smoke-v1', True), ('main-v1', False)]:
            output = BENCH / 'staging-20260922' / label
            run('llm-' + label, [sys.executable, LAB / 'benchmarks/compare_staging_20260922.py',
                '--label', label, '--run', *(['--smoke'] if diagnostic else [])], LAB, output)
            results = read(output / 'results.json')
            assert len(results) == (2 if diagnostic else 30), (label, len(results))
            assert all(r['inputs_unchanged'] and not r.get('error') and not r.get('cleanup_error') for r in results), label
            if diagnostic:
                assert all(r.get('clean_finish') and r['completion_tokens'] > 0 and not r.get('quota_failure') for r in results), 'Pi integration smoke did not pass'
        state['status'] = 'complete'
    except BaseException as exc:
        state.update(status='stopped' if isinstance(exc, InterruptedError) else 'failed', error=repr(exc))
        raise
    finally:
        save(QUEUE / 'status.json', state)
        (QUEUE / 'RUNNING.lock').unlink()


if __name__ == '__main__':
    main()
