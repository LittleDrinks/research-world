import json
import re

_SECRET = re.compile(r'(?i)(api[_-]?key|authorization|password|secret|access[_-]?token|credential|cookie)')
_INLINE = re.compile(r'''(?ix)(["']?(?:api[_-]?key|password|secret|access[_-]?token|authorization|credential)["']?\s*[:=]\s*["']?)([^\s,"';}]+)''')
_BEARER = re.compile(r'(?i)\b(Bearer|Basic)\s+[^\s,"\'}]+')


def sanitize(value):
    if isinstance(value, dict):
        return {key: '<redacted>' if _SECRET.search(key) else sanitize(item) for key,item in value.items()}
    if isinstance(value, (list,tuple)):
        return [sanitize(item) for item in value]
    if not isinstance(value, str):
        return value
    if value.lstrip().startswith(('{','[')):
        try:
            return json.dumps(sanitize(json.loads(value)), ensure_ascii=False)
        except ValueError:
            pass
    return _INLINE.sub(r'\1<redacted>', _BEARER.sub(r'\1 <redacted>', value))
