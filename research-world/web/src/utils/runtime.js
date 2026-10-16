export function runtimeKey(id, realm) {
  return JSON.stringify([id, realm]);
}


export function runtimeRefKey(ref) {
  return ref?.id && ref?.realm ? runtimeKey(ref.id, ref.realm) : "";
}


export function findRuntime(catalog, ref) {
  return (catalog?.runtimes || []).find((item) => runtimeRefKey(item) === runtimeRefKey(ref));
}


export function defaultRuntime(catalog) {
  const value = (catalog?.runtimes || []).find((item) => item.id === "codex" && item.status === "ready");
  return value ? { id: value.id, realm: value.realm } : null;
}


export function runtimeIssue(ref, catalog) {
  if (!ref?.id || !ref?.realm) return "Runtime 未选择";
  const runtime = findRuntime(catalog, ref);
  if (!runtime) return `Runtime 不在 catalog：${ref.id} · ${ref.realm}`;
  if (runtime.id !== "codex") return "Runtime 不受支持";
  if (runtime.status !== "ready") return `Runtime 当前不可用${reasonSuffix(runtime)}`;
  return "";
}


export function endpointIssue(spec, catalog) {
  const endpoint = (catalog?.endpoints || []).find((item) => item.id === spec.endpoint);
  if (!endpoint) return "Endpoint 不在 catalog";
  if (endpoint.available !== true) return "Endpoint 当前不可用";
  if (!(catalog.models || []).some((item) => item.endpoint === spec.endpoint && item.id === spec.model)) {
    return "模型与 Endpoint 不匹配";
  }
  const refs = endpoint.runtime_refs || [];
  return refs.some((item) => runtimeRefKey(item) === runtimeRefKey(spec.runtime)) ? "" : "Endpoint 与 Runtime 不兼容";
}


function reasonSuffix(runtime) {
  return runtime.reason?.code ? `（${runtime.reason.code}）` : "";
}
