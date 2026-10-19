"""Publish the historical q049 audit as a bounded, readable Artifact."""
import argparse
import json
from pathlib import Path

import httpx


def data_for(template, record):
    data = template['example'] | {'title': 'q049 · 引力波计算审计（历史整理）', 'target_artifact_id': record['artifact_ids'][0]}
    data['summary'] = '整理已有 V3 计算报告和 review-v3 独立评审：限定模型内的数值复算通过，概率归因仍需修订。本次仅验证报告发布与阅读流程，没有重新执行计算或独立审计。'
    calculation, review = record['artifact_ids'][:2]
    data['sections'][0].update(markdown='**审计范围：**历史地球—太阳孤立、圆轨道双体近似。\n\n\\[\nP_{\\rm GW}=\\frac{32}{5}\\frac{G^4m_1^2m_2^2(m_1+m_2)}{c^5a^5}\n\\]\n\n该近似下的引力波耗散尺度不能替代真实多体稳定性、潮汐或太阳演化判断。', evidence=evidence(calculation, 'V3 §7：公式、输入与输出'))
    data['sections'][1].update(markdown='下列结果转录自历史评审。展开每项可查看判据和原文定位。', checks=checks(review))
    data['sections'][2].update(markdown='修订 V3 的概率来源归因，并将限定模型计算与真实太阳系预测分开。完整脚本与原始日志应作为独立附件；历史评审注明 V3 未附脚本本体。', evidence=evidence(review, '§三局限与 Finding 1'))
    data['conclusion'] = {'verdict': 'revise', 'markdown': '历史 V3 数值可复现，但概率来源归因需要修订。本报告保留当时的缺陷，不把后续修正倒写为 V3 已通过。'}
    return data


def evidence(artifact, locator):
    return [{'artifact_id': artifact, 'locator': locator}]


def checks(review):
    return [
        check('功率与时间尺度复算', 'check', 'pass', '历史评审独立重算得到 P = 196.291 W、t = 1.069×10²³ 年，与 V3 输出一致。本次未重复执行。', evidence(review, '§三：限定计算独立复算')),
        check('水星失稳概率的来源归因', 'check', 'fail', '历史评审指出：V3 将约 1% 概率归到 Batygin & Laughlin 不成立，需修订归因。单条构造轨迹不能作为概率估计。', evidence(review, 'Finding 1：约 1% 概率归属')),
        check('重新取得并核对全部论文全文', 'check', 'unverified', '本次仅整理历史材料，没有重新获取全文；历史评审的核验范围见原件。', []),
        check('新的多体长期模拟', 'skip', 'not_applicable', '本次是已有计算的报告整理，多体模拟不在审计范围内，不能作为已完成结果。', [])]


def check(label, action, result, reason, evidence):
    return dict(label=label, action=action, result=result, reason=reason, evidence=evidence)


def prepare(client):
    projects = client.get('/api/v1/projects').raise_for_status().json()
    project = next(p for p in projects if p['name'] == 'q049 · 联合条件演示')
    root = f"/api/v1/projects/{project['id']}"
    records = client.get(root + '/records').raise_for_status().json()
    record = next(r for r in records if r['content']['title'] == 'Peters 公式计算 · 历史已执行')
    template = client.get(root + '/artifact-templates').raise_for_status().json()[0]
    return root, record, template, data_for(template, record)


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--url', default='http://localhost:8095')
    parser.add_argument('--output', type=Path, required=True); args = parser.parse_args()
    with httpx.Client(base_url=args.url, timeout=60) as client:
        root, record, template, data = prepare(client)
        args.output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
        body = {'content': json.dumps(data, ensure_ascii=False), 'schema_id': template['id'], 'record_id': record['id']}
        result = client.post(root + '/artifacts', json=body).raise_for_status().json()
        print(json.dumps({'project_id': record['project_id'], 'record_id': record['id'], 'schema_id': template['id'],
                          'artifact_id': result['id'], 'preview': args.url + result['view_url']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
