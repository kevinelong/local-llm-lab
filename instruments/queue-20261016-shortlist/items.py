"""items.py - one function per declared item in this root's queue.json.

Run through runner.py (which owns the gates, the STOP file, status.json and REPORT.md), or one item by
hand:  python items.py q1-strata-kv-residency

Conventions carried over from the 2026-10-11 queue: every item starts and stops its own engine through the
Engine context manager, exits 0 only on success, and writes result-<id>.json beside this file. Predictions
live in queue.json and the driver writes them into REPORT.md *before* the run.

The instruments are borrowed, not invented: knowledge_deep.py for the 93-item reasoning letters,
llama.cpp's own `timings` object for the rate, the Strata engine's log lines for its rates and hit rate,
and colibri-laya-20261011/laya_replay.py for the decision screen.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

BASE = Path(r'C:\Users\kevin\ai_bench')
ROOT = Path(__file__).resolve().parent
OVERNIGHT = BASE / 'overnight-20261011'
DEEP = BASE / 'new-items-20261007'
LAYA_REPLAY = BASE / 'colibri-laya-20261011' / 'laya_replay.py'
QWEN36_GGUF = BASE / 'staged-qwen36-20261007' / 'Qwen3.6-35B-A3B-Q4_K_M.gguf'
QWEN36_ALIAS = 'qwen3.6-35b-a3b'
B11480_SERVER = BASE / 'staged-llamacpp-b11480' / 'llama-server.exe'
B11461_SERVER = BASE / 'staged-27b-20261007' / 'llamacpp-b11461' / 'llama-server.exe'

sys.path.insert(0, str(OVERNIGHT))
import shared                                     # noqa: E402  the lab's Engine/gates/ports

# Keep this root's own logs (engine logs included) out of the other queue's log directory.
shared.LOGS = ROOT / 'logs'
shared.LOGS.mkdir(exist_ok=True)

RATE_PROMPT = ('Write a short Python function that returns the n-th Fibonacci number, then explain in two '
               'sentences why the naive version is slow.')


def log(name, message):
    line = '%s  %s' % (time.strftime('%F %T'), message)
    with (ROOT / 'logs' / (name + '.log')).open('a', encoding='utf-8') as handle:
        handle.write(line + '\n')
    print(line, flush=True)


def write_result(name, payload):
    path = ROOT / ('result-%s.json' % name)
    path.write_text(json.dumps(payload, indent=1), encoding='utf-8')
    log(name, 'wrote %s' % path.name)
    return path


def run(name, command, cwd=None, timeout=7200):
    log(name, 'run: %s' % ' '.join(str(c) for c in command))
    done = subprocess.run([str(c) for c in command], cwd=str(cwd) if cwd else None, capture_output=True,
                          text=True, timeout=timeout)
    tail = (done.stdout or '').strip().splitlines()[-8:]
    for line in tail:
        log(name, '  | ' + line)
    if done.returncode != 0:
        log(name, 'exit code %d' % done.returncode)
    return done.returncode


# ------------------------------------------------------------------ instruments

def rate_probe(url, model, max_tokens=160, timeout=900):
    """One chat request; return llama.cpp's own timings plus our wall clock.

    llama-server answers with a `timings` object (`prompt_per_second`, `predicted_per_second`), which is the
    engine's measurement rather than ours; the wall clock is kept beside it for the engines that omit it.
    """
    body = {'model': model, 'messages': [{'role': 'user', 'content': RATE_PROMPT}], 'temperature': 0,
            'seed': 20260929, 'stream': False, 'max_tokens': max_tokens}
    request = urllib.request.Request(url.rstrip('/') + '/v1/chat/completions',
                                     data=json.dumps(body).encode('utf-8'),
                                     headers={'Content-Type': 'application/json'})
    started = time.monotonic()
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.load(response)
    wall = time.monotonic() - started
    timings = payload.get('timings') or {}
    usage = payload.get('usage') or {}
    return {'wall_s': round(wall, 2), 'timings': timings, 'usage': usage,
            'predicted_per_second': timings.get('predicted_per_second'),
            'prompt_per_second': timings.get('prompt_per_second'),
            'completion_tokens': usage.get('completion_tokens')}


def reason_letters(name, url, model, label, limit=93):
    """The 93-item reasoning form: the letters are the correctness guard for any engine change."""
    code = run(name, [sys.executable, DEEP / 'knowledge_deep.py', '--url', url, '--model', model,
                      '--label', label, '--forms', 'reason', '--limit', str(limit), '--pool', 'shared',
                      '--seeds', '1', '--timeout', '300'], cwd=DEEP, timeout=6 * 3600)
    path = DEEP / ('knowledge-deep-result-%s.json' % label)
    letters = None
    if path.exists():
        forms = json.loads(path.read_text(encoding='utf-8')).get('forms', {})
        letters = (forms.get('reason') or {}).get('letter_correct')
    return code, letters, path


def engine_rate_lines(engine_name, patterns=('prefill', 'decode', 'tok/s', 'hit rate', 'experts')):
    """Whatever rate lines the engine itself logged, kept verbatim - not parsed into a number we invent."""
    path = shared.LOGS / ('engine-%s.log' % engine_name)
    if not path.exists():
        return []
    found = []
    for line in path.read_text(encoding='utf-8', errors='replace').splitlines():
        if any(p in line.lower() for p in patterns):
            found.append(line.strip())
    return found[-25:]


def llama_engine_b11480(name, cache_mib):
    """The declared Qwen3.6 launch, on the staged b11480 build, with one --moe-cache-mib rung."""
    engine = shared.llama_engine(name, [QWEN36_GGUF], extra=['--cpu-moe', '--load-mode', 'none',
                                                            '--moe-cache-mib', str(cache_mib)])
    engine.args[0] = str(B11480_SERVER)           # same declared flags, the one-build-newer binary
    return engine


# ------------------------------------------------------------------ items

def q1_strata_kv_residency(name='q1-strata-kv-residency'):
    """Does KV residency move the answers at fixed capacity, or only the rate?

    Arms: the config as we run it (base), and the same config plus --kv-resident 32768. --kv int8,
    --max-context 65536, --resident-budget-gib 2 and --expert-cache auto stay identical in both, so
    capacity is not the variable. The lead is issue #2342 (3080 10 GB): 756 -> 1,416 experts and
    628 -> 1,528 tok/s prefill with --kv-resident 32768.
    """
    base = json.loads(shared.STRATA_CONFIG.read_text(encoding='utf-8'))
    arms = {'base': base,
            'kv-resident-32768': dict(base, args=list(base['args']) + ['--kv-resident', '32768'])}
    out = {}
    for arm, config in arms.items():
        cfg_path = ROOT / ('strata-cfg-%s.json' % arm)
        cfg_path.write_text(json.dumps(config, indent=1), encoding='utf-8')
        engine_name = 'q1-strata-%s' % arm
        log(name, 'arm %s: config %s' % (arm, cfg_path.name))
        with shared.strata_engine(engine_name, cfg_path):
            probe = rate_probe('http://127.0.0.1:8080', 'strata-coder')
            code, letters, path = reason_letters(name, 'http://127.0.0.1:8080', 'strata-coder',
                                                 'q1-%s' % arm)
            out[arm] = {'probe': probe, 'letters_of_93': letters, 'reason_exit': code,
                        'result_file': str(path), 'engine_rate_lines': engine_rate_lines(engine_name)}
            log(name, 'arm %s: letters %s, wall %.1fs, engine says %s' % (
                arm, letters, probe['wall_s'], probe['timings'].get('predicted_per_second')))
    letters = {arm: out[arm]['letters_of_93'] for arm in arms}
    write_result(name, {'item': name, 'arms': out, 'letters': letters,
                        'letters_identical': len(set(letters.values())) == 1})
    return 0


def q2_moe_cache_ladder(name='q2-moe-cache-mib-ladder'):
    """Ladder --moe-cache-mib on the staged b11480 build, with the letters as the guard."""
    rungs = [0, 256, 512, 1024, 2048, 4096]
    out = {}
    for rung in rungs:
        engine_name = 'q2-moe-cache-%d' % rung
        with llama_engine_b11480(engine_name, rung):
            probe = rate_probe('http://127.0.0.1:11436', QWEN36_ALIAS)
            code, letters, path = reason_letters(name, 'http://127.0.0.1:11436', QWEN36_ALIAS,
                                                 'q2-cache-%d' % rung)
            out[str(rung)] = {'probe': probe, 'letters_of_93': letters, 'reason_exit': code,
                              'result_file': str(path),
                              'engine_rate_lines': engine_rate_lines(engine_name, ('moe', 'cache', 'n_expert'))}
            log(name, 'rung %s MiB: %.1f tok/s (engine), wall %.1fs, letters %s'
                % (rung, probe['predicted_per_second'] or -1, probe['wall_s'], letters))
    rates = {int(k): (v['probe']['predicted_per_second'] or 0) for k, v in out.items()}
    best = max(rates, key=lambda k: rates[k]) if rates else None
    write_result(name, {'item': name, 'rungs': out, 'rates': rates, 'best_rung_mib': best,
                        'monotonic': all(rates[a] <= rates[b] for a, b in zip(sorted(rates), sorted(rates)[1:])),
                        'letters_identical': len({v['letters_of_93'] for v in out.values()}) == 1})
    return 0


def q3_noise_floor(name='q3-noise-floor'):
    """Two identical control runs: the spread is the floor any timing claim must beat."""
    runs = []
    for repeat in (1, 2):
        engine_name = 'q3-control-%d' % repeat
        with llama_engine_b11480(engine_name, 0):
            probe = rate_probe('http://127.0.0.1:11436', QWEN36_ALIAS)
        runs.append(probe)
        log(name, 'control run %d: %.1f tok/s, wall %.1fs'
            % (repeat, probe['predicted_per_second'] or -1, probe['wall_s']))
    rates = [r['predicted_per_second'] or 0 for r in runs]
    walls = [r['wall_s'] for r in runs]
    spread = {'rate_tok_s': rates, 'rate_spread_pct': (abs(rates[0] - rates[1]) / max(rates) * 100) if max(rates) else None,
              'wall_s': walls, 'wall_spread_pct': abs(walls[0] - walls[1]) / max(walls) * 100}
    write_result(name, {'item': name, 'runs': runs, 'spread': spread})
    log(name, 'spread: %s' % json.dumps(spread))
    return 0


def q4_calibrated_profile(name='q4-calibrated-warm-cache'):
    """Warm with real text, SAVE the profile, then start from it - the path our 2026-10-11 test never asked for.

    That test warmed with prompts and then found expert-profile.bin byte-identical, i.e. the engine was never
    asked to learn one. The engine learns one through the *config keys* `expert_profile_save` and
    `expert_profile_save_every` (minutes; 0 means only at QUIT), which the server turns into
    `--expert-profile-save*` and which also do the header match that lets the next start adopt the profile.
    Two traps, both hit on the first attempt (2026-10-16): passing the flag as a raw arg works only if the
    engine saves some other way, and the default `every` is **ten minutes** - while Engine.__exit__ stops the
    engine with `taskkill /F`, so a profile that is only written at QUIT never appears. This item therefore
    uses the config keys, sets `every` to one minute, keeps the warm phase long enough to cross it, and
    **fails** if the profile is still absent instead of reporting a green run that tested nothing.
    """
    base = json.loads(shared.STRATA_CONFIG.read_text(encoding='utf-8'))
    saved = ROOT / 'q4-expert-profile.bin'
    if saved.exists():
        saved.unlink()
    warm_cfg = ROOT / 'strata-cfg-q4-warm.json'
    warm = dict(base)
    warm['expert_profile_save'] = str(saved)
    warm['expert_profile_save_every'] = 1
    warm_cfg.write_text(json.dumps(warm, indent=1), encoding='utf-8')
    out = {}
    with shared.strata_engine('q4-warm', warm_cfg):
        sent = 0
        started = time.monotonic()
        while sent < 40 and (time.monotonic() - started) < 150:   # cross the one-minute save interval
            rate_probe('http://127.0.0.1:8080', 'strata-coder', max_tokens=160)
            sent += 1
            if sent % 5 == 0:
                log(name, 'warm-up %d sent (%.0f s in), profile present: %s'
                    % (sent, time.monotonic() - started, saved.exists()))
        out['warm_ups_sent'] = sent
        out['warm_seconds'] = round(time.monotonic() - started, 1)
        out['cold_probe_after_warm'] = rate_probe('http://127.0.0.1:8080', 'strata-coder')
        out['warm_engine_lines'] = engine_rate_lines('q4-warm')
    out['profile_saved'] = saved.exists()
    out['profile_bytes'] = saved.stat().st_size if saved.exists() else 0
    if not saved.exists():
        write_result(name, {'item': name, **out,
                            'status': 'INCOMPLETE',
                            'why': 'the engine wrote no profile, so the from-profile half did not run'})
        print('INCOMPLETE: no expert profile was written, so there is nothing to start from.')
        print('The warm half ran (%d warm-ups, %.0f s); the item is unscored rather than green.'
              % (out['warm_ups_sent'], out['warm_seconds']))
        return 4
    cal_cfg = ROOT / 'strata-cfg-q4-saved.json'
    cal_cfg.write_text(json.dumps(warm, indent=1), encoding='utf-8')
    with shared.strata_engine('q4-from-saved', cal_cfg):
        out['probe_from_saved'] = rate_probe('http://127.0.0.1:8080', 'strata-coder')
        code, letters, _ = reason_letters(name, 'http://127.0.0.1:8080', 'strata-coder', 'q4-from-saved')
        out['letters_of_93'] = letters
        out['reason_exit'] = code
        out['saved_engine_lines'] = engine_rate_lines('q4-from-saved')
    write_result(name, {'item': name, **out})
    return 0


def q5_ollama_decision_path(name='q5-ollama-decision-path'):
    """Ollama 0.40.4's native decision-model path on the frozen 18 windows.

    Refuses to run, loudly, until a decision model is actually present in Ollama's store: the pull is a
    download and this queue downloads nothing without saying so here.
    """
    listed = subprocess.run(['ollama', 'list'], capture_output=True, text=True, timeout=120).stdout
    decision = [line for line in listed.splitlines()
                if any(k in line.lower() for k in ('laya', 'gliner', 'nimble', 'clef'))]
    if not decision:
        write_result(name, {'item': name, 'status': 'blocked', 'reason': 'no decision model in ollama list',
                            'pull': 'ollama run nimble   (or the Laya/GLiNER tag 0.40.4 documents)'})
        print('BLOCKED: no decision model is present in Ollama. Pull one first:')
        print('    ollama run nimble')
        print('then re-run this item. Nothing was downloaded by this queue.')
        return 3
    model = decision[0].split()[0]
    code = run(name, [sys.executable, LAYA_REPLAY, '--url', 'http://127.0.0.1:11434',
                      '--out', str(ROOT / 'q5-ollama-decision.json'),
                      '--engine', 'ollama 0.40.4 native decision path', '--checkpoint', model],
               cwd=LAYA_REPLAY.parent, timeout=3 * 3600)
    write_result(name, {'item': name, 'model': model, 'exit': code,
                        'out': str(ROOT / 'q5-ollama-decision.json')})
    return code


ITEMS = {'q1-strata-kv-residency': q1_strata_kv_residency,
         'q2-moe-cache-mib-ladder': q2_moe_cache_ladder,
         'q3-noise-floor': q3_noise_floor,
         'q4-calibrated-warm-cache': q4_calibrated_profile,
         'q5-ollama-decision-path': q5_ollama_decision_path}


if __name__ == '__main__':
    wanted = sys.argv[1]
    sys.exit(ITEMS[wanted](wanted))
