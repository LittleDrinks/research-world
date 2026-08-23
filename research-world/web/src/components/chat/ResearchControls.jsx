import { Workflow, X } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { LaunchControl } from "./LaunchControl";
import { RunCard } from "./RunCard";


function useDismiss(open, root, trigger, close) {
  useEffect(() => {
    if (!open) return undefined;
    const dismiss = (event) => {
      if (event.type === "keydown" && event.key !== "Escape") return;
      if (event.type === "pointerdown" && root.current?.contains(event.target)) return;
      close(); requestAnimationFrame(() => trigger.current?.focus());
    };
    document.addEventListener("keydown", dismiss);
    document.addEventListener("pointerdown", dismiss);
    return () => { document.removeEventListener("keydown", dismiss); document.removeEventListener("pointerdown", dismiss); };
  }, [open, close]);
}


export function ResearchControls({ thread, runs }) {
  const [open, setOpen] = useState(false);
  const [hidden, setHidden] = useState(() => new Set());
  const root = useRef(null);
  const trigger = useRef(null);
  const close = useCallback(() => setOpen(false), []);
  useDismiss(open, root, trigger, close);
  const visible = runs.filter((run) => !hidden.has(run.id));
  const hide = (runId) => setHidden((value) => new Set([...value, runId]));
  return <div className="research-controls" ref={root}>
    <button ref={trigger} className="composer-tool" aria-label="研究运行" aria-expanded={open}
      onClick={() => setOpen(!open)}><Workflow size={15} /><span>研究运行</span><em>{visible.length}</em></button>
    {open && <ResearchPopover thread={thread} runs={visible} hidden={hidden} hide={hide}
      restore={() => setHidden(new Set())} close={close} />}
  </div>;
}


function ResearchPopover({ thread, runs, hidden, hide, restore, close }) {
  return <section className="research-popover" role="dialog" aria-label="研究运行与流程">
    <header><b>研究运行</b><button className="icon-button" aria-label="关闭研究运行" onClick={close}><X size={15} /></button></header>
    <LaunchControl thread={thread} />
    <div className="research-popover-runs">
      {runs.map((run) => <RunCard key={run.id} run={run} threadId={thread.id} onDismiss={hide} />)}
      {!runs.length && <p className="record-empty">当前对话没有运行</p>}
      {hidden.size > 0 && <button className="run-restore" onClick={restore}>恢复已移出的 {hidden.size} 项</button>}
    </div>
  </section>;
}
