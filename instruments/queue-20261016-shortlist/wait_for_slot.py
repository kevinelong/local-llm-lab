"""wait_for_slot.py - wait for the inference slot, then drive this queue once, in order.

Why this exists: the queue was declared while a measured run was still in flight (the Colibri knowledge
item, which owns the one inference slot until it stops). The driver refuses to start while an engine is
listening on the lab's Colibri port, so this waits for that port to fall silent and then runs the driver
exactly as if it had been typed by hand.

Launch it through the harness, never with a bare shell `&` - the 2026-10-11 queue lost its driver that way.

    python wait_for_slot.py         # waits up to 16 h for the slot, then runs the queue

Everything it does is visible while it waits: `logs/wait_for_slot.log` gets a line per check, and the driver
writes `status.json` and `REPORT.md` from the moment it starts.
"""
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / 'overnight-20261011'))
sys.path.insert(0, str(ROOT))
import shared                                     # noqa: E402

MAX_WAIT_S = 16 * 3600
POLL_S = 60


def log(message):
    line = '%s  %s' % (time.strftime('%F %T'), message)
    (ROOT / 'logs').mkdir(exist_ok=True)
    with (ROOT / 'logs' / 'wait_for_slot.log').open('a', encoding='utf-8') as handle:
        handle.write(line + '\n')
    print(line, flush=True)


def main():
    started = time.time()
    last = 0.0
    while shared.port_open(shared.COLIBRI_PORT):
        if time.time() - started > MAX_WAIT_S:
            log('gave up waiting for port %d after %.0f h; nothing started'
                % (shared.COLIBRI_PORT, MAX_WAIT_S / 3600))
            return 3
        if time.time() - last > 900:              # a line every 15 min, not a line per check
            log('waiting: an engine still holds port %d (%.1f h so far)'
                % (shared.COLIBRI_PORT, (time.time() - started) / 3600))
            last = time.time()
        time.sleep(POLL_S)

    log('the inference slot is free; starting the queue')
    done = subprocess.run([sys.executable, str(ROOT / 'runner.py')], cwd=str(ROOT), text=True)
    log('queue driver exited %d' % done.returncode)
    return done.returncode


if __name__ == '__main__':
    sys.exit(main())
