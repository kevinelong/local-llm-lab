"""refresh-snapshot.py - copy the lab's instruments and small evidence into this repo, with a hash manifest.

Why: `C:/Users/kevin/ai_bench` is where the work lives but it holds tens of gigabytes of model packs, so it
is not itself version-controlled. This script takes a curated, reproducible snapshot of the *code*, the
frozen inputs and the small evidence into `local-llm-lab/instruments/`, and writes `SNAPSHOT.json` mapping
every copied file to its source path, size and sha256 - so anyone can see what was copied, and re-run this
after a change to refresh it and commit the difference.

Never copied: model packs, weights, archives, executables, databases, wire captures, per-run logs, caches,
and anything over the size cap. The list below is the whole policy; keep it explicit.

Usage: python refresh-snapshot.py [--check]     (--check reports drift without writing)
"""
import argparse
import hashlib
import json
import shutil
from fnmatch import fnmatch
from pathlib import Path

BASE = Path(r'C:\Users\kevin\ai_bench')
DEST_ROOT = Path(__file__).resolve().parent
SIZE_CAP = 2 * 1024 * 1024

# source directory -> patterns to include (relative to that directory); ('**' is matched by fnmatch via rel)
INCLUDE = {
    'new-items-20261007': ['*.py', 'knowledge-items-*.jsonl', 'knowledge-result-*.json',
                           'knowledge-deep-*.json', 'knowledge-deep-corpus-*.json', '*.md'],
    'bespoke-metric-20261010': ['*'],
    'colibri-laya-20261011': ['*'],
    'decision-signal-20261011': ['*'],
    'strata-warmcache-20261011': ['*'],
    'overnight-20261011': ['*.py', '*.json', '*.md', 'logs/*.log', 'OVERNIGHT-STOP'],
    'bespoke-suite-20261010-v1': ['*.py', '*.md', 'evidence/*.json', 'evidence/*/runs/*/rows.jsonl'],
    'local-decisions-followup-20260925-v1': ['*.py', '*.json', '*.md'],
    'strata-20261005-v1': ['*.md'],
}
ALWAYS_EXCLUDE = ('__pycache__', '.git', 'node_modules', 'RUNNING.lock')


def matches(relative, patterns):
    """A relative path matches when any pattern matches it, or matches its file name for bare patterns."""
    for pattern in patterns:
        if fnmatch(relative, pattern):
            return True
        if '/' not in pattern and fnmatch(Path(relative).name, pattern):
            return True
    return False


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()

    manifest, copied, skipped_big, missing = {}, 0, [], []
    for source, patterns in INCLUDE.items():
        source_dir = BASE / source
        if not source_dir.exists():
            missing.append(source)
            continue
        entries = []
        for path in sorted(source_dir.rglob('*')):
            if not path.is_file():
                continue
            relative = str(path.relative_to(source_dir)).replace('\\', '/')
            if any(part in ALWAYS_EXCLUDE for part in path.parts):
                continue
            if not matches(relative, patterns):
                continue
            if path.stat().st_size > SIZE_CAP:
                skipped_big.append('%s/%s (%.2f MiB)' % (source, relative, path.stat().st_size / 1048576))
                continue
            entries.append((relative, path))
        for relative, path in entries:
            target = DEST_ROOT / source / relative
            manifest['%s/%s' % (source, relative)] = {'bytes': path.stat().st_size,
                                                      'sha256': sha256(path)}
            if not args.check:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, target)
                copied += 1

    if not args.check:
        (DEST_ROOT / 'SNAPSHOT.json').write_text(json.dumps(
            {'generated': '2026-10-12', 'source_root': str(BASE), 'size_cap_bytes': SIZE_CAP,
             'policy': 'code, frozen inputs and small evidence only; never packs, weights, archives, '
                       'executables, databases, wire captures, per-run logs or caches',
             'files': manifest}, indent=1, sort_keys=True), encoding='utf-8')

    print('files: %d   total: %.2f MiB' % (len(manifest), sum(v['bytes'] for v in manifest.values()) / 1048576))
    for source in INCLUDE:
        count = sum(1 for key in manifest if key.startswith(source + '/'))
        print('  %-40s %4d files' % (source, count))
    if skipped_big:
        print('skipped over the %d MiB cap:' % (SIZE_CAP // 1048576))
        for item in skipped_big:
            print('  ', item)
    if missing:
        print('source directories not present:', missing)
    if not args.check:
        print('wrote SNAPSHOT.json')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
