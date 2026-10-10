"""Two CPU packing rounds with reversed order and explicit memory qualification."""
import argparse
import ctypes
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
import compare_staging_20260922 as base
import compare_bonsai_packing_20260922 as packing
import overnight_research_20260922 as overnight

ROOT=Path('C:/Users/kevin/ai_bench/cpu-headroom-20260923-v1')


def memory():
    class Memory(ctypes.Structure):
        _fields_=[('length',ctypes.c_ulong),('load',ctypes.c_ulong)]+[(n,ctypes.c_ulonglong) for n in
            ('total','available','page_total','page_available','virtual_total','virtual_available','extended')]
    m=Memory()
    m.length=ctypes.sizeof(m)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m)):
        raise OSError('Cannot inspect memory')
    return dict(time=time.time(),available=m.available,commit_headroom=m.page_available,commit_limit=m.page_total)


def qualified(sample,loaded=False):
    return sample['available'] >= (3 if loaded else 14)*1024**3 and sample['commit_headroom'] >= (3 if loaded else 10)*1024**3


def counters():
    cmd=['powershell.exe','-NoProfile','-Command',
         "Get-Counter '\\Memory\\Pages Input/sec','\\Memory\\Page Reads/sec','\\Memory\\Committed Bytes','\\Memory\\Commit Limit' -ErrorAction Stop | Select-Object -ExpandProperty CounterSamples | Select-Object Path,CookedValue | ConvertTo-Json -Compress"]
    proc=base.spawn_owned(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,creationflags=base.NO_WINDOW)
    try:
        out,err=proc.communicate(timeout=8)
        if proc.returncode:
            raise RuntimeError(err)
        return json.loads(out)
    finally:
        if proc.poll() is None:
            base.stop_owned(proc)
        cleanup=base.finish_owned(proc)
        if cleanup['returncode'] or cleanup['active_before']:
            raise RuntimeError('Counter process cleanup failed')


def run(root):
    overnight.verify(root)
    base.OWNED_JOBS=True
    state=dict(status='checking',jobs=[],started=time.time())
    def save(): overnight.save(root/'status.json',state)
    save()
    first=memory()
    state['initial_memory']=first
    if not qualified(first):
        state.update(status='held',reason='Need 14 GiB physical and 10 GiB commit headroom before CPU loading')
        save()
        print(json.dumps(state),flush=True)
        return
    packing.preflight()
    with (root/'RUNNING.lock').open('x') as handle: handle.write(str(__import__('os').getpid()))
    try:
        for index,name in enumerate(('PTQ1','PQ2','PQ2','PTQ1')):
            overnight.verify(root)
            packing.preflight()
            if list((overnight.LAB/'goproverbs/results').glob('**/RUNNING.lock')):
                raise RuntimeError('Go inference lock present')
            if not qualified(memory()):
                state.update(status='held',reason='Headroom fell before next packing')
                break
            label=f'headroom-20260923-{index+1}-{name.lower()}'
            output=overnight.BENCH/'packing-20260922'/label
            if output.exists(): raise RuntimeError('Refusing to reuse output '+str(output))
            row=dict(label=label,status='running',output=str(output),started=time.time())
            state['jobs'].append(row)
            state['status']='running'
            save()
            cmd=[sys.executable,str(root/'source/compare_bonsai_packing_20260922.py'),'--label',label,
                 '--run','--cpu','--only',name+'-ctx8192-ngl0','--request-timeout','600']
            with (root/(label+'.log')).open('w') as log, (root/(label+'-memory.jsonl')).open('w') as telemetry:
                proc=base.spawn_owned(cmd,stdout=log,stderr=subprocess.STDOUT,creationflags=base.NO_WINDOW)
                start=time.monotonic()
                next_counters=0
                try:
                    while proc.poll() is None:
                        sample=memory()
                        if time.monotonic() >= next_counters:
                            sample['paging_counters']=counters()
                            next_counters=time.monotonic()+10
                        telemetry.write(json.dumps(sample)+'\n')
                        telemetry.flush()
                        if not qualified(sample,loaded=True) or (root/'STOP').exists() or time.monotonic()-start>3600:
                            row['invalid_reason']='Memory qualification, STOP, or one-hour case cap'
                            row['termination']=base.stop_owned(proc)
                            break
                        time.sleep(.5)
                finally:
                    if proc.poll() is None: row['termination']=base.stop_owned(proc)
                    row['cleanup']=base.finish_owned(proc)
            row.update(exit_code=proc.returncode,finished=time.time())
            if row.get('invalid_reason') or proc.returncode or row['cleanup']['returncode'] or row['cleanup']['active_before']:
                row['status']='invalid'
                state['status']='stopped'
                break
            row['status']='complete'
            save()
        else:
            state['status']='complete'
    except BaseException as exc:
        state.update(status='failed',error=repr(exc))
        raise
    finally:
        state.update(finished=time.time(),final_model_processes=packing.active_processes(),final_models=base.api('/api/ps'))
        (root/'RUNNING.lock').unlink()
        save()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('prepare','run','check'))
    parser.add_argument('--root',type=Path,default=ROOT)
    args=parser.parse_args()
    if args.action=='prepare':
        overnight.prepare(args.root)
        shutil.copy2(Path(__file__),args.root/'source'/Path(__file__).name)
        shutil.copy2(overnight.LAB/'CPU-HEADROOM-PLAN-2026-09-23.md',args.root/'PROTOCOL.md')
        files=list((args.root/'source').glob('*'))+[args.root/'PROTOCOL.md',base.PI]
        overnight.save(args.root/'manifest.json',{str(p):base.sha(p) for p in files})
    elif args.action=='check':
        print(json.dumps(dict(memory=memory(),qualified=qualified(memory())),indent=2))
    else:
        if Path(__file__).parent.resolve()!=(args.root/'source').resolve():
            raise RuntimeError('Run frozen source')
        run(args.root)


if __name__=='__main__': main()
