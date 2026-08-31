import { readFile } from "node:fs/promises";

try {
  const token = (await readFile("/penguin-data/api-token", "utf8")).trim();
  if (!token) throw new Error();
  const response = await fetch("http://127.0.0.1:7364/api/version", {
    headers: { Authorization: `Bearer ${token}` },
    signal: AbortSignal.timeout(2000),
  });
  const report = response.ok ? await response.json() : null;
  if (report?.version !== "0.2.9" || report?.describe !== "v0.2.9") throw new Error();
} catch {
  process.exitCode = 1;
}
