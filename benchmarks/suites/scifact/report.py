from html import escape
from pathlib import Path
import json


def report(root):
    rows=[]
    for arm in ('baseline','research'):
        for case in json.loads((root/arm/'cases.json').read_text()):
            rows.append(_row(arm,case))
    body=''.join(rows)
    content=f'''<!doctype html><html lang="zh"><meta charset="utf-8"><title>SciFact 联调</title>
<style>body{{font:16px system-ui;max-width:1100px;margin:40px auto;padding:0 20px}}table{{border-collapse:collapse;width:100%}}td,th{{padding:12px;border-bottom:1px solid #ddd;text-align:left}}a{{margin-right:12px}}</style>
<h1>SciFact 逐题结果</h1><p>训练题联调，不代表正式成绩；没有同等 token 预算，费用未知。NEI 正确拒答的逐题 F1 仍为 0，需同时查看标签匹配。</p>
<table><thead><tr><th>组</th><th>题目</th><th>状态</th><th>标签匹配</th><th>证据句 F1</th><th>秒</th><th>证据</th></tr></thead><tbody>{body}</tbody></table></html>'''
    (root/'report.html').write_text(content)


def _row(arm,case):
    base=f'{arm}/{case["id"]}'
    links=''.join(f'<a href="{base}/{file}">{label}</a>' for file,label in
                  [('answer.txt','答案'),('trajectory.json','轨迹'),('gold.jsonl','标注'),('metrics.json','评分')])
    values=[arm,case['id'],case['status'],case['prediction_matches_gold_labels'],
            round(case['official_metrics']['sentence_label_f1'],3),case['seconds']]
    return '<tr>'+''.join(f'<td>{escape(str(v))}</td>' for v in values)+f'<td>{links}</td></tr>'
