"""Check-level discrimination census: which of our checks still separate models, and which are dead.

Frame from the saturation literature (arXiv 2602.16763 defines saturation as the loss of reliable
discriminative power among top models; arXiv 2505.15055 applies item-response theory to benchmark
items). The same idea applies at *check* level, and our own runs contain the data: for every scored
artifact on disk, each check either passed or failed, so a check that every artifact passes (or every
artifact fails) carries no information, while a check with a mixed outcome separates models.

For every check we report:
  n        how many artifacts were scored on it
  pass     how many passed
  rate     pass / n
  split    1 - |2*rate - 1|  (0 = everyone passes or everyone fails, 1 = maximally mixed)
  r        point-biserial correlation between this check and the artifact's overall score on that
           task: how much the check tracks the rest of the task, i.e. its ability to rank artifacts

Read-only. Usage: python census_checks.py [task ...]
"""
import json
import math
import statistics
import sys
from collections import defaultdict
from pathlib import Path

BASE = Path(r'C:\Users\kevin\ai_bench')


def artifacts():
    """(task, model-label, checks) for every scored artifact on disk."""
    seen = set()
    # every root family, including the newest ones (newtasks-ctx-*, strata-ctx-*, strata-ab-*)
    for pattern in ('candidates-*', 'truncation-*', 'newtasks*', 'provision-*', 'strata-*'):
        for evidence in sorted(BASE.glob(pattern + '/evidence/*-coding.json')):
            root = evidence.parent.parent.name
            model = evidence.name.replace('-coding.json', '')
            try:
                data = json.loads(evidence.read_text())
            except Exception:
                continue
            for task in data.get('tasks', []):
                evaluation = task.get('evaluation') or {}
                checks = evaluation.get('checks')
                if not checks:
                    continue
                key = (root, task.get('task'))
                if key in seen:
                    continue
                seen.add(key)
                yield task.get('task'), '%s:%s' % (model, root), checks
    for pattern in ('strata*',):
        for result in sorted(BASE.glob(pattern + '/runs/oms-*/result.json')):
            try:
                data = json.loads(result.read_text(encoding='utf-8'))
            except Exception:
                continue
            evaluation = data.get('evaluation') or {}
            checks = evaluation.get('checks')
            task = data.get('task') or result.parent.name.replace('oms-', '')
            key = (result.parts[-4], task)
            if not checks or key in seen:
                continue
            seen.add(key)
            yield task, 'strata:%s' % result.parts[-4], checks


def load_missing_ledger2():
    """The 226-check battery applied offline to every saved ledger artifact (see rescore.py)."""
    import importlib.util
    spec = importlib.util.spec_from_file_location('nt', BASE / 'new-items-20261007/new_tasks_20261008.py')
    module = importlib.util.module_from_spec(spec)
    sys.modules['nt'] = module
    spec.loader.exec_module(module)
    for root in sorted(BASE.glob('*2026*')):
        if not root.is_dir():
            continue
        for artifact in sorted(root.glob('**/*ledger*/**/final-artifact.py')):
            parts = str(artifact).replace('\\', '/').split('/')
            if 'trial' not in parts and 'runs' not in parts:
                continue
            try:
                result = module.evaluate('ledger2', artifact)
            except Exception:
                continue
            yield 'ledger2', 'offline:%s/%s' % (parts[-4], parts[-3]), result['checks']


def main():
    wanted = [a for a in sys.argv[1:] if not a.startswith('-')]
    per_task = defaultdict(list)
    for task, label, checks in artifacts():
        if wanted and task not in wanted:
            continue
        per_task[task].append((label, checks))
    for task, label, checks in load_missing_ledger2():
        if wanted and task not in wanted:
            continue
        per_task[task].append((label, checks))

    for task in sorted(per_task):
        rows = per_task[task]
        n_artifacts = len(rows)
        index_count = defaultdict(int)
        passes = defaultdict(int)
        for label, checks in rows:
            for check in checks:
                index_count[check['case']] += 1
                if check.get('pass'):
                    passes[check['case']] += 1
        totals = {label: sum(1 for c in checks if c.get('pass')) for label, checks in rows}
        # point-biserial: correlation between this check's indicator and the artifact's total
        stats = []
        for case, n in index_count.items():
            if n < 3:
                continue
            rate = passes[case] / n
            split = 1 - abs(2 * rate - 1)
            xs, ys = [], []
            for label, checks in rows:
                value = next((c.get('pass') for c in checks if c['case'] == case), None)
                if value is None:
                    continue
                xs.append(1.0 if value else 0.0)
                # leave-one-out total: a check must not correlate with a total that contains it
                ys.append(float(totals[label] - (1 if value else 0)))
            r = 0.0
            if len(set(xs)) > 1 and len(set(ys)) > 1:
                mx, my = statistics.mean(xs), statistics.mean(ys)
                num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
                den = math.sqrt(sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys))
                r = num / den if den else 0.0
            stats.append((case, n, passes[case], rate, split, r))
        best = max(totals.values()) if totals else 0
        top_rows = [(label, checks) for label, checks in rows if totals[label] >= 0.9 * best]
        top_pass = defaultdict(int)
        top_n = defaultdict(int)
        for label, checks in top_rows:
            for check in checks:
                top_n[check['case']] += 1
                if check.get('pass'):
                    top_pass[check['case']] += 1
        top_live = [c for c in top_n if top_n[c] >= 3 and 0.0 < top_pass[c] / top_n[c] < 1.0]
        dead = [s for s in stats if s[4] <= 0.02]
        live = [s for s in stats if s[4] > 0.02]
        print('== %s: %d artifacts, %d checks' % (task, n_artifacts, len(stats)))
        print('   saturated (no split): %d of %d (%.0f%%) | discriminating: %d' % (
            len(dead), len(stats), 100 * len(dead) / max(1, len(stats)), len(live)))
        live.sort(key=lambda s: -s[5])
        print('   most discriminating by point-biserial: ' + ', '.join(
            'case %d (rate %.2f, r %.2f)' % (s[0], s[3], s[5]) for s in live[:6]))
        if dead:
            print('   always-pass: %d | always-fail: %d' % (
                sum(1 for s in dead if s[3] == 1.0), sum(1 for s in dead if s[3] == 0.0)))
        print('   TOP GROUP (>=90%% of the best score): %d artifacts; checks still splitting among them: %d of %d' % (
            len(top_rows), len(top_live), len(top_n)))
        if top_live:
            # 2026-10-09: rank by failure rate. Sorting by case number hid the leading case
            # (case 19 in the ledger, the ASCII-digit trap) behind the 14-entry display cap.
            ranked = sorted(top_live, key=lambda c: (top_pass[c] / top_n[c], c))
            print('     splitting cases (most-failing first): ' + ', '.join(
                'case %d (%d/%d)' % (c, top_pass[c], top_n[c]) for c in ranked[:14]))
        print()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
