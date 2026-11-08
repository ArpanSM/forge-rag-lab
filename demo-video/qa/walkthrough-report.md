# Narrated walkthrough — QA report

**File:** `videos/rag-lab-walkthrough.mp4`
**Source:** `demos/rag-lab-walkthrough.demo.ts` + `demos/rag-lab-walkthrough.scenes.json`
**Recorded:** hosted fixture-mode app, 2026-11-08
**Direction:** hard cuts between views, smooth programme scroll within a view,
spotlight/focusRing for citations and warnings. No `zoomTo` calls, no
small-target camera moves.

## ffprobe

- 1920 × 1080, 30 fps, H.264 (`yuv420p`, BT.709)
- AAC 48 kHz, mono, **74.93 s**, 13.19 MB
- Integrated loudness **−14.9 LUFS**, true peak **−1.4 dBTP**
- First frame: landing page, not black; poster at
  `videos/rag-lab-walkthrough-poster.png` (1920 × 1080, readable end card)

## Voice

- LFM3 Audio 2B, `voice: "male"` (measured median f0 ≈ 100 Hz)
- Speed per scene: 1.00 hook, 0.97 fixed-abstain, 0.96 baseline-abstain,
  0.98 fixed-answer, 0.97 citation, 0.97 baseline-answer, 0.96 health,
  0.98 close. Deliberate read; no speed increase.

## Scene map

| Scene | Start | What is on screen |
|---|---:|---|
| hook | 0.0 | Landing page: “Ask the docs. Check the evidence.”; 60 px programme drift + cursor travel |
| fixed-abstain | 7.2 | On-prem sample, Fixed: “Answer withheld — evidence is insufficient.” |
| baseline-abstain | 15.9 | Baseline: invented `sudo helios-install …`, “No citation.” |
| fixed-answer | 24.4 | API-key sample, Fixed: v3 answer, 3 claims / 3 citations |
| citation | 34.4 | Citation drawer, API keys v3 p.2 b4, exact quote highlighted |
| baseline-answer | 42.6 | Baseline: v2 stale answer |
| health | 51.8 | Health report: 80-question table and stats |
| close | 66.7 | End card: “Ask the docs. Check the evidence.” + measured delta |

Final duration 74.93 s; composition end card is 8.2 s.

## Fixes in this pass

- **Hook motion:** the landing page drifts **60 px over 5.2 s** while the
  pointer glides to the primary action. This replaces the former 6.6 s static
  opening. No `zoomTo`/small-target pan was added.
- **Answer holds:** each long answer hold now gets a slow programme scroll
  (100–160 px over 4.0–6.5 s) at roughly 20–30 px/s. When the page is already
  at the bottom, the move reverses to reveal the question above instead of
  sitting still. The citation drawer gets a page drift behind it.
- **Highlights:** the fixed/baseline answers, claim support, citation quote and
  health failure use scroll-safe CSS outlines/glows instead of fixed spotlight
  overlays, so the highlight travels with the content during the scroll.
- **End card:** the composition gets a slow 1.04 centre push over 6.4 s, so the
  closing hold moves instead of freezing.
- **14 s skeleton:** the hosted fixture mock’s 200–1000 ms fake latency is
  clamped to 80 ms for recording pace (the latency numbers rendered on the
  cards are unchanged), and the cursor click is now a short travel rather than
  a multi-second glide. The fixed answer is on screen by ~10 s and holds
  through the voice-over; the former “Running the fixed pipeline…” skeleton at
  14 s is gone.
- **End-card cut:** the end-card composition’s headline is now present on the
  first frame of the composition instead of fading in after the cut. The
  near-uniform 68.93–69.27 s frames are gone.
- **Voice:** kept male at 0.96–1.00; no re-record at a higher speed.

## QA (`qa/report.md`, `qa/report.json`, contact sheets)

- **PASS** frame 0 is a finished composition (mean 222.8, contrast 11.8).
- **PASS** no single-frame flashes.
- **PASS** loudness −14.9 LUFS, true peak −1.4 dBTP.
- **PASS** silence before the loudest moment.
- **PASS** no flat-frame warning at the end-card cut.
- **WARN** pops: intended answer-card, spotlight and drawer transitions.
- **WARN** frozen stretches: the longest is now **3.07 s** (4.17–7.23 s,
  the hook’s final poster read); the former 6.4 / 5.97 / 5.57 / 5.83 / 6.6 s
  holds are gone. Remaining 2–3 s stretches are voice-over reading holds after
  the slow move completes. The end card no longer has a 6.6 s final hold.
- Contact sheets: `qa/beats_sheet.jpg`, `qa/phone_sheet.jpg`, `qa/hook_sheet.jpg`.

## Caveats

- The health page still shows a short real loading state as the static export
  hydrates; the mock’s artificial delay is clamped, but the page itself is the
  hosted app, not a mock-up.
- The app is the fixture-mode demo; it is not the live API. All numbers are the
  project’s development numbers on a synthetic Helios corpus.
- Subtitles are normalized to whole milliseconds with
  `scripts/normalize-subtitles.mjs`.
