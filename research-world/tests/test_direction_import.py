import json
from pathlib import Path

import pytest

from server.importing.corpus import corpus
from server.importing.directions import import_directions,load_directions
from server.importing.writer import Writer
from server.kernel_interface import create_kernel

ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'research-world/evidence/contest-2026'


def test_q120_three_independent_directions_preserve_arguments():
    directions=load_directions(EVIDENCE,'q120')['directions']
    assert [d['title'] for d in directions]==['生物基质必要论','功能主义路径','关系性意识模型']
    for i,direction in enumerate(directions,1):
        assert f'Direction {i}：' in direction['text']
        assert all(f'Direction {j}：' not in direction['text'] for j in range(1,4) if j!=i)
        assert '可区分预测' in direction['text'] and '比较选择' not in direction['text']


def test_discontinuous_evidence_stays_with_its_direction():
    directions=load_directions(EVIDENCE,'q029')['directions']
    for direction,phrase in zip(directions,['HARs证据来自','基因重复方向证据包括','ARHGAP11B方向证据显示']):
        assert phrase in direction['text'] and len(direction['source_spans'])==2
    assert '基因重复方向证据包括' not in directions[2]['text']


def test_source_drift_is_rejected(tmp_path):
    (tmp_path/'all').mkdir();(tmp_path/'all/q120.md').write_text('changed')
    (tmp_path/'direction-spans.json').write_bytes((EVIDENCE/'direction-spans.json').read_bytes())
    with pytest.raises(ValueError,match='source changed'):load_directions(tmp_path,'q120')


def test_full_corpus_builds_distinct_directions_without_duplication(tmp_path):
    kernel=create_kernel(tmp_path/'database',tmp_path/'artifacts');writer=Writer(kernel,ROOT)
    for item in corpus(ROOT):
        project=writer.project(item['qid'],item['question']);spec=item['directions']
        question=writer.record(project,'question','question',{'text':item['question']})
        artifact=writer.file(project,EVIDENCE/spec['path'])
        key='all/'+item['qid'] if spec['path'].startswith('all/') else spec['path']
        report=writer.record(project,key,'source',{'text':'Original report'},(artifact.id,))
        import_directions(writer,project,question,item);count=writer.created
        import_directions(writer,project,question,item)
        assert writer.created==count
        directions=[r for r in kernel.list_records(project.id) if r.type=='direction']
        assert len(directions)==3 and len({r.content['title'] for r in directions})==3
        assert all(r.content['verified'] is False and len(r.content['text'])>60 for r in directions)
        edges=kernel.list_relations(project.id)
        assert len(edges)==6 and all(e.target_id in {question.id,report.id} and e.type=='depends_on' for e in edges)
