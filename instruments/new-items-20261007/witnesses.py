"""Split the TRUNCATED_TURN class by cause: reply-cap truncation vs context exhaustion.

For every session the census classified as TRUNCATED_TURN, read the last wire call and report the
prompt size, the allowance (max_tokens) and the completion size, so a reply cut at its cap
(completion == allowance) can be told apart from a reply cut by the served context (prompt near the
context, small completion). Read-only.
"""
import json
import re
from pathlib import Path

BASE = Path(r'C:\Users\kevin\ai_bench')


def witness_rows():
    for root in sorted(BASE.glob('*2026*')):
        if not root.is_dir():
            continue
        for events_path in sorted(root.glob('**/events.jsonl')):
            folder = events_path.parent
            result_path = folder / 'result.json'
            if not result_path.exists():
                continue
            turns, last = [], None
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
                content = message.get('content') or []
                last = {'stop': message.get('stopReason'),
                        'call': any(isinstance(p, dict) and p.get('type') == 'toolCall' for p in content),
                        'think': max([len(p.get('thinking') or '') for p in content
                                      if isinstance(p, dict) and p.get('type') == 'thinking'] or [0]),
                        'text': max([len(p.get('text') or '') for p in content
                                     if isinstance(p, dict) and p.get('type') == 'text'] or [0])}
            if not last or last['stop'] != 'length' or last['call']:
                continue
            result = json.loads(result_path.read_text(encoding='utf-8'))
            evaluation = result.get('evaluation') or {}
            yield root, folder, last, result, evaluation


def last_wire(folder):
    wire = folder / 'wire' if (folder / 'wire').is_dir() else None
    if wire is None:
        return None
    summaries = sorted(wire.glob('*.summary.json'), key=lambda p: p.stat().st_mtime)
    for summary in reversed(summaries):
        try:
            data = json.loads(summary.read_text(encoding='utf-8-sig'))
            request = json.loads((summary.with_suffix('').with_suffix('').parent /
                                  summary.name.replace('.summary.json', '.request.json')).read_text(encoding='utf-8-sig'))
        except Exception:
            continue
        usage = data.get('usage') or {}
        return {'prompt': usage.get('prompt_tokens'), 'completion': usage.get('completion_tokens'),
                'allowance': request.get('max_tokens'), 'error': data.get('error')}
    return None


def main():
    print('%-26s %-14s %-7s %-8s %-7s %-9s %-9s %-8s %s' % (
        'root', 'session', 'score', 'prompt', 'compl', 'allowance', 'ctx_used%', 'thinking', 'cause'))
    rows = []
    for root, folder, last, result, evaluation in witness_rows():
        wire = last_wire(folder)
        ctx = None
        # the served context appears in the engine log or the runner constants; read it where present
        for log in (folder.parent / (folder.name.replace('trial', 'session') + '.log'), folder / 'server.log'):
            if log.exists():
                found = re.search(r'context (\d+) tokens|-c (\d+)', log.read_text(encoding='utf-8', errors='replace'))
                if found:
                    ctx = int(found.group(1) or found.group(2))
                    break
        prompt = (wire or {}).get('prompt')
        completion = (wire or {}).get('completion')
        allowance = (wire or {}).get('allowance')
        cause = '?'
        if wire:
            if completion is not None and allowance is not None and completion >= (allowance or 0) * 0.98:
                cause = 'reply-cap'
            elif ctx and prompt and prompt >= ctx * 0.95:
                cause = 'context-full'
            elif completion is not None and allowance is not None and completion < allowance * 0.5:
                cause = 'other-length'
        rows.append(cause)
        print('%-26s %-14s %-7s %-8s %-7s %-9s %-9s %-8s %s' % (
            root.name, folder.name[:14], '%s/%s' % (evaluation.get('passed'), evaluation.get('total')),
            prompt, completion, allowance,
            ('%.0f' % (100.0 * prompt / ctx)) if (ctx and prompt) else ('ctx=%s' % ctx if ctx else '-'),
            last['think'], cause))
    counts = {}
    for cause in rows:
        counts[cause] = counts.get(cause, 0) + 1
    print()
    print('witnesses: %d | %s' % (len(rows), counts))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
