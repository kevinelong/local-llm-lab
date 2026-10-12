"""items.py - the overnight queue's items, one function each, dispatched by name.

python items.py <item-name>

Each item starts and stops its own engine (one inference workload at a time) and writes only inside this
root, except the knowledge instrument, which writes its own result files next to itself by design. Any
failure is logged and returned as a non-zero exit code; nothing is retried blindly.
"""
import glob
import json
import os
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import shared

BASE = shared.BASE
KNOWLEDGE_ROOT = BASE / 'new-items-20261007'
DEEP_ROOT = BASE / 'new-items-20261007'
LAYA_REPLAY = BASE / 'colibri-laya-20261011' / 'laya_replay.py'
KOLIBRI_GGUF = BASE / 'staged-kolibri-20261007' / 'Kolibri-1-Q3_K_M.gguf'
COLIBRI_DIR = BASE / 'staged-colibri-20261011'
GLINER_DIR = Path(r'D:\ai_bench-staged\models\GLiNER2.5-Decide')


def run(name, command, cwd=None, timeout=7200):
    shared.log(name, 'run: %s' % ' '.join(str(c) for c in command))
    done = subprocess.run([str(c) for c in command], cwd=str(cwd) if cwd else None,
                          capture_output=True, text=True, timeout=timeout)
    tail = (done.stdout or '').strip().splitlines()[-12:]
    for line in tail:
        shared.log(name, '  | ' + line)
    if done.returncode != 0:
        shared.log(name, 'exit code %d' % done.returncode)
    return done.returncode


def item_limit(full):
    """OVERNIGHT_LIMIT lets a smoke run cover a couple of items before the real night starts."""
    override = int(os.environ.get('OVERNIGHT_LIMIT', '0') or 0)
    return override if override else full


def knowledge(name, url, model, label, timeout=240, limit=0):
    command = [sys.executable, KNOWLEDGE_ROOT / 'knowledge_run.py', '--url', url, '--model', model,
               '--label', label, '--timeout', str(timeout)]
    limit = item_limit(limit)
    if limit:
        command += ['--limit', str(limit)]
    return run(name, command, cwd=KNOWLEDGE_ROOT, timeout=6 * 3600)


def deep(name, forms, label, url, model, limit=93, pool='shared', seeds=3):
    command = [sys.executable, DEEP_ROOT / 'knowledge_deep.py', '--url', url, '--model', model,
               '--label', label, '--forms', forms, '--limit', str(item_limit(limit)), '--pool', pool,
               '--seeds', str(seeds), '--timeout', '300']
    return run(name, command, cwd=DEEP_ROOT, timeout=6 * 3600)


# ---------------------------------------------------------------- items

def i1_strata_placement(name='i1-strata-placement'):
    """Does the resident budget change the answers? Same 93 items at 2 GiB and 8 GiB resident."""
    original = json.loads(shared.STRATA_CONFIG.read_text(encoding='utf-8'))
    configs = {}
    for gib in (2, 8):
        cfg = json.loads(json.dumps(original))
        args = cfg['args']
        index = args.index('--resident-budget-gib')
        args[index + 1] = str(gib)
        path = shared.ROOT / ('strata-cfg-resident%d.json' % gib)
        cfg['log'] = str(shared.ROOT / ('strata-resident%d.log' % gib))
        path.write_text(json.dumps(cfg, indent=1), encoding='utf-8')
        configs[gib] = path
    codes = {}
    for gib, path in configs.items():
        label = 'strata-res%d' % gib
        with shared.strata_engine(label, path):
            codes[gib] = deep(name, 'reason', label, 'http://127.0.0.1:8080', 'strata-coder', limit=93)
    # compare the two runs' replies item by item
    rows = {}
    for gib in configs:
        result = json.loads((DEEP_ROOT / ('knowledge-deep-result-strata-res%d.json' % gib)).read_text(encoding='ascii'))
        rows[gib] = {r['id']: r for r in result['forms']['reason']['rows']}
    ids = sorted(set(rows[2]) & set(rows[8]))
    differing = [i for i in ids if rows[2][i]['reply'] != rows[8][i]['reply']]
    letters = [i for i in ids if rows[2][i]['first_letter'] != rows[8][i]['first_letter']]
    correct = {g: sum(1 for i in ids if rows[g][i]['letter_ok']) for g in configs}
    shared.write_result(name, {'item': name, 'codes': codes, 'items': len(ids),
                               'replies_differing': len(differing), 'letters_differing': len(letters),
                               'correct_at_2gib': correct.get(2), 'correct_at_8gib': correct.get(8),
                               'differing_ids': differing})
    shared.log(name, 'placement: %d/%d replies differ, letters differ on %d, correct %s vs %s'
               % (len(differing), len(ids), len(letters), correct.get(2), correct.get(8)))
    return 0


def i2_kolibri_knowledge(name='i2-kolibri-knowledge'):
    """A third model on the knowledge instrument: Kolibri-1 with its own patched runtime.

    Two launch details cost a night each to learn and are recorded here rather than rediscovered:

    - `-b 512 -ub 512` is REQUIRED with a 128k context. Without an explicit micro-batch, llama.cpp picks a
      default that makes the flash-attention kernel request more shared memory than the card allows, and the
      community `hob-b11434` build dies at load with `CUDA error: shared object initialization failed` inside
      `launch_fattn` (`cudaOccupancyMaxActiveBlocksPerMultiprocessor(nbytes_shared)`). Probed both ways.
    - `-ctk/-ctv q8_0` requires `-fa on`: with `-fa off` the context fails to build at all
      ("failed to create_context"), which is the opposite pairing to the one the error message suggests.
    """
    flags = ['--cpu-moe', '-fa', 'on', '-ctk', 'q8_0', '-ctv', 'q8_0', '--load-mode', 'none',
             '-b', '512', '-ub', '512',
             '--chat-template-kwargs', '{"reasoning_effort":"low"}']
    engine = shared.llama_engine('kolibri-1', [KOLIBRI_GGUF], flags)
    engine.args[0] = str(shared.KOLIBRI_SERVER)
    with engine:
        code = knowledge(name, 'http://127.0.0.1:11436', 'kolibri-1', 'kolibri-131072', timeout=300)
    shared.write_result(name, {'item': name, 'exit': code,
                               'result': str(KNOWLEDGE_ROOT / 'knowledge-result-kolibri-131072.json')})
    return code


def i3_colibri_qwen36(name='i3-colibri-qwen36'):
    """The same model on a second engine: Colibri's Qwen3.6-35B-A3B, same 1,100 items.

    The setup download is ~23 GB and slower than the rest of the lab's sources (21.45 GiB in two hours on the
    first attempt, so the item timed out with the download unfinished). `coli setup` resumes, so it is looped
    up to three times and the model directory is checked for a plausible footprint before the instrument runs.
    """
    shared.COLIBRI_MODELS.mkdir(parents=True, exist_ok=True)
    setup_code = 0
    for attempt in range(3):
        setup_code = run(name, [shared.COLIBRI, 'setup', '--model', 'qwen36-35b', '--yes',
                                '--dir', str(shared.COLIBRI_MODELS)], cwd=COLIBRI_DIR, timeout=5400)
        sizes = [p.stat().st_size for p in shared.COLIBRI_MODELS.rglob('*.safetensors')]
        total = sum(sizes)
        shared.log(name, 'attempt %d: setup exit %d, %d safetensors, %.2f GiB' %
                   (attempt + 1, setup_code, len(sizes), total / 1024 ** 3))
        if total > 20 * 1024 ** 3:
            break
    candidates = [Path(p) for p in glob.glob(str(shared.COLIBRI_MODELS / '*'))]
    model_dir = None
    for candidate in sorted(candidates):
        if candidate.is_dir() and any(candidate.rglob('*.safetensors')):
            model_dir = candidate
            break
    if model_dir is None:
        shared.write_result(name, {'item': name, 'setup_exit': setup_code, 'error': 'no model directory'})
        return setup_code or 3
    with shared.colibri_engine('colibri-qwen36', model_dir):
        code = knowledge(name, 'http://127.0.0.1:8000', 'qwen36-35b', 'colibri-qwen36-131072', timeout=200)
    shared.write_result(name, {'item': name, 'setup_exit': setup_code, 'model_dir': str(model_dir),
                               'result': str(KNOWLEDGE_ROOT / 'knowledge-result-colibri-qwen36-131072.json')})
    return code


def i4_reason_repeat(name='i4-reason-repeat'):
    """The lab's repeat rule on our own instrument: the format-fixed 93-item run, again."""
    command = [sys.executable, BASE / 'new-items-20261007' / 'knowledge_ab.py', '--script', 'knowledge_deep.py',
               '--forms', 'reason', '--seeds', '1', '--limit', '93', '--pool', 'shared',
               '--suffix=-rep-reason', '--timeout', '300']
    code = run(name, command, cwd=BASE / 'new-items-20261007', timeout=6 * 3600)
    shared.write_result(name, {'item': name, 'exit': code})
    return code


def i5_papers_repeat(name='i5-papers-repeat'):
    """Repeatability of the free-form form: three papers per stack again."""
    command = [sys.executable, BASE / 'new-items-20261007' / 'knowledge_ab.py', '--script', 'knowledge_deep.py',
               '--forms', 'paper', '--seeds', '3', '--suffix=-rep-paper', '--timeout', '300']
    code = run(name, command, cwd=BASE / 'new-items-20261007', timeout=6 * 3600)
    shared.write_result(name, {'item': name, 'exit': code})
    return code


def i6_gliner(name='i6-gliner-replay'):
    """A second decision model on a second engine, same frozen windows: GLiNER2.5-Decide on Colibri.

    The revision is pinned to `a6ef71ce`, the newest one that carries the checkpoint layout the pinned
    engine recognises. Upstream renamed the architecture after it: from revision `2125c8ac` ("Load this
    checkpoint as a Transformers schema-extractor") the root `config.json` says `model_type: gliner2` with
    `architectures: [Gliner2ForSchemaExtraction]`, and `coli serve` refuses it with
    "unsupported model: unsupported model_type: gliner2". At `a6ef71ce` and earlier it is
    `model_type: extractor` / `architectures: [SpanExtractor]`, which is what Colibri's doc describes.
    """
    revision = 'a6ef71ce'
    api = 'https://huggingface.co/api/models/fastino/GLiNER2.5-Decide'
    with urllib.request.urlopen(api, timeout=60) as response:
        meta = json.load(response)
    files = ['model.safetensors', 'config.json', 'tokenizer.json', 'tokenizer_config.json',
             'special_tokens_map.json']
    files += [s['rfilename'] for s in meta['siblings'] if s['rfilename'].startswith('encoder_config/')]
    GLINER_DIR.mkdir(parents=True, exist_ok=True)
    # The first attempt downloaded the newest revision, whose config the engine refuses; clear it so the
    # pinned revision is what actually lands. Redownloadable, and nothing else uses this path.
    if (GLINER_DIR / 'config.json').exists():
        text = (GLINER_DIR / 'config.json').read_text(encoding='utf-8', errors='replace')
        if '"extractor"' not in text:
            shared.log(name, 'clearing the wrong-revision download in %s' % GLINER_DIR)
            shutil.rmtree(GLINER_DIR, ignore_errors=True)
            GLINER_DIR.mkdir(parents=True, exist_ok=True)
    for relative in files:
        target = GLINER_DIR / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() and target.stat().st_size > 0:
            continue
        url = 'https://huggingface.co/fastino/GLiNER2.5-Decide/resolve/%s/%s' % (revision, relative)
        shared.log(name, 'download %s at %s' % (relative, revision))
        subprocess.run(['curl', '-sSL', '--create-dirs', '-o', str(target), url], check=True, timeout=3600)
    with shared.colibri_engine('colibri-gliner', GLINER_DIR):
        code = run(name, [sys.executable, LAYA_REPLAY, '--url', 'http://127.0.0.1:8000',
                          '--out', str(shared.ROOT / 'gliner-colibri.json')],
                   cwd=LAYA_REPLAY.parent, timeout=3 * 3600)
    shared.write_result(name, {'item': name, 'exit': code, 'revision': revision,
                               'out': str(shared.ROOT / 'gliner-colibri.json')})
    return code


ITEMS = {'i1-strata-placement': i1_strata_placement, 'i2-kolibri-knowledge': i2_kolibri_knowledge,
         'i3-colibri-qwen36': i3_colibri_qwen36, 'i4-reason-repeat': i4_reason_repeat,
         'i5-papers-repeat': i5_papers_repeat, 'i6-gliner-replay': i6_gliner}


if __name__ == '__main__':
    if len(sys.argv) != 2 or sys.argv[1] not in ITEMS:
        print('usage: python items.py <%s>' % '|'.join(ITEMS))
        sys.exit(2)
    sys.exit(ITEMS[sys.argv[1]]())
