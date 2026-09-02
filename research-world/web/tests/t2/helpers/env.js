// 凭证注册表：.env 值与运行时注入的测试凭证只存在于进程内存，失败输出一律脱敏。
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
export const RW_ROOT = path.resolve(HERE, "../../../..");
export const REPO_ROOT = path.resolve(RW_ROOT, "..");
const ENV_FILES = [path.join(RW_ROOT, ".env"), path.join(REPO_ROOT, ".env")];

const registry = new Set();

function splitEnvLine(line) {
  const match = /^([A-Za-z_][A-Za-z0-9_]*)=(.*)$/.exec(line.trim());
  if (!match) return null;
  const value = match[2].replace(/^"(.*)"$/, "$1").replace(/^'(.*)'$/, "$1").trim();
  return [match[1], value];
}

export function loadDotenv(file) {
  if (!fs.existsSync(file)) return {};
  return Object.fromEntries(fs.readFileSync(file, "utf8").split("\n").map(splitEnvLine).filter(Boolean));
}

// 同一凭证的等价形式：原值、去尾斜杠、去 scheme、主机名。
export function secretVariants(value) {
  const list = [value, value.replace(/\/+$/, ""), value.replace(/^https?:\/\//, "")];
  try { list.push(new URL(value).hostname); } catch { /* 非绝对 URL，忽略 */ }
  return list.filter((item) => item && item.length >= 4);
}

export function registerSecret(value) {
  if (value) for (const variant of secretVariants(value)) registry.add(variant);
}

export function registerSecrets(values) {
  for (const value of values) registerSecret(value);
}

export function registeredSecrets() {
  return [...registry];
}

export function findLeak(haystack) {
  for (const secret of registeredSecrets()) if (haystack.includes(secret)) return secret;
  return null;
}

export function redact(text) {
  let out = String(text ?? "");
  for (const secret of registeredSecrets()) out = out.split(secret).join("[REDACTED]");
  return out;
}

// 泄露上下文：命中点前后各 60 字符，凭证值已脱敏。
export function leakContext(haystack, secret) {
  const at = haystack.indexOf(secret);
  const start = Math.max(0, at - 60);
  return redact(haystack.slice(start, at + secret.length + 60));
}

for (const file of ENV_FILES) {
  const values = loadDotenv(file);
  registerSecrets([values.apikey, values.baseurl]);
}
