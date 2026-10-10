"""Verify tree cleanup on a parent and child created only by this control."""
import ctypes
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import compare_staging_20260922 as base


def main():
    base.OWNED_JOBS = True
    with tempfile.TemporaryDirectory() as tmp:
        ready = Path(tmp) / 'child.json'
        program = ("import subprocess,sys,json,time; from pathlib import Path; "
                   "p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(90)'],creationflags=0x08000000); "
                   "Path(sys.argv[1]).write_text(json.dumps({'pid':p.pid})); time.sleep(90)")
        parent = base.spawn_owned([sys.executable, '-c', program, str(ready)], creationflags=base.NO_WINDOW)
        handle = None
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.OpenProcess.restype = ctypes.c_void_p
        kernel.WaitForSingleObject.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
        kernel.CloseHandle.argtypes = [ctypes.c_void_p]
        try:
            end = time.monotonic() + 10
            while not ready.exists() and time.monotonic() < end:
                time.sleep(.1)
            child = json.loads(ready.read_text())['pid']
            handle = kernel.OpenProcess(0x00100000, False, child)
            if not handle:
                raise OSError(ctypes.get_last_error(), 'Cannot observe owned child handle')
            cleanup = base.stop_owned(parent)
            child_exited = kernel.WaitForSingleObject(handle, 5000) == 0
            print(json.dumps({'cleanup': cleanup, 'child_exited': child_exited}))
            assert cleanup.get('returncode') == 0 and child_exited, 'Owned-tree cleanup control failed'
        finally:
            if parent.poll() is None:
                base.stop_owned(parent)
            if handle:
                kernel.CloseHandle(handle)
            base.finish_owned(parent)
    for _ in range(3):
        normal = base.spawn_owned([sys.executable, '-c', "print('NORMAL_EXIT')"], stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, text=True, creationflags=base.NO_WINDOW)
        stdout, stderr = normal.communicate(timeout=10)
        settled = base.finish_owned(normal)
        assert normal.returncode == 0 and stdout.strip() == 'NORMAL_EXIT', (stdout, stderr)
        assert settled['active_before'] == 0 and settled['active_after'] == 0, settled
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / 'solution.py').write_text('def plan(tasks):\n    return []\n')
        code, result = base.score_artifact('graph', root / 'solution.py', root, dict(__import__('os').environ))
        assert result['owned_tree']['active_before'] == 0 and result['owned_tree']['returncode'] == 0, result
    print('Normal process and scorer lifecycle controls passed.')


if __name__ == '__main__':
    main()
