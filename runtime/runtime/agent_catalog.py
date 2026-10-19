from __future__ import annotations

import json
import os
from pathlib import Path

TOOLS = {
    'workspace': '读写、编辑和运行项目工作区文件，与 JupyterLab 共享',
    'graph': '查询当前项目的研究图谱',
    'record': '将研究方向或实验结果写入当前项目',
    'change': '读取研究记录与版本、查看历史、修订、评论、贴标及管理项目标签',
    'mmr': '按相关性与多样性选择候选，返回选择顺序和逐步评分',
    'artifact': '保存不可变研究报告或实验产物',
    'joint_condition': '记录 AND、OR 或 k-of-N 联合条件及其证据，不代表科学判真',
    'connect': '连接支持、反驳或依赖关系',
    'literature': '检索 Crossref、OpenAlex、arXiv 或 PubMed',
    'delegate': '委派独立上下文的研究或审查 Agent',
}


def catalog():
    root = Path(os.environ['PI_CODING_AGENT_DIR'])
    settings = _read(root / 'settings.json')
    providers = _read(root / 'models.json').get('providers', {})
    models = [f'{provider}/{model["id"]}' for provider, value in providers.items()
              for model in value.get('models', [])]
    default = '/'.join(settings.get(key, '') for key in ('defaultProvider', 'defaultModel'))
    return {'models': models, 'default_model': default if default in models else '',
            'skills': list(skill_paths()), 'tools': TOOLS, 'runtime': 'pi'}


def skill_paths():
    roots = os.getenv('RUNTIME_SKILLS_PATHS', '/app/skills').split(':')
    found = {}
    for root in roots:
        for path in sorted(Path(root).glob('*/SKILL.md')):
            found.setdefault(path.parent.name, str(path))
    return found


def _read(path):
    return json.loads(path.read_text()) if path.exists() else {}


def validate_spec(spec):
    value = catalog()
    if spec.get('model') not in value['models']:
        raise ValueError('请选择 Pi 配置中存在的模型')
    if set(spec.get('tools', [])) - TOOLS.keys():
        raise ValueError('Agent 包含未知工具')
    if set(spec.get('skills', [])) - set(value['skills']):
        raise ValueError('Agent 包含未知 Skill')


def has_workspace(spec):
    return bool(spec.get('project_id')) and spec.get('params', {}).get('mode') != 'title'


def selected_tools(spec):
    selected = [name for name in spec.get('tools', []) if name != 'workspace']
    return [*selected, 'workspace'] if has_workspace(spec) else selected
