# Forge RAG Lab — demo videos

Two deliverables for the hosted fixture-mode app
`https://arpansm.github.io/forge-rag-lab/`:

1. **Narrated walkthrough** — 74.93 s, 1920 × 1080, 30 fps, real LFM3 voiceover.
2. **Huashu Motion launch film** — 30 s, 1920 × 1080, 60 fps, music and
   effects only.

Nothing here is uploaded, committed or pushed.

## Files

| File | What |
|---|---|
| `videos/rag-lab-walkthrough.mp4` | Narrated walkthrough, H.264 + AAC |
| `videos/rag-lab-walkthrough.srt` / `.vtt` | Normalized subtitles |
| `videos/rag-lab-walkthrough-poster.png` | 1920 × 1080 end card |
| `huashu-film/out/forge-rag-lab-launch.mp4` | 30 s launch film, 60 fps |
| `huashu-film/out/forge-rag-lab-launch-poster.png` | 1920 × 1080 end card |
| `qa/` | Walkthrough Video Director report + contact sheets; Huashu check/QA + contact sheet |

## Reproduce the walkthrough

From `demo-video/`:

```bash
PATH=/tmp/opencode/bin:$PATH npx argo pipeline rag-lab-walkthrough
```

This runs LFM3 TTS → Playwright recording of the hosted app → alignment → MP4.
The LFM3 service must be up at `127.0.0.1:8082` (`curl /health`). The demo
records the real fixture-mode UI; it does not run the Next app.

After the pipeline, the delivery audio was normalized from −16.1 to
−14.9 LUFS with:

```bash
ffmpeg -y -i videos/rag-lab-walkthrough.mp4 \
  -c:v copy -c:a aac -b:a 192k -ar 48000 \
  -af loudnorm=I=-14:TP=-1.5:LRA=11 \
  videos/rag-lab-walkthrough.norm.mp4
mv videos/rag-lab-walkthrough.norm.mp4 videos/rag-lab-walkthrough.mp4
node scripts/normalize-subtitles.mjs videos/rag-lab-walkthrough.srt videos/rag-lab-walkthrough.vtt
ffmpeg -y -ss 76.2 -i videos/rag-lab-walkthrough.mp4 -frames:v 1 videos/rag-lab-walkthrough-poster.png
```

## Reproduce the launch film

```bash
cd demo-video
PATH=/tmp/opencode/bin:$PATH npx om check huashu-film
PATH=/tmp/opencode/bin:$PATH npx om sound huashu-film
PATH=/tmp/opencode/bin:$PATH npx om render huashu-film --fps 60 --workers 8 --blur 4
PATH=/tmp/opencode/bin:$PATH npx om qa huashu-film
```

The film is `huashu-film/index.html`; screenshots and crops are in
`huashu-film/materials/` and are listed in `huashu-film/materials.md`. The
delivered copy is `out/forge-rag-lab-launch.mp4`; drafts are removed. The
10.35 → 10.5 s handoff clears the claim strip before the answer/citation chips
appear.

## Exact narration

1. A confident answer is not the same as evidence. This assistant shows you the page.
2. Ask for an install command the docs do not contain. The fixed pipeline withholds the answer, instead of guessing.
3. The baseline invents a retired command, and cites nothing. That is the failure this demo makes visible.
4. Now, a question the docs can answer. In the fixed pipeline, every claim carries a citation: a version, a page, a block.
5. Open a citation, and the exact block is highlighted. You can check the answer, instead of trusting it.
6. The baseline answers from version two, silently. No version filter. No reranker. No abstention.
7. Eighty questions. Recall: zero point eight six five, to zero point nine four three. Citation coverage: zero point seven nine seven, to one. Version disambiguation: zero to one.
8. Every answer can be checked. Every missing answer can be refused. The code is in the repository.

Voice: LFM3 Audio 2B, male, speed 0.96–1.00 per scene (no 1.06). The measured
median f0 is ≈100 Hz.

## Direction notes

- The Agent MCP walkthrough’s small-target `zoomTo` moves are gone. This demo
  uses hard cuts between views, worked programme scrolls inside a view, and
  `spotlight` / `focusRing` on the abstention, the “No citation” chip, the
  claim support block and the citation quote. No camera move is used.
- The opening is now live: a 60 px programme drift over 5.2 s plus a deliberate
  pointer travel to the primary action. The cursor is a single seeded SVG
  pointer; it travels to each control and clicks once, and is disposed before
  the end card.
- Every long answer hold gets a slow programme scroll (100–160 px over
  4.0–6.5 s, roughly 20–30 px/s). At the bottom of the page the move reverses
  to reveal the question; the highlight is a scroll-safe CSS outline, not a
  fixed spotlight. The citation drawer gets a page drift behind it.
- The hosted fixture mock’s 200–1000 ms fake latency is clamped to 80 ms during
  recording (the latency numbers on the cards are unchanged), so the answer is
  on screen for the voice-over instead of a held loading skeleton.
- The end-card composition now shows its headline on the first frame after the
  cut and carries a slow 1.04 centre push through the hold.
- The health page still has a short real loading state while the static export
  hydrates; it is the real app, not a mocked state.

## Caveats

- Hosted app is in fixture mode; the live API is not deployed.
- Synthetic Helios corpus; development numbers, not a production benchmark.
- No LLM judge was run; answer correctness/faithfulness are not measured.
- The walkthrough and film are for review; no upload, commit or push was done.
