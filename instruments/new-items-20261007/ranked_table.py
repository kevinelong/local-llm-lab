"""ranked_table.py - the ranking metric of 2026-10-09, computed from the roots' own evidence.

Convention (declared 2026-10-09, Kevin's instruction): `events` and `paths` are retired from ranking -
the census shows them splitting on 5/76 and 3/75 checks in the top group, so they absorb budget and
manufacture ties. They stay in the loop as sanity checks. The ranking metric is the discriminating
subset:

    ledger (70) + ledger2 (226) + repo (78) + longctx (40) = 414 checks

Each row also carries the context the run was served, read from the run's own artifacts rather than
from a table: llama-server roots from the `-c` value in a session's status.json command, Strata roots
from the engine config's `--max-context`. Read-only; writes ranked-20261009.json next to itself.

Usage: python ranked_table.py [--json-only]
"""
import glob
import json
import sys
from pathlib import Path

BASE = Path(r'C:\Users\kevin\ai_bench')
DRIVER = BASE / 'new-items-20261007'
RANKED = ('ledger', 'ledger2', 'repo', 'longctx')
RANKED_TOTAL = 414
SIX = ('events', 'ledger', 'paths', 'ledger2', 'repo', 'longctx')
NINE = SIX + ('repo2', 'perf', 'longctx2')
STRATA = (BASE / 'strata-newtasks-20261009-v2', BASE / 'strata-newtasks-20261009-v3',
          BASE / 'strata-newtasks-20261009-v4', BASE / 'strata-newtasks-20261009-v1')


def llama_context(root):
    for status in sorted(root.glob('*/status.json')):
        try:
            command = json.loads(status.read_text(encoding='utf-8')).get('command') or []
        except (ValueError, OSError):
            continue
        if '-c' in command:
            return int(command[command.index('-c') + 1])
    return None


def strata_context():
    cfg = json.loads((BASE / 'staged-strata-20261007' / 'engine-src-v0.1.40.3' /
                      'strata-q2_0.json').read_text(encoding='utf-8-sig'))
    args = cfg.get('args') or []
    return int(args[args.index('--max-context') + 1]) if '--max-context' in args else None


def from_coding():
    """One row per new-task root that has a coding.json with evaluations."""
    rows = []
    for path in sorted(glob.glob(str(BASE / 'newtasks-*/evidence/*-coding.json'))):
        root = Path(path).parent.parent
        data = json.loads(Path(path).read_text(encoding='utf-8'))
        tasks = {}
        for task in data.get('tasks') or []:
            evaluation = task.get('evaluation') or {}
            if not evaluation.get('checks'):
                continue
            tasks[task['task']] = {'passed': evaluation['passed'], 'total': evaluation['total'],
                                   'correct': task.get('correct'),
                                   'unscored': 'abnormal_evaluator_exit' in evaluation}
        if tasks:
            rows.append({'root': root.name, 'model': data.get('model'), 'engine': 'llama-server',
                         'context': llama_context(root), 'tasks': tasks})
    return rows


def from_strata():
    """One row per Strata root, assembled from its per-task session results."""
    rows = []
    for root in STRATA:
        if not root.exists():
            continue
        tasks = {}
        for result in sorted((root / 'runs').glob('oms-*/result.json')):
            data = json.loads(result.read_text(encoding='utf-8'))
            evaluation = data.get('evaluation') or {}
            if not evaluation.get('checks'):
                continue
            name = data.get('task') or result.parent.name.replace('oms-', '')
            tasks[name] = {'passed': evaluation['passed'], 'total': evaluation['total'],
                           'correct': data.get('correct'),
                           'unscored': 'abnormal_evaluator_exit' in evaluation}
        if tasks:
            rows.append({'root': root.name, 'model': 'qwen3.8-flash-next-coder', 'engine': 'strata',
                         'context': strata_context(), 'tasks': tasks})
    return rows


def strata_combined():
    """One declared row for the Strata track: in-flight scores where the run produced them, plus the
    offline re-scores of v2's artifacts (same battery, deterministic input) where it did not."""
    tasks = {}
    for row in from_strata():
        tasks.update(row['tasks'])
    rescored = DRIVER / 'offline-rescores-20261009.json'
    if rescored.exists():
        for item in json.loads(rescored.read_text(encoding='utf-8'))['results']:
            if item['root'].startswith('strata-') and item['task'] not in tasks:
                tasks[item['task']] = {'passed': item['passed'], 'total': item['total'],
                                       'correct': item['passed'] == item['total'],
                                       'unscored': False, 'source': 'offline re-score'}
    if not tasks:
        return []
    return [{'root': 'strata-newtasks-20261009-v2+v3+v4 (combined, declared)', 'model': 'qwen3.8-flash-next-coder',
             'engine': 'strata', 'context': strata_context(), 'tasks': tasks}]


def subtotal(tasks, wanted):
    got = [tasks[k] for k in wanted if k in tasks]
    if len(got) != len(wanted):
        return None, None, len(got)
    return sum(g['passed'] for g in got), sum(g['total'] for g in got), len(got)


def main():
    rows = from_coding() + strata_combined()
    table = []
    for row in rows:
        ranked, ranked_total, ranked_have = subtotal(row['tasks'], RANKED)
        six, six_total, _ = subtotal(row['tasks'], SIX)
        nine, nine_total, _ = subtotal(row['tasks'], NINE)
        table.append({**row, 'ranked': ranked, 'ranked_total': ranked_total,
                      'registered': ranked_have, 'six': six, 'six_total': six_total,
                      'nine': nine, 'nine_total': nine_total})
    table.sort(key=lambda r: (-(r['ranked'] or 0), r['root']))
    print('%-30s %-24s %-10s %-9s %-6s %s' % ('root', 'model', 'ranked/414', 'six', 'ctx', 'engine'))
    for row in table:
        if row['ranked'] is None:
            continue
        print('%-30s %-24s %3d/%-6d %-9s %-6s %s' % (
            row['root'], str(row['model'])[:24], row['ranked'], row['ranked_total'],
            ('%s/%s' % (row['six'], row['six_total'])) if row['six'] is not None else '-',
            row['context'], row['engine']))
    target = DRIVER / 'ranked-20261009.json'
    target.write_text(json.dumps({'convention': 'events and paths retired from ranking 2026-10-09',
                                  'ranked_tasks': list(RANKED), 'ranked_total': RANKED_TOTAL,
                                  'rows': table}, indent=1), encoding='ascii')
    if '--json-only' not in sys.argv:
        print('\nwritten: %s' % target.name)


if __name__ == '__main__':
    main()
