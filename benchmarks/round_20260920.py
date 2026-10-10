"""Pinned replay and agent comparison. One inference workload at a time."""
import argparse
import copy
import hashlib
import http.server
import json
import os
from pathlib import Path
import random
import shutil
import subprocess
import sys
import threading
import time
import urllib.request
import urllib.error
import uuid

import overnight_20260916 as night
import diagnose_stream_20260916 as diagnosis
import eval_tasks_v2 as evaluator
from night_tasks_20260916 import TASKS

ROOT = Path('C:/Users/kevin/ai_bench/round-20260920')
REPO = Path('C:/Users/kevin/local-llm-lab')
OLD_PI = night.old.PI
NEW_PI = ROOT.parent/'pi-lab-0861/node_modules/@earendil-works/pi-coding-agent/dist/bundle/cli.js'
SAVE = night.SAVE

def status(phase, **extra):
    SAVE(ROOT/'status.json', dict(phase=phase, utc=night.now(), pid=os.getpid(), **extra))
    print(night.now(), phase, json.dumps(extra), flush=True)

def metadata():
    return dict(utc=night.now(), ollama=night.api('/api/version'), tags=night.api('/api/tags'),
                gpu=night.old.gpu(), python=sys.version,
                evaluator_sha256=hashlib.sha256((REPO/'benchmarks/eval_tasks_v2.py').read_bytes()).hexdigest())

def replay():
    folder = ROOT/'replay'
    folder.mkdir(parents=True, exist_ok=True)
    SAVE(folder/'inventory.json', metadata())
    source = json.loads(diagnosis.SOURCE.read_text())
    show = night.api('/api/show', {'model':source['model']})
    SAVE(folder/'model.json', show)
    SAVE(folder/'source.json', dict(path=str(diagnosis.SOURCE), sha256=hashlib.sha256(diagnosis.SOURCE.read_bytes()).hexdigest()))
    diagnosis.ROOT = folder
    for cap in (4096,8192,12288):
        if (folder/f'stream-{cap}.json').exists(): continue
        status('replay', cap=cap)
        diagnosis.run('stream', cap)
    status('replay-complete')

class Relay(night.Relay):
    def do_POST(self):
        capture = night.CAPTURE
        if capture is None or self.path != '/v1/chat/completions':
            self.send_error(404); return
        folder = capture/'wire'
        folder.mkdir(exist_ok=True)
        ident = uuid.uuid4().hex
        body = self.rfile.read(int(self.headers.get('Content-Length','0')))
        (folder/(ident+'-request.json')).write_bytes(body)
        info = dict(start=night.now(), finish_reasons=[], done_marker=False)
        sent = False
        start = time.monotonic()
        try:
            request = urllib.request.Request(night.old.BASE+self.path,data=body,headers={'Content-Type':'application/json'})
            with urllib.request.urlopen(request,timeout=600) as response, (folder/(ident+'-response.sse')).open('wb') as raw:
                self.send_response(response.status)
                self.send_header('Content-Type',response.headers.get('Content-Type','text/event-stream'))
                self.end_headers(); sent = True
                for line in response:
                    raw.write(line); raw.flush()
                    if line.startswith(b'data: '):
                        info.setdefault('first_event_seconds',time.monotonic()-start)
                        data = line[6:].strip()
                        if data==b'[DONE]': info['done_marker']=True
                        else:
                            try:
                                event=json.loads(data)
                                if event.get('usage'): info['usage']=event['usage']
                                for choice in event.get('choices',[]):
                                    if choice.get('finish_reason') is not None: info['finish_reasons'].append(choice['finish_reason'])
                            except ValueError: pass
                    self.wfile.write(line); self.wfile.flush()
        except urllib.error.HTTPError as exc:
            error = exc.read()
            (folder/(ident+'-error.json')).write_bytes(error)
            info.update(error=error.decode(errors='replace'),http_status=exc.code)
            if not sent:
                self.send_response(exc.code); self.end_headers(); self.wfile.write(error)
        except Exception as exc:
            info['error']=repr(exc)
            if not sent: self.send_error(502, 'Local upstream failed')
        finally:
            info.update(end=night.now(),seconds=time.monotonic()-start)
            SAVE(folder/(ident+'-summary.json'),info)

def stop_owned_process(process):
    """Bound Windows taskkill itself; preserve its outcome for diagnosis."""
    info = {}
    try:
        p = subprocess.run(['taskkill','/PID',str(process.pid),'/T','/F'], capture_output=True, text=True, timeout=15)
        info.update(exit_code=p.returncode, stdout=p.stdout, stderr=p.stderr)
    except subprocess.TimeoutExpired:
        info['tree_kill_timed_out'] = True
    if process.poll() is None:
        process.kill()
        info['direct_kill'] = True
    process.wait(timeout=5)
    return info

def agent(version, task, repeat, port, backend='ollama', context=32768, output_limit=12288, isolated=False):
    label = f'{backend}-pi-{version}-{task}-{repeat}' + ('-isolated' if isolated else '')
    work = ROOT/'runs'/label
    if (work/'result.json').exists(): return
    work.mkdir(parents=True, exist_ok=False)
    workspace = work/'workspace' if isolated else work
    workspace.mkdir(exist_ok=True)
    result = dict(label=label, version=version, task=task, repeat=repeat, backend=backend,
                  context=context, output_limit=output_limit, started=night.now(),
                  isolated_workspace=isolated, workspace=str(workspace))
    if backend == 'ollama': result['preflight'] = night.preflight()
    else: result['preflight'] = dict(gpu=night.old.gpu())
    if task == 'hard':
        shutil.copy2(REPO/'examples/spec2-tasks.md', workspace/'spec.md')
        prompt = 'Read spec.md and implement every requirement in tasks.py. Work incrementally; run python tasks.py test and repair failures.'
    else:
        fixture = TASKS[task]
        (workspace/'spec.md').write_text(fixture['spec'], encoding='ascii')
        (workspace/'solution.py').write_text(fixture['code'], encoding='ascii')
        (workspace/'test_public.py').write_text(fixture['public'], encoding='ascii')
        prompt = 'Read spec.md. Repair solution.py. Run python test_public.py and fix failures. Do not alter test_public.py.'
    prompt += ' Python is 3.11.9. Use only standard library. Work only in the current directory. No network, package installation, other agents, or files outside this directory. Finish with a brief summary.'
    prompt += ' Keep file writes and edits incremental; do not repeat identical failing actions.'
    (work/'prompt.txt').write_text(prompt, encoding='ascii')
    config = json.loads((ROOT.parent/'stream-diagnosis-20260916/pi-config-roomy/models.json').read_text())
    provider = config['providers']['lab']
    provider['baseUrl'] = f'http://127.0.0.1:{port}/v1'
    model = provider['models'][0]
    model.update(id='night-20260916-omni-32768' if backend=='ollama' else 'bonsai2', contextWindow=context, maxTokens=output_limit)
    model['samplingParams']['max_tokens'] = output_limit
    if backend != 'ollama':
        model['samplingParams']['chat_template_kwargs'] = {'enable_thinking':False}
    SAVE(work/'config/models.json', config)
    SAVE(work/'config/settings.json', {'cacheWarming':'off', 'compaction':{'enabled':True,'reserveTokens':output_limit,'keepRecentTokens':4096},'retry':{'enabled':False}})
    env = os.environ.copy()
    for name in list(env):
        if any(s in name.upper() for s in ('API_KEY','AUTH_TOKEN','OAUTH_TOKEN')): env.pop(name,None)
    env.update(PI_CODING_AGENT_DIR=str(work/'config'), PI_OFFLINE='1', PI_TELEMETRY='0', PYTHONIOENCODING='utf-8')
    cli = OLD_PI if version=='0.85.1' else NEW_PI
    command = ['node',str(cli),'--offline','--no-extensions','--no-skills','--no-context-files','--no-prompt-templates','--no-themes','--no-session','--provider','lab','--model',model['id'],'--tools','read,write,edit,powershell','--mode','json','-p',prompt]
    result['cli_sha256'] = hashlib.sha256(cli.read_bytes()).hexdigest()
    result['time_limit'] = 600 if task=='hard' else 180
    status('agent', label=label)
    night.CAPTURE = work
    start = time.monotonic()
    process = None
    try:
        with (work/'events.jsonl').open('w',encoding='utf-8') as out, (work/'stderr.txt').open('w',encoding='utf-8') as err:
            process = subprocess.Popen(command, cwd=workspace, env=env, stdout=out, stderr=err, stdin=subprocess.DEVNULL)
            SAVE(work/'process.json',dict(pid=process.pid,command=command[:-1]))
            while process.poll() is None:
                if (ROOT/'STOP').exists() or time.monotonic()-start > result['time_limit']:
                    result['timed_out'] = True
                    result['timeout_cleanup'] = stop_owned_process(process)
                    break
                # First artifact is preserved without interfering with writes.
                artifact = workspace/('tasks.py' if task=='hard' else 'solution.py')
                if artifact.exists() and not (work/'first-artifact.py').exists():
                    shutil.copy2(artifact,work/'first-artifact.py')
                time.sleep(1)
            result['exit_code'] = process.returncode
        result['seconds'] = time.monotonic()-start
        events = []
        for line in (work/'events.jsonl').read_text(encoding='utf-8').splitlines():
            try: events.append(json.loads(line))
            except ValueError: pass
        messages = [e['message'] for e in events if e.get('type')=='message_end' and e.get('message',{}).get('role')=='assistant']
        result['stop_reason'] = messages[-1].get('stopReason') if messages else None
        result['agent_errors'] = [m.get('errorMessage') for m in messages if m.get('stopReason')=='error']
        result['tool_calls'] = sum(e.get('type')=='tool_execution_start' for e in events)
        result['tool_errors'] = sum(e.get('type')=='tool_execution_end' and e.get('isError',False) for e in events)
        result['usage'] = [m.get('usage') for m in messages if m.get('usage')]
        result['clean_finish'] = not result.get('timed_out') and result['exit_code']==0 and result['stop_reason']=='stop'
        if task=='hard':
            scored = evaluator.evaluate(workspace)
            SAVE(work/'evaluation-v2.json',scored)
            result.update(score=scored['passed'],total=scored['total'])
            p = subprocess.run([sys.executable,str(REPO/'examples/eval2.py'),str(workspace)], capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=120,env=env)
            (work/'evaluation-historical.txt').write_text(p.stdout+p.stderr,encoding='utf-8')
        else:
            p = subprocess.run([sys.executable,str(REPO/'benchmarks/night_tasks_20260916.py'),task,str(workspace/'solution.py')],capture_output=True,text=True,timeout=25,env=env)
            scored = json.loads(p.stdout.strip().splitlines()[-1])
            SAVE(work/'evaluation.json',scored)
            result.update(score=scored['passed'],total=scored['total'])
        result['success'] = result['clean_finish'] and result['score']==result['total']
        if backend=='ollama': result['placement'] = night.api('/api/ps')
        result['gpu'] = night.old.gpu()
    except Exception as exc: result['error'] = repr(exc)
    finally:
        if process is not None and process.poll() is None:
            result['final_process_cleanup'] = stop_owned_process(process)
        # Relay handlers finish independently; do not fabricate terminal signals.
        time.sleep(1)
        night.CAPTURE = None
        if backend=='ollama': result['cleanup'] = night.cleanup()
        SAVE(work/'result.json',result)
        print(json.dumps({k:v for k,v in result.items() if k in ('label','score','total','clean_finish','seconds','error','stop_reason')}),flush=True)

def agents():
    night.DEADLINE = time.monotonic()+7200
    SAVE(ROOT/'agent-inventory.json',metadata())
    server = http.server.ThreadingHTTPServer(('127.0.0.1',0), Relay)
    server.daemon_threads = True
    threading.Thread(target=server.serve_forever,daemon=True).start()
    plan = [(v,t,r) for v in ('0.85.1','0.86.1') for t in ('graph','intervals') for r in (1,2,3)]
    random.Random(20260920).shuffle(plan)
    plan += [('0.85.1','hard',1),('0.86.1','hard',1)]
    SAVE(ROOT/'agent-plan.json',plan)
    try:
        for version,task,repeat in plan:
            if (ROOT/'STOP').exists(): raise InterruptedError('STOP requested')
            agent(version,task,repeat,server.server_port)
    finally:
        server.shutdown(); server.server_close()
        SAVE(ROOT/'agent-final-cleanup.json',night.cleanup())
    status('agents-complete')

if __name__=='__main__':
    ROOT.mkdir(parents=True,exist_ok=True)
    lock = ROOT/'RUNNING.lock'
    with lock.open('x') as f: f.write(str(os.getpid()))
    try:
        if sys.argv[1]=='replay': replay()
        elif sys.argv[1]=='agents': agents()
        else: raise ValueError('Expected replay or agents')
    finally: lock.unlink(missing_ok=True)
