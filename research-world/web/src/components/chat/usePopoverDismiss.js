import { useEffect } from "react";


export function usePopoverDismiss(open, root, trigger, close) {
  useEffect(() => {
    if (!open) return undefined;
    const dismiss = (event) => {
      if (event.type === "keydown" && event.key !== "Escape") return;
      if (event.type === "pointerdown" && root.current?.contains(event.target)) return;
      close(); requestAnimationFrame(() => trigger.current?.focus());
    };
    document.addEventListener("keydown", dismiss);
    document.addEventListener("pointerdown", dismiss);
    return () => { document.removeEventListener("keydown", dismiss); document.removeEventListener("pointerdown", dismiss); };
  }, [open, close]);
}
