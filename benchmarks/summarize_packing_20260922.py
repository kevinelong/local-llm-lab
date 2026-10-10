"""Summarize saved packing measurements without inference or executing outputs."""
import ast
import json
from pathlib import Path
import re
import statistics

LAB = Path(__file__).resolve().parents[1]
BASE = Path.home() / 'ai_bench/packing-20260922'


def gpu_used(state):
    if state.get('gpu', {}).get('exit_code') != 0 or not state['gpu'].get('stdout'):
        return None
    return int(state['gpu']['stdout'].strip().splitlines()[-1].split(',')[1].strip().split()[0])


def main():
    runs = [BASE / label for label in ('main-v2', 'cpu-ptq1-v2', 'cpu-pq2-v2') if (BASE / label / 'protocol.json').exists()]
    protocols = {run.name: json.loads((run / 'protocol.json').read_text()) for run in runs}
    rows = []
    texts = []
    for path in sorted(path for run in runs for path in run.glob('*/result.json')):
        record = json.loads(path.read_text())
        reps = record.get('repetitions', [])
        row = {key: record.get(key) for key in ('packing', 'context', 'ngl', 'status', 'load_ms', 'owned_server_exited', 'error')}
        row['case'] = path.parent.name
        row['run'] = path.parent.parent.name
        row['repetitions'] = len(reps)
        if reps:
            row['median_generation_tps'] = statistics.median(r['response']['timings']['predicted_per_second'] for r in reps)
            row['median_prompt_tps'] = statistics.median(r['response']['timings']['prompt_per_second'] for r in reps)
            row['median_response_ms'] = statistics.median(r['ms'] for r in reps)
            gpu_samples = [gpu_used(r['state']) for r in reps]
            row['missing_gpu_samples'] = sum(value is None for value in gpu_samples)
            valid_gpu = [value for value in gpu_samples if value is not None]
            row['median_gpu_used_mib'] = statistics.median(valid_gpu) if valid_gpu else None
            row['baseline_gpu_used_mib'] = gpu_used(record['before'])
            row['observed_gpu_delta_mib'] = (row['median_gpu_used_mib'] - row['baseline_gpu_used_mib']
                if row['median_gpu_used_mib'] is not None and row['baseline_gpu_used_mib'] is not None else None)
            row['finish_reasons'] = [r['response']['choices'][0]['finish_reason'] for r in reps]
            row['completion_tokens'] = [r['response']['usage']['completion_tokens'] for r in reps]
            row['cached_prompt_tokens'] = [r['response']['timings']['cache_n'] for r in reps]
            syntax_valid = []
            for rep in reps:
                content = rep['response']['choices'][0]['message']['content']
                texts.append(content)
                match = re.fullmatch(r'\s*```python\s*\n(.*?)\n```\s*', content, re.S)
                try:
                    tree = ast.parse(match.group(1) if match else content)
                    syntax_valid.append(any(isinstance(node, ast.FunctionDef) and node.name == 'merge_counts' for node in tree.body))
                except SyntaxError:
                    syntax_valid.append(False)
            row['named_function_parses'] = syntax_valid
        rows.append(row)
    summary = {'runs': {label: {key: protocol.get(key) for key in ('status', 'inputs_unchanged', 'model_unloaded_check', 'error')}
                       for label, protocol in protocols.items()}, 'cases': rows,
               'identical_observed_texts': bool(texts) and len(set(texts)) == 1}
    lines = ['# Bonsai packing results, September 22', '',
             f"Evidence: `{BASE.as_posix()}`. Run status: " + ', '.join(f"{label}={r['status']}" for label, r in summary['runs'].items()) + '.', '',
             '| Packing | Context | Device | Reps | Median generation tok/s | Median request ms | GPU delta MiB |',
             '|---|---:|---|---:|---:|---:|---:|']
    incomplete = []
    for row in rows:
        if 'median_generation_tps' in row:
            delta = f"{row['observed_gpu_delta_mib']:.0f}" if row['observed_gpu_delta_mib'] is not None else 'unavailable'
            lines.append(f"| {row['packing']} | {row['context']} | {'GPU' if row['ngl'] else 'CPU'} | {row['repetitions']} | {row['median_generation_tps']:.2f} | {row['median_response_ms']:.1f} | {delta} |")
        else:
            incomplete.append(f"Incomplete case {row['case']}: {row.get('error')}.")
    lines += [''] + incomplete
    if incomplete:
        lines += ['', 'Both corrected CPU controls passed plain text but timed out on the required-tool request at the 120-second bound, before any fixed-prompt repetitions. This does not measure their unconstrained CPU throughput.']
    lines += ['', 'GPU delta is whole-device usage relative to the pre-load snapshot, not a process-isolated allocation.',
              f"Missing GPU telemetry samples: {sum(row.get('missing_gpu_samples', 0) for row in rows)}. Memory medians use only successful queries; raw failures remain recorded.",
              'Three repetitions use one fixed short prompt with cache_prompt=false, seed 260922, temperature zero, and no thinking.',
              'The context column is allocated capacity; this does not measure long-prompt processing or long-context quality.',
              'CPU runs use 16 threads and disable GPU, KV, and operation offload. Report them separately from GPU.',
              'Controls cover exact plain text, forced tool JSON, and streamed tool-call reconstruction.',
              f"All observed generated texts identical: {summary['identical_observed_texts']}. This finite observation does not prove mathematical equivalence or general coding quality.",
              'Source/model/runtime hashes, load times, placement logs and raw responses are retained. File hashing warmed the filesystem cache.',
              'Run order was fixed; system memory pressure and application activity limit speed comparisons. No stock-versus-Prism runtime conclusion follows.', '',
              'The preserved main-v1 run used an unsupported object-form tool_choice that the server downgraded to auto. Its observations are excluded from this table.',
              'Main-v2 and both cpu-*-v2 runs use the supported required string with one available tool. Each measured case must pass these corrected controls first.',
              'CPU-only PTQ1 in main-v1 passed plain text at about 0.61 generated tokens/s, then its tool-control request timed out at 120 seconds. No fixed-prompt repetitions were reached; this is not a matched throughput result.', '']
    cleanup = BASE / 'final-cleanup-v2.json'
    if cleanup.exists():
        final = json.loads(cleanup.read_text())
        lines += ['Final cleanup: no active model processes or run locks; Ollama has no resident model.',
                  f"Available RAM: {final['ram_bytes']['available']/2**30:.2f} GiB. GPU and source verification are recorded in final-cleanup-v2.json.", '']
    (LAB / 'PACKING-RESULTS-2026-09-22.md').write_text('\n'.join(lines), encoding='ascii')
    (BASE / 'packing-summary-v2.json').write_text(json.dumps(summary, indent=2), encoding='ascii')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
