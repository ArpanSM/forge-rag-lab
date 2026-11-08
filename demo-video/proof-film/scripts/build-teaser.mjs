// Teaser (22 s) timeline from the measured teaser VO.
import fs from 'node:fs';
import path from 'node:path';

const root = path.resolve('proof-film');
const voDir = path.join(root, 'audio/vo-teaser');
const outDir = path.join(root, 'out');
const compDir = path.join(root, 'compositions');

function readWav(file) {
  const b = fs.readFileSync(file);
  let i = 12;
  let sr = null;
  let data = null;
  while (i + 8 <= b.length) {
    const cid = b.toString('ascii', i, i + 4);
    const size = b.readUInt32LE(i + 4);
    const body = i + 8;
    if (cid === 'fmt ') sr = b.readUInt32LE(body + 4);
    else if (cid === 'data') data = b.subarray(body, body + size);
    i = body + size + (size % 2);
  }
  const n = data.length / 4;
  const win = Math.floor(sr * 0.02);
  const rms = [];
  for (let j = 0; j + win < n; j += win) {
    let s = 0;
    for (let k = 0; k < win; k++) {
      const v = data.readFloatLE((j + k) * 4);
      s += v * v;
    }
    rms.push(Math.sqrt(s / win));
  }
  const thr = Math.max(...rms) * 0.02;
  let first = 0;
  let last = rms.length - 1;
  while (first < rms.length && rms[first] <= thr) first++;
  while (last >= 0 && rms[last] <= thr) last--;
  return { dur: n / sr, speechStart: first * 0.02, speechEnd: (last + 1) * 0.02 };
}

const manifest = JSON.parse(fs.readFileSync(path.join(voDir, 'manifest.json'), 'utf8'));
const units = manifest.map((u) => ({ ...u, ...readWav(u.file) }));
const byId = Object.fromEntries(units.map((u) => [u.id, u]));

// Hand-set speech starts: the teaser is cut to a 22 s clock.
const starts = {
  t01a: 0.3,
  t02a: 4.1,
  t02b: 6.1,
  t03a: 8.85,
  t04a: 14.1,
  t04b: 16.02,
  t05a: 19.7,
};
for (const u of units) {
  u.speechFrom = starts[u.id];
  u.speechTo = u.speechFrom + (u.speechEnd - u.speechStart);
}

const beats = [
  { id: 'hook', start: 0, end: byId.t02a.speechFrom - 0.15 },
  { id: 'split', start: 0, end: byId.t03a.speechFrom - 0.15 },
  { id: 'why', start: 0, end: byId.t04a.speechFrom - 0.3 },
  { id: 'number', start: 0, end: byId.t05a.speechFrom - 0.15 },
  { id: 'end', start: 0, end: 22.1 },
];
for (let i = 1; i < beats.length; i++) beats[i].start = beats[i - 1].end;
const b = Object.fromEntries(beats.map((x) => [x.id, x]));

const cues = {
  hookOutline: 1.42,
  framingChip: 0,
  splitRight: b.split.start + 0.12,
  splitRed: byId.t02a.speechFrom,
  splitGreen: byId.t02b.speechFrom,
  citationRing: 0,
  citationDrawer: 0,
  citationPanel: 0,
  whyOutline: b.why.start + 0.4,
  whyStrip: b.why.start + 0.25,
  whyStep2: byId.t03a.speechFrom + 1.7,
  whyStep3: byId.t03a.speechFrom + 3.2,
  numberStrike: byId.t04b.speechFrom + 0.25,
  numberSixteen: byId.t04b.speechFrom + 1.75,
  endUnderline: b.end.start + 0.5,
  endCta: b.end.start + 0.35,
};

const cap = (id, text) => ({ start: byId[id].speechFrom - 0.04, end: byId[id].speechTo + 0.18, text });
const captions = [
  cap('t01a', 'Ever gotten an answer with no source?'),
  cap('t02a', 'Baseline invents a command.'),
  cap('t02b', "Fixed says: I can't answer that."),
  cap('t03a', 'I reproduce it, separate retrieval from generation, rank the fixes.'),
  cap('t04a', 'Sixteen unanswerable.'),
  { start: byId.t04a.speechTo + 0.02, end: 17.2, text: 'Baseline none.' },
  { start: 17.22, end: 19.6, text: 'Fixed all sixteen.' },
  cap('t05a', 'Send three bad answers.'),
];
for (let i = 0; i < captions.length; i++) {
  if (i + 1 < captions.length) captions[i].end = Math.min(captions[i].end, captions[i + 1].start - 0.05);
  if (captions[i].end - captions[i].start < 0.9) captions[i].end = captions[i].start + 0.9;
}
captions.at(-1).end = 22.1;

const timeline = {
  cut: 'teaser',
  footage: 'real hosted fixture app + authored cards',
  duration: 22.1,
  fps: 30,
  width: 1920,
  height: 1080,
  beats: beats.map((x) => ({ ...x, start: +x.start.toFixed(3), end: +x.end.toFixed(3) })),
  cues: Object.fromEntries(Object.entries(cues).map(([k, v]) => [k, +v.toFixed(3)])),
  vo: units.map((u) => ({
    id: u.id,
    text: u.text,
    speed: u.speed,
    file: path.relative(root, u.file),
    start: +u.speechFrom.toFixed(3),
    end: +u.speechTo.toFixed(3),
    fileStart: +(u.speechFrom - u.speechStart).toFixed(3),
  })),
  captions: captions.map((c) => ({ start: +c.start.toFixed(3), end: +c.end.toFixed(3), text: c.text })),
};

fs.writeFileSync(path.join(compDir, 'timeline-teaser.json'), JSON.stringify(timeline, null, 2));

const ts = (s, sep) => {
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = Math.floor(s % 60);
  const ms = Math.round((s - Math.floor(s)) * 1000);
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(sec).padStart(2, '0')}${sep}${String(ms).padStart(3, '0')}`;
};
fs.writeFileSync(
  path.join(outDir, 'rag-proof-teaser-22s.srt'),
  timeline.captions.map((c, i) => `${i + 1}\n${ts(c.start, ',')} --> ${ts(c.end, ',')}\n${c.text}\n`).join('\n'),
);

console.log(JSON.stringify({ duration: timeline.duration, beats, cues, captions }, null, 2));
