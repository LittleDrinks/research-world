// THROWAWAY PROTOTYPE: issue #63 Agent Runtime settings contract.
import { AgentRail } from "./AgentRail";
import { AgentWorkspace } from "./AgentWorkspace";
import { DeleteDialog, DraftDialog, PrepareDrawer } from "./Overlays";
import { Notice } from "./shared";
import { TracePagePrototype } from "./TracePagePrototype";
import { usePrototypeState } from "./usePrototypeState";
import "./agent-runtime-prototype.css";

export function AgentRuntimePrototype() {
  if (new URLSearchParams(window.location.search).get("view") === "trace") return <TracePagePrototype />;
  return <AgentRuntimeSetup />;
}

function AgentRuntimeSetup() {
  const state = usePrototypeState();
  return <div className="arp-shell"><AgentRail state={state} /><AgentWorkspace state={state} /><DraftDialog state={state} /><PrepareDrawer state={state} /><DeleteDialog state={state} /><Notice state={state} /></div>;
}
