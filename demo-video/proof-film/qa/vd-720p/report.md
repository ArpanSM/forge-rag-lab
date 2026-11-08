# QA: rag-proof-45s-720p.mp4

1280x720 @ 30.000 fps, 46.55 s, audio: True

| level | check | detail |
|---|---|---|
| PASS | frame 0 | mean 241.0, contrast 19.1; still confirm it's a finished composition |
| PASS | hook text | 'hook' at 0.7 s: ~104.2 px font (>= 84), contrast 14.7:1 (>= 7:1) |
| PASS | cta text | 'cta' at 43.7 s: ~50.0 px font (>= 48), contrast 14.8:1 (>= 7:1) |
| PASS | term text | 'number' at 39.1 s: ~206.2 px font (>= 48), contrast 7.8:1 (>= 7:1) |
| PASS | term text | 'proof' at 44.1 s: ~135.4 px font (>= 48), contrast 12.0:1 (>= 7:1) |
| PASS | single-frame flashes | none |
| PASS | pops | none |
| PASS | cuts vs plan | max error 0.69 f; missing []; unplanned [] |
| WARN | frozen stretch | 6.47-11.33 s (4.87 s): designed hold or dead air? |
| WARN | frozen stretch | 11.53-15.87 s (4.33 s): designed hold or dead air? |
| WARN | frozen stretch | 15.87-18.8 s (2.93 s): designed hold or dead air? |
| WARN | frozen stretch | 19.0-22.73 s (3.73 s): designed hold or dead air? |
| WARN | frozen stretch | 22.9-26.1 s (3.2 s): designed hold or dead air? |
| WARN | frozen stretch | 32.87-38.13 s (5.27 s): designed hold or dead air? |
| WARN | frozen stretch | 38.17-41.63 s (3.47 s): designed hold or dead air? |
| WARN | frozen stretch | 41.63-46.53 s (4.9 s): final hold |
| PASS | loudness | -14.2 LUFS (target -14.0 +/-1), true peak -1.5 dBTP (<= -1.0) |
| INFO | loudest moment | loudest 100 ms at 17.55 s (-6.8 dBFS); voice clock: confirm the payoff hit is the loudest non-voice sound and sits in a VO pause |
| PASS | silence before peak | silences >= 0.4 s below -30.0 dBFS: [{'from': 3.0, 'to': 3.5}, {'from': 5.75, 'to': 6.65}, {'from': 10.9, 'to': 11.45}, {'from': 15.4, 'to': 15.9}, {'from': 16.7, 'to': 17.25}, {'from': 18.4, 'to': 18.95}, {'from': 23.4, 'to': 24.1}, {'from': 25.2, 'to': 26.25}] |

Sheets: proof-film/qa/vd-720p/beats_sheet.jpg, proof-film/qa/vd-720p/phone_sheet.jpg, proof-film/qa/vd-720p/hook_sheet.jpg
Look at all three: numbers catch broken, not bad. The hook sheet is the muted test.
