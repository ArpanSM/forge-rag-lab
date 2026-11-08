// Render deterministic frames with Playwright. Serves proof-film over HTTP.
// Usage:
//   node proof-film/scripts/render.mjs stills 0,3,8,14,19,23,30,36,39,44
//   node proof-film/scripts/render.mjs frames [--cut primary] [--layout 16x9] [--from 0 --to N]
import { chromium } from 'playwright';
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';

const ROOT = path.resolve('proof-film');
const mode = process.argv[2] || 'stills';
const arg = (name, dflt) => {
  const i = process.argv.indexOf('--' + name);
  return i >= 0 ? process.argv[i + 1] : dflt;
};
const cut = arg('cut', 'primary');
const layout = arg('layout', '16x9');
const W = layout === 'square' ? 1080 : 1920;
const H = 1080;

const MIME = {
  '.html': 'text/html',
  '.js': 'text/javascript',
  '.json': 'application/json',
  '.png': 'image/png',
  '.css': 'text/css',
  '.woff2': 'font/woff2',
};

function serve() {
  return new Promise((resolve) => {
    const server = http.createServer((req, res) => {
      const url = decodeURIComponent(req.url.split('?')[0]);
      const file = path.join(ROOT, url);
      if (!file.startsWith(ROOT) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) {
        res.writeHead(404);
        res.end('not found');
        return;
      }
      res.writeHead(200, { 'Content-Type': MIME[path.extname(file)] || 'application/octet-stream' });
      fs.createReadStream(file).pipe(res);
    });
    server.listen(0, '127.0.0.1', () => resolve(server));
  });
}

async function main() {
  const server = await serve();
  const port = server.address().port;
  const browser = await chromium.launch({ channel: 'chrome' });
  const page = await browser.newPage({
    viewport: { width: W, height: H },
    deviceScaleFactor: 1,
    colorScheme: 'light',
  });
  page.on('console', (m) => {
    if (m.type() === 'error') console.error('[page]', m.text());
  });
  const pagePath = layout === 'square' ? 'compositions/square.html' : `compositions/film.html?cut=${cut}&layout=${layout}`;
  await page.goto(`http://127.0.0.1:${port}/${pagePath}`, {
    waitUntil: 'networkidle',
  });
  await page.waitForFunction(() => window.__ready === true || window.__error, null, { timeout: 30000 });
  const err = await page.evaluate(() => window.__error);
  if (err) throw new Error(err);
  const dur = await page.evaluate(() => window.DUR);
  const fps = await page.evaluate(() => window.FPS);
  console.log('duration', dur, 'fps', fps, 'size', W + 'x' + H);

  if (mode === 'stills') {
    const times = (process.argv[3] || '0,3,8,14,19,23,30,36,39,44').split(',').map(Number);
    const dir = path.join(ROOT, 'qa', 'stills');
    fs.mkdirSync(dir, { recursive: true });
    for (const t of times) {
      await page.evaluate((tt) => window.seek(tt), t);
      await page.waitForTimeout(120);
      const file = path.join(dir, `${cut}-${String(t).replace('.', '_')}.png`);
      await page.screenshot({ path: file });
      console.log('still', file);
    }
  } else {
    const from = Number(arg('from', 0));
    const to = Number(arg('to', Math.ceil(dur * fps)));
    const dir = path.join(ROOT, 'render', cut + '-' + layout);
    fs.rmSync(dir, { recursive: true, force: true });
    fs.mkdirSync(dir, { recursive: true });
    for (let i = from; i < to; i++) {
      const t = i / fps;
      await page.evaluate((tt) => window.seek(tt), t);
      await page.screenshot({
        path: path.join(dir, `f${String(i).padStart(5, '0')}.jpg`),
        type: 'jpeg',
        quality: 95,
      });
      if (i % 90 === 0) console.log('frame', i, '/', to);
    }
    console.log('rendered', to - from, 'frames to', dir);
  }

  await browser.close();
  server.close();
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
