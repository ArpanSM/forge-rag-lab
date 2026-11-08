// Compute the VO clock from measured speech bounds, then write timeline.json,
// a self-contained timeline.js, and matching SRT/VTT.
import fs from 'node:fs';
import path from 'node:path';

const root = path.resolve('proof-film');
const voDir = path.join(root, 'audio/vo');
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
    if (cid === 'fmt ') {
      sr = b.readUInt32LE(body + 4);
    } else if (cid === 'data') {
      data = b.subarray(body, body + size);
    }
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
  const peak = Math.max(...rms);
  const thr = peak * 0.02;
  let first = 0;
  let last = rms.length - 1;
  while (first < rms.length && rms[first] <= thr) first++;
  while (last >= 0 && rms[last] <= thr) last--;
  return { dur: n / sr, speechStart: first * 0.02, speechEnd: (last + 1) * 0.02 };
}

const manifest = JSON.parse(fs.readFileSync(path.join(voDir, 'manifest.json'), 'utf8'));
const units = manifest.map((u) => ({ ...u, ...readWav(u.file) }));

const byId = Object.fromEntries(units.map((u) => [u.id, u]));

// Placement: start of speech for each unit, and the gap after it.
const gaps = {
  u01a: 0.85,
  u02a: 0.22,
  u02b: 0.55,
  u03a: 0.18,
  u03b: 0.22,
  u03c: 0.55,
  u04a: 0.2,
  u04b: 0.85,
  u05a: 0.95,
  u06a: 0.45,
  u06b: 0.4,
  u06c: 0.95,
  u07a: 0.35,
  u07b: 0.45,
};

let cursor = 0.32;
for (const u of units) {
  u.at = cursor;
  u.speechAt = u.at - u.speechStart * 0 + 0; // speech begins at u.at
  u.speechFrom = u.at;
  u.speechTo = u.at + (u.speechEnd - u.speechStart);
  cursor = u.speechTo + gaps[u.id];
}

const t = (id) => ({ start: byId[id].speechFrom, end: byId[id].speechTo });

const beats = [
  { id: 'hook', start: 0, end: byId.u02a.speechFrom - 0.15 },
  { id: 'framing', start: 0, end: byId.u03a.speechFrom - 0.15 },
  { id: 'split', start: 0, end: byId.u04a.speechFrom - 0.15 },
  { id: 'citations', start: 0, end: byId.u05a.speechFrom - 0.15 },
  { id: 'why', start: 0, end: byId.u06a.speechFrom - 0.35 },
  { id: 'number', start: 0, end: byId.u07a.speechFrom - 0.2 },
  { id: 'end', start: 0, end: byId.u07b.speechTo + 0.45 },
];
for (let i = 1; i < beats.length; i++) beats[i].start = beats[i - 1].end;

const b = Object.fromEntries(beats.map((x) => [x.id, x]));

const cues = {
  hookOutline: byId.u01a.speechFrom + 2.35,
  framingChip: b.framing.start + 0.55,
  splitRight: b.split.start + 0.22,
  splitRed: byId.u03b.speechFrom,
  splitGreen: byId.u03c.speechFrom,
  citationRing: b.citations.start + 1.45,
  citationDrawer: byId.u04b.speechFrom - 0.3,
  citationPanel: byId.u04b.speechFrom + 0.25,
  whyOutline: b.why.start + 0.6,
  whyStrip: byId.u05a.speechFrom + 0.25,
  whyStep2: byId.u05a.speechFrom + 2.35,
  whyStep3: byId.u05a.speechFrom + 2.95,
  numberStrike: byId.u06b.speechFrom,
  numberSixteen: byId.u06c.speechFrom,
  endUnderline: b.end.start + 0.95,
  endCta: b.end.start + 1.2,
};

const cap = (id, text) => ({ start: byId[id].speechFrom - 0.04, end: byId[id].speechTo + 0.22, text });

// Split u05a at its measured pause after "generation," (4.63 s in the clip).
const u5 = byId.u05a;
const splitAt = u5.speechFrom + (4.63 - u5.speechStart);
const captions = [
  cap('u01a', 'Has your assistant answered from an old policy —\nor invented a command with no source?'),
  cap('u02a', 'Proof of concept: synthetic docs.'),
  cap('u02b', 'The method works on yours.'),
  cap('u03a', "Ask something the docs don't contain."),
  cap('u03b', 'Baseline invents a command.'),
  cap('u03c', "Fixed says: I can't answer that."),
  cap('u04a', 'Every claim cites a version, a page, a block.'),
  cap('u04b', 'Open it; the source is highlighted.'),
  { start: u5.speechFrom - 0.04, end: splitAt - 0.02, text: 'I reproduce it on your corpus, separate retrieval from generation,' },
  { start: splitAt + 0.02, end: u5.speechTo + 0.2, text: 'and rank the fixes.' },
  cap('u06a', 'Sixteen unanswerable questions.'),
  cap('u06b', 'Baseline refused none.'),
  cap('u06c', 'Fixed refused all sixteen.'),
  cap('u07a', 'Send me three bad answers.'),
  cap('u07b', "I'll tell you which layer failed."),
];

// Extend the final caption to the end card's hold, and ensure every caption
// gets at least 1.15 s on screen without overlapping the next.
for (let i = 0; i < captions.length; i++) {
  const c = captions[i];
  if (i === captions.length - 1) c.end = beats.at(-1).end;
  if (i + 1 < captions.length) c.end = Math.min(c.end, captions[i + 1].start - 0.06);
  if (c.end - c.start < 1.15) c.end = c.start + 1.15;
}

const timeline = {
  cut: 'primary',
  footage: 'real hosted fixture app + authored cards',
  duration: +beats.at(-1).end.toFixed(3),
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
  captions: captions.map((c) => ({
    start: +c.start.toFixed(3),
    end: +c.end.toFixed(3),
    text: c.text,
  })),
};

fs.writeFileSync(path.join(compDir, 'timeline-primary.json'), JSON.stringify(timeline, null, 2));
fs.writeFileSync(
  path.join(compDir, 'timeline-primary.js'),
  `window.TIMELINE = ${JSON.stringify(timeline, null, 2)};\n`,
);

// SRT / VTT
const ts = (s, sep) => {
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = Math.floor(s % 60);
  const ms = Math.round((s - Math.floor(s)) * 1000);
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(sec).padStart(2, '0')}${sep}${String(ms).padStart(3, '0')}`;
};
const srt = timeline.captions
  .map((c, i) => `${i + 1}\n${ts(c.start, ',')} --> ${ts(c.end, ',')}\n${c.text}\n`)
  .join('\n');
fs.writeFileSync(path.join(outDir, 'rag-proof-45s.srt'), srt);
const vtt =
  'WEBVTT\n\n' +
  timeline.captions
    .map((c, i) => `${i + 1}\n${ts(c.start, '.')} --> ${ts(c.end, '.')}\n${c.text}\n`)
    .join('\n');
fs.writeFileSync(path.join(outDir, 'rag-proof-45s.vtt'), vtt);

console.log(JSON.stringify({ duration: timeline.duration, beats, cues }, null, 2));
console.log('\nVO placement:');
for (const u of units) console.log(u.id, u.at.toFixed(2), '→', u.speechTo.toFixed(2), `(${u.speechEnd - u.speechStart > 0 ? (u.speechTo - u.speechFrom).toFixed(2) : 0}s)`);
console.log('\nCaptions:');
for (const c of timeline.captions) console.log(c.start.toFixed(2), c.end.toFixed(2), c.text);
