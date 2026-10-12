"""Label every ledger2 case index with the trap it tests, and profile artifacts by trap class.

Read-only companion to new_tasks_20261008.py: the frozen battery's cases 0-69 keep their frozen
indices, so extra cases start at 70. This maps the extras to their trap class and re-prints the
re-score grouped by class, which is what makes the finer battery readable.
"""
import sys
from collections import defaultdict
from pathlib import Path

BASE = Path(r'C:\Users\kevin\ai_bench')
sys.path.insert(0, str(BASE / 'new-items-20261007'))
import new_tasks_20261008 as nt  # noqa: E402
import rescore  # noqa: E402


def label_extra(index):
    """Return the trap class of an extra case by rebuilding the battery in order."""
    # rebuild exactly as extra_values() does, one append at a time, recording the labels
    labels = []
    for name, _digit in nt.UNICODE_DIGITS.items():
        labels += ['unicode-digit/%s/%s' % (name, s) for s in ('plain', 'leading-zero', 'embedded')]
    for name, _space in nt.UNICODE_SPACES.items():
        labels += ['unicode-space/%s/%s' % (name, s) for s in ('trailing', 'leading', 'both', 'interior')]
    labels += ['cents-shape/%r' % bad for bad in ['+1', '-1', '1.0', '1e3', '0x1', '1_0', ' 1', '1 ', '\t1', '1\t', '1\n',
                                                   '', ' ', '\t', '01x', 'x01', '1,000', '\u0661\u0662']]
    labels += ['csv-shape/%d' % i for i in range(20)]
    labels += ['header/%d' % i for i in range(10)]
    labels += ['name/%d' % i for i in range(9)]
    labels += ['accumulation/%d' % i for i in range(4)]
    return labels[index] if 0 <= index < len(labels) else 'random-valid/%d' % index


def main():
    values = nt.cases('ledger2')
    extra = len(values) - 70
    print('ledger2: %d cases (%d frozen + %d extra)' % (len(values), 70, extra))
    print('extra-case labels:')
    for i in range(extra):
        if i < 45 or i in (77, 90, 91, 100, 110, 111, 124, 125, 131, 132, 135, 137, 139, 140, 141, 158, 159, 160):
            print('   %3d  %s' % (70 + i, label_extra(i)))
    print()
    # profile each artifact by trap class
    rows = []
    for root, folder, artifact, result_path in rescore.artifacts():
        try:
            new = nt.evaluate('ledger2', artifact)
        except Exception:
            continue
        classes = defaultdict(int)
        for check in new['checks']:
            if check['pass']:
                continue
            index = check['case'] - 70
            classes['frozen-0-69' if index < 0 else label_extra(index).split('/')[0]] += 1
        rows.append((root.name, folder.name, new['passed'], dict(classes)))
    print('%-26s %-14s %-9s %s' % ('root', 'session', 'score', 'failures by class'))
    for root, folder, passed, classes in sorted(rows, key=lambda r: -r[2]):
        print('%-26s %-14s %-9s %s' % (root, folder[:14], passed, classes))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
