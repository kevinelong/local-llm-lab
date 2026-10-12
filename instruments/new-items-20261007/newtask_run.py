"""Run the new ledger2 task live, in a root that also runs the three frozen tasks.

Plumbing (verified offline before any inference): the relay scores an artifact by running
`staged_tasks_20260922.py <task> <artifact>` in its own directory, and the runner imports TASKS from
the same module name. So the root gets a *superset* module under that exact name, which re-exports
the frozen module and adds `ledger2`; putting the root's source directory first on sys.path makes
both the runner's import and the relay's subprocess resolve to it. The relay itself is untouched.

Usage: python newtask_run.py [--check] [qwen36-35b-a3b ...]
"""
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

BASE = Path(r'C:\Users\kevin\ai_bench')
DRIVER = BASE / 'new-items-20261007'
# Each model needs its own root, because the root hardlinks that model's weights and the runner's
# CLI must accept its name. `newtasks-20261008-v2..` are the re-baseline roots for the top group.
MODEL_TEMPLATES = {
    'qwen36-35b-a3b': 'candidates-20261007-v26-1',
    'kolibri-1': 'candidates-20261007-v7',
    'swift': 'candidates-20261007-v8',
    'nemotron-3.5-lightning-30b': 'candidates-20261007-v20-2',
    'gpt-oss-20b': 'candidates-20261007-v18-1',
    'minicpm': 'candidates-20261007-v13-3',
}
ROOT_FOR = {
    'qwen36-35b-a3b': 'newtasks-ctx-20261008-v8',   # tonight: repeat (n=2) with the declared repo wall
    'kolibri-1': 'newtasks-ctx-20261008-v9',
    'swift': 'newtasks-ctx-20261009-v11',   # retry: v6 usage-gap smoke, v10 131k KV monitor trip
    'nemotron-3.5-lightning-30b': 'newtasks-ctx-20261008-v7',
    'gpt-oss-20b': 'newtasks-ctx-20261008-v2',
    'minicpm': 'newtasks-ctx-20261008-v5',
}
# Provisioning declaration for every new-task root (verified in provision-20261008-v1).
SERVER_CONTEXT = '131072'
HOST_CONTEXT = 131072
HOST_MAX_TOKENS = 32768
REASONING_BUDGET = '6144'
BUDGET_MESSAGE = 'Stop thinking and act now: run the check you intended, or make the edit you intended.'
# 2026-10-08 DECLARED per-model session quota. MiniCPM's `repo` ended on `length` at exactly
# 48,000 tokens with no effective edit - a budget stop, not a capability verdict - so its
# root declares 96,000 to find out which it was.
BUDGET_QUOTA = {'minicpm': 96000}
# 2026-10-09 DECLARED RANKING CHANGE (Kevin's instruction): `events` and `paths` are RETIRED from
# ranking. The census shows them splitting on 5/76 and 3/75 checks in the top group, so they absorb
# budget and manufacture ties. They stay in the loop as sanity checks; the ranking metric is the
# discriminating subset below (70 + 226 + 78 + 40 = 414 checks).
RANKED_TASKS = ('ledger', 'ledger2', 'repo', 'longctx')
# 2026-10-09 DECLARED CONTEXT CONVENTION: each model is reported at the context it can afford, and the
# context travels with the number. Probed 65,536 and 131,072 on the exempt model: both trip its GPU
# floor during load, so Swift's affordable window is 32,768 while the others run at 131,072, and a
# table row without its context is unreadable.
# 2026-10-09 DECLARED: models whose runtime cannot take the provisioning flags. Measured for Swift
# Bonsai 2 on its Prism fork (staged-swift-20260930): a raised context crosses the 0.5 GiB GPU floor
# during *model load* - 65,536 bottomed at 0.31 GiB **twice** (24.8 s and 26.0 s) and 131,072 at
# 0.49, all monitor stops, while 32,768 holds 0.69-1.28 GiB across two runs. Generation-time peaks are a poor guide here (max GPU
# used only moves 10.38 -> 11.18 GiB between the 32k and 131k runs); the load is what trips. Those
# models keep their template's context and flags and take only the runtime-agnostic changes (relay
# usage-gap tolerance, the raised reply cap, the repo wall).
PROVISION_EXEMPT = {'swift': 'Prism fork: a raised context (65,536 and 131,072 both measured) crosses the 0.5 GiB GPU floor at load; 32,768 holds'}
# Single source of truth for the long-context prompt: injected into every new-task root's run.py below,
# and reused by the Strata port (newtask_strata.py), so both suites ask for the same work.
LONGCTX_PROMPT = ('Read README.md. legacy.py in this directory is a large generated module of helpers. '
 'Exactly one function, reconcile_batch, is wrong and the rest must keep their exact source. Use grep '
 'and read to find it, fix only that function, run the public tests, audit the cases the public tests '
 'do not cover, and finish with a brief summary.')
TEMPLATE = BASE / MODEL_TEMPLATES['qwen36-35b-a3b']
ROOT = BASE / ROOT_FOR['qwen36-35b-a3b']
BATTERY = DRIVER / 'new_tasks_20261008.py'
REPO_BATTERY = DRIVER / 'new_tasks_repo.py'
SIBLINGS = ('owned_process_20260922.py', 'night_tasks_20260916.py', 'test_compare_staging_20260922.py',
            'validate_staged_tasks_20260922.py')
SUPERSET = '''"""Superset scorer for the 2026-10-08 new-task root: frozen tasks plus ledger2.

Named `staged_tasks_20260922.py` deliberately: the relay's score_artifact runs that filename in its
own directory, and the runner imports TASKS from that name, so shadowing it here adds the new task to
both paths without editing the relay.
"""
import importlib.util
import json
import sys
from pathlib import Path

SOURCE = Path(r'C:\\Users\\kevin\\ai_bench\\completion-20260923-v1\\source')
if str(SOURCE) not in sys.path:
    sys.path.insert(0, str(SOURCE))


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


frozen = _load(SOURCE / 'staged_tasks_20260922.py', 'frozen_tasks_20260922')
battery = _load(Path(__file__).with_name('new_tasks_20261008.py'), 'ledger2_battery')
repo = _load(Path(__file__).with_name('new_tasks_repo.py'), 'repo_battery')
longctx = _load(Path(__file__).with_name('new_tasks_longctx.py'), 'longctx_battery')
repo2 = _load(Path(__file__).with_name('new_tasks_repo2.py'), 'repo2_battery')
perf = _load(Path(__file__).with_name('new_tasks_perf.py'), 'perf_battery')
longctx2 = _load(Path(__file__).with_name('new_tasks_longctx2.py'), 'longctx2_battery')

TASKS = dict(frozen.TASKS)
TASKS.update(battery.TASKS)
TASKS.update({'repo': {'spec': repo.FILES['README.md'], 'code': repo.FILES['solution.py'],
                       'public': repo.FILES['test_public.py']}})
TASKS.update({'longctx': {'spec': longctx.SPEC, 'code': longctx.SHIM, 'public': longctx.PUBLIC}})
TASKS.update({'repo2': {'spec': repo2.SPEC, 'code': repo2.SHIM, 'public': repo2.PUBLIC}})
TASKS.update({'perf': {'spec': perf.SPEC, 'code': perf.FILES['solution.py'],
                       'public': perf.FILES['test_public.py']}})
TASKS.update({'longctx2': {'spec': longctx2.SPEC, 'code': longctx2.SHIM, 'public': longctx2.PUBLIC}})
# Extra workspace files the runner must write for a task, beyond README/solution/test_public.
NEW_TASK_FILES = {'repo': {'varint.py': repo.FILES['varint.py'], 'store.py': repo.FILES['store.py']},
                  'longctx': {'legacy.py': longctx.module_source(True)},
                  'repo2': {'codec.py': repo2.FILES['codec.py'], 'frames.py': repo2.FILES['frames.py'],
                            'registry.py': repo2.FILES['registry.py']},
                  'longctx2': {'legacy.py': longctx2.module_source(True)}}
REPO_CASES = len(repo.cases('repo'))
LONGCTX_CASES = len(longctx.cases('longctx'))
REPO2_CASES = len(repo2.cases('repo2'))
PERF_CASES = len(perf.cases('perf'))
LONGCTX2_CASES = len(longctx2.cases('longctx2'))
FUNCTIONS = dict(frozen.FUNCTIONS)
FUNCTIONS.update({'ledger2': 'reconcile'})
REFERENCES = dict(frozen.REFERENCES)
REFERENCES.update({'ledger2': frozen.reference_ledger})
same_value = frozen.same_value


def cases(kind):
    if kind == 'ledger2':
        return battery.cases(kind)
    if kind == 'repo':
        return list(range(REPO_CASES))
    if kind == 'longctx':
        return list(range(LONGCTX_CASES))
    if kind == 'repo2':
        return list(range(REPO2_CASES))
    if kind == 'perf':
        return list(range(PERF_CASES))
    if kind == 'longctx2':
        return list(range(LONGCTX2_CASES))
    return frozen.cases(kind)


def evaluate(kind, path):
    if kind == 'ledger2':
        return battery.evaluate(kind, path)
    if kind == 'repo':
        # The relay always scores `workspace/solution.py`; the task lives in that directory.
        target = Path(path)
        return repo.evaluate_repo(target if target.is_dir() else target.parent)
    if kind == 'longctx':
        target = Path(path)
        return longctx.evaluate_longctx(target if target.is_dir() else target.parent)
    if kind == 'repo2':
        target = Path(path)
        return repo2.evaluate_repo2(target if target.is_dir() else target.parent)
    if kind == 'perf':
        target = Path(path)
        return perf.evaluate_perf(target if target.is_dir() else target.parent)
    if kind == 'longctx2':
        target = Path(path)
        return longctx2.evaluate_longctx2(target if target.is_dir() else target.parent)
    return frozen.evaluate(kind, path)


if __name__ == '__main__':
    result = evaluate(sys.argv[1], Path(sys.argv[2]))
    print(json.dumps(result))
    sys.exit(0 if result['passed'] == result['total'] else 1)
'''


def build(model='qwen36-35b-a3b', root=None):
    template = BASE / MODEL_TEMPLATES[model]
    root = root or (BASE / ROOT_FOR[model])
    if root.exists():
        raise SystemExit('%s already exists' % root)
    return _build_into(template, root, model)


def _build_into(TEMPLATE, ROOT, model):
    """Build one new-task root from a template, with every declared change in one place."""
    (ROOT / 'evidence').mkdir(parents=True)
    (ROOT / 'source').mkdir()
    (ROOT / 'models').mkdir()
    shutil.copyfile(TEMPLATE / 'manifest.json', ROOT / 'manifest.json')
    shutil.copyfile(TEMPLATE / 'protocol.json', ROOT / 'protocol.json')
    # 2026-10-09 DECLARED GATE CHANGE, carried into the record: the 6 GiB worker-private cap is
    # removed, so the inherited protocol field must not still claim it.
    _protocol = json.loads((ROOT / 'protocol.json').read_text(encoding='utf-8'))
    if _protocol.get('decision_worker_private_cap_gib') == 6:
        _protocol['decision_worker_private_cap_gib'] = None
        _protocol['worker_private_cap_note'] = (
            'removed 2026-10-09 on Kevin\'s instruction (WORKER_PRIVATE_CAP_GIB = None in '
            'local-decisions-20260925-v1/run.py); the eligibility gate and the 3/2/0.5 GiB runtime '
            'floors are unchanged')
        (ROOT / 'protocol.json').write_text(json.dumps(_protocol, indent=1), encoding='utf-8')
    text = (TEMPLATE / 'run.py').read_text(encoding='utf-8')

    # 1. the root's source directory must win the `staged_tasks_20260922` name (the harness puts its own
    # benchmarks directory on sys.path, so the name alone resolves to the wrong module).
    anchor = "sys.path.insert(0,str(SOURCE))"
    assert text.count(anchor) == 1, 'sys.path anchor not unique'
    text = text.replace(anchor, anchor + "\n"
        "# 2026-10-08 DECLARED: shadow the frozen task-module name with a superset that adds the new\n"
        "# tasks, so both the runner's import and the relay's score_artifact subprocess see them.\n"
        "sys.path.insert(0,str(ROOT/'source'))\n"
        "# 2026-10-09: bind the task-module NAME eagerly to the root's superset. The harness resolves\n"
        "# its scorer with a name-based import (mimo-harness-20260925-v1/run.py:324), and sys.modules\n"
        "# caches whichever copy arrives first - that race left two cells unscored in the gpt-oss r2/r3\n"
        "# roots while r1 and every other root scored the same task fine.\n"
        "import staged_tasks_20260922 as _superset\n"
        "assert hasattr(_superset,'NEW_TASK_FILES'), 'the root superset did not win the module name: '+_superset.__file__")

    # 2. raise the reply cap and session quota (precedent truncation-20261008-v*): the templates carry
    # Budget(quota=24000, cap=12288), small enough to cut a long thinking block before the model acts.
    budget_old = " class Budget24000(fresh.Budget):"
    if budget_old in text:
        quota = BUDGET_QUOTA.get(model, 48000)
        text = text.replace(budget_old, " class BudgetRaised(fresh.Budget):")
        text = text.replace("  def __init__(self,quota=24000,cap=12288):super().__init__(quota=24000,cap=cap)",
                            "  def __init__(self,quota=%d,cap=32768):super().__init__(quota=%d,cap=cap)" % (quota, quota))
        text = text.replace("fresh.Budget=Budget24000", "fresh.Budget=BudgetRaised")

    # 3. the harness's execute() loop ends a session whenever `budget.failure` is set, and the relay sets
    # `quota_unknown` when a response carries no usage (Swift and the Strata engine both do that
    # intermittently). Count the gap instead; every other failure value still stops the session.
    budget_anchor = " fresh.Budget=BudgetRaised"
    if budget_anchor in text:
        text = text.replace(budget_anchor, budget_anchor + "\n"
            " class _BudgetUsageTolerant(BudgetRaised):\n"
            "  def account(self,usage,allowance):\n"
            "   super().account(usage,allowance)\n"
            "   if self.failure=='quota_unknown':\n"
            "    self.usage_gap=getattr(self,'usage_gap',0)+1\n"
            "    self.failure=None\n"
            " fresh.Budget=_BudgetUsageTolerant")

    # 4. per-task prompt and wall: `longctx` targets legacy.py (not solution.py) and needs reading time;
    # `repo` hit the 720 s wall twice in the first six-task runs.
    const_anchor = "SOURCE=ROOT.parent/'completion-20260923-v1/source'"
    assert text.count(const_anchor) == 1, 'constant anchor not unique'
    text = text.replace(const_anchor, const_anchor + '''
LONGCTX_PROMPT=%r
LONGCTX_WALL=1800
# 2026-10-08 DECLARED per-task wall: `repo` hit 720 s twice (Kolibri 44 turns/60 tool calls - artifact
# already complete - and MiniCPM, which thrashed). Every other task keeps the 720 s wall.
TASK_WALL={'repo':1800,'longctx':1800}''' % LONGCTX_PROMPT)

    # 5. the task loop: six tasks by default so sweeps stay comparable with the 2026-10-08 family;
    # LAB_EXTENDED_TASKS=1 adds the three batteries authored that night.
    loop = "for task in ['events','ledger','paths']"
    assert text.count(loop) == 1
    import os as _os
    tasks = ['events','ledger','paths','ledger2','repo','longctx']
    if _os.environ.get('LAB_EXTENDED_TASKS') == '1':
        tasks += ['repo2','perf','longctx2']
    # LAB_TASKS=ledger2,repo builds a root whose loop is exactly that subset - for targeted repeats
    # (variance on one battery) without paying for a full sweep. Unknown names are refused, not dropped.
    if _os.environ.get('LAB_TASKS'):
        wanted = [name.strip() for name in _os.environ['LAB_TASKS'].split(',') if name.strip()]
        unknown = [name for name in wanted if name not in tasks]
        assert not unknown, 'LAB_TASKS names not built into this root: %r' % (unknown,)
        tasks = wanted
    text = text.replace(loop, "for task in %r" % (tasks,))

    # 6. the runner's sweep guard: quota_unknown is an engine reporting gap, not a task outcome.
    fatal = "if result['quota_failure'] not in (None,'quota_exhausted'):raise RuntimeError('Quota accounting stop: '+str(result['quota_failure']))"
    tolerant = "if result['quota_failure'] not in (None,'quota_exhausted','quota_unknown'):raise RuntimeError('Quota accounting stop: '+str(result['quota_failure']))"
    if fatal in text:
        text = text.replace(fatal, tolerant)

    # 7. load the superset by path (see 1) and write the new tasks' extra workspace files.
    import_line = "from staged_tasks_20260922 import TASKS"
    assert text.count(import_line) == 1
    text = text.replace(import_line,
                        "_taskmod=module('newtask_tasks',ROOT/'source'/'staged_tasks_20260922.py')\n"
                        "  TASKS=_taskmod.TASKS; NEW_TASK_FILES=_taskmod.NEW_TASK_FILES")
    files_line = ("    for filename,key in [('README.md','spec'),('solution.py','code'),('test_public.py','public')]:"
                  " (work/filename).write_text(TASKS[task][key],encoding='ascii')")
    assert text.count(files_line) == 1, 'workspace file loop not found'
    text = text.replace(files_line, files_line + "\n    for extra_name,extra_text in NEW_TASK_FILES.get(task,{}).items():"
                                                  " (work/extra_name).write_text(extra_text,encoding='utf-8')")

    # 8. the execute call: per-task prompt and wall.
    call_old = "    result=lab.execute(session,'omp1831',folder,fresh.PROMPTS['one-shot'],wall=720,task=task)"
    call_new = ("    result=lab.execute(session,'omp1831',folder,\n"
                "     (fresh.PROMPTS['one-shot'] if task!='longctx' else LONGCTX_PROMPT),\n"
                "     wall=TASK_WALL.get(task,720),task=task)")
    assert text.count(call_old) == 1, 'execute call not found in the template'
    text = text.replace(call_old, call_new)

    # 9. provisioning (verified in provision-20261008-v1): served context 32,768 -> 131,072, the host
    # descriptor's contextWindow/maxTokens -> 131,072/32,768, and llama.cpp's thinking budget. Skipped
    # for an exempt model - both the engine flags AND the host window, or the host would believe it has
    # a window the server does not serve.
    # LAB_CONTEXT=<tokens> is an operator declaration for one build: it sets the served context and the
    # host window, and it deliberately overrides PROVISION_EXEMPT (the exemption records that 131,072 does
    # not fit a given model's card, not that its runtime rejects the flags - Swift's Prism fork accepted
    # them and died on VRAM). The root's README records the value.
    override = _os.environ.get('LAB_CONTEXT')
    server_context = override or SERVER_CONTEXT
    host_context = int(override) if override else HOST_CONTEXT
    exempt = model in PROVISION_EXEMPT and not override
    ctx = ("SERVER_CONTEXT=%r\nHOST_CONTEXT=%d\nHOST_MAX_TOKENS=%d\nREASONING_BUDGET=%r\nBUDGET_MESSAGE=%r"
           % (server_context, host_context, HOST_MAX_TOKENS, REASONING_BUDGET, BUDGET_MESSAGE))
    src_anchor = "SOURCE=ROOT.parent/'completion-20260923-v1/source'"
    assert text.count(src_anchor) == 1
    text = text.replace(src_anchor, ctx + "\n" + src_anchor)
    if exempt:
        text = text.replace("sys.path.insert(0,str(ROOT/'source'))",
                            "sys.path.insert(0,str(ROOT/'source'))\n"
                            "# provisioned? NO - %s" % PROVISION_EXEMPT[model].replace("'", ""))
    else:
        launch_anchor = "  def launch(self,args,**kwargs):\n   args=list(args)\n   if str(args[0])==str(lab.RUNTIME):"
        assert text.count(launch_anchor) == 1, 'launch anchor not unique'
        text = text.replace(launch_anchor, launch_anchor + "\n"
            "    if '-c' in args:\n     args[args.index('-c')+1]=SERVER_CONTEXT\n"
            "    if '--reasoning-format' in args:\n     at=args.index('--reasoning-format')+2\n"
            "     args[at:at]=['--reasoning-budget',REASONING_BUDGET,'--reasoning-budget-message',BUDGET_MESSAGE]")
        relay_anchor = " lab.base=fresh"
        assert text.count(relay_anchor) == 1, 'relay anchor not unique'
        text = text.replace(relay_anchor, relay_anchor + "\n"
            " _hcfg=lab.configuration\n"
            " def _configuration_with_bigger_window(folder,harness,port):\n"
            "  env=_hcfg(folder,harness,port)\n"
            "  path=folder/'config'/'models.yml'\n"
            "  if path.exists():\n"
            "   data=json.loads(path.read_text(encoding='utf-8'))\n"
            "   for provider in (data.get('providers') or {}).values():\n"
            "    for entry in provider.get('models') or []:\n"
            "     entry['contextWindow']=HOST_CONTEXT\n"
            "     entry['maxTokens']=HOST_MAX_TOKENS\n"
            "   path.write_text(json.dumps(data,indent=1),encoding='utf-8')\n"
            "  return env\n"
            " lab.configuration=_configuration_with_bigger_window")

    (ROOT / 'run.py').write_text(text, encoding='utf-8')
    (ROOT / 'source' / 'staged_tasks_20260922.py').write_text(SUPERSET, encoding='utf-8')
    for battery in ('new_tasks_20261008.py', 'new_tasks_repo.py', 'new_tasks_longctx.py',
                    'new_tasks_repo2.py', 'new_tasks_perf.py', 'new_tasks_longctx2.py'):
        shutil.copyfile(DRIVER / battery, ROOT / 'source' / battery)
    for extra in SIBLINGS:
        shutil.copyfile(TEMPLATE / 'source' / extra, ROOT / 'source' / extra)
    for model_dir in (TEMPLATE / 'models').iterdir():
        target = ROOT / 'models' / model_dir.name
        target.mkdir(parents=True, exist_ok=True)
        for weights in model_dir.iterdir():
            os.link(weights, target / weights.name)
    # 2026-10-09: the roots copy the template's manifest, which pins 120 files by digest - including
    # the monitor module. A declared change to any pinned file makes every new root refuse to run
    # (verify(): "AssertionError: [...]"), which is the freeze working as designed. So the manifest is
    # re-pinned here, with the old -> new digests recorded beside it as evidence, rather than the check
    # being bypassed.
    import importlib.util as _ilu
    _spec = _ilu.spec_from_file_location('mon_for_pins', str(BASE / 'local-decisions-20260925-v1' / 'run.py'))
    _mon = _ilu.module_from_spec(_spec)
    _spec.loader.exec_module(_mon)
    _manifest_path = ROOT / 'manifest.json'
    _manifest = json.loads(_manifest_path.read_text(encoding='utf-8'))
    _changes = []
    for _path, _old in list(_manifest.items()):
        _file = Path(_path)
        if not _file.exists():
            continue
        _new = _mon.digest(_file)
        if _new != _old:
            _manifest[_path] = _new
            _changes.append({'path': _path, 'old': _old, 'new': _new})
    if _changes:
        _manifest_path.write_text(json.dumps(_manifest, indent=1), encoding='ascii')
        (ROOT / 'evidence' / 'pin-change.json').write_text(json.dumps(
            {'reason': 'declared gate change 2026-10-09: 6 GiB worker-private cap removed',
             'repinned': _changes}, indent=1), encoding='ascii')

    (ROOT / 'README.md').write_text(
        '# %s: the frozen three tasks plus the new ones\n\n'
        'Template `%s`, model `%s`. Task loop: %s.\n'
        'Declared: relay Budget demotes quota_unknown to a counted usage gap; reply cap %s/%s;\n'
        'provisioning %s.\n'
        'Scoring runs through a superset module that shadows the frozen task-module name.\n' % (
            ROOT.name, TEMPLATE.name, model, ', '.join(tasks),
            BUDGET_QUOTA.get(model, 48000), 32768,
            ('EXEMPT - %s' % PROVISION_EXEMPT[model]) if exempt
            else 'context %s, host window %s/%s, thinking budget %s' % (
                server_context, host_context, HOST_MAX_TOKENS, REASONING_BUDGET))
        , encoding='ascii')
    return ROOT


def check():
    """Offline: the superset CLI must score a known artifact identically to the battery module."""
    sys.path.insert(0, str(DRIVER))
    import new_tasks_20261008 as battery
    artifact = BASE / 'candidates-20261007-v26-1' / 'qwen36-35b-a3b-ledger' / 'trial' / 'final-artifact.py'
    direct = battery.evaluate('ledger2', artifact)
    process = subprocess.run([sys.executable, str(ROOT / 'source' / 'staged_tasks_20260922.py'),
                              'ledger2', str(artifact)], cwd=str(ROOT / 'source'),
                             capture_output=True, text=True, timeout=300)
    through_superset = json.loads(process.stdout.strip().splitlines()[-1])
    frozen = subprocess.run([sys.executable, str(ROOT / 'source' / 'staged_tasks_20260922.py'),
                             'ledger', str(artifact)], cwd=str(ROOT / 'source'),
                            capture_output=True, text=True, timeout=300)
    frozen_result = json.loads(frozen.stdout.strip().splitlines()[-1])
    print(json.dumps({'artifact': str(artifact), 'direct': [direct['passed'], direct['total']],
                      'superset': [through_superset['passed'], through_superset['total']],
                      'superset_frozen_ledger': [frozen_result['passed'], frozen_result['total']],
                      'match': [c for c in direct['checks']] == [c for c in through_superset['checks']]}))
    return 0


def main():
    if '--check' in sys.argv:
        return check()
    argv = list(sys.argv[1:])
    # `--root NAME` builds and runs this invocation under an explicit root, so a model can have more
    # than one root on disk (an extended-loop smoke, an n=3 repeat) without touching a frozen one.
    forced_root = None
    if '--root' in argv:
        i = argv.index('--root'); forced_root = argv[i + 1]; del argv[i:i + 2]
    names = argv or ['qwen36-35b-a3b']
    assert not (forced_root and len(names) > 1), '--root applies to exactly one model'
    # accumulate: tonight's batches run as separate invocations, so never clobber the record
    record_path = DRIVER / 'newtask-run.json'
    out = json.loads(record_path.read_text()) if record_path.exists() else {}
    for name in names:
        root_name = forced_root or ROOT_FOR.get(name)
        if not root_name or not (BASE / root_name).exists():
            build(name, BASE / root_name if root_name else None)
        root = BASE / root_name
        began = time.monotonic()
        with (root / 'evidence' / (name + '-run.log')).open('w', encoding='utf8') as handle:
            proc = subprocess.run([sys.executable, str(root / 'run.py'), 'coding', name], cwd=str(root),
                                  stdout=handle, stderr=subprocess.STDOUT, timeout=14400)
        entry = {'root': root.name, 'model': name, 'returncode': proc.returncode,
                 'wall_seconds': round(time.monotonic() - began, 1)}
        evidence = root / 'evidence' / (name + '-coding.json')
        if evidence.exists():
            data = json.loads(evidence.read_text())
            entry['error'] = data.get('error')
            entry['tasks'] = []
            for task in data.get('tasks', []):
                record = {'task': task.get('task'), 'passed': (task.get('evaluation') or {}).get('passed'),
                          'total': (task.get('evaluation') or {}).get('total'),
                          'clean': task.get('clean_finish'), 'correct': task.get('correct'),
                          'seconds': round(task.get('seconds') or 0, 1),
                          'tokens': task.get('completion_tokens')}
                # 2026-10-09: a scorer that exits abnormally records passed=0/total=N, which reads
                # like a model failure. Surface the harness's own flag so an unscored task is legible.
                if (task.get('evaluation') or {}).get('abnormal_evaluator_exit'):
                    record['unscored'] = True
                if task.get('task') == 'ledger2':
                    checks = (task.get('evaluation') or {}).get('checks') or []
                    sys.path.insert(0, str(DRIVER))
                    import new_tasks_20261008 as battery
                    labels = battery.case_labels()
                    record['failing_traps'] = [labels.get(c['case'], str(c['case'])) for c in checks if not c['pass']]
                entry['tasks'].append(record)
        # keyed by ROOT, not by model: a repeat for the same model must not overwrite the earlier run
        # ranking metric + declared context travel with every run (see RANKED_TASKS above)
        ranked = [t for t in entry.get('tasks') or [] if t['task'] in RANKED_TASKS]
        if ranked:
            entry['ranked_passed'] = sum(t['passed'] for t in ranked)
            entry['ranked_total'] = sum(t['total'] for t in ranked)
            entry['ranked_tasks'] = list(RANKED_TASKS)
        # the context that actually served the run, and how it was declared
        if os.environ.get('LAB_CONTEXT'):
            entry['context'] = int(os.environ['LAB_CONTEXT'])
            entry['provisioning'] = 'provisioned@%s (operator override)' % os.environ['LAB_CONTEXT']
        elif name in PROVISION_EXEMPT:
            entry['context'] = 32768
            entry['provisioning'] = 'exempt (template window 32768)'
        else:
            entry['context'] = int(SERVER_CONTEXT)
            entry['provisioning'] = 'provisioned'
        out[root.name] = entry
        record_path.write_text(json.dumps(out, indent=2), encoding='ascii')
        print(json.dumps(entry), flush=True)
    return 0


if __name__ == '__main__':
    if '--check' not in sys.argv and not ROOT.exists():
        build()
    sys.exit(main())
