// THROWAWAY PROTOTYPE: host + switcher for the 10 kimi variants on /prototype/kimi?v=.
import { Suspense, lazy, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { ChevronLeft, ChevronRight } from "lucide-react";
import "./kimi.css";

const VARIANTS = [
  { id: "01", name: "深海玻璃", en: "Deep-Sea Glass", logic: "图谱即桌面", load: lazy(() => import("./v01-deep-sea")) },
  { id: "02", name: "ASCII 原子终端", en: "Atom Terminal", logic: "键盘优先 CLI", load: lazy(() => import("./v02-atom-terminal")) },
  { id: "03", name: "任务控制", en: "Mission Control", logic: "监控优先", load: lazy(() => import("./v03-mission-control")) },
  { id: "04", name: "活手稿", en: "Living Manuscript", logic: "阅读写作优先", load: lazy(() => import("./v04-living-manuscript")) },
  { id: "05", name: "看板分流", en: "Kanban Triage", logic: "分诊优先", load: lazy(() => import("./v05-kanban-triage")) },
  { id: "06", name: "对话编排", en: "Chat Orchestrator", logic: "会话优先", load: lazy(() => import("./v06-chat-orchestrator")) },
  { id: "07", name: "蓝图 CAD", en: "Blueprint", logic: "图优先+精密详图", load: lazy(() => import("./v07-blueprint-cad")) },
  { id: "08", name: "星图天文台", en: "Observatory", logic: "缩放导航", load: lazy(() => import("./v08-observatory")) },
  { id: "09", name: "积木桌面", en: "Bento Desktop", logic: "可组合桌面", load: lazy(() => import("./v09-bento-desktop")) },
  { id: "10", name: "实验日志", en: "Lab Journal", logic: "时间优先", load: lazy(() => import("./v10-lab-journal")) },
];

function isTyping(target) {
  return target.closest("input, textarea, select, [contenteditable]");
}

export function KimiPrototype() {
  const [params, setParams] = useSearchParams();
  const index = Math.max(0, VARIANTS.findIndex((v) => v.id === (params.get("v") || "01")));
  const current = VARIANTS[index];

  const go = (next) => {
    const wrapped = (next + VARIANTS.length) % VARIANTS.length;
    setParams({ v: VARIANTS[wrapped].id }, { replace: true });
  };

  useEffect(() => {
    const onKey = (event) => {
      if (isTyping(event.target)) return;
      if (event.key === "ArrowLeft") go(index - 1);
      if (event.key === "ArrowRight") go(index + 1);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  });

  const Current = current.load;
  return <div className="kimi-host">
    <Suspense fallback={<div className="kimi-loading">载入 {current.en}…</div>}><Current /></Suspense>
    {import.meta.env.DEV && <nav className="kimi-switcher" aria-label="prototype variant switcher">
      <button onClick={() => go(index - 1)} aria-label="上一套"><ChevronLeft size={16} /></button>
      <div className="kimi-switcher-label">
        <b>V{current.id} · {current.name}</b>
        <span>{current.en} — {current.logic}</span>
        <div className="kimi-switcher-dots">
          {VARIANTS.map((v, i) => <button key={v.id} className={i === index ? "on" : ""} onClick={() => go(i)} title={`V${v.id} ${v.name}`}>{v.id}</button>)}
        </div>
      </div>
      <button onClick={() => go(index + 1)} aria-label="下一套"><ChevronRight size={16} /></button>
    </nav>}
  </div>;
}
