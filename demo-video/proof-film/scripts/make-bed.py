"""Generate a restrained bed and two low payoff hits for the proof film.

No melody: a quiet low pad under the method/number section and two soft hits,
the second (16/16) the loudest non-voice moment. Written at 48 kHz stereo.
"""
import math
import struct
import sys
import json
import wave

cut = sys.argv[1] if len(sys.argv) > 1 else "primary"
timeline = json.load(open(f"proof-film/compositions/timeline-{cut}.json", encoding="utf-8"))
dur = timeline["duration"]
sr = 48000
n = int(dur * sr)
L = [0.0] * n
R = [0.0] * n


def add(sec, val, pan=0.0):
    i = int(sec * sr)
    if 0 <= i < n:
        lv = val * (1.0 - max(0.0, pan) * 0.35)
        rv = val * (1.0 - max(0.0, -pan) * 0.35)
        L[i] += lv
        R[i] += rv


def env(t, a, b, fade_in, fade_out):
    if t < a or t > b:
        return 0.0
    if t < a + fade_in:
        return (t - a) / fade_in
    if t > b - fade_out:
        return (b - t) / fade_out
    return 1.0


if cut == "primary":
    pad_start, pad_end = 25.4, 41.6
else:
    pad_start, pad_end = 8.5, 19.7

# Low D/A pad, very quiet. Slow detune makes it breathe without a pulse.
for i in range(n):
    t = i / sr
    e = env(t, pad_start, pad_end, 1.6, 1.4)
    if e <= 0:
        continue
    mod = 0.82 + 0.18 * math.sin(2 * math.pi * 0.055 * t + 0.7)
    v = (
        0.55 * math.sin(2 * math.pi * 73.42 * t)
        + 0.32 * math.sin(2 * math.pi * 110.0 * t + 0.6)
        + 0.13 * math.sin(2 * math.pi * 146.83 * t + 1.7)
    )
    s = v * e * mod * 0.012  # about -38 dBFS
    L[i] += s
    R[i] += s * 0.97


def hit(sec, amp, length, freq):
    i0 = int(sec * sr)
    m = int(length * sr)
    for j in range(m):
        t = j / sr
        # fast attack, exponential decay, slight pitch drop
        a = min(1.0, t / 0.006)
        d = math.exp(-t * 7.5)
        f = freq * (1.0 - 0.08 * min(1.0, t / 0.12))
        v = math.sin(2 * math.pi * f * t) * a * d * amp
        k = i0 + j
        if 0 <= k < n:
            L[k] += v
            R[k] += v


if cut == "primary":
    hit(timeline["beats"][5]["start"] + 0.02, 0.055, 0.55, 58.0)
    hit(timeline["cues"]["numberSixteen"], 0.085, 0.8, 58.0)
else:
    hit(timeline["beats"][3]["start"] + 0.02, 0.05, 0.45, 60.0)
    hit(timeline["cues"]["numberSixteen"], 0.075, 0.65, 60.0)

# Gentle stereo width and soft clip guard
out = bytearray()
for i in range(n):
    l = max(-0.95, min(0.95, L[i]))
    r = max(-0.95, min(0.95, R[i]))
    out += struct.pack("<hh", int(l * 32767), int(r * 32767))

with wave.open(f"proof-film/audio/bed-{cut}.wav", "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(sr)
    w.writeframes(bytes(out))
print("wrote", f"proof-film/audio/bed-{cut}.wav", round(n / sr, 2), "s")
