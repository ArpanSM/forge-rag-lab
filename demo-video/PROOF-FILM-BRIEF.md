# RAG client proof film — 45s primary + 22s teaser

Produce a **client proof film**, not a product tour: one failure, one fix, one number, one why-me,
one CTA. Target: attached to an Upwork proposal or a cold email, watched on a phone, muted.

Work in `/home/arpan/Forge/forge-rag-lab/demo-video/proof-film/`. Do not touch `videos/`,
`huashu-film/`, `draft.md`, or anything already released. Do not upload, commit, or push.

## Hard rules

1. **45 s primary**, 44–49 s allowed. **100 spoken words maximum.** If a line does not fit its slot
   at 0.97 speed, cut words. Never raise the voice speed to fit.
2. **One failure:** the unanswerable on-premises install command. Do not add the stale-version case
   to this cut.
3. **One number:** unanswerable questions refused, **baseline 0 of 16 → fixed 16 of 16**. The
   underlying rate 0.800 → 1.000 may appear smaller on the health report, but the headline is the
   count, because it has a clear denominator. Verified in `docs/case-study.md` line 48.
4. **Proof-of-concept framing in the first 12 s and on the end card:** “synthetic Helios corpus;
   the method applies to your docs.”
5. **No moving camera over UI.** No `zoomTo` on cards, rows or buttons. Use hard cuts, static crops
   (the answer card can fill the frame), slow programme scroll inside a shot, and outlines/glows
   that travel with content. A full-frame centre push of 1.02–1.04 is allowed on cards, never a pan.
6. **Burned-in captions**, high contrast, one or two lines, bottom safe area, never over the answer
   text. The viewer is likely muted.
7. Voice: LFM3 male, 0.97–1.00, shorter sentences, real pauses after the opening question and
   before the number. Vary per-beat pace (0.96 on the number, 1.00 on framing). Do not use female.
8. Do not claim production readiness, “no hallucinations”, live hosted API, or real customer data.
   Label fixture mode where the UI does.

## Verified UI states (hosted fixture app)

Use `https://arpansm.github.io/forge-rag-lab/`. Selectors and real copy:

- Sample buttons: `getByRole('button', { name: /exact Helios on-premises install command/ })`,
  `/How do I rotate an API key in v3/`.
- Pipeline: `getByRole('button', { name: /Baseline/ })`, `/Fixed/`. **Switching the pipeline alone
  does not re-run the query.** Click the sample again after switching, and wait for the card to
  update before recording.
- Baseline + unanswerable question renders:
  `Run sudo helios-install --license HELIOS-ENTERPRISE --version 3.0 on the target host.`
  plus `This answer has claims but no supporting citations.` and a `No citation` chip.
  This exact state is the opening shot. There is no “source not found” chip; do not fake one.
- Fixed + same question renders: `Answer withheld — evidence is insufficient` and
  `I can't answer that. Helios ended sales of the on-premises distribution on 2024-12-31…`
- Fixed + API-key question renders the v3 answer with `CLAIM SUPPORT · 3 claims · 3 citations`
  and citation chips `API keys · v3 · p.2 · b3/b4`.
- Citation drawer: `button[aria-label^="Open citation"]`; the drawer shows the document block with
  the quote highlighted and the version/page/block metadata.
- Health page: `https://arpansm.github.io/forge-rag-lab/health/`; metric table with
  `Correct abstention 0.800 → 1.000` (or the equivalent row), plus the failure gallery.

Capture at 1920×1080 with a clean profile, no bookmarks bar, no terminal, no cursor wander.

## Script (45 s)

| Time | Picture | Voiceover | On-screen |
|---|---|---|---|
| 0:00–0:06 | Hard open on the baseline answer card: the invented `sudo helios-install …` command, `No citation`, cropped so the text is readable on a phone. Red outline on `No citation`. | Has your assistant ever answered from an old policy — or invented a command with no source? | Has this happened to you? |
| 0:06–0:11 | Static pull to the full card with the `BASELINE` label visible; small chip `synthetic Helios corpus`. | This proof of concept runs on synthetic docs. The method works on yours. | Proof of concept · synthetic corpus |
| 0:11–0:19 | Split screen, labelled: left baseline invents, right fixed `Answer withheld — evidence is insufficient`. Both cards hold still. | Ask something the docs don't contain. The baseline invents a command. The fixed pipeline says: I can't answer that. | Baseline invents · fixed abstains |
| 0:19–0:26 | Fixed API-key answer lands with three citation chips; open the first citation; highlight the block. | Every claim cites a version, a page, a block. Open it, and the source is highlighted. | Version · page · block |
| 0:26–0:34 | Wide health report; three-step strip resolves over it: Reproduce → Measure → Fix + regression gate. | I reproduce this on your corpus, separate retrieval from generation, and rank the fixes with a before-and-after. | Reproduce → Measure → Fix + gate |
| 0:34–0:40 | Hard cut to a big number card over a dimmed failure gallery: `0 / 16` crossed out → `16 / 16`. Hold at least 3 s. | Sixteen unanswerable questions. The baseline refused none. The fixed pipeline refused all sixteen. | 0/16 → 16/16 unanswerable questions refused |
| 0:40–0:45 | End card: title, `github.com/ArpanSM/forge-rag-lab`, proof-of-concept line, `Send three bad answers`. | Send me three bad answers. I'll tell you which layer failed. | Send 3 bad answers · Proof of concept · method applies to your docs |

Word check: ~103. Trim the middle of beat 5 first if the read runs long; beat 6 must not be cut.

## Assembly

- **Argo** for all real UI capture (video or stills; stills are fine where nothing moves).
- **Compositions** for the title, split screen, three-step strip, number card and end card. Argo
  compositions or a local HTML page captured at 1920×1080 both work; use ffmpeg for the final
  assembly, split screen, captions burn-in and audio mux.
- **ffmpeg** (`/tmp/opencode/bin/ffmpeg`) at the end: H.264 High, 30 fps, `+faststart`,
  AAC 192 kbps, −14 LUFS integrated, −1.5 dBTP. Keep the 45 s file under 30 MB so it attaches
  easily; a 720p variant is welcome.
- **Video Director** for QA: hook in the first 3 s, no flat frames over 1.5 s, no text collisions,
  readable captions at 25% scale, loudness.

## Teaser (22 s)

Same footage, 16:9. Beats: question (4 s) → baseline invents / fixed abstains (5 s) → why-me line
(5 s) → 0/16 → 16/16 (4 s) → CTA end card (4 s). Same voice, same captions. If the framing survives
a 1:1 crop, add a 1:1 version; if it would cut the split screen, skip it and say so.

## Deliverables

- `proof-film/out/rag-proof-45s.mp4`, `.srt`, `.vtt`, poster PNG
- `proof-film/out/rag-proof-teaser-22s.mp4`, poster
- `proof-film/out/rag-proof-45s-720p.mp4`
- `proof-film/out/` 1:1 teaser if it holds up
- `proof-film/qa/` Video Director report, contact sheets, stills at 0, 3, 8, 14, 19, 23, 30, 36, 39, 44
- `proof-film/README.md` with the exact script, VO file, capture commands and reproduce steps

## Report back

Paths, ffprobe facts (duration, resolution, fps, size, loudness), the exact narration, QA result,
and any beat that had to change because the real UI did not match. Flag anything you could not
capture honestly.
