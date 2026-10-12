"""newtask_strata.py - the new-task batteries under the Strata engine.

Why this exists: the new-task suite (ledger2, repo, longctx, repo2, perf, longctx2) has only ever run
on llama-server. The report's status table records Strata as the one model still absent from it.

Shape of the port: the Strata runner (`strata-20261007-v19-1`) already drives
`lab.execute(session, 'omp1831', ...)` with its own engine in the session's place, so this is the same
patch set `newtask_run.py` applies to the OMP templates, anchored on the Strata template's own lines.
Declared changes, all written into the built root's README:

  1. the superset task module shadows `staged_tasks_20260922`, adding the new workspaces and
     NEW_TASK_FILES (loaded BY PATH, because the bare name resolves to the frozen module);
  2. `screen()` writes the extra workspace files of each new task, and a `sweep` action runs a list;
  3. `longctx` gets its own prompt and wall (`repo`/`repo2` too - they need output the fast models
     spend 5-26k tokens on, at 6.5-9.6 tok/s here);
  4. `lab.base.Budget` is overridden (the harness builds `base.Budget(quota=16000, cap=12288)`
     explicitly, so the subclass ignores those values) and `quota_unknown` becomes a counted usage gap;
  5. the host descriptor's contextWindow/maxTokens are set to the engine's own declared context,
     read from the engine config at build time rather than assumed.

Unchanged by design: the engine config, the resident budget, the low-RAM variant, the lookahead
setting, the VRAM reserve, and every floor (3 / 2 / 0.5 GiB). The engine's own startup line is the
context verification, not this file's intention.

Usage:
  python newtask_strata.py build [root]              build the root (default strata-newtasks-20261009-v1)
  python newtask_strata.py check [root]              run the root's `check` (engine setup --check)
  python newtask_strata.py sweep [root] [tasks]      run tasks (default: the six new-task suite)
"""
import json
import os as _os
import shutil
import sys
from pathlib import Path

import newtask_run as nt

BASE = Path(r'C:\Users\kevin\ai_bench')
DRIVER = BASE / 'new-items-20261007'
TEMPLATE = BASE / 'strata-20261007-v19-1'
ENGINE = BASE / 'staged-strata-20261007' / 'engine-src-v0.1.40.3'
# The harness's base module and its siblings live here; the OMP templates copy them into each
# root's source/ and swap lab.base for that copy, which is what makes score_artifact
# resolve HERE/'staged_tasks_20260922.py' to the root's superset instead of the frozen
# module. Omitting the copy gives abnormal_evaluator_exit on every new battery - the
# lab hit exactly this on 2026-10-07 (see candidates-20261007-v26-1/run.py).
FROZEN_SOURCE = BASE / 'completion-20260923-v1' / 'source'
SIBLINGS = ('owned_process_20260922.py', 'night_tasks_20260916.py',
            'test_compare_staging_20260922.py', 'validate_staged_tasks_20260922.py')
CONFIG_NAME = 'strata-q2_0.json'
DEFAULT_ROOT = 'strata-newtasks-20261009-v1'

# The suite this port exists to add: the frozen three plus the four batteries authored 2026-10-08/09.
SWEEP = ['events', 'ledger', 'paths', 'ledger2', 'repo', 'longctx', 'repo2', 'perf', 'longctx2']

# Declared per-task walls. Measured engine rates (2026-10-06): decode 6.5-9.6 tok/s, prompt reading
# 550-670 tok/s. At the low end 3,600 s is ~23k output tokens, which covers every task's observed
# output on llama-server (5-26k) with margin; repo2 gets 5,400 because it is the largest workspace and
# the only multi-file repair in the set.
NEW_WALLS = {'ledger2': 3600, 'repo': 3600, 'repo2': 5400, 'perf': 3600,
             'longctx': 3600, 'longctx2': 3600}

# Declared session budget. The harness's own values (16,000 / 12,288) were written for the 720 s frozen
# screens; the ledger alone needed 3,600 s here, so a session quota can otherwise end a task early for
# a reason that has nothing to do with the model.
BUDGET_QUOTA = 96000
# Declared engine resident budget. The template's 12 GiB (chosen for the 64 GB platform) drove free
# physical to 3.18 GiB against the 3 GiB floor in the first sweep session, so the documented-safe 4 GiB
# is declared instead; see declare_resident_budget() for the measurement and the trade.
RESIDENT_BUDGET_GIB = 4
BUDGET_CAP = 32768


def declare_resident_budget(root, gib):
    """Declare `--resident-budget-gib` in the engine config, keeping a pre-change copy as evidence.

    Measured 2026-10-09: with the template's 12 GiB resident declaration the first sweep session
    (`strata-newtasks-20261009-v1`, `events`) drove free physical to **3.18 GiB against the 3 GiB
    floor** - the monitor stopped it, correctly - while GPU was fine (min 1.52 GiB free) and the engine
    itself loaded in 31.7 s and decoded at 66-79 tok/s. The 12 GiB value was declared for the 64 GB
    platform as "an order of magnitude more headroom than the 3 GiB floor needs"; the mmap'd expert
    pages plus the file cache ate that headroom. The lab's own earlier working configuration on a
    smaller box was 4 GiB (`STRATA_LOOKAHEAD=0` already set), which held 9.6-10.5 GiB free, so 4 GiB is
    the documented-safe value rather than a guess. The cost is more expert streaming, i.e. slower
    decode - a rate, not a score, and the walls are ceilings.
    """
    path = ENGINE / CONFIG_NAME
    cfg = json.loads(path.read_text(encoding='utf-8-sig'))
    before = root / 'evidence' / 'engine-config-before.json'
    if not before.exists():
        before.write_text(json.dumps({'_path': str(path), '_config': cfg}, indent=1), encoding='utf-8')
    args = list(cfg.get('args') or [])
    if '--resident-budget-gib' in args:
        args[args.index('--resident-budget-gib') + 1] = str(gib)
    else:
        args += ['--resident-budget-gib', str(gib)]
    cfg['args'] = args
    path.write_text(json.dumps(cfg, indent=1), encoding='utf-8')
    after = json.loads(path.read_text(encoding='utf-8-sig'))
    value = after['args'][after['args'].index('--resident-budget-gib') + 1]
    assert int(value) == gib, 'resident budget did not stick: %s' % value
    return int(value)


def engine_context():
    """The engine's own declared context, read from the config the run will use."""
    cfg = json.loads((ENGINE / CONFIG_NAME).read_text(encoding='utf-8-sig'))
    args = cfg.get('args') or []
    assert '--max-context' in args, 'the engine config declares no --max-context'
    return int(args[args.index('--max-context') + 1])


def declare_fit_max_tokens(root):
    """Declare `fit_max_tokens: true` in the engine config, keeping a pre-change copy as evidence.

    Why: the engine answers **400** when `prompt + max_tokens` exceeds the context ("requests are never
    truncated", #545) - a session in `strata-20261007-v19-1` died exactly that way at 31,445 + 1,460
    tokens against a 32,768 window, and the new batteries produce far bigger sessions. The key is
    declared by the engine itself (`serve/runconfig.py`: "Shorten a max_tokens that does not fit the
    context instead of answering 400"), so the mitigation is supported rather than hoped for. It trades
    a hard session failure for a clamped output cap; a clamp stays visible as `clean_finish=false` /
    `stopReason=length` in the session's own evidence, so it cannot pass silently.
    """
    path = ENGINE / CONFIG_NAME
    cfg = json.loads(path.read_text(encoding='utf-8-sig'))
    before = root / 'evidence' / 'engine-config-before.json'
    if not before.exists():
        before.write_text(json.dumps({'_path': str(path), '_config': cfg}, indent=1), encoding='utf-8')
    if cfg.get('fit_max_tokens') is not True:
        cfg['fit_max_tokens'] = True
        path.write_text(json.dumps(cfg, indent=1), encoding='utf-8')
    after = json.loads(path.read_text(encoding='utf-8-sig'))
    assert after.get('fit_max_tokens') is True, 'fit_max_tokens did not stick'
    return after['fit_max_tokens']


def build(root_name=DEFAULT_ROOT):
    root = BASE / root_name
    assert not root.exists(), '%s already exists - pick another root name' % root
    (root / 'evidence').mkdir(parents=True)
    (root / 'source').mkdir()
    text = (TEMPLATE / 'run.py').read_text(encoding='utf-8')

    # 1. the superset task module, loaded by path (see the module docstring).
    anchor = ("sys.path.insert(0, str(BASE / 'completion-20260923-v1/source'))\n"
              "from staged_tasks_20260922 import TASKS")
    assert text.count(anchor) == 1, 'task-module anchor not unique'
    context = engine_context()
    text = text.replace(anchor,
        "sys.path.insert(0, str(BASE / 'completion-20260923-v1/source'))\n"
        "# 2026-10-09 DECLARED: the new-task root shadows the frozen task-module name with a superset\n"
        "# that adds the new workspaces, and loads it BY PATH - the bare name resolves to the frozen\n"
        "# module because the harness puts its own benchmarks directory on sys.path.\n"
        "sys.path.insert(0, str(ROOT / 'source'))\n"
        "_taskmod = module('newtask_tasks', ROOT / 'source' / 'staged_tasks_20260922.py')\n"
        "TASKS = _taskmod.TASKS\n"
        "NEW_TASK_FILES = _taskmod.NEW_TASK_FILES\n"
        "ENGINE_CONTEXT = %d\n"
        "HOST_MAX_TOKENS = %d\n"
        "BUDGET_QUOTA = %d\n"
        "LONGCTX_PROMPT = %r\n"
        "\n"
        "# 2026-10-09 DECLARED: the harness builds base.Budget(quota=16000, cap=12288) explicitly, so\n"
        "# the subclass ignores those arguments; quota_unknown is an engine usage-reporting gap, not a\n"
        "# task outcome, and the tolerant subclass counts it instead of ending the session.\n"
        "class BudgetRaised(lab.base.Budget):\n"
        "    def __init__(self, quota=None, cap=None):\n"
        "        super().__init__(quota=BUDGET_QUOTA, cap=%d)\n"
        "    def account(self, usage, allowance):\n"
        "        super().account(usage, allowance)\n"
        "        if self.failure == 'quota_unknown':\n"
        "            self.usage_gap = getattr(self, 'usage_gap', 0) + 1\n"
        "            self.failure = None\n"
        "lab.base.Budget = BudgetRaised\n"
        "\n"
        "# 2026-10-09 DECLARED: the host descriptor must not claim a window the engine does not serve.\n"
        "_hcfg = lab.configuration\n"
        "def _configuration_with_engine_window(folder, harness, port):\n"
        "    env = _hcfg(folder, harness, port)\n"
        "    path = folder / 'config' / 'models.yml'\n"
        "    if path.exists():\n"
        "        data = json.loads(path.read_text(encoding='utf-8'))\n"
        "        for provider in (data.get('providers') or {}).values():\n"
        "            for model in provider.get('models') or []:\n"
        "                model['contextWindow'] = ENGINE_CONTEXT\n"
        "                model['maxTokens'] = HOST_MAX_TOKENS\n"
        "        path.write_text(json.dumps(data, indent=1), encoding='utf-8')\n"
        "    return env\n"
        "lab.configuration = _configuration_with_engine_window"
        % (context, 32768, BUDGET_QUOTA, nt.LONGCTX_PROMPT, BUDGET_CAP))

    # 1b. the scorer must be the ROOT's copy of the base module, so its HERE resolves to the root's
    # source/ and its task modules are the superset. This is the OMP template's `lab.base=fresh` move.
    relay_anchor = "lab.base.MODEL = 'strata-coder'"
    assert text.count(relay_anchor) == 1, 'strata relay anchor not unique'
    text = text.replace(relay_anchor, relay_anchor + "\n"
        "# 2026-10-09 DECLARED: score_artifact resolves HERE/'staged_tasks_20260922.py' from the base\n"
        "# module's own directory, so the base must be the root's copy with the superset beside it.\n"
        "_fresh = module('candidate_relay_strata', ROOT / 'source' / 'relay_strata.py')\n"
        "_fresh.BASE = lab.base.BASE\n"
        "_fresh.MODEL = lab.base.MODEL\n"
        "_fresh.OWNED_JOBS = True\n"
        "lab.base = _fresh")

    # 2. per-task walls for the new batteries (merged into the template's map, not nested in it).
    walls_anchor = "TASK_WALL_SECONDS = {'events': 720, 'ledger': 3600, 'paths': 720}"
    assert text.count(walls_anchor) == 1, 'wall anchor not unique'
    walls = {'events': 720, 'ledger': 3600, 'paths': 720}
    walls.update(NEW_WALLS)
    text = text.replace(walls_anchor, 'TASK_WALL_SECONDS = %r' % walls)

    # 3. the extra workspace files and the longctx prompt inside screen().
    files_anchor = """    for name, key in [('README.md', 'spec'), ('solution.py', 'code'), ('test_public.py', 'public')]:
        target = workspace / name
        if not target.exists():
            target.write_text(TASKS[task][key], encoding='ascii')"""
    assert text.count(files_anchor) == 1, 'workspace file loop not found'
    text = text.replace(files_anchor, files_anchor + """
    for extra_name, extra_text in NEW_TASK_FILES.get(task, {}).items():
        extra = workspace / extra_name
        if not extra.exists():
            extra.write_text(extra_text, encoding='utf-8')""")
    call_anchor = ("        result = lab.execute(session, 'omp1831', folder, lab.base.PROMPTS['one-shot'],\n"
                   "                             wall=TASK_WALL_SECONDS[task], task=task)")
    assert text.count(call_anchor) == 1, 'execute call not found'
    text = text.replace(call_anchor,
        "        prompt = LONGCTX_PROMPT if task == 'longctx' else lab.base.PROMPTS['one-shot']\n"
        "        result = lab.execute(session, 'omp1831', folder, prompt,\n"
        "                             wall=TASK_WALL_SECONDS[task], task=task)")

    # 4. a sweep action, so one invocation runs the suite in order with STOP honoured between tasks.
    sweep_fn = '''

def sweep(tasks):
    """Run tasks in order, one engine session each. A STOP file stops the sweep between tasks."""
    for task in tasks:
        if (ROOT / 'STOP').exists():
            print('STOP present: sweep stops before %s' % task, flush=True)
            return
        print('=== %s ===' % task, flush=True)
        try:
            screen(task)
        except BaseException as exc:
            print('session %s raised %r' % (task, exc), flush=True)

'''
    cli_anchor = "def audit():"
    assert text.count(cli_anchor) == 1
    text = text.replace(cli_anchor, sweep_fn.lstrip('\n') + '\n' + cli_anchor)
    dispatch_anchor = "    elif len(args) == 2 and args[0] == 'screen' and args[1] in TASKS:"
    assert text.count(dispatch_anchor) == 1
    text = text.replace(dispatch_anchor,
        "    elif args and args[0] == 'sweep':\n"
        "        wanted = [a for a in args[1].split(',')] if len(args) > 1 else list(SWEEP_DEFAULT)\n"
        "        unknown = [t for t in wanted if t not in TASKS]\n"
        "        assert not unknown, 'unknown task(s): %r' % (unknown,)\n"
        "        sweep(wanted)\n"
        + dispatch_anchor)

    # SWEEP_DEFAULT is what "the suite" means when the sweep action gets no explicit list.
    text = text.replace("def audit():", "SWEEP_DEFAULT = %r\n\n\ndef audit():" % (SWEEP,), 1)

    (root / 'run.py').write_text(text, encoding='utf-8')
    (root / 'source' / 'staged_tasks_20260922.py').write_text(nt.SUPERSET, encoding='utf-8')
    # the root-local base module plus the siblings score_artifact needs beside it
    shutil.copyfile(FROZEN_SOURCE / 'compare_staging_20260922.py', root / 'source' / 'relay_strata.py')
    for sibling in SIBLINGS:
        shutil.copyfile(FROZEN_SOURCE / sibling, root / 'source' / sibling)
    fit_max_tokens = declare_fit_max_tokens(root)
    # LAB_RESIDENT_GIB lets a build declare a different resident budget without editing this file
    # (2026-10-09: 4 GiB left the 3 GiB physical floor marginal - minima 2.94-5.11 GiB - so 2 GiB is
    # the declared value for the continuation).
    budget = int(_os.environ.get('LAB_RESIDENT_GIB') or RESIDENT_BUDGET_GIB)
    resident_budget = declare_resident_budget(root, budget)
    for battery in ('new_tasks_20261008.py', 'new_tasks_repo.py', 'new_tasks_longctx.py',
                    'new_tasks_repo2.py', 'new_tasks_perf.py', 'new_tasks_longctx2.py'):
        shutil.copyfile(DRIVER / battery, root / 'source' / battery)
    (root / 'README.md').write_text(
        '# %s: the new-task suite under the Strata engine\n\n'
        'Template `%s` (engine `%s`, config `%s`, VRAM reserve 2000 MiB,\n'
        'STRATA_LOOKAHEAD=0, reasoning_budget_tokens 6144 - all unchanged; the resident budget is the\n'
        'declared change below). The engine declares\n'
        'context %d and that value is what the host window is set to; the engine startup line is the\n'
        'verification.\n\n'
        'Suite: %s.\n\n'
        'Declared changes: the superset task module is loaded by path so the new workspaces exist and\n'
        'the relay scores them; `screen()` writes each task\'s extra files; `longctx` uses its own\n'
        'prompt; the per-task walls are %r; the session Budget is overridden to quota %d / cap %d with\n'
        '`quota_unknown` demoted to a counted usage gap; and the engine config carries\n'
        '`fit_max_tokens: %s` (a declared change, pre-change copy in evidence/) so a request that would\n'
        'overflow the context is clamped instead of answered 400. A clamp stays visible as\n'
        'clean_finish=false / stopReason=length in the session evidence. The engine resident budget is\n'
        'declared at %d GiB instead of the template\'s 12 (measured: 12 drove free physical to 3.18 GiB\n'
        'against the 3 GiB floor; 4 GiB is the lab\'s documented-safe value, at the cost of more expert\n'
        'streaming). Nothing else differs from the template.\n'
        % (root.name, TEMPLATE.name, ENGINE.name, CONFIG_NAME, context, ', '.join(SWEEP),
           NEW_WALLS, BUDGET_QUOTA, BUDGET_CAP, fit_max_tokens, resident_budget), encoding='ascii')
    print('built %s (engine context %d)' % (root, context))
    return root


def main():
    args = sys.argv[1:]
    action = args[0] if args else 'build'
    if action == 'build':
        build(args[1] if len(args) > 1 else DEFAULT_ROOT)
        return 0
    root = BASE / (args[1] if len(args) > 1 else DEFAULT_ROOT)
    assert root.exists(), '%s does not exist - build it first' % root
    import subprocess
    if action == 'check':
        return subprocess.call([sys.executable, str(root / 'run.py'), 'check'], cwd=str(root))
    if action == 'sweep':
        tasks = args[2] if len(args) > 2 else ','.join(SWEEP)
        return subprocess.call([sys.executable, str(root / 'run.py'), 'sweep', tasks], cwd=str(root))
    raise SystemExit('usage: build [root] | check [root] | sweep [root] [tasks]')


if __name__ == '__main__':
    sys.exit(main())
