#!/usr/bin/env python3
import hashlib,json,sys,xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; REQUIRED={'question','decision','investigation','evidence','claim'}
def fail(errors,message): errors.append(message); print(f'FAIL {message}')
def check_source(record,errors):
    path=ROOT/record['localPath']
    if not path.exists(): fail(errors,f"{record['id']}: source missing")
    elif hashlib.sha256(path.read_bytes()).hexdigest()!=record['sha256']: fail(errors,f"{record['id']}: hash mismatch")
    elif record['provider']=='arxiv' and not path.read_bytes().startswith(b'%PDF'): fail(errors,f"{record['id']}: invalid PDF")
    elif record['provider']=='pmc':
        try: ET.parse(path)
        except ET.ParseError: fail(errors,f"{record['id']}: invalid XML")
def check_graph(record,graph,errors):
    pid=record['id']; nodes=graph.get('nodes',[]); ids={node.get('id') for node in nodes}
    if graph.get('paper',{}).get('category')!=record['category']: fail(errors,f'{pid}: category mismatch')
    if not REQUIRED.issubset({node.get('kind') for node in nodes}): fail(errors,f'{pid}: missing node kind')
    if len(ids)!=len(nodes): fail(errors,f'{pid}: duplicate node id')
    for node in nodes:
        if node.get('provenance') not in {'explicit','inferred'} or not node.get('locator'): fail(errors,f"{pid}: invalid node {node.get('id')}")
        if graph.get('reconstruction',{}).get('review')=='schema-audited' and node.get('provenance')=='explicit' and node.get('body') not in record['abstract']: fail(errors,f"{pid}: explicit text not in abstract")
    for edge in graph.get('edges',[]):
        if edge.get('from') not in ids or edge.get('to') not in ids or edge.get('provenance') not in {'explicit','inferred'}: fail(errors,f'{pid}: invalid edge')
    bodies=[node['body'] for node in nodes]
    if len(bodies)!=len(set(bodies)): fail(errors,f'{pid}: duplicate node body')
def main():
    records=json.loads((ROOT/'metadata.json').read_text()); errors=[]; counts=Counter(item['category'] for item in records)
    if len(records)<60 or set(counts.values())!={10}: fail(errors,f'category counts {dict(counts)}')
    manifest=json.loads((ROOT/'manifest.json').read_text())['papers']; expected={(item['id'],item['sha256']) for item in records}; actual={(item['id'],item['sha256']) for item in manifest}
    if expected!=actual: fail(errors,'manifest differs from metadata')
    if any(len(item.get('abstract',''))<100 for item in records): fail(errors,'abstract missing')
    if any(not item.get('license') for item in records): fail(errors,'license metadata missing')
    for record in records:
        check_source(record,errors); path=ROOT/'graphs'/f"{record['id']}.json"
        if not path.exists(): fail(errors,f"{record['id']}: graph missing"); continue
        check_graph(record,json.loads(path.read_text()),errors)
    graph_ids={path.stem for path in (ROOT/'graphs').glob('*.json')}; record_ids={item['id'] for item in records}
    if graph_ids!=record_ids: fail(errors,f'graph set differs: {sorted(graph_ids^record_ids)}')
    if list(ROOT.glob('raw/**/*.part')): fail(errors,'partial downloads remain')
    print(json.dumps({'papers':len(records),'categories':counts,'errors':len(errors)},default=dict,indent=2)); return bool(errors)
if __name__=='__main__': sys.exit(main())
