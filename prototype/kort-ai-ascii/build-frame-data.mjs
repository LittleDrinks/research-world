import { spawnSync } from "node:child_process";
import { writeFileSync } from "node:fs";

const [xhs, web, output = "frame-data.js"] = process.argv.slice(2);
if (!xhs || !web) throw new Error("usage: node build-frame-data.mjs <xhs.mp4> <ascii-web.mp4> [output]");

const specs = [
  ["hero", xhs, 0.45, 3, 8, [18, 58, 828, 220], [138, 37], "xo"],
  ["marketWave", xhs, 1.5, 1.4, 8, [0, 405, 220, 145], [44, 29], "01", true],
  ["marketMeteor", xhs, 1.5, 1.4, 8, [235, 405, 365, 145], [73, 29], "01", true],
  ["marketFold", xhs, 1.5, 1.4, 8, [615, 405, 230, 145], [46, 29], "01", true],
  ["globe", web, 0, 10, 8, [18, 28, 185, 130], [74, 52], "01"],
  ["spiral", web, 8, 6, 6, [106, 174, 107, 88], [43, 30], "01"],
  ["planet", web, 8, 6, 6, [213, 174, 107, 88], [43, 30], "01"],
  ["helmet", web, 8, 6, 6, [0, 252, 107, 82], [43, 30], "01"],
  ["bust", web, 8, 6, 6, [106, 252, 107, 82], [43, 30], "01"],
  ["dna", web, 8, 6, 6, [213, 252, 107, 82], [43, 30], "01"],
  ["why", xhs, 11.5, 18.2, 8, [300, 150, 540, 320], [108, 54], "01"],
];

function readFrames(spec) {
  const [, source, start, duration, fps, crop, size] = spec;
  const [x, y, width, height] = crop;
  const [cols, rows] = size;
  const filter = `crop=${width}:${height}:${x}:${y},fps=${fps},scale=${cols}:${rows}:flags=area`;
  const args = ["-v", "error", "-ss", `${start}`, "-i", source];
  if (duration) args.push("-t", `${duration}`);
  else args.push("-frames:v", "1");
  args.push("-vf", filter, "-pix_fmt", "rgb24", "-f", "rawvideo", "-");
  const result = spawnSync("ffmpeg", args, { maxBuffer: 64 * 1024 * 1024 });
  if (result.status) throw new Error(result.stderr.toString());
  return result.stdout;
}

function density(red, green, blue) {
  const purple = Math.max(0, blue - (red + green) / 2);
  const darkness = 255 - (red + green + blue) / 3;
  const value = Math.round((purple * 1.5 + darkness * 0.05 - 8) / 6);
  return Math.max(0, Math.min(15, value));
}

function pack(raw) {
  const cells = raw.length / 3;
  const packed = Buffer.alloc(Math.ceil(cells / 2));
  for (let cell = 0; cell < cells; cell += 1) {
    const level = density(raw[cell * 3], raw[cell * 3 + 1], raw[cell * 3 + 2]);
    packed[cell >> 1] |= level << (cell % 2 ? 0 : 4);
  }
  return packed.toString("base64");
}

function pingPong(raw, frameSize) {
  const count = raw.length / frameSize;
  const frames = Array.from({ length: count }, (_, index) => raw.subarray(index * frameSize, (index + 1) * frameSize));
  for (let index = count - 2; index > 0; index -= 1) frames.push(frames[index]);
  return Buffer.concat(frames);
}

function encode(spec) {
  const [name, , , , fps, , [cols, rows], glyphs, mirrored] = spec;
  const source = readFrames(spec);
  const raw = mirrored ? pingPong(source, cols * rows * 3) : source;
  const frames = raw.length / (cols * rows * 3);
  return [name, { cols, rows, fps, frames, glyphs, data: pack(raw) }];
}

const data = Object.fromEntries(specs.map(encode));
writeFileSync(output, `window.KORT_FRAME_DATA = ${JSON.stringify(data)};\n`);
