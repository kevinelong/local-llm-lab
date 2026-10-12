"""One CPU model, loopback-only serial HTTP, then exit and release all tensors."""
import hashlib
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import math
from pathlib import Path
import subprocess
import sys
import threading
import time

ROOT = Path(__file__).parent
IDENTITIES = {
    'laya':'laya-multilingual@e4e9ddf21a7b1903b7acffd8814ad4307bf63a67',
    'openjev':'openjev-0.8b-v5@058a6c24911b46d908fbe23541390f8af3df3e4d',
}
MAX_LEN=2048

def main():
    model_name, split, directory = sys.argv[1:]
    assert model_name in IDENTITIES and split in ('timing','natural')
    dest=Path(directory)
    import torch
    torch.set_num_threads(4)
    torch.set_num_interop_threads(1)
    torch.manual_seed(17)
    assert not torch.cuda.is_available(), 'CPU-only environment required'
    started=time.perf_counter()
    model_path=ROOT.parent/'local-decisions-20260925-v1'/'models'/model_name
    if model_name=='laya':
        from laya import Agent
        from laya.common import build_sequence
        model=Agent(str(model_path),device='cpu',fast=False,compile=False)
        assert model.device.type=='cpu' and not model.amp_enabled
        def predict(state, questions):
            counts=[]
            for q in questions.values():
                internal=model._to_internal(q)
                seq,_=build_sequence(model.tok,state,internal,max_len=100000,head_max_len=256)
                if len(seq)>MAX_LEN:
                    raise ValueError('token_budget_exceeded')
                counts.append(len(seq))
            result=model.system_one(state,questions,max_len=MAX_LEN,head_max_len=256)
            return result['answers'],counts
    else:
        sys.path.insert(0,str(ROOT.parent/'local-decisions-20260925-v1'/'upstream/openjev'))
        from openjev_decide import OpenJev,TEMPLATE
        model=OpenJev.from_pretrained(str(model_path),device='cpu',dtype=torch.float32,bs=1,max_len=MAX_LEN)
        model.ce.model.config.use_cache=False
        def predict(state, questions):
            text=json.dumps(state,ensure_ascii=False)
            counts=[]
            for q in questions.values():
                for label in ['no','yes']:
                    hyp=TEMPLATE.format(instr=q['instructions'].strip(),label=label,crit=label)
                    encoded=model.ce.tok(model.ce.template.format(premise=text.strip(),hypothesis=hyp.strip()),truncation=False)['input_ids']
                    if len(encoded)>MAX_LEN:
                        raise ValueError('token_budget_exceeded')
                    counts.append(len(encoded))
            native=model.decide(state,[{**q,'options':['no','yes']} for q in questions.values()])
            return {key:{'type':'noul','noul':row['noul']} for key,row in zip(questions,native)},counts
    parameters=model.model.parameters() if model_name=='laya' else model.ce.model.parameters()
    dtypes=sorted({str(p.dtype) for p in parameters})
    if dtypes!=['torch.float32']:
        raise RuntimeError('Unexpected parameter dtypes: '+str(dtypes))
    (dest/'loaded.json').write_text(json.dumps({'model':IDENTITIES[model_name],'device':'cpu','parameter_dtypes':dtypes,
        'load_seconds':time.perf_counter()-started,'torch':torch.__version__,'threads':torch.get_num_threads()},indent=2))
    print('MODEL_READY '+IDENTITIES[model_name],flush=True)
    limit=len(json.loads((ROOT/(split+'-inputs.json')).read_text()))
    attempted=0
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args): pass
        def do_POST(self):
            nonlocal attempted
            try:
                if self.path!='/v1/systemone': raise ValueError('invalid_route')
                length=int(self.headers.get('Content-Length','0'))
                if not 0<length<=16000: raise ValueError('invalid_size')
                body=json.loads(self.rfile.read(length))
                if body.get('model')!=IDENTITIES[model_name]: raise ValueError('model_mismatch')
                questions=body['questions']
                if set(questions)!={'stuck'} or any(q['type']!='noul' for q in questions.values()):
                    raise ValueError('invalid_questions')
                if attempted>=limit: raise ValueError('budget_exceeded')
                attempted+=1
                start=time.perf_counter()
                with torch.inference_mode():
                    answers,counts=predict(body['state'],questions)
                for a in answers.values():
                    if not isinstance(a['noul'],(int,float)) or not math.isfinite(a['noul']) or not 0<=a['noul']<=1:
                        raise ValueError('invalid_probability')
                response={'model':IDENTITIES[model_name],'answers':answers,'tokenCounts':counts,
                          'usage':{'input_tokens':sum(counts),'output_tokens':0}}
                with (dest/'server.jsonl').open('a') as f:
                    f.write(json.dumps({'attempt':attempted,'inference_ms':1000*(time.perf_counter()-start),'tokenCounts':counts,
                        'state_sha256':hashlib.sha256(json.dumps(body['state'],sort_keys=True).encode()).hexdigest()})+'\n')
                encoded=json.dumps(response,allow_nan=False).encode()
                self.send_response(200)
            except Exception as exc:
                print(type(exc).__name__+': '+str(exc),flush=True)
                encoded=json.dumps({'error':type(exc).__name__}).encode()
                self.send_response(422)
            self.send_header('Content-Type','application/json')
            self.send_header('Content-Length',str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)
    server=HTTPServer(('127.0.0.1',8098),Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True)
    thread.start()
    try:
        result=subprocess.run(['node',str(ROOT/'replay-local.mjs'),model_name,split,str(dest/'predictions.jsonl')],
            timeout=750,creationflags=subprocess.CREATE_NO_WINDOW)
        if result.returncode:raise RuntimeError('Local replay failed')
        if attempted!=limit:raise RuntimeError('Incorrect request count')
    finally:
        server.shutdown();server.server_close();thread.join(10)

if __name__=='__main__':main()
