"""Frozen prompt-only completion experiment. New directories; serial owned jobs."""
import argparse
import json
import os
from pathlib import Path
import random
import shutil
import sys
import time
import compare_staging_20260922 as base
import guarded_study_20260922 as previous
import overnight_research_20260922 as overnight
from staged_tasks_20260922 import TASKS

ROOT = Path('C:/Users/kevin/ai_bench/completion-20260923-v1')
INSTRUCTION = (' Completion procedure: after your final repair, run python test_public.py. '
    'Collect any additional edge-case assertions in one diagnostic.py file and run that file. '
    'A successful command with no output is not a failure. Catch expected exceptions in your '
    'diagnostic assertions so an expected rejection is reported as a passing check. '
    'Do not rerun an unchanged successful check. If a check fails, repair the relevant code '
    'or diagnostic before rerunning it. Once public tests and your finite edge-case checks '
    'pass, stop using tools and give your final summary. If you cannot resolve a failure, '
    'finish with an explicit description of the unresolved issue instead of repeating it.')


def entries_for(suite):
    if suite == 'ablation':
        rng = random.Random(260923)
        blocks = [(task, repeat) for task in ('graph', 'intervals') for repeat in range(1, 4)]
        rng.shuffle(blocks)
        entries = []
        for task, repeat in blocks:
            modes = ['baseline', 'completion']
            rng.shuffle(modes)
            entries += [dict(task=task, repeat=repeat, treatment='one-shot', prompt_mode=mode,
                             loop_mode='observe', label=f'{task}-{repeat}-one-shot-{mode}') for mode in modes]
        return entries
    entries = base.schedule(TASKS)
    if suite == 'smoke':
        entries = [e for e in entries if e['task'] in ('graph', 'intervals') and e['repeat'] == 1]
    return [dict(e, prompt_mode='completion', loop_mode='observe', label=e['label']+'-completion') for e in entries]


def clean(row):
    return bool(row.get('success') and row.get('completion_tokens_complete')
                and row.get('completion_tokens', 0) > 0 and row.get('inputs_unchanged')
                and not base.infrastructure_failure(row))


def eligible(smoke, ablation):
    if len(smoke) != 4 or not all(clean(r) for r in smoke) or len(ablation) != 12:
        return False
    candidate = [r for r in ablation if r['prompt_mode'] == 'completion']
    if len(candidate) != 6 or not all(r.get('correct') for r in candidate) or sum(clean(r) for r in candidate) < 5:
        return False
    return all(sum(clean(r) for r in candidate if r['task'] == task) >=
               sum(clean(r) for r in ablation if r['task'] == task and r['prompt_mode'] == 'baseline')
               for task in ('graph', 'intervals'))


def report(root, state):
    lines = ['# Completion follow-up, September 23', '', 'Status: '+state['status'], '',
             'Staging gate: '+state.get('staging_gate', 'pending'), '',
             '| Suite / task / prompt / treatment | Runs | Correct | Clean | Success |',
             '|---|---:|---:|---:|---:|']
    for suite in ('smoke', 'ablation', 'staging'):
        path = root / suite / 'results.json'
        if not path.exists():
            continue
        rows = json.loads(path.read_text())
        keys = sorted({(r['task'], r['prompt_mode'], r['treatment']) for r in rows})
        for key in keys:
            values = [r for r in rows if (r['task'], r['prompt_mode'], r['treatment']) == key]
            counts = [sum(bool(r.get(field)) for r in values) for field in ('correct', 'clean_finish', 'success')]
            lines.append(f"| {suite} / {' / '.join(key)} | {len(values)} | {' | '.join(map(str, counts))} |")
        if suite == 'ablation':
            lines += ['', 'Paired outcomes below are completion minus baseline; incomplete pairs omitted.', '',
                      '| Task / repeat | Correct delta | Clean delta | Seconds delta |', '|---|---:|---:|---:|']
            for task in ('graph', 'intervals'):
                for repeat in range(1, 4):
                    pair = {r['prompt_mode']:r for r in rows if r['task']==task and r['repeat']==repeat}
                    if len(pair) != 2:
                        continue
                    a, b = pair['completion'], pair['baseline']
                    lines.append(f"| {task} / {repeat} | {int(a.get('correct',False))-int(b.get('correct',False))} | {int(a.get('clean_finish',False))-int(b.get('clean_finish',False))} | {a.get('seconds',0)-b.get('seconds',0):.1f} |")
            lines += ['', 'Three technical repeats on two development tasks do not establish generalization.', '']
    lines += ['', 'No forced guard termination is enabled in either arm. Fixed model/budgets/scorer.',
              'STOP in this directory requests cancellation. Historical records remain separate.', '']
    (root / 'REPORT.md').write_text('\n'.join(lines), encoding='ascii')


def run(root):
    overnight.verify(root)
    base.OWNED_JOBS = True
    if not json.loads((root/'validation.json').read_text())['passed']:
        raise RuntimeError('Validation required')
    state = dict(status='running', pid=os.getpid(), started=time.time(), suites=[])
    root_lock = root/'RUNNING.lock'
    with root_lock.open('x') as handle:
        handle.write(str(os.getpid()))
    original_prompts = dict(base.PROMPTS)
    original_schedule = base.schedule
    deadline = time.monotonic()+3*3600
    results = {}

    def record():
        overnight.save(root/'status.json', state)
        report(root, state)

    try:
        record()
        for suite in ('smoke', 'ablation', 'staging'):
            if suite == 'staging':
                accepted = eligible(results['smoke'], results['ablation'])
                state['staging_gate'] = 'passed' if accepted else 'held: completion criteria not met'
                record()
                if not accepted:
                    continue
            overnight.verify(root)
            if (root/'STOP').exists() or time.monotonic() >= deadline:
                raise InterruptedError('STOP or three-hour queue cap')
            import compare_bonsai_packing_20260922 as packing
            packing.preflight()
            if list((overnight.LAB/'goproverbs/results').glob('**/RUNNING.lock')):
                raise RuntimeError('Go inference lock present')
            entries = entries_for(suite)
            base.schedule = lambda _: entries
            try:
                folder, _ = base.prepare(suite, TASKS, root=root)
            finally:
                base.schedule = original_schedule
            protocol = json.loads((folder/'protocol.json').read_text())
            protocol.update(completion_instruction=INSTRUCTION, seed=260923 if suite=='ablation' else 20260922,
                            guard='observation only in both arms', gate='See frozen PROTOCOL.md')
            base.save(folder/'protocol.json', protocol)
            protocol_hash = base.sha(folder/'protocol.json')
            models = base.api('/api/tags')['models']
            matches = [m for m in models if m['name'].split(':')[0] == base.MODEL]
            if len(matches)!=1:
                raise RuntimeError('Unique existing alias required')
            base.save(folder/'model.json', {'tag':matches[0], 'show':base.api('/api/show', {'model':base.MODEL})})
            rows = []
            results[suite] = rows
            state['suites'].append(suite)
            with (base.ROOT/'RUNNING.lock').open('x') as handle:
                handle.write(json.dumps({'pid':os.getpid(), 'folder':str(folder)}))
            try:
                for entry in entries:
                    if (root/'STOP').exists() or time.monotonic() >= deadline:
                        raise InterruptedError('STOP or three-hour queue cap')
                    overnight.verify(root)
                    if base.sha(folder/'protocol.json') != protocol_hash:
                        raise RuntimeError('Protocol changed')
                    state.update(active=entry['label'], suite=suite)
                    record()
                    base.PROMPTS = {key:value+(INSTRUCTION if entry['prompt_mode']=='completion' and key!='plan' else '')
                                    for key,value in original_prompts.items()}
                    # Use root STOP so cancellation is observed inside the trial too.
                    # execute_run uses folder/STOP; a small forwarding thread mirrors it.
                    import threading
                    done = threading.Event()
                    def forward():
                        while not done.wait(.5):
                            if (root/'STOP').exists() or time.monotonic() >= deadline:
                                (folder/'STOP').touch()
                                return
                    thread = threading.Thread(target=forward, daemon=True)
                    thread.start()
                    try:
                        row = base.execute_run(folder, entry)
                    finally:
                        done.set()
                        thread.join(timeout=2)
                    overnight.verify(root)
                    row['inputs_unchanged'] = base.sha(folder/'protocol.json') == protocol_hash
                    rows.append(row)
                    base.save(folder/'results.json', rows)
                    previous.report(folder, rows, 'running')
                    record()
                    print(entry['label'], row.get('correct'), row.get('clean_finish'), flush=True)
                    if base.infrastructure_failure(row):
                        raise RuntimeError('Infrastructure failure: '+entry['label'])
            finally:
                (base.ROOT/'RUNNING.lock').unlink()
                previous.report(folder, rows, 'complete' if len(rows)==len(entries) else 'incomplete')
        state['status']='complete'
    except BaseException as exc:
        state.update(status='stopped' if isinstance(exc,InterruptedError) else 'failed', error=repr(exc))
        raise
    finally:
        base.PROMPTS=original_prompts
        state['finished']=time.time()
        state['final_models']=base.api('/api/ps')
        root_lock.unlink()
        record()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('prepare','run'))
    parser.add_argument('--root',type=Path,default=ROOT)
    args=parser.parse_args()
    if args.action=='prepare':
        overnight.prepare(args.root)
        for name in ('completion_followup_20260923.py','test_completion_followup_20260923.py'):
            shutil.copy2(Path(__file__).parent/name,args.root/'source'/name)
        shutil.copy2(overnight.LAB/'COMPLETION-PLAN-2026-09-23.md',args.root/'PROTOCOL.md')
        files=list((args.root/'source').glob('*'))+[args.root/'PROTOCOL.md',base.PI]
        overnight.save(args.root/'manifest.json',{str(p):base.sha(p) for p in files})
    else:
        if Path(__file__).parent.resolve() != (args.root/'source').resolve():
            raise RuntimeError('Run the frozen source copy')
        run(args.root)


if __name__=='__main__':
    main()
