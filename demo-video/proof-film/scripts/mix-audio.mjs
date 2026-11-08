// Mix narration onto the timeline and add a restrained bed + two payoff hits.
import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';

const root = path.resolve('proof-film');
const cut = process.argv[2] || 'primary';
const TL = JSON.parse(fs.readFileSync(path.join(root, 'compositions', `timeline-${cut}.json`), 'utf8'));

const inputs = [];
const filters = [];
TL.vo.forEach((u, i) => {
  const file = path.join(root, u.file);
  inputs.push('-i', file);
  const ms = Math.round(u.fileStart * 1000);
  filters.push(`[${i}:a]aresample=48000,aformat=channel_layouts=stereo,adelay=${ms}|${ms}[a${i}]`);
});
const mixIn = TL.vo.map((_, i) => `[a${i}]`).join('');
const voLabel = `[vo]`;

// bed + hits are generated separately
const bed = path.join(root, 'audio', `bed-${cut}.wav`);
const bedIdx = TL.vo.length;
inputs.push('-i', bed);
filters.push(`[${bedIdx}:a]aresample=48000,aformat=channel_layouts=stereo[bed]`);

filters.push(`${mixIn}amix=inputs=${TL.vo.length}:normalize=0,highpass=f=70,alimiter=limit=0.95[vo]`);
filters.push(`[vo][bed]amix=inputs=2:normalize=0,alimiter=limit=0.95,atrim=0:${TL.duration}[mix]`);

const out = path.join(root, 'audio', `mix-${cut}.wav`);
const args = [
  '-hide_banner', '-y',
  ...inputs,
  '-filter_complex', filters.join(';'),
  '-map', '[mix]',
  '-ar', '48000', '-ac', '2', '-c:a', 'pcm_s24le',
  out,
];
const r = spawnSync('ffmpeg', args, { encoding: 'utf8', maxBuffer: 64 * 1024 * 1024 });
if (r.status !== 0) {
  console.error(r.stderr);
  process.exit(1);
}
console.log('wrote', out);
