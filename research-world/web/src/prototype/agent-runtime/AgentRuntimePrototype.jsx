// THROWAWAY PROTOTYPE: OpenDesign-inspired Agent runtime and capability discovery.
import { AgentRail, Notice, StatePeek } from "./shared";
import { OpenDesignAgentPanel } from "./OpenDesignAgentPanel";
import { TracePagePrototype } from "./TracePagePrototype";
import { usePrototypeState } from "./usePrototypeState";
import "./agent-runtime-prototype.css";

export function AgentRuntimePrototype() {
  if (new URLSearchParams(window.location.search).get("view") === "trace") return <TracePagePrototype />;
  return <AgentRuntimeSetup />;
}

function AgentRuntimeSetup() {
  const state = usePrototypeState();
  return <div className="ar-prototype">
    <AgentRail state={state} />
    <OpenDesignAgentPanel state={state} />
    <Notice state={state} />
    <StatePeek state={state} />
  </div>;
}
