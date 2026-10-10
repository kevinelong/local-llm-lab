"""Windows Job containment for this lab's children, with a start handshake."""
import ctypes
from ctypes import wintypes as w
import json
from pathlib import Path
import subprocess
import sys
import time


class BasicLimit(ctypes.Structure):
    _fields_ = [('process_time', ctypes.c_longlong), ('job_time', ctypes.c_longlong),
                ('flags', w.DWORD), ('min_ws', ctypes.c_size_t), ('max_ws', ctypes.c_size_t),
                ('active_limit', w.DWORD), ('affinity', ctypes.c_size_t),
                ('priority', w.DWORD), ('scheduling', w.DWORD)]


class ExtendedLimit(ctypes.Structure):
    _fields_ = [('basic', BasicLimit), ('io', ctypes.c_ulonglong * 6),
                ('process_memory', ctypes.c_size_t), ('job_memory', ctypes.c_size_t),
                ('peak_process', ctypes.c_size_t), ('peak_job', ctypes.c_size_t)]


class Accounting(ctypes.Structure):
    _fields_ = [('times', ctypes.c_longlong * 4), ('faults', w.DWORD),
                ('total', w.DWORD), ('active', w.DWORD), ('terminated', w.DWORD)]


class Job:
    def __init__(self):
        self.kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        signatures = {
            'CreateJobObjectW': ([ctypes.c_void_p, w.LPCWSTR], w.HANDLE),
            'SetInformationJobObject': ([w.HANDLE, ctypes.c_int, ctypes.c_void_p, w.DWORD], w.BOOL),
            'AssignProcessToJobObject': ([w.HANDLE, w.HANDLE], w.BOOL),
            'QueryInformationJobObject': ([w.HANDLE, ctypes.c_int, ctypes.c_void_p, w.DWORD, ctypes.c_void_p], w.BOOL),
            'TerminateJobObject': ([w.HANDLE, w.UINT], w.BOOL),
            'CloseHandle': ([w.HANDLE], w.BOOL),
        }
        for name, (args, result) in signatures.items():
            fn = getattr(self.kernel, name)
            fn.argtypes, fn.restype = args, result
        self.handle = self.kernel.CreateJobObjectW(None, None)
        self.check(self.handle)
        limits = ExtendedLimit()
        limits.basic.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE; no breakaway.
        try:
            self.check(self.kernel.SetInformationJobObject(self.handle, 9, ctypes.byref(limits), ctypes.sizeof(limits)))
        except BaseException:
            self.kernel.CloseHandle(self.handle)
            raise

    @staticmethod
    def check(value):
        if not value:
            raise ctypes.WinError(ctypes.get_last_error())

    def active(self):
        info = Accounting()
        self.check(self.kernel.QueryInformationJobObject(self.handle, 1, ctypes.byref(info), ctypes.sizeof(info), None))
        return info.active

    def terminate(self, process):
        before = self.active()
        self.check(self.kernel.TerminateJobObject(self.handle, 143))
        process.wait(timeout=10)
        end = time.monotonic() + 5
        while self.active() and time.monotonic() < end:
            time.sleep(.05)
        after = self.active()
        return {'method': 'windows_job', 'returncode': 0 if after == 0 else 1,
                'active_before': before, 'active_after': after}

    def finish(self, process):
        # Process exit and job accounting can settle a few milliseconds apart.
        # Give normal descendants a bounded chance to disappear before reaping.
        end = time.monotonic() + 1
        while process.poll() is not None and self.active() and time.monotonic() < end:
            time.sleep(.02)
        before = self.active()
        result = self.terminate(process) if before else {'method': 'windows_job', 'returncode': 0, 'active_before': 0, 'active_after': 0}
        self.check(self.kernel.CloseHandle(self.handle))
        self.handle = None
        return result


def spawn(command, **kwargs):
    job = Job()
    kwargs['stdin'] = subprocess.PIPE
    process = None
    try:
        process = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), '--child', json.dumps(command)], **kwargs)
        job.check(job.kernel.AssignProcessToJobObject(job.handle, int(process._handle)))
        process._lab_job = job
        process.stdin.write('G' if kwargs.get('text') else b'G')
        process.stdin.flush()
        process.stdin.close()
        process.stdin = None
        return process
    except BaseException:
        if process is not None and process.poll() is None:
            process.kill()
            process.wait(timeout=5)
        job.kernel.CloseHandle(job.handle)
        raise


if __name__ == '__main__':
    if sys.argv[1] != '--child' or sys.stdin.buffer.read(1) != b'G':
        raise SystemExit('Missing owner handshake')
    child = subprocess.Popen(json.loads(sys.argv[2]), stdin=subprocess.DEVNULL,
                             creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    raise SystemExit(child.wait())
