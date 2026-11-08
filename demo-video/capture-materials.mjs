import { chromium } from 'playwright';
import { mkdirSync } from 'node:fs';
const OUT = 'huashu-film/materials';
mkdirSync(OUT, { recursive: true });
const b = await chromium.launch({ channel: 'chrome', headless: true });
const p = await b.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 2, colorScheme: 'light' });
const shoot = async (name) => {
  await p.evaluate(() => document.fonts.ready);
  await p.waitForTimeout(300);
  await p.screenshot({ path: `${OUT}/${name}.png` });
  console.log(name);
};
const scrollTo = async (y) => { await p.evaluate((y) => window.scrollTo({ top: y, behavior: 'instant' }), y); };
const scrollEl = async (locator, top = 140) => {
  await locator.scrollIntoViewIfNeeded();
  const y = await locator.evaluate((el) => el.getBoundingClientRect().top + window.scrollY);
  await scrollTo(Math.max(0, Math.round(y - top)));
};

await p.goto('https://arpansm.github.io/forge-rag-lab/', { waitUntil: 'networkidle' });
await p.getByRole('button', { name: /How do I rotate an API key in v3/ }).waitFor();
await shoot('01-landing');

// Fixed abstention.
await p.getByRole('button', { name: /exact Helios on-premises install command/ }).click();
let card = p.locator('article.surface').filter({ hasText: 'Answer withheld — evidence is insufficient' }).last();
await card.waitFor();
await scrollEl(card, 100);
await shoot('02-fixed-abstain');

// Baseline invented command.
await p.locator('aside').getByRole('button', { name: /Baseline/ }).click();
let base = p.locator('article.surface').filter({ hasText: 'Run sudo helios-install' }).last();
await base.waitFor();
await scrollEl(base, 90);
await shoot('03-baseline-invented');

// Fixed answer with citations.
await p.locator('aside').getByRole('button', { name: /^Fixed/ }).click();
await p.waitForTimeout(1100);
await p.getByRole('button', { name: /How do I rotate an API key in v3/ }).click();
let ans = p.locator('article.surface').filter({ hasText: 'Rotation starts in Settings' }).last();
await ans.waitFor();
await scrollEl(ans, 90);
await shoot('04-fixed-citations');

// Citation drawer.
await ans.locator('button[aria-label^="Open citation"]').first().click();
const drawer = p.getByRole('dialog');
await drawer.waitFor();
await drawer.locator('mark.citation-mark').first().waitFor();
await p.waitForTimeout(500);
await p.screenshot({ path: `${OUT}/05-citation-drawer.png` });
console.log('05-citation-drawer');
await p.keyboard.press('Escape');
await drawer.waitFor({ state: 'hidden' });

// Baseline v2 stale answer.
await scrollTo(390);
await p.locator('aside').getByRole('button', { name: /Baseline/ }).click();
let stale = p.locator('article.surface').filter({ hasText: 'In v2, open Settings' }).last();
await stale.waitFor();
await scrollEl(stale, 90);
await shoot('06-baseline-stale');

// Health report.
await p.goto('https://arpansm.github.io/forge-rag-lab/health/', { waitUntil: 'networkidle' });
await p.getByRole('table').waitFor();
await p.waitForTimeout(400);
await shoot('07-health-top');
await scrollTo(790);
await shoot('08-health-table');
const failure = p.locator('article.surface').filter({ hasText: 'What is the exact Helios on-premises install command?' }).first();
await scrollEl(failure, 150);
await shoot('09-health-failure');

await b.close();
