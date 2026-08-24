#!/usr/bin/env python3
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; GRAPHS=ROOT/'graphs'
CURATED={'kepler-proof','matbench','solar-chaos','gw150914','petase','amr','sleep-eeg'}
LABELS={'formal-proof':('Formal verification','Formal proof'),'benchmark':('Scientific machine learning','Benchmark'),'numerical-simulation':('Computational science','Numerical simulation'),'observation':('Observational science','Observation'),'wet-lab':('Experimental biology','Wet lab'),'human-clinical':('Human and clinical research','Human / clinical')}
TITLES={'formal-proof':('Fix the formal system','Machine-check the proof'),'benchmark':('Freeze tasks and metrics','Evaluate reference systems'),'numerical-simulation':('Choose model and boundary conditions','Run the numerical experiment'),'observation':('Choose instrument and selection','Acquire and analyze observations'),'wet-lab':('Choose construct and controls','Run assays against controls'),'human-clinical':('Choose cohort and endpoint','Measure human outcomes')}
METHOD_WORDS=('using','we use','we develop','we construct','we perform','we formal','we implement','random','dataset','simulation','observ','measur','trial','participants','sample','model')
RESULT_WORDS=('we find','we found','we show','we prove','we demonstrate','our results','there were','was observed','were observed','achieved','outperform','estimated','significant','accuracy','improved','revealed','proved','conferred','reduced','increased','lower than','higher than')
EVIDENCE_WORDS={'formal-proof':('formal proof','formaliz','proof assistant','machine-check','verified','theorem'),'benchmark':('benchmark','baseline','tasks','dataset','samples','performance','accuracy','outperform','improvement'),'numerical-simulation':('reproduces','predicts','skill','outperform','faster','resolution','simulation','results'),'observation':('detected','detection','significance','sigma','measured','observed','evidence','mass','distance'),'wet-lab':('activity','correction','cells','mutant','kill','folding','expression','degradation','inhibit'),'human-clinical':('hazard','rate ratio','confidence interval','95% ci','deaths','cases','participants','efficacy','no benefit','associated')}
CLAIM_OVERRIDES={'atom3d':'Our results indicate that many molecular problems stand to gain from three-dimensional molecular learning, and that there is potential for improvement on many tasks which remain underexplored.','protein-folding-stability':'The cDNA display proteolysis method is fast, accurate and uniquely scalable, and promises to reveal the quantitative rules for how amino acid sequences encode folding stability.','dexamethasone':'In patients hospitalized with Covid-19, the use of dexamethasone resulted in lower 28-day mortality among those who were receiving either invasive mechanical ventilation or oxygen alone at randomization but not among those receiving no respiratory support.','empagliflozin-ckd':'Empagliflozin reduced the risk of the composite outcome of kidney disease progression or cardiovascular death in a wide range of patients at risk of CKD progression.','uk-biobank':'Deep phenotype and genome-wide genetic data from 500,000 individuals from the UK Biobank, describing population structure and relatedness in the cohort, and imputation to increase the number of testable variants to 96 million.'}
QUESTION={'formal-proof':'How is the reported theorem converted into a machine-checkable proof?','benchmark':'How can the target scientific task be compared under fixed data and evaluation rules?','numerical-simulation':'What does the reported model reveal when the target system is simulated?','observation':'What phenomenon is supported by the reported observations?','wet-lab':'Which intervention or mechanism produces the reported experimental effect?','human-clinical':'What effect or association is supported in the studied human population?'}
def sentences(text):
    parts=re.split(r'(?<!vs\.)(?<!i\.e\.)(?<!e\.g\.)(?<=[.!?])\s+(?=[A-Z0-9])',' '.join(text.split()))
    return [part for part in parts if len(part)>35]
def score(sentence,words):
    metric=bool(re.search(r'(?:%|±|\bci\b|confidence interval|hazard ratio|rate ratio|\d[\d,.]*\s*(?:million|participants|cases|deaths|samples|mpc|hours|days|years))',sentence.lower()))
    return 2*sum(word in sentence.lower() for word in words)+metric
def choose(items,words,used,reverse=False):
    choices=[(score(item,words),index,item) for index,item in enumerate(items) if item not in used and not is_metadata(item)]
    choices.sort(key=lambda row:(row[0],row[1] if reverse else -row[1]),reverse=True)
    return choices[0][2] if choices else ''
def is_metadata(sentence): return any(word in sentence.lower() for word in ('funded by','clinicaltrials.gov','trial registration','copyright ©','keywords:','available at http','github.com'))
def paper_block(record):
    domain,modality=LABELS[record['category']]; authors=', '.join(record['authors'][:3])+(' et al.' if len(record['authors'])>3 else '')
    short=record['title'].split(':')[0][:62]
    return {'id':record['id'],'title':record['title'],'shortTitle':short,'authors':authors,'year':record['year'],'domain':domain,'modality':modality,'category':record['category'],'sourceUrl':record['sourceUrl'],'localPath':record['localPath']}
def node(nid,kind,title,body,provenance,state): return {'id':nid,'kind':kind,'title':title,'body':body,'provenance':provenance,'locator':'Abstract','state':state}
def select_content(record):
    items=sentences(record['abstract']); used=set(); claims=[item for item in items if not is_metadata(item)]
    if record['id'] in CLAIM_OVERRIDES: claim=CLAIM_OVERRIDES[record['id']]
    elif record['category']=='formal-proof': claim=choose(items,EVIDENCE_WORDS['formal-proof'],used)
    else: claim=claims[-1]
    used.add(claim)
    evidence=choose(items,RESULT_WORDS+EVIDENCE_WORDS[record['category']],used,True) or choose(items,(),used,True); used.add(evidence)
    method=choose(items,METHOD_WORDS,used); used.add(method)
    investigation=choose(items,METHOD_WORDS,used)
    return method,investigation,evidence or items[0],claim
def inferred_investigation(record): return f"The graph treats the study's reported {LABELS[record['category']][1].lower()} procedure as the investigation that tests its central claim."
def inferred_decision(record): return f"The graph treats the paper's declared {LABELS[record['category']][1].lower()} scope as a reconstructed design decision."
def generated_graph(record):
    prefix=record['id']; method,investigation,evidence,claim=select_content(record); decision_title,investigation_title=TITLES[record['category']]
    decision_body=method or inferred_decision(record); decision_source='explicit' if method else 'inferred'
    investigation_body=investigation or inferred_investigation(record); investigation_source='explicit' if investigation else 'inferred'
    nodes=[node(f'{prefix}-q','question','Research question',QUESTION[record['category']],'inferred','open'),node(f'{prefix}-d','decision',decision_title,decision_body,decision_source,'accepted'),node(f'{prefix}-i','investigation',investigation_title,investigation_body,investigation_source,'completed'),node(f'{prefix}-e','evidence','Primary reported result',evidence,'explicit','supporting'),node(f'{prefix}-c','claim','Published conclusion',claim,'explicit','supported')]
    edges=[{'from':f'{prefix}-q','to':f'{prefix}-d','relation':'motivates','provenance':'inferred'},{'from':f'{prefix}-d','to':f'{prefix}-i','relation':'constrains','provenance':'inferred'},{'from':f'{prefix}-i','to':f'{prefix}-e','relation':'produces','provenance':'explicit'},{'from':f'{prefix}-e','to':f'{prefix}-c','relation':'supports','provenance':'inferred'}]
    return {'paper':paper_block(record),'thesis':claim,'reconstruction':{'scope':'abstract-level graph with retained full text','method':'deterministic sentence selection','review':'schema-audited'},'nodes':nodes,'edges':edges,'openQuestions':['The local full text supports deeper section-level extraction beyond this abstract-level graph.']}
def enrich_curated(record,path):
    graph=json.loads(path.read_text()); graph['paper']['category']=record['category']; graph['paper']['providerId']=record['providerId']; graph['reconstruction']={'scope':'section-level manual graph','method':'manual source review','review':'manually curated'}
    path.write_text(json.dumps(graph,ensure_ascii=False,indent=2)+'\n')
def main():
    records=json.loads((ROOT/'metadata.json').read_text()); GRAPHS.mkdir(exist_ok=True)
    for record in records:
        path=GRAPHS/f"{record['id']}.json"
        if record['id'] in CURATED: enrich_curated(record,path)
        else: path.write_text(json.dumps(generated_graph(record),ensure_ascii=False,indent=2)+'\n')
        print(record['id'])
if __name__=='__main__': main()
