// THROWAWAY PROTOTYPE: OpenDesign-inspired Agent runtime and capability discovery.
import { AgentRail, Notice, StatePeek } from "./shared";
import { OpenDesignAgentPanel } from "./OpenDesignAgentPanel";
import { usePrototypeState } from "./usePrototypeState";
import "./agent-runtime-prototype.css";

export function AgentRuntimePrototype() {
  const state = usePrototypeState();
  return <div className="ar-prototype">
    <AgentRail state={state} />
    <OpenDesignAgentPanel state={state} />
    <Notice state={state} />
    <StatePeek state={state} />
  </div>;
}
