"""Forensics for new items 3 and 4, on runs already on disk (no inference).

Item 3: why does the ledger session end after two or three turns?
  For every failing ledger session, report the agent's turn structure, tool calls, and the final
  assistant message (content vs reasoning), plus which checks failed. If the stop is "the model
  emitted a final message with no tool call", that is a model-behaviour stop; if a tool call failed or
  the response was empty, it is something else.

Item 4: did Strata v0.1.40.1's tool-call rescue change tool behaviour in the harness?
  The rescue turns a `<tool_call>` written inside thinking or a code fence into a real call. Compare
  tool-execution counts per session between the v0.1.39 runs and the v0.1.40.3 runs of the same tasks.

Usage: python forensics.py
"""
import glob
import json
import re
from collections import Counter
from pathlib import Path

BASE = Path(r'C:\Users\kevin\ai_bench')

LEDGER_FAILS = [
    ('strata-20261005-v1', 'oms-ledger'), ('strata-20261007-v1', 'oms-ledger'),
    ('strata-20261007-v3', 'oms-ledger'), ('strata-20261007-v15-1', 'oms-ledger'),
]


def summarise_session(session_dir, trial=None):
    # Strata roots keep events.jsonl directly under runs/oms-<task>; the candidates roots use a
    # trial/ subfolder. Accept either.
    candidates = [session_dir / 'events.jsonl', session_dir / 'trial' / 'events.jsonl']
    ev_path = next((p for p in candidates if p.exists()), candidates[0])
    result_path = ev_path.parent / 'result.json'
    out = {'dir': str(session_dir)}
    if result_path.exists():
        d = json.loads(result_path.read_text())
        e = d.get('evaluation') or {}
        out.update({'passed': e.get('passed'), 'total': e.get('total'),
                    'clean': d.get('clean_finish'), 'exit': d.get('exit_code'),
                    'tokens': d.get('completion_tokens'), 'seconds': round(d.get('seconds') or 0, 1),
                    'final_text_len': len(d.get('final_text') or '')})
    if not ev_path.exists():
        out['events'] = 'missing'
        return out
    events = [json.loads(l) for l in ev_path.read_text(encoding='utf8').splitlines() if l.startswith('{')]
    types = Counter(e.get('type') for e in events)
    tool_starts = [e for e in events if e.get('type') == 'tool_execution_start']
    assistant_msgs = [e for e in events if e.get('type') == 'message_end'
                      and ((e.get('message') or {}).get('role') == 'assistant')]
    reasoning_chars = 0
    content_chars = 0
    last_tool_calls = None
    for m in assistant_msgs:
        content = (m['message'].get('content') or [])
        if isinstance(content, list):
            for part in content:
                if part.get('type') == 'thinking':
                    reasoning_chars += len(part.get('thinking') or '')
                elif part.get('type') == 'text':
                    content_chars += len(part.get('text') or '')
        last_tool_calls = len(m['message'].get('tool_calls') or [])
    out.update({'turns': types.get('turn_start', 0), 'assistant_messages': len(assistant_msgs),
                'tool_calls_executed': len(tool_starts),
                'tools_used': Counter(t.get('toolName') for t in tool_starts).most_common(),
                'reasoning_chars': reasoning_chars, 'content_chars': content_chars,
                'last_message_tool_calls': last_tool_calls})
    return out


def main():
    print('ITEM 3 - failing ledger sessions, what actually happened')
    for root, label in LEDGER_FAILS:
        d = BASE / root / 'runs' / label
        if not d.exists():
            print('  %-22s missing' % root)
            continue
        info = summarise_session(d)
        print('  %-22s %s/%s clean=%s exit=%s tokens=%s turns=%s msgs=%s tools=%s last_tool_calls=%s reasoning=%s content=%s' % (
            root, info.get('passed'), info.get('total'), info.get('clean'), info.get('exit'),
            info.get('tokens'), info.get('turns'), info.get('assistant_messages'),
            info.get('tool_calls_executed'), info.get('last_message_tool_calls'),
            info.get('reasoning_chars'), info.get('content_chars')))
        if info.get('tools_used'):
            print('        tools used:', info['tools_used'])

    print('\nITEM 4 - tool executions per session, v0.1.39 versus v0.1.40.3')
    rows = []
    for path in sorted(glob.glob(str(BASE / 'strata-2026*' / 'runs' / 'oms-*' / 'events.jsonl'))):
        root = Path(path).parts[-4]
        task = Path(path).parent.name.replace('oms-', '')
        engine = 'v0.1.39' if root in ('strata-20261005-v1', 'strata-20261007-v1', 'strata-20261007-v2') else 'v0.1.40.3'
        events = [json.loads(l) for l in Path(path).read_text(encoding='utf8').splitlines() if l.startswith('{')]
        starts = [e for e in events if e.get('type') == 'tool_execution_start']
        msgs = [e for e in events if e.get('type') == 'message_end'
                and ((e.get('message') or {}).get('role') == 'assistant')]
        fc = sum(len((m['message'].get('tool_calls') or [])) for m in msgs)
        rows.append((engine, root, task, len(starts), fc, Counter(t.get('toolName') for t in starts).most_common(3)))
    for engine in ('v0.1.39', 'v0.1.40.3'):
        subset = [r for r in rows if r[0] == engine]
        print('  %s: %d sessions, tool executions %s, tool_calls in messages %s' % (
            engine, len(subset), [r[3] for r in subset], [r[4] for r in subset]))
        for r in subset:
            print('      %-22s %-8s executed=%-3d in_messages=%-3d %s' % (r[1], r[2], r[3], r[4], r[5]))
    # direct evidence of the rescue: a tool call written inside thinking
    print('\n  searching every strata transcript for tool-call markup inside reasoning:')
    hits = 0
    for path in glob.glob(str(BASE / 'strata-2026*' / 'runs' / 'oms-*' / 'events.jsonl')):
        for line in Path(path).read_text(encoding='utf8', errors='replace').splitlines():
            if '<tool_call>' in line and 'thinking' in line:
                hits += 1
                if hits <= 3:
                    print('    %s ... %s' % (Path(path).parts[-4], line[:160]))
    print('    lines containing both "<tool_call>" and "thinking":', hits)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
