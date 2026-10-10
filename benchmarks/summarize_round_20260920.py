"""Publish compact local evidence without running inference."""
import ast
import datetime
import hashlib
import json
from pathlib import Path
import re

ROOT=Path('C:/Users/kevin/ai_bench/round-20260920')
REPO=Path('C:/Users/kevin/local-llm-lab')
OUT=REPO/'results/2026-09-20'
OUT.mkdir(parents=True,exist_ok=True)

def read(path): return json.loads(path.read_text(encoding='utf-8-sig'))

summary={'status':read(ROOT/'status.json') if (ROOT/'status.json').exists() else {},'replay':[],'agents':[],'bonsai':[]}
if (ROOT/'evaluation/validation.json').exists(): summary['evaluation_validation']=read(ROOT/'evaluation/validation.json')

for path in sorted((ROOT/'replay').glob('stream-*.json')):
    if path.stem.endswith('-request'): continue
    r=read(path)
    item={k:r.get(k) for k in ('cap','seconds','http_status','finish_reasons','done_marker','usage','error')}
    calls={}
    for tc in r.get('tool_calls',[]):
        call=calls.setdefault(tc.get('index',0),{'name':'','arguments':''})
        for field in call:
            value=tc.get('function',{}).get(field,'')
            call[field]+=value if isinstance(value,str) else json.dumps(value)
    item['valid_tool_json']=bool(calls)
    item['tool_names']=[]
    for call in calls.values():
        item['tool_names'].append(call['name'])
        try:
            args=json.loads(call['arguments'])
            if isinstance(args,dict) and 'content' in args:
                try: ast.parse(args['content']); item['python_syntax_valid']=True
                except SyntaxError: item['python_syntax_valid']=False
        except ValueError: item['valid_tool_json']=False
    summary['replay'].append(item)

if (ROOT/'replay/model.json').exists():
    now=read(ROOT/'replay/model.json')
    then=read(ROOT.parent/'overnight-20260916/model-omni-16384.json')
    def params(value): return dict(line.split(None,1) for line in value.strip().splitlines())
    def blob(value): return re.search(r'^FROM (.+)$',value,re.M)[1]
    summary['replay_identity']={'same_weight_blob':blob(now['modelfile'])==blob(then['modelfile']),
                               'same_parameters':params(now['parameters'])==params(then['parameters']),
                               'same_template':now['template']==then['template'],'current_version':read(ROOT/'replay/inventory.json')['ollama']}

for path in sorted((ROOT/'runs').glob('*/result.json')):
    r=read(path)
    item={k:r.get(k) for k in ('label','version','task','repeat','backend','context','output_limit','seconds','clean_finish','score','total','success','stop_reason','tool_calls','tool_errors','error','gpu')}
    item['isolated_workspace']=r.get('isolated_workspace',False)
    item['timed_out']=r.get('timed_out',False)
    recovered=path.parent/'evaluation-v2-recovered.json'
    if recovered.exists():
        assessed=read(recovered)
        item.update(score=assessed['passed'],total=assessed['total'],clean_finish=False,success=False,
                    recovered_assessment=True)
        recovery=read(path.parent/'recovery.json')
        item.update(tool_calls=recovery['tool_calls'],tool_errors=recovery['tool_errors'])
    wire=[read(p) for p in (path.parent/'wire').glob('*-summary.json')]
    item['captured_requests']=len(wire)
    item['terminal_signals']=sum(bool(w.get('finish_reasons')) for w in wire)
    requests=[read(p) for p in (path.parent/'wire').glob('*-request.json')]
    item['response_caps']=sorted({str(p.get('max_tokens',p.get('max_completion_tokens'))) for p in requests})
    item['reasoning_efforts']=sorted({str(p.get('reasoning_effort')) for p in requests})
    item['strict_schema_values']=sorted({str(t.get('function',{}).get('strict')) for p in requests for t in p.get('tools',[])})
    item['usage']={key:sum(u.get(key,0) for u in r.get('usage',[])) for key in ('input','output','totalTokens')}
    hist=path.parent/'evaluation-historical.txt'
    if hist.exists():
        m=re.search(r'SCORE: (\d+)/10',hist.read_text())
        item['historical_score']=int(m[1]) if m else None
    summary['agents'].append(item)

for path in sorted((ROOT/'bonsai/runs').glob('*/server.json')):
    r=read(path)
    item={'label':path.parent.name,**{k:r.get(k) for k in ('context','gpu_loaded','gpu_after','error')}}
    if r.get('started') and r.get('finished'):
        item['server_lifetime_seconds']=(datetime.datetime.fromisoformat(r['finished'])-datetime.datetime.fromisoformat(r['started'])).total_seconds()
    for filename in ('text.json','tool-json.json','tool-stream.json','throughput.json'):
        p=path.parent/filename
        if p.exists():
            result=read(p)
            item[filename]={k:result.get(k) for k in ('correct','seconds','gpu')}
            if result.get('response',{}).get('timings'): item[filename]['timings']=result['response']['timings']
    summary['bonsai'].append(item)
if (ROOT/'bonsai/verified.json').exists(): summary['bonsai_identity']=read(ROOT/'bonsai/verified.json')
(OUT/'summary.json').write_text(json.dumps(summary,indent=2),encoding='ascii')

lines=['# Local lab experiments: September 20, 2026','',
       'Status: '+summary['status'].get('phase','not started')+'. See the dated source review in [REVIEW-2026-09-20.md](REVIEW-2026-09-20.md).',
       '', 'This round validates evaluator v2, replays a saved failure on Ollama 0.34.2, compares pinned Pi versions, and tests Bonsai 2. Original results and installations are retained. No cloud inference or global server settings are used.',
       '', 'Compact evidence: [summary.json](results/2026-09-20/summary.json). Raw requests, transcripts, models, and programs remain in `C:/Users/kevin/ai_bench/round-20260920`.',
       '', '## Findings','',
       'The current Ollama replay still fails at 4k output and succeeds at 8k/12k. Updating the backend did not remove that output-budget failure. Keep output allowance distinct from input context.',
       '', '| Deployment | Graph runs fully passed | Interval runs fully passed | Full-task v2 |',
       '|---|---:|---:|---:|']
for backend,version in [('ollama','0.85.1'),('ollama','0.86.1'),('bonsai','0.86.1')]:
    runs=[r for r in summary['agents'] if r['backend']==backend and r['version']==version and not r['isolated_workspace']]
    cells=[]
    for task in ('graph','intervals'):
        group=[r for r in runs if r['task']==task]
        cells.append(f"{sum(bool(r.get('success')) for r in group)}/{len(group)}")
    hard=[r for r in runs if r['task']=='hard']
    cells.append(f"{hard[0]['score']}/{hard[0]['total']}" if hard else 'pending')
    lines.append('| '+('Omni / Ollama' if backend=='ollama' else 'Bonsai / Prism')+' / Pi '+version+' | '+' | '.join(cells)+' |')
for r in summary['agents']:
    if r['isolated_workspace']:
        lines += ['', f"Separate workspace-isolation diagnostic: {r['label']} scored {r['score']}/{r['total']}, clean stop = {r['clean_finish']}, agent seconds = {r['seconds']:.1f}. Model, runtime, prompt, context, output allowance, and scorer were held fixed; candidate workspace contents changed. One follow-up cannot establish causality or stability."]
lines += ['', 'These are three repetitions of each of two small tasks and one full-task run per deployment, not a broad capability ranking. The new-Pi Omni full-task artifact fails status-filter syntax, never-reused IDs, and both self-test isolation groups. Its clean completion does not make it safe for real task data.',
       '', 'The original runs placed transcripts/configuration beside the candidate files. Bonsai read those logs and repeated directory listings during its full-task run. This is a harness confound: the primary table is a result for that environment. An isolated follow-up keeps capture files outside the candidate working directory and is listed separately below; the layout is not a security boundary.',
       '', 'Evaluator v2 changes the historical picture: the archived Aider implementation scores 14/21 and Claude scores 19/21, while the other three archived programs pass 21/21. Passing still means passing this finite suite, not proof of all-spec correctness.',
       '', 'Bonsai fits and works with its pinned Prism runtime on this RTX 5070, including 32k context. Its original full-task trial produced no file and timed out. The isolated follow-up produced a 16/21 artifact but also timed out; it fails ID reuse, two error-exit-code groups, and both self-test groups because its self-test crashes. The unchanged historical scorer gives that artifact 9/10. Neither full-task configuration establishes reliable unattended implementation.',
       '', 'Next use: retain Bonsai as a candidate for bounded repairs, keep external validation, and use isolated candidate workspaces for every model. The next meaningful comparison is staged implementation across at least five distinct tasks with repeated runs, using matched workspace layout and budgets. Do not promote Pi 0.86.1 or Bonsai to a universal winner from this small sample. PTQ packing, CPU alternatives, and broader task diversity remain future experiments.',
       '', '## Evaluator v2','',
       'The [21-group evaluator](benchmarks/eval_tasks_v2.py) checks persisted behavior and rejection diagnostics. Its [contract and limits](benchmarks/EVALUATOR-V2.md) explain output parsing and coverage. These scores are separate from historical ten-check scores.',
       '', '| Archived program | V2 groups passed |', '|---|---:|']
for name,v in summary.get('evaluation_validation',{}).items():
    if name.startswith('tasks.'): lines.append(f"| {name} | {v['passed']}/{v['total']} |")
lines += ['', 'Validation includes an archived passing control and six faulty controls: unconditional crash/success, self-test data overwrite, swallowed cycle exit, no-op import, and ID reuse. See `evaluation/validation.json` in raw evidence.',
          '', '## Captured request replay','', '| Output allowance | Seconds | Terminal signal | Valid tool arguments |','|---|---:|---|---|']
for r in summary['replay']: lines.append(f"| {r['cap']} | {r['seconds']:.2f} | {bool(r['finish_reasons']) and r['done_marker']} | {r['valid_tool_json']} |")
lines += ['', 'This is a comparison to saved 0.34.0 traces, not a simultaneous backend A/B. Weight blob, normalized parameters, and template identity are checked in the summary. A valid replay response does not establish program correctness.',
          '', '## Agent trials','', '| Run | Checks | Clean stop | Seconds | Tool errors |','|---|---:|---|---:|---:|']
for r in summary['agents']:
    sec=f"{r['seconds']:.1f}" if r.get('seconds') is not None else '?'
    lines.append(f"| {r['label']} | {r.get('score')}/{r.get('total')} | {r.get('clean_finish')} | {sec} | {r.get('tool_errors')} |")
lines += ['', 'The Pi comparison holds OmniCoder Q4_K_M, Ollama, 32k context, 12k output allowance/reserve, sampling settings, and prompts fixed. Small trials use three fresh workspaces per task/version in a shuffled order; hard trials are single runs capped at 600 seconds. Cache warming and retries are off. Agent prompt/tool differences across versions are part of the version treatment.',
          '', 'The old-Pi hard run reached its deadline, but Windows process-tree cleanup stalled and automatic scoring was interrupted. Its saved artifact was assessed after cleanup without repair (evaluation-v2-recovered.json); original result.json remains intact. All 41 captured responses had terminal signals. The harness now bounds taskkill itself. The new-Pi hard trial started only after the old process and model had stopped. This cleanup interruption limits timing comparisons.',
          '', 'Bonsai uses its required fork: small trials use 16k context/8k output; the hard trial attempts 32k context/12k output, matching the Omni allowance if it loads. This is a deployment comparison, not an isolated model comparison. Each trial starts a fresh server, and stopping that owned server unloads its model. Small trials have 180-second limits.',
          '', 'Agent seconds include the Pi process but exclude external scoring. Bonsai server startup happens before that timer; Omni loads through the first timed request. Do not compare these agent times as equal cold-start latency. Bonsai server lifetimes, including loading, agent/scoring work, and shutdown, are recorded separately in the summary.',
          '', 'Graph/interval checks are deterministic cases within two tasks, not independent task samples. A clean stop alone is insufficient for success. Full success requires every external check. First-artifact files are early snapshots and are not guaranteed to represent the first completed solution.',
          '', '## Bonsai compatibility','', '| Server/trial | Context | GPU MiB sample loaded | Error |','|---|---:|---|---|']
for r in summary['bonsai']:
    used=(r.get('gpu_loaded') or '').split(',')[0]
    lines.append(f"| {r['label']} | {r['context']} | {used} | {r.get('error') or ''} |")
for r in summary['bonsai']:
    if not r['label'].startswith('controls-'): continue
    passed=[r.get(k,{}).get('correct') for k in ('text.json','tool-json.json','tool-stream.json')]
    timings=r.get('throughput.json',{}).get('timings',{})
    speed=timings.get('predicted_per_second')
    lines += ['', f"{r['label']}: text / JSON tool / streamed tool controls = {passed}. Short-text decode tokens/sec = {speed}. This probe is not a coding-throughput benchmark."]
lines += ['', 'Pinned model revision and SHA256, runtime tag/commit, and verified weight bytes are in the summary. Total GPU samples include desktop applications; they are not continuous peaks. Text and native/streamed tool-call control records are saved before agent trials.',
          '', '## Reproduction','',
          '1. `python benchmarks/validate_tasks_v2.py`',
          '2. `python benchmarks/round_20260920.py replay`',
          '3. `python benchmarks/round_20260920.py agents`',
          '4. `powershell.exe -NoProfile -File benchmarks/setup_bonsai_20260920.ps1`',
          '5. `python benchmarks/bonsai_20260920.py`',
          '6. `python benchmarks/bonsai_20260920.py --isolated-hard` (separate diagnostic)',
          '7. `python benchmarks/summarize_round_20260920.py`','',
          'These scripts use this machine\'s fixed lab paths. Completed replay/agent labels are preserved. Bonsai server labels refuse overwrites. `RUNNING.lock` prevents overlapping new coordinators; `STOP` requests cancellation at the next check. Inspect existing workloads before launching.', '']
(REPO/'RESULTS-2026-09-20.md').write_text('\n'.join(lines),encoding='ascii')
print(json.dumps({'replay':len(summary['replay']),'agents':len(summary['agents']),'bonsai':len(summary['bonsai']),'status':summary['status']}))
