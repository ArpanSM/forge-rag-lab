# Huashu Motion launch film — QA report

**File:** `huashu-film/out/forge-rag-lab-launch.mp4`
**Source:** `huashu-film/index.html` (one composition, GSAP, 15 bars at 120 BPM)
**Poster:** `huashu-film/out/forge-rag-lab-launch-poster.png` (1920 × 1080)
**Stills:** `qa/huashu-stills/` at 0, 1, 2, 5, 8, 10, 10.5, 11, 12, 16, 20, 24, 28, 30 s
**Length:** 30.00 s, 60 fps, 1920 × 1080, H.264 + AAC stereo 48 kHz
**Sound:** programmatic score + effects, no narration
**Signature:** “Made with huashu-motion” in the free bottom-right corner for the
last 1.2 s; switch off with `data-om-signature="off"` if commissioned.

## Story beats

| Time | Beat |
|---:|---|
| 0.0–1.0 | Dark hook poster: the baseline answer + “A confident answer / is not evidence.” |
| 1.0–2.0 | Close-up of the invented command: “A command that never existed.” |
| 2.0–4.0 | Claim support detail; the 0-citations number stamps in at 3.0 |
| 4.0–8.0 | Fixed pipeline: “Answer withheld — evidence is insufficient” |
| 8.0–12.0 | The answerable v3 answer; one beat per claim (3 claims, 3 citations) |
| 12.0–16.0 | Citation drawer; the exact quoted block is highlighted |
| 16.0–20.0 | 80-question health report; recall / citation coverage / version disambiguation |
| 20.0–22.0 | The turn: “Confidence is not evidence.” |
| 22.0–26.0 | Drop: the measured delta on a dark ink panel |
| 26.0–30.0 | End card: “Ask the docs. Check the evidence.”, stats, repo, caveat |

## Material

Real hosted-app screenshots at 1920 × 1080 / 2× (Playwright, Chrome), captured
2026-11-08; no redrawn UI. Sources and crops are listed in
`huashu-film/materials.md`. Palette and type come from the app’s own tokens:
paper, ink, ember, moss, danger, amber; Noto Serif / Sans / Mono.

## Checks

- `npx om check huashu-film` → **0 errors, 0 warnings** (`qa/huashu-check.txt`).
- `npx om qa huashu-film` (`qa/huashu-qa.txt`):
  - **PASS** no single-frame pops.
  - **6 hard cuts** detected at **0.85 / 0.87 / 22 / 22.02 / 25.85 / 25.87 s**
    (the hook cut and the dark drop/return). The straight ffmpeg scene pass
    finds the full edit at **0.85, 3.85, 4, 7.85, 8, 8.85, 10.5, 11.85, 12,
    15.85, 16, 19.85, 22, 25.85 s** (`qa/huashu-cuts.txt`).
  - **No flat-opening failure**: the strongest second in the first 5 s is
    **2.8**.
  - Remaining `still for ≥1 s` warnings are now **1.3–2.1 s reading holds**;
    the former 3.8–4 s blocks are split by the slow parallax/pushes (citation
    card +40 px, health scene +40 px, delta stats −60 px, end card 4 % push)
    and a single reframe at 14 / 18 / 24 / 28 s. The detector still lists them
    as holds because they are deliberately slow, not busy motion.
- Loudness: **−14.9 LUFS**, true peak **−1.3 dBFS** after delivery loudnorm.
- Score fit: 120 BPM, Dm; marks at 0 / 4 / 8 / 12 / 16 / 20 / 22 / 26 s;
  tempo bend ≤ 0.4%; energy −19.3 hook → −15.1 drop, with a −20.9 stop.
- Contact sheet: `qa/huashu-contact-sheet.jpg`.

## Fixes in this pass

- **10 s collision cleared.** The claim scene is hidden at **10.35 s**, the
  full v3 answer appears at **10.5 s**. No claim strip is on screen when the
  citation chips arrive. The 0.15 s gap is a clean cream beat; the MP4's motion
  blur softens the first frames of the answer, but no claim text is present.
  Stills at `10.00s.png`, `10.50s.png` and `11.00s.png` confirm the handoff
  (claim 3 → clean answer); the 10.5/11.0 composition stills are fully sharp.
- **Slow reads.** Added continuous parallax/push on the citation, health,
  delta and end-card holds; the fixed card keeps its 5 s reframe.
- **Drafts removed.** `huashu-film/out/` contains only the final MP4 and
  poster.

## Caveats

- Fixture-mode demo · synthetic Helios corpus · development numbers, not a
  production benchmark.
- The film shows the app’s real screens; the title/end cards are authored type,
  not product screens.
- The 30 s master is a fixed composition. If the end-hold variable changes,
  re-run `om sound` and `om render`.
