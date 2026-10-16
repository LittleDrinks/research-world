"""Supervise one Docker exec, including background descendants of its command."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys


def kill_group(pid):
    try: os.killpg(pid, signal.SIGKILL)
    except ProcessLookupError: pass


def main():
    state = Path('/tmp') / ('rw-exec-' + sys.argv[1])
    state.mkdir(mode=0o700, exist_ok=True)
    request = json.loads(sys.stdin.readline())
    code = request.pop('code')
    if (state/'cancel').exists(): return 130
    process = subprocess.Popen([sys.executable,'-u','-c',code], stdin=subprocess.PIPE, start_new_session=True)
    (state/'pid').write_text(str(process.pid))
    try:
        if (state/'cancel').exists(): kill_group(process.pid)
        process.communicate(json.dumps(request).encode())
        return process.returncode if process.returncode >= 0 else 128 - process.returncode
    finally: kill_group(process.pid)


if __name__ == '__main__': sys.exit(main())
