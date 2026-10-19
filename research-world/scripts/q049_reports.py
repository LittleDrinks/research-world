"""Readable outputs for the executed q049 component experiments."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / 'benchmarks/research-changes-385'


def coverage(manifest):
    base = 'http://localhost:8095/projects/' + manifest['project_id']
    records = {key: base + '/records/' + rid for key, rid in manifest['records'].items()}
    rows = [('联合依据', 'methods', '两篇论文共同约束方法检查；AND及原文定位'),
            ('竞争解释', 'drift', 'OR、数值误差支持与物理耗散反驳的适用范围'),
            ('预算选择', 'budget', '3个配额选2项；k-of-N与可行组合'),
            ('数值复算', 'radiation', '功率与时标；代码、参数和结果'),
            ('积分实验', 'drift', '两种积分器、三种步长；误差曲线和CSV'),
            ('版本讨论', 'numeric', '当前判断、证据、修订差异与固定版本评论'),
            ('下一轮检查', 'resolution', '规划输入与预算依据'),
            ('研究缺口', 'physical', '用户标签和解释适用范围')]
    text = '# q049 组件与研究语义\n\n| 模块 | 内容与结果 | 入口 |\n| --- | --- | --- |\n'
    text += '\n'.join(f'| {name} | {content} | [打开]({records[key]}) |' for name, key, content in rows)
    return text + f"\n| 文献筛选 | MMR的输入、选择顺序与扣分 | [结果](http://localhost:8095{manifest['mmr'][0]['view_url']}) |\n"


def reports():
    values = json.loads((ROOT/'experiments/results.json').read_text())
    return {'radiation': radiation(values['radiation']), 'integration': integration(values['integration']),
            'budget': budget(values['budget']), 'papers': papers()}


def radiation(value):
    return f'''# 地球—太阳引力波尺度复算
孤立双体、圆轨道、固定质量；输入采用 SI 单位。

| 量 | 计算结果 |
| --- | ---: |
| 辐射功率 | {value['power_W']:.6f} W |
| Peters 形式并合时间 | {value['merge_years']:.6e} 年 |
| 局部能量时标 | {value['local_energy_years']:.6e} 年 |
| 局部时标 / 并合时间 | {value['local_to_merge_ratio']:.6f} |

瞬时功率与积分得到的时间描述不同物理量。局部能量时标为形式并合时间的四倍，符合该圆轨道模型的积分关系。

公式、常数与单位保存在计算代码和 results.json 中。太阳演化、潮汐及多体扰动不在这次方程组内。
'''


def integration(rows):
    table='\n'.join(f"| {r['method']} | {r['steps_per_orbit']} | {r['max_relative_energy_error']:.6e} | {r['seconds']:.6f} |" for r in rows)
    return f'''# 积分器与步长对照
方程：GM=1，初始位置(1,0)、速度(0,1)，积分30个轨道周期。方程中没有耗散项。

| 方法 | 每圈步数 | 最大相对能量误差 | 本次耗时 / 秒 |
| --- | ---: | ---: | ---: |
{table}

Euler 产生明显能量漂移；Leapfrog 在相同模型和分辨率下误差显著较小，减小步长后继续下降。因此，这组结果支持数值误差解释，排除了“该次漂移必须由物理耗散导致”的解释。

下一步分别检查更小步长、更长积分和初值扰动。
'''


def budget(value):
    return '''# 计算配额下的实验选择
预算输入为3个规划配额，至少选择2项检查。配额用于比较工作包，不是实付费用。

| 候选实验 | 配额 | 是否选中 |
| --- | ---: | --- |
| 加倍时间分辨率 | 1 | 是 |
| 延长积分时间 | 2 | 是 |
| 初值扰动集合 | 3 | 否 |

枚举全部两项组合后，只有“分辨率＋积分时长”满足预算。地图上的2-of-3表达至少完成两项检查；费用约束由预算计算结果提供。

三项均为下一轮工作计划，选择结果保存在 results.json 的 budget 部分。
'''


def papers():
    return '''# 两篇论文如何共同约束数值检查
| 来源 | 已核对位置 | 对研究方向的贡献 |
| --- | --- | --- |
| Rein & Tamayo, WHFast | arXiv:1506.01084 PDF第1页摘要、第2页误差讨论 | 算法实现中的偏差与舍入误差会影响长期能量误差；需要检查积分实现 |
| Rein & Spiegel, IAS15 | arXiv:1409.4779v2 PDF第1页摘要、第2页方法讨论 | 高阶方法、步长控制和误差来源需要共同检查；仅看“是否辛”不足以描述数值表现 |

联合研究方向：同时检查积分方法和误差控制，再解释轨道数值结果。两篇论文共享一位作者，这里组合的是方法依据，不把它们计作两次独立复现。

当前代码比较Euler与Leapfrog；论文中的WHFast和IAS15实现不包含在本次运行中。

[WHFast原文](https://arxiv.org/pdf/1506.01084) · [IAS15原文](https://arxiv.org/pdf/1409.4779)
'''
