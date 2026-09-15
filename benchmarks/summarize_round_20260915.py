"""Summarize saved local test evidence without running any model."""
import json
from pathlib import Path
import re

root = Path('C:/Users/kevin/ai_bench/round-20260915')
result = {'probes': [], 'agents': []}
for path in sorted(root.glob('probe-*.json')):
    data = json.loads(path.read_text(encoding='utf-8'))
    measurements = []
    for probe in data['probes']:
        r = probe['response']
        duration = r.get('eval_duration', 0) / 1e9
        placements = probe['placement']['models']
        measurements.append({'name': probe['name'], 'pass': probe['pass'],
                             'wall_seconds': round(probe['wall_seconds'], 2),
                             'load_seconds': round(r.get('load_duration', 0) / 1e9, 2),
                             'output_tokens': r.get('eval_count'),
                             'tokens_per_second': round(r.get('eval_count', 0) / duration, 2) if duration else None,
                             'gpu': probe['gpu'],
                             'gpu_bytes': placements[0].get('size_vram') if placements else None,
                             'total_model_bytes': placements[0].get('size') if placements else None})
    result['probes'].append({'label': path.stem, 'measurements': measurements})
for path in sorted((root / 'runs').glob('*/run.json')):
    run = json.loads(path.read_text(encoding='utf-8'))
    item = {k: run.get(k) for k in ('label','harness','model','smoke','wall_seconds','exit_code','timed_out','reasoning_effort','context')}
    evaluation = path.with_name('evaluation.txt')
    if evaluation.exists():
        text = evaluation.read_text(encoding='utf-8')
        score = re.search(r'SCORE: (\d+/\d+)', text)
        item['score'] = score.group(1) if score else None
        item['failures'] = [line.strip() for line in text.splitlines() if 'FAIL' in line]
    extra = path.with_name('evaluation-extra.json')
    if extra.exists():
        try: item['extra'] = json.loads(extra.read_text(encoding='utf-8'))
        except ValueError: item['extra_error'] = True
    events = path.with_name('events.jsonl')
    counts = {'tool_calls': 0, 'tool_errors': 0, 'compactions': 0, 'input_tokens': 0, 'output_tokens': 0}
    for line in events.read_text(encoding='utf-8').splitlines():
        try: event = json.loads(line)
        except ValueError: continue
        if not isinstance(event, dict): continue
        kind = event.get('type')
        if kind == 'tool_execution_start': counts['tool_calls'] += 1
        if kind == 'tool_execution_end' and event.get('isError'): counts['tool_errors'] += 1
        if kind in ('compaction_end', 'auto_compaction_end'): counts['compactions'] += 1
        if kind == 'message_end':
            message = event.get('message', {})
            if message.get('role') == 'assistant':
                usage = message.get('usage', {})
                counts['input_tokens'] += usage.get('input', 0)
                counts['output_tokens'] += usage.get('output', 0)
                item['last_stop_reason'] = message.get('stopReason')
                if message.get('errorMessage'): item['last_error'] = message['errorMessage']
    if item['harness'] == 'pi': item['event_counts'] = counts
    result['agents'].append(item)
(root / 'summary.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result, indent=2))
