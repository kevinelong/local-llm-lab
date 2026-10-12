"""Provisioning tweaks, and the check that proves they took effect.

Three changes, one root, all declared:
  1. Server context 32,768 -> 131,072 (`-c`), because six historical witnesses died with a prompt of
     32,475-32,764 against a 32,768 window - and because the box has been measured at 262,144 with
     26-27 GiB still free, so 32k was a choice, not a limit.
  2. Host context window + per-reply cap 32,768/12,288 -> 131,072/32,768 in the OMP model descriptor,
     so the agent can actually use the window the server now offers.
  3. Server-side thinking budget `--reasoning-budget 6144` with a wrap-up message, i.e. the
     llama.cpp-side equivalent of the Strata fix that produced 10/10: bound the thinking so the model
     answers before the reply cap arrives. The sibling `--reasoning-format deepseek` is already set by
     the harness. Note: upstream reported this sampler hanging in some 2026 builds (forge#54,
     llama.cpp#22717), so this root *measures* it rather than assuming it works.
Context shift stays disabled (llama.cpp default, confirmed in this build's help) and `--cache-reuse`
is left at 0: it reuses cache via KV shifting, which is not something to enable blind on long sessions.

Usage: python provision.py build | args | check
"""
import importlib.util
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

BASE = Path(r'C:\Users\kevin\ai_bench')
DRIVER = BASE / 'new-items-20261007'
TEMPLATE = BASE / 'candidates-20261007-v26-1'
ROOT = BASE / 'provision-20261008-v1'
SERVER_CONTEXT = '131072'
HOST_CONTEXT = 131072
HOST_MAX_TOKENS = 32768
REASONING_BUDGET = '6144'
BUDGET_MESSAGE = 'Stop thinking and act now: run the check you intended, or make the edit you intended.'
SIBLINGS = ('staged_tasks_20260922.py', 'owned_process_20260922.py', 'night_tasks_20260916.py',
            'test_compare_staging_20260922.py', 'validate_staged_tasks_20260922.py')

LAUNCH_ANCHOR = "  def launch(self,args,**kwargs):\n   args=list(args)\n   if str(args[0])==str(lab.RUNTIME):"
LAUNCH_PATCH = '''  def launch(self,args,**kwargs):
   args=list(args)
   if str(args[0])==str(lab.RUNTIME):
    # 2026-10-08 DECLARED provisioning changes (see README): raise the served context, and bound the
    # thinking so the reply cannot be cut before the model acts. Every floor and gate is unchanged.
    if '-c' in args:
     args[args.index('-c')+1]=SERVER_CONTEXT
    if '--reasoning-format' in args:
     at=args.index('--reasoning-format')+2
     args[at:at]=['--reasoning-budget',REASONING_BUDGET,'--reasoning-budget-message',BUDGET_MESSAGE]'''

CONFIG_ANCHOR = " lab.base=fresh\n"
CONFIG_PATCH = ''' lab.base=fresh
 # 2026-10-08 DECLARED: the host's model descriptor carries contextWindow 32768 / maxTokens 12288,
 # which would cap the session below the context the server now serves. Raise both in the yml the
 # harness writes, so the agent can use the window. Nothing else in the descriptor changes.
 _harness_configuration=lab.configuration
 def _configuration_with_bigger_window(folder,harness,port):
  env=_harness_configuration(folder,harness,port)
  path=folder/'config'/'models.yml'
  if path.exists():
   data=json.loads(path.read_text(encoding='utf-8'))
   for provider in (data.get('providers') or {}).values():
    for model in provider.get('models') or []:
     model['contextWindow']=HOST_CONTEXT
     model['maxTokens']=HOST_MAX_TOKENS
   path.write_text(json.dumps(data,indent=1),encoding='utf-8')
  return env
 lab.configuration=_configuration_with_bigger_window'''


def build():
    if ROOT.exists():
        raise SystemExit('%s already exists' % ROOT)
    (ROOT / 'evidence').mkdir(parents=True)
    (ROOT / 'source').mkdir()
    (ROOT / 'models').mkdir()
    shutil.copyfile(TEMPLATE / 'manifest.json', ROOT / 'manifest.json')
    shutil.copyfile(TEMPLATE / 'protocol.json', ROOT / 'protocol.json')
    text = (TEMPLATE / 'run.py').read_text(encoding='utf-8')
    for anchor, patch in ((LAUNCH_ANCHOR, LAUNCH_PATCH), (CONFIG_ANCHOR, CONFIG_PATCH)):
        assert text.count(anchor) == 1, 'anchor not unique: %r' % anchor[:60]
        text = text.replace(anchor, patch)
    # names for the patched constants, injected after the module constants block
    marker = "SOURCE=ROOT.parent/'completion-20260923-v1/source'"
    assert text.count(marker) == 1
    text = text.replace(marker,
        "SERVER_CONTEXT=%r\nHOST_CONTEXT=%d\nHOST_MAX_TOKENS=%d\nREASONING_BUDGET=%r\nBUDGET_MESSAGE=%r\n%s" % (
            SERVER_CONTEXT, HOST_CONTEXT, HOST_MAX_TOKENS, REASONING_BUDGET, BUDGET_MESSAGE, marker))
    (ROOT / 'run.py').write_text(text, encoding='utf-8')
    for extra in SIBLINGS:
        shutil.copyfile(TEMPLATE / 'source' / extra, ROOT / 'source' / extra)
    for model_dir in (TEMPLATE / 'models').iterdir():
        target = ROOT / 'models' / model_dir.name
        target.mkdir(parents=True, exist_ok=True)
        for model in model_dir.iterdir():
            import os
            os.link(model, target / model.name)
    (ROOT / 'README.md').write_text(
        '# provision-20261008-v1: raised context and a server-side thinking budget\n\n'
        'Template `candidates-20261007-v26-1` (Qwen3.6-35B-A3B Q4_K_M plain, three frozen tasks).\n\n'
        'Declared changes, all three visible in `evidence/provision.json`:\n'
        '1. served context `-c` 32768 -> %s (six historical witnesses died at prompt 32.5-32.8k);\n'
        '2. host model descriptor contextWindow/maxTokens -> %d/%d, so the agent can use it;\n'
        '3. `--reasoning-budget %s` with a wrap-up message - the llama.cpp equivalent of the Strata\n'
        '   thinking budget that took the ledger to 10/10. This sampler has upstream hang reports, so\n'
        '   `check` verifies a generation actually returns rather than assuming it.\n'
        'Unchanged: context shift stays disabled (llama.cpp default), --cache-reuse 0, every memory\n'
        'gate and floor, the 720 s task wall, and the relay.\n' % (
            SERVER_CONTEXT, HOST_CONTEXT, HOST_MAX_TOKENS, REASONING_BUDGET), encoding='ascii')
    return ROOT


def args_report():
    """Show the exact launch arguments the patched runner will use."""
    spec = importlib.util.spec_from_file_location('prov', ROOT / 'run.py')
    module = importlib.util.module_from_spec(spec)
    module.__dict__['__file__'] = str(ROOT / 'run.py')
    import sys as _sys
    _sys.argv = ['run.py']
    spec.loader.exec_module(module)
    print('constants in the patched runner: context=%s host_window=%s host_max=%s budget=%s' % (
        module.SERVER_CONTEXT, module.HOST_CONTEXT, module.HOST_MAX_TOKENS, module.REASONING_BUDGET))
    source = (ROOT / 'run.py').read_text(encoding='utf-8')
    for needle in ("args[args.index('-c')+1]=SERVER_CONTEXT", "'--reasoning-budget'",
                   "'--reasoning-budget-message'", "lab.configuration=_configuration_with_bigger_window",
                   "model['contextWindow']=HOST_CONTEXT"):
        print('  %-52s present=%s' % (needle, needle in source))
    return source


def check():
    """Run the real screen in the provisioned root, then verify what the run actually used.

    Session is local to the runner's coding(), so the check is the run itself plus an inspection pass:
    served context from each server log, the launch command, the host descriptor the harness wrote, the
    per-task scores, and whether the reasoning-budget sampler returned (upstream reports of it hanging).
    """
    root = ROOT
    log = root / 'evidence' / 'qwen36-35b-a3b-run.log'
    with log.open('w', encoding='utf8') as handle:
        proc = subprocess.run([sys.executable, str(root / 'run.py'), 'coding', 'qwen36-35b-a3b'],
                              cwd=str(root), stdout=handle, stderr=subprocess.STDOUT, timeout=14400)
    out = {'returncode': proc.returncode, 'sessions': {}}
    for folder in sorted(root.glob('qwen36-35b-a3b-*')):
        entry = {}
        server = folder / 'server.log'
        if server.exists():
            text = server.read_text(encoding='utf-8', errors='replace')
            entry['n_ctx'] = sorted({m.group(1) for m in re.finditer(r'n_ctx\s*[:=]\s*(\d+)', text)})[:4]
            entry['unknown_argument'] = [l.strip() for l in text.splitlines() if 'unknown argument' in l.lower()][:3]
            entry['errors'] = [l.strip() for l in text.splitlines() if 'error' in l.lower()][:3]
        status = folder / 'status.json'
        if status.exists():
            data = json.loads(status.read_text(encoding='utf-8'))
            command = data.get('command') or (data.get('before') or {}).get('command')
            if command:
                flat = [str(a) for a in command]
                entry['context_arg'] = flat[flat.index('-c') + 1] if '-c' in flat else None
                entry['reasoning_budget'] = flat[flat.index('--reasoning-budget') + 1] if '--reasoning-budget' in flat else None
                entry['budget_message_present'] = '--reasoning-budget-message' in flat
        models = folder / 'config' / 'models.yml'
        if models.exists():
            data = json.loads(models.read_text(encoding='utf-8'))
            for provider in (data.get('providers') or {}).values():
                for model in provider.get('models') or []:
                    entry['host_contextWindow'] = model.get('contextWindow')
                    entry['host_maxTokens'] = model.get('maxTokens')
        result = folder / 'result.json'
        if result.exists():
            data = json.loads(result.read_text(encoding='utf-8'))
            evaluation = data.get('evaluation') or {}
            entry.update({'passed': evaluation.get('passed'), 'total': evaluation.get('total'),
                          'seconds': round(data.get('seconds') or 0, 1),
                          'tokens': data.get('completion_tokens'),
                          'stop': (data.get('final_text') or '')[:0] or None})
            turns = []
            events = folder / 'events.jsonl'
            if events.exists():
                for line in events.read_text(encoding='utf-8', errors='replace').splitlines():
                    if '"message_end"' not in line:
                        continue
                    try:
                        event = json.loads(line)
                    except ValueError:
                        continue
                    if (event.get('message') or {}).get('role') == 'assistant':
                        turns.append(event['message'].get('stopReason'))
            entry['last_stop'] = turns[-1] if turns else None
        out['sessions'][folder.name] = entry
    (root / 'evidence' / 'provision.json').write_text(json.dumps(out, indent=1, default=str), encoding='ascii')
    print(json.dumps(out, indent=1, default=str)[:2500])
    return 0


if __name__ == '__main__':
    action = sys.argv[1] if len(sys.argv) > 1 else 'build'
    if action == 'build':
        print('built:', build())
    elif action == 'args':
        args_report()
    elif action == 'check':
        raise SystemExit(check())
