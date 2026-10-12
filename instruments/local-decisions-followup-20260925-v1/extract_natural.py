"""Extract archived real-tool repeat windows; no model calls and no automatic labels."""
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).parent
BASE=ROOT.parent

def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def sha(x):return hashlib.sha256(x.encode()).hexdigest()
def text(content):
    if isinstance(content,str):return content
    return '\n'.join(c.get('text','') for c in (content or []) if c.get('type')=='text')

def main():
    paths=sorted(list((BASE/'round-20260920/runs').glob('*/events.jsonl'))+
                 list((BASE/'completion-20260923-v1/ablation/runs').glob('*/one-shot-events.jsonl')))
    candidates=[];sources=[]
    for path in paths:
        raw=path.read_bytes();events=[json.loads(line) for line in raw.decode('utf8').splitlines() if line.strip()]
        sources.append({'path':str(path),'sha256':hashlib.sha256(raw).hexdigest()})
        task='';recent=[];found=0;seen=set()
        for line,e in enumerate(events,1):
            if e.get('type')=='message_end' and e.get('message',{}).get('role')=='user':
                task=text(e['message'].get('content'))[:1200]
            if e.get('type')=='tool_execution_start':
                inp=e.get('args',{});tool=e['toolName'];key=sha(canonical({'tool':tool,'input':inp}))
                recent.append({'id':e['toolCallId'],'key':key,'tool':tool,'input':canonical(inp)[:500],'fullInput':inp,'line':line})
                recent=recent[-12:]
                matches=[r for r in recent if r['key']==key]
                if len(matches)==3 and key not in seen and all('outcome' in r for r in matches[:-1]):
                    seen.add(key);found+=1
                    if found>3:continue
                    state={'task':task,'recentCalls':[{k:v for k,v in r.items() if k in ('tool','input','outcome')} for r in recent]}
                    candidates.append({'id':'natural-'+str(len(candidates)+1),'source':str(path),'sourceLine':line,
                        'state':state,'audit':[{k:v for k,v in r.items() if k!='id'} for r in recent],
                        'repeatedTool':tool,'repeatedInput':inp,'repeatOutcomes':[r['outcome'] for r in matches[:-1]]})
            elif e.get('type')=='tool_execution_end':
                call=next((r for r in recent if r['id']==e['toolCallId']),None)
                if call is not None:
                    result=text(e.get('result',{}).get('content'))
                    call['outcome']={'isError':bool(e.get('isError')),'sha256':sha(result),'chars':len(result),
                        'excerpt':result[:350]+('\n...\n'+result[-150:] if len(result)>500 else result[350:])}
    (ROOT/'natural-candidates.json').write_text(json.dumps(candidates,indent=2),encoding='ascii')
    (ROOT/'evidence/natural-sources.json').write_text(json.dumps(sources,indent=2),encoding='ascii')
    preview=[{'id':c['id'],'run':Path(c['source']).parent.name,'tool':c['repeatedTool'],
        'input':str(c['repeatedInput'])[:180],'prior':[r['excerpt'][:180] for r in c['repeatOutcomes']],
        'sequence':[r['tool'] for r in c['audit']]} for c in candidates]
    (ROOT/'candidate-review.json').write_text(json.dumps(preview,indent=2),encoding='ascii')
    print(json.dumps({'sources':len(paths),'candidates':len(candidates)}))
if __name__=='__main__':main()
