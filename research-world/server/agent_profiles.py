from __future__ import annotations

import json
import re
import secrets
from pathlib import Path

DEFAULT_INSTRUCTIONS = ('围绕科学问题开展研究，区分事实、推断和待验证方向。先查询已有研究图谱，'
    '需要文献时使用 literature。复杂任务可 delegate 独立研究或审查 Agent，'
    '根据返回意见决定下一步。需要保留研究进展时使用 record，证据关系使用 connect。'
    '多个研究对象共同构成条件时用joint_condition，明确AND/OR/k-of-N、角色、目标陈述、理由与证据定位；关系不代表已证实。'
    'Question只定义研究范围，不能参与supports/refutes；方向与问题用Direction指向Question的depends_on。'
    '读写或运行文件时使用workspace的read/write/edit/bash，文件位于/workspace，与JupyterLab共享。'
    'artifact仅发布不可变研究产物，不用于代替创建工作文件。'
    '禁止编造来源、实验结果或把研究计划写成已完成实验。最后给出简明工作摘要和下一步。')


class AgentProfiles:
    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def list(self, default_model):
        values = [json.loads(p.read_text()) for p in sorted(self.root.glob('*.json'))]
        if not any(value['id'] == 'research-assistant' for value in values):
            values.insert(0, default_profile(default_model))
        return values

    def get(self, agent_id, default_model):
        return next(value for value in self.list(default_model) if value['id'] == agent_id)

    def save(self, value):
        value = validate_profile(value)
        path = self.root / f'{value["id"]}.json'
        temporary = path.with_suffix(f'.{secrets.token_hex(8)}.tmp')
        temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2))
        temporary.replace(path)
        return value


def default_profile(model):
    return {'id': 'research-assistant', 'name': '研究助手', 'model': model,
            'instructions': DEFAULT_INSTRUCTIONS, 'thinking': 'high',
            'skills': [], 'tools': ['graph', 'record', 'connect', 'joint_condition', 'artifact', 'literature', 'delegate', 'workspace']}


def validate_profile(value):
    fields = set(default_profile(''))
    if set(value) != fields or not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,63}', value['id']):
        raise ValueError('Agent 字段或标识无效')
    if any(not isinstance(value[k], str) or not value[k].strip() for k in fields - {'tools','skills'}):
        raise ValueError('Agent 必填字段不能为空')
    if value['thinking'] not in {'off','minimal','low','medium','high','xhigh','max'}:
        raise ValueError('无效 thinking 级别')
    for key in ('tools', 'skills'):
        if not isinstance(value[key], list) or any(not isinstance(v,str) for v in value[key]):
            raise ValueError('Skills 和 Tools 必须为标识列表')
    return value
