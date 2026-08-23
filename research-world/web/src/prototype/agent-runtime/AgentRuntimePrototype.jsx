// THROWAWAY PROTOTYPE: three Agent/Runtime inventory variants on /prototype/agent-runtime?variant=A|B|C.
import { ChevronLeft, ChevronRight } from "lucide-react";
import { useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { Notice, StatePeek } from "./shared";
import { usePrototypeState } from "./usePrototypeState";
import { VariantA } from "./VariantA";
import { VariantB } from "./VariantB";
import { VariantC } from "./VariantC";
import "./agent-runtime-prototype.css";

const VARIANTS = { A: "清单优先", B: "引导式配置", C: "能力目录" };

export function AgentRuntimePrototype() {
  const [params, setParams] = useSearchParams();
  const variant = VARIANTS[params.get("variant")] ? params.get("variant") : "A";
  const state = usePrototypeState();
  useVariantKeys(variant, params, setParams);
  return <div className="ar-prototype">{variant === "A" && <VariantA state={state} />}
    {variant === "B" && <VariantB state={state} />}{variant === "C" && <VariantC state={state} />}
    <Notice state={state} /><StatePeek state={state} />
    <Switcher variant={variant} params={params} setParams={setParams} /></div>;
}

function Switcher({ variant, params, setParams }) {
  const move = (delta) => cycleVariant(variant, delta, params, setParams);
  return <nav className="ar-switcher" aria-label="原型方案切换"><button onClick={() => move(-1)} aria-label="上一方案"><ChevronLeft size={16} /></button>
    <b>{variant} · {VARIANTS[variant]}</b><button onClick={() => move(1)} aria-label="下一方案"><ChevronRight size={16} /></button></nav>;
}

function cycleVariant(variant, delta, params, setParams) {
  const keys = Object.keys(VARIANTS);
  const next = keys[(keys.indexOf(variant) + delta + keys.length) % keys.length];
  const updated = new URLSearchParams(params);
  updated.set("variant", next);
  setParams(updated, { replace: true });
}

function useVariantKeys(variant, params, setParams) {
  useEffect(() => {
    const handler = (event) => {
      if (!["ArrowLeft", "ArrowRight"].includes(event.key) || event.target.closest("input, textarea, select, [contenteditable]")) return;
      cycleVariant(variant, event.key === "ArrowLeft" ? -1 : 1, params, setParams);
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [variant, params, setParams]);
}
