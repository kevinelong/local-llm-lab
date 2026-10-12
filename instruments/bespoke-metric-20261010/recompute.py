"""recompute.py - independent re-derivation of the decision suite's metric, from frozen rows only.

Why: the 2026-10-08 note (`local-llm-lab/BESPOKE-METRIC-2026-10-08.md`) found that `civil_comments` is a
90/10 subset, so plain accuracy there is the majority baseline plus noise, and that scoring the binary
subsets class-balanced flips the ranking (kev4 4B ahead of nimble 9B). That finding was never propagated
into the suite roots or the README. This recomputes it from the stored `rows.jsonl` - no inference, no
network - so the front-page recommendation rests on a re-derived number, not a restated one.

Two macros are reported per model:
  accuracy_macro - the original metric: plain accuracy, averaged over all 13 subsets.
  balanced_macro - the proposed metric: balanced accuracy for `noul` (binary) subsets, plain accuracy
                   for the rest, averaged over all 13 subsets (comparability with the published table).
For binary subsets it also reports the majority baseline and the positive prediction rate, because a
balanced number without the baseline hides how little signal a skewed subset carries.

Usage: python recompute.py [--json out.json]
"""
import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

BASE = Path(r'C:\Users\kevin\ai_bench')
import os
NEWER = BASE / 'bespoke-suite-20261010-v1'                       # kev4/nimble post-RAM-upgrade
OLD = BASE / 'bespoke-suite-20261005-v1'
LEGACY_ROOT = NEWER if os.environ.get('SUITE_ROOT') == 'new' else OLD
SOURCES = {                     # model -> (root, evidence directory)
    'kev4': (LEGACY_ROOT, 'kev4-suite'),
    'nimble': (LEGACY_ROOT, 'nimble-suite'),
    'lev': (BASE / 'bespoke-suite-20261007-v1', 'lev-suite'),
    'kev0': (BASE / 'bespoke-suite-20261007-v1', 'kev0-suite'),
    'laya': (BASE / 'bespoke-suite-20261007-v1', 'laya-suite'),
}


def load_rows(root, suite):
    runs = root / 'evidence' / suite / 'runs'
    subsets = {}
    for directory in sorted(runs.iterdir()):
        if not directory.is_dir():
            continue
        rows = [json.loads(line) for line in (directory / 'rows.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]
        if rows:
            subsets[directory.name] = rows
    return subsets


def score_subset(rows):
    """Plain accuracy always; balanced accuracy, majority baseline and prediction rate when binary."""
    total = len(rows)
    correct = sum(1 for r in rows if r.get('correct'))
    out = {'n': total, 'accuracy': round(correct / total, 4),
           'type': rows[0].get('type'), 'binary': rows[0].get('type') == 'noul'}
    if out['binary']:
        positives = sum(1 for r in rows if r['target'] is True or r['target'] == 1)
        negatives = total - positives
        predicted_positive = sum(1 for r in rows if r.get('prediction') is True or r.get('prediction') == 1)
        pos_recall = (sum(1 for r in rows if (r['target'] in (True, 1)) and r.get('correct')) / positives) if positives else None
        neg_recall = (sum(1 for r in rows if (r['target'] in (False, 0)) and r.get('correct')) / negatives) if negatives else None
        recalls = [x for x in (pos_recall, neg_recall) if x is not None]
        out.update({'majority_baseline': round(max(positives, negatives) / total, 4),
                    'balanced_accuracy': round(sum(recalls) / len(recalls), 4),
                    'prediction_rate': round(predicted_positive / total, 4),
                    'positive_recall': round(pos_recall, 4) if pos_recall is not None else None,
                    'negative_recall': round(neg_recall, 4) if neg_recall is not None else None})
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--json', default=str(Path(__file__).resolve().parent / 'recomputed.json'))
    args = parser.parse_args()

    report, table = {}, {}
    for model, (root, suite) in SOURCES.items():
        subsets = load_rows(root, suite)
        scored = {name: score_subset(rows) for name, rows in subsets.items()}
        accuracies = [s['accuracy'] for s in scored.values()]
        balanced = [s.get('balanced_accuracy', s['accuracy']) for s in scored.values()]
        report[model] = {
            'root': str(root), 'suite': suite, 'subsets': len(scored),
            'records': sum(s['n'] for s in scored.values()),
            'accuracy_macro': round(sum(accuracies) / len(accuracies), 4),
            'balanced_macro': round(sum(balanced) / len(balanced), 4),
            'per_subset': scored,
        }
        table[model] = report[model]

    order_old = sorted(table, key=lambda m: -table[m]['accuracy_macro'])
    order_new = sorted(table, key=lambda m: -table[m]['balanced_macro'])
    print('%-8s %6s %6s %8s  %10s %10s' % ('model', 'subs', 'recs', 'binary', 'accuracy', 'balanced'))
    print('-' * 56)
    for model in order_old:
        t = table[model]
        binary = sum(1 for s in t['per_subset'].values() if s['binary'])
        print('%-8s %6d %6d %8d  %10.4f %10.4f' % (model, t['subsets'], t['records'], binary,
                                                    t['accuracy_macro'], t['balanced_macro']))
    print('\nrank by accuracy (original): %s' % ' > '.join(order_old))
    print('rank by balanced accuracy  : %s' % ' > '.join(order_new))
    flip = order_old[0] != order_new[0]
    print('leader changes under the class-balanced metric: %s' % flip)
    for model in table:
        cc = table[model]['per_subset'].get('civil_comments')
        if cc:
            print('  %-7s civil_comments acc %.3f (majority %.3f) balanced %.3f pred-rate %.3f'
                  % (model, cc['accuracy'], cc['majority_baseline'], cc['balanced_accuracy'],
                     cc['prediction_rate']))
    Path(args.json).write_text(json.dumps({'generated': '2026-10-10', 'sources': SOURCES and
                                           {m: str(SOURCES[m][0].name) + '/' + SOURCES[m][1] for m in SOURCES},
                                           'models': report}, indent=1), encoding='utf-8')
    print('\nwrote %s' % args.json)
    return 0


if __name__ == '__main__':
    sys.exit(main())
