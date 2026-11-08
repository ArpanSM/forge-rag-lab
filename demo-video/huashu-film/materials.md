# Materials — Forge RAG Lab evidence film

All screenshots are of the real hosted fixture-mode app at
`https://arpansm.github.io/forge-rag-lab/`, captured at 1920×1080 with
Playwright/Chrome at 2× device scale on 2026-11-08. No screen was redrawn or
invented; crops only remove surrounding page chrome.

| File | What it is | Source |
|---|---|---|
| `01-landing.png` | Landing / chat console, top of page | Hosted app `/` |
| `02-fixed-abstain.png` | Fixed pipeline abstains on the on-premises install question | Hosted app `/`, sample question |
| `03-baseline-invented.png` | Baseline invents `sudo helios-install …`; "No citation" | Hosted app `/`, same question, Baseline |
| `04-fixed-citations.png` | v3 API-key rotation answer with three claims and three citations | Hosted app `/`, API-key sample, Fixed |
| `05-citation-drawer.png` | Citation viewer, API keys v3, page 2, block b4, highlighted span | Hosted app `/`, first citation |
| `06-baseline-stale.png` | Baseline answers the same question from v2 | Hosted app `/`, Baseline |
| `07-health-top.png` | Health report header and summary tiles | Hosted app `/health/` |
| `08-health-table.png` | 80-question metric table | Hosted app `/health/` |
| `09-health-failure.png` | Failure gallery, "No abstention" (q057) | Hosted app `/health/` |
| `baseline-command.png` | Crop of the baseline answer card from 03 | Derived |
| `command-detail.png` | Close crop of the invented `sudo helios-install …` line from 03 | Derived |
| `nocite-detail.png` | Close crop of claim support + “No citation” from 03 | Derived |
| `claim-1.png` / `claim-2.png` / `claim-3.png` | One claim + citation chip per row from 04 | Derived |
| `fixed-abstain.png` | Crop of the fixed answer card from 02 | Derived |
| `fixed-citations.png` | Crop of the v3 answer and claim support from 04 | Derived |
| `citation-drawer.png` | Crop of the citation viewer from 05 | Derived |
| `citation-quote.png` | Crop of the highlighted source block from 05 | Derived |
| `health-table.png` | Crop of the metric table from 08 | Derived |
| `health-failure.png` | Crop of the failure card from 09 | Derived |

## Palette

Taken from the app's real tokens (`web/app/globals.css`):

- paper `#f5f1e8`, surface `#fffdf8`
- ink `#1d1e1c`, ink-soft `#343531`, muted `#706c63`
- line `#e5dfd2`
- ember `#d65a31` (accent; a darker `#a84a26` for small text contrast)
- moss `#116b57` (verified / fixed)
- danger `#a33b32`, amber `#975a16` (baseline warning)

## Type

- Noto Serif Regular/Italic — display (the app's serif stack).
- Noto Sans Regular/Bold — UI and body (the app's sans stack).
- Noto Sans Mono — labels (the app's mono stack).

The three Noto families are shipped in `assets/fonts/` under the SIL Open Font
License (see `assets/fonts/OFL.txt` and `LICENSES.md`).

## Facts on screen

- 80 questions: 24 single-hop, 16 multi-hop, 16 version-specific, 8
  conflicting-version, 16 unanswerable (project README).
- Baseline → fixed: recall@10 0.865 → 0.943; gold-source citation coverage
  0.797 → 1.000; version disambiguation 0 → 1.000 (project README and
  `docs/case-study.md`). These are development numbers on a synthetic corpus,
  not a production benchmark.
