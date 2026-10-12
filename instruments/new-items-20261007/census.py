"""Census every session on disk: how it ended, and whether a sub-perfect score was the model's fault.

Motivated by the finding that MiniCPM `paths` 9/75 and the Strata ledger failures are the same
mechanism: a reply truncated inside its thinking (stopReason=length, no tool call), which ends the
agent loop before it acts. This census counts that class against genuine model errors, historical.

Classification of a session with score < total:
  TRUNCATED_TURN   last assistant turn has stopReason=length and no tool call
  EXTERNAL_KILL    exit code 143/1 (SIGTERM/forced stop) with no truncation signature
  OTHER            ended normally (stop/toolUse) but the artifact is still wrong

Usage: python census.py [root-filter]
"""
import json
import sys
from pathlib import Path

BASE = Path(r'C:\Users\kevin\ai_bench')


def sessions(filter_text=None):
    for root in sorted(BASE.glob('*2026*')):
        if not root.is_dir():
            continue
        if filter_text and filter_text not in root.name:
            continue
        for events_path in sorted(root.glob('**/events.jsonl')):
            folder = events_path.parent
            result_path = folder / 'result.json'
            if result_path.exists():
                yield root, folder, events_path, result_path


def analyse(events_path, result_path):
    turns = []
    for line in events_path.read_text(encoding='utf-8', errors='replace').splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if event.get('type') != 'message_end':
            continue
        message = event.get('message') or {}
        if message.get('role') != 'assistant':
            continue
        content = message.get('content')
        has_call = False
        thinking = 0
        if isinstance(content, list):
            for part in content:
                if isinstance(part, dict):
                    if part.get('type') == 'toolCall':
                        has_call = True
                    elif part.get('type') == 'thinking':
                        thinking = max(thinking, len(part.get('thinking') or ''))
        turns.append({'stop': message.get('stopReason'), 'call': has_call, 'think': thinking})
    result = json.loads(result_path.read_text(encoding='utf-8'))
    evaluation = result.get('evaluation') or {}
    return turns, result, evaluation


def main():
    filter_text = sys.argv[1] if len(sys.argv) > 1 else None
    rows = []
    for root, folder, events_path, result_path in sessions(filter_text):
        try:
            turns, result, evaluation = analyse(events_path, result_path)
        except Exception as exc:
            continue
        passed, total = evaluation.get('passed'), evaluation.get('total')
        if passed is None or not total:
            continue
        last = turns[-1] if turns else {}
        if passed == total:
            kind = 'COMPLETE'
        elif last.get('stop') == 'length' and not last.get('call'):
            kind = 'TRUNCATED_TURN'
        elif result.get('exit_code') in (143, 1, -1):
            kind = 'EXTERNAL_KILL'
        else:
            kind = 'OTHER'
        rows.append({'root': root.name, 'folder': str(folder.relative_to(root)), 'passed': passed, 'total': total,
                     'kind': kind, 'last_stop': last.get('stop'), 'turns': len(turns),
                     'think': last.get('think'), 'tokens': result.get('completion_tokens'),
                     'exit': result.get('exit_code'), 'clean': result.get('clean_finish'),
                     'seconds': round(result.get('seconds') or 0, 1)})
    print('%-26s %-14s %-8s %-15s %-10s %-6s %-8s %s' % ('root', 'session', 'score', 'class', 'last_stop', 'turns', 'think', 'exit'))
    for r in rows:
        print('%-26s %-14s %-8s %-15s %-10s %-6s %-8s %s' % (
            r['root'], r['folder'].split('\\')[-1][:14], '%s/%s' % (r['passed'], r['total']), r['kind'],
            r['last_stop'], r['turns'], r['think'], r['exit']))
    counts = {}
    for r in rows:
        counts[r['kind']] = counts.get(r['kind'], 0) + 1
    print()
    print('sessions: %d  |  %s' % (len(rows), counts))
    bad = [r for r in rows if r['kind'] != 'COMPLETE']
    print('sub-perfect: %d  |  %s' % (len(bad), {k: sum(1 for r in bad if r['kind'] == k) for k in counts if k != 'COMPLETE'}))
    for r in bad:
        print('   %-24s %-14s %-8s %-15s stop=%-8s exit=%s think=%s' % (
            r['root'], r['folder'].split('\\')[-1][:14], '%s/%s' % (r['passed'], r['total']), r['kind'], r['last_stop'], r['exit'], r['think']))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
