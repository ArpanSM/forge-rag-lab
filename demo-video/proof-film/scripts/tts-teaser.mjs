// Teaser narration units (22 s cut). Run from demo-video/ with ffmpeg on PATH.
import { lfm3Engine } from '../../lfm3-engine.mjs';
import fs from 'node:fs';
import path from 'node:path';

const OUT = path.resolve('proof-film/audio/vo-teaser');
fs.mkdirSync(OUT, { recursive: true });

const units = [
  { id: 't01a', speed: 1.0, text: 'Ever gotten an answer with no source?' },
  { id: 't02a', speed: 1.0, text: 'Baseline invents a command.' },
  { id: 't02b', speed: 1.0, text: "Fixed says: I can't answer that." },
  { id: 't03a', speed: 0.99, text: 'I reproduce it, separate retrieval from generation, rank the fixes.' },
  { id: 't04a', speed: 0.97, text: 'Sixteen unanswerable.' },
  { id: 't04b', speed: 0.97, text: 'Baseline none. Fixed all sixteen.' },
  { id: 't05a', speed: 0.99, text: 'Send three bad answers.' },
]

const engine = lfm3Engine({ voice: 'male', lang: 'en' });
const manifest = [];

for (const unit of units) {
  process.stdout.write(`${unit.id} … `);
  const wav = await engine.generate(unit.text, { speed: unit.speed });
  fs.writeFileSync(path.join(OUT, `${unit.id}.wav`), wav);
  manifest.push({ ...unit, file: path.join(OUT, `${unit.id}.wav`) });
  console.log(`${(wav.length / 4 / 24000).toFixed(2)} s`);
}

fs.writeFileSync(path.join(OUT, 'manifest.json'), JSON.stringify(manifest, null, 2));
