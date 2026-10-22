"""orphan_check.py - who owns our ports, and is anything still holding memory with no visible owner?

Written after two orphan incidents on 2026-10-22:

  * the ComfyUI desktop app exited (code 0) twice and left backend pythons holding **3.1 GiB of commit** and ~1.9 GiB
    of VRAM; the Electron shell was gone, the backend was not;
  * the q7 A/B was contaminated because `proc.terminate()` killed the `cmd /c strata.cmd` wrapper while the
    python/engine children kept the port - so the wrong server answered for an arm. Only a model-id mismatch exposed it.

Cheap enough to run before anything that loads a model: it reads port ownership and the commit of the top holders.
Exit code is 1 when one of OUR lab ports is listening, because that means an engine we did not intend is resident.

    python orphan_check.py
"""

from __future__ import annotations

import json
import subprocess
import sys

# Ports this lab uses. 8000/8001/8003/8004 ComfyUI, 8080/8082-8085 Strata, 8188 ComfyUI default, 11436-11440 llama.cpp.
LAB_PORTS = [8000, 8001, 8003, 8004, 8080, 8082, 8083, 8084, 8085, 8188, 11436, 11437, 11438, 11439, 11440]

PS_PORTS = (
    "$rows=@(); foreach ($p in %s) { "
    "$c = Get-NetTCPConnection -LocalPort $p -State Listen -ErrorAction SilentlyContinue; "
    "foreach ($x in $c) { $pr = Get-Process -Id $x.OwningProcess -ErrorAction SilentlyContinue; "
    "$rows += [pscustomobject]@{port=$p; pid=$x.OwningProcess; name=$(if ($pr) { $pr.ProcessName } else { '?' }); "
    "mib=$(if ($pr) { [math]::Round($pr.PrivateMemorySize64/1MB) } else { 0 })} } }; $rows | ConvertTo-Json -Compress"
) % json.dumps(LAB_PORTS)

PS_MEM = (
    "$o=Get-CimInstance Win32_OperatingSystem; "
    "'free_gib={0:N1} commit_free_gib={1:N1}' -f ($o.FreePhysicalMemory/1MB), ($o.FreeVirtualMemory/1MB); "
    "Get-Process | Sort-Object -Descending PrivateMemorySize64 | Select-Object -First 6 | "
    "ForEach-Object { '  {0,-26} {1,6} MiB commit' -f $_.ProcessName, [math]::Round($_.PrivateMemorySize64/1MB) }"
)


def run(ps):
    return subprocess.run(['powershell', '-NoProfile', '-Command', ps], capture_output=True, text=True, timeout=120).stdout


def main():
    out = run(PS_PORTS).strip()
    try:
        rows = json.loads(out) if out else []
    except Exception:
        rows = []
    if isinstance(rows, dict):
        rows = [rows]

    print('lab ports listening: %d' % len(rows))
    for r in rows:
        print('  port %-5s pid %-7s %-12s %s MiB commit' % (r['port'], r['pid'], r['name'], r['mib']))

    print('\nmemory:')
    print(run(PS_MEM).rstrip())

    try:
        vram = subprocess.run(['nvidia-smi', '--query-gpu=memory.used,memory.total', '--format=csv,noheader'],
                              capture_output=True, text=True, timeout=20).stdout.strip()
        print('vram: %s MiB' % vram)
    except Exception:
        pass

    if rows:
        print('\none of our ports is listening: an engine is resident. Confirm it is intended before loading another, '
              'and remember killing a cmd wrapper does not kill its python/engine children.')
        return 1
    print('\nnothing on our ports: clean before a load.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
