"""Bounded local-only model/agent experiments; artifacts stay in ai_bench.

Commands: prepare, pull, probe KEY [cpu], agent HARNESS KEY LABEL [smoke] [no-think], unload.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import urllib.request

HOME = Path('C:/Users/kevin')
ROOT = HOME / 'ai_bench/round-20260915'
PI = HOME / 'ai_bench/pi-lab/node_modules/@earendil-works/pi-coding-agent/dist/bundle/cli.js'
EVAL = HOME / 'local-llm-lab/examples/eval2.py'
SPEC = HOME / 'ai_bench/hard-test/spec2.md'
BASE = 'http://127.0.0.1:11434'
MODELS = {
    'qwen': 'qwen3.5:9b',
    'smoffyy': 'hf.co/Smoffyy/Qwen3.5-4B-Instruct-Revised-GGUF:Q4_K_M',
    'omni': 'hf.co/Tesslate/OmniCoder-9B-GGUF:Q4_K_M',
}
CTX = 16384

def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2), encoding='utf-8')

def api(route, body=None, timeout=600):
    req = urllib.request.Request(BASE + route, data=None if body is None else json.dumps(body).encode(),
                                 headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.load(response)

def gpu():
    p = subprocess.run(['nvidia-smi', '--query-gpu=memory.used,memory.free,utilization.gpu',
                        '--format=csv,noheader,nounits'], capture_output=True, text=True)
    return p.stdout.strip()

def unload():
    before = gpu()
    resident = api('/api/ps')['models']
    for model in resident:
        api('/api/generate', {'model': model['name'], 'keep_alive': 0})
    for _ in range(20):
        if not api('/api/ps')['models']:
            break
        time.sleep(0.5)
    remaining = api('/api/ps')['models']
    if remaining:
        raise RuntimeError('Resident models remain; refusing concurrent test')
    state = {'before_gpu_mib_used_free_util': before, 'unloaded': [m['name'] for m in resident],
             'after_gpu_mib_used_free_util': gpu()}
    print('PREFLIGHT ' + json.dumps(state), flush=True)
    return state

def alias(key):
    return 'lab-20260915-' + key + '-16k'

def prepare():
    ROOT.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SPEC, ROOT / 'spec2.md')
    save(ROOT / 'inventory.json', {'version': api('/api/version'), 'models': api('/api/tags'),
                                 'gpu': gpu(), 'spec_sha256': hashlib.sha256(SPEC.read_bytes()).hexdigest(),
                                 'evaluator_sha256': hashlib.sha256(EVAL.read_bytes()).hexdigest()})
    providers = {'lab': {'baseUrl': BASE + '/v1', 'api': 'openai-completions', 'apiKey': 'local-only',
                        'compat': {'supportsDeveloperRole': False, 'supportsReasoningEffort': False,
                                   'maxTokensField': 'max_tokens', 'supportsStore': False},
                        'models': [{'id': alias(k), 'contextWindow': CTX, 'maxTokens': 8192,
                                    'samplingParams': {'temperature': 0, 'max_tokens': 8192}, 'reasoning': False} for k in MODELS]}}
    save(ROOT / 'pi-config/models.json', {'providers': providers})
    save(ROOT / 'pi-config/settings.json', {'defaultProvider': 'lab', 'defaultModel': alias('qwen'),
                                         'compaction': {'enabled': True, 'reserveTokens': 4096, 'keepRecentTokens': 4096}})
    fast_providers = json.loads(json.dumps(providers))
    for model in fast_providers['lab']['models']:
        model['samplingParams']['reasoning_effort'] = 'none'
    save(ROOT / 'pi-config-no-think/models.json', {'providers': fast_providers})
    shutil.copy2(ROOT / 'pi-config/settings.json', ROOT / 'pi-config-no-think/settings.json')
    print('Prepared isolated Pi configuration', flush=True)

def pull():
    installed = {m['name'] for m in api('/api/tags')['models']}
    for key, name in MODELS.items():
        if name not in installed:
            print('PULL ' + name, flush=True)
            req = urllib.request.Request(BASE + '/api/pull', data=json.dumps({'model': name, 'stream': True}).encode(),
                                         headers={'Content-Type': 'application/json'})
            last = 0
            with urllib.request.urlopen(req, timeout=1800) as response:
                for line in response:
                    event = json.loads(line)
                    if 'error' in event:
                        raise RuntimeError(event['error'])
                    if time.monotonic() - last > 15 or event.get('status') == 'success':
                        print(json.dumps(event), flush=True)
                        last = time.monotonic()
        api('/api/create', {'model': alias(key), 'from': name,
                           'parameters': {'num_ctx': CTX, 'temperature': 0}, 'stream': False})
        save(ROOT / ('model-' + key + '.json'), api('/api/show', {'model': alias(key)}))
        print('READY ' + alias(key), flush=True)

def probe(key, cpu=False):
    label = key + ('-cpu' if cpu else '-gpu')
    path = ROOT / ('probe-' + label + '.json')
    if path.exists():
        raise RuntimeError('Result exists: ' + str(path))
    result = {'key': key, 'cpu_requested': cpu, 'preflight': unload(), 'context': CTX, 'probes': []}
    options = {'num_ctx': CTX, 'num_predict': 384, 'temperature': 0}
    if cpu:
        options.update(num_gpu=0, num_thread=8)
    prompts = [
        ('throughput', 'Explain how a bicycle works in about 180 words. Use full sentences.', None),
        ('extraction', 'Return only JSON with keys name, count, color. Text: We ordered seven blue cables for Morgan. name means the person.',
         {'name': 'Morgan', 'count': 7, 'color': 'blue'}),
        ('instruction', 'Reply with exactly: LOCAL_OK', 'LOCAL_OK'),
        ('reasoning', 'A ticket and a case cost 135 dollars total. The case costs 105 dollars more than the ticket. What is the ticket price? Reply with only the number.', '15'),
    ]
    try:
        for title, prompt, expected in prompts:
            started = time.monotonic()
            response = api('/api/chat', {'model': alias(key), 'messages': [{'role': 'user', 'content': prompt}],
                                        'stream': False, 'think': False, 'options': options, 'keep_alive': '5m'})
            content = response['message'].get('content', '').strip()
            try:
                parsed = json.loads(content) if isinstance(expected, dict) else content
                passed = None if expected is None else parsed == expected
            except ValueError:
                passed = False
            item = {'name': title, 'pass': passed, 'response': response, 'wall_seconds': time.monotonic() - started,
                    'placement': api('/api/ps'), 'gpu': gpu()}
            result['probes'].append(item)
            print('PROBE ' + title + ' ' + json.dumps({'pass': passed, 'answer': content[:180]}), flush=True)
            save(path, result)
    finally:
        result['cleanup'] = unload()
        save(path, result)

def agent(harness, key, label, smoke=False, thinking=None):
    work = ROOT / 'runs' / label
    work.mkdir(parents=True, exist_ok=False)
    shutil.copy2(SPEC, work / 'spec2.md')
    prompt = ('Create hello.py that prints LOCAL_OK, execute it using Python and confirm the output.' if smoke else
              'Read spec2.md and implement every requirement as tasks.py. Work incrementally, execute python tasks.py test, '
              'fix any failures and finish the implementation. Do not merely describe a solution.')
    prompt += ' Work only in the current directory. Use Python standard library; do not install packages or use network, other agents, or files outside this directory.'
    env = os.environ.copy()
    for name in list(env):
        if any(s in name for s in ('API_KEY', 'AUTH_TOKEN', 'OAUTH_TOKEN')):
            env.pop(name, None)
    env.update(PI_CODING_AGENT_DIR=str(ROOT / 'pi-config'), PI_OFFLINE='1', PI_TELEMETRY='0',
               PYTHONIOENCODING='utf-8', OLLAMA_API_BASE=BASE, NO_COLOR='1')
    if harness == 'pi':
        if thinking:
            config = json.loads((ROOT / 'pi-config/models.json').read_text(encoding='utf-8'))
            for model in config['providers']['lab']['models']:
                model['samplingParams']['reasoning_effort'] = thinking
            private_config = work / 'pi-config'
            save(private_config / 'models.json', config)
            shutil.copy2(ROOT / 'pi-config/settings.json', private_config / 'settings.json')
            env['PI_CODING_AGENT_DIR'] = str(private_config)
        command = ['node', str(PI), '--offline', '--no-extensions', '--no-skills', '--no-context-files',
                   '--no-prompt-templates', '--no-themes', '--no-session', '--provider', 'lab', '--model', alias(key),
                   '--tools', 'read,write,edit,powershell', '--mode', 'json', '-p', prompt]
    elif harness == 'opencode':
        config = {'enabled_providers': ['lab'], 'model': 'lab/' + alias(key), 'small_model': 'lab/' + alias(key),
                  'autoupdate': False, 'share': 'disabled', 'snapshot': False,
                  'permission': {'external_directory': 'deny', 'webfetch': 'deny', 'websearch': 'deny', 'task': 'deny'},
                  'provider': {'lab': {'npm': '@ai-sdk/openai-compatible', 'options': {'baseURL': BASE + '/v1', 'apiKey': 'local-only'},
                                       'models': {alias(key): {'name': alias(key), 'limit': {'context': CTX, 'output': 8192}}}}}}
        env['OPENCODE_CONFIG_CONTENT'] = json.dumps(config)
        command = [str(HOME / 'AppData/Roaming/npm/node_modules/opencode-ai/bin/opencode.exe'),
                   'run', '--pure', '--auto', '--format', 'json', '-m', 'lab/' + alias(key), prompt]
    elif harness == 'aider':
        command = ['C:/AiderEnv/Scripts/aider.exe', '--model', 'ollama_chat/' + alias(key), '--no-git',
                   '--yes-always', '--no-show-model-warnings', '--no-check-update', '--no-analytics',
                   '--edit-format', 'whole', '--auto-test', '--test-cmd', 'python tasks.py test',
                   '--read', 'spec2.md', '--message', prompt, 'tasks.py']
    else:
        raise ValueError(harness)
    meta = {'harness': harness, 'model': alias(key), 'label': label, 'smoke': smoke,
            'context': CTX, 'preflight': unload(), 'time_limit_seconds': 180 if smoke else 600}
    meta['reasoning_effort'] = thinking or 'server_default'
    meta['pi_settings'] = json.loads((ROOT / 'pi-config/settings.json').read_text(encoding='utf-8'))
    meta['pi_models_config'] = json.loads(Path(env['PI_CODING_AGENT_DIR'], 'models.json').read_text(encoding='utf-8'))
    save(work / 'run.json', meta)
    start = time.monotonic()
    try:
        with (work / 'events.jsonl').open('w', encoding='utf-8') as out, (work / 'stderr.txt').open('w', encoding='utf-8') as err:
            p = subprocess.Popen(command, cwd=work, env=env, stdout=out, stderr=err, stdin=subprocess.DEVNULL)
            meta['process_id'] = p.pid
            save(work / 'run.json', meta)
            try:
                deadline = start + meta['time_limit_seconds']
                while True:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        raise subprocess.TimeoutExpired(command, meta['time_limit_seconds'])
                    try:
                        meta['exit_code'] = p.wait(timeout=min(30, remaining))
                        break
                    except subprocess.TimeoutExpired:
                        if time.monotonic() >= deadline:
                            raise
                        print('RUNNING ' + label + ' seconds=' + str(round(time.monotonic() - start)), flush=True)
            except subprocess.TimeoutExpired:
                subprocess.run(['taskkill', '/PID', str(p.pid), '/T', '/F'], capture_output=True)
                p.wait(timeout=15)
                meta['timed_out'] = True
        meta['wall_seconds'] = round(time.monotonic() - start, 2)
        meta['placement'] = api('/api/ps')
        meta['gpu_after'] = gpu()
        if not smoke:
            evaluation = subprocess.run([sys.executable, str(EVAL), str(work)], capture_output=True, text=True, timeout=180)
            (work / 'evaluation.txt').write_text(evaluation.stdout + evaluation.stderr, encoding='utf-8')
            meta['evaluation'] = evaluation.stdout
            print(evaluation.stdout, flush=True)
            extra = subprocess.run([sys.executable, str(Path(__file__).with_name('eval_round_20260915.py')), str(work)],
                                   capture_output=True, text=True, timeout=180)
            (work / 'evaluation-extra.json').write_text(extra.stdout, encoding='utf-8')
            meta['extra_evaluation'] = extra.stdout
        print('AGENT ' + json.dumps({k: v for k, v in meta.items() if k not in ('evaluation', 'placement')}), flush=True)
    finally:
        meta['cleanup'] = unload()
        save(work / 'run.json', meta)

if __name__ == '__main__':
    cmd, *args = sys.argv[1:]
    if cmd == 'prepare': prepare()
    elif cmd == 'pull': pull()
    elif cmd == 'probe': probe(args[0], len(args) > 1 and args[1] == 'cpu')
    elif cmd == 'agent': agent(*args[:3], smoke='smoke' in args[3:], thinking='none' if 'no-think' in args[3:] else None)
    elif cmd == 'unload': unload()
    else: raise SystemExit('Unknown command')
