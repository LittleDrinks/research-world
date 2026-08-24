"use strict";

const MONO = 'ui-monospace, "SFMono-Regular", Menlo, Consolas, monospace';
const states = [];
const byCanvas = new WeakMap();
const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
const colors = [
  "transparent", "#cecaf0", "#bcb7e8", "#aaa3df",
  "#9890d5", "#867bca", "#7568bd", "#6757af",
  "#5947a0", "#4f3d95", "#46348c", "#3e2d83",
  "#38277b", "#322272", "#2e1e6c", "#2a1b66",
];

function decode(name) {
  const source = window.KORT_FRAME_DATA[name];
  const binary = atob(source.data);
  const bytes = Uint8Array.from(binary, char => char.charCodeAt(0));
  return { ...source, bytes };
}

function levelAt(bytes, index) {
  const byte = bytes[index >> 1];
  return index & 1 ? byte & 15 : byte >> 4;
}

function resize(state) {
  const box = state.canvas.getBoundingClientRect();
  const dpr = Math.min(devicePixelRatio || 1, 2);
  state.canvas.width = Math.max(2, Math.round(box.width * dpr));
  state.canvas.height = Math.max(2, Math.round(box.height * dpr));
  state.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  state.width = box.width;
  state.height = box.height;
}

function prepare(state) {
  const { ctx, clip, width, height } = state;
  ctx.clearRect(0, 0, width, height);
  state.cellWidth = width / clip.cols;
  state.cellHeight = height / clip.rows;
  ctx.font = `${Math.max(3, state.cellHeight * 1.12)}px ${MONO}`;
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
}

function drawGrid(state, frame) {
  const { ctx, clip, cellWidth, cellHeight } = state;
  const cells = clip.cols * clip.rows;
  const phase = Math.floor(frame / 2);
  for (let cell = 0; cell < cells; cell += 1) {
    const level = levelAt(clip.bytes, frame * cells + cell);
    if (!level) continue;
    const column = cell % clip.cols;
    const row = Math.floor(cell / clip.cols);
    ctx.fillStyle = colors[level];
    ctx.fillText(clip.glyphs[(cell + phase) % clip.glyphs.length], (column + 0.5) * cellWidth, (row + 0.5) * cellHeight);
  }
}

function localTime(state, now) {
  if (reduced) return 0;
  return Math.max(0, (now - state.started) / 1000);
}

function paint(state, now) {
  const time = localTime(state, now);
  const frame = Math.floor(time * state.clip.fps) % state.clip.frames;
  prepare(state);
  drawGrid(state, frame);
  if (state.canvas.id === "why-art") updateWhy(time);
}

function updateWhy(time) {
  const labels = ["Real-Time Market Intelligence", "Institution-Grade Insights", "Precision-Driven Analytics"];
  const index = time % 18.2 < 2.6 ? 0 : time % 18.2 < 6.5 ? 1 : 2;
  document.getElementById("why-label").textContent = labels[index];
  document.querySelector(".stats").dataset.phase = `${index}`;
}

function register(canvas) {
  const state = { canvas, ctx: canvas.getContext("2d"), clip: decode(canvas.dataset.ascii), visible: true, started: performance.now() };
  states.push(state);
  byCanvas.set(canvas, state);
  resize(state);
  paint(state, state.started);
  observer.observe(canvas);
  resizer.observe(canvas);
}

const observer = new IntersectionObserver(entries => {
  for (const entry of entries) {
    const state = byCanvas.get(entry.target);
    state.visible = entry.isIntersecting;
    if (state.visible && !state.started) state.started = performance.now();
  }
}, { rootMargin: "160px" });

const resizer = new ResizeObserver(entries => {
  for (const entry of entries) {
    const state = byCanvas.get(entry.target);
    resize(state);
    paint(state, performance.now());
  }
});

function animate(now) {
  for (const state of states) if (state.visible) paint(state, now);
  requestAnimationFrame(animate);
}

function bindRail() {
  const rail = document.querySelector(".market-track");
  document.querySelectorAll("[data-scroll]").forEach(button => {
    button.addEventListener("click", () => rail.scrollBy({ left: Number(button.dataset.scroll) * rail.clientWidth * 0.72, behavior: "smooth" }));
  });
}

function boot() {
  document.querySelectorAll("canvas[data-ascii]").forEach(register);
  bindRail();
  requestAnimationFrame(animate);
}

document.readyState === "loading" ? document.addEventListener("DOMContentLoaded", boot) : boot();
