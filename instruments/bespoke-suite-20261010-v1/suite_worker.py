"""Run the rebuilt Bespoke public suite through a llama-server /v1/systemone endpoint.

Scoring mirrors nimble/evaluation/evaluate_pilot.assess exactly: probabilities are keyed by
candidate value, prediction is the argmax, NLL is -ln p(reference), multiclass Brier sums
squared errors over candidates, binary Brier uses P(true), and Score MAE is
|sum(i * p_i) - target|.

Usage: suite_worker.py BASE_URL DATA_ROOT OUT_DIR [SUBSET ...]
Writes OUT_DIR/<subset>/{rows.jsonl,summary.json} and OUT_DIR/suite.json. Subsets with a
summary already present are skipped, so an interrupted run resumes.
"""
import json, math, statistics, sys, time, urllib.request
from pathlib import Path


def post(base, payload, timeout=300):
    request = urllib.request.Request(base.rstrip('/') + '/v1/systemone',
                                     data=json.dumps(payload).encode('utf-8'),
                                     headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


def probabilities(answer):
    """Candidate-keyed probabilities from either the categorical or the scalar Noul answer."""
    if isinstance(answer.get('probabilities'), dict):
        return {str(key): float(value) for key, value in answer['probabilities'].items()}
    if isinstance(answer.get('noul'), (int, float)):
        value = float(answer['noul'])
        return {'false': 1.0 - value, 'true': value}
    raise ValueError('unrecognised answer shape: ' + json.dumps(answer))


def target_key(target, kind):
    if kind == 'noul':
        return str(bool(target)).lower()
    if kind == 'score':
        return str(int(target))
    return str(target)


def assess(kind, distribution, target):
    gold = target_key(target, kind)
    if gold not in distribution:
        raise ValueError('reference %r absent from candidates %s' % (gold, sorted(distribution)))
    total = sum(distribution.values())
    if not math.isclose(total, 1.0, abs_tol=1e-6):
        raise ValueError('probabilities do not sum to one: %r' % total)
    best = max(distribution, key=distribution.get)
    row = {'prediction': (best == 'true') if kind == 'noul' else int(best) if kind == 'score' else best,
           'reference_probability': distribution[gold],
           'top_probability': distribution[best],
           'negative_log_likelihood': -math.log(max(distribution[gold], 1e-15)),
           'multiclass_brier': sum((p - int(k == gold)) ** 2 for k, p in distribution.items()),
           'correct': best == gold}
    if kind == 'noul':
        row['binary_brier'] = (distribution['true'] - int(bool(target))) ** 2
    if kind == 'score':
        expected = sum(int(k) * p for k, p in distribution.items())
        row['expected_score'] = expected
        row['absolute_score_error'] = abs(expected - int(target))
    return row


def summarize(rows):
    group = {'count': len(rows), 'correct': sum(row['correct'] for row in rows)}
    group['accuracy'] = group['correct'] / group['count']
    for metric in ('negative_log_likelihood', 'multiclass_brier', 'binary_brier', 'absolute_score_error'):
        values = [row[metric] for row in rows if metric in row]
        if len(values) == len(rows):
            group['mean_' + metric] = statistics.mean(values)
    latencies = sorted(row['ms'] for row in rows)
    group['median_ms'] = statistics.median(latencies)
    group['p95_ms'] = latencies[math.ceil(0.95 * len(latencies)) - 1]
    return group


def by_type(rows):
    result = {}
    for kind in ('noul', 'choice', 'score'):
        selected = [row for row in rows if row['type'] == kind]
        if selected:
            result[kind] = summarize(selected)
    return result


def main():
    base, data_root, out_root = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])
    wanted = set(sys.argv[4:])
    subsets = sorted(folder.name for folder in data_root.iterdir()
                     if (folder / 'all.jsonl').exists() and (not wanted or folder.name in wanted))
    if not subsets:
        raise SystemExit('no subsets under ' + str(data_root))
    suite = {}
    for subset in subsets:
        folder = out_root / subset
        folder.mkdir(parents=True, exist_ok=True)
        summary_path = folder / 'summary.json'
        if summary_path.exists():
            suite[subset] = json.loads(summary_path.read_text())
            print('skip %-22s already complete' % subset, flush=True)
            continue
        records = [json.loads(line) for line in (data_root / subset / 'all.jsonl')
                   .read_text(encoding='utf-8').split('\n') if line.strip()]
        rows = []
        began = time.perf_counter()
        with (folder / 'rows.jsonl').open('w', encoding='ascii') as stream:
            for record in records:
                kind = record['input']['questions']['decision']['type']
                started = time.perf_counter()
                answer = post(base, record['input'])['answers']['decision']
                ms = (time.perf_counter() - started) * 1000.0
                distribution = probabilities(answer)
                scored = assess(kind, distribution, record['reference']['target'])
                row = {'id': record['id'], 'subset': subset, 'domain': record['domain'], 'type': kind,
                       'target': record['reference']['target'], 'ms': ms, 'probabilities': distribution,
                       'server_choice': answer.get('choice'), 'server_score': answer.get('score'),
                       **{key: value for key, value in scored.items()}}
                rows.append(row)
                stream.write(json.dumps(row, ensure_ascii=True) + '\n')
                stream.flush()
        summary = {'subset': subset, 'types': sorted({row['type'] for row in rows}),
                   'wall_seconds': round(time.perf_counter() - began, 1),
                   'all': summarize(rows), 'by_type': by_type(rows)}
        summary_path.write_text(json.dumps(summary, indent=2))
        suite[subset] = summary
        print('done %-22s %3d/%3d correct (%.1f%%)  %.1fs'
              % (subset, summary['all']['correct'], summary['all']['count'],
                 100.0 * summary['all']['accuracy'], summary['wall_seconds']), flush=True)
    aggregate = {'subsets': {name: {'count': value['all']['count'], 'correct': value['all']['correct'],
                                    'accuracy': value['all']['accuracy'], 'types': value['types']}
                             for name, value in suite.items()}}
    counts = [value['count'] for value in aggregate['subsets'].values()]
    aggregate['macro_accuracy'] = statistics.mean(value['accuracy'] for value in aggregate['subsets'].values())
    aggregate['micro_accuracy'] = (sum(value['correct'] for value in aggregate['subsets'].values())
                                   / sum(counts))
    aggregate['records'] = sum(counts)
    for kind in ('noul', 'choice', 'score'):
        selected = [value for value in suite.values() if value['types'] == [kind]]
        if selected:
            aggregate['by_type'] = aggregate.get('by_type', {})
            aggregate['by_type'][kind] = {
                'subsets': len(selected),
                'macro_accuracy': statistics.mean(value['all']['accuracy'] for value in selected),
                'micro_accuracy': (sum(value['all']['correct'] for value in selected)
                                   / sum(value['all']['count'] for value in selected)),
                'records': sum(value['all']['count'] for value in selected)}
    (out_root / 'suite.json').write_text(json.dumps(aggregate, indent=2))
    print(json.dumps(aggregate, indent=2), flush=True)


if __name__ == '__main__':
    main()
