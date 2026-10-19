import hashlib
import json
import platform
import subprocess
import sys
import time
from pathlib import Path
import numpy
import scipy

ROOT=Path('/work')

def run(folder,name):
    started=time.perf_counter()
    completed=subprocess.run([sys.executable,name],cwd=folder,capture_output=True,text=True,timeout=120)
    (folder/(name+'.stdout.txt')).write_text(completed.stdout)
    (folder/(name+'.stderr.txt')).write_text(completed.stderr)
    return completed,time.perf_counter()-started

def execute(folder):
    generated,prep=run(folder,'data_en.py')
    if generated.returncode:raise RuntimeError(generated.stderr)
    result,elapsed=run(folder,'main_en.py')
    expected=(folder/'expected.txt').read_text()
    actual=float(result.stdout.split('[Final Output]')[-1].strip()) if result.returncode==0 else None
    target=float(expected.split('[Final Output]')[-1].strip())
    raw_inputs={str(p.relative_to(folder)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (folder/'data').glob('*') if p.is_file()}
    return {'case':folder.parent.name,'input':folder.name,'exit_code':result.returncode,'seconds':elapsed,'prepare_seconds':prep,
            'expected':target,'observed':actual,'absolute_error':abs(actual-target) if actual is not None else None,
            'exact_stdout':result.stdout.strip()==expected.strip(),'data_sha256':raw_inputs,
            'code_sha256':hashlib.sha256((folder/'main_en.py').read_bytes()).hexdigest()}

def main():
    rows=[execute(folder) for folder in sorted(ROOT.glob('case*/input*'))]
    result={'environment':{'python':platform.python_version(),'numpy':numpy.__version__,'scipy':scipy.__version__},'runs':rows}
    (ROOT/'reference-results.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
