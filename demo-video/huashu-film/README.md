# Forge RAG Lab — launch film (Huashu Motion)

A 30-second, 1920 × 1080, 60 fps launch film about evidence-first retrieval.
Music and effects only; no narration. Built as one editable Huashu Motion
composition (`index.html`, HTML + GSAP, 120 BPM, 15 bars).

**Output:** `out/forge-rag-lab-launch.mp4`
**Poster:** `out/forge-rag-lab-launch-poster.png`
**QA:** `../qa/huashu-report.md`, `../qa/huashu-qa.txt`, `../qa/huashu-check.txt`
**Stills:** `../qa/huashu-stills/` at 0, 1, 2, 5, 8, 10, 10.5, 11, 12, 16,
20, 24, 28, 30 s

## The film

- **0–1 s** — dark hook poster: the baseline answer + “A confident answer / is
  not evidence.”
- **1–2 s** — close-up of the invented command: “A command that never existed.”
- **2–4 s** — claim support detail; the 0-citations number stamps in at 3.0 s.
- **4–8 s** — fixed pipeline: “Answer withheld — evidence is insufficient.”
- **8–12 s** — the answerable v3 question, then one beat per claim: three
  claims, three citations.
- **12–16 s** — open the citation; the exact source block is highlighted.
- **16–20 s** — the 80-question health report: recall, citation coverage,
  version disambiguation.
- **20–22 s** — the turn: “Confidence is not evidence.”
- **22–26 s** — the measured delta on the film’s one dark ink panel.
- **26–30 s** — end card: “Ask the docs. Check the evidence.”, stats, repo,
  and the fixture-mode caveat.

The opening is a real move: a 1.08 full-frame push on the dark poster, then a
hard cut at 1 s to the command close-up and another at 2 s to the claim detail.
The 10.5 s return from the claim burst to the full answer is a clean handoff:
the claim scene is hidden at 10.35 s and the answer appears at 10.5 s, so no
claim strip ever shares the frame with the citation chips. Reading holds carry
slow parallax/pushes rather than sitting still.

The film keeps the Huashu signature in the free bottom-right corner for the
last 1.2 s. It can be removed with `data-om-signature="off"` on the root.

## Material

`materials/` holds real screenshots of `https://arpansm.github.io/forge-rag-lab/`
captured at 1920 × 1080 with Playwright/Chrome at 2× on 2026-11-08, plus crops
of the answer cards, claim rows, citation drawer and health table.
`materials.md` lists every file and its source.

Palette from the app’s own tokens: paper `#f5f1e8`, ink `#1d1e1c`, ember
`#d65a31`, moss `#116b57`, danger `#a33b32`, amber `#975a16`, line `#e5dfd2`.
Type: Noto Serif / Noto Sans / Noto Sans Mono (shipped in `assets/fonts/`,
SIL OFL).

## Reproduce

From `demo-video/`:

```bash
# optional: recapture the real screenshots from the hosted app
node capture-materials.mjs

PATH=/tmp/opencode/bin:$PATH npx om check huashu-film
PATH=/tmp/opencode/bin:$PATH npx om still huashu-film --at 0,1,2,3,5,8,10,12,16,20,24,28,30
PATH=/tmp/opencode/bin:$PATH npx om sound huashu-film
PATH=/tmp/opencode/bin:$PATH npx om render huashu-film --fps 60 --workers 8 --blur 4
PATH=/tmp/opencode/bin:$PATH npx om qa huashu-film
```

The render writes `out/huashu-film-vN.mp4`; the delivered copy is
`out/forge-rag-lab-launch.mp4`. The poster is a 27.8 s frame.

## Sound

Composer mode: an `om-score` in ABC at 120 BPM, D minor, with marks on the
scene labels. Pulse (synpluck), piano motif, strings, bass and a cinematic kit.
The stop at 20–22 s is a held breath with a riser; the delta at 22 s is the
drop with impact/subdrop. `om sound` reports −14.2 LUFS, peak −1.5 dBFS; the delivered AAC was
loudness-trimmed to **−14.9 LUFS, −1.3 dBFS**.

## Caveats

Fixture-mode demo · synthetic Helios corpus · development numbers, not a
production benchmark. The hosted app is static; the film shows its real
fixture-mode screens.
