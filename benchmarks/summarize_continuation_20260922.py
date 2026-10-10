"""Summarize saved continuation evidence without running inference."""
import json
from pathlib import Path
import statistics

LAB = Path(__file__).resolve().parents[1]
GO = LAB / 'goproverbs'
BASE = GO / 'results/direct-20260922'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def main():
    summary = {'go': {}, 'budget_probes': {}, 'llm': {},
               'limitations': ['No Elo estimate or default promotion.',
                'Smoke and incomplete comparisons are excluded from confirmation claims.',
                'Budget probes are development-position throughput diagnostics, not strength tests.',
                'Staging includes separate contexts/processes and plan transfer, not wording alone.']}
    lines = ['# September 22 continuation evidence', '',
             'Generated from saved records; running and completed studies are distinguished.', '']
    for name in ('smoke-v2', 'expansion-v2', 'cpu-small-v2'):
        path = BASE / name / 'manifest.json'
        if not path.exists():
            continue
        record = read(path)
        games = record.get('games', [])
        roles = {}
        for game in games:
            for role, data in game['roles'].items():
                result = roles.setdefault(role, {'decisions': 0, 'fallbacks': 0, 'complete_neural_rounds': 0, 'max_ms': 0})
                result['decisions'] += data['decisions']
                result['fallbacks'] += data['fallbacks']
                result['complete_neural_rounds'] += data.get('external_complete_rounds', 0)
                result['max_ms'] = max(result['max_ms'], data['max_ms'] or 0)
        matchups = {}
        for game in games:
            data = matchups.setdefault(game['matchup'], {'finished': 0, 'a_wins': 0, 'draws': 0, 'unfinished': 0,
                                                       'a_wins_as_black': 0, 'a_wins_as_white': 0})
            data['finished'] += game['finished']
            data['a_wins'] += game['a_won']
            data['draws'] += game['finished'] and game['result'] == '0'
            data['unfinished'] += not game['finished']
            data['a_wins_as_black'] += game['a_won'] and game['a_color'] == 'B'
            data['a_wins_as_white'] += game['a_won'] and game['a_color'] == 'W'
        summary['go'][name] = dict(status=record['status'], matchups=matchups, roles=roles,
            hashes_unchanged=record.get('hashes_unchanged'), paired=record.get('paired'),
            broker=record.get('broker'), error=record.get('error'))
        lines += [f'## Go {name}: {record["status"]}', '',
                  '| Matchup | NH wins | As Black / White | Finished | Unfinished |', '|---|---:|---:|---:|---:|']
        for matchup, row in matchups.items():
            lines.append(f'| {matchup} | {row["a_wins"]} | {row["a_wins_as_black"]} / {row["a_wins_as_white"]} | {row["finished"]} | {row["unfinished"]} |')
        lines += ['', 'Smoke is diagnostic only. The first smoke-v1 search results are invalid and excluded.', '']
        if 'NN' in roles:
            nn = roles['NN']
            lines += [f'NN complete-round retention: {nn["complete_neural_rounds"]}/{nn["decisions"]} '
                      f'({100*nn["complete_neural_rounds"]/nn["decisions"]:.1f}%). Prespecified expansion gate: 80%.', '']
            buckets = {'retained': [], 'fallback': []}
            for trace_path in (BASE / name).glob('*NH-vs-NN-*.jsonl'):
                for line in trace_path.read_text(encoding='ascii').splitlines():
                    row = json.loads(line)
                    if row['role'] != 'NN':
                        continue
                    report = row['trace']['report']
                    key = 'retained' if 'external_leaf=true' in report else 'fallback'
                    buckets[key].append({'nominees': sum('neural_hint=' in s for s in report.splitlines()), 'turn': row['turn']})
            summary['go'][name]['nn_nominee_diagnostic'] = {key: {
                'moves': len(rows), 'median_nominees': statistics.median(r['nominees'] for r in rows),
                'median_turn': statistics.median(r['turn'] for r in rows)} for key, rows in buckets.items() if rows}
    for budget in (50, 100, 200, 400):
        path = BASE / f'budget-{budget}-v2' / 'manifest.json'
        if not path.exists():
            continue
        record = read(path)
        rows = record.get('records', [])
        by_mode = {}
        for mode in ('NH', 'NN'):
            selected = [row['trace'] for row in rows if row['mode'] == mode]
            if selected:
                by_mode[mode] = {'decisions': len(selected), 'median_ms': statistics.median(r['ms'] for r in selected),
                    'max_ms': max(r['ms'] for r in selected), 'root_timeouts': sum(r.get('root_timeout', False) for r in selected),
                    'complete_neural_rounds': sum('external_leaf=true' in r['report'] for r in selected)}
        summary['budget_probes'][budget] = dict(status=record['status'], modes=by_mode)
    if summary['budget_probes']:
        lines += ['## Fixed-model budget probes', '',
                  '| Budget ms | Mode | Decisions | Median ms | Neural complete | Root timeouts |',
                  '|---:|---|---:|---:|---:|---:|']
        for budget, record in summary['budget_probes'].items():
            for mode, row in record['modes'].items():
                lines.append(f'| {budget} | {mode} | {row["decisions"]} | {row["median_ms"]:.1f} | {row["complete_neural_rounds"]} | {row["root_timeouts"]} |')
        lines += ['', 'Same eight development histories, b10/OpenCL model and profile. These measure throughput, not playing strength.', '']
    llm = Path.home() / 'ai_bench/staging-20260922'
    for run_directory in sorted(llm.iterdir()):
        label = run_directory.name
        if not label.startswith(('smoke-', 'main-')):
            continue
        path = run_directory / 'results.json'
        if not path.exists():
            continue
        rows = read(path)
        groups = {}
        for row in rows:
            key = row['task'] + '/' + row['treatment']
            groups.setdefault(key, []).append(row)
        summary['llm'][label] = {'runs': len(rows), 'groups': {key: {
            'runs': len(group), 'successes': sum(bool(r.get('success')) for r in group),
            'correct': sum(bool(r.get('correct')) for r in group),
            'timeouts': sum(bool(r.get('timed_out')) for r in group),
            'incomplete_token_counts': sum(not r.get('completion_tokens_complete', True) for r in group),
            'median_seconds': statistics.median(r['seconds'] for r in group if 'seconds' in r) if any('seconds' in r for r in group) else None,
        } for key, group in groups.items()}}
        summary['llm'][label]['pretrial_failures'] = sum(not r.get('phases') for r in rows)
        lines += [f'## LLM {label}: {len(rows)} recorded runs', '',
                  '| Task/treatment | Success | Correct | Runs | Timeouts |', '|---|---:|---:|---:|---:|']
        for key, data in summary['llm'][label]['groups'].items():
            lines.append(f'| {key} | {data["successes"]} | {data["correct"]} | {data["runs"]} | {data["timeouts"]} |')
        lines += ['', f'Pretrial failures (no agent phase): {summary["llm"][label]["pretrial_failures"]}.',
                  'Success requires correctness and clean completion within both budgets. Smoke is excluded from main results.', '']
    lines += ['## Limits', ''] + ['- ' + text for text in summary['limitations']]
    if not summary['llm']:
        lines += ['', 'LLM execution has not begun. Smoke-v1 stopped at a WMI permission preflight;'
                  ' smoke-v2 passed all runner/scorer checks but stopped below the 4 GiB RAM gate.'
                  ' Failed preparations are preserved separately from actual model trials.']
    if summary['llm'] and not any(label.startswith('main-') for label in summary['llm']):
        lines += ['', 'No main staging comparison has run. The clean-completion smoke gate remains unmet;'
                  ' see the [staging diagnosis](STAGING-RESULTS-2026-09-22.md).']
    lines += ['', 'The separate [Bonsai packing report](PACKING-RESULTS-2026-09-22.md) records corrected API controls, GPU measurements, and CPU control outcomes.']
    (BASE / 'continuation-summary.json').write_text(json.dumps(summary, indent=2), encoding='ascii')
    (LAB / 'CONTINUATION-RESULTS-2026-09-22.md').write_text('\n'.join(lines) + '\n', encoding='ascii')
    print(json.dumps({'go': {k: v['status'] for k, v in summary['go'].items()},
                      'budgets': list(summary['budget_probes']), 'llm': {k: v['runs'] for k, v in summary['llm'].items()}}))


if __name__ == '__main__':
    main()
