import { test } from '@argo-video/cli';
import {
  createHumanCursor,
  renderComposition,
  resetCamera,
} from '@argo-video/cli';
import type { Locator, Page } from '@playwright/test';

const APP = 'https://arpansm.github.io/forge-rag-lab/';
const HEALTH = 'https://arpansm.github.io/forge-rag-lab/health/';

/**
 * Smooth programme scroll. The app sets scroll-behavior: smooth, which would
 * turn each window.scrollTo into its own competing animation, so the helper
 * pins the root to auto and drives one eased scroll on rAF.
 */
async function smoothScrollTo(page: Page, y: number, ms = 700): Promise<void> {
  await page.evaluate(
    async ({ y, ms }) => {
      const root = document.documentElement;
      const previous = root.style.scrollBehavior;
      root.style.scrollBehavior = 'auto';
      const start = window.scrollY;
      const delta = Math.max(0, y) - start;
      const t0 = performance.now();
      await new Promise<void>((resolve) => {
        const step = (now: number) => {
          const p = Math.min(1, (now - t0) / ms);
          const eased = 1 - Math.pow(1 - p, 3);
          window.scrollTo(0, start + delta * eased);
          if (p < 1) requestAnimationFrame(step);
          else resolve();
        };
        requestAnimationFrame(step);
      });
      root.style.scrollBehavior = previous;
    },
    { y, ms },
  );
}

async function scrollElementTo(page: Page, target: Locator, top = 168, ms = 700): Promise<void> {
  const y = await target.evaluate((el) => el.getBoundingClientRect().top + window.scrollY);
  await smoothScrollTo(page, Math.round(y - top), ms);
}

async function driftPage(page: Page, px: number, ms: number): Promise<void> {
  const { y, max } = await page.evaluate(() => ({
    y: window.scrollY,
    max: Math.max(0, document.documentElement.scrollHeight - window.innerHeight),
  }));
  // If the page is already at the bottom, reveal the content above instead:
  // the answer card is still on screen, and the programme move is real.
  const delta = y + px > max ? -Math.min(Math.abs(px), y) : px;
  if (delta !== 0) await smoothScrollTo(page, y + delta, ms);
}

async function highlight(target: Locator, color: string): Promise<void> {
  await target.evaluate((el, color) => {
    const node = el as HTMLElement;
    node.style.boxShadow = `0 0 0 3px ${color}, 0 0 0 14px rgba(29,30,28,0.06)`;
    node.style.borderRadius = node.style.borderRadius || '18px';
  }, color);
}

async function driftDrawer(page: Page, px: number, ms: number): Promise<void> {
  await page.evaluate(
    async ({ px, ms }) => {
      const container = document.querySelector<HTMLElement>('[role="dialog"] .overflow-y-auto');
      if (!container) return;
      const start = container.scrollTop;
      const max = Math.max(0, container.scrollHeight - container.clientHeight);
      const delta = start + px > max ? -Math.min(Math.abs(px), start) : px;
      if (delta === 0) return;
      const t0 = performance.now();
      await new Promise<void>((resolve) => {
        const step = (now: number) => {
          const p = Math.min(1, (now - t0) / ms);
          const eased = 1 - Math.pow(1 - p, 3);
          container.scrollTop = start + delta * eased;
          if (p < 1) requestAnimationFrame(step);
          else resolve();
        };
        requestAnimationFrame(step);
      });
    },
    { px, ms },
  );
}

/** Ease the drawer's own scroll area, without moving the page behind it. */
async function scrollDrawerQuoteIntoView(page: Page, mark: Locator, top = 250, ms = 520): Promise<void> {
  await mark.evaluate(
    async (el, { top, ms }) => {
      const container = el.closest('.overflow-y-auto') as HTMLElement | null;
      if (!container) return;
      const start = container.scrollTop;
      const target =
        el.getBoundingClientRect().top -
        container.getBoundingClientRect().top +
        container.scrollTop -
        top;
      const t0 = performance.now();
      await new Promise<void>((resolve) => {
        const step = (now: number) => {
          const p = Math.min(1, (now - t0) / ms);
          const eased = 1 - Math.pow(1 - p, 3);
          container.scrollTop = start + (target - start) * eased;
          if (p < 1) requestAnimationFrame(step);
          else resolve();
        };
        requestAnimationFrame(step);
      });
    },
    { top, ms },
  );
}

/**
 * A slow, visible pointer travel. The SVG cursor follows real mousemoves; the
 * waits make the path read as one deliberate glide rather than a teleport.
 */
async function glideTo(
  page: Page,
  target: Locator,
  steps = 14,
  stepMs = 80,
): Promise<void> {
  await target.scrollIntoViewIfNeeded();
  const box = await target.boundingBox();
  if (!box) return;
  const start = await page.evaluate(() => {
    const el = document.getElementById('argo-cursor');
    const left = el ? parseFloat(el.style.left) : NaN;
    const top = el ? parseFloat(el.style.top) : NaN;
    return {
      x: Number.isFinite(left) ? left : innerWidth * 0.86,
      y: Number.isFinite(top) ? top : innerHeight * 0.57,
    };
  });
  const dest = {
    x: box.x + box.width * 0.5,
    y: box.y + box.height * 0.55,
  };
  for (let i = 1; i <= steps; i += 1) {
    await page.mouse.move(
      start.x + ((dest.x - start.x) * i) / steps,
      start.y + ((dest.y - start.y) * i) / steps,
    );
    await page.waitForTimeout(stepMs);
  }
}

/**
 * A visible click without Playwright's actionability stability wait. The SVG
 * cursor still travels on real mouse events and the click is a real mouse
 * press at the same point; we only skip waiting on a page that is mid-scroll.
 */
async function clickWithCursor(
  page: Page,
  _cursor: Awaited<ReturnType<typeof createHumanCursor>>,
  target: Locator,
  _durationMs = 450,
): Promise<void> {
  // The page has already been scrolled to the control. Keep the click quick:
  // fixture latency is clamped, so the answer should land early in its scene.
  const box = await target.boundingBox();
  if (!box) throw new Error('clickWithCursor: target has no box');
  const x = box.x + box.width * 0.08;
  const y = box.y + box.height * 0.78;
  await page.mouse.move(x, y, { steps: 4 });
  await page.waitForTimeout(60);
  await page.mouse.click(x, y, { delay: 70 });
  await page.waitForTimeout(160);
}

test('rag-lab-walkthrough', async ({ page, narration }) => {
  test.setTimeout(240_000);

  // Argo's durationFor() is time-aware but can target a placement end beyond
  // the scene when earlier clips backlog. Track the mark ourselves and hold
  // each scene to its own TTS duration, so the cut never drifts.
  let sceneStart = 0;
  const markScene = (scene: string) => {
    narration.mark(scene);
    sceneStart = Date.now();
  };
  const holdScene = async (
    scene: string,
    options: { leadOutMs?: number; extraMs?: number } = {},
  ) => {
    const total = narration.sceneDuration(scene, {
      leadOutMs: options.leadOutMs ?? 500,
    });
    const elapsed = Date.now() - sceneStart;
    const wait = Math.max(0, total - elapsed) + (options.extraMs ?? 0);
    if (wait > 0) await page.waitForTimeout(wait);
  };

  await page.setViewportSize({ width: 1920, height: 1080 });

  // The hosted fixture mock adds 200–900 ms of fake latency. Clamp only that
  // band for recording pace so the skeleton is a flash, not a held beat. The
  // latency numbers rendered on the cards are unchanged.
  await page.addInitScript(() => {
    const original = window.setTimeout.bind(window);
    (window as unknown as { setTimeout: typeof window.setTimeout }).setTimeout = (
      handler: TimerHandler,
      timeout?: number,
      ...args: unknown[]
    ) =>
      original(
        handler,
        typeof timeout === 'number' && timeout >= 200 && timeout <= 1000
          ? 80
          : timeout,
        ...args,
      );
  });

  await page.goto(APP, { waitUntil: 'networkidle' });
  await page.addStyleTag({ content: 'html { scroll-behavior: auto !important; }' });
  await page.getByRole('heading', { name: /Ask the docs/ }).waitFor();

  // Warm the health route's bundle and fonts off-camera so the cut into the
  // report does not spend two seconds on skeletons.
  const warm = await page.context().newPage();
  await warm.goto(HEALTH, { waitUntil: 'networkidle' });
  await warm.getByRole('table').waitFor();
  await warm.close();
  await page.getByRole('button', { name: /How do I rotate an API key in v3/ }).waitFor();

  const cursor = await createHumanCursor(page, {
    seed: 'forge-rag-lab-walkthrough',
    size: 32,
    start: { x: 0.86, y: 0.57 },
  });

  try {
    await narration.startRecording(page);

    // 1 · Hook — landing page, no camera move.
    markScene('hook');
    // Subtle live motion: a 50 px programme drift, then a deliberate pointer
    // travel to the primary action. No small-target zoom.
    await smoothScrollTo(page, 60, 5200);
    await glideTo(page, page.getByRole('button', { name: 'Run query' }), 12, 85);
    await holdScene('hook', { leadOutMs: 500 });

    // 2 · Unanswerable, fixed.
    markScene('fixed-abstain');
    await smoothScrollTo(page, 430, 650);
    const onPrem = page.getByRole('button', {
      name: /exact Helios on-premises install command/,
    });
    await clickWithCursor(page, cursor, onPrem, 520);

    const fixedAbstain = page
      .locator('article.surface')
      .filter({ hasText: 'Answer withheld — evidence is insufficient' })
      .last();
    await fixedAbstain.waitFor({ state: 'visible' });
    await scrollElementTo(page, fixedAbstain, 164, 620);
    await highlight(fixedAbstain, '#975a16');
    await driftPage(page, 120, 4500);
    await holdScene('fixed-abstain', { leadOutMs: 500 });

    // 3 · Unanswerable, baseline. The pipeline control is still in frame.
    markScene('baseline-abstain');
    const baselineButton = page.locator('aside').getByRole('button', { name: /Baseline/ });
    await clickWithCursor(page, cursor, baselineButton, 420);

    const baselineAbstain = page
      .locator('article.surface')
      .filter({ hasText: 'Baseline pipeline' })
      .filter({ hasText: 'helios-install' })
      .last();
    await baselineAbstain.waitFor({ state: 'visible' });
    await scrollElementTo(page, baselineAbstain, 168, 620);
    await highlight(baselineAbstain, '#a33b32');
    await driftPage(page, 120, 4500);
    await holdScene('baseline-abstain', { leadOutMs: 500 });

    // 4 · Answerable, fixed. Switch back, run the API-key sample.
    markScene('fixed-answer');
    await resetCamera(page);
    await smoothScrollTo(page, 390, 620);
    const fixedButton = page.locator('aside').getByRole('button', { name: /^Fixed/ });
    await clickWithCursor(page, cursor, fixedButton, 380);
    // The fixed re-run takes ~880 ms in fixture mode; the sample buttons are
    // disabled while isLoading, so let it settle before the next click.
    await page.waitForTimeout(1100);
    await smoothScrollTo(page, 390, 420);

    const apiSample = page.getByRole('button', { name: /How do I rotate an API key in v3/ });
    await clickWithCursor(page, cursor, apiSample, 460);

    const fixedAnswer = page
      .locator('article.surface')
      .filter({ hasText: 'Fixed pipeline' })
      .filter({ hasText: 'Rotation starts in Settings' })
      .last();
    await fixedAnswer.waitFor({ state: 'visible' });
    await scrollElementTo(page, fixedAnswer, 156, 640);
    const claimSupport = fixedAnswer.locator('section').filter({ hasText: 'Claim support' });
    await highlight(claimSupport, '#116b57');
    await driftPage(page, 150, 4500);
    await holdScene('fixed-answer', { leadOutMs: 500 });

    // 5 · Citation drawer.
    markScene('citation');
    await resetCamera(page);
    const firstCitation = fixedAnswer.locator('button[aria-label^="Open citation"]').first();
    await scrollElementTo(page, firstCitation, 400, 520);
    await clickWithCursor(page, cursor, firstCitation, 420);

    const drawer = page.getByRole('dialog');
    await drawer.waitFor({ state: 'visible' });
    const highlighted = drawer.locator('mark.citation-mark').first();
    await highlighted.waitFor({ state: 'visible' });
    await page.waitForTimeout(250);
    await scrollDrawerQuoteIntoView(page, highlighted, 250, 540);
    await highlight(highlighted, '#d65a31');
    await driftDrawer(page, 130, 5000);
    // The drawer content fits without scrolling, so let the page behind it
    // drift; the drawer and its highlighted quote stay put.
    await driftPage(page, 120, 5000);
    await holdScene('citation', { leadOutMs: 500 });

    // 6 · Answerable, baseline. Close the drawer, switch pipeline.
    markScene('baseline-answer');
    await resetCamera(page);
    await page.keyboard.press('Escape');
    await drawer.waitFor({ state: 'hidden' });

    await smoothScrollTo(page, 390, 620);
    await clickWithCursor(page, cursor, baselineButton, 400);

    const baselineAnswer = page
      .locator('article.surface')
      .filter({ hasText: 'Baseline pipeline' })
      .filter({ hasText: 'In v2, open Settings' })
      .last();
    await baselineAnswer.waitFor({ state: 'visible' });
    await scrollElementTo(page, baselineAnswer, 156, 640);
    await highlight(baselineAnswer, '#a33b32');
    await driftPage(page, 120, 4500);
    await holdScene('baseline-answer', { leadOutMs: 500 });

    // 7 · Health report. Navigate during the silent tail so the cut is clean.
    await resetCamera(page);
    await page.goto(HEALTH, { waitUntil: 'domcontentloaded' });
    await page.getByRole('table').waitFor();
    await page.getByText('Where the fixed pipeline earns its keep').waitFor();
    await page.addStyleTag({ content: 'html { scroll-behavior: auto !important; }' });
    await page.waitForTimeout(150);

    markScene('health');
    await page.waitForTimeout(900);
    await smoothScrollTo(page, 790, 850);
    await smoothScrollTo(page, 940, 3800);
    await page.waitForTimeout(300);

    const failure = page
      .locator('article.surface')
      .filter({ hasText: 'What is the exact Helios on-premises install command?' })
      .first();
    await failure.scrollIntoViewIfNeeded();
    await scrollElementTo(page, failure, 226, 780);
    const baselineBlock = failure
      .locator('div.rounded-xl')
      .filter({ hasText: 'Run sudo helios-install' })
      .first();
    await baselineBlock.evaluate((el) => {
      const node = el as HTMLElement;
      node.style.outline = '2px solid #a33b32';
      node.style.outlineOffset = '4px';
      node.style.borderRadius = '14px';
      node.style.boxShadow = '0 0 0 12px rgba(163,59,50,0.10)';
    });
    await driftPage(page, 160, 6500);
    await holdScene('health', { leadOutMs: 500 });

    // 8 · End card composition. Drop the pointer first so it cannot sit on the card.
    await resetCamera(page);
    await cursor.dispose();
    await renderComposition(page, narration, 'compositions/close.html', { scene: 'close' });
  } finally {
    await cursor.dispose();
    await resetCamera(page);
  }
});
