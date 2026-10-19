"""Creation checks shared by people and agents."""
import hashlib
import json
import re
from difflib import SequenceMatcher
from urllib.parse import urlsplit, urlunsplit

from .change_store import ChangeConflict


def canonical_link(value):
    parts = urlsplit(str(value or '').strip())
    if parts.scheme not in {'http', 'https'} or not parts.hostname or parts.username or parts.password:
        raise ValueError('来源需要可定位的官方链接或 DOI 链接')
    host = parts.netloc.lower()
    path = parts.path.rstrip('/')
    if host in {'doi.org', 'dx.doi.org'}:
        host, path = 'doi.org', path.lower()
        if not re.fullmatch(r'/10\.\d{4,9}/\S+', path):
            raise ValueError('DOI 链接格式无效')
    return urlunsplit(('https' if host == 'doi.org' else parts.scheme, host, path, '' if host == 'doi.org' else parts.query, ''))


def normalized(text):
    return ''.join(re.findall(r'\w', str(text).casefold()))


def match_record(record, content):
    same_link = bool(content.get('canonical_url')) and record.content.get('canonical_url') == content['canonical_url']
    title = SequenceMatcher(None, normalized(content.get('title')), normalized(record.content.get('title')), autojunk=False).ratio()
    body = SequenceMatcher(None, normalized(content.get('text')), normalized(record.content.get('text')), autojunk=False).ratio()
    score = max(title if content.get('title') else 0, body if len(normalized(content.get('text'))) >= 30 else 0)
    if not same_link and score < .82:
        return None
    return {'id': record.id, 'revision': record.revision, 'title': record.content.get('title', ''),
            'text': record.content.get('text', '')[:1200], 'score': round(score, 4),
            'reason': '规范链接相同' if same_link else '标题或正文文本高度重合'}


def inspect_creation(records, kind, content):
    content = dict(content)
    if kind not in {'question', 'direction', 'source', 'experiment'}:
        raise ValueError('研究对象类型无效')
    if any(key in content for key in ('status', 'close_reason', 'duplicate_of', 'creation_decision')):
        raise ValueError('状态通过 Changes 提交；创建决策由重复检查记录')
    if kind == 'source':
        content['canonical_url'] = canonical_link(content.get('canonical_url'))
    matches = [match_record(record, content) for record in records if record.type == kind]
    digest = hashlib.sha256(json.dumps([kind, content], ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    return content, {'draft_hash': digest, 'method': '规范链接匹配与文本 SequenceMatcher；不是语义判定',
                     'matches': sorted(filter(None, matches), key=lambda m: (-m['score'], m['id']))}


def confirm_creation(check, resolution):
    matches = {m['id']: m['revision'] for m in check['matches']}
    if not matches and resolution is None:
        return
    if not resolution or not resolution.get('reason', '').strip() or resolution.get('matches') != matches or resolution.get('draft_hash') != check['draft_hash']:
        raise CreationConflict(check)


class CreationConflict(ChangeConflict):
    def __init__(self, check):
        self.detail = {'message': '发现可能重复的研究对象，请查看对比；仍需新建时说明差异。', **check}
        super().__init__(self.detail['message'])
