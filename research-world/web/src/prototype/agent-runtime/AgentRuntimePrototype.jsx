// THROWAWAY PROTOTYPE: issue #63 Agent Runtime settings contract.
import { AgentRail } from "./AgentRail";
import { AgentWorkspace } from "./AgentWorkspace";
import { DeleteDialog, DraftDialog, PrepareDrawer } from "./Overlays";
import { Notice } from "./shared";
import { usePrototypeState } from "./usePrototypeState";
import "./agent-runtime-prototype.css";

export function AgentRuntimePrototype() {
  const state = usePrototypeState();
  return <div className="arp-shell"><AgentRail state={state} /><AgentWorkspace state={state} /><DraftDialog state={state} /><PrepareDrawer state={state} /><DeleteDialog state={state} /><Notice state={state} /></div>;
}
