"""Local-only, resumable overnight experiment coordinator. Run: python ... run.

Five-hour ceiling, one inference workload, per-agent deadlines, incremental report.
STOP file requests graceful cancellation; no cloud inference or global config changes.
"""
import datetime
import http.server
import json
import os
from pathlib import Path
import random
import shutil
import statistics
import subprocess
import sys
import threading
import time
import urllib.request
import uuid

import round_20260915 as old
from night_tasks_20260916 import TASKS

ROOT=old.HOME/'ai_bench/overnight-20260916'
REPO=old.HOME/'local-llm-lab'
REPORT=REPO/'RESULTS-2026-09-16-OVERNIGHT.md'
SAVE=old.save
LIMIT=5*3600
ACTIVE=None
DEADLINE=0
CAPTURE=None
SERVER=None
PROXY_PORT=0

def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def status(phase, **extra):
    SAVE(ROOT/'status.json',dict(phase=phase,updated_utc=now(),pid=os.getpid(),**extra))
    print(now(),phase,json.dumps(extra),flush=True)
def check_time():
    if (ROOT/'STOP').exists() or time.monotonic()>DEADLINE: raise InterruptedError('Stop requested or five-hour ceiling reached')
def alias(key,ctx): return f'night-20260916-{key}-{ctx}'
def api(route,body=None,timeout=120): return old.api(route,body,timeout)
def cleanup():
    # Only unload this experiment's aliases. Never interrupt a newly arrived user model.
    before=old.gpu()
    names=[m['name'] for m in api('/api/ps')['models'] if m['name'].startswith('night-20260916-')]
    for name in names: api('/api/generate',{'model':name,'keep_alive':0})
    for _ in range(30):
        if not any(m['name'].startswith('night-20260916-') for m in api('/api/ps')['models']): break
        time.sleep(1)
    return dict(before=before,unloaded=names,after=old.gpu(),remaining=api('/api/ps'))
def preflight():
    check_time()
    loaded=api('/api/ps')['models']
    if any(not m['name'].startswith('night-20260916-') for m in loaded):
        raise InterruptedError('Another model is resident; preserving user workload')
    state=cleanup()
    if state['remaining']['models']: raise RuntimeError('Model failed to unload')
    fields=old.gpu().split(',')
    if len(fields)<2 or int(fields[1])<7500: raise InterruptedError('Insufficient free VRAM; preserving other applications')
    # Windows available physical RAM, no additional package needed.
    import ctypes
    class Memory(ctypes.Structure):
        _fields_=[('length',ctypes.c_ulong),('load',ctypes.c_ulong)]+[(n,ctypes.c_ulonglong) for n in ('total','available','page_total','page_available','virtual_total','virtual_available','extended')]
    mem=Memory(); mem.length=ctypes.sizeof(mem)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(mem))
    state['available_ram_bytes']=mem.available
    if mem.available<4*1024**3: raise InterruptedError('Less than 4 GiB RAM available')
    return state

class Relay(http.server.BaseHTTPRequestHandler):
    def log_message(self,*args): pass
    def do_POST(self):
        capture=CAPTURE
        if capture is None or self.path!='/v1/chat/completions': self.send_error(404); return
        ident=uuid.uuid4().hex
        body=self.rfile.read(int(self.headers.get('Content-Length','0')))
        folder=capture/'wire'; folder.mkdir(exist_ok=True)
        (folder/(ident+'-request.json')).write_bytes(body)
        info={'id':ident,'start':now(),'finish_reasons':[],'done_marker':False,'bytes':0}
        try:
            req=urllib.request.Request(old.BASE+self.path,data=body,headers={'Content-Type':'application/json'})
            with urllib.request.urlopen(req,timeout=120) as upstream, (folder/(ident+'-response.sse')).open('wb') as raw:
                self.send_response(200); self.send_header('Content-Type',upstream.headers.get('Content-Type','text/event-stream')); self.end_headers()
                for line in upstream:
                    raw.write(line); raw.flush(); info['bytes']+=len(line)
                    if line.startswith(b'data: '):
                        data=line[6:].strip()
                        if data==b'[DONE]': info['done_marker']=True
                        else:
                            try:
                                event=json.loads(data)
                                for choice in event.get('choices',[]):
                                    if choice.get('finish_reason') is not None: info['finish_reasons'].append(choice['finish_reason'])
                            except ValueError: pass
                    self.wfile.write(line); self.wfile.flush()
        except Exception as exc: info['error']=str(exc)
        finally:
            info['end']=now(); SAVE(folder/(ident+'-summary.json'),info)

def prepare():
    ROOT.mkdir(parents=True,exist_ok=True)
    SAVE(ROOT/'inventory.json',{'time':now(),'version':api('/api/version'),'tags':api('/api/tags'),'gpu':old.gpu()})
    for key,name in old.MODELS.items():
        for ctx in (16384,32768):
            api('/api/create',{'model':alias(key,ctx),'from':name,'parameters':{'num_ctx':ctx,'temperature':0,'presence_penalty':0,'repeat_penalty':1,'top_p':0.95,'top_k':40,'seed':42},'stream':False})
            SAVE(ROOT/f'model-{key}-{ctx}.json',api('/api/show',{'model':alias(key,ctx)}))

def wire_probe(key,repeat,mode):
    label=f'wire-{key}-{repeat}-{mode}'
    path=ROOT/'probes'/f'{label}.json'
    if path.exists(): return
    result={'label':label,'model':key,'kind':'wire','mode':mode,'preflight':preflight()}
    prompt='Call record exactly once with text equal to LOCAL_OK.'
    tool={'type':'function','function':{'name':'record','description':'Record a string','parameters':{'type':'object','properties':{'text':{'type':'string'}},'required':['text']}}}
    body={'model':alias(key,16384),'messages':[{'role':'user','content':prompt}],'tools':[tool],'temperature':0,'max_tokens':512,'reasoning_effort':'none','stream':mode=='stream'}
    started=time.monotonic()
    try:
        if mode=='native':
            response=api('/api/chat',{'model':alias(key,16384),'messages':body['messages'],'tools':[tool],'think':False,'stream':False,'options':{'num_predict':512}})
            calls=response['message'].get('tool_calls',[])
            result.update(response=response,finished=response.get('done',False),correct=any(c['function']['name']=='record' and c['function']['arguments']=={'text':'LOCAL_OK'} for c in calls))
        elif mode=='json':
            response=api('/v1/chat/completions',body)
            choice=response['choices'][0]; calls=choice['message'].get('tool_calls',[])
            result.update(response=response,finished=bool(choice.get('finish_reason')),correct=any(c['function']['name']=='record' and json.loads(c['function']['arguments'])=={'text':'LOCAL_OK'} for c in calls))
        else:
            req=urllib.request.Request(old.BASE+'/v1/chat/completions',data=json.dumps(body).encode(),headers={'Content-Type':'application/json'})
            with urllib.request.urlopen(req,timeout=120) as response: raw=response.read().decode()
            path.parent.mkdir(parents=True,exist_ok=True); path.with_suffix('.sse').write_text(raw,encoding='utf-8')
            events=[json.loads(line[6:]) for line in raw.splitlines() if line.startswith('data: ') and line[6:]!='[DONE]']
            finish=[c.get('finish_reason') for e in events for c in e.get('choices',[]) if c.get('finish_reason')]
            calls={}
            for e in events:
                for c in e.get('choices',[]):
                    for tc in c.get('delta',{}).get('tool_calls',[]):
                        target=calls.setdefault(tc.get('index',0),{'name':'','arguments':''})
                        for field in ('name','arguments'): target[field]+=tc.get('function',{}).get(field,'')
            result.update(finish_reasons=finish,finished=bool(finish),done_marker='data: [DONE]' in raw,tool_calls=calls,
                          correct=any(c['name']=='record' and json.loads(c['arguments'])=={'text':'LOCAL_OK'} for c in calls.values()))
        result['placement']=api('/api/ps')
    except Exception as exc: result['error']=str(exc)
    finally:
        result['seconds']=time.monotonic()-started; result['cleanup']=cleanup(); SAVE(path,result); report()

def cpu_probe(threads,repeat):
    label=f'cpu-smoffyy-{threads}-{repeat}'; path=ROOT/'probes'/f'{label}.json'
    if path.exists(): return
    result={'label':label,'kind':'cpu','threads':threads,'preflight':preflight()}
    try:
        common={'model':alias('smoffyy',16384),'stream':False,'think':False,'options':{'num_gpu':0,'num_thread':threads,'num_predict':256}}
        api('/api/chat',{**common,'messages':[{'role':'user','content':'Reply OK.'}]})
        start=time.monotonic()
        response=api('/api/chat',{**common,'messages':[{'role':'user','content':'Explain how a bicycle works in about 150 words.'}]})
        result.update(seconds=time.monotonic()-start,response=response,placement=api('/api/ps'),gpu=old.gpu(),tokens_per_second=response['eval_count']/(response['eval_duration']/1e9))
        result['verified_cpu']=all(m['size_vram']==0 for m in result['placement']['models']) and bool(result['placement']['models'])
    except Exception as exc: result['error']=str(exc)
    finally: result['cleanup']=cleanup(); SAVE(path,result); report()

def agent(key,task,ctx,repeat,prompt_suffix='',output_limit=4096):
    global ACTIVE,CAPTURE
    label=f'pi-{key}-{task}-{ctx}-{repeat}'; work=ROOT/'runs'/label
    if (work/'result.json').exists(): return
    work.mkdir(parents=True,exist_ok=False)
    if task=='hard':
        shutil.copy2(old.SPEC,work/'spec.md')
        prompt='Read spec.md and implement every requirement in tasks.py. Work incrementally; run python tasks.py test and repair failures.'
    else:
        fixture=TASKS[task]
        (work/'spec.md').write_text(fixture['spec'])
        (work/'solution.py').write_text(fixture['code'])
        (work/'test_public.py').write_text(fixture['public'])
        prompt='Read spec.md. Repair solution.py. Run python test_public.py and fix failures. Do not alter test_public.py.'
    prompt+=' Python is 3.11.9. Use only standard library. Work only in the current directory. No network, package installation, other agents, or files outside this directory. Finish with a brief summary.'
    prompt+=' '+prompt_suffix
    config=json.loads((old.ROOT/'pi-config-no-think/models.json').read_text())
    provider=config['providers']['lab']; provider['baseUrl']=f'http://127.0.0.1:{PROXY_PORT}/v1'
    model=provider['models'][0]; model.update(id=alias(key,ctx),contextWindow=ctx,maxTokens=output_limit)
    model['samplingParams'].update(max_tokens=output_limit,temperature=0,presence_penalty=0,frequency_penalty=0,reasoning_effort='none')
    provider['models']=[model]
    SAVE(work/'config/models.json',config)
    SAVE(work/'config/settings.json',{'compaction':{'enabled':True,'reserveTokens':output_limit,'keepRecentTokens':4096},'retry':{'enabled':False}})
    env=os.environ.copy()
    for name in list(env):
        if any(s in name.upper() for s in ('API_KEY','AUTH_TOKEN','OAUTH_TOKEN')): env.pop(name,None)
    env.update(PI_CODING_AGENT_DIR=str(work/'config'),PI_OFFLINE='1',PI_TELEMETRY='0',PYTHONIOENCODING='utf-8')
    command=['node',str(old.PI),'--offline','--no-extensions','--no-skills','--no-context-files','--no-prompt-templates','--no-themes','--no-session','--provider','lab','--model',alias(key,ctx),'--tools','read,write,edit,powershell','--mode','json','-p',prompt]
    result={'label':label,'model':key,'task':task,'context':ctx,'repeat':repeat,'preflight':preflight(),'started':now(),'time_limit':600 if task=='hard' else 240}
    result['prompt_suffix']=prompt_suffix
    result['output_limit']=output_limit
    start=time.monotonic(); CAPTURE=work
    try:
        with (work/'events.jsonl').open('w',encoding='utf-8') as out,(work/'stderr.txt').open('w',encoding='utf-8') as err:
            ACTIVE=subprocess.Popen(command,cwd=work,env=env,stdout=out,stderr=err,stdin=subprocess.DEVNULL)
            SAVE(work/'running.json',{'pid':ACTIVE.pid,'started':now()})
            while ACTIVE.poll() is None:
                check_time()
                if time.monotonic()-start>result['time_limit']:
                    result['timed_out']=True; break
                time.sleep(2)
            if ACTIVE.poll() is None:
                subprocess.run(['taskkill','/PID',str(ACTIVE.pid),'/T','/F'],capture_output=True); ACTIVE.wait(timeout=15)
            result['exit_code']=ACTIVE.returncode
        result['seconds']=time.monotonic()-start
        result['placement']=api('/api/ps')
        events=[]
        for line in (work/'events.jsonl').read_text(encoding='utf-8').splitlines():
            try: events.append(json.loads(line))
            except ValueError: pass
        assistants=[e['message'] for e in events if e.get('type')=='message_end' and e.get('message',{}).get('role')=='assistant']
        result['last_stop_reason']=assistants[-1].get('stopReason') if assistants else None
        result['agent_errors']=[m.get('errorMessage') for m in assistants if m.get('stopReason')=='error']
        result['tool_calls']=sum(e.get('type')=='tool_execution_start' for e in events)
        result['tool_errors']=sum(e.get('type')=='tool_execution_end' and e.get('isError',False) for e in events)
        result['wire']=[json.loads(p.read_text()) for p in (work/'wire').glob('*-summary.json')]
        if task=='hard':
            for script,filename in [(old.EVAL,'evaluation.txt'),(REPO/'benchmarks/eval_round_20260915.py','evaluation-extra.json')]:
                p=subprocess.run([sys.executable,str(script),str(work)],capture_output=True,text=True,timeout=120)
                (work/filename).write_text(p.stdout+p.stderr,encoding='utf-8')
            import re
            text=(work/'evaluation.txt').read_text()
            score=re.search(r'SCORE: (\d+)/10',text)
            result['score']=int(score.group(1)) if score else 0; result['total']=10
            try: result['extra']=json.loads((work/'evaluation-extra.json').read_text())
            except ValueError: pass
        else:
            p=subprocess.run([sys.executable,str(REPO/'benchmarks/night_tasks_20260916.py'),task,str(work/'solution.py')],capture_output=True,text=True,timeout=20)
            result['evaluation']=json.loads(p.stdout.strip().splitlines()[-1])
            result['score']=result['evaluation']['passed']; result['total']=result['evaluation']['total']
        result['clean_finish']=not result.get('timed_out') and result['exit_code']==0 and result['last_stop_reason']=='stop'
        result['success']=result['clean_finish'] and result['score']==result['total'] and (task!='hard' or result.get('extra',{}).get('passed')==4)
    except Exception as exc: result['error']=str(exc)
    finally:
        if ACTIVE is not None and ACTIVE.poll() is None:
            subprocess.run(['taskkill','/PID',str(ACTIVE.pid),'/T','/F'],capture_output=True); ACTIVE.wait(timeout=15)
        ACTIVE=None; CAPTURE=None
        result['cleanup']=cleanup(); SAVE(work/'result.json',result); report()

def report():
    runs=[json.loads(p.read_text()) for p in (ROOT/'runs').glob('*/result.json')]
    probes=[json.loads(p.read_text()) for p in (ROOT/'probes').glob('*.json')]
    state=json.loads((ROOT/'status.json').read_text()) if (ROOT/'status.json').exists() else {}
    SAVE(ROOT/'summary.json',{'status':state,'runs':runs,'probes':probes})
    lines=['# Overnight local AI experiments: September 16, 2026','',f"Status: **{state.get('phase','preparing')}**. Updated {now()}.",'',
           '## Design','',
           'One workload at a time; five-hour ceiling. Existing weights only. Raw native/JSON/SSE tool-call controls, repeated Python 3.11 bug repairs with external deterministic checks, CPU thread sweep, then 16k/32k hard-task trials on the two strongest repair candidates. Temperature 0 and sampling parameters are normalized using separate aliases; no global server settings are changed. Trials repeat deterministic configurations to measure operational stability, not stochastic model quality. Order is shuffled with a recorded fixed seed.',
           '', 'Pi sends an explicit 4096-token response cap and reasoning_effort=none. Compaction reserves 4096 tokens. Retries are disabled so failures remain visible. A loopback relay captures the actual request and raw SSE; it forwards without repairing or synthesizing finish events. Relay transport overhead and altered configuration mean these are not exact repetitions of September 15.',
           '', 'Raw records, wire captures, configurations, generated programs and evaluators: `C:/Users/kevin/ai_bench/overnight-20260916`. A STOP file there requests cancellation. External scorers are outside candidate workspaces. A score alone is not a successful agent run.',
           '', '## Coding trials','', '| Run | Checks | Clean finish | Seconds | Error / stop |','|---|---:|---|---:|---|']
    for r in runs:
        outcome=r.get('error') or ('timeout' if r.get('timed_out') else r.get('last_stop_reason','unknown'))
        lines.append(f"| {r['label']} | {r.get('score','?')}/{r.get('total','?')} | {r.get('clean_finish',False)} | {r.get('seconds',0):.1f} | {str(outcome).replace('|','/')} |")
    wire=[p for p in probes if p.get('kind')=='wire']
    lines+=['','## Direct tool-call transport controls','',f"Recorded {len(wire)} probes; {sum(p.get('correct',False) for p in wire)} correct tool calls; {sum(p.get('finished',False) for p in wire)} explicit terminal signals.",'']
    for key in old.MODELS:
        for mode in ('native','json','stream'):
            group=[p for p in wire if p['model']==key and p['mode']==mode]
            if group: lines.append(f"- {key}, {mode}: {sum(p.get('correct',False) for p in group)}/{len(group)} correct; {sum(p.get('finished',False) for p in group)}/{len(group)} terminal signals.")
    lines+=['','## CPU-only thread sweep','', '| Threads | Completed repeats | Median output tok/s | All placements CPU-only |','|---:|---:|---:|---|']
    for threads in (4,8,16,24):
        group=[p for p in probes if p.get('kind')=='cpu' and p['threads']==threads and 'tokens_per_second' in p]
        if group: lines.append(f"| {threads} | {len(group)} | {statistics.median(p['tokens_per_second'] for p in group):.2f} | {all(p['verified_cpu'] for p in group)} |")
    malformed=[w for r in runs for w in r.get('wire',[]) if not w.get('finish_reasons')]
    lines+=['','## Interpretation limits','',f"{sum(r.get('success',False) for r in runs)}/{len(runs)} completed coding records both finished cleanly and passed all external checks. {len(malformed)} captured agent streams lacked a finish reason; some may be intentional client disconnects or timeouts, so inspect the associated error and raw capture before attributing blame.",
            '', 'Small repair checks are separate from the historical hard-spec score. The historical scorer can award a rejection point to broken code; hard-task success also requires all four supplemental checks. CPU tests include a warm-up and use the same prose prompt; speed alone does not measure answer quality.',
            '', 'Sources consulted: [Ollama compatibility](https://docs.ollama.com/api/openai-compatibility), [Pi model configuration](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/models.md). No new external model benchmark claims are inferred from these sources.']
    REPORT.write_text('\n'.join(lines)+'\n',encoding='ascii',errors='backslashreplace')

def run():
    global DEADLINE,SERVER,PROXY_PORT
    ROOT.mkdir(parents=True,exist_ok=True)
    lock=ROOT/'RUNNING.lock'
    with lock.open('x') as f: f.write(str(os.getpid()))
    DEADLINE=time.monotonic()+LIMIT
    import ctypes
    ctypes.windll.kernel32.SetThreadExecutionState(0x80000001)
    try:
        status('preparing',budget_seconds=LIMIT); preflight(); prepare()
        SERVER=http.server.ThreadingHTTPServer(('127.0.0.1',0),Relay); SERVER.daemon_threads=True
        PROXY_PORT=SERVER.server_port
        threading.Thread(target=SERVER.serve_forever,daemon=True).start()
        plan=[(key,repeat,mode) for key in old.MODELS for repeat in range(1,4) for mode in ('native','json','stream')]
        random.Random(20260916).shuffle(plan)
        SAVE(ROOT/'plan.json',{'wire':plan,'small_repeats':3,'small_limit_seconds':240,'hard_repeats':3,'hard_limit_seconds':600,'total_limit_seconds':LIMIT,'selection':'top two mean repair pass fractions; clean finishes break ties'})
        for key,repeat,mode in plan:
            check_time(); status('transport-controls',model=key,repeat=repeat,mode=mode); wire_probe(key,repeat,mode)
        small=[(key,task,repeat) for key in old.MODELS for task in TASKS for repeat in range(1,4)]
        random.Random(20260917).shuffle(small)
        for key,task,repeat in small:
            check_time(); status('repair-trials',model=key,task=task,repeat=repeat); agent(key,task,16384,repeat)
        sweep=[(threads,repeat) for threads in (4,8,16,24) for repeat in range(1,4)]
        random.Random(20260918).shuffle(sweep)
        for threads,repeat in sweep:
            check_time(); status('cpu-sweep',threads=threads,repeat=repeat); cpu_probe(threads,repeat)
        runs=[json.loads(p.read_text()) for p in (ROOT/'runs').glob('*/result.json')]
        ranking=[]
        for key in old.MODELS:
            group=[r for r in runs if r['model']==key and r['task']!='hard']
            ranking.append((sum(r.get('score',0)/max(1,r.get('total',1)) for r in group)/max(1,len(group)),sum(r.get('clean_finish',False) for r in group),key))
        ranking.sort(reverse=True); selected=[r[2] for r in ranking[:2]]
        SAVE(ROOT/'selection.json',{'ranking':ranking,'selected':selected})
        hard=[(key,ctx,repeat) for key in selected for ctx in (16384,32768) for repeat in range(1,4)]
        random.Random(20260919).shuffle(hard)
        for key,ctx,repeat in hard:
            check_time(); status('hard-trials',model=key,context=ctx,repeat=repeat); agent(key,'hard',ctx,repeat)
        status('complete')
    except InterruptedError as exc: status('stopped',reason=str(exc))
    except Exception as exc: status('failed',reason=repr(exc)); raise
    finally:
        try: SAVE(ROOT/'final-cleanup.json',cleanup())
        finally:
            if SERVER: SERVER.shutdown(); SERVER.server_close()
            report(); lock.unlink(missing_ok=True)
            ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)

if __name__=='__main__':
    if sys.argv[1:] == ['run']: run()
    elif sys.argv[1:] == ['report']: report()
    else: raise SystemExit('Use run or report')
