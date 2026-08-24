"use strict";
/* 渲染引擎：register(canvas) + rAF，密度分级 → 墨色深浅，高光用 accent 蓝 */

const MONO = 'ui-monospace, "SFMono-Regular", Menlo, Consolas, monospace';
const RAMP = " .·:-=+*#%@";
const INK = "26, 29, 41";
const ACCENT = "#2563eb";
const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
const states = [];
const byCanvas = new WeakMap();

function makeSampler(canvas) {
  const def = window.ASCII_ASSETS[canvas.dataset.ascii];
  if (!def) throw new Error(`unknown ascii asset: ${canvas.dataset.ascii}`);
  return def(canvas.dataset);
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
  const { ctx, width, height, cols } = state;
  ctx.clearRect(0, 0, width, height);
  state.rows = Math.max(2, Math.round(cols * height / width * 0.52));
  state.cellW = width / cols;
  state.cellH = height / state.rows;
  ctx.font = `${Math.max(3, state.cellH * 1.05)}px ${MONO}`;
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
}

function ink(level) {
  const alpha = 0.18 + 0.72 * (level / (RAMP.length - 1));
  return `rgba(${INK}, ${alpha.toFixed(3)})`;
}

function drawGrid(state, t) {
  const { ctx, cols, rows, cellW, cellH, sample, fit } = state;
  const aspect = state.width / Math.max(1, state.height);
  for (let row = 0; row < rows; row += 1) {
    for (let col = 0; col < cols; col += 1) {
      let x = (col + 0.5) / cols, y = (row + 0.5) / rows;
      if (fit) {
        if (aspect > 1) x = 0.5 + (x - 0.5) * aspect;
        else y = 0.5 + (y - 0.5) / aspect;
        if (x < 0 || x > 1 || y < 0 || y > 1) continue;
      }
      const { v, hot } = sample(x, y, t);
      if (v <= 0.02) continue;
      const level = Math.min(RAMP.length - 1, Math.round(v * (RAMP.length - 1)));
      ctx.fillStyle = hot ? ACCENT : ink(level);
      ctx.fillText(RAMP[level], (col + 0.5) * cellW, (row + 0.5) * cellH);
    }
  }
}

function paint(state, now) {
  const t = reduced ? 0 : (now - state.started) / 1000;
  prepare(state);
  drawGrid(state, t);
}

function register(canvas) {
  const state = {
    canvas,
    ctx: canvas.getContext("2d"),
    sample: makeSampler(canvas),
    cols: Number(canvas.dataset.cols) || 36,
    fit: canvas.dataset.fit === "square",
    visible: true,
    started: performance.now(),
  };
  states.push(state);
  byCanvas.set(canvas, state);
  resize(state);
  paint(state, state.started);
  observer.observe(canvas);
  resizer.observe(canvas);
}

const observer = new IntersectionObserver(entries => {
  for (const entry of entries) byCanvas.get(entry.target).visible = entry.isIntersecting;
}, { rootMargin: "120px" });

const resizer = new ResizeObserver(entries => {
  for (const entry of entries) {
    const state = byCanvas.get(entry.target);
    resize(state);
    paint(state, performance.now());
  }
});

function animate(now) {
  for (const state of states) if (state.visible && !reduced) paint(state, now);
  requestAnimationFrame(animate);
}

function boot() {
  document.querySelectorAll("canvas[data-ascii]").forEach(register);
  requestAnimationFrame(animate);
}

document.readyState === "loading"
  ? document.addEventListener("DOMContentLoaded", boot)
  : boot();
