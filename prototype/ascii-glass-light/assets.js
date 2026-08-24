"use strict";
/* 程序化 ASCII 像素素材：bust / planet / music
 * 每个生成器返回 sample(x, y, t) -> { v: 0..1 密度, hot: 是否高光 }
 */

const TAU = Math.PI * 2;
const clamp01 = v => Math.min(1, Math.max(0, v));

/* ---------- 人像：手写遮罩 + 方向光 + 呼吸 ---------- */
const BUST_MASK = [
  "                                ",
  "            ######              ",
  "          ##########            ",
  "         ############           ",
  "        ##############          ",
  "       ######OOOOO######        ",
  "       #####OOOOOOOOO####       ",
  "      #####OOOOOOOOOOO#####     ",
  "      ####OOOOOOOOOOOOO####     ",
  "      ###OOOOOOOOOOOOOOO###     ",
  "      ###OOOOOOOOOOOOOOO###     ",
  "      ###OOOOOOOOOOOOOOO###     ",
  "      ####OOOOOOOOOOOOO####     ",
  "      ####OOOOOOOOOOOOO####     ",
  "       ###OOOOOOOOOOOO###       ",
  "       ####OOOOOOOOOO####       ",
  "       #####OOOOOOOO#####       ",
  "        ####OOOOOOO####         ",
  "        #####OOnnOO####         ",
  "         ####nnnnn#####         ",
  "         ###nnnnnnn###          ",
  "         ###nnnnnnn###          ",
  "        ##nnnnnnnnnnn##         ",
  "       ===nnnnnnnnnnn===        ",
  "      ====nnnnnnnnnn=====       ",
  "    ======================      ",
  "   ========================     ",
  "  ==========================    ",
  " ============================   ",
  "   ________________________     ",
  "                                ",
];
const BUST_COLS = 32, BUST_ROWS = BUST_MASK.length;

function bustCell(x, y) {
  const row = BUST_MASK[Math.floor(y * BUST_ROWS)];
  if (!row) return " ";
  return row[Math.floor(x * BUST_COLS)] || " ";
}

function makeBust() {
  return (x, y, t) => {
    const ch = bustCell(x, y);
    if (ch === " ") return { v: 0, hot: false };
    const light = clamp01(0.62 - (x - 0.32) * 0.9 - (y - 0.28) * 0.7);
    const dx = x - 0.5, dy = y - 0.34;
    const dist = Math.sqrt(dx * dx + dy * dy);
    const breath = 0.82 + 0.18 * Math.sin(t * 0.9 - dist * 5.0);
    const shade = { O: 1.0, n: 0.85, "#": 0.68, "=": 0.8, _: 0.55 }[ch] || 0.5;
    const v = clamp01((0.3 + 0.7 * light) * shade * breath + 0.14);
    return { v, hot: light > 0.82 && (ch === "O" || ch === "#") };
  };
}

/* ---------- 行星：球体光照 + 纬度条带 + 光环/卫星 ---------- */
const LIGHT = norm3(-0.55, -0.45, 0.7);
function norm3(x, y, z) {
  const l = Math.hypot(x, y, z);
  return { x: x / l, y: y / l, z: z / l };
}

function sphereShade(nx, ny) {
  const r2 = nx * nx + ny * ny;
  if (r2 > 1) return -1;
  const nz = Math.sqrt(1 - r2);
  const d = nx * LIGHT.x + ny * LIGHT.y + nz * LIGHT.z;
  return clamp01(0.15 + 0.95 * Math.max(0, d));
}

function ringValue(nx, ny) {
  const u = nx, v = (ny - nx * 0.22) / 0.34;
  const d = Math.abs(Math.hypot(u, v) - 1.52);
  return clamp01(1 - d / 0.13) * 0.7;
}

function moonAt(nx, ny, t) {
  const a = t * 0.35;
  const mx = Math.cos(a) * 1.9, my = Math.sin(a) * 0.55;
  const d = Math.hypot(nx - mx, ny - my);
  return d < 0.09 ? 0.9 : 0;
}

function makePlanet(opts = {}) {
  const bands = opts.bands ?? 6.5;
  const ring = opts.ring !== "false";
  return (x, y, t) => {
    const nx = (x - 0.5) * 2.4, ny = (y - 0.5) * 2.4;
    let v = moonAt(nx, ny, t);
    let hot = v > 0;
    const shade = sphereShade(nx, ny);
    if (shade >= 0) {
      const band = 0.5 + 0.5 * Math.sin(ny * bands + t * 0.5 + Math.sin(nx * 2 + t * 0.3));
      const sv = shade * (0.72 + 0.28 * band);
      if (sv >= v) { v = sv; hot = shade > 0.93; }
    } else if (ring) {
      const rv = ringValue(nx, ny);
      if (rv > v) { v = rv; hot = false; }
    }
    return { v: clamp01(v), hot };
  };
}

/* ---------- 音乐：均衡器柱 / 波形 ---------- */
function barHeight(i, n, t) {
  const p = (i + 0.5) / n;
  const a = Math.sin(t * 2.1 + i * 1.7) * 0.5 + 0.5;
  const b = Math.sin(t * 3.3 + i * 0.9) * 0.5 + 0.5;
  const c = Math.sin(t * 1.1 + p * TAU * 2) * 0.5 + 0.5;
  return 0.18 + 0.72 * (0.45 * a + 0.35 * b + 0.2 * c);
}

function makeBars(opts = {}) {
  const n = opts.bars || 18;
  return (x, y, t) => {
    const i = Math.min(n - 1, Math.floor(x * n));
    const local = x * n - i;
    if (local > 0.72) return { v: 0, hot: false };
    const h = barHeight(i, n, t);
    const fromBottom = 1 - y;
    if (fromBottom > h) {
      const tip = fromBottom - h;
      return { v: tip < 0.06 ? 0.4 : 0, hot: false };
    }
    const v = 0.35 + 0.6 * (1 - fromBottom / Math.max(h, 0.01));
    return { v: clamp01(v), hot: fromBottom > h - 0.09 };
  };
}

function waveY(x, t) {
  return 0.5
    + 0.16 * Math.sin(x * TAU * 1.6 + t * 1.4)
    + 0.09 * Math.sin(x * TAU * 3.1 - t * 2.2)
    + 0.05 * Math.sin(x * TAU * 5.3 + t * 0.7);
}

function makeWave(opts = {}) {
  const soft = opts.soft ?? 0.05;
  return (x, y, t) => {
    const d = Math.abs(y - waveY(x, t));
    const v = clamp01(1 - d / soft);
    return { v: v * 0.95, hot: v > 0.86 };
  };
}

/* ---------- 注册表 ---------- */
window.ASCII_ASSETS = {
  bust: makeBust,
  planet: makePlanet,
  bars: makeBars,
  wave: makeWave,
};
