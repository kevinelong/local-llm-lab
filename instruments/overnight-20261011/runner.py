"""runner.py - the overnight queue driver.

Serial by construction (one item at a time, one inference workload at a time). Conventions borrowed from
this lab's earlier overnight roots: a STOP file checked before each item, a status.json that always shows
where the night is, a REPORT.md that grows as items finish, preserved logs, gates checked between items and
the queue *stopped* (not weakened) on a trip, and no blind retries.

Usage: python runner.py [--only i1-strata-placement,i3-colibri-qwen36] [--from i2-kolibri-knowledge]
"""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
QUEUE = ROOT / 'queue.json'
STATUS = ROOT / 'status.json'
REPORT = ROOT / 'REPORT.md'
STOP = ROOT / 'OVERNIGHT-STOP'

sys.path.insert(0, str(ROOT))
import shared


def save_status(state):
    STATUS.write_text(json.dumps(state, indent=1), encoding='utf-8')


def append_report(text):
    with REPORT.open('a', encoding='utf-8') as handle:
        handle.write(text + '\n')


def kill_engine_trees():
    for port in (shared.LLAMA_PORT, shared.STRATA_PORT, shared.COLIBRI_PORT):
        shared.kill_port(port, 'runner')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--only', default=None)
    parser.add_argument('--from', dest='start_at', default=None)
    args = parser.parse_args()

    queue = json.loads(QUEUE.read_text(encoding='utf-8'))
    items = queue['items']
    if args.only:
        wanted = [x.strip() for x in args.only.split(',')]
        items = [i for i in items if i['id'] in wanted]
    if args.start_at:
        names = [i['id'] for i in items]
        if args.start_at in names:
            items = items[names.index(args.start_at):]

    if not REPORT.exists():
        REPORT.write_text('# Overnight queue, %s\n\n%s\n\n' % (queue['declared'], queue['purpose']), encoding='utf-8')

    state = {'declared': queue['declared'], 'started': time.strftime('%F %T'), 'queue': [i['id'] for i in items],
             'results': [], 'stopped': None}
    save_status(state)
    shared.log('runner', 'queue of %d items: %s' % (len(items), ', '.join(i['id'] for i in items)))

    for item in items:
        if STOP.exists():
            state['stopped'] = 'STOP file present before %s' % item['id']
            save_status(state)
            append_report('**Stopped** by STOP file before `%s`. Nothing running.\n' % item['id'])
            shared.log('runner', state['stopped'])
            kill_engine_trees()
            return 0

        ok, resources = shared.guard_ok()
        if not ok:
            state['stopped'] = 'gate trip before %s (free %.2f GiB, commit headroom %.2f GiB)' % (
                item['id'], resources.get('free', -1), resources.get('commit_headroom', -1))
            save_status(state)
            append_report('**Stopped** on a resource gate before `%s`: free %.2f GiB, commit headroom %.2f GiB. '
                          'Gates were not lowered.\n' % (item['id'], resources.get('free', -1),
                                                         resources.get('commit_headroom', -1)))
            shared.log('runner', state['stopped'])
            return 0

        append_report('## %s - %s\n\n%s\n\nPrediction recorded before the run: %s\n'
                      % (item['id'], item['title'], item['question'], item['prediction']))
        started = time.time()
        shared.log('runner', 'starting %s (timeout %ds)' % (item['id'], item['timeout']))
        try:
            done = subprocess.run([sys.executable, str(ROOT / 'items.py'), item['id']], cwd=str(ROOT),
                                  capture_output=True, text=True, timeout=item['timeout'])
            code, note = done.returncode, ((done.stdout or '') + (done.stderr or '')).strip().splitlines()[-6:]
        except subprocess.TimeoutExpired:
            code, note = -9, ['timeout after %ds' % item['timeout']]
        duration = time.time() - started
        kill_engine_trees()
        entry = {'id': item['id'], 'exit': code, 'seconds': round(duration, 1), 'tail': note,
                 'result_file': str(ROOT / ('result-%s.json' % item['id']))
                 if (ROOT / ('result-%s.json' % item['id'])).exists() else None}
        state['results'].append(entry)
        save_status(state)
        verdict = 'ok' if code == 0 else ('TIMEOUT' if code == -9 else 'exit %d' % code)
        append_report('- finished in %.0f s: %s\n' % (duration, verdict) +
                      ''.join('\n  - %s' % line for line in note) + '\n')
        shared.log('runner', '%s -> %s in %.0f s' % (item['id'], verdict, duration))

    state['stopped'] = 'queue complete'
    state['finished'] = time.strftime('%F %T')
    save_status(state)
    append_report('\n**Queue complete** at %s.\n' % state['finished'])
    shared.log('runner', 'queue complete')
    return 0


if __name__ == '__main__':
    sys.exit(main())
