"""Project documented q049 revisions into a research-iteration example."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / 'evidence/contest-2026/q049'
SCENE = '研究闭环'


def post(client, path, data):
    response = client.post(path, json=data)
    response.raise_for_status()
    return response.json()


def historical_record(client, root, title, text, files, kind='experiment'):
    artifacts = [post(client, root + '/artifacts', {'content': (ROOT / name).read_text(),
                 'media_type': 'text/plain'}) for name in files]
    content = {'title': title, 'text': text, 'note': f'{SCENE} · q049 历史研究投影',
               'attachments': [{'id': a['id'], 'name': name} for a, name in zip(artifacts, files)]}
    return post(client, root + '/records', {'type': kind, 'content': content,
                                           'artifact_ids': [a['id'] for a in artifacts]})


def rejected_directions(client, root):
    power = historical_record(client, root, 'V1 旧方向 · 功率阈值判断耗散',
        '历史错误论证：把地球—太阳引力波功率写成约 10⁻²⁰ W，并以该阈值判断可忽略性。review-v1 明确要求改写；保留用于查看为何修订，不作为当前结论。', ['v1.md', 'review-v1.md'], 'direction')
    ordering = historical_record(client, root, 'V2 旧方向 · 时间尺度错误排序',
        '历史错误论证：以“太阳演化约 5 Gyr ≪ 混沌失稳约 1–5 Gyr”支撑主方向选择。该不等式不成立；review-v2 要求改为并列比较。', ['v2.md', 'review-v2.md'], 'direction')
    return power, ordering


def instability_source(client, root):
    return historical_record(client, root, 'S1 · 混沌失稳的文献反例',
        'Batygin & Laughlin (2008), On the Dynamical Stability of the Solar System. DOI: [10.1086/589232](https://doi.org/10.1086/589232)。V8 S1 记录构造的水星约 1.261 Gyr 坠日轨迹；这不是总体发生概率。该情形反驳“5 Gyr 远早于所有混沌失稳”的排序。来源访问范围沿用历史报告，本次未重新核验全文。', ['v8.md'], 'source')


def revised_direction(client, root):
    return historical_record(client, root, 'V3 修订方向 · 分机制比较时间尺度',
        '在地球—太阳圆轨道近似下，引力波衰减时间远长于太阳主序寿命；混沌失稳作为低概率事件单独讨论，太阳演化作为外部边界。修订吸收两轮反证，不再使用错误功率阈值或时间排序。', ['v3.md', 'v8.md'], 'direction')


def verification(client, root):
    return historical_record(client, root, 'Peters 公式计算 · 历史已执行',
        'V3 §7 公开输入、公式、命令与输出：P = 196.291 W；t = 3.374×10³⁰ s = 1.069×10²³ 年。计算反驳 V1 的错误功率量级，并支持限定的引力波耗散尺度。独立复算审计报告作为附件保存；不把评审另建为实验，也不把该计算外推为潮汐或混沌的验证。', ['v3.md', 'review-v3.md'])


def followups(client, root):
    numerical = historical_record(client, root, '下一轮 · N体与相对论对照（未执行）',
        '待执行：用相同初值比较牛顿 N 体与加入广义相对论的积分，区分混沌机制与模型效应。输入、对照与待检验问题来自 V8 §6；没有新的模拟结果。', ['v8.md'])
    evolution = historical_record(client, root, '下一轮 · 太阳演化对照（未执行）',
        '待执行：在相同轨道初值上加入太阳质量损失，比较轨道响应；按 V8 §6 保留基线和对照。用于继续检验适用范围，不能预先挂 supports 或 refutes。', ['v8.md'])
    return numerical, evolution


def connect(client, root, source, target, kind):
    return post(client, root + '/relations', {'source_id': source['id'], 'target_id': target['id'], 'type': kind})


def connect_history(client, root, old, source, calculation, revised, planned):
    connect(client, root, calculation, old[0], 'refutes')
    connect(client, root, source, old[1], 'refutes')
    gw = next(r for r in client.get(root + '/records').json() if r['content']['title'] == '地球—太阳引力波耗散尺度')
    connect(client, root, calculation, gw, 'supports')
    for experiment in planned:
        connect(client, root, experiment, revised, 'depends_on')


def revision_condition(client, root, source, calculation, revised):
    return post(client, root + '/joint-conditions', {
        'title': f'{SCENE} · 计算与反例共同约束修订', 'rule': 'AND', 'target_id': revised['id'],
        'members': [{'record_id': r['id'], 'role': role} for r, role in
                    [(calculation, '引力波时间尺度'), (source, '混沌失稳的范围边界')]],
        'statement': '修订方向同时采用正确的引力波耗散尺度，并保留混沌失稳早于太阳演化边界的可能性。',
        'rationale': '计算纠正错误功率量级；文献反例纠正过强的时间排序。二者针对不同机制，联合约束分机制比较，不据此宣称真实太阳系的最终命运已确定。',
        'evidence': [{'artifact_id': calculation['artifact_ids'][0], 'locator': 'V3 §7 已执行计算；§9 判据修订'},
                     {'artifact_id': source['artifact_ids'][0], 'locator': 'V8 §3 S1：构造的约1.261 Gyr失稳轨迹；§5 并列比较'}]})


def seed_semantic_loop(client, root):
    if any(c['title'] == f'{SCENE} · 计算与反例共同约束修订' for c in client.get(root + '/joint-conditions').json()):
        return
    old = rejected_directions(client, root)
    source = instability_source(client, root)
    revised = revised_direction(client, root)
    calculation = verification(client, root)
    planned = followups(client, root)
    connect_history(client, root, old, source, calculation, revised, planned)
    revision_condition(client, root, source, calculation, revised)
