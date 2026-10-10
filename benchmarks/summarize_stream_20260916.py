"""Export compact diagnosis evidence, excluding prompts and generated source."""
import json
from pathlib import Path

home=Path('C:/Users/kevin')
root=home/'ai_bench/stream-diagnosis-20260916'
result={'replays':[],'agent_trials':[]}
for path in sorted(root.glob('*.json')):
    if path.name.endswith('-request.json'): continue
    data=json.loads(path.read_text())
    if 'mode' not in data: continue
    row={k:data.get(k) for k in ('mode','cap','http_status','finish_reasons','done_marker','seconds','usage','error')}
    row['tool_call_count']=len(data.get('tool_calls',[]))
    row['server_error']=data.get('response',{}).get('error')
    row['invalid_control']=data['mode']=='native' and data.get('http_status')==400
    result['replays'].append(row)
for path in sorted((root/'agent-tests/runs').glob('*/result.json')):
    data=json.loads(path.read_text())
    row={k:data.get(k) for k in ('label','context','output_limit','seconds','timed_out','score','total','clean_finish','success','agent_errors','error')}
    if row['output_limit'] is None:
        config=json.loads((path.parent/'config/models.json').read_text())
        row['output_limit']=config['providers']['lab']['models'][0]['maxTokens']
    row['extra_passed']=data.get('extra',{}).get('passed')
    wire=data.get('wire',[])
    row['captured_streams']=len(wire)
    row['streams_with_terminal_signal']=sum(bool(w.get('finish_reasons')) for w in wire)
    row['streams_without_terminal_signal']=[w for w in wire if not w.get('finish_reasons')]
    row['placement']=data.get('placement')
    row['cleanup']=data.get('cleanup')
    result['agent_trials'].append(row)
target=home/'local-llm-lab/results/2026-09-16/stream-diagnosis.json'
target.parent.mkdir(parents=True,exist_ok=True)
target.write_text(json.dumps(result,indent=2),encoding='ascii')
print(target)
