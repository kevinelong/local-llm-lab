"""supervise.py - wait for the orphaned i3 item, then drive the remaining two items properly.

Context: queue 2 was launched with a bare shell `&` and the driver was reaped when the tool call returned,
while its first item (i3-colibri-qwen36) kept running as an orphan. This waits for that item to exit, clears
the engine ports, then runs the queue driver for the two remaining items in the foreground - which is how it
should have been launched in the first place, so the harness owns the job and reports the result.

Usage: python supervise.py            (long-running; launch it through the harness, not with `&`)
"""
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import shared


def orphan_alive():
    out = subprocess.run(['powershell.exe', '-NoProfile', '-Command',
                          "(Get-CimInstance Win32_Process -Filter \"name='python.exe'\" | "
                          "Where-Object { $_.CommandLine -match 'items.py i3-colibri-qwen36' } | "
                          "Measure-Object).Count"],
                         capture_output=True, text=True)
    try:
        return int(out.stdout.strip().splitlines()[-1]) > 0
    except Exception:
        return False


def main():
    waited = 0
    while orphan_alive():
        if waited % 300 == 0:
            shared.log('supervise', 'waiting for the orphaned i3 item (%ds so far)' % waited)
        time.sleep(30)
        waited += 30
    shared.log('supervise', 'orphan finished after %ds; clearing engine ports' % waited)
    for port in (shared.LLAMA_PORT, shared.STRATA_PORT, shared.COLIBRI_PORT):
        shared.kill_port(port, 'supervise')
    shared.log('supervise', 'starting the remaining items through the driver')
    code = subprocess.call([sys.executable, str(ROOT / 'runner.py'),
                            '--only', 'i4-reason-repeat,i6-gliner-replay'], cwd=str(ROOT))
    shared.log('supervise', 'driver exited %d' % code)
    return code


if __name__ == '__main__':
    sys.exit(main())
