"""deep_report.py - turn the two knowledge-deep results into a table and a blind scorecard.

Machine metrics come straight from the result JSONs (grounding and exact-figure checks against the
pinned Wikipedia corpus). The open-ended parts - argument quality, whether the 25 facts are varied and
worth knowing, whether the paper is any good - are NOT measurable by the corpus checks, so this also
writes a scorecard with the two stacks' outputs relabelled A and B, hiding which model wrote which.
The mapping stays in the result JSONs; it is deliberately not repeated in the scorecard.

Usage: python deep_report.py
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PAIRS = (('qwen36-deep', 'strata-deep'),)
SCORECARD = HERE / 'DEEP-SCORECARD.md'


def load(label):
    return json.loads((HERE / ('knowledge-deep-result-%s.json' % label)).read_text(encoding='ascii'))


def main():
    labels = PAIRS[0]
    missing = [l for l in labels if not (HERE / ('knowledge-deep-result-%s.json' % l)).exists()]
    if missing:
        print('missing results:', missing)
        return 2
    results = {label: load(label) for label in labels}
    names = {label: results[label]['responder'] for label in labels}
    print('corpus sha256 %s (anchor %s)\n' % (results[labels[0]]['corpus_sha256'][:16],
                                              results[labels[0]]['anchor']))
    header = '%-16s %-10s %8s %8s %8s %8s' % ('stack', 'form', 'n', 'grounded', 'figures', 'extra')
    print(header)
    print('-' * len(header))
    for label in labels:
        forms = results[label]['forms']
        if 'reason' in forms:
            f = forms['reason']
            print('%-16s %-10s %8d %8s %8s %8s' % (label, 'reason', f['items'], '-', '-',
                                                   'letters %d/%d, distractors %.1f'
                                                   % (f['letter_correct'], f['items'],
                                                      f['mean_distractors_addressed'])))
        if 'facts' in forms:
            f = forms['facts']
            print('%-16s %-10s %8d %8.3f %8s %8s' % (label, 'facts', f['facts_listed'], f['grounded'],
                                                     f['numeric_rate'] if f['numeric_rate'] is not None else '-',
                                                     'ungrounded %d, with figures %d'
                                                     % (f['facts_ungrounded'], f['facts_with_numbers'])))
        if 'paper' in forms:
            f = forms['paper']
            figures = [p['numeric_rate'] for p in f['rows'] if p['numeric_rate'] is not None]
            print('%-16s %-10s %8d %8.3f %8s %8s' % (label, 'paper', f['papers'], f['grounded'],
                                                     ('%.2f' % (sum(figures) / len(figures))) if figures else '-',
                                                     'mean %d words, on-subject %d/%d, topics %d'
                                                     % (f['mean_words'], f['on_subject'], f['papers'],
                                                        f['distinct_topics'])))
    print()
    if 'reason' in results[labels[0]]['forms'] and 'reason' in results[labels[1]]['forms']:
        a = {r['id']: r for r in results[labels[0]]['forms']['reason']['rows']}
        b = {r['id']: r for r in results[labels[1]]['forms']['reason']['rows']}
        shared = sorted(set(a) & set(b))
        agree = sum(1 for i in shared if a[i]['letter_ok'] == b[i]['letter_ok'])
        print('reason form: %d shared items, %d identical outcomes, qwen36 %d correct, strata %d correct'
              % (len(shared), agree, sum(1 for i in shared if a[i]['letter_ok']),
                 sum(1 for i in shared if b[i]['letter_ok'])))

    order = list(labels)
    lines = ['# Scorecard: tied-topic expansion (Mars)', '',
             'Both stacks answered the same pinned prompts (temperature 0). Machine checks are exact:',
             '`grounded` = share of sentences naming a proper noun the pinned corpus uses mid-sentence or',
             'citing a figure that occurs in the corpus; `figures` = share of the distinctive numeric',
             'claims that occur in the corpus. Those checks cannot judge **truth, relevance or argument**',
             'quality - that is what this scorecard is for.', '',
             'Metrics (see the run output for the full table):', '']
    for label in order:
        forms = results[label]['forms']
        lines.append('- **%s**' % 'A' if label == order[0] else '- **%s**' % 'B')
        if 'facts' in forms:
            f = forms['facts']
            lines.append('  - facts: %d listed, grounded %.3f, ungrounded %d, figures %s'
                         % (f['facts_listed'], f['grounded'], f['facts_ungrounded'], f['numeric_rate']))
        if 'paper' in forms:
            f = forms['paper']
            lines.append('  - papers: mean %d words, grounded %.3f, on-subject %d/%d'
                         % (f['mean_words'], f['grounded'], f['on_subject'], f['papers']))
    lines += ['', '## How to score each item (0-3)', '',
              '1. **On-topic and specific** - real Mars-science subject, not vague filler.',
              '2. **Reasoning** - argues, uses evidence, engages the strongest counter-point.',
              '3. **Accuracy** - claims you can spot-check are right (the machine checks covered entities',
              '   and figures; you are looking for wrong statements that use real names).',
              '4. **Value** - would you learn something, or is it well-formed emptiness?', '']
    for form in ('facts', 'paper'):
        lines += ['## %s' % form.title(), '']
        for index, label in enumerate(order):
            forms = results[label]['forms']
            if form not in forms:
                continue
            letter = 'AB'[index]
            if form == 'facts':
                rows = forms['facts']['rows']
                lines += ['### %s: facts list (%d lines)' % (letter, len(rows)), '']
                for row in rows:
                    lines.append('- %s' % row['fact'].replace('\n', ' '))
                lines += ['', 'Score %s: on-topic __/3  accuracy __/3  value __/3  notes:' % letter, '']
            else:
                for paper in forms['paper']['rows']:
                    lines += ['### %s: paper %d - topic line: %s'
                              % (letter, paper['seed_index'], paper['topic_line']), '',
                              '`words %d, paragraphs %d, grounded %.2f, figures %s`'
                              % (paper['words'], paper['paragraphs'], paper['grounded'],
                                 paper['numeric_rate']), '']
                    lines += [paper['reply'].rstrip(), '',
                              'Score %s/p%d: on-topic __/3  reasoning __/3  accuracy __/3  value __/3' % (letter, paper['seed_index']), '']
    SCORECARD.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print('wrote %s (A/B relabelled; the mapping is only in the result JSONs)' % SCORECARD.name)
    print('A = %s, B = %s' % (order[0], order[1]))
    return 0


if __name__ == '__main__':
    sys.exit(main())
