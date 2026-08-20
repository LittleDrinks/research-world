export function Badge({ kind, children }) {
  return <span className={`act-badge ${kind}`}>{children}</span>;
}

export function Fold({ meta, children }) {
  return <details className="act-fold"><summary>{meta}</summary><pre>{children}</pre></details>;
}
