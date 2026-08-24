const encoder = new TextEncoder();

function decodePrefix(bytes, limit) {
  let visibleBytes = Math.min(bytes.length, limit);
  while (visibleBytes) {
    try {
      const decoder = new TextDecoder("utf-8", { fatal: true });
      return { visible: decoder.decode(bytes.subarray(0, visibleBytes)), visibleBytes };
    } catch {
      visibleBytes -= 1;
    }
  }
  return { visible: "", visibleBytes: 0 };
}

export function truncateUtf8(value, limit) {
  const bytes = encoder.encode(value);
  const prefix = decodePrefix(bytes, limit);
  return {
    ...prefix,
    totalBytes: bytes.length,
    remainingBytes: bytes.length - prefix.visibleBytes,
  };
}

export async function writeClipboard(clipboard, value) {
  if (!clipboard || typeof clipboard.writeText !== "function") return "unavailable";
  try {
    await clipboard.writeText(value);
    return "success";
  } catch {
    return "failed";
  }
}

export function treeKeyAction(key, row) {
  if (key === "ArrowRight" && row.expandable && !row.open) return { type: "expand" };
  if (key === "ArrowRight" && row.expandable && row.firstChild) return { type: "focus", id: row.firstChild };
  if (key === "ArrowLeft" && row.expandable && row.open) return { type: "collapse" };
  if (key === "ArrowLeft" && row.parent) return { type: "focus", id: row.parent };
  return null;
}
