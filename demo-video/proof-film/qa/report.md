# Video Director QA — consolidated

Four files were measured with
`video-director/scripts/qa_video.py`. Full reports, contact sheets and the
muted-phone/hook sheets are next to this file.

| File | Size | Loudness | True peak | Text checks | Cuts |
|---|---|---|---|---:|---|
| `out/rag-proof-45s.mp4` | 1920×1080, 46.55 s | −14.2 LUFS | −1.5 dBTP | all pass | 0.69 f max error |
| `out/rag-proof-45s-720p.mp4` | 1280×720, 46.55 s | −14.2 LUFS | −1.5 dBTP | all pass | 0.69 f max error |
| `out/rag-proof-teaser-22s.mp4` | 1920×1080, 22.10 s | −14.0 LUFS | −1.5 dBTP | all pass | 0.51 f max error |
| `out/rag-proof-teaser-22s-1x1.mp4` | 1080×1080, 22.10 s | −14.0 LUFS | −1.5 dBTP | all pass | 0.51 f max error |

Primary text measurements (rendered, 1080 short side):

- Hook `Has this happened to you?` — 102.8 px, 14.8:1
- CTA `Send 3 bad answers` — 51.4 px, 14.8:1
- `0 / 16` — 204.2 px, 7.9:1
- End-card proof line — 14.4:1

All four files: frame 0 is a finished composition, no single-frame flashes, no
audio pops, planned cuts detected within one frame. The hook sheet at 360 px is
readable muted; the phone sheet at 360 px wide reads at every beat.

## Why the frozen-frame WARNs are designed holds

The automated check reports long low-motion stretches. Each is a held card with
voice under it; the check cannot hear the voice. None is a slideshow freeze.

| File | Window | Why it holds |
|---|---|---|
| 45 s | 6.47–11.33 (4.87 s) | Full real baseline card read. VO runs 6.61–10.91. 2% card push, chip/underline resolve. |
| 45 s | 11.53–18.80 | Split screen. The brief requires both cards to hold still. Ember ring 13.88, moss ring 15.80; VO 11.46–18.38. |
| 45 s | 19.00–22.73 (3.73 s) | Claim support read; first citation ring at 20.23. |
| 45 s | 22.90–26.10 (3.20 s) | Citation drawer; metadata rows and bracket resolve 23.28–23.85; VO 23.03–25.39. |
| 45 s | 32.87–38.13 (5.27 s) | `0 / 16` read with a 2% centre push and a slow background programme scroll; strike at 36.16; VO 33.21–37.70. |
| 45 s | 38.17–41.63 (3.47 s) | The required ≥3 s hold on `16 / 16`. |
| 45 s | 41.63–46.53 (4.90 s) | Final end-card read: headline, CTA, URL, proof line. |
| 22 s | 4.17–8.70 (4.53 s) | Split screen; the same brief rule. |
| 22 s | 13.80–19.13 (5.33 s) | `0 / 16` hold, strike 16.27, `16 / 16` 17.77. |
| 22 s | 19.57–22.10 (2.53 s) | Final end-card read. |
| 1:1 | 0.37–2.97 (2.60 s) | Hook card read, ring at 1.42; 2% push. |
| 1:1 | 13.80–19.57 (5.77 s) | Number hold, strike 16.27, `16 / 16` 17.77. |
| 1:1 | 19.57–22.10 (2.53 s) | Final end-card read. |

## Loudest moment

With a voice clock the loudest 100 ms is the voice (17.55 s in the 45 s cut;
7.35 s in the teaser). The loudest non-voice sound is the low hit on the
`16 / 16` reveal at 38.10 s (45 s) / 17.77 s (teaser), placed at the end of the
0.95 s (45 s) / 0.65 s (teaser) pause before "Fixed refused all sixteen."
The bed is a quiet D/A pad under 25.4–41.6 s (45 s) / 8.5–19.7 s (teaser).

## Layout verification (post-review)

- 16:9 three-step row spans **120–1800 px**, three 533.33 px cards with 40 px
  gutters and equal outer margins. The health table below is independent.
- 1:1 stack spans **55–1010 px**; all three cards use the same left/right edges.
- All three cards show number, title and subline from their first frame. The
  resolve is the **moss top rule** filling at its cue; card bodies stay opaque,
  so no table text shows through and no card text sits on table text. Empty
  dashed placeholders are gone; there is no vertical offset either.
- First subline is **“Same 16 questions. Your docs.”** in both cuts.
- Stills checked: `stills/primary-{8,10.5,12,13,26,29,31}.png`,
  `stills/teaser-1x1-{9,10.5,12,13}.png`. The why beat begins at 26.09 s, so
  the `primary-26.1.png` still is the first why frame; `primary-26.png` is the
  last citation frame.

## Read checks

- Every card is above the 25% / 360 px legibility check; the hook sheet and
  phone sheet are in each `vd-*` folder.
- Captions are burned in, max two lines, 40 px (16:9) / 34 px (1:1) on a
  solid cream bar in the bottom safe area. The answer text/citation block is
  composed above the bar; no caption overlaps it.
- The end-card proof line is 48 px ink on cream (14.4:1) so the
  proof-of-concept framing survives muted and on a phone.
