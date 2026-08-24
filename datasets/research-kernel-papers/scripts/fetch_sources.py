#!/usr/bin/env python3
import hashlib,json,subprocess,time,urllib.parse,urllib.request,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ARXIV={'a':'http://www.w3.org/2005/Atom','x':'http://arxiv.org/schemas/atom'}
def text(node): return ' '.join(''.join(node.itertext()).split()) if node is not None else ''
def sha256(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def load_seed(): return json.loads((ROOT/'sources.seed.json').read_text())['sources']
def arxiv_metadata(sources):
    ids=','.join(item['providerId'] for item in sources)
    query=urllib.parse.urlencode({'id_list':ids,'max_results':len(sources)})
    root=ET.fromstring(urllib.request.urlopen(f'https://export.arxiv.org/api/query?{query}',timeout=90).read())
    return {entry.findtext('a:id','',ARXIV).split('/abs/')[-1].rsplit('v',1)[0]:entry for entry in root.findall('a:entry',ARXIV)}
def arxiv_record(item,entry):
    authors=[text(node) for node in entry.findall('a:author/a:name',ARXIV)]
    published=entry.findtext('a:published','',ARXIV)
    license_node=entry.find('x:license',ARXIV)
    license_text=license_node.attrib.get('href','') if license_node is not None else 'not declared in arXiv Atom metadata'
    return base_record(item,text(entry.find('a:title',ARXIV)),authors,published[:4],text(entry.find('a:summary',ARXIV)),license_text)
def pmc_record(item,root):
    authors=[text(node) for node in root.findall('.//contrib-group/contrib/name')]
    collabs=[text(node) for node in root.findall('.//contrib-group/contrib/collab')]
    title=text(root.find('.//article-title')); year=root.findtext('.//pub-date/year','')
    abstract=' '.join(dict.fromkeys(text(node) for node in root.findall('.//abstract//p')))
    license_node=root.find('.//permissions/license'); license_text=text(license_node)
    return base_record(item,title,authors or collabs,year,abstract,license_text[:240])
def base_record(item,title,authors,year,abstract,license_text):
    suffix='paper.pdf' if item['provider']=='arxiv' else 'fulltext.xml'
    url=f"https://arxiv.org/abs/{item['providerId']}" if item['provider']=='arxiv' else f"https://pmc.ncbi.nlm.nih.gov/articles/{item['providerId']}/"
    return {**item,'title':title,'authors':authors,'year':int(year),'abstract':abstract,'sourceUrl':url,'localPath':f"raw/{item['id']}/{suffix}",'license':license_text}
def download(url,target,kind):
    if target.exists() and target.stat().st_size>1000: return
    target.parent.mkdir(parents=True,exist_ok=True); temp=target.with_suffix(target.suffix+'.part')
    subprocess.run(['curl','-sS','-L','--fail','--retry','5','--retry-all-errors','--max-time','180','-A','ai4sci-research-corpus/1.0',url,'-o',str(temp)],check=True)
    head=temp.read_bytes()[:512]; valid=head.startswith(b'%PDF') if kind=='pdf' else b'<article' in head
    if not valid: raise ValueError(f'invalid {kind}: {url}')
    temp.replace(target); time.sleep(.4)
def fetch_one(item):
    target=ROOT/'raw'/item['id']/('paper.pdf' if item['provider']=='arxiv' else 'fulltext.xml')
    url=f"https://arxiv.org/pdf/{item['providerId']}" if item['provider']=='arxiv' else f"https://www.ebi.ac.uk/europepmc/webservices/rest/{item['providerId']}/fullTextXML"
    download(url,target,'pdf' if item['provider']=='arxiv' else 'xml'); return target
def manifest(records):
    fields=('id','category','provider','providerId','title','authors','year','sourceUrl','localPath','sha256','license')
    return {'version':2,'frozenAt':'2026-08-18','papers':[{key:item[key] for key in fields} for item in records]}
def main():
    sources=load_seed(); arxiv_sources=[item for item in sources if item['provider']=='arxiv']; entries=arxiv_metadata(arxiv_sources)
    records=[]
    for index,item in enumerate(sources,1):
        path=fetch_one(item)
        record=arxiv_record(item,entries[item['providerId']]) if item['provider']=='arxiv' else pmc_record(item,ET.parse(path).getroot())
        record['sha256']=sha256(path); records.append(record); print(f"[{index:02d}/{len(sources)}] {item['id']}")
    (ROOT/'metadata.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
    (ROOT/'manifest.json').write_text(json.dumps(manifest(records),ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__': main()
