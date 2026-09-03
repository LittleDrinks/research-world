// 共享：从 web/node_modules 解析 playwright，提供录制上下文与视频落盘。
import { createRequire } from "node:module";
import path from "node:path";
import { fileURLToPath } from "node:url";
import fs from "node:fs";

export const HERE = path.dirname(fileURLToPath(import.meta.url));
export const RW = path.resolve(HERE, "../..");
export const REPO = path.resolve(RW, "..");
export const VIDEO_DIR = path.join(REPO, ".scratch/video/rec");
export const SHOT_DIR = path.join(REPO, ".scratch/video/shots");

export function pw() {
  const req = createRequire(path.resolve(RW, "web/package.json"));
  return req("playwright");
}

// 录制整个 page 生命周期，结束后把 webm 移到 <VIDEO_DIR>/<name>.webm。
export async function record(name, viewport, fn) {
  const { chromium } = pw();
  fs.mkdirSync(VIDEO_DIR, { recursive: true });
  fs.mkdirSync(SHOT_DIR, { recursive: true });
  const browser = await chromium.launch();
  const context = await browser.newContext({
    viewport,
    recordVideo: { size: viewport, dir: VIDEO_DIR },
  });
  const page = await context.newPage();
  await fn(page);
  await page.close();
  const [video] = await page.video().path() ? [await page.video().path()] : [];
  await context.close();
  await browser.close();
  const target = path.join(VIDEO_DIR, `${name}.webm`);
  if (video) fs.renameSync(video, target);
  console.log("recorded:", target);
}
