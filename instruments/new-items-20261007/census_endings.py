"""Per-model ending census: how each model's sessions actually finish.

The whole-history census found that 45 % of sub-perfect sessions were harness-mediated and the single
largest class was the *prose-quit* - the model writing a completion summary while hidden checks still
failed. That was a global number. This breaks it down per model, because "how often does this model
declare victory early" is a reliability axis the scores do not show.

For every task session on disk with both events.jsonl and result.json:
  ending      summary-all-passed | summary-with-failures | truncated | killed | error | no-turn
  score       passed/total
where a "summary" is an assistant turn with text and no tool call, `truncated` is
stopReason=length with no tool call, `killed` is exit 143, and `error` is a stopReason of error.

Read-only. Usage: python census_endings.py [model-substring]
"""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

BASE = Path(r'C:\Users\kevin\ai_bench')


def sessions():
    for pattern in ('candidates-*', 'truncation-*', 'newtasks*', 'provision-*'):
        for events in sorted(BASE.glob(pattern + '/**/events.jsonl')):
            folder = events.parent
            result = folder / 'result.json'
            if not result.exists():
                continue
            # model = the session folder's name minus the task suffix
            name = folder.parent.name if folder.name in ('trial', 'runs') else folder.name
            yield name, events, result


def classify(events, result):
    turns = []
    for line in events.read_text(encoding='utf-8', errors='replace').splitlines():
        if '"message_end"' not in line:
            continue
        try:
            event = json.loads(line)
        except ValueError:
            continue
        message = event.get('message') or {}
        if message.get('role') != 'assistant':
            continue
        content = message.get('content') or []
        turns.append({'stop': message.get('stopReason'),
                      'call': any(isinstance(p, dict) and p.get('type') == 'toolCall' for p in content),
                      'text': sum(len(p.get('text') or '') for p in content if isinstance(p, dict) and p.get('type') == 'text')})
    data = json.loads(result.read_text(encoding='utf-8'))
    evaluation = data.get('evaluation') or {}
    passed, total = evaluation.get('passed'), evaluation.get('total')
    last = turns[-1] if turns else {}
    if not turns:
        ending = 'no-turn'
    elif passed is None or not total:
        # smoke sessions (parser/host probes) have no evaluation at all - they are not failures
        ending = 'no-evaluation'
    elif last.get('stop') == 'length' and not last.get('call'):
        ending = 'truncated'
    elif data.get('exit_code') in (143, -1):
        ending = 'killed'
    elif last.get('stop') == 'error':
        ending = 'error'
    elif not last.get('call') and last.get('text', 0) > 0:
        ending = 'summary-all-passed' if (passed is not None and total and passed == total) else 'summary-with-failures'
    elif not last.get('call'):
        ending = 'quiet-stop'
    else:
        ending = 'other'
    return ending, passed, total, len(turns)


def main():
    wanted = sys.argv[1] if len(sys.argv) > 1 else None
    per_model = defaultdict(Counter)
    scores = defaultdict(lambda: [0, 0])
    for name, events, result in sessions():
        if wanted and wanted not in name:
            continue
        try:
            ending, passed, total, turns = classify(events, result)
        except Exception:
            continue
        model = name.rsplit('-', 1)[0] if name.count('-') else name
        per_model[model][ending] += 1
        if passed is not None and total:
            scores[model][0] += passed
            scores[model][1] += total
    print('%-30s %5s %8s %9s %7s %8s %7s %6s %8s %8s' % (
        'model', 'sess', 'sum-pass', 'sum-fail', 'honest', 'trunc', 'killed', 'error', 'smoke', 'checks'))
    for model, counter in sorted(per_model.items(), key=lambda kv: -sum(kv[1].values())):
        got, tot = scores[model]
        judged = counter['summary-all-passed'] + counter['summary-with-failures']
        honest = ('%.0f%%' % (100 * counter['summary-all-passed'] / judged)) if judged else '-'
        print('%-30s %5d %8d %9d %7s %8d %7d %6d %6d %8s' % (
            model[:30], sum(counter.values()), counter['summary-all-passed'], counter['summary-with-failures'],
            honest, counter['truncated'], counter['killed'], counter['error'], counter['no-evaluation'],
            '%d/%d' % (got, tot) if tot else '-'))
    totals = Counter()
    for counter in per_model.values():
        totals.update(counter)
    print()
    print('all sessions: %d | %s' % (sum(totals.values()), dict(totals)))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
