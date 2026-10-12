"""morning_report.py - read the overnight queue's results and score the recorded predictions.

Run after `runner.py` finishes (or any time, with --partial). It only reads: the item results, the knowledge
and deep instrument artifacts the items produced, and the item logs. It writes REPORT-SUMMARY.md next to
itself and prints the same to stdout.
"""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
KNOWLEDGE = Path(r'C:\Users\kevin\ai_bench\new-items-20261007')
PREDICTIONS = {
    'i1-strata-placement': 'replies differ on 20-60% of items; letters differ on at most 3 of 93; correctness within 2',
    'i2-kolibri-knowledge': 'within 3 points of the two leaders (85-92%); GSM8K not worse than MMLU',
    'i3-colibri-qwen36': 'accuracy inside 2 points of 88.5%; wall time is the interesting number',
    'i4-reason-repeat': '90/93 and 92/93 again',
    'i5-papers-repeat': 'Qwen3.6 one distinct topic, Strata two or three',
    'i6-gliner-replay': 'warm p95 20-35 s, 0/4 stalls caught',
}


def load(path):
    try:
        return json.loads(Path(path).read_text(encoding='utf-8', errors='replace'))
    except Exception:
        return None


def knowledge_summary(path):
    data = load(path)
    if not data:
        return None
    out = {'passed': data.get('passed'), 'total': data.get('total'),
           'rate_pct': round(100 * data.get('rate', 0), 1),
           'seconds': round(data.get('seconds', 0), 0),
           'per_item_s': round(data.get('seconds', 0) / max(1, data.get('total', 1)), 2),
           'failures': len(data.get('failures', []))}
    for key in ('per_suite', 'per_subject'):
        if key in data:
            out[key] = {k: (round(100 * v['rate'], 1) if isinstance(v, dict) and 'rate' in v else v)
                        for k, v in data[key].items()}
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--partial', action='store_true')
    args = parser.parse_args()

    lines = ['# Overnight summary, from the queue artifacts', '']
    status = load(ROOT / 'status.json') or {}
    lines.append('Queue: %s (%s)' % (status.get('declared', '?'), status.get('stopped', '?')))
    lines.append('')
    lines.append('| item | exit | seconds | prediction recorded before the run |')
    lines.append('|---|---|---|---|')
    for entry in status.get('results', []):
        lines.append('| `%s` | %s | %.0f | %s |'
                     % (entry['id'], entry['exit'], entry['seconds'], PREDICTIONS.get(entry['id'], '')))
    lines.append('')

    placement = load(ROOT / 'result-i1-strata-placement.json')
    lines.append('## i1 placement versus output (Strata, 2 GiB vs 8 GiB resident)')
    if placement:
        lines.append('Same 93 shared-correct items, everything else identical: **%d of %d replies differ**, '
                     'chosen letters differ on **%d**, correctness **%s vs %s** (%s).'
                     % (placement['replies_differing'], placement['items'], placement['letters_differing'],
                        placement['correct_at_2gib'], placement['correct_at_8gib'], placement['codes']))
        lines.append('Differing item ids: %s' % ', '.join(placement['differing_ids']) or 'none')
    else:
        lines.append('no result file')
    lines.append('')

    lines.append('## i2 Kolibri-1 78B on the 1,100-item knowledge set')
    kolibri = knowledge_summary(KNOWLEDGE / 'knowledge-result-kolibri-131072.json')
    if kolibri:
        lines.append('**%d/%d = %.1f%%** in %.0f s (%.2f s per item), %d failures.'
                     % (kolibri['passed'], kolibri['total'], kolibri['rate_pct'], kolibri['seconds'],
                        kolibri['per_item_s'], kolibri['failures']))
        for key in ('per_suite', 'per_subject'):
            if key in kolibri:
                lines.append('- %s: %s' % (key, kolibri[key]))
        lines.append('- for reference: Qwen3.6-35B-A3B Q4 88.5%, Strata Q2_0 89.7%')
    else:
        lines.append('no result')
    lines.append('')

    lines.append('## i3 Colibri Qwen3.6-35B-A3B (same 1,100 items, second engine)')
    colibri = knowledge_summary(KNOWLEDGE / 'knowledge-result-colibri-qwen36-131072.json')
    lines.append(json.dumps(colibri) if colibri else 'no result - the item timed out at 7200 s; see logs/i3-colibri-qwen36.log')
    lines.append('')

    lines.append('## i4 reasoning repeat')
    for label in ('qwen36-deep-93-rep1', 'strata-deep-93-rep1'):
        data = load(KNOWLEDGE / ('knowledge-deep-result-%s.json' % label))
        if data and 'reason' in data.get('forms', {}):
            form = data['forms']['reason']
            lines.append('- %s: **%d/%d** letters' % (label, form['letter_correct'], form['items']))
    lines.append('- first run was qwen36 90/93 and strata 92/93')
    lines.append('')

    lines.append('## i5 paper form repeated')
    for label in ('qwen36-deep-rep1', 'strata-deep-rep1'):
        data = load(KNOWLEDGE / ('knowledge-deep-result-%s.json' % label))
        if data and 'paper' in data.get('forms', {}):
            form = data['forms']['paper']
            lines.append('- %s: %d papers, **%d distinct topics**, %.0f mean words'
                         % (label, form['papers'], form['distinct_topics'], form['mean_words']))
            for row in form['rows']:
                lines.append('  - %s' % row['topic_line'][:90])
    lines.append('- first run: qwen36 1 distinct topic, strata 2')
    lines.append('')

    lines.append('## i6 GLiNER2.5-Decide on Colibri')
    gliner = load(ROOT / 'gliner-colibri.json')
    if gliner:
        lines.append('noul: correct %s/%s, stalls caught %s/%s, false alarms %s/%s; warm p95 %s ms'
                     % (gliner['noul']['correct'], gliner['noul']['total'], gliner['noul']['stalls_caught'],
                        gliner['noul']['stalls_total'], gliner['noul']['false_alarms'],
                        gliner['noul']['nonstalls_total'], gliner['latency_ms']['noul_warm_p95']))
    else:
        lines.append('no result - the item exited 1; see logs/i6-gliner-replay.log')
    lines.append('')

    report = '\n'.join(lines) + '\n'
    (ROOT / 'REPORT-SUMMARY.md').write_text(report, encoding='utf-8')
    print(report)


if __name__ == '__main__':
    main()
