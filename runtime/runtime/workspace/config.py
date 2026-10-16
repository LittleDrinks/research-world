import io
import json
import tarfile
from pathlib import Path


def pi_configuration(root,model):
    provider,identifier=model.split('/',1)
    providers=json.loads((root/'models.json').read_text())['providers']
    if provider not in providers:raise ValueError('模型提供方不存在')
    entry=providers[provider]
    models=[m for m in entry.get('models',[]) if m['id']==identifier]
    if not models:raise ValueError('工作区模型不存在')
    settings={'defaultProvider':provider,'defaultModel':identifier,'defaultThinkingLevel':'high'}
    auth=json.loads((root/'auth.json').read_text()) if (root/'auth.json').exists() else {}
    return {'models.json':{'providers':{provider:{**entry,'models':models}}},
            'settings.json':settings,'auth.json':{provider:auth[provider]} if provider in auth else {}}


def configuration_archive(files):
    data=io.BytesIO()
    with tarfile.open(fileobj=data,mode='w') as archive:
        for name,value in files.items():
            content=json.dumps(value).encode();info=tarfile.TarInfo(name)
            info.size=len(content);info.mode=0o600;info.uid=info.gid=1000
            archive.addfile(info,io.BytesIO(content))
    return data.getvalue()
