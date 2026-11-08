// Clean single-state captures from the hosted fixture app, 1920x1080 @2x.
// Each state gets a fresh page so the chat history never stacks.
import { chromium } from 'playwright';
import fs from 'node:fs/promises';
import path from 'node:path';

const APP = 'https://arpansm.github.io/forge-rag-lab/';
const HEALTH = 'https://arpansm.github.io/forge-rag-lab/health/';
const OUT = path.resolve('proof-film/captures');

const log = (...a) => console.log('[capture]', ...a);

async function smoothScrollTo(page, y, ms = 500) {
  await page.evaluate(
    async ({ y, ms }) => {
      const root = document.documentElement;
      root.style.scrollBehavior = 'auto';
      const start = window.scrollY;
      const delta = y - start;
      const t0 = performance.now();
      await new Promise((resolve) => {
        const step = (now) => {
          const p = Math.min(1, (now - t0) / ms);
          const eased = 1 - Math.pow(1 - p, 3);
          window.scrollTo(0, start + delta * eased);
          if (p < 1) requestAnimationFrame(step);
          else resolve();
        };
        requestAnimationFrame(step);
      });
    },
    { y, ms },
  );
}

async function scrollToEl(page, locator, top = 150, ms = 500) {
  const y = await locator.evaluate((el) => el.getBoundingClientRect().top + window.scrollY);
  await smoothScrollTo(page, Math.max(0, Math.round(y - top)), ms);
}

const rel = (box, scrollY) => ({
  x: +box.x.toFixed(1),
  y: +(box.y + scrollY).toFixed(1),
  w: +box.width.toFixed(1),
  h: +box.height.toFixed(1),
});

async function newPage(browser) {
  const page = await browser.newPage({
    viewport: { width: 1920, height: 1080 },
    deviceScaleFactor: 2,
    colorScheme: 'light',
  });
  await page.addInitScript(() => {
    const original = window.setTimeout.bind(window);
    window.setTimeout = (handler, timeout, ...args) =>
      original(handler, typeof timeout === 'number' && timeout >= 200 && timeout <= 1000 ? 80 : timeout, ...args);
  });
  return page;
}

async function main() {
  await fs.mkdir(OUT, { recursive: true });
  const browser = await chromium.launch({ channel: 'chrome' });
  const meta = {};

  // ---- baseline unanswerable, single card ----
  {
    const page = await newPage(browser);
    await page.goto(APP, { waitUntil: 'networkidle' });
    await page.addStyleTag({ content: 'html{scroll-behavior:auto!important}' });
    await page.getByRole('heading', { name: /Ask the docs/ }).waitFor();
    await page.locator('aside').getByRole('button', { name: /^Baseline/ }).click();
    await page.waitForTimeout(150);
    await page.getByRole('button', { name: /exact Helios on-premises install command/ }).click();
    const card = page
      .locator('article.surface')
      .filter({ hasText: 'Baseline pipeline' })
      .filter({ hasText: 'helios-install' })
      .last();
    await card.waitFor({ state: 'visible' });
    await page.waitForTimeout(400);
    await scrollToEl(page, card, 130, 350);
    await page.waitForTimeout(150);
    const sy = await page.evaluate(() => scrollY);
    await page.screenshot({ path: path.join(OUT, '10-baseline.png'), animations: 'disabled', caret: 'hide' });
    meta.baseline = {
      scrollY: sy,
      card: rel(await card.boundingBox(), sy),
      noCitation: rel(await card.getByText('No citation', { exact: true }).first().boundingBox(), sy),
      invented: rel(await card.getByText(/Run sudo helios-install/).first().boundingBox(), sy),
      text: await card.innerText(),
    };
    await page.close();
  }

  // ---- fixed abstain, single card ----
  {
    const page = await newPage(browser);
    await page.goto(APP, { waitUntil: 'networkidle' });
    await page.addStyleTag({ content: 'html{scroll-behavior:auto!important}' });
    await page.getByRole('heading', { name: /Ask the docs/ }).waitFor();
    await page.getByRole('button', { name: /exact Helios on-premises install command/ }).click();
    const card = page
      .locator('article.surface')
      .filter({ hasText: 'Fixed pipeline' })
      .filter({ hasText: 'Answer withheld' })
      .last();
    await card.waitFor({ state: 'visible' });
    await page.waitForTimeout(400);
    await scrollToEl(page, card, 130, 350);
    await page.waitForTimeout(150);
    const sy = await page.evaluate(() => scrollY);
    await page.screenshot({ path: path.join(OUT, '20-fixed-abstain.png'), animations: 'disabled', caret: 'hide' });
    meta.fixedAbstain = {
      scrollY: sy,
      card: rel(await card.boundingBox(), sy),
      withheld: rel(await card.getByText(/Answer withheld/).first().boundingBox(), sy),
      text: await card.innerText(),
    };
    await page.close();
  }

  // ---- fixed API answer + drawer ----
  {
    const page = await newPage(browser);
    await page.goto(APP, { waitUntil: 'networkidle' });
    await page.addStyleTag({ content: 'html{scroll-behavior:auto!important}' });
    await page.getByRole('heading', { name: /Ask the docs/ }).waitFor();
    await page.getByRole('button', { name: /How do I rotate an API key in v3/ }).click();
    const card = page
      .locator('article.surface')
      .filter({ hasText: 'Fixed pipeline' })
      .filter({ hasText: /Rotation starts in Settings|API keys/ })
      .last();
    await card.waitFor({ state: 'visible' });
    await page.waitForTimeout(450);
    await scrollToEl(page, card, 96, 350);
    await page.waitForTimeout(150);
    let sy = await page.evaluate(() => scrollY);
    await page.screenshot({ path: path.join(OUT, '30-fixed-answer.png'), animations: 'disabled', caret: 'hide' });
    const chips = card.locator('button[aria-label^="Open citation"]');
    meta.fixedAnswer = {
      scrollY: sy,
      card: rel(await card.boundingBox(), sy),
      claimSupport: rel(
        await card.locator('section').filter({ hasText: 'Claim support' }).first().boundingBox(),
        sy,
      ),
      chips: [],
      text: await card.innerText(),
    };
    for (let i = 0; i < (await chips.count()); i++) {
      meta.fixedAnswer.chips.push(rel(await chips.nth(i).boundingBox(), sy));
    }

    await chips.first().click();
    const drawer = page.getByRole('dialog');
    await drawer.waitFor({ state: 'visible' });
    const mark = drawer.locator('mark.citation-mark').first();
    await mark.waitFor({ state: 'visible' });
    await page.waitForTimeout(400);
    sy = await page.evaluate(() => scrollY);
    await page.screenshot({ path: path.join(OUT, '40-citation-drawer.png'), animations: 'disabled', caret: 'hide' });
    meta.drawer = {
      scrollY: sy,
      box: rel(await drawer.boundingBox(), sy),
      mark: rel(await mark.boundingBox(), sy),
      text: await drawer.innerText(),
    };
    await page.close();
  }

  // ---- health table + abstention rows + gallery ----
  {
    const page = await newPage(browser);
    await page.goto(HEALTH, { waitUntil: 'networkidle' });
    await page.getByRole('table').waitFor();
    await page.waitForTimeout(900);
    await page.addStyleTag({ content: 'html{scroll-behavior:auto!important}' });

    const table = page.getByRole('table');
    const abstention = page.getByText(/^Abstention accuracy/).first();
    const missed = page.getByText(/^Missed abstention rate/).first();
    await abstention.scrollIntoViewIfNeeded();
    await page.waitForTimeout(200);
    await scrollToEl(page, table, 150, 300);
    await page.waitForTimeout(200);
    let sy = await page.evaluate(() => scrollY);
    await page.screenshot({ path: path.join(OUT, '50-health-table.png'), animations: 'disabled', caret: 'hide' });
    meta.healthTable = {
      scrollY: sy,
      table: rel(await table.boundingBox(), sy),
      abstention: rel(await abstention.boundingBox(), sy),
      missed: rel(await missed.boundingBox(), sy),
      pageHeight: await page.evaluate(() => document.documentElement.scrollHeight),
    };

    await missed.scrollIntoViewIfNeeded();
    await page.waitForTimeout(200);
    sy = await page.evaluate(() => scrollY);
    await page.screenshot({ path: path.join(OUT, '51-health-abstention.png'), animations: 'disabled', caret: 'hide' });
    meta.healthAbstention = {
      scrollY: sy,
      missed: rel(await missed.boundingBox(), sy),
    };

    // failure gallery top
    const gallery = page.getByText('Missed detail', { exact: true }).first();
    await gallery.scrollIntoViewIfNeeded();
    await page.waitForTimeout(250);
    await smoothScrollTo(page, Math.max(0, (await page.evaluate(() => scrollY)) - 120), 300);
    await page.waitForTimeout(200);
    sy = await page.evaluate(() => scrollY);
    await page.screenshot({ path: path.join(OUT, '60-gallery.png'), animations: 'disabled', caret: 'hide' });
    meta.gallery = { scrollY: sy };

    // tall health page for the programme-scroll shot
    await page.goto(HEALTH, { waitUntil: 'networkidle' });
    await page.getByRole('table').waitFor();
    await page.waitForTimeout(900);
    await page.screenshot({ path: path.join(OUT, '70-health-full.png'), fullPage: true });
    meta.healthFull = {
      pageHeight: await page.evaluate(() => document.documentElement.scrollHeight),
    };
    await page.close();
  }

  await fs.writeFile(path.join(OUT, 'meta.json'), JSON.stringify(meta, null, 2));
  log('wrote meta.json');
  await browser.close();
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
