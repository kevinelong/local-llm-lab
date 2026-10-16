"""runner.py - the serial driver for this root's queue, modelled on the 2026-10-11 one.

Conventions from that queue, kept deliberately: serial by construction (one inference workload at a time),
a STOP file checked before each item, a status.json that always shows where the queue is, a REPORT.md that
grows as items finish, the resource gates checked between items and the queue *stopped* rather than weakened
on a trip, and no blind retries.

What is added here: a **slot check** before anything runs. A measured run was in flight when this queue was
declared, and two engines at once would contaminate both measurements, so the driver refuses to start while
an engine is listening on the lab's Colibri port.

Usage:
    python runner.py                       # the whole queue, in order
    python runner.py --only q1-strata-kv-residency,q2-moe-cache-mib-ladder
    python runner.py --from q3-noise-floor
    python runner.py --dry-run             # gates, slot check, plan, status and report; no engines
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
STOP = ROOT / 'QUEUE-STOP'

sys.path.insert(0, str(ROOT.parent / 'overnight-20261011'))
import shared                                     # noqa: E402
shared.LOGS = ROOT / 'logs'
shared.LOGS.mkdir(exist_ok=True)


def save_status(state):
    STATUS.write_text(json.dumps(state, indent=1), encoding='utf-8')


def append_report(text):
    with REPORT.open('a', encoding='utf-8') as handle:
        handle.write(text + '\n')


def kill_engine_trees():
    for port in (shared.LLAMA_PORT, shared.STRATA_PORT, shared.COLIBRI_PORT):
        shared.kill_port(port, 'runner')


def slot_free():
    """False while a measured run holds the one inference slot (the Colibri engine on its port)."""
    return not shared.port_open(shared.COLIBRI_PORT)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--only', default=None)
    parser.add_argument('--from', dest='start_at', default=None)
    parser.add_argument('--dry-run', action='store_true')
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
        REPORT.write_text('# Queue, %s\n\n%s\n\n' % (queue['declared'], queue['purpose']), encoding='utf-8')

    state = {'declared': queue['declared'], 'started': time.strftime('%F %T'),
             'queue': [i['id'] for i in items], 'results': [], 'stopped': None}
    save_status(state)
    shared.log('runner', 'queue of %d items: %s' % (len(items), ', '.join(i['id'] for i in items)))

    if not slot_free() and not args.dry_run:
        state['stopped'] = ('inference slot busy: an engine is listening on port %d, so a measured run is '
                            'still in flight' % shared.COLIBRI_PORT)
        save_status(state)
        append_report('**Not started:** %s. Wait for it, then run this queue unchanged.\n' % state['stopped'])
        shared.log('runner', state['stopped'])
        return 0

    if not args.dry_run:
        # Clear the engine ports BEFORE the first item as well as between items. The 2026-10-11 driver only
        # cleared them between items, and that cost its i4 its Strata arm: a dev-server was holding port 8080
        # (this lab's own STRATA_PORT), so the arm refused to start while the other arm ran fine.
        kill_engine_trees()

    for item in items:
        status = item.get('status')
        if status in ('parked', 'gated') or 'gate' in item:
            reason = item.get('gate') or item.get('parked_until') or status
            state['results'].append({'id': item['id'], 'exit': None, 'skipped': True, 'reason': reason})
            save_status(state)
            append_report('## %s - SKIPPED\n\nDeclared not runnable: %s\n' % (item['id'], reason))
            shared.log('runner', 'skipped %s (%s)' % (item['id'], reason))
            continue

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
            append_report('**Stopped** on a resource gate before `%s`: free %.2f GiB, commit headroom '
                          '%.2f GiB. Gates were not lowered.\n' % (item['id'], resources.get('free', -1),
                                                                   resources.get('commit_headroom', -1)))
            shared.log('runner', state['stopped'])
            return 0

        append_report('## %s - %s\n\n%s\n\nPrediction recorded before the run: %s\n'
                      % (item['id'], item['title'], item['question'], item['prediction']))
        if args.dry_run:
            shared.log('runner', 'dry run: would start %s (timeout %ds)' % (item['id'], item['timeout']))
            append_report('- dry run: not started.\n')
            continue

        started = time.time()
        shared.log('runner', 'starting %s (timeout %ds)' % (item['id'], item['timeout']))
        try:
            done = subprocess.run([sys.executable, str(ROOT / 'items.py'), item['id']], cwd=str(ROOT),
                                  capture_output=True, text=True, timeout=item['timeout'])
            code = done.returncode
            note = ((done.stdout or '') + (done.stderr or '')).strip().splitlines()[-8:]
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

    state['stopped'] = 'queue complete' if not args.dry_run else 'dry run complete'
    state['finished'] = time.strftime('%F %T')
    save_status(state)
    append_report('\n**%s** at %s.\n' % (state['stopped'].capitalize(), state['finished']))
    shared.log('runner', state['stopped'])
    return 0


if __name__ == '__main__':
    sys.exit(main())
