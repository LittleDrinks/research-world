import json
import os
import shutil
from pathlib import Path


def prepare():
    source = Path('/pi-source')
    target = Path(os.environ['PI_CODING_AGENT_DIR'])
    target.mkdir(parents=True, exist_ok=True)
    for name in ('models.json', 'auth.json'):
        if (source / name).exists():
            shutil.copyfile(source / name, target / name)
            (target / name).chmod(0o600)
    settings = json.loads((source / 'settings.json').read_text()) if (source / 'settings.json').exists() else {}
    selected = {k:v for k,v in settings.items() if k in {'defaultProvider','defaultModel','defaultThinkingLevel'}}
    (target / 'settings.json').write_text(json.dumps(selected))


prepare()
os.execvp('python', ['python', '-m', 'runtime'])
