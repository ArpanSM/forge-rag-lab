/* 1:1 teaser composition, 1080x1080. Deterministic seek(t). */
(() => {
  const stage = document.getElementById('stage');
  const shotsRoot = document.getElementById('shots');
  const captionBar = document.getElementById('captionBar');
  let T = null;
  const R = {};
  const shotEls = {};
  const clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
  const ramp = (t, a, b) => clamp((t - a) / (b - a));
  const easeOut = (p) => 1 - Math.pow(1 - p, 3);

  function el(tag, cls, parent, text) {
    const n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    (parent || shotsRoot).appendChild(n);
    return n;
  }
  function pos(n, x, y, w, h) {
    n.style.position = 'absolute';
    if (x != null) n.style.left = x + 'px';
    if (y != null) n.style.top = y + 'px';
    if (w != null) n.style.width = w + 'px';
    if (h != null) n.style.height = h + 'px';
    return n;
  }
  function crop(parent, { src, box, x, y, w, h }) {
    const wrap = el('div', 'ui-crop', parent);
    pos(wrap, x, y, w, h);
    const img = new Image();
    img.src = src;
    const k = w / box.w;
    img.style.position = 'absolute';
    img.style.width = 1920 * k + 'px';
    img.style.height = 'auto';
    img.style.maxWidth = 'none';
    img.style.left = -box.x * k + 'px';
    img.style.top = -box.y * k + 'px';
    wrap.appendChild(img);
    return { wrap, img, k };
  }
  function ring(parent, { box, cropBox, k, x = 0, y = 0, color = 'ember' }) {
    const r = el('div', 'ring ' + (color === 'moss' ? 'moss' : ''), parent);
    r.style.left = (x + (box.x - cropBox.x) * k) + 'px';
    r.style.top = (y + (box.y - cropBox.y) * k) + 'px';
    r.style.width = box.w * k + 'px';
    r.style.height = box.h * k + 'px';
    return r;
  }
  function shot(id) {
    const b = T.beats.find((x) => x.id === id);
    if (!b) return null;
    const n = el('section', 'shot', shotsRoot);
    n.id = 'shot-' + id;
    shotEls[id] = n;
    return n;
  }
  const cue = (name, dflt) => (typeof T.cues[name] === 'number' ? T.cues[name] : dflt);
  const ASSET = (f) => '../captures/' + f;

  const BOX = {
    card: { x: 674, y: 178, w: 900, h: 316 },
    hook: { x: 674, y: 230, w: 900, h: 250 },
    invented: { x: 705, y: 261.2, w: 838, h: 30 },
    noCitation: { x: 769, y: 445.5, w: 92.1, h: 23.8 },
    fixed: { x: 674, y: 178, w: 900, h: 316 },
    withheld: { x: 774, y: 282.2, w: 748, h: 24 },
    missedRow: { x: 356, y: 1898, w: 1208, h: 42 },
  };

  function buildHook() {
    const s = shot('hook');
    if (!s) return;
    pos(el('div', 'kicker ember', s), 60, 48).innerHTML = '<span class="dot"></span>The failure';
    const title = pos(el('div', 'display title', s), 56, 68);
    title.style.fontSize = '84px';
    title.textContent = 'Has this happened to you?';
    const note = pos(el('div', 'mono', s), null, 50);
    note.style.right = '60px';
    note.style.fontSize = '11px';
    note.style.color = 'var(--muted)';
    note.textContent = 'Real hosted UI · fixture mode';
    const proof = pos(el('div', 'mono', s), 60, 900);
    proof.style.fontSize = '18px';
    proof.style.color = 'var(--moss)';
    proof.textContent = 'Proof of concept · synthetic corpus';
    const sub = pos(el('div', 'mono subnote', s), 60, 166);
    sub.textContent = 'Baseline pipeline · no citation';

    const z = pos(el('div', '', s), 20, 200, 1040, 289);
    z.style.transformOrigin = '50% 50%';
    const c = crop(z, { src: ASSET('10-baseline.png'), box: BOX.hook, x: 0, y: 0, w: 1040, h: 289 });
    const outline = ring(z, { box: BOX.noCitation, cropBox: BOX.hook, k: c.k });
    const stamp = pos(el('div', 'display stamp', s), 60, 540);
    stamp.style.color = 'var(--ember-deep)';
    stamp.textContent = 'One answer. Zero sources.';
    R.hook = { z, c, outline, stamp };
  }

  function buildSplit() {
    const s = shot('split');
    if (!s) return;
    pos(el('div', 'kicker', s), 60, 50).innerHTML = '<span class="dot"></span>The same question';
    pos(el('div', 'mono q', s), 60, 74).textContent = 'Exact on-premises install command';
    const proof = pos(el('div', 'mono', s), null, 50);
    proof.style.right = '60px';
    proof.style.fontSize = '11px';
    proof.style.color = 'var(--moss)';
    proof.textContent = 'Proof of concept · synthetic corpus';

    const l1 = pos(el('div', 'mono lab', s), 60, 112);
    l1.innerHTML = '<span class="dot"></span>Baseline · invents';
    const c1 = crop(s, { src: ASSET('10-baseline.png'), box: BOX.card, x: 50, y: 138, w: 980, h: 344 });
    const r1 = ring(s, { box: BOX.invented, cropBox: BOX.card, k: c1.k, x: 50, y: 138 });

    const l2 = pos(el('div', 'mono lab moss', s), 60, 502);
    l2.innerHTML = '<span class="dot moss"></span>Fixed · refuses to guess';
    const c2 = crop(s, { src: ASSET('20-fixed-abstain.png'), box: BOX.fixed, x: 50, y: 528, w: 980, h: 344 });
    const r2 = ring(s, { box: BOX.withheld, cropBox: BOX.fixed, k: c2.k, x: 50, y: 528, color: 'moss' });
    R.split = { r1, r2 };
  }

  function buildWhy() {
    const s = shot('why');
    if (!s) return;
    const health = pos(el('div', 'health', s), 0, 0, 1080, 1080);
    const img = new Image();
    img.src = ASSET('70-health-full.png');
    img.style.width = '1080px';
    img.style.height = 'auto';
    img.style.left = '0';
    img.style.top = '0';
    health.appendChild(img);
    const band = pos(el('div', 'band', s), 0, 0, 1080, 590);
    pos(el('div', 'kicker moss', s), 60, 48).style.zIndex = '2';
    const kick = s.querySelector('.kicker');
    kick.innerHTML = '<span class="dot moss"></span>How I would work on your corpus';

    // 55..1010, the stack's own margins.
    const steps = [
      ['01', 'Reproduce', 'Same 16 questions. Your docs.'],
      ['02', 'Measure', 'Retrieval vs generation, separately.'],
      ['03', 'Fix + gate', 'Before/after, then a regression gate.'],
    ];
    R.why = { img, steps: [], scene: s };
    steps.forEach(([n, h, b], i) => {
      const card = pos(el('div', 'step', s), 55, 100 + i * 160, 955, 140);
      const bar = pos(el('div', 'bar', card), 0, 0, 0, 4);
      bar.style.background = 'var(--moss)';
      el('div', 'num', card, n);
      el('div', 'h', card, h);
      el('div', 'b', card, b);
      R.why.steps.push({ card, bar, w: 955 });
    });
    const ringRow = pos(el('div', 'ringrow', s), 200, 700, 680, 24);
    R.why.ringRow = ringRow;
    R.why.kick = kick;
  }

  function buildNumber() {
    const s = shot('number');
    if (!s) return;
    const bg = pos(el('div', 'bg', s), 0, 0, 1080, 1080);
    const bgc = crop(bg, { src: ASSET('70-health-full.png'), box: { x: 0, y: 2800, w: 1920, h: 1080 }, x: 0, y: 0, w: 1080, h: 608 });
    pos(el('div', 'veil', s), 0, 0, 1080, 1080);
    const card = pos(el('div', 'frame', s), 60, 90, 960, 600);

    pos(el('div', 'kicker', card), 40, 34).innerHTML = '<span class="dot moss"></span>The number · n = 16';
    const bl = pos(el('div', 'mono lab', card), 66, 108);
    bl.style.color = 'var(--ember-deep)';
    bl.textContent = 'Baseline';
    const bn = pos(el('div', 'num', card), 50, 132, 440, 160);
    bn.style.whiteSpace = 'nowrap';
    bn.style.color = 'var(--ember-deep)';
    bn.textContent = '0 / 16';
    pos(el('div', 'sub', card), 66, 288).textContent = 'refused none';
    const strike = pos(el('div', 'strike', card), 58, 186, 300, 7);

    const fl = pos(el('div', 'mono lab', card), 520, 108);
    fl.style.color = 'var(--moss-deep)';
    fl.textContent = 'Fixed';
    const fw = pos(el('div', 'sixteen', card), 500, 132, 440, 160);
    fw.style.whiteSpace = 'nowrap';
    const fn = pos(el('div', 'num', fw), 0, 0);
    fn.style.color = 'var(--moss-deep)';
    fn.textContent = '16 / 16';
    const fs = pos(el('div', 'sub', card), 520, 288);
    fs.style.color = 'var(--moss-deep)';
    fs.textContent = 'refused all sixteen';

    const arrow = pos(el('div', '', card), 452, 186, 24, 24);
    arrow.style.borderRight = '3px solid rgba(29,30,28,.28)';
    arrow.style.borderBottom = '3px solid rgba(29,30,28,.28)';
    arrow.style.transform = 'rotate(-45deg)';

    const check = pos(el('div', 'check', card), 850, 286);
    check.innerHTML = '<svg width="42" height="42" viewBox="0 0 58 58" fill="none"><circle cx="29" cy="29" r="28" stroke="#0b5747" stroke-width="3"/><path d="M17 30.5l8 8 16-18" stroke="#0b5747" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/></svg>';

    const srcLabel = el('div', 'mono', card, 'From the health report');
    srcLabel.style.cssText = 'position:absolute;left:40px;top:350px;font-size:11px;';
    const srcWrap = crop(card, { src: ASSET('70-health-full.png'), box: { x: 353, y: 1884, w: 1214, h: 66 }, x: 40, y: 372, w: 880, h: 47.8 });
    srcWrap.wrap.style.border = '1px solid rgba(29,30,28,.12)';
    const foot = pos(el('div', 'mono', card), 40, 500);
    foot.style.fontSize = '10px';
    foot.style.color = 'var(--muted)';
    foot.textContent = 'N = 16 · all sixteen unanswerable questions';
    R.number = { card, strike, fw, fl, fs, check, bn };
  }

  function buildEnd() {
    const s = shot('end');
    if (!s) return;
    pos(el('div', 'kicker ember', s), 60, 80).innerHTML = '<span class="dot"></span>Forge RAG Lab';
    const head = pos(el('div', 'display headline', s), 56, 112);
    head.textContent = 'Send three bad answers.';
    const sub = pos(el('div', 'display sub', s), 60, 222);
    sub.textContent = "I'll name the failed layer.";
    const ul = pos(el('div', 'uline', s), 62, 200, 0, 4);
    const cta = pos(el('div', 'cta', s), 60, 300);
    cta.innerHTML = '<span>Send 3 bad answers</span><span style="font-size:38px">→</span>';
    cta.style.opacity = '1';
    const url = pos(el('div', 'url', s), 62, 424);
    url.textContent = 'github.com/ArpanSM/forge-rag-lab';
    const proof = pos(el('div', 'proof', s), 62, 478);
    proof.style.fontSize = '48px';
    proof.style.opacity = '1';
    proof.textContent = 'Proof of concept · synthetic Helios corpus\nThe method applies to your docs.';
    pos(el('div', 'ghost', s), null, null).textContent = '16/16';
    R.end = { head, sub, ul, cta, url, proof };
  }

  function build() {
    buildHook();
    buildSplit();
    buildWhy();
    buildNumber();
    buildEnd();
  }

  function updateHook(t, b) {
    const r = R.hook;
    if (!r) return;
    const p = ramp(t, b.start, b.end);
    r.z.style.transform = `scale(${(1.02 + 0.02 * p).toFixed(4)})`;
    const q = ramp(t, cue('hookOutline', 1.4), cue('hookOutline', 1.4) + 0.4);
    r.outline.style.opacity = String(q);
    r.stamp.style.opacity = '1';
  }
  function updateSplit(t, b) {
    const r = R.split;
    if (!r) return;
    const a = ramp(t, cue('splitRed', b.start + 0.4), cue('splitRed', b.start + 0.4) + 0.4);
    r.r1.style.opacity = String(a);
    r.r1.style.transform = `scale(${0.97 + 0.03 * easeOut(a)})`;
    const c = ramp(t, cue('splitGreen', b.start + 2.2), cue('splitGreen', b.start + 2.2) + 0.4);
    r.r2.style.opacity = String(c);
    r.r2.style.transform = `scale(${0.97 + 0.03 * easeOut(c)})`;
  }
  function updateWhy(t, b) {
    const r = R.why;
    if (!r) return;
    const p = ramp(t, b.start, b.end);
    const off = 654 + 30 * p;
    r.img.style.top = `${-off * 0.5625}px`;
    r.ringRow.style.top = `${(BOX.missedRow.y - off) * 0.5625}px`;
    r.ringRow.style.left = `${356 * 0.5625}px`;
    r.ringRow.style.width = `${1208 * 0.5625}px`;
    r.ringRow.style.height = `${42 * 0.5625}px`;
    const rq = ramp(t, cue('whyOutline', b.start + 0.4), cue('whyOutline', b.start + 0.4) + 0.4);
    r.ringRow.style.opacity = String(rq);
    const cues = [cue('whyStrip', b.start + 0.25), cue('whyStep2', b.start + 2.0), cue('whyStep3', b.start + 3.5)];
    r.steps.forEach(({ card, bar, w }, i) => {
      card.style.opacity = '1';
      card.style.transform = 'none';
      const q = ramp(t, cues[i], cues[i] + 0.32);
      bar.style.width = `${w * easeOut(q)}px`;
    });
  }
  function updateNumber(t, b) {
    const r = R.number;
    if (!r) return;
    const p = ramp(t, b.start, b.end);
    r.card.style.transform = `scale(${(1.02 + 0.02 * p).toFixed(4)})`;
    r.card.style.transformOrigin = '50% 50%';
    const s = ramp(t, cue('numberStrike', b.start + 2.5), cue('numberStrike', b.start + 2.5) + 0.34);
    r.strike.style.opacity = String(0.92 * s);
    r.strike.style.width = `${360 * easeOut(s)}px`;
    const q = ramp(t, cue('numberSixteen', b.start + 4.0), cue('numberSixteen', b.start + 4.0) + 0.45);
    r.fw.style.opacity = String(q);
    r.fw.style.transform = `translateY(${(1 - easeOut(q)) * 18}px)`;
    r.fl.style.opacity = String(q);
    r.fs.style.opacity = String(q);
    r.check.style.opacity = String(ramp(t, cue('numberSixteen', b.start + 4.0) + 0.25, cue('numberSixteen', b.start + 4.0) + 0.55));
  }
  function updateEnd(t, b) {
    const r = R.end;
    if (!r) return;
    r.ul.style.width = `${520 * easeOut(ramp(t, cue('endUnderline', b.start + 0.5), cue('endUnderline', b.start + 0.5) + 0.5))}px`;

  }

  const U = { hook: updateHook, split: updateSplit, why: updateWhy, number: updateNumber, end: updateEnd };

  function seek(t) {
    if (!T) return;
    t = clamp(t, 0, T.duration);
    for (const b of T.beats) {
      const on = t >= b.start && t < b.end;
      const n = shotEls[b.id];
      if (!n) continue;
      n.style.display = on ? 'block' : 'none';
      if (on) U[b.id]?.(t, b);
    }
    let active = null;
    for (const c of T.captions || []) if (t >= c.start && t < c.end) { active = c; break; }
    if (!active) {
      captionBar.style.opacity = '0';
      captionBar.textContent = '';
    } else {
      if (captionBar.textContent !== active.text) captionBar.textContent = active.text;
      const fade = Math.min(1, (t - active.start) / 0.12, (active.end - t) / 0.12);
      captionBar.style.opacity = String(clamp(fade));
    }
  }

  async function preload() {
    const srcs = ['10-baseline.png', '20-fixed-abstain.png', '70-health-full.png'].map(ASSET);
    await Promise.all(srcs.map((src) => new Promise((res) => {
      const im = new Image();
      im.onload = () => res();
      im.onerror = () => res();
      im.src = src;
    })));
  }

  async function main() {
    const res = await fetch('timeline-teaser.json', { cache: 'no-store' });
    T = await res.json();
    await preload();
    build();
    window.TIMELINE = T;
    window.DUR = T.duration;
    window.FPS = T.fps;
    window.seek = seek;
    window.__ready = true;
    seek(0);
  }
  main().catch((e) => { console.error(e); window.__error = String(e); });
})();
