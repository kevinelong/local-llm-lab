"""Classify why a session scored badly: turn structure, stop reasons, wire finish_reason, artifact.

Item: whether the *other* catastrophic failures (MiniCPM `paths` 9/75, gpt-oss `events` 0/76,
MiniCPM `events` 0/76) are model failures or turn-termination artifacts, using the method that
explained the Strata ledger. Read-only.

Usage: python classify.py ROOT LABEL [ROOT LABEL ...]
"""
import json
import sys
from pathlib import Path

BASE = Path(r'C:\Users\kevin\ai_bench')


def folder_for(root, label):
    base = BASE / root
    hits = [p.parent for p in base.glob('**/events.jsonl')
            if ('oms-' + label) in str(p) or p.parent.name == label or p.parent.parent.name.endswith('-' + label)]
    preferred = [h for h in hits if h.name == 'trial'] or hits
    return preferred[0] if preferred else None


def describe(folder):
    events = [json.loads(l) for l in (folder / 'events.jsonl').read_text(encoding='utf-8').splitlines() if l.strip()]
    print('  events: %d' % len(events))
    turns = []
    for e in events:
        if e.get('type') != 'message_end':
            continue
        m = e.get('message') or {}
        role = m.get('role')
        if role != 'assistant':
            continue
        content = m.get('content')
        parts = []
        if isinstance(content, list):
            for part in content:
                if not isinstance(part, dict):
                    parts.append('?'); continue
                kind = part.get('type')
                if kind == 'thinking':
                    parts.append('think(%d)' % len(part.get('thinking') or ''))
                elif kind == 'text':
                    parts.append('text(%d)' % len(part.get('text') or ''))
                elif kind == 'toolCall':
                    parts.append('call:%s(%d)' % (part.get('name'), len(json.dumps(part.get('arguments') or {}))))
                else:
                    parts.append(str(kind))
        turns.append((m.get('stopReason'), parts))
    print('  assistant turns: %d' % len(turns))
    for i, (stop, parts) in enumerate(turns, 1):
        print('    %-3d %-10s %s' % (i, stop, ', '.join(parts)[:150]))
    calls = sum(1 for e in events if e.get('type') == 'tool_execution_start')
    print('  tool executions: %d' % calls)
    # wire finish reasons
    wire = folder / 'wire'
    if wire.is_dir():
        reasons = {}
        for s in sorted(wire.glob('*.sse')):
            text = s.read_text(encoding='utf-8', errors='replace')
            for token in ('"finish_reason": "length"', '"finish_reason":"length"', '"finish_reason": "stop"', '"finish_reason":"stop"',
                          '"finish_reason": "tool_calls"', '"finish_reason":"tool_calls"'):
                if token in text:
                    key = token.split(':')[1].strip().strip('"')
                    reasons[key] = reasons.get(key, 0) + 1
        print('  wire finish_reason: %s' % (reasons or 'none found'))
    # artifact vs starter
    artifact = folder / 'final-artifact.py'
    workspace = folder / 'workspace'
    for path, name in ((artifact, 'final-artifact.py'), (workspace / 'solution.py', 'workspace/solution.py')):
        if path.exists():
            text = path.read_text(encoding='utf-8', errors='replace')
            print('  %-22s %d bytes, %d lines' % (name, len(text), text.count('\n') + 1))
    result = folder / 'result.json'
    if result.exists():
        r = json.loads(result.read_text(encoding='utf-8'))
        ev = r.get('evaluation') or {}
        print('  result: %s/%s clean=%s correct=%s exit=%s tokens=%s seconds=%.1f' % (
            ev.get('passed'), ev.get('total'), r.get('clean_finish'), r.get('correct'),
            r.get('exit_code'), r.get('completion_tokens'), r.get('seconds') or 0))
        bad = [c['case'] for c in (ev.get('checks') or []) if not c.get('pass')]
        print('  failing checks: %s%s' % (bad[:12], ' ...' if len(bad) > 12 else ''))


def main():
    pairs = list(zip(sys.argv[1::2], sys.argv[2::2]))
    for root, label in pairs:
        folder = folder_for(root, label)
        print('=' * 100)
        print('%s / %s' % (root, label))
        if folder is None:
            print('  no events.jsonl found')
            continue
        describe(folder)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
