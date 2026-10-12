"""Swift's context ladder: served context vs the VRAM it actually consumed, per root.

Read-only. The exemption for Swift was measured once (`gpu_free` bottomed at 0.49 GiB against the
0.5 GiB floor at 131,072); this prints the same numbers for every Swift root on disk so the ladder
(32,768 / 65,536 / 98,304 / 131,072) can be read off the artifacts instead of argued about.

The floor and the gate are the lab's own: runtime floor 0.5 GiB GPU free (0.49 is a trip), and the
monitor's verdict is in each session's status.json `monitor_errors`.

Usage: python ctx_ladder.py [root ...]      (default: every newtasks-*swift* root)
"""
import json
import re
import sys
from pathlib import Path

BASE = Path(r'C:\Users\kevin\ai_bench')
FLOOR_GIB = 0.5


def session_dirs(root):
    return sorted(p for p in root.iterdir() if p.is_dir() and (p / 'resources.json').exists())


def served_context(session):
    log = session / 'server.log'
    if not log.exists():
        return None
    for line in log.read_text(encoding='utf-8', errors='replace').splitlines():
        if 'n_ctx_slot =' in line:
            digits = re.findall(r'\d+', line.split('n_ctx_slot =')[1])
            if digits:
                return int(digits[0])
    return None


def monitor_verdict(session):
    path = session / 'status.json'
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except ValueError:
        return None
    return data.get('monitor_errors') or data.get('error')


def main():
    names = sys.argv[1:]
    roots = [BASE / n for n in names] if names else sorted(BASE.glob('newtasks-*swift*'))
    print('%-34s %-8s %-9s %-9s %-9s %s' % ('root', 'served', 'min_gpu', 'min_phys', 'max_gpu', 'verdict'))
    for root in roots:
        if not root.is_dir():
            continue
        gpu_free, phys, gpu_used, ctx = [], [], [], None
        verdict = None
        for session in session_dirs(root):
            samples = json.loads((session / 'resources.json').read_text(encoding='utf-8'))
            for sample in samples:
                if isinstance(sample.get('gpu_free_gib'), (int, float)):
                    gpu_free.append(sample['gpu_free_gib'])
                if isinstance(sample.get('physical_available_gib'), (int, float)):
                    phys.append(sample['physical_available_gib'])
                if isinstance(sample.get('gpu_used_gib'), (int, float)):
                    gpu_used.append(sample['gpu_used_gib'])
            ctx = ctx or served_context(session)
            verdict = verdict or monitor_verdict(session)
        if not gpu_free:
            print('%-34s %-8s %s' % (root.name, ctx or '-', 'no samples'))
            continue
        trip = 'TRIP' if min(gpu_free) < FLOOR_GIB else 'ok'
        print('%-34s %-8s %-9.2f %-9.2f %-9.2f %s %s' % (
            root.name, ctx if ctx else '-', min(gpu_free), min(phys), max(gpu_used), trip,
            ('%s' % verdict)[:44] if verdict else ''))


if __name__ == '__main__':
    main()
