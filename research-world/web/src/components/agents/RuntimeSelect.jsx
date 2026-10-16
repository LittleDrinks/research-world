import { runtimeKey, runtimeRefKey } from "../../utils/runtime";


export function RuntimeSelect({ value, runtimes, onChange }) {
  const selected = runtimeRefKey(value);
  const known = runtimes.some((item) => runtimeRefKey(item) === selected);
  return <label className="field"><span>Runtime</span><select aria-label="Runtime" value={selected} onChange={changeRuntime(runtimes, onChange)}>
    {!known && selected && <option value={selected} disabled>{value.id} · {value.realm}（不在 catalog）</option>}
    {!selected && <option value="">未选择</option>}
    {runtimes.map(runtimeOption)}</select></label>;
}


function changeRuntime(runtimes, onChange) {
  return (event) => {
    const runtime = runtimes.find((item) => runtimeRefKey(item) === event.target.value);
    onChange(runtime ? { id: runtime.id, realm: runtime.realm } : null);
  };
}


function runtimeOption(item) {
  const status = item.status === "ready" ? "" : `（${item.reason?.code || item.status || "不可用"}）`;
  return <option key={runtimeKey(item.id, item.realm)} value={runtimeKey(item.id, item.realm)} disabled={item.status !== "ready"}>
    {item.display_name || item.id} · {item.realm}{status}</option>;
}
