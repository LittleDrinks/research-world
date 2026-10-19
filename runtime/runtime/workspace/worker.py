"""Executed as the workspace user; stdin contains one operation, stdout its bytes."""
import json
import mimetypes
import os
from pathlib import Path
import subprocess
import sys


def workspace_path(value):
    path = (Path('/workspace') / value).resolve()
    if not path.is_relative_to('/workspace'):
        raise ValueError('File path must stay inside /workspace')
    return path


def file_operation(request):
    path = workspace_path(request['path'])
    operation = request['operation']
    if operation == 'read':
        if not path.is_file(): raise ValueError('Not a regular file')
        with path.open('rb') as source:
            content = source.read(request['max_bytes'] + 1) if 'max_bytes' in request else source.read()
        if 'max_bytes' in request and len(content) > request['max_bytes']:
            raise ValueError('File exceeds capture limit')
        sys.stdout.buffer.write(content)
    elif operation == 'write': path.write_text(request['content'], encoding='utf-8')
    elif operation == 'mkdir': path.mkdir(parents=True, exist_ok=True)
    elif operation == 'access':
        if not path.is_file() or not os.access(path, os.R_OK): raise ValueError('File is not readable')
    elif operation == 'mime': print(mimetypes.guess_type(path)[0] or '')
    else: raise ValueError('Unknown workspace operation')


def main():
    request = json.load(sys.stdin)
    if request['operation'] == 'bash':
        environment = {k:v for k,v in os.environ.items() if k != 'JUPYTER_TOKEN'}
        result = subprocess.run(['/bin/bash','--noprofile','--norc','-c',request['command']],
                                cwd='/workspace', env=environment)
        sys.exit(result.returncode if result.returncode >= 0 else 128 - result.returncode)
    file_operation(request)


if __name__ == '__main__':
    try: main()
    except Exception as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
