"""Bounded serial stock-GGUF placement/throughput screen with enforced memory gates."""
import argparse
import ctypes as C
from ctypes import wintypes as W
import datetime
import hashlib
import json
from pathlib import Path
import re
import socket
import statistics
import subprocess
import threading
import time
import urllib.error
import urllib.request
from a3b_preflight_20260924 import BASE, GIB, RUNTIME, inspect, placements, memory, process_inventory, ollama_state, eligibility

ROOT = BASE/'ai_bench/a3b-offload-20260924-v1'
PORT = 8097
URL = 'http://127.0.0.1:'+str(PORT)


def save(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=True), encoding='ascii')


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(8*1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def gpu():
    raw = subprocess.check_output(['nvidia-smi','--query-gpu=memory.free,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True,timeout=10)
    free, used, utilization = map(float, raw.strip().splitlines()[0].split(','))
    return {'gpu_free_gib': free/1024, 'gpu_used_gib': used/1024, 'gpu_utilization_pct': utilization}


def danger(sample):
    return [key for key, threshold in [('physical_available_gib',3),('commit_headroom_gib',2),('gpu_free_gib',0.5)] if sample[key] < threshold]


class Paging:
    class Value(C.Structure):
        _fields_ = [('status',W.DWORD),('value',C.c_double)]

    def __init__(self):
        self.dll = C.WinDLL('pdh')
        self.query = W.HANDLE()
        self.counter = W.HANDLE()
        self.dll.PdhOpenQueryW.argtypes = [W.LPCWSTR,C.c_size_t,C.POINTER(W.HANDLE)]
        self.dll.PdhAddEnglishCounterW.argtypes = [W.HANDLE,W.LPCWSTR,C.c_size_t,C.POINTER(W.HANDLE)]
        self.dll.PdhCollectQueryData.argtypes = [W.HANDLE]
        self.dll.PdhGetFormattedCounterValue.argtypes = [W.HANDLE,W.DWORD,C.POINTER(W.DWORD),C.POINTER(self.Value)]
        self.dll.PdhCloseQuery.argtypes = [W.HANDLE]
        if self.dll.PdhOpenQueryW(None,0,C.byref(self.query)):
            raise RuntimeError('Cannot open Windows paging monitor')
        if self.dll.PdhAddEnglishCounterW(self.query,r'\Memory\Pages Input/sec',0,C.byref(self.counter)):
            raise RuntimeError('Cannot add hard-page input counter')
        self.dll.PdhCollectQueryData(self.query)

    def sample(self):
        if self.dll.PdhCollectQueryData(self.query):
            raise RuntimeError('Paging monitor collection failed')
        value = self.Value()
        rc = self.dll.PdhGetFormattedCounterValue(self.counter,0x200,None,C.byref(value))
        if rc or value.status not in (0,1):
            return None
        return value.value

    def close(self):
        self.dll.PdhCloseQuery(self.query)


def process_memory(pid):
    class Counters(C.Structure):
        _fields_ = [('cb',W.DWORD),('faults',W.DWORD)]+[(name,C.c_size_t) for name in ('peak_ws','ws','peak_paged','paged','peak_nonpaged','nonpaged','pagefile','peak_pagefile','private')]
    kernel = C.WinDLL('kernel32',use_last_error=True)
    kernel.OpenProcess.argtypes=[W.DWORD,W.BOOL,W.DWORD]
    kernel.OpenProcess.restype=W.HANDLE
    kernel.CloseHandle.argtypes=[W.HANDLE]
    api = C.WinDLL('psapi')
    api.GetProcessMemoryInfo.argtypes=[W.HANDLE,C.POINTER(Counters),W.DWORD]
    handle = kernel.OpenProcess(0x410,False,pid)
    if not handle:
        return {}
    try:
        counters=Counters()
        counters.cb=C.sizeof(counters)
        if not api.GetProcessMemoryInfo(handle,C.byref(counters),counters.cb):
            raise RuntimeError('Cannot read owned server memory')
        return {'server_working_gib':counters.ws/GIB,'server_private_gib':counters.private/GIB,'server_page_faults_total_soft_and_hard':counters.faults}
    finally:
        kernel.CloseHandle(handle)


class Monitor:
    def __init__(self, folder):
        self.folder=folder
        self.process=None
        self.error=None
        self.phase='loading'
        self.stop=threading.Event()
        self.deadline=time.monotonic()+300
        self.paging=Paging()
        self.thread=threading.Thread(target=self.loop,daemon=True)

    def abort(self, reason):
        self.error=reason
        if self.process is not None and self.process.poll() is None:
            self.process.terminate() # Only the Popen-owned server, never another process.

    def loop(self):
        pressure=0
        with (self.folder/'resources.jsonl').open('w',encoding='ascii') as log:
            while not self.stop.is_set():
                try:
                    sample={**memory(),**gpu(),'time_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'phase':self.phase,'hard_pages_input_per_sec_system':self.paging.sample()}
                    if self.process is not None:
                        sample.update(process_memory(self.process.pid))
                    log.write(json.dumps(sample)+'\n'); log.flush()
                    pressure=pressure+1 if sample['physical_available_gib']<4 and (sample['hard_pages_input_per_sec_system'] or 0)>512 else 0
                    reasons=danger(sample)
                    if reasons or pressure>=10 or time.monotonic()>self.deadline or (ROOT/'STOP').exists():
                        self.abort('memory_or_deadline_or_stop: '+str(reasons)+', paging_pressure_samples='+str(pressure))
                        return
                except Exception as exc:
                    self.abort('monitor_failure: '+repr(exc))
                    return
                self.stop.wait(1)

    def close(self):
        self.stop.set();self.thread.join(15);self.paging.close()
        if self.thread.is_alive():
            raise RuntimeError('Monitor did not stop')


def request(endpoint, body=None, timeout=10):
    data=None if body is None else json.dumps(body).encode()
    req=urllib.request.Request(URL+endpoint,data=data,headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=timeout) as response:
        return json.load(response)


def stream(tokens, folder, label, monitor, count=256):
    body={'prompt':tokens,'n_predict':count,'temperature':0,'seed':240924,'cache_prompt':False,'stream':True,'return_tokens':True,'ignore_eos':True}
    save(folder/(label+'-request.json'),body)
    req=urllib.request.Request(URL+'/completion',data=json.dumps(body).encode(),headers={'Content-Type':'application/json'})
    monitor.phase=label;monitor.deadline=time.monotonic()+240
    started=time.monotonic();first=None;terminal=None;generated=[];text=[]
    with (folder/(label+'-events.jsonl')).open('w',encoding='ascii') as log:
        with urllib.request.urlopen(req,timeout=240) as response:
            for line in response:
                if not line.startswith(b'data: '):continue
                payload=line[6:].strip()
                if payload==b'[DONE]':break
                event=json.loads(payload)
                log.write(json.dumps(event,ensure_ascii=True)+'\n');log.flush()
                if first is None and (event.get('tokens') or event.get('content')):first=time.monotonic()-started
                generated.extend(event.get('tokens',[]));text.append(event.get('content',''))
                if event.get('stop'):terminal=event
    if monitor.error:raise RuntimeError(monitor.error)
    if not terminal or terminal.get('stop_type')!='limit' or terminal.get('truncated'):
        raise RuntimeError('Missing complete bounded stream or truncated context')
    timing=terminal.get('timings',{})
    if timing.get('predicted_n')!=count or timing.get('prompt_n',0)<len(tokens)-1:
        raise RuntimeError('Unexpected token count or prompt reuse: '+str(timing))
    result={'label':label,'wall_seconds':time.monotonic()-started,'ttft_seconds':first,'timings':timing,'tokens':generated,'text':''.join(text),'terminal':terminal,'quality_claim':False}
    save(folder/(label+'-result.json'),result)
    return result


def prompt_tokens(count):
    # Raw code continuation workload, not a chat/tool or coding-correctness evaluation.
    text='\n'.join('def function_'+str(i)+'(x):\n    return x + '+str(i)+'\n' for i in range(700))
    tokens=request('/tokenize',{'content':text,'add_special':True})['tokens']
    if len(tokens)<count:raise RuntimeError('Insufficient prompt tokens')
    return tokens[:count]


def preflight(model, layers, own_lock):
    processes=process_inventory()
    competing=[p for p in processes if p['name'].lower().startswith(('llama-server','llama-cli','llama-bench','vllm','kobold'))]
    if competing:raise RuntimeError('Competing inference processes: '+str(competing))
    resident=ollama_state(processes)
    locks=[str(p) for p in (BASE/'ai_bench').rglob('RUNNING.lock') if p!=own_lock]
    mem=memory();graphics=gpu()
    plan=placements(inspect(Path(model['path'])),mem,graphics['gpu_free_gib'])
    row=next(x for x in plan['placements'] if x['cpu_expert_layers']==layers)
    return {'memory':mem,'gpu':graphics,'placement':row,'holds':eligibility(row,resident,locks),'ollama':resident,'locks':locks}


def run_case(case, model, root, lock):
    folder=root/case['name'];folder.mkdir()
    check=preflight(model,case['layers'],lock);save(folder/'preflight.json',check)
    if check['holds']:
        result={**case,'status':'held','reasons':check['holds']};save(folder/'result.json',result);return result
    with socket.socket() as probe:
        probe.bind(('127.0.0.1',PORT))
    cmd=[str(RUNTIME),'--model',model['path'],'--host','127.0.0.1','--port',str(PORT),'--ctx-size','8192','--parallel','1','--n-gpu-layers','999','--n-cpu-moe',str(case['layers']),'--fit','off','--threads',str(case['threads']),'--threads-batch',str(case['threads']),'--batch-size','512','--ubatch-size','128','--flash-attn','on','--cache-type-k','f16','--cache-type-v','f16','--cache-ram','0','--cache-reuse','0','--no-warmup','--no-context-shift','--load-mode',case['load_mode'],'-lv','5']
    save(folder/'command.json',cmd)
    server=None;monitor=None;result={**case,'status':'failed'}
    before=time.monotonic()
    try:
        monitor=Monitor(folder);monitor.thread.start()
        with (folder/'server.log').open('w',encoding='utf8') as log:
            if monitor.error:raise RuntimeError(monitor.error)
            server=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
            monitor.process=server
            if monitor.error:server.terminate();raise RuntimeError(monitor.error)
            while time.monotonic()-before<300:
                if monitor.error:raise RuntimeError(monitor.error)
                if server.poll() is not None:raise RuntimeError('Server exited '+str(server.returncode))
                try:
                    if request('/health',timeout=2).get('status')=='ok':break
                except (urllib.error.URLError,TimeoutError):pass
                time.sleep(0.5)
            else:raise TimeoutError('Model load exceeded 300 seconds')
            load=time.monotonic()-before
            log_text=(folder/'server.log').read_text(encoding='utf8',errors='replace')
            if 'RTX 5070' not in log_text or not re.search(r'CUDA0.*(?:model buffer|buffer size)',log_text):
                raise RuntimeError('CUDA placement not evidenced in load log')
            save(folder/'props.json',request('/props'))
            short=prompt_tokens(512);long=prompt_tokens(4096)
            save(folder/'prompts.json',{'short':short,'long':long,'sha256':hashlib.sha256(json.dumps([short,long]).encode()).hexdigest(),'format':'raw code continuation; ignore_eos throughput only'})
            stream(short,folder,'warmup',monitor,64)
            measurements=[]
            for repetition in range(3):
                for length,tokens in [('short',short),('long',long)]:
                    measurements.append(stream(tokens,folder,length+'-'+str(repetition+1),monitor))
                    print(json.dumps({'case':case['name'],'completed':measurements[-1]['label'],'decode_tps':measurements[-1]['timings'].get('predicted_per_second')}),flush=True)
            result.update(status='complete',load_seconds=load,summary={length:{'median_decode_tps':statistics.median(x['timings']['predicted_per_second'] for x in measurements if x['label'].startswith(length)), 'median_ttft_seconds':statistics.median(x['ttft_seconds'] for x in measurements if x['label'].startswith(length))} for length in ('short','long')})
    except Exception as exc:
        result['error']=repr(exc)
    finally:
        if server is not None and server.poll() is None:
            server.terminate()
            try:server.wait(10)
            except subprocess.TimeoutExpired:server.kill();server.wait(10)
        if monitor is not None:
            monitor.close()
            result['monitor_error']=monitor.error
        result['server_exited']=server is None or server.poll() is not None
        time.sleep(3)
        result['after_cleanup']={**memory(),**gpu()}
        result['cleanup_gpu_ok']=result['after_cleanup']['gpu_free_gib']>=check['gpu']['gpu_free_gib']-0.5
        result['cleanup_ram_ok']=result['after_cleanup']['physical_available_gib']>=check['memory']['physical_available_gib']-1
        if not result['cleanup_gpu_ok'] or not result['cleanup_ram_ok']:
            result['status']='failed_cleanup'
        save(folder/'result.json',result)
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--matrix',choices=('placements','threads','thinking','single'),required=True)
    p.add_argument('--load-mode',choices=('auto','none'),default='auto')
    p.add_argument('--layers',type=int,choices=(32,36,40,48),default=36)
    p.add_argument('--threads',type=int,choices=(8,16,24),default=8)
    p.add_argument('--monitor-self-check',action='store_true')
    args=p.parse_args()
    if args.monitor_self_check:
        paging=Paging();time.sleep(1);print(json.dumps({**memory(),**gpu(),**process_memory(__import__('os').getpid()),'hard_pages_input_per_sec_system':paging.sample()}));paging.close();return
    root=ROOT/('serial-'+args.matrix+'-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'));root.mkdir()
    for name in ('a3b_serial_20260924.py','a3b_preflight_20260924.py','test_a3b_preflight_20260924.py'):
        (root/name).write_bytes(Path(__file__).with_name(name).read_bytes())
    lock=ROOT/'RUNNING.lock'
    with lock.open('x',encoding='ascii') as f:f.write(json.dumps({'pid':__import__('os').getpid(),'run':str(root)}))
    results=[]
    try:
        evidence=json.loads((ROOT/'preflight-postboot-01.json').read_text())
        model=evidence['models'][1 if args.matrix=='thinking' else 0]
        # Full model hash read is streaming; no model tensor loading or inference here.
        actual=digest(Path(model['path']))
        if 'sha256:'+actual!=model['manifest_digest_not_rehashed']:raise RuntimeError('Model digest mismatch')
        save(root/'identity.json',{'model':model['ollama_name'],'model_sha256':actual,'runtime_sha256':digest(RUNTIME),'script_sha256':digest(Path(__file__)),'preflight_sha256':digest(Path(__file__).with_name('a3b_preflight_20260924.py'))})
        cases=([{'layers':n,'threads':8} for n in (36,32,40,48)] if args.matrix=='placements' else [{'layers':args.layers,'threads':n} for n in (16,24)] if args.matrix=='threads' else [{'layers':args.layers,'threads':args.threads}])
        for case in cases:
            case['load_mode']=args.load_mode
            case['name']=args.matrix+'-cpu'+str(case['layers'])+'-t'+str(case['threads'])
            result=run_case(case,model,root,lock);results.append(result);save(root/'results.json',results)
            print(json.dumps({'case':case['name'],'status':result['status'],'error':result.get('error'),'summary':result.get('summary')}),flush=True)
            if result['status'].startswith('failed'):break
    finally:
        lock.unlink(missing_ok=True)
        save(root/'status.json',{'state':'finished','results':results,'time_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})
        print('RUN_DIRECTORY='+str(root),flush=True)


if __name__=='__main__':main()
