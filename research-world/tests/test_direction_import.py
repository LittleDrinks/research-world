import json
from pathlib import Path

import pytest

from server.importing.corpus import corpus
from server.importing.directions import import_directions,load_directions
from server.importing.writer import Writer,import_project
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
        result=import_project(writer,item,{})
        count=writer.created;import_project(writer,item,{})
        assert writer.created==count
        records=kernel.list_records(result['project_id'])
        directions=[r for r in records if r.type=='direction']
        assert len(directions)==3 and len({r.content['title'] for r in directions})==3
        assert all(r.content['verified'] is False and len(r.content['text'])>60 for r in directions)
        assert not any(r.content.get('title','').startswith(('历史候选报告','深度案例','历史资料')) for r in records)
        question=next(r for r in records if r.type=='question')
        assert len(question.artifact_ids)>=4
        for direction in directions:
            assert any(e.source_id==direction.id and e.target_id==question.id for e in kernel.list_relations(result['project_id']))
            assert kernel.read_artifact(result['project_id'],direction.artifact_ids[0])==(EVIDENCE/item['directions']['path']).read_bytes()


def test_missing_source_spans_are_rejected():
    from server.importing.directions import _extract
    with pytest.raises(ValueError,match='Empty direction'):
        _extract('original',{'title':'Missing excerpt','spans':[]})


def test_q112_routes_retain_dispersed_conditions_and_evidence():
    routes=load_directions(EVIDENCE,'q112')['directions']
    assert '[S6]' in routes[0]['text'] and 'C_min' in routes[0]['text']
    assert 'not EN 13432 certification requirements' in routes[1]['text']
    assert '[S7]' in routes[2]['text'] and 'N_eff' in routes[2]['text']
    assert 'Remains a hypothesis' in routes[2]['text']
    assert all('No LCA calculations' in route['text'] for route in routes)
    assert all('Economic failure' not in route['text'] for route in routes[:2])
    assert 'Compostable container screening' not in routes[2]['text']


def test_only_explicit_source_ids_create_direction_dependencies(tmp_path):
    kernel=create_kernel(tmp_path/'database',tmp_path/'artifacts');writer=Writer(kernel,ROOT)
    item=next(item for item in corpus(ROOT) if item['qid']=='q049')
    result=import_project(writer,item,{})
    records=kernel.list_records(result['project_id']);edges=kernel.list_relations(result['project_id'])
    sources=[r for r in records if r.type=='source']
    assert sources and all('/v8.md/source/' in r.content['origin']['key'] for r in sources)
    assert all(e.type=='depends_on' for e in edges)
    source_ids={r.id for r in sources}
    assert len([e for e in edges if e.target_id in source_ids])==7
    assert not any(r.content['origin']['key']=='archive' for r in records)
    assert all(r.type=='question' or len(r.artifact_ids)<=1 for r in records)
