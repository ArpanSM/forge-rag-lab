/* Deterministic proof-film composition. Every frame is a function of t. */
(() => {
  const stage = document.getElementById('stage');
  const shotsRoot = document.getElementById('shots');
  const captionBar = document.getElementById('captionBar');
  const params = new URLSearchParams(location.search);
  const CUT = params.get('cut') || 'primary';
  const SQUARE = params.get('layout') === 'square';

  let T = null;
  const R = {};
  const shotEls = {};

  const clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
  const ramp = (t, a, b) => clamp((t - a) / (b - a));
  const easeOut = (p) => 1 - Math.pow(1 - p, 3);
  const easeInOut = (p) => (p < 0.5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2);
  const pad = (n, w = 2) => String(n).padStart(w, '0');

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
  function crop(parent, { src, box, x, y, w, h, radius = 0, cls = '' }) {
    const wrap = el('div', 'ui-crop ' + cls, parent);
    pos(wrap, x, y, w, h);
    wrap.style.borderRadius = radius + 'px';
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
  function ring(parent, { box, cropBox, k, color = 'ember', x = 0, y = 0 }) {
    const r = el('div', 'ring ' + (color === 'moss' ? 'moss' : ''), parent);
    r.style.left = (x + (box.x - cropBox.x) * k) + 'px';
    r.style.top = (y + (box.y - cropBox.y) * k) + 'px';
    r.style.width = box.w * k + 'px';
    r.style.height = box.h * k + 'px';
    return r;
  }
  function shot(id) {
    const beat = T.beats.find((b) => b.id === id);
    if (!beat) return null;
    const n = el('section', 'shot', shotsRoot);
    n.id = 'shot-' + id;
    shotEls[id] = n;
    return n;
  }
  function extraShot(id) {
    if (shotEls[id]) return shotEls[id];
    const n = el('section', 'shot', shotsRoot);
    n.id = 'shot-' + id;
    shotEls[id] = n;
    return n;
  }
  function cue(name, dflt) {
    const v = T.cues[name];
    return typeof v === 'number' ? v : dflt;
  }
  const ASSET = (f) => '../captures/' + f;

  // Viewport screenshots use viewport coordinates (the meta scrollY was 519);
  // the full-page health capture keeps page coordinates.
  const BOX = {
    baselineCard: { x: 674, y: 178, w: 900, h: 316 },
    fixedCard: { x: 674, y: 178, w: 900, h: 316 },
    invented: { x: 705, y: 261.2, w: 838, h: 30 },
    noCitation: { x: 769, y: 445.5, w: 92.1, h: 23.8 },
    withheld: { x: 774, y: 282.2, w: 748, h: 24 },
    claimPanel: { x: 699, y: 365.1, w: 850, h: 347 },
    chip1: { x: 769, y: 461.4, w: 177.4, h: 26.3 },
    drawerBlock: { x: 1350, y: 411, w: 570, h: 370 },
    mark: { x: 1394, y: 532.6, w: 439.5, h: 48 },
    missedRow: { x: 356, y: 1898, w: 1208, h: 42 },
  };

  function buildHook() {
    const s = shot('hook');
    if (!s) return;
    pos(el('div', 'kicker ember', s), 120, 84).innerHTML = '<span class="dot"></span>The failure';
    const title = pos(el('div', 'display hook-title', s), 118, 118);
    title.textContent = 'Has this happened to you?';
    const note = pos(el('div', 'mono ui-note', s), null, 84);
    note.style.right = '120px';
    note.textContent = 'Real hosted UI · fixture mode';
    if (CUT === 'teaser') {
      const proof = pos(el('div', 'mono', s), null, 120);
      proof.style.right = '120px';
      proof.style.fontSize = '22px';
      proof.style.color = 'var(--moss)';
      proof.textContent = 'Proof of concept · synthetic Helios corpus';
    }

    const sub = pos(el('div', 'mono subnote', s), 120, 288);
    sub.textContent = 'Baseline pipeline · no citation';

    const HOOK_BOX = { x: 674, y: 160, w: 900, h: 330 };
    const zoom = pos(el('div', '', s), 140, 326, 1600, 586.7);
    zoom.style.transformOrigin = '50% 50%';
    const c = crop(zoom, { src: ASSET('10-baseline.png'), box: HOOK_BOX, x: 0, y: 0, w: 1600, h: 586.7 });
    const outline = ring(zoom, { box: BOX.noCitation, cropBox: HOOK_BOX, k: c.k });
    outline.dataset.baseTop = outline.style.top;
    R.hook = { zoom, outline, img: c.img, k: c.k, hookBox: HOOK_BOX };

  }

  function buildFraming() {
    const s = shot('framing');
    if (!s) return;
    pos(el('div', 'kicker moss', s), 120, 84).innerHTML = '<span class="dot moss"></span>Proof of concept';
    const title = pos(el('div', 'display title', s), 118, 112);
    title.textContent = 'The method applies to your docs.';
    const uline = pos(el('div', 'uline', s), 120, 200);
    const chips = pos(el('div', 'chips', s), 120, 238);
    const chip = el('div', 'chip moss', chips);
    chip.innerHTML = '<span class="dot moss"></span>Synthetic Helios corpus';
    const chip2 = el('div', 'chip', chips);
    chip2.textContent = 'No real customer data';
    const small = pos(el('div', '', s), 122, 290);
    small.style.fontSize = '19px';
    small.style.color = 'var(--muted)';
    small.textContent = 'Fixture mode. The numbers are development numbers.';

    const fz = pos(el('div', '', s), 170, 318, 1400, 600.4);
    fz.style.transformOrigin = '50% 50%';
    const c = crop(fz, { src: ASSET('10-baseline.png'), box: { ...BOX.baselineCard, h: 386 }, x: 0, y: 0, w: 1400, h: 600.4 });
    c.wrap.setAttribute('data-baseline', 'full');
    R.framing = { uline, chip, chip2, small, zoom: fz };
  }

  function buildSplit() {
    const s = shot('split');
    if (!s) return;
    pos(el('div', 'kicker', s), 80, 78).innerHTML = '<span class="dot"></span>The same question';
    const q = pos(el('div', 'mono q', s), 80, 112);
    q.textContent = 'Exact Helios on-premises install command';
    if (CUT === 'teaser') {
      const proof = pos(el('div', 'mono', s), null, 80);
      proof.style.right = '80px';
      proof.style.fontSize = '22px';
      proof.style.color = 'var(--moss)';
      proof.textContent = 'Proof of concept · synthetic Helios corpus';
    }

    const l = pos(el('div', 'mono lab', s), 80, 156);
    l.style.color = 'var(--ember)';
    l.innerHTML = '<span class="dot"></span>Baseline';
    const rlab = pos(el('div', 'mono lab', s), 980, 156);
    rlab.style.color = 'var(--moss)';
    rlab.innerHTML = '<span class="dot moss"></span>Fixed';

    const cb = crop(s, { src: ASSET('10-baseline.png'), box: BOX.baselineCard, x: 80, y: 208, w: 860, h: 302 });
    const cf = crop(s, { src: ASSET('20-fixed-abstain.png'), box: BOX.fixedCard, x: 980, y: 208, w: 860, h: 302 });

    const ringB = ring(s, { box: BOX.invented, cropBox: BOX.baselineCard, k: cb.k, x: 80, y: 208 });
    const ringF = ring(s, { box: BOX.withheld, cropBox: BOX.fixedCard, k: cf.k, x: 980, y: 208, color: 'moss' });

    const vb = pos(el('div', 'display verdict', s), 80, 552);
    vb.style.color = 'var(--ember)';
    vb.textContent = 'Invents a command.';
    const vf = pos(el('div', 'display verdict', s), 980, 552);
    vf.style.color = 'var(--moss)';
    vf.textContent = 'Refuses to guess.';

    pos(el('div', 'vline', s), null, null);
    const vline = s.querySelector('.vline');
    vline.style.left = '958px';
    vline.style.top = '150px';
    vline.style.height = '560px';

    const foot = pos(el('div', 'mono', s), 80, 856);
    foot.style.fontSize = '16px';
    foot.style.color = 'var(--muted)';
    foot.textContent = 'Same question · same fixture · one refuses the missing evidence';

    R.split = { ringB, ringF, vb, vf };
  }

  function buildCitations() {
    const s = shot('citations');
    if (!s) return;
    pos(el('div', 'kicker moss', s), 120, 82).innerHTML = '<span class="dot moss"></span>The fix · evidence';
    const title = pos(el('div', 'display title', s), 118, 114);
    title.textContent = 'Three claims. Three citations.';
    const fixed = pos(el('div', 'chip fixedchip moss', s), null, 112);
    fixed.style.right = '120px';
    fixed.innerHTML = '<span class="dot moss"></span>Fixed';
    const cz = pos(el('div', '', s), 135, 244, 1650, 673.7);
    cz.style.transformOrigin = '50% 50%';
    const c = crop(cz, { src: ASSET('30-fixed-answer.png'), box: BOX.claimPanel, x: 0, y: 0, w: 1650, h: 673.7 });
    const ringChip = ring(cz, { box: BOX.chip1, cropBox: BOX.claimPanel, k: c.k, x: 0, y: 0, color: 'moss' });
    R.citations = { ringChip, c, zoom: cz, img: c.img, k: c.k };
  }

  function buildCitationsB() {
    if (!T.beats.find((b) => b.id === 'citations')) return;
    const s = extraShot('citationsB');
    pos(el('div', 'kicker moss', s), 120, 82).innerHTML = '<span class="dot moss"></span>Citation open · real UI';
    const title = pos(el('div', 'display title', s), 118, 114);
    title.textContent = 'Version. Page. Block.';

    const rows = [
      ['Version', 'v3', 262],
      ['Page', '2', 402],
      ['Block', 'b4', 542],
    ];
    R.citationsB = { rows: [] };
    for (const [lab, val, y] of rows) {
      const row = pos(el('div', 'meta-row', s), 140, y);
      pos(el('div', 'meta-lab', row), 0, 0).textContent = lab;
      pos(el('div', 'meta-val', row), 0, 24).textContent = val;
      R.citationsB.rows.push(row);
    }
    const rule = pos(el('div', 'meta-rule', s), 100, 258);
    rule.style.height = '430px';
    R.citationsB.rule = rule;

    const c = crop(s, { src: ASSET('40-citation-drawer.png'), box: BOX.drawerBlock, x: 710, y: 196, w: 1080, h: 701 });
    const k = c.k;
    const bracket = pos(el('div', '', s), 710 + (BOX.mark.x - BOX.drawerBlock.x) * k - 26, 196 + (BOX.mark.y - BOX.drawerBlock.y) * k, 6, BOX.mark.h * k);
    bracket.style.background = 'var(--moss)';
    bracket.style.borderRadius = '3px';
    R.citationsB.bracket = bracket;
    R.citationsB.k = k;
    R.citationsB.qlab = null;
  }

  function buildWhy() {
    const s = shot('why');
    if (!s) return;
    const health = pos(el('div', 'health', s), 0, 0, 1920, 1080);
    const img = new Image();
    img.src = ASSET('70-health-full.png');
    img.style.width = '1920px';
    img.style.height = 'auto';
    img.style.left = '0';
    img.style.top = '0';
    health.appendChild(img);

    const ringRow = pos(el('div', 'ringrow', s), 356, 0, 1208, 58);
    const capSpace = pos(el('div', 'caption-space', s), 0, 930, 1920, 150);
    const band = pos(el('div', '', s), 0, 0, 1920, 430);
    band.style.background = 'linear-gradient(to bottom, rgba(245,241,232,.985) 0%, rgba(245,241,232,.96) 58%, rgba(245,241,232,0) 100%)';
    band.style.zIndex = '1';

    const kick = pos(el('div', 'kicker moss', s), 120, 70);
    kick.innerHTML = '<span class="dot moss"></span>How I would work on your corpus';
    kick.style.zIndex = '2';

    // 120..1800 with 40 px gutters: three 533.33 px cards, equal outer margins.
    const CW = 533.333;
    const steps = [
      ['01', 'Reproduce', 'Same 16 questions. Your docs.', 120],
      ['02', 'Measure', 'Retrieval vs generation, separately.', 120 + CW + 40],
      ['03', 'Fix + gate', 'Before/after, then a regression gate.', 120 + 2 * (CW + 40)],
    ];
    R.why = { img, ringRow, steps: [] };
    for (const [n, h, b, x] of steps) {
      const card = pos(el('div', 'step', s), x, 128, CW, 206);
      card.style.zIndex = '2';
      const bar = pos(el('div', 'bar', card), 0, 0, 0, 5);
      bar.style.background = 'var(--moss)';
      pos(el('div', 'num', card), 26, 24).textContent = n;
      pos(el('div', 'h', card), 26, 52).textContent = h;
      pos(el('div', 'b', card), 26, 106, CW - 52, 84).textContent = b;
      R.why.steps.push({ card, bar, w: CW });
    }
    R.why.health = health;
    R.why.capSpace = capSpace;
  }

  function buildNumber() {
    const s = shot('number');
    if (!s) return;
    const bg = pos(el('div', 'bg', s), 0, 0, 1920, 1080);
    const bgc = crop(bg, { src: ASSET('70-health-full.png'), box: { x: 0, y: 2800, w: 1920, h: 1080 }, x: 0, y: 0, w: 1920, h: 1080 });
    bg.style.opacity = '.38';
    bg.dataset.scrollable = '1';
    const bgImg = bg.querySelector('img');
    const veil = pos(el('div', 'veil', s), 0, 0, 1920, 1080);
    veil.style.background = 'rgba(245,241,232,.62)';
    const card = pos(el('div', 'frame card', s), 210, 160, 1500, 680);
    pos(el('div', 'kicker', card), 60, 44).innerHTML = '<span class="dot moss"></span>The number · n = 16';

    const bLab = pos(el('div', 'mono lab', card), 90, 142);
    bLab.style.color = 'var(--ember-deep)';
    bLab.textContent = 'Baseline';
    const bNum = pos(el('div', 'num', card), 70, 176, 640, 240);
    bNum.style.color = 'var(--ember-deep)';
    bNum.textContent = '0 / 16';
    const bSub = pos(el('div', 'sub', card), 92, 436);
    bSub.textContent = 'refused none';

    const strike = pos(el('div', 'strike', card), 80, 290, 570, 11);
    strike.style.background = 'var(--ember-deep)';

    const fLab = pos(el('div', 'mono lab', card), 820, 142);
    fLab.style.color = 'var(--moss)';
    fLab.textContent = 'Fixed';
    const fWrap = pos(el('div', 'sixteen', card), 790, 176, 640, 240);
    const fNum = pos(el('div', 'num', fWrap), 0, 0);
    fNum.style.color = 'var(--moss-deep)';
    fNum.textContent = '16 / 16';
    const fSub = pos(el('div', 'sub', card), 822, 436);
    fSub.style.color = 'var(--moss)';
    fSub.textContent = 'refused all sixteen';

    const arrow = pos(el('div', '', card), 744, 290, 28, 28);
    arrow.style.borderRight = '3px solid rgba(29,30,28,.28)';
    arrow.style.borderBottom = '3px solid rgba(29,30,28,.28)';
    arrow.style.transform = 'rotate(-45deg)';
    arrow.style.width = '24px';
    arrow.style.height = '24px';
    arrow.style.top = '302px';
    arrow.style.left = '744px';

    const check = pos(el('div', 'check', card), 1356, 424);
    check.innerHTML = '<svg width="58" height="58" viewBox="0 0 58 58" fill="none"><circle cx="29" cy="29" r="28" stroke="#0b5747" stroke-width="3"/><path d="M17 30.5l8 8 16-18" stroke="#0b5747" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/></svg>';

    // The number's denominator, shown from the real health report.
    pos(el('div', 'mono', card), 60, 506).textContent = 'From the health report';
    const srcWrap = crop(card, {
      src: ASSET('70-health-full.png'),
      box: { x: 353, y: 1884, w: 1214, h: 66 },
      x: 60, y: 534, w: 1250, h: 67.9, radius: 0,
    });
    srcWrap.wrap.style.border = '1px solid rgba(29,30,28,.12)';
    srcWrap.wrap.style.background = 'var(--cream-2)';

    const foot = pos(el('div', 'mono', card), 60, 636);
    foot.style.fontSize = '15px';
    foot.style.color = 'var(--muted)';
    foot.textContent = 'N = 16 · all sixteen unanswerable questions';
    R.number = { bg, bgImg, card, strike, fWrap, check, bNum, fLab, fSub, srcWrap };
  }

  function buildEnd() {
    const s = shot('end');
    if (!s) return;
    pos(el('div', 'kicker ember', s), 160, 126).innerHTML = '<span class="dot"></span>Forge RAG Lab · Helios reliability';
    const head = pos(el('div', 'display headline', s), 156, 174);
    head.textContent = 'Send three bad answers.';
    const sub = pos(el('div', 'display sub', s), 160, 346);
    sub.textContent = CUT === 'teaser' ? "I'll name the failed layer." : "I'll tell you which layer failed.";
    const uline = pos(el('div', 'uline', s), 166, 318, 0, 6);
    const cta = pos(el('div', 'cta', s), 160, 486);
    cta.innerHTML = '<span>Send 3 bad answers</span><span style="font-size:42px;line-height:1">→</span>';
    const url = pos(el('div', 'url', s), 162, 646);
    url.textContent = 'github.com/ArpanSM/forge-rag-lab';
    const proof = pos(el('div', 'proof', s), 162, 716);
    proof.textContent = 'Proof of concept · synthetic Helios corpus\nThe method applies to your docs.';
    pos(el('div', 'ghost', s), null, null).textContent = '16/16';
    R.end = { head, sub, uline, cta, url, proof };
  }

  function buildCaptions() {
    // nothing static; seek updates the bar
  }

  function build() {
    buildHook();
    buildFraming();
    buildSplit();
    buildCitations();
    buildCitationsB();
    buildWhy();
    buildNumber();
    buildEnd();
    buildCaptions();
  }

  function updateHook(t, b) {
    const r = R.hook;
    if (!r) return;
    const p = ramp(t, b.start, b.end);
    r.zoom.style.transform = `scale(${(1.02 + 0.02 * p).toFixed(4)})`;
    // a slow programme scroll inside the static crop, not a camera move
    const drift = 20 * p;
    r.img.style.top = `${-r.hookBox.y * r.k - drift * r.k}px`;
    r.outline.style.top = `${(BOX.noCitation.y - r.hookBox.y) * r.k - drift * r.k}px`;
    const q = ramp(t, cue('hookOutline', b.start + 2.4), cue('hookOutline', b.start + 2.4) + 0.42);
    r.outline.style.opacity = String(q);
    r.outline.style.transform = `scale(${0.96 + 0.04 * easeOut(q)})`;
  }

  function updateFraming(t, b) {
    const r = R.framing;
    if (!r) return;
    const p = ramp(t, cue('framingChip', b.start + 0.5), cue('framingChip', b.start + 0.5) + 0.5);
    r.chip.style.opacity = String(p);
    r.chip.style.transform = `translateY(${(1 - easeOut(p)) * 14}px)`;
    r.chip2.style.opacity = String(p * 0.9);
    r.small.style.opacity = String(0.4 + p * 0.6);
    r.uline.style.width = `${260 * easeOut(ramp(t, b.start + 0.55, b.start + 1.25))}px`;
    const zp = ramp(t, b.start, b.end);
    r.zoom.style.transform = `scale(${(1.02 + 0.02 * zp).toFixed(4)})`;
  }

  function updateSplit(t, b) {
    const r = R.split;
    if (!r) return;
    const a = ramp(t, cue('splitRed', b.start + 2.5), cue('splitRed', b.start + 2.5) + 0.4);
    r.ringB.style.opacity = String(a);
    r.ringB.style.transform = `scale(${0.97 + 0.03 * easeOut(a)})`;
    const v = ramp(t, cue('splitGreen', b.start + 4.4), cue('splitGreen', b.start + 4.4) + 0.4);
    r.ringF.style.opacity = String(v);
    r.ringF.style.transform = `scale(${0.97 + 0.03 * easeOut(v)})`;
    const vv = ramp(t, b.start, b.start + 0.45);
    r.vb.style.opacity = String(vv);
    r.vf.style.opacity = String(vv);
  }

  function updateCitations(t, b) {
    const r = R.citations;
    if (!r) return;
    const a = ramp(t, cue('citationRing', b.start + 1.45), cue('citationRing', b.start + 1.45) + 0.42);
    r.ringChip.style.opacity = String(a);
    r.ringChip.style.transform = `scale(${0.97 + 0.03 * easeOut(a)})`;
    const zp = ramp(t, b.start, b.end);
    r.zoom.style.transform = `scale(${(1.02 + 0.02 * zp).toFixed(4)})`;
  }

  function updateCitationsB(t, b) {
    const r = R.citationsB;
    if (!r) return;
    const base = cue('citationPanel', b.start + 0.5);
    r.rows.forEach((row, i) => {
      const p = ramp(t, base + i * 0.16, base + i * 0.16 + 0.34);
      row.style.opacity = String(p);
      row.style.transform = `translateY(${(1 - easeOut(p)) * 16}px)`;
    });
    r.rule.style.height = `${430 * easeOut(ramp(t, base, base + 0.6))}px`;
    const q = ramp(t, base + 0.55, base + 1.05);
    r.bracket.style.height = `${BOX.mark.h * r.k * easeOut(q)}px`;
    r.bracket.style.opacity = String(q);
  }

  function updateWhy(t, b) {
    const r = R.why;
    if (!r) return;
    const start = t - b.start; // 0..beat length
    const off = 1400 + 90 * clamp(start / (b.end - b.start));
    r.img.style.top = `${-off}px`;
    const ringY = (BOX.missedRow.y - off);
    r.ringRow.style.top = ringY + 'px';
    const rp = ramp(t, cue('whyOutline', b.start + 0.6), cue('whyOutline', b.start + 0.6) + 0.4);
    r.ringRow.style.opacity = String(rp);
    const cues = [
      cue('whyStrip', b.start + 0.4),
      cue('whyStep2', b.start + 2.3),
      cue('whyStep3', b.start + 4.3),
    ];
    // Every card is opaque with its full text from the first frame. The
    // resolve is a 10 px settle plus the moss top rule filling at its cue.
    r.steps.forEach(({ card, bar, w }, i) => {
      // Full text, opaque, aligned from the first frame. Only the top rule
      // resolves, so no card body or text ever sits over the report at alpha.
      card.style.opacity = '1';
      card.style.transform = 'none';
      const q = ramp(t, cues[i], cues[i] + 0.35);
      bar.style.width = `${w * easeOut(q)}px`;
    });
  }

  function updateNumber(t, b) {
    const r = R.number;
    if (!r) return;
    const push = ramp(t, b.start, b.end);
    r.card.style.transform = `scale(${(1.02 + 0.02 * push).toFixed(4)})`;
    r.card.style.transformOrigin = '50% 50%';
    r.bgImg.style.top = `${-2800 - 20 * push}px`;
    const s = ramp(t, cue('numberStrike', b.start + 3.3), cue('numberStrike', b.start + 3.3) + 0.36);
    r.strike.style.opacity = String(0.92 * s);
    r.strike.style.width = `${570 * easeOut(s)}px`;
    const q = ramp(t, cue('numberSixteen', b.start + 5.2), cue('numberSixteen', b.start + 5.2) + 0.5);
    r.fWrap.style.opacity = String(q);
    r.fWrap.style.transform = `translateY(${(1 - easeOut(q)) * 22}px)`;
    r.fLab.style.opacity = String(q);
    r.fSub.style.opacity = String(q);
    r.check.style.opacity = String(ramp(t, cue('numberSixteen', b.start + 5.2) + 0.28, cue('numberSixteen', b.start + 5.2) + 0.6));
    r.check.style.transform = `scale(${0.7 + 0.3 * easeOut(ramp(t, cue('numberSixteen', b.start + 5.2), cue('numberSixteen', b.start + 5.2) + 0.5))})`;
  }

  function updateEnd(t, b) {
    const r = R.end;
    if (!r) return;
    const u = ramp(t, cue('endUnderline', b.start + 0.95), cue('endUnderline', b.start + 0.95) + 0.55);
    r.uline.style.width = `${620 * easeOut(u)}px`;
  }

  const UPDATERS = {
    hook: updateHook,
    framing: updateFraming,
    split: updateSplit,
    citations: updateCitations,
    citationsB: updateCitationsB,
    why: updateWhy,
    number: updateNumber,
    end: updateEnd,
  };

  function seek(t) {
    if (!T) return;
    t = clamp(t, 0, T.duration);
    for (const b of T.beats) {
      const visible = t >= b.start && t < b.end;
      const node = shotEls[b.id];
      if (!node) continue;
      node.style.display = visible ? 'block' : 'none';
      if (visible) UPDATERS[b.id]?.(t, b);
    }
    // some cuts split one beat into two visual states (citations → citationsB)
    const cb = T.beats.find((b) => b.id === 'citations');
    if (cb) {
      const bNode = shotEls.citations;
      const b2 = shotEls.citationsB;
      if (bNode && b2) {
        const showB = t >= cue('citationDrawer', cb.start + 4) && t < cb.end;
        const showA = t >= cb.start && t < cue('citationDrawer', cb.start + 4);
        bNode.style.display = showA ? 'block' : 'none';
        b2.style.display = showB ? 'block' : 'none';
        if (showB) updateCitationsB(t, cb);
        if (showA) updateCitations(t, cb);
      }
    }
    // captions
    const caps = T.captions || [];
    let active = null;
    for (const c of caps) {
      if (t >= c.start && t < c.end) { active = c; break; }
    }
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
    const srcs = [
      ASSET('10-baseline.png'),
      ASSET('20-fixed-abstain.png'),
      ASSET('30-fixed-answer.png'),
      ASSET('40-citation-drawer.png'),
      ASSET('60-gallery.png'),
      ASSET('70-health-full.png'),
    ];
    await Promise.all(srcs.map((src) => new Promise((res) => {
      const im = new Image();
      im.onload = () => res();
      im.onerror = () => res();
      im.src = src;
    })));
  }

  async function main() {
    const res = await fetch(`timeline-${CUT}.json`, { cache: 'no-store' });
    T = await res.json();
    if (SQUARE) {
      stage.classList.add('square');
      stage.style.width = '1080px';
      stage.style.height = '1080px';
      T.width = 1080;
      T.height = 1080;
    }
    await preload();
    build();
    window.TIMELINE = T;
    window.DUR = T.duration;
    window.FPS = T.fps || 30;
    window.seek = seek;
    window.__ready = true;
    seek(0);
  }

  main().catch((e) => {
    console.error(e);
    window.__error = String(e);
  });
})();
