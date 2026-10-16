import argparse
import json
from pathlib import Path

from .config import load_settings
from .kernel_interface import create_kernel
from .importing.corpus import corpus,raw_sessions,sessions_for
from .importing.writer import Writer,import_project


def main():
    parser=argparse.ArgumentParser(description='Import the archived 125-question research corpus')
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--inventory',type=Path,required=True)
    parser.add_argument('--ids',nargs='+')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    selected=[item for item in corpus(args.source) if not args.ids or item['qid'] in args.ids]
    index=raw_sessions(args.inventory,args.source)
    if any(sessions_for(item,index)[1] for item in selected):raise ValueError("Required trajectories missing")
    settings=load_settings();kernel=create_kernel(settings.database,settings.artifacts)
    writer=Writer(kernel,args.source)
    results=[import_project(writer,item,index) for item in selected]
    value={'projects':results,'created_records':writer.created}
    args.output.write_text(json.dumps(value,ensure_ascii=False,indent=2))
    print(json.dumps({'projects':len(results),'created_records':writer.created}))


if __name__=='__main__':main()
