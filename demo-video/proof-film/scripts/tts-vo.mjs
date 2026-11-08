// Generate LFM3 narration units. Run from demo-video/ with ffmpeg on PATH.
import { lfm3Engine } from '../../lfm3-engine.mjs';
import fs from 'node:fs';
import path from 'node:path';

const OUT = path.resolve('proof-film/audio/vo');
fs.mkdirSync(OUT, { recursive: true });

const units = [
  { id: 'u01a', speed: 1.0, text: 'Has your assistant answered from an old policy — or invented a command with no source?' },
  { id: 'u02a', speed: 1.0, text: 'Proof of concept: synthetic docs.' },
  { id: 'u02b', speed: 1.0, text: 'The method works on yours.' },
  { id: 'u03a', speed: 0.99, text: "Ask something the docs don't contain." },
  { id: 'u03b', speed: 0.99, text: 'Baseline invents a command.' },
  { id: 'u03c', speed: 0.99, text: "Fixed says: I can't answer that." },
  { id: 'u04a', speed: 0.98, text: 'Every claim cites a version, a page, a block.' },
  { id: 'u04b', speed: 0.98, text: 'Open it; the source is highlighted.' },
  { id: 'u05a', speed: 0.99, text: 'I reproduce it on your corpus, separate retrieval from generation, and rank the fixes.' },
  { id: 'u06a', speed: 0.96, text: 'Sixteen unanswerable questions.' },
  { id: 'u06b', speed: 0.96, text: 'Baseline refused none.' },
  { id: 'u06c', speed: 0.96, text: 'Fixed refused all sixteen.' },
  { id: 'u07a', speed: 0.99, text: 'Send me three bad answers.' },
  { id: 'u07b', speed: 0.99, text: "I'll tell you which layer failed." },
];

const engine = lfm3Engine({ voice: 'male', lang: 'en' });
const force = process.argv.includes('--force');
const manifest = [];

for (const unit of units) {
  const file = path.join(OUT, `${unit.id}.wav`);
  if (!force && fs.existsSync(file)) {
    const b = fs.readFileSync(file);
    manifest.push({ ...unit, file });
    console.log(`${unit.id} cached (${(b.length / 4 / 24000).toFixed(2)} s)`);
    continue;
  }
  process.stdout.write(`${unit.id} … `);
  const wav = await engine.generate(unit.text, { speed: unit.speed });
  fs.writeFileSync(file, wav);
  manifest.push({ ...unit, file });
  console.log(`${(wav.length / 4 / 24000).toFixed(2)} s`);
}

fs.writeFileSync(path.join(OUT, 'manifest.json'), JSON.stringify(manifest, null, 2));
