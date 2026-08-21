/* Kort AI ASCII replica v2 — 3D point-cloud sculptures rendered as matrix digit columns. */
"use strict";

const DPR = Math.min(window.devicePixelRatio || 1, 2);
const MONO = 'ui-monospace, "SF Mono", Menlo, Consolas, monospace';
const C_NEAR = [47, 39, 119];
const C_MID = [87, 78, 185];
const C_FAR = [190, 186, 236];
const CW = 4, CH = 6, CAM_D = 3.2;

/* ---------- utils ---------- */
const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
const rgba = (c, a) => `rgba(${c[0]},${c[1]},${c[2]},${a})`;
const fract = v => v - Math.floor(v);
const hash1 = n => fract(Math.sin(n * 127.1) * 43758.5453);
const hash3 = (x, y, z) => fract(Math.sin(x * 127.1 + y * 311.7 + z * 74.7) * 43758.5453);

function noise3(x, y, z) {
  const xi = Math.floor(x), yi = Math.floor(y), zi = Math.floor(z);
  const u = (x - xi) ** 2 * (3 - 2 * (x - xi));
  const v = (y - yi) ** 2 * (3 - 2 * (y - yi));
  const w = (z - zi) ** 2 * (3 - 2 * (z - zi));
  let acc = 0;
  for (let i = 0; i < 8; i++) {
    const dx = i & 1, dy = (i >> 1) & 1, dz = (i >> 2) & 1;
    acc += (dx ? u : 1 - u) * (dy ? v : 1 - v) * (dz ? w : 1 - w) * hash3(xi + dx, yi + dy, zi + dz);
  }
  return acc;
}

function fbm3(x, y, z) {
  return noise3(x, y, z) * 0.55 + noise3(x * 2.13 + 5, y * 2.13 + 9, z * 2.13 + 3) * 0.3
       + noise3(x * 4.31 + 11, y * 4.31 + 7, z * 4.31 + 17) * 0.15;
}

function rng(seed) {
  let s = seed;
  return () => { s = (s * 16807) % 2147483647; return (s - 1) / 2147483646; };
}

function fitCanvas(cv) {
  const r = cv.getBoundingClientRect();
  cv.width = Math.max(2, Math.round(r.width * DPR));
  cv.height = Math.max(2, Math.round(r.height * DPR));
  const ctx = cv.getContext("2d");
  ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
  return { ctx, w: r.width, h: r.height };
}

/* ---------- point-cloud shapes (each returns number[] of xyz triplets) ---------- */
function fibSphere(n, cb) { // near-uniform sphere points
  const ga = Math.PI * (3 - Math.sqrt(5));
  for (let i = 0; i < n; i++) {
    const y = 1 - 2 * (i + 0.5) / n, r = Math.sqrt(1 - y * y), th = ga * i;
    cb(Math.cos(th) * r, y, Math.sin(th) * r, i);
  }
}

const CONTINENTS = [
  [[-168, 62], [-140, 72], [-105, 70], [-82, 50], [-55, 47], [-78, 15], [-110, 22], [-130, 48]],
  [[-81, 12], [-52, 8], [-35, -10], [-50, -55], [-70, -42]],
  [[-12, 35], [-1, 37], [18, 33], [35, 12], [44, -12], [25, -35], [5, -28], [-17, 15]],
  [[-10, 36], [8, 60], [38, 70], [78, 72], [120, 57], [170, 60], [145, 35], [105, 8], [70, 24], [45, 30]],
  [[112, -10], [154, -12], [150, -40], [116, -35]],
  [[-55, 60], [-25, 82], [-20, 62]],
];

function inPolygon(x, y, polygon) {
  let inside = false;
  for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
    const [xi, yi] = polygon[i], [xj, yj] = polygon[j];
    const crosses = yi > y !== yj > y && x < (xj - xi) * (y - yi) / (yj - yi) + xi;
    if (crosses) inside = !inside;
  }
  return inside;
}

function landAt(x, y, z) {
  const lon = Math.atan2(z, x) / Math.PI * 180;
  const lat = Math.asin(y) / Math.PI * 180;
  return CONTINENTS.some(polygon => inPolygon(lon, lat, polygon));
}

function addSphere(p, n, center, scale) {
  fibSphere(n, (x, y, z) => p.push(
    center[0] + x * scale[0], center[1] + y * scale[1], center[2] + z * scale[2]
  ));
}

const Shapes = {
  sphere(n) { const p = []; fibSphere(n, (x, y, z) => p.push(x, y, z)); return p; },

  globe(n) {
    const p = [];
    fibSphere(n * 3, (x, y, z, i) => {
      if (landAt(x, y, z) || hash1(i * 3.3) < 0.025) p.push(x, y, z);
    });
    return p;
  },

  torus(n) {
    const p = [], r = rng(31);
    for (let i = 0; i < n; i++) {
      const u = r() * 6.2832, v = r() * 6.2832, ring = 1 + 0.3 * Math.cos(v);
      p.push(ring * Math.cos(u), 0.3 * Math.sin(v), ring * Math.sin(u));
    }
    return p;
  },

  apple(n) {
    const p = [], body = Math.floor(n * 0.85);
    fibSphere(body, (x, y, z) => {
      const bulge = 0.78 + 0.24 * (1 - y * y);
      const notch = 0.18 * Math.exp(-(((y - 0.9) * 6) ** 2));
      p.push(x * bulge, y * 0.9 - notch, z * bulge);
    });
    addSphere(p, n - body, [0.2, 1, 0], [0.36, 0.12, 0.16]);
    return p;
  },

  clover(n) {
    const p = [], leaf = Math.floor(n * 0.2);
    [[0, 0.68], [0.68, 0], [0, -0.68], [-0.68, 0]].forEach(([x, y]) =>
      addSphere(p, leaf, [x, y, 0], [0.5, 0.3, 0.3]));
    addSphere(p, Math.floor(n * 0.1), [-1.32, 0.82, 0.05], [0.16, 0.16, 0.16]);
    addSphere(p, n - p.length / 3, [1.35, -0.68, 0], [0.14, 0.14, 0.14]);
    return p;
  },

  pinwheel(n) {
    const p = [], r = rng(23);
    while (p.length / 3 < n) {
      const radius = Math.sqrt(r()), angle = r() * Math.PI * 2;
      const turn = fract((angle - radius * 1.7) / (Math.PI * 0.4));
      if (turn > 0.38 && radius > 0.2) continue;
      const z = Math.sqrt(1 - radius * radius) * (r() > 0.5 ? 1 : -1);
      p.push(Math.cos(angle) * radius, Math.sin(angle) * radius, z * 0.5);
    }
    return p;
  },

  ringStack(n) {
    const p = [], r = rng(77), per = Math.floor(n * 0.85 / 5);
    for (let k = 0; k < 5; k++) for (let i = 0; i < per; i++) {
      const a = r() * 6.2832, rad = 0.95 + (r() - 0.5) * 0.06;
      p.push(rad * Math.cos(a), -0.9 + k * 0.45 + (r() - 0.5) * 0.05, rad * Math.sin(a));
    }
    fibSphere(n - per * 5, (x, y, z) => p.push(x * 0.3, y * 0.3, z * 0.3));
    return p;
  },

  planet(n) {
    const p = [], body = Math.floor(n * 0.28), r = rng(91);
    fibSphere(body, (x, y, z) => p.push(x * 0.38, y * 0.38, z * 0.38));
    while (p.length / 3 < n) {
      const a = r() * Math.PI * 2, radius = 0.68 + r() * 0.48;
      const x = Math.cos(a) * radius, z = Math.sin(a) * radius;
      p.push(x, z * 0.18, z * 0.72);
    }
    return p;
  },

  drum(n) {
    const p = [], r = rng(83);
    while (p.length / 3 < n) {
      const a = r() * Math.PI * 2, top = r() > 0.52;
      const radius = top ? 0.35 + r() * 0.6 : 0.92 + (r() - 0.5) * 0.08;
      const y = top ? (r() > 0.5 ? 0.48 : -0.48) : r() - 0.5;
      p.push(Math.cos(a) * radius, y, Math.sin(a) * radius);
    }
    return p;
  },

  helmet(n) {
    const p = [], dome = Math.floor(n * 0.7), r = rng(47);
    fibSphere(dome * 2, (x, y, z) => { if (y > -0.15 && p.length / 3 < dome) p.push(x, y * 0.8, z); });
    while (p.length / 3 < n) {
      const a = r() * Math.PI, radius = 0.45 + r() * 0.5;
      p.push(Math.cos(a) * radius, -0.22 - Math.sin(a) * 0.35, (r() - 0.5) * 0.3);
    }
    return p;
  },

  dna(n) {
    const p = [], m = Math.floor(n * 0.36);
    for (let s = 0; s < 2; s++) for (let i = 0; i < m; i++) {
      const y = (i / m) * 2.2 - 1.1, a = y * 4.4 + s * Math.PI;
      p.push(0.5 * Math.cos(a), y, 0.5 * Math.sin(a));
    }
    for (let i = 0; p.length / 3 < n; i++) { // rungs between strands
      const y = (i % 9) / 9 * 2.2 - 1.1, a = y * 4.4, k = hash1(i * 5.1);
      p.push(0.5 * Math.cos(a) * (k * 2 - 1), y, 0.5 * Math.sin(a) * (k * 2 - 1));
    }
    return p;
  },

  bust(n) {
    const p = [], headN = Math.floor(n * 0.45);
    fibSphere(headN, (x, y, z) => p.push(x * 0.42, 0.52 + y * 0.48, z * 0.42));
    fibSphere(n - headN, (x, y, z) => { if (y < 0.15) p.push(x * 0.95, -0.3 + y * 0.45, z * 0.5); });
    return p;
  },

  ribbon(n) {
    const p = [], r = rng(13);
    while (p.length / 3 < n) {
      const s = r(), w = r() * 2 - 1;
      if (fract(s * 7 + w * 1.5) < 0.28) continue; // diagonal stripe gaps
      const x = (s * 2 - 1) * 1.45;
      p.push(x, -x * 0.42 + w * 0.62, 0.38 * Math.sin(s * 4.2) + w * 0.12);
    }
    return p;
  },

  arrowBlob(n) {
    const p = [], r = rng(41);
    while (p.length / 3 < n) {
      const x = r() * 2.5 - 1.25, y = r() * 1.3 - 0.65;
      const head = x < -0.35 && Math.abs(y) < (x + 1.25) / 0.9 * 0.65;
      const shaft = x >= -0.45 && Math.abs(y) < 0.22;
      if (head || shaft) p.push(x, y, (r() - 0.5) * 0.32);
    }
    return p;
  },

};

/* ---------- sculpture core ---------- */
function normalize(pts) {
  let m = 0;
  for (const v of pts) m = Math.max(m, Math.abs(v));
  return pts.map(v => v / m);
}

function resample(pts, n) { // any-length cloud -> exactly n points
  const m = pts.length / 3, out = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) {
    const j = m >= n ? Math.floor(i * m / n) : (i < m ? i : Math.floor(hash1(i * 3.7) * m));
    const jit = m >= n || i < m ? 0 : 0.03;
    for (let k = 0; k < 3; k++) out[i * 3 + k] = pts[j * 3 + k] + (hash1(i * 7 + k) - 0.5) * jit;
  }
  return out;
}

const easeIO = k => k < 0.5 ? 4 * k * k * k : 1 - ((-2 * k + 2) ** 3) / 2;

function morphInto(fx, t) { // shape list cycle: hold 2.5s, morph 1.2s
  const cs = fx.clouds, out = fx.scratch;
  if (cs.length === 1) { out.set(cs[0]); return; }
  const k = Math.floor(t / 3.7), ph = t - k * 3.7;
  const a = cs[k % cs.length], b = cs[(k + 1) % cs.length];
  const e = ph < 2.5 ? 0 : easeIO((ph - 2.5) / 1.2);
  for (let i = 0; i < out.length; i++) out[i] = a[i] + (b[i] - a[i]) * e;
}

function sculptSetup(cv) {
  const s = fitCanvas(cv);
  const names = cv.dataset.shapes.split(",");
  s.N = +cv.dataset.n || 2200;
  s.scale = +cv.dataset.scale || 1;
  s.motion = cv.dataset.motion || "spin";
  s.angle = +cv.dataset.angle || 0;
  s.tilt = +(cv.dataset.tilt || 0.5);
  s.clouds = names.map(nm => resample(normalize(Shapes[nm](s.N)), s.N));
  s.scratch = new Float32Array(s.N * 3);
  s.gcols = Math.ceil(s.w / CW);
  s.grid = new Int32Array(s.gcols * Math.ceil(s.h / CH));
  s.gdep = new Float32Array(s.grid.length);
  s.phase = hash1(names.join("").length * 3.3) * 6.28;
  return s;
}

function sculptTick(ctx, W, H, t, fx) {
  ctx.clearRect(0, 0, W, H);
  morphInto(fx, t);
  projectAll(fx, t, W, H);
  drawCells(ctx, fx, t);
}

function projectAll(fx, t, W, H) { // rotate Y + tilt X, perspective, nearest-wins grid
  const turn = turnAngle(fx, t);
  const cY = Math.cos(turn), sY = Math.sin(turn);
  const cX = Math.cos(fx.tilt), sX = Math.sin(fx.tilt);
  const K = fx.scale * 0.66 * Math.min(W, H) * (CAM_D - 1);
  const cx = W / 2, cy = H / 2, p = fx.scratch;
  fx.grid.fill(-1); fx.gdep.fill(1e9);
  for (let i = 0; i < fx.N; i++) {
    const x = p[i * 3], y = p[i * 3 + 1], z = p[i * 3 + 2];
    const x1 = x * cY + z * sY, z1 = -x * sY + z * cY;
    const y2 = y * cX - z1 * sX, zp = y * sX + z1 * cX + CAM_D;
    const col = Math.round((cx + x1 * K / zp - CW / 2) / CW);
    const row = Math.round((cy - y2 * K / zp - CH / 2) / CH);
    const c = row * fx.gcols + col;
    if (col < 0 || row < 0 || c < 0 || c >= fx.grid.length) continue;
    if (zp < fx.gdep[c]) { fx.gdep[c] = zp; fx.grid[c] = i; }
  }
}

function turnAngle(fx, t) {
  if (fx.motion === "sway") return fx.angle + Math.sin(t * 0.65 + fx.phase) * 0.16;
  if (fx.motion === "orbit") return Math.sin(t * 0.32) * 0.8;
  return t * 0.5 + fx.phase;
}

function depthStyle(n) {
  const color = n > 0.58 ? C_NEAR : n > 0.25 ? C_MID : C_FAR;
  return rgba(color, 0.2 + 0.8 * Math.pow(n, 1.45));
}

function drawCells(ctx, fx, t) {
  ctx.font = `6.5px ${MONO}`; ctx.textAlign = "center"; ctx.textBaseline = "middle";
  const frame = Math.floor(t * 8);
  for (let c = 0; c < fx.grid.length; c++) {
    const i = fx.grid[c];
    if (i < 0) continue;
    const col = c % fx.gcols, row = (c / fx.gcols) | 0;
    const n = clamp((CAM_D + 1 - fx.gdep[c]) / 2, 0, 1);
    const flip = hash1(i * 2.17 + frame * 0.913) < 0.03;
    ctx.fillStyle = depthStyle(n);
    ctx.fillText((hash1(i * 1.31) > 0.5) !== flip ? "1" : "0", col * CW + CW / 2, row * CH + CH / 2);
    drawTrail(ctx, fx, c, i, col, row, frame, 0.2 + 0.8 * Math.pow(n, 1.45));
  }
}

function drawTrail(ctx, fx, c, i, col, row, frame, alpha) {
  for (let k = 1; k <= 2; k++) {
    const cb = c + k * fx.gcols;
    if (cb >= fx.grid.length || fx.grid[cb] !== -1 || hash1(i * 4.7 + k * 0.61) > 0.8) break;
    fx.grid[cb] = -2;
    ctx.fillStyle = rgba(C_MID, alpha * 0.35 / k);
    ctx.fillText(hash1(i + k * frame) > 0.5 ? "1" : "0", col * CW + CW / 2, (row + k) * CH + CH / 2);
  }
}

/* ---------- hero: drifting financial glyph columns ---------- */
const HERO_GLYPHS = "$¥€£%#01+-";

function heroTick(ctx, W, H, t) {
  ctx.clearRect(0, 0, W, H);
  ctx.font = `12px ${MONO}`; ctx.textAlign = "center"; ctx.textBaseline = "middle";
  const frame = Math.floor(t * 4), cols = Math.ceil(W / 18), rows = Math.ceil(H / 16);
  for (let x = 0; x < cols; x++) for (let y = 0; y < rows; y++) {
    const band = fbm3(x * 0.12, y * 0.11 - t * 0.04, x * 0.03);
    if (band < 0.43 || hash3(x, y, 8) < 0.16) continue;
    const head = fract(hash1(x * 7.9) + t * (0.015 + hash1(x) * 0.02));
    const glow = 1 - Math.min(1, Math.abs(y / rows - head) * 2.4);
    const glyph = HERO_GLYPHS[Math.floor(hash3(x, y, frame) * HERO_GLYPHS.length)];
    ctx.fillStyle = rgba(glow > 0.7 ? C_NEAR : C_MID, 0.12 + band * 0.42 + glow * 0.25);
    ctx.fillText(glyph, x * 18 + 9, y * 16 + 8);
  }
}

/* ---------- effect registry: one rAF, offscreen pause ---------- */
const effects = [];

function register(cv, fps, setup, tick) {
  const fx = { cv, fps, setup, tick, ctx: null, w: 0, h: 0, last: 0, started: 0, visible: false };
  effects.push(fx);
  return fx;
}

const io = new IntersectionObserver(entries => {
  for (const e of entries) {
    const fx = effects.find(f => f.cv === e.target);
    if (fx) fx.visible = e.isIntersecting;
  }
}, { rootMargin: "120px" });

function loop(ts) {
  for (const fx of effects) {
    if (!fx.visible || ts - fx.last < 1000 / fx.fps) continue;
    if (!fx.started) fx.started = ts;
    fx.last = ts;
    if (!fx.ctx) Object.assign(fx, fx.setup(fx.cv));
    fx.tick(fx.ctx, fx.w, fx.h, (ts - fx.started) / 1000, fx);
  }
  requestAnimationFrame(loop);
}

let resizeTimer = 0;
window.addEventListener("resize", () => {
  clearTimeout(resizeTimer);
  resizeTimer = setTimeout(() => effects.forEach(f => { f.ctx = null; }), 150);
});

/* ---------- scramble label ---------- */
function initScramble(el, words, holdMs) {
  let idx = 0;
  setInterval(() => {
    idx = (idx + 1) % words.length;
    scrambleTo(el, words[idx]);
  }, holdMs);
}

function scrambleTo(el, target) {
  const from = el.textContent, len = Math.max(from.length, target.length);
  let step = 0;
  const timer = setInterval(() => {
    step++;
    el.textContent = scrambleFrame(from, target, len, step);
    if (step < 34) return;
    el.textContent = target;
    clearInterval(timer);
  }, 34);
}

function scrambleFrame(from, target, len, step) {
  const glyphs = "!<>-_/[]{}=+*^?#01";
  let out = "";
  for (let i = 0; i < len; i++) {
    const reveal = i / len * 18.2;
    if (step > reveal + 8) out += target[i] || "";
    else if (step > reveal) out += glyphs[Math.floor(Math.random() * glyphs.length)];
    else out += from[i] || "";
  }
  return out;
}

/* ---------- boot ---------- */
function initBars() {
  document.querySelectorAll("i.bars").forEach(el => {
    const n = +el.dataset.n, c = el.dataset.c;
    let html = "";
    for (let i = 0; i < 7; i++) html += `<b class="${i < n ? "f-" + c : ""}"></b>`;
    el.innerHTML = html;
  });
}

function sculpt(cv, fps) {
  register(cv, fps || 30, sculptSetup, sculptTick);
}

function boot() {
  initBars();
  register(document.getElementById("fx-hero"), 22, fitCanvas, heroTick);
  sculpt(document.getElementById("fx-globe"));
  sculpt(document.getElementById("fx-torus"));
  document.querySelectorAll("canvas.fx-sculpt").forEach(cv => sculpt(cv, 24));
  effects.forEach(fx => io.observe(fx.cv));
  initScramble(document.getElementById("scramble"),
    ["Precision-Driven Analytics", "Real-Time Market Intelligence", "Institution-Grade Insights"], 4200);
  requestAnimationFrame(loop);
}

document.readyState === "loading" ? document.addEventListener("DOMContentLoaded", boot) : boot();
