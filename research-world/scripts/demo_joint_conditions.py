"""Create an isolated q049 joint-condition demonstration through the public API."""
import argparse
from pathlib import Path

import httpx

from q049_semantic_loop import seed_semantic_loop

ROOT = Path(__file__).resolve().parents[1]
NAME = 'q049 · 联合条件演示'


def post(client, path, value):
    response = client.post(path, json=value)
    response.raise_for_status()
    return response.json()


def record(client, root, title, text, artifact, kind='direction'):
    return post(client, root + '/records', {'type': kind, 'content': {'title': title, 'text': text},
                                          'artifact_ids': [artifact]})['id']


def condition(client, root, title, rule, members, target, statement, rationale, artifact, locator, k=None):
    return post(client, root + '/joint-conditions', {
        'title': title, 'rule': rule, 'k': k, 'target_id': target, 'statement': statement,
        'rationale': rationale, 'members': [{'record_id': i, 'role': role} for i, role in members],
        'evidence': [{'artifact_id': artifact, 'locator': locator}]})


def seed_and(client, root, artifact):
    d1 = record(client, root, 'D1 · 理想模型中的守恒', '无耗散的理想二体模型中，不存在能量损失驱动的持续螺旋内落。不能由此推出真实多体系统永不失稳。', artifact)
    d2 = record(client, root, 'D2 · 真实耗散的时间尺度', 'v8 记录地球—太阳圆轨道引力波计算：inspiral 时间约 1.069×10²³ 年。潮汐结论与适用范围仍需单独核查。', artifact)
    target = record(client, root, '区分自然衰减与真实轨道命运', 'q049 报告解释的关系投影，未经新增审计；守恒解释与耗散时间尺度必须分别说明，不等同于永远稳定。', artifact)
    return condition(client, root, '理想守恒与耗散尺度共同解释', 'AND', [(d1, '理想模型前提'), (d2, '真实耗散补充')], target,
                     '解释为何不能把行星运动概括为必然、持续的螺旋内落，需要同时说明理想模型与真实耗散尺度。',
                     '只讲守恒会忽略真实耗散；只报耗散时间又缺少理想模型基准。两者共同构成分层解释，适用范围仍受原报告限制。',
                     artifact, 'v8 §4 Direction 2：D1+D2共同回答；§5 主方向选择；§7 已执行引力波计算。')


def seed_or(client, root, artifact):
    collision = record(client, root, '条件 · 实际碰撞', '待执行模拟的判据：两天体距离不大于半径和。这里没有新模拟结果。', artifact, 'experiment')
    infall = record(client, root, '条件 · 坠日', '待执行模拟的判据：近日点 q_i 不大于随时间变化的太阳半径 R_sun(t)。', artifact, 'experiment')
    target = record(client, root, '碰撞或坠日事件判定', '判据表达，非已观测事件；轨道交叉只是预警，不等同于实际碰撞。', artifact)
    return condition(client, root, '任一事件触发终局检查', 'OR', [(collision, '碰撞判据'), (infall, '坠日判据')], target,
                     '在待执行轨道模拟中，满足实际碰撞或坠日任一判据，就进入对应事件检查。',
                     '两类事件可以独立触发检查，无需同时发生；不由 OR 关系推断事件已经发生。',
                     artifact, 'v8 §6 可执行研究计划 → 定量判据：实际碰撞、坠日；该节明确 planned，非 executed。')


def seed_threshold(client, root, artifact):
    checks = [('步长敏感性', '减小时间步长后检查事件结论是否变化。'), ('积分器对照', '比较不同积分器下的事件判断。'), ('守恒误差检查', '在对应保守模型中检查能量误差。')]
    members = [(record(client, root, name, '演示新增的待执行检查：' + text, artifact, 'experiment'), name) for name, text in checks]
    target = record(client, root, '数值可靠性专项复核', '演示规则：三项检查中至少两项报告异常时启动专项复核；不是科学成立判据，也不是独立复现数量。尚未执行这些检查。', artifact)
    return condition(client, root, '三项异常中至少两项触发复核', 'k-of-N', members, target,
                     '三项数值检查中至少两项报告异常时，启动数值可靠性专项复核。',
                     '这是为展示 k-of-N 新提出的复核触发规则，阈值未经研究验证；它不能用来宣布轨道结论正确。',
                     artifact, 'v8 §6 回退：若数值不稳定，降低时间步长或改用辛积分器；§8 数值误差风险。三项检查组合与 k=2 是演示新增方案，并非报告原结论。', 2)


REFERENCE_TITLE = '两篇文献联合支持引力波耗散分析'


def seed_references(client, root):
    existing = client.get(root + '/joint-conditions').json()
    if any(c['title'] == REFERENCE_TITLE for c in existing):
        return
    artifact = post(client, root + '/artifacts', {'content': (ROOT / 'evidence/contest-2026/q049/v8.md').read_text(), 'media_type': 'text/plain'})['id']
    s4 = record(client, root, 'S4 · Peters & Mathews (1963)',
                'Gravitational Radiation from Point Masses in a Keplerian Orbit\n\nDOI: [10.1103/PhysRev.131.435](https://doi.org/10.1103/PhysRev.131.435)\n\n提供引力波辐射功率公式的文献依据。来源信息沿用 q049 v8；原报告注明未提取全文，本次没有重新核验论文。', artifact, 'source')
    s5 = record(client, root, 'S5 · Peters (1964)',
                'Gravitational Radiation and the Motion of Two Point Masses\n\nDOI: [10.1103/PhysRev.136.B1224](https://doi.org/10.1103/PhysRev.136.B1224)\n\n提供轨道演化与衰减时间公式的文献依据。来源信息沿用 q049 v8；原报告注明未提取全文，本次没有重新核验论文。', artifact, 'source')
    target = record(client, root, '地球—太阳引力波耗散尺度',
                    '研究方向：以辐射功率和轨道衰减时间两部分分析引力波耗散。q049 v8 §7 已记录圆轨道计算约 196 W、1.069×10²³ 年。这里新增文献关系投影，没有新实验；不外推为潮汐可忽略或多体系统永远稳定。', artifact)
    condition(client, root, REFERENCE_TITLE, 'AND', [(s4, '辐射功率依据'), (s5, '轨道演化依据')], target,
              '在地球—太阳圆轨道近似下，同时给出引力波辐射功率及其对应的轨道衰减时间尺度。',
              '两篇文献分别承担功率公式与轨道演化公式的依据，共同覆盖该方向的两个论证环节。文献数量不是独立复现次数；其他耗散机制与混沌稳定性不在这条关系的支撑范围。',
              artifact, 'q049 v8 §3 S4/S5 来源记录；§4 Direction 2；§7 已执行引力波计算。原报告说明全文访问受限；本次只增加关系表达。')


def seed(client):
    projects = client.get('/api/v1/projects').json()
    existing = next((p for p in projects if p['name'] == NAME), None)
    if existing:
        root = f'/api/v1/projects/{existing["id"]}'
        seed_references(client, root)
        seed_semantic_loop(client, root)
        return existing['id']
    project = post(client, '/api/v1/projects', {'name': NAME, 'question': '行星轨道为何不持续衰减？以历史 q049 报告展示联合条件；不新增科学实验结果。'})
    root = f'/api/v1/projects/{project["id"]}'
    artifact = post(client, root + '/artifacts', {'content': (ROOT / 'evidence/contest-2026/q049/v8.md').read_text(), 'media_type': 'text/plain'})['id']
    for create in (seed_and, seed_or, seed_threshold):
        create(client, root, artifact)
    seed_references(client, root)
    seed_semantic_loop(client, root)
    return project['id']


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', default='http://127.0.0.1:8095')
    args = parser.parse_args()
    with httpx.Client(base_url=args.url, timeout=30) as client:
        print(seed(client))
