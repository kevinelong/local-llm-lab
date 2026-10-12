"""suite_report.py - report any Bespoke decision-suite root under the corrected metric.

The 2026-10-08 note established that plain accuracy on a skewed subset is a majority-class measurement, and
`recompute.py` in this root proves it from the frozen rows. This is the reusable half: point it at any suite
root and it reports, per subset, accuracy, balanced accuracy, positive prediction rate and majority
baseline; per metric family (`noul`, `choice`, `score`); both macros; and for `score` subsets the primitive
that actually fits them, mean |prediction - target|.

No inference, no network: it reads `<root>/evidence/<model>-suite/runs/<subset>/rows.jsonl`.

Usage: python suite_report.py --root C:/Users/kevin/ai_bench/bespoke-suite-20261010-v1
       python suite_report.py --root <root> --json out.json
"""
import argparse
import json
import sys
from pathlib import Path


def load_subsets(root, evidence_name):
    runs = root / 'evidence' / evidence_name / 'runs'
    subsets = {}
    for directory in sorted(runs.iterdir()) if runs.exists() else []:
        if not directory.is_dir():
            continue
        rows_path = directory / 'rows.jsonl'
        if not rows_path.exists():
            continue
        rows = [json.loads(line) for line in rows_path.read_text(encoding='utf-8').splitlines() if line.strip()]
        if rows:
            subsets[directory.name] = rows
    return subsets


def score_subset(rows):
    total = len(rows)
    correct = sum(1 for r in rows if r.get('correct'))
    kind = rows[0].get('type')
    out = {'type': kind, 'n': total, 'accuracy': round(correct / total, 4)}
    if kind == 'noul':
        pos = [r for r in rows if r['target'] in (True, 1)]
        neg = [r for r in rows if r['target'] in (False, 0)]
        pos_recall = (sum(1 for r in pos if r['correct']) / len(pos)) if pos else None
        neg_recall = (sum(1 for r in neg if r['correct']) / len(neg)) if neg else None
        recalls = [x for x in (pos_recall, neg_recall) if x is not None]
        predicted_positive = sum(1 for r in rows if r.get('prediction') in (True, 1))
        out.update({'balanced_accuracy': round(sum(recalls) / len(recalls), 4) if recalls else None,
                    'majority_baseline': round(max(len(pos), len(neg)) / total, 4),
                    'prediction_rate': round(predicted_positive / total, 4)})
    if kind == 'score':
        errors = [abs(float(r['target']) - float(r['prediction'])) for r in rows]
        out.update({'mean_abs_score_error': round(sum(errors) / len(errors), 4),
                    'mean_prediction': round(sum(float(r['prediction']) for r in rows) / total, 3),
                    'mean_target': round(sum(float(r['target']) for r in rows) / total, 3)})
    return out


def report(root, evidence_name):
    subsets = load_subsets(root, evidence_name)
    if not subsets:
        return None
    scored = {name: score_subset(rows) for name, rows in subsets.items()}
    accuracies = [s['accuracy'] for s in scored.values()]
    balanced = [s.get('balanced_accuracy') if s.get('balanced_accuracy') is not None else s['accuracy']
                for s in scored.values()]
    families = {}
    for name, s in scored.items():
        fam = s['type']
        families.setdefault(fam, {'subsets': 0, 'records': 0, 'correct': 0,
                                  'balanced_sum': 0.0, 'balanced_n': 0, 'score_err': 0.0, 'score_n': 0})
        f = families[fam]
        f['subsets'] += 1
        f['records'] += s['n']
        f['correct'] += round(s['accuracy'] * s['n'])
        if s.get('balanced_accuracy') is not None:
            f['balanced_sum'] += s['balanced_accuracy']
            f['balanced_n'] += 1
        if s.get('mean_abs_score_error') is not None:
            f['score_err'] += s['mean_abs_score_error'] * s['n']
            f['score_n'] += s['n']
    out_families = {}
    for fam, f in families.items():
        out_families[fam] = {'subsets': f['subsets'], 'records': f['records'],
                             'accuracy': round(f['correct'] / f['records'], 4),
                             'balanced': round(f['balanced_sum'] / f['balanced_n'], 4) if f['balanced_n'] else None,
                             'mean_abs_score_error': round(f['score_err'] / f['score_n'], 4) if f['score_n'] else None}
    return {'root': str(root), 'evidence': evidence_name, 'subsets': len(scored), 'records': sum(s['n'] for s in scored.values()),
            'accuracy_macro': round(sum(accuracies) / len(accuracies), 4),
            'balanced_macro': round(sum(balanced) / len(balanced), 4),
            'families': out_families, 'per_subset': scored}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', required=True)
    parser.add_argument('--json', default=None)
    parser.add_argument('--only-models', default=None, help='comma list to restrict, otherwise every *-suite dir')
    args = parser.parse_args()

    root = Path(args.root)
    evidence = root / 'evidence'
    if not evidence.exists():
        sys.exit('no evidence dir under %s' % root)
    names = sorted(d.name for d in evidence.iterdir() if d.is_dir() and d.name.endswith('-suite'))
    if args.only_models:
        wanted = ['%s-suite' % m.strip() for m in args.only_models.split(',')]
        names = [n for n in names if n in wanted]
    if not names:
        sys.exit('no *-suite evidence under %s' % evidence)

    everything = {}
    header = '%-10s %6s %5s %8s %8s %8s  %s' % ('model', 'subs', 'recs', 'accuracy', 'balanced', 'score|err|', 'by family (acc / balanced)')
    print(header)
    print('-' * len(header))
    for name in names:
        model = name[:-len('-suite')]
        rep = report(root, name)
        if not rep:
            continue
        everything[model] = rep
        fam = ' '.join('%s %.3f%s' % (k, v['accuracy'],
                                      ('/%.3f' % v['balanced']) if v['balanced'] is not None else '')
                       for k, v in sorted(rep['families'].items()))
        score_err = (rep['families'].get('score') or {}).get('mean_abs_score_error')
        print('%-10s %6d %5d %8.4f %8.4f %8s  %s'
              % (model, rep['subsets'], rep['records'], rep['accuracy_macro'], rep['balanced_macro'],
                 ('%.3f' % score_err) if score_err is not None else '-', fam))
    print()
    for model, rep in everything.items():
        for name, s in sorted(rep['per_subset'].items()):
            if s['type'] == 'noul':
                print('  %-10s %-22s n %3d  acc %.3f  balanced %.3f  majority %.3f  pred-rate %.3f'
                      % (model, name, s['n'], s['accuracy'], s['balanced_accuracy'],
                         s['majority_baseline'], s['prediction_rate']))
    if args.json:
        Path(args.json).write_text(json.dumps(everything, indent=1), encoding='utf-8')
        print('\nwrote %s' % args.json)
    return 0


if __name__ == '__main__':
    sys.exit(main())
