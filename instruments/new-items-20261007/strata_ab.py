"""Strata 0.1.41 A/B set: engine upgrade, the expert-cache hint, and the route-resident switch.

Measured question: v0.1.41's headline is "Windows, model bigger than RAM: prompts about twice as
fast (#1323)" and our suite is 43.6 tokens read per token written, so prompt throughput is the wall.
The ledger is already at 70/70, so scores will be noise - the metrics that move are the engine's own
rates, which its log reports per session:

  prompt tok/s   from "reading the prompt: N of M tokens, T s so far"
  decode tok/s   from "done: N tokens in T s (X tok/s) (stop, ...)"
  cache hit      from the same "done:" line, "expert cache 48.8% hit"

Arms, three fresh roots each, all otherwise identical to the 64k/12 GiB declaration
(context 65536, reasoning_budget_tokens 6144, resident budget 12 GiB, reserve 2000 MiB):
  A  engine 0.1.41, nothing else changed
  B  0.1.41 + `--expert-cache 1500`   (release note: 15-27% on short prompts on RTX 5070 + Q2_0,
                                       where the automatic cache is bigger than useful)
  C  0.1.41 + `STRATA_ROUTE_RESIDENT=1` (release note: +4.1% decode on RTX 5070 with Q2_0, 6/6)

Baseline: the 0.1.40.3 runs at the same 64k declaration (strata-ctx-20261008-v42/v43 and v1..v3),
whose logs are read with the same extractor.

Usage: python strata_ab.py [baseline] [A] [B] [C] [--n 3]
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
TEMPLATE = BASE / 'strata-ctx-20261008-v42'          # 64k context + budget + tolerant Budget
ENGINE_OLD = "STRATA = BASE / 'staged-strata-20261007' / 'engine-src-v0.1.40.3'"
ENGINE_NEW = "STRATA = BASE / 'staged-strata-20261008' / 'engine-src-v0.1.41'"
STAGE_PREFIX = 'strata-ab-20261008-v'
ARMS = {'A': {}, 'B': {'cache': '1500'}, 'C': {'env': {'STRATA_ROUTE_RESIDENT': '1'}}}
BASELINE_ROOTS = ['strata-ctx-20261008-v42', 'strata-ctx-20261008-v43',
                  'strata-ctx-20261008-v1', 'strata-ctx-20261008-v2', 'strata-ctx-20261008-v3']

PROMPT_RE = re.compile(r'reading the prompt: ([\d,]+) of ([\d,]+) tokens, ([\d.]+) s')
DONE_RE = re.compile(r'done: ([\d,]+) tokens in ([\d.]+) s \(([\d.]+) tok/s\)(?:.*?expert cache ([\d.]+)% hit)?')


def metrics(root):
    """Rates from one session's engine log + the session result, if present."""
    log = root / 'oms-ledger' / 'strata-server.log'
    out = {'root': root.name}
    if log.exists():
        text = log.read_text(encoding='utf-8', errors='replace')
        # Per-request summaries the engine prints itself: tokens generated, elapsed, rate, cache hit.
        # These are the agent-relevant numbers (the prompt read is inside the elapsed time).
        done = DONE_RE.findall(text)
        if done:
            rates = sorted(float(d[2]) for d in done)
            out['requests'] = len(done)
            out['gen_tokens'] = sum(int(d[0].replace(',', '')) for d in done)
            out['done_seconds'] = round(sum(float(d[1]) for d in done), 1)
            out['decode_tok_s_median'] = round(rates[len(rates) // 2], 1)
            out['decode_tok_s_min'] = round(rates[0], 1)
            out['decode_tok_s_max'] = round(rates[-1], 1)
        hits = [float(h) for h in re.findall(r'expert cache ([\d.]+)% hit', text)]
        if hits:
            out['cache_hit_pct_first'] = hits[0]
            out['cache_hit_pct_last'] = hits[-1]
        # Prompt reading: the progress lines are sparse and per-request, and the total includes the
        # engine's cache reuse, so only the FIRST group (the cold system prompt) is a clean read rate.
        groups, current = [], None
        for m in PROMPT_RE.finditer(text):
            now, total, secs = (int(m.group(1).replace(',', '')), int(m.group(2).replace(',', '')), float(m.group(3)))
            if current and (now < current[-1][0] or total != current[-1][1]):
                groups.append(current); current = None
            if current is None:
                current = []
            current.append((now, total, secs))
        if current:
            groups.append(current)
        if groups:
            _now, total, secs = max(groups[0], key=lambda x: x[2])
            if secs > 0:
                out['cold_prompt_tokens'] = total
                out['cold_prompt_seconds'] = secs
                out['cold_prompt_tok_s'] = round(total / secs, 1)
            out['prompt_progress_groups'] = len(groups)
    result = root / 'runs' / 'oms-ledger' / 'result.json'
    if result.exists():
        data = json.loads(result.read_text(encoding='utf-8'))
        evaluation = data.get('evaluation') or {}
        out.update({'passed': evaluation.get('passed'), 'total': evaluation.get('total'),
                    'seconds': round(data.get('seconds') or 0, 1), 'tokens': data.get('completion_tokens'),
                    'clean': data.get('clean_finish'), 'exit': data.get('exit_code')})
    config = root / 'runs' / 'oms-ledger' / 'status.json'
    if config.exists():
        data = json.loads(config.read_text(encoding='utf-8'))
        command = data.get('command') or []
        if command:
            flat = [str(a) for a in command]
            out['max_context'] = flat[flat.index('--max-context') + 1] if '--max-context' in flat else None
            out['expert_cache'] = flat[flat.index('--expert-cache') + 1] if '--expert-cache' in flat else 'auto'
    return out


def build(arm, index):
    root = BASE / ('%s%s%d' % (STAGE_PREFIX, arm, index))
    if root.exists():
        print('skip existing', root.name, flush=True)
        return None
    shutil.copytree(TEMPLATE, root, ignore=shutil.ignore_patterns('runs', 'oms-*', 'RUNNING.lock', 'STOP', '*.log'))
    (root / 'evidence').mkdir(exist_ok=True)
    text = (root / 'run.py').read_text(encoding='utf-8')
    # 1. point the runner at the 0.1.41 install (the pinned 0.1.40.3 tree is untouched)
    assert text.count(ENGINE_OLD) == 1, 'engine path line not unique'
    text = text.replace(ENGINE_OLD, ENGINE_NEW)
    spec = ARMS[arm]
    # 2. Expert cache, declared EXPLICITLY for every arm. The engine config file lives in the engine
    # install and is SHARED by every root that uses it, so an arm that does not state its value
    # inherits whatever the previous arm wrote - which contaminated the first arm-C batch (all six
    # B/C runs showed an identical cold prompt because C inherited B's 1500).
    if 'cache' not in spec:
        anchor = "    cleaned.extend(['--resident-budget-gib'"
        assert text.count(anchor) == 1, 'configure anchor not unique'
        text = text.replace(anchor,
            "    while '--expert-cache' in cleaned:\n"
            "        _i = cleaned.index('--expert-cache')\n"
            "        del cleaned[_i:_i + 2]\n" + anchor)
    # 3. arm B: the release's own card-specific hint
    if 'cache' in spec:
        anchor = "    cleaned.extend(['--resident-budget-gib'"
        assert text.count(anchor) == 1, 'configure anchor not unique'
        text = text.replace(anchor,
            "    while '--expert-cache' in cleaned:\n"
            "        _i = cleaned.index('--expert-cache')\n"
            "        del cleaned[_i:_i + 2]\n"
            "    cleaned.extend(['--expert-cache', %r])\n" % spec['cache'] + anchor)
    # 3. arm C: the route-resident env switch
    for key, value in (spec.get('env') or {}).items():
        marker = "ENGINE_ENV = {"
        assert text.count(marker) == 1
        text = text.replace(marker, marker + "'%s': '%s', " % (key, value))
    (root / 'run.py').write_text(text, encoding='utf-8')
    (root / 'README.md').write_text(
        '# %s: Strata 0.1.41, arm %s\n\nTemplate `strata-ctx-20261008-v42` (context 65536, thinking budget 6144,\n'
        '12 GiB resident, reserve 2000). Declared change: engine %s (was %s).%s\n'
        'Nothing else changes; the pinned 0.1.40.3 tree stays byte-identical.\n' % (
            root.name, arm, ENGINE_NEW, ENGINE_OLD,
            ('  Arm settings: %s' % json.dumps(spec)) if spec else ''),
        encoding='ascii')
    return root


def one(root):
    # Preflight: the config written by `configure` must show the arm's declared expert cache.
    began = time.monotonic()
    with (root / 'evidence' / 'run.log').open('w', encoding='utf8') as handle:
        subprocess.run([sys.executable, str(root / 'run.py'), 'configure'], cwd=str(root),
                       stdout=handle, stderr=subprocess.STDOUT, timeout=1800)
        subprocess.run([sys.executable, str(root / 'run.py'), 'screen', 'ledger'], cwd=str(root),
                       stdout=handle, stderr=subprocess.STDOUT, timeout=14400)
    entry = metrics(root)
    entry['wall_seconds'] = round(time.monotonic() - began, 1)
    return entry


def main():
    argv = [a for a in sys.argv[1:] if not a.startswith('--')]
    count = 3
    if '--n' in sys.argv:
        count = int(sys.argv[sys.argv.index('--n') + 1])
    arms = [a for a in argv if a in ARMS]
    out = {}
    if not argv or 'baseline' in argv:
        for name in BASELINE_ROOTS:
            root = BASE / name
            if root.exists():
                out['baseline:' + name] = metrics(root)
        (DRIVER / 'strata-ab.json').write_text(json.dumps(out, indent=2), encoding='ascii')
        print(json.dumps({k: v for k, v in out.items()}, indent=1)[:2000], flush=True)
    for arm in arms:
        for index in range(1, count + 1):
            root = build(arm, index)
            if root is None:
                continue
            entry = one(root)
            out['%s:%s' % (arm, root.name)] = entry
            (DRIVER / 'strata-ab.json').write_text(json.dumps(out, indent=2), encoding='ascii')
            print(json.dumps(entry), flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
