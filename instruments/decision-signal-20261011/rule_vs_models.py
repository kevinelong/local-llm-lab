"""rule_vs_models.py - is the stall signal in the frozen windows readable by a rule, and did the models miss it?

Context: across every model this lab has screened for the stall-detection task, catches are 0 of 4 (Laya on
two engines, kev4, kev0, julia) except the lab's own deterministic rule, recorded 2026-09-25 as "identical-
failure / no-successful-mutation", which caught 1 of 4 with 0 of 14 false alarms. That rule required the
repeat to be an *error*. Reading the frozen features shows three of the four labelled stalls repeated a
*successful* action with byte-identical output - so this measures the error-agnostic version of the same rule
and a trail-wide variant, and reports what the models add on top.

Frozen inputs only; no inference, no network. Everything here is a small sample and the thresholds are
chosen on these same 18 labels, so this is **descriptive, not validation** - the lab's rule applies.

Usage: python rule_vs_models.py [--json out.json]
"""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

BASE = Path(r'C:\Users\kevin\ai_bench')
FOLLOWUP = BASE / 'local-decisions-followup-20260925-v1'
CANDIDATES = FOLLOWUP / 'natural-candidates.json'
LABELS = FOLLOWUP / 'natural-labels.json'
LAYA = BASE / 'colibri-laya-20261011' / 'laya-colibri-maxlen4096.json'


def outcome_hash(entry):
    """The repeated-pair entry carries sha256 already; a trail entry carries an outcome string."""
    if entry.get('sha256'):
        return entry['sha256']
    outcome = entry.get('outcome')
    return json.dumps(outcome, sort_keys=True)[:512] if outcome is not None else None


def rule_r1(case):
    """The lab's recorded rule: the same action repeated and both repeats ERRORED identically."""
    repeats = case.get('repeatOutcomes') or []
    errs = [e for e in repeats if e.get('isError')]
    return len(errs) >= 2 and len({outcome_hash(e) for e in errs}) == 1


def rule_r2(case):
    """Error-agnostic: the same action repeated and produced the SAME outcome, error or not."""
    repeats = case.get('repeatOutcomes') or []
    if len(repeats) < 2:
        return False
    return len({outcome_hash(e) for e in repeats}) == 1


def rule_r3(case):
    """Trail-wide: any (tool, input key) appearing twice with an identical outcome anywhere in the window."""
    seen = Counter()
    for entry in case.get('audit') or []:
        key = (entry.get('tool'), entry.get('key'), outcome_hash(entry))
        seen[key] += 1
    return any(count >= 2 for count in seen.values())


def rule_r5(case):
    """R2 plus the lab's original clause: no mutation actually succeeded in the window. The two false
    alarms R2 makes on these windows are repeats with a successful write/edit in between, i.e. progress."""
    if not rule_r2(case):
        return False
    for entry in case.get('audit') or []:
        if entry.get('tool') in ('write', 'edit'):
            outcome = entry.get('outcome')
            if isinstance(outcome, dict) and not outcome.get('isError'):
                return False
    return True


def rule_r6(case):
    """R2 plus a sharper progress test: a window shows no progress when every SUCCESSFUL mutation produced
    the same outcome. Three identical successful edits are as much a stall as three identical failures."""
    if not rule_r2(case):
        return False
    successes = set()
    for entry in case.get('audit') or []:
        if entry.get('tool') in ('write', 'edit'):
            outcome = entry.get('outcome')
            if isinstance(outcome, dict) and not outcome.get('isError'):
                successes.add(outcome.get('sha256'))
    return len(successes) <= 1


def score(predicate, cases, labels, ids):
    caught = [i for i in ids if predicate(cases[i]) and labels[i]]
    false = [i for i in ids if predicate(cases[i]) and not labels[i]]
    return {'caught': sorted(caught), 'false_alarms': sorted(false),
            'stalls_caught': len(caught), 'stalls_total': sum(1 for i in ids if labels[i]),
            'false_alarms_total': len(false), 'nonstalls_total': sum(1 for i in ids if not labels[i])}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--json', default=str(Path(__file__).resolve().parent / 'rule-vs-models.json'))
    args = parser.parse_args()

    cases = {c['id']: c for c in json.loads(CANDIDATES.read_text(encoding='utf-8'))}
    labels = {l['id']: bool(l['stuck']) for l in json.loads(LABELS.read_text(encoding='utf-8'))}
    ids = sorted(cases, key=lambda i: int(i.split('-')[1]))
    print('%d windows, %d labelled stalls' % (len(ids), sum(1 for i in ids if labels[i])))

    rules = {'R1 lab rule (identical ERROR repeat)': rule_r1,
             'R2 error-agnostic (identical outcome)': rule_r2,
             'R3 trail-wide (any repeated identical outcome)': rule_r3,
             'R5 R2 + no successful mutation': rule_r5,
             'R6 R2 + no DISTINCT successful outcome': rule_r6}
    out = {'windows': len(ids), 'stalls': sum(1 for i in ids if labels[i]), 'rules': {}}
    print('\n%-46s %8s %8s  %s' % ('rule', 'caught', 'false', 'ids caught'))
    for name, predicate in rules.items():
        result = score(predicate, cases, labels, ids)
        out['rules'][name] = result
        print('%-46s %5d/%-2d %5d/%-2d  %s'
              % (name, result['stalls_caught'], result['stalls_total'], result['false_alarms_total'],
                 result['nonstalls_total'], ', '.join(x.split('-')[1] for x in result['caught'])))

    if LAYA.exists():
        laya = json.loads(LAYA.read_text(encoding='utf-8'))
        noul = {r['id']: r.get('noul') for r in laya['rows']}
        choice = {r['id']: r.get('choice_prob') for r in laya['rows']}
        print('\nwhat Laya adds on top of R2 (descriptive):')
        for label, key, values in (('noul', 'noul', noul), ('choice workaround', 'choice', choice)):
            for threshold in (0.85, 0.70, 0.60):
                def combined(case, t=threshold, v=values):
                    return rule_r2(case) or (v.get(case['id']) is not None and v[case['id']] >= t)
                result = score(combined, cases, labels, ids)
                adds = [i for i in result['caught'] if not rule_r2(cases[i])]
                print('  R2 or %-16s at %.2f -> catches %d/4, false alarms %d/14 (Laya-only additions: %s)'
                      % (label, threshold, result['stalls_caught'], result['false_alarms_total'],
                         ', '.join(x.split('-')[1] for x in adds) or 'none'))
        out['laya_used'] = {'file': str(LAYA.name), 'noul': noul, 'choice_prob': choice}
        # is Laya's own signal complementary at all? correlation of its value with the label
        stalls = [noul[i] for i in ids if labels[i] and noul.get(i) is not None]
        others = [noul[i] for i in ids if not labels[i] and noul.get(i) is not None]
        print('  Laya noul mean: stalls %.4f vs non-stalls %.4f (difference %+.4f)'
              % (sum(stalls) / len(stalls), sum(others) / len(others),
                 sum(stalls) / len(stalls) - sum(others) / len(others)))

    Path(args.json).write_text(json.dumps(out, indent=1), encoding='utf-8')
    print('\nwrote %s' % args.json)
    print('\nDESCRIPTIVE ONLY: thresholds and rules chosen on these same 18 labels; a real detector needs a '
          'fresh labelled set.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
