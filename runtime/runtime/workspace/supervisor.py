"""Supervise a Docker exec and reap descendants, including detached process groups."""
import ctypes
import json
import os
from pathlib import Path
import signal
import subprocess
import sys

import psutil


def terminate_children():
    while children := psutil.Process().children(recursive=True):
        for child in children:
            try: child.kill()
            except psutil.NoSuchProcess: pass
        psutil.wait_procs(children, timeout=2)


def prepare(state):
    if ctypes.CDLL(None, use_errno=True).prctl(36, 1, 0, 0, 0) != 0:
        raise OSError(ctypes.get_errno(), 'Cannot supervise workspace descendants')
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(130))
    state.mkdir(mode=0o700, exist_ok=True)
    (state/'pid.tmp').write_text(str(os.getpid()))
    (state/'pid.tmp').replace(state/'pid')


def main():
    state = Path('/tmp') / ('rw-exec-' + sys.argv[1])
    request = json.loads(sys.stdin.readline())
    code = request.pop('code')
    prepare(state)
    try:
        if (state/'cancel').exists(): return 130
        process = subprocess.Popen([sys.executable,'-u','-c',code], stdin=subprocess.PIPE, start_new_session=True)
        process.communicate(json.dumps(request).encode())
        return process.returncode if process.returncode >= 0 else 128 - process.returncode
    finally:
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        terminate_children()
        (state/'pid').unlink(missing_ok=True)


if __name__ == '__main__': sys.exit(main())
