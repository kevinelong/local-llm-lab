"""Isolated Bonsai CUDA compatibility, tool controls, and bounded Pi trials."""
import contextlib
import http.server
import json
from pathlib import Path
import socket
import subprocess
import sys
import threading
import time
import urllib.request

import round_20260920 as current
import overnight_20260916 as night

ROOT = current.ROOT
B = ROOT/'bonsai'
SAVE = current.SAVE

def free_port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0)); return sock.getsockname()[1]

def api(base,route,body=None):
    request = urllib.request.Request(base+route,data=None if body is None else json.dumps(body).encode(),headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(request,timeout=600) as response:
        return json.loads(response.read())

@contextlib.contextmanager
def server(ctx,label):
    night.DEADLINE = time.monotonic()+7200
    preflight = night.preflight()
    port = free_port()
    command = [str(B/'runtime/llama-server.exe'),'-m',str(B/'Ternary-Bonsai-2-27B-PQ2_0.gguf'),
               '--host','127.0.0.1','--port',str(port),'--alias','bonsai2','-ngl','99','-c',str(ctx),
               '-np','1','-b','512','-ub','128','-fa','on','--fit','off','--jinja','--no-webui',
               '--chat-template-kwargs','{"enable_thinking":false}','--reasoning-budget','0',
               '--seed','42','--temp','0','--top-k','40','--top-p','0.95','--repeat-penalty','1']
    info = dict(command=command,preflight=preflight,started=night.now(),context=ctx)
    folder = B/'runs'/label
    folder.mkdir(parents=True,exist_ok=False)
    process = None
    try:
        with (folder/'server.log').open('w',encoding='utf-8') as log:
            process = subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,
                                       creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            info['pid']=process.pid
            SAVE(folder/'server.json',info)
            base = f'http://127.0.0.1:{port}'
            deadline = time.monotonic()+180
            while time.monotonic()<deadline:
                if process.poll() is not None: raise RuntimeError(f'Server exited {process.returncode}; see {folder}/server.log')
                try:
                    with urllib.request.urlopen(base+'/health',timeout=2) as response:
                        if response.status==200: break
                except Exception: time.sleep(1)
            else: raise TimeoutError('Bonsai load exceeded 180s')
            info['gpu_loaded']=night.old.gpu()
            SAVE(folder/'properties.json',api(base,'/props'))
            current.status('bonsai-ready',context=ctx,gpu=info['gpu_loaded'])
            yield base,folder
    except Exception as exc:
        info['error']=repr(exc)
        raise
    finally:
        if process is not None and process.poll() is None:
            process.terminate()
            try: process.wait(timeout=20)
            except subprocess.TimeoutExpired:
                subprocess.run(['taskkill','/PID',str(process.pid),'/T','/F'],capture_output=True)
                process.wait(timeout=20)
        info.update(finished=night.now(),gpu_after=night.old.gpu())
        SAVE(folder/'server.json',info)

def controls(base,folder):
    common = dict(model='bonsai2',temperature=0,seed=42,chat_template_kwargs={'enable_thinking':False},max_tokens=512)
    start=time.monotonic()
    body={**common,'messages':[{'role':'user','content':'Reply with exactly LOCAL_OK and nothing else.'}],'stream':False}
    response=api(base,'/v1/chat/completions',body)
    text=response['choices'][0]['message'].get('content','').strip()
    SAVE(folder/'text.json',dict(request=body,response=response,seconds=time.monotonic()-start,gpu=night.old.gpu(),correct=text=='LOCAL_OK'))
    if text!='LOCAL_OK': raise RuntimeError('Bonsai text control failed: '+repr(text))
    tool={'type':'function','function':{'name':'record','description':'Record text','parameters':{'type':'object','properties':{'text':{'type':'string'}},'required':['text']}}}
    prompt=[{'role':'user','content':'Call record exactly once with text equal to LOCAL_OK.'}]
    body={**common,'messages':prompt,'tools':[tool],'stream':False}
    start=time.monotonic()
    response=api(base,'/v1/chat/completions',body)
    choice=response['choices'][0]
    calls=choice['message'].get('tool_calls',[])
    correct=len(calls)==1 and calls[0]['function']['name']=='record' and json.loads(calls[0]['function']['arguments'])=={'text':'LOCAL_OK'}
    SAVE(folder/'tool-json.json',dict(request=body,response=response,correct=correct,seconds=time.monotonic()-start,gpu=night.old.gpu()))
    if not correct: raise RuntimeError('Bonsai structured tool control failed')
    body.update(stream=True,stream_options={'include_usage':True})
    SAVE(folder/'tool-stream-request.json',body)
    start=time.monotonic()
    request=urllib.request.Request(base+'/v1/chat/completions',data=json.dumps(body).encode(),headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(request,timeout=180) as response: raw=response.read().decode()
    (folder/'tool-stream.sse').write_text(raw,encoding='utf-8')
    events=[json.loads(line[6:]) for line in raw.splitlines() if line.startswith('data: ') and line[6:]!='[DONE]']
    calls={}; finish=[]
    for event in events:
        for choice in event.get('choices',[]):
            if choice.get('finish_reason'): finish.append(choice['finish_reason'])
            for call in choice.get('delta',{}).get('tool_calls',[]):
                target=calls.setdefault(call.get('index',0),dict(name='',arguments=''))
                for key in target: target[key]+=call.get('function',{}).get(key,'')
    correct=bool(finish) and 'data: [DONE]' in raw and len(calls)==1 and any(c['name']=='record' and json.loads(c['arguments'])=={'text':'LOCAL_OK'} for c in calls.values())
    SAVE(folder/'tool-stream.json',dict(correct=correct,finish_reasons=finish,calls=calls,seconds=time.monotonic()-start,gpu=night.old.gpu()))
    if not correct: raise RuntimeError('Bonsai streaming tool control failed')
    body={**common,'max_tokens':256,'messages':[{'role':'user','content':'Explain how a bicycle works in about 150 words.'}],'stream':False}
    start=time.monotonic()
    response=api(base,'/v1/chat/completions',body)
    SAVE(folder/'throughput.json',dict(request=body,response=response,seconds=time.monotonic()-start,gpu=night.old.gpu()))
    current.status('bonsai-controls-passed',context=folder.name)

def run(isolated=False):
    if not isolated:
        with server(8192,'controls-8192') as (base,folder): controls(base,folder)
        with server(16384,'controls-16384') as (base,folder): controls(base,folder)
    plan=[('hard',1)] if isolated else [(task,repeat) for task in ('graph','intervals') for repeat in (1,2,3)]+[('hard',1)]
    for task,repeat in plan:
        if (ROOT/'STOP').exists(): raise InterruptedError('STOP requested')
        ctx,cap = (32768,12288) if task=='hard' else (16384,8192)
        with server(ctx,f'agent-{task}-{repeat}'+('-isolated' if isolated else '')) as (base,folder):
            old_base=night.old.BASE
            night.old.BASE=base
            relay=http.server.ThreadingHTTPServer(('127.0.0.1',0),current.Relay)
            relay.daemon_threads=True
            threading.Thread(target=relay.serve_forever,daemon=True).start()
            try:
                current.agent('0.86.1',task,repeat,relay.server_port,backend='bonsai',context=ctx,output_limit=cap,isolated=isolated)
            finally:
                relay.shutdown(); relay.server_close(); night.old.BASE=old_base
    current.status('bonsai-complete')

if __name__=='__main__':
    lock=ROOT/'RUNNING.lock'
    with lock.open('x') as f:
        import os
        f.write(str(os.getpid()))
    try: run(isolated='--isolated-hard' in sys.argv)
    finally: lock.unlink(missing_ok=True)
