# Forge RAG Lab — client proof film

A 46.55 s proof film and a 22.10 s teaser cut, made for a muted, phone-first
viewer. One failure, one fix, one number, one why-me, one CTA. Real hosted
fixture UI; authored cards in the app's cream / ink / ember / moss palette.

Nothing here is uploaded, committed or pushed.

## Deliverables (`out/`)

| File | Facts |
|---|---|
| `rag-proof-45s.mp4` | 1920 × 1080, 30 fps, H.264 High, 46.55 s, 6.98 MB, AAC 192 kbps, −14.2 LUFS, −1.5 dBTP |
| `rag-proof-45s-720p.mp4` | 1280 × 720, 30 fps, H.264 High, 46.55 s, 3.41 MB, audio copy |
| `rag-proof-45s.srt` / `.vtt` | 15 burned-in captions, matching the final mix |
| `rag-proof-45s-poster.png` | 1920 × 1080, the 16/16 reveal at 39.5 s |
| `rag-proof-teaser-22s.mp4` | 1920 × 1080, 30 fps, 22.10 s, 3.33 MB, −14.0 LUFS, −1.5 dBTP |
| `rag-proof-teaser-22s.srt` / `.vtt` | 8 captions |
| `rag-proof-teaser-22s-poster.png` | 1920 × 1080, the 16/16 reveal |
| `rag-proof-teaser-22s-1x1.mp4` | 1080 × 1080, 30 fps, 22.10 s, 2.02 MB, −14.0 LUFS, −1.5 dBTP |
| `rag-proof-teaser-22s-1x1-poster.png` | 1080 × 1080 |

The 1:1 teaser is a dedicated re-layout (the split screen is stacked, not
cropped), so it survives the square frame.

## Exact narration — 91 spoken words

Voice: LFM3 Audio 2B, **male**, 0.96–1.00. Measured median f0 on the opening
line: **109.6 Hz**. No female voice. No speed above 1.00.

| # | Line | Speed | Speech starts | Speech ends |
|---|---|---|---:|---:|
| 1 | Has your assistant answered from an old policy — or invented a command with no source? | 1.00 | 0.32 | 5.76 |
| 2 | Proof of concept: synthetic docs. | 1.00 | 6.61 | 8.85 |
| 3 | The method works on yours. | 1.00 | 9.07 | 10.91 |
| 4 | Ask something the docs don't contain. | 0.99 | 11.46 | 13.70 |
| 5 | Baseline invents a command. | 0.99 | 13.88 | 15.58 |
| 6 | Fixed says: I can't answer that. | 0.99 | 15.80 | 18.38 |
| 7 | Every claim cites a version, a page, a block. | 0.98 | 18.93 | 22.83 |
| 8 | Open it; the source is highlighted. | 0.98 | 23.03 | 25.39 |
| 9 | I reproduce it on your corpus, separate retrieval from generation, and rank the fixes. | 0.99 | 26.24 | 32.26 |
| 10 | Sixteen unanswerable questions. | 0.96 | 33.21 | 35.71 |
| 11 | Baseline refused none. | 0.96 | 36.16 | 37.70 |
| 12 | Fixed refused all sixteen. | 0.96 | 38.10 | 40.88 |
| 13 | Send me three bad answers. | 0.99 | 41.83 | 43.85 |
| 14 | I'll tell you which layer failed. | 0.99 | 44.20 | 46.10 |

Pause after the opening question: **0.85 s** (5.76 → 6.61).
Pause before the number: **0.95 s** (32.26 → 33.21).
VO master: `audio/final-primary.wav` (source takes in `audio/vo/`).

Teaser narration (38 words, `audio/vo-teaser/`):

1. Ever gotten an answer with no source? (1.00)
2. Baseline invents a command. (1.00)
3. Fixed says: I can't answer that. (1.00)
4. I reproduce it, separate retrieval from generation, rank the fixes. (0.99)
5. Sixteen unanswerable. (0.97)
6. Baseline none. Fixed all sixteen. (0.97)
7. Send three bad answers. (0.99)

The teaser's "I'll name the failed layer." is on the end card, not spoken; the
spoken CTA is the first half, because 22 s does not fit the full sentence
without speeding the voice.

## Beat sheet (primary)

| Time | Picture | On screen | Voice |
|---|---|---|---|
| 0.00–6.46 | Hard open: real baseline card, crop on the invented `sudo helios-install …` command; ember ring draws on the `No citation` chip at 2.67. 20 px programme drift + 1.02→1.04 push. | Has this happened to you? / Baseline pipeline · no citation | 1 |
| 6.46–11.31 | Hard cut to the full baseline card (header, claim support, model/trace footer). 2% card push; moss chip and underline resolve. | Proof of concept · synthetic Helios corpus / No real customer data | 2–3 |
| 11.31–18.78 | Split screen, real baseline (left) and real fixed abstention (right). Both cards hold still; ember ring on the command at 13.88, moss ring on `Answer withheld` at 15.80. | Baseline / Fixed; Invents a command. / Refuses to guess. | 4–6 |
| 18.78–26.09 | Real `CLAIM SUPPORT · 3 claims · 3 citations`, moss ring on the first chip; hard cut to the open citation drawer with the highlighted block. | Three claims. Three citations. / Version. Page. Block. | 7–8 |
| 26.09–32.86 | Real health report, slow programme scroll; moss ring on the missed-abstention row. All three step cards are readable from the first frame; each moss top rule fills at its cue, card bodies opaque over the report. | Reproduce → Measure → Fix + gate | 9 |
| 32.86–41.63 | Big `0 / 16` struck out → `16 / 16` over the dimmed failure gallery. Real health row as the source strip. Hold on 16/16: 3.53 s. | The number · N = 16 / From the health report | 10–12 |
| 41.63–46.55 | End card: title, CTA pill, repo URL, proof-of-concept line. | Send 3 bad answers · Proof of concept · The method applies to your docs. | 13–14 |

## The one number

`0 / 16` is the baseline's unanswerable refusals (it answered every
unanswerable question). `16 / 16` is the fixed pipeline's refusals. The real
health report row used on screen is **`Missed abstention rate 100% → 0%`,
N = 16**; the 100% → 0% means the baseline missed all 16 and the fixed pipeline
missed none. The count is used as the headline because it has a clear
denominator; the underlying `Correct abstention 0.800 → 1.000` is the same
result. Verified in `docs/case-study.md` line 48.

No production-readiness, “no hallucinations”, live-API or customer-data claim is
made. The fixture mode and synthetic corpus are labelled on screen.

## How it is built

- **Real UI**: `scripts/capture-ui.mjs` opens a fresh page per state, selects
  the pipeline, then clicks the sample again (switching the pipeline alone does
  not re-run the query), waits for the card, and captures at 1920 × 1080 @2x.
  Fixture latency (200–1000 ms) is clamped to 80 ms for capture pace only; the
  latency values printed on the cards are untouched.
- **Cards**: `compositions/film.html` + `film.js` (16:9) and
  `compositions/square.html` + `square.js` (1:1), drawn with the app's type and
  palette. Every frame is a function of `t`; no CSS transitions, timers or
  randomness. `window.seek(t)` is the page contract.
- **Captures used**: `captures/10-baseline.png`, `20-fixed-abstain.png`,
  `30-fixed-answer.png`, `40-citation-drawer.png`, `70-health-full.png`.
  `captures/meta.json` stores page coordinates (scrollY + viewport y); the film
  converts the four viewport captures back to viewport coordinates (scrollY
  519) and uses page coordinates only for the full health capture.
- **Render**: Playwright (Chrome 156) renders one JPEG per frame at 30 fps;
  ffmpeg encodes H.264 High with `+faststart`.
- **Sound**: LFM3 takes are placed on the measured speech bounds. A quiet D/A
  pad runs under the method/number section; two low hits sit at the number cut
  and the 16/16 reveal (38.10). The mix is two-pass loudnorm to −14 LUFS /
  −1.5 dBTP; the primary is then encoded 0.1 dB down so the AAC true peak lands
  at −1.5 dBTP.

## Reproduce

From `demo-video/`:

```bash
export PATH=/tmp/opencode/bin:$PATH
curl -s http://127.0.0.1:8082/health      # {"status":"ok"}; start with: lfm3 audio

node proof-film/scripts/capture-ui.mjs
node proof-film/scripts/tts-vo.mjs          # add --force to regenerate all takes
node proof-film/scripts/tts-teaser.mjs
node proof-film/scripts/build-timeline.mjs
node proof-film/scripts/build-teaser.mjs
python3 proof-film/scripts/make-bed.py primary
python3 proof-film/scripts/make-bed.py teaser
node proof-film/scripts/mix-audio.mjs primary
node proof-film/scripts/mix-audio.mjs teaser
```

Two-pass loudnorm (the values are the delivered takes):

```bash
# primary: input I -23.30, TP -6.02, LRA 4.00, thresh -33.93, offset 0.19
ffmpeg -y -i proof-film/audio/mix-primary.wav \
  -af "loudnorm=I=-14:TP=-1.5:LRA=11:measured_I=-23.30:measured_TP=-6.02:measured_LRA=4.00:measured_thresh=-33.93:offset=0.19:linear=true" \
  -ar 48000 -ac 2 -c:a pcm_s24le proof-film/audio/final-primary.wav
# teaser: input I -22.25, TP -6.25, LRA 3.50, thresh -32.83, offset 0.13
ffmpeg -y -i proof-film/audio/mix-teaser.wav \
  -af "loudnorm=I=-14:TP=-1.5:LRA=11:measured_I=-22.25:measured_TP=-6.25:measured_LRA=3.50:measured_thresh=-32.83:offset=0.13:linear=true" \
  -ar 48000 -ac 2 -c:a pcm_s24le proof-film/audio/final-teaser.wav
```

Render and encode:

```bash
node proof-film/scripts/render.mjs frames --cut primary --layout 16x9
node proof-film/scripts/render.mjs frames --cut teaser  --layout 16x9
node proof-film/scripts/render.mjs frames --cut teaser  --layout square

ffmpeg -y -framerate 30 -i proof-film/render/primary-16x9/f%05d.jpg \
  -i proof-film/audio/final-primary.wav \
  -af "volume=-0.1dB" \
  -c:v libx264 -profile:v high -level 4.1 -preset slow -crf 18 -pix_fmt yuv420p \
  -color_primaries bt709 -color_trc bt709 -colorspace bt709 -movflags +faststart \
  -c:a aac -b:a 192k -ar 48000 -shortest proof-film/out/rag-proof-45s.mp4
```

The primary encode applies `-0.1 dB` to `final-primary.wav` so the decoded AAC
lands at −1.5 dBTP; the 720p variant is a lanczos downscale with `-c:a copy`.

TTS is not deterministic: regenerating the takes changes their lengths, so the
timelines must be rebuilt. The delivered WAVs and timeline JSONs are the fixed
cut.

## Video Director QA

Reports, sheets and stills are in `qa/`:

- `qa/vd-primary/report.md` + `beats_sheet.jpg`, `phone_sheet.jpg`, `hook_sheet.jpg`
- `qa/vd-720p/report.md` + sheets
- `qa/vd-teaser/report.md` + sheets
- `qa/vd-square/report.md` + sheets
- `qa/contact-sheet-primary.jpg`; `qa/stills/primary-{0,3,8,14,19,23,30,36,39,44}.png`
- `qa/report.md` — the consolidated result

Primary result: frame 0 PASS; hook 102.8 px / 14.8:1; CTA 51.4 px / 14.8:1;
number 204.2 px / 7.9:1; proof line 14.4:1; no flashes or pops; planned cuts
within 0.69 frame; −14.2 LUFS / −1.5 dBTP. Teaser and 1:1: all text checks pass,
−14.0 LUFS / −1.5 dBTP.

The remaining WARNs are the automated frozen-frame check. They are designed
holds, not dead air: the split holds still by instruction, the 16/16 is held
3.53 s by instruction, and every hold carries voice. The check cannot hear the
VO; the contact sheet and phone sheet were reviewed by eye.

**Layout verification after the review pass.** The three-step row is
120–1800 px with 40 px gutters and 533.33 px cards; the 1:1 stack is 55–1010 px.
All three cards carry number, title and subline from their first frame; the
resolve is the moss top rule filling at its cue. Card bodies stay opaque: no
alpha over table content, no vertical offset. Requested stills: `qa/stills/primary-{8,10.5,12,13,26,29,31}.png`
and `qa/stills/teaser-1x1-{9,10.5,12,13}.png`. The why beat starts at 26.09 s, so
`primary-26.1.png` is the first why frame; 26.0 s is the last citation frame.

## Deviations from the brief

1. **Total is 46.55 s, not 45.0.** The opening beat runs 6.46 s, not 6.0, so the
   0.85 s pause after the question survives without raising the voice speed.
   Within the allowed 44–49 s.
2. **Citation drawer is a hard cut to the open drawer**, not a recorded click.
   The drawer is the real hosted UI with the real highlighted block; the click
   is elided in the edit. No cursor animation was captured, so none is faked.
3. **The health row wording is `Missed abstention rate 100% → 0%, N=16`**, the
   UI's own row, not the `Correct abstention 0.800 → 1.000` form. The headline
   `0/16 → 16/16` is derived from that row and `docs/case-study.md` line 48.
4. **All UI motion is a slow programme drift or a 2–4% centre push.** No pans,
   no `zoomTo`, no small-target camera moves. The split cards hold still.
5. **The teaser's end-card second line is on screen only** ("I'll name the
   failed layer."); the spoken CTA is "Send three bad answers." to fit 22 s.
6. **The teaser's early proof framing is a 22 px top-right label**, not a full
   framing beat; the 48 px end-card line carries the proof statement. The
   primary has the full 4.85 s framing beat.
7. **The 1:1 teaser re-lays the split as a vertical stack** rather than
   cropping the 16:9 split. It holds up and preserves both cards.
8. **No "source not found" chip** was added to the baseline card. The real card
   only has `No citation`; that is what the film shows.
9. **The `old policy` clause is rhetorical.** Only the unanswerable install
   command is demonstrated; there is no stale-version beat.

## Caveats

Hosted app is in fixture mode; the live API is not deployed. Synthetic Helios
corpus; no real customer data. Development numbers, one run, no LLM judge.
Answer correctness/faithfulness are not measured. The poster and end card say
"proof of concept"; the film does not claim production readiness.
