export function runtimeKey(id, realm) {
  return JSON.stringify([id, realm]);
}
