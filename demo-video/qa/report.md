# QA: rag-lab-walkthrough.mp4

1920x1080 @ 30.000 fps, 74.93 s, audio: True

| level | check | detail |
|---|---|---|
| PASS | frame 0 | mean 222.8, contrast 11.8; still confirm it's a finished composition |
| PASS | single-frame flashes | none |
| WARN | pops | small spikes at [0.2, 0.4, 7.233, 7.4, 7.567, 7.733, 7.867, 9.267, 9.467, 9.967, 10.167, 10.333, 10.467, 10.633, 10.8, 11.0, 11.333, 11.467, 11.633, 12.0, 17.167, 17.667, 17.833, 18.0, 18.167, 18.367, 18.667, 18.833, 19.0, 19.2, 19.367, 19.533, 19.667, 19.867, 20.033, 24.333, 24.8, 27.767, 29.333, 29.533, 30.2, 30.4, 30.567, 30.733, 31.067, 31.233, 31.4, 31.567, 31.733, 31.933, 32.067, 32.233, 32.433, 32.6, 38.367, 39.033, 39.767, 40.433, 44.6, 45.633, 45.8, 46.0, 46.167, 46.333, 46.467, 46.667, 46.833, 47.0, 47.2, 47.367, 47.533, 47.667, 47.867, 52.133, 52.633, 53.0, 53.167, 53.267, 53.467, 53.6, 53.8, 53.967, 54.133, 54.267, 54.433, 54.6, 54.767, 54.933, 55.067, 55.233, 58.033, 58.2, 58.367, 58.467, 58.667, 59.0, 59.267, 59.467, 59.6, 59.8, 59.933, 60.067, 60.233, 60.4, 60.567, 60.733, 60.867, 61.367, 61.533, 61.667, 61.833, 62.167]: intended hits, or glitches/stray transitions? |
| INFO | detected cuts | [17.0, 24.467, 24.633, 26.567, 26.733, 26.867, 27.4, 27.6, 29.133, 34.333, 34.467, 36.233, 43.367, 44.433, 44.8, 51.6, 52.8, 57.867, 66.867] |
| WARN | frozen stretch | 4.17-7.23 s (3.07 s): designed hold or dead air? |
| WARN | frozen stretch | 13.8-16.8 s (3.0 s): designed hold or dead air? |
| WARN | frozen stretch | 21.57-24.33 s (2.77 s): designed hold or dead air? |
| WARN | frozen stretch | 25.0-26.17 s (1.17 s): designed hold or dead air? |
| WARN | frozen stretch | 27.77-28.93 s (1.17 s): designed hold or dead air? |
| WARN | frozen stretch | 34.47-36.23 s (1.77 s): designed hold or dead air? |
| WARN | frozen stretch | 36.23-38.37 s (2.13 s): designed hold or dead air? |
| WARN | frozen stretch | 41.83-43.37 s (1.53 s): designed hold or dead air? |
| WARN | frozen stretch | 49.2-51.6 s (2.4 s): designed hold or dead air? |
| WARN | frozen stretch | 56.83-57.87 s (1.03 s): designed hold or dead air? |
| WARN | frozen stretch | 64.43-66.87 s (2.43 s): designed hold or dead air? |
| PASS | loudness | -14.9 LUFS (target -14.0 +/-1), true peak -1.4 dBTP (<= -1.0) |
| INFO | loudest moment | loudest 100 ms at 69.45 s (-8.3 dBFS); is this the payoff? |
| PASS | silence before peak | silences >= 0.4 s below -30.0 dBFS: [{'from': 3.1, 'to': 3.7}, {'from': 5.85, 'to': 7.5}, {'from': 10.9, 'to': 11.55}, {'from': 15.1, 'to': 16.05}, {'from': 18.8, 'to': 19.3}, {'from': 20.3, 'to': 20.85}, {'from': 23.4, 'to': 24.55}, {'from': 26.65, 'to': 27.25}] |

Sheets: qa/beats_sheet.jpg, qa/phone_sheet.jpg, qa/hook_sheet.jpg
Look at all three: numbers catch broken, not bad. The hook sheet is the muted test.
