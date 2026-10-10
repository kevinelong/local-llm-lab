"""Replay the captured failed request directly, without Pi or the relay."""
import copy
import json
from pathlib import Path
import sys
import time
import urllib.error
import urllib.request
import overnight_20260916 as night

ROOT=night.old.HOME/'ai_bench/stream-diagnosis-20260916'
SOURCE=night.ROOT/'runs/pi-omni-hard-16384-1/wire/67b06584b98647ab9bf9548cc5b7b5b7-request.json'

def run(mode,cap):
    night.DEADLINE=time.monotonic()+1800
    path=ROOT/f'{mode}-{cap}.json'
    if path.exists(): raise RuntimeError('Refusing to overwrite '+str(path))
    original=json.loads(SOURCE.read_text()); body=copy.deepcopy(original)
    body['max_tokens']=cap; body['stream']=mode=='stream'
    route='/v1/chat/completions'
    if mode=='json': body.pop('stream_options',None)
    if mode.startswith('native'):
        route='/api/chat'
        for message in body['messages']:
            if isinstance(message.get('content'),list):
                message['content']=''.join(part.get('text','') for part in message['content'] if part.get('type')=='text')
            if message.get('content') is None: message['content']=''
            if message['role']=='tool': message['tool_name']='read'
            for call in message.get('tool_calls',[]):
                args=call['function']['arguments']
                if isinstance(args,str): call['function']['arguments']=json.loads(args)
        body={k:body[k] for k in ('model','messages','tools')}
        body.update(stream=False,think=False,options={'num_predict':cap,'temperature':0,'presence_penalty':0})
    result={'mode':mode,'cap':cap,'preflight':night.preflight(),'source':str(SOURCE)}
    night.SAVE(ROOT/f'{mode}-{cap}-request.json',body)
    start=time.monotonic()
    try:
        req=urllib.request.Request(night.old.BASE+route,data=json.dumps(body).encode(),headers={'Content-Type':'application/json'})
        try:
            with urllib.request.urlopen(req,timeout=240) as response:
                result['http_status']=response.status; raw=response.read().decode()
        except urllib.error.HTTPError as exc:
            result['http_status']=exc.code; raw=exc.read().decode()
        (ROOT/f'{mode}-{cap}.raw').write_text(raw,encoding='utf-8')
        if mode=='stream':
            events=[json.loads(line[6:]) for line in raw.splitlines() if line.startswith('data: ') and line[6:]!='[DONE]']
            result['finish_reasons']=[c['finish_reason'] for e in events for c in e.get('choices',[]) if c.get('finish_reason')]
            result['done_marker']='data: [DONE]' in raw
            result['tool_calls']=[tc for e in events for c in e.get('choices',[]) for tc in c.get('delta',{}).get('tool_calls',[])]
            result['errors']=[e for e in events if 'error' in e]
            result['usage']=[e.get('usage') for e in events if e.get('usage')]
        else:
            parsed=json.loads(raw); result['response']=parsed
            if mode.startswith('native'):
                result['finish_reasons']=[parsed.get('done_reason')]; result['tool_calls']=parsed.get('message',{}).get('tool_calls',[])
            else:
                result['finish_reasons']=[c.get('finish_reason') for c in parsed.get('choices',[])]
                result['tool_calls']=[tc for c in parsed.get('choices',[]) for tc in c.get('message',{}).get('tool_calls',[])]
        result['placement']=night.api('/api/ps')
    except Exception as exc: result['error']=repr(exc)
    finally:
        result['seconds']=time.monotonic()-start; result['cleanup']=night.cleanup(); night.SAVE(path,result)
        print(json.dumps({k:v for k,v in result.items() if k not in ('response','tool_calls','placement','preflight','cleanup')}),flush=True)
        print('TOOL_CALLS',len(result.get('tool_calls',[])),flush=True)

def mitigate(cap=4096):
    import threading
    import http.server
    night.ROOT=ROOT/'agent-tests'
    night.REPORT=night.ROOT/'progress.md'
    night.DEADLINE=time.monotonic()+1200
    night.status('chunked-write-mitigation')
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),night.Relay)
    server.daemon_threads=True; night.PROXY_PORT=server.server_port
    threading.Thread(target=server.serve_forever,daemon=True).start()
    try:
        night.agent('omni','hard',32768 if cap>8192 else 16384,{4096:1,8192:2,12288:3}[cap],
                    f'The response limit is {cap} tokens. Keep every write/edit/shell tool call under 1500 tokens. '
                    'Create a short initial file, then build it through small edits or PowerShell Add-Content. '
                    'Never send the entire implementation in one tool call. Keep final explanations brief.',output_limit=cap)
        night.status('complete')
    finally:
        night.SAVE(night.ROOT/'final-cleanup.json',night.cleanup())
        server.shutdown(); server.server_close(); night.report()

if __name__=='__main__':
    ROOT.mkdir(parents=True,exist_ok=True)
    if sys.argv[1:2]==['mitigate']: mitigate(int(sys.argv[2]) if len(sys.argv)>2 else 4096)
    elif len(sys.argv)>1: run(sys.argv[1],int(sys.argv[2]))
    else:
        for mode,cap in [('stream',4096),('json',4096),('native',4096),('stream',8192)]: run(mode,cap)
