"""paired.py - is the kev4-vs-nimble gap real? Paired analysis of the frozen decision-suite rows.

Why this before more passes: both models are scored on the *same* 3,880 records, so their difference is
paired and the uncertainty can be read off the discordant pairs - no new inference. A second full pass
would mainly re-measure the endpoint's determinism (the lab already found two bit-identical passes on the
18-window set), while this asks the actual question: are the observed 0.5-point macro gaps larger than
sampling noise?

Reports, per subset and pooled:
  - discordant pairs b (kev4 right, nimble wrong) and c (the reverse), with McNemar's exact two-sided p;
  - the accuracy difference, and for binary subsets the balanced-accuracy difference with its components
    (positive and negative recall);
  - a paired bootstrap CI for the macro difference under both metrics (records resampled within subset,
    so the macro structure is preserved).

Nothing is written outside this root; the suite roots stay frozen.

Usage: python paired.py
"""
import json
import math
import random
import sys
from pathlib import Path

BASE = Path(r'C:\Users\kevin\ai_bench')
NEWER = BASE / 'bespoke-suite-20261010-v1' / 'evidence'          # kev4/nimble post-RAM-upgrade
OLDER = BASE / 'bespoke-suite-20261005-v1' / 'evidence'          # kev4/nimble pre-upgrade
import os
ROOT = NEWER if os.environ.get('SUITE_ROOT') == 'new' else OLDER
A = ('kev4', ROOT / 'kev4-suite' / 'runs')
B = ('nimble', ROOT / 'nimble-suite' / 'runs')
RESAMPLES = 4000
RNG = random.Random(20261010)


def load(runs):
    subsets = {}
    for directory in sorted(runs.iterdir()):
        if not directory.is_dir():
            continue
        rows = [json.loads(l) for l in (directory / 'rows.jsonl').read_text(encoding='utf-8').splitlines() if l.strip()]
        if rows:
            subsets[directory.name] = {r['id']: r for r in rows}
    return subsets


def mcnemar_exact(b, c):
    """Two-sided exact McNemar: 2 * P(X <= min(b, c)) with X ~ Binomial(b + c, 0.5)."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / (2 ** n)
    return min(1.0, 2 * tail)


def recalls(rows, model_key):
    pos = [r for r in rows if r['target'] in (True, 1)]
    neg = [r for r in rows if r['target'] in (False, 0)]
    pr = (sum(1 for r in pos if r[model_key]) / len(pos)) if pos else None
    nr = (sum(1 for r in neg if r[model_key]) / len(neg)) if neg else None
    vals = [x for x in (pr, nr) if x is not None]
    return pr, nr, (sum(vals) / len(vals) if vals else None)


def main():
    sa, sb = load(A[1]), load(B[1])
    subsets = sorted(set(sa) & set(sb))
    print('subsets compared: %d, models: %s vs %s, resamples: %d\n' % (len(subsets), A[0], B[0], RESAMPLES))
    header = '%-22s %6s %7s %7s %5s %5s %8s  %s' % ('subset', 'n', 'acc_A', 'acc_B', 'b', 'c', 'p_mcnemar', 'balanced A vs B')
    print(header)
    print('-' * len(header))
    table, pooled = {}, {'b': 0, 'c': 0, 'n': 0, 'a': 0, 'b_correct': 0}
    for name in subsets:
        ids = sorted(set(sa[name]) & set(sb[name]))
        assert len(ids) == len(sa[name]) == len(sb[name]), 'id mismatch in %s' % name
        rows = [{'target': sa[name][i]['target'], 'a': bool(sa[name][i]['correct']), 'b': bool(sb[name][i]['correct'])}
                for i in ids]
        n = len(rows)
        a_ok = sum(1 for r in rows if r['a'])
        b_ok = sum(1 for r in rows if r['b'])
        discord_b = sum(1 for r in rows if r['a'] and not r['b'])
        discord_c = sum(1 for r in rows if r['b'] and not r['a'])
        p = mcnemar_exact(discord_b, discord_c)
        binary = sa[name][ids[0]]['type'] == 'noul'
        bal = ''
        if binary:
            pr_a, nr_a, bal_a = recalls(rows, 'a')
            pr_b, nr_b, bal_b = recalls(rows, 'b')
            bal = '%.3f vs %.3f (pos-rec %.2f vs %.2f)' % (bal_a, bal_b, pr_a, pr_b)
        table[name] = {'n': n, 'binary': binary, 'family': sa[name][ids[0]]['type'],
                       'acc_a': a_ok / n, 'acc_b': b_ok / n,
                       'discordant_kev4_only': discord_b, 'discordant_nimble_only': discord_c, 'p_mcnemar': p,
                       'rows': rows}
        pooled['b'] += discord_b
        pooled['c'] += discord_c
        pooled['n'] += n
        pooled['a'] += a_ok
        pooled['b_correct'] += b_ok
        print('%-22s %6d %7.3f %7.3f %5d %5d %8.4f  %s'
              % (name, n, a_ok / n, b_ok / n, discord_b, discord_c, p, bal))

    print('\npooled (record-level): %d records, %s %.4f vs %s %.4f'
          % (pooled['n'], A[0], pooled['a'] / pooled['n'], B[0], pooled['b_correct'] / pooled['n']))
    print('pooled discordant: kev4-only %d, nimble-only %d, McNemar exact p = %.4f'
          % (pooled['b'], pooled['c'], mcnemar_exact(pooled['b'], pooled['c'])))

    print('\nby metric family (the Oct 8 recommendation: never average these into one macro):')
    for family in ('noul', 'choice', 'score'):
        names = [n for n in subsets if table[n]['family'] == family]
        if not names:
            continue
        records = sum(table[n]['n'] for n in names)
        a_ok = sum(round(table[n]['acc_a'] * table[n]['n']) for n in names)
        b_ok = sum(round(table[n]['acc_b'] * table[n]['n']) for n in names)
        db = sum(table[n]['discordant_kev4_only'] for n in names)
        dc = sum(table[n]['discordant_nimble_only'] for n in names)
        print('  %-6s %d subsets %4d records  kev4 %.4f vs nimble %.4f  diff %+.4f  discordant %d/%d  p = %.4f'
              % (family, len(names), records, a_ok / records, b_ok / records,
                 (a_ok - b_ok) / records, db, dc, mcnemar_exact(db, dc)))

    for metric in ('accuracy', 'balanced'):
        observed = 0.0
        for name, t in table.items():
            if metric == 'balanced' and t['binary']:
                _, _, ra = recalls(t['rows'], 'a')
                _, _, rb = recalls(t['rows'], 'b')
                observed += (ra - rb) / len(table)
            else:
                observed += (t['acc_a'] - t['acc_b']) / len(table)
        diffs = []
        names = list(table)
        for _ in range(RESAMPLES):
            total = 0.0
            for name in names:
                t = table[name]
                idx = [RNG.randrange(t['n']) for _ in range(t['n'])]
                rows = [t['rows'][i] for i in idx]
                if metric == 'balanced' and t['binary']:
                    _, _, ra = recalls(rows, 'a')
                    _, _, rb = recalls(rows, 'b')
                    total += (ra - rb)
                else:
                    total += (sum(1 for r in rows if r['a']) - sum(1 for r in rows if r['b'])) / t['n']
            diffs.append(total / len(names))
        diffs.sort()
        lo, hi = diffs[int(0.025 * len(diffs))], diffs[int(0.975 * len(diffs))]
        crosses = lo <= 0 <= hi
        print('macro difference (%s - %s), %s: %+.4f  95%% CI [%+.4f, %+.4f]  %s'
              % (A[0], B[0], metric, observed, lo, hi, 'crosses zero' if crosses else 'excludes zero'))

    out = Path(__file__).resolve().parent / 'paired.json'
    out.write_text(json.dumps({'generated': '2026-10-10', 'models': [A[0], B[0]], 'resamples': RESAMPLES,
                               'subsets': {k: {kk: vv for kk, vv in v.items() if kk != 'rows'} for k, v in table.items()},
                               'pooled': pooled}, indent=1), encoding='utf-8')
    print('\nwrote %s' % out)
    return 0


if __name__ == '__main__':
    sys.exit(main())
