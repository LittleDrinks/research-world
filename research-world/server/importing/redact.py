from functools import lru_cache
import json
import re

_SECRET=re.compile(r'(?i)api.?key|authorization|password|secret|access.?token|refresh.?token|^token$|cookie|base_?url')
_INLINE=re.compile(r'''(?i)(\b(?:[\w-]{0,64}(?:api.?key|password|secret|access.?token|refresh.?token|base_?url)|token|authorization)["']?\s*[:=]\s*["']?)[^\s,"';}]+''')
_BEARER=re.compile(r'''(?i)\b(Bearer|Basic)\s+[^\s,"'}]+''')
_KEY=re.compile(r'\b(?:sk-[A-Za-z0-9_-]{12,}|gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,})')
_URL_AUTH=re.compile(r'(https?://)[^/\s:@]+:[^/\s@]+@')


def sanitize(value):
    if isinstance(value,dict):
        return {key:'<redacted>' if _SECRET.search(key) else sanitize(item) for key,item in value.items()}
    if isinstance(value,list):return [sanitize(item) for item in value]
    if not isinstance(value,str):return value
    value=_KEY.sub('<redacted>',_URL_AUTH.sub(r'\1<redacted>@',value))
    return _INLINE.sub(r'\1<redacted>',_BEARER.sub(r'\1 <redacted>',value))


def _session_metadata(value):
    if value.get('type')=='session':
        return {key:value[key] for key in ['type','id','timestamp','version'] if key in value}
    if value.get('type')=='session_meta':
        payload=value.get('payload',{})
        return {**value,'payload':{key:payload[key] for key in ['id','timestamp','cli_version'] if key in payload}}
    return value


@lru_cache(maxsize=8)
def trajectory(path):
    records=[]
    with path.open() as source:
        for line in source:
            if not line.strip():continue
            value=_session_metadata(json.loads(line))
            records.append(json.dumps(sanitize(value),ensure_ascii=False))
    return ('\n'.join(records)+'\n').encode()
