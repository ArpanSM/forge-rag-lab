# QA: rag-proof-teaser-22s-1x1.mp4

1080x1080 @ 30.000 fps, 22.10 s, audio: True

| level | check | detail |
|---|---|---|
| PASS | frame 0 | mean 238.8, contrast 22.8; still confirm it's a finished composition |
| PASS | hook text | 'hook' at 0.8 s: ~84.7 px font (>= 84), contrast 14.8:1 (>= 7:1) |
| PASS | cta text | 'cta' at 20.8 s: ~83.3 px font (>= 48), contrast 14.8:1 (>= 7:1) |
| PASS | term text | 'number' at 18.7 s: ~105.6 px font (>= 48), contrast 7.8:1 (>= 7:1) |
| PASS | term text | 'proof' at 21.0 s: ~134.7 px font (>= 48), contrast 14.4:1 (>= 7:1) |
| PASS | single-frame flashes | none |
| PASS | pops | none |
| PASS | cuts vs plan | max error 0.51 f; missing []; unplanned [] |
| WARN | frozen stretch | 0.37-2.97 s (2.6 s): designed hold or dead air? |
| WARN | frozen stretch | 4.17-6.13 s (1.97 s): designed hold or dead air? |
| WARN | frozen stretch | 6.17-8.7 s (2.53 s): designed hold or dead air? |
| WARN | frozen stretch | 13.8-19.57 s (5.77 s): designed hold or dead air? |
| WARN | frozen stretch | 19.57-22.1 s (2.53 s): final hold |
| PASS | loudness | -14.0 LUFS (target -14.0 +/-1), true peak -1.5 dBTP (<= -1.0) |
| INFO | loudest moment | loudest 100 ms at 7.35 s (-7.3 dBFS); voice clock: confirm the payoff hit is the loudest non-voice sound and sits in a VO pause |
| PASS | silence before peak | silences >= 0.4 s below -30.0 dBFS: [{'from': 2.85, 'to': 4.1}, {'from': 8.1, 'to': 8.85}, {'from': 9.8, 'to': 10.25}, {'from': 15.65, 'to': 16.05}, {'from': 17.1, 'to': 17.75}, {'from': 19.3, 'to': 19.75}, {'from': 21.6, 'to': 22.1}] |

Sheets: proof-film/qa/vd-square/beats_sheet.jpg, proof-film/qa/vd-square/phone_sheet.jpg, proof-film/qa/vd-square/hook_sheet.jpg
Look at all three: numbers catch broken, not bad. The hook sheet is the muted test.
