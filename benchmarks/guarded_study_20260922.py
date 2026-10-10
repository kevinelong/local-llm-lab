"""Fresh, fixed schedules for the overnight guard intervention; no historical reuse."""
import argparse
import json
import os
from pathlib import Path
import random
import time
import compare_staging_20260922 as base
from staged_tasks_20260922 import TASKS


def entries_for(suite):
    if suite in ('smoke', 'staging'):
        entries = base.schedule(TASKS)
        if suite == 'smoke':
            entries = [r for r in entries if r['task'] == 'graph' and r['repeat'] == 1]
        return [{**r, 'loop_mode': 'guard', 'label': r['label'] + '-guard'} for r in entries]
    rng = random.Random(260922)
    blocks = [(task, repeat) for task in ('graph', 'intervals') for repeat in range(1, 4)]
    rng.shuffle(blocks)
    entries = []
    for task, repeat in blocks:
        modes = ['observe', 'guard']
        rng.shuffle(modes)
        entries.extend(dict(task=task, repeat=repeat, treatment='one-shot', loop_mode=mode,
                            label=f'{task}-{repeat}-one-shot-{mode}') for mode in modes)
    return entries


def report(folder, rows, status):
    lines = [f'# {folder.name}: {status}', '',
             '| Trial | Correct | Clean | Success | Seconds | Tokens complete | Guard blocks |',
             '|---|---|---|---|---:|---|---:|']
    for r in rows:
        seconds = r.get('seconds', 0)
        lines.append(f"| {r['label']} | {r.get('correct', False)} | {r.get('clean_finish', False)} | {r.get('success', False)} | {seconds:.1f} | {r.get('completion_tokens_complete', False)} | {sum(p.get('guard_blocks', 0) for p in r['phases'])} |")
    lines += ['', 'Correctness and clean agent completion are separate. Guard-forced termination is failure.',
              'Three repeats are technical repeats at temperature zero, not independent task samples.',
              'Smoke is excluded from the main comparisons; task families were already used for development.', '']
    (folder / 'REPORT.md').write_text('\n'.join(lines), encoding='ascii')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--suite', choices=('smoke', 'ablation', 'staging'), required=True)
    args = parser.parse_args()
    base.OWNED_JOBS = True
    entries = entries_for(args.suite)
    original_schedule = base.schedule
    base.schedule = lambda _: entries
    try:
        folder, entries = base.prepare(args.suite, TASKS, root=args.root / 'staging')
    finally:
        base.schedule = original_schedule
    protocol = json.loads((folder / 'protocol.json').read_text())
    protocol.update(suite=args.suite, extension='repeat_guard_20260922.mjs',
                    repeated_command='same canonical powershell arguments and solution.py hash; first three allowed; fourth blocked with warning; fifth terminates',
                    original_main_comparison='not resumed; new intervention treatment',
                    extension_control='observe loads the same extension without blocking')
    base.save(folder / 'protocol.json', protocol)
    files = list(base.HERE.glob('*.py')) + list(base.HERE.glob('*.mjs')) + [folder / 'protocol.json', base.PI]
    identity = {str(path): base.sha(path) for path in files}
    base.save(folder / 'identity.json', identity)
    lock = base.ROOT / 'RUNNING.lock'
    rows, state = [], {'status': 'running', 'expected_runs': len(entries), 'runs': 0}
    with lock.open('x') as stream:
        stream.write(json.dumps({'pid': os.getpid(), 'folder': str(folder)}))
    try:
        base.save(folder / 'preflight.json', base.preflight())
        tags = base.api('/api/tags')
        matches = [m for m in tags['models'] if m['name'].split(':')[0] == base.MODEL]
        if len(matches) != 1:
            raise RuntimeError('Missing unique existing model alias')
        base.save(folder / 'model.json', {'tag': matches[0], 'show': base.api('/api/show', {'model': base.MODEL})})
        for entry in entries:
            if (args.root / 'STOP').exists() or (folder / 'STOP').exists():
                state['status'] = 'stopped'
                break
            if any(base.sha(Path(p)) != digest for p, digest in identity.items()):
                raise RuntimeError('Frozen input changed')
            state.update(active=entry['label'], runs=len(rows), updated=time.time())
            base.save(folder / 'status.json', state)
            print('Starting', entry['label'], flush=True)
            result = base.execute_run(folder, entry)
            result['inputs_unchanged'] = all(base.sha(Path(p)) == digest for p, digest in identity.items())
            rows.append(result)
            base.save(folder / 'results.json', rows)
            report(folder, rows, state['status'])
            print(entry['label'], result.get('success'), result.get('seconds'), flush=True)
            if base.infrastructure_failure(result):
                raise RuntimeError('Infrastructure failure; inspect saved result')
        else:
            state['status'] = 'complete'
    except BaseException as exc:
        state.update(status='failed', error=repr(exc))
        raise
    finally:
        state.update(runs=len(rows), updated=time.time())
        base.save(folder / 'status.json', state)
        report(folder, rows, state['status'])
        lock.unlink()


if __name__ == '__main__':
    main()
