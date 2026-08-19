#!/usr/bin/env python3
"""Layered documentary drone: dark pad + mystery fifth + slow pulse."""
import math
import struct
import wave
from pathlib import Path

SR = 44100
DUR = 280  # seconds, trim later
OUT = Path("/home/user/Adem/audio/music_bed.wav")


def sine(t, f, amp=1.0):
    return amp * math.sin(2 * math.pi * f * t)


def main():
    n = int(SR * DUR)
    frames = bytearray()
    for i in range(n):
        t = i / SR
        # slow fade envelope
        fade_in = min(1.0, t / 4.0)
        fade_out = min(1.0, (DUR - t) / 8.0)
        env = fade_in * fade_out
        # narrative arc: swell mid-late (siege)
        swell = 0.55 + 0.45 * (0.5 - 0.5 * math.cos(math.pi * min(1.0, t / 180.0)))
        if t > 200:
            swell *= 0.55 + 0.45 * math.exp(-(t - 200) / 40.0)
        drone = (
            sine(t, 55.0, 0.22)
            + sine(t, 82.5, 0.12)
            + sine(t, 110.0, 0.08)
            + sine(t, 164.8, 0.05)
        )
        mystery = sine(t, 196.0, 0.04) * (0.6 + 0.4 * math.sin(2 * math.pi * t / 17.0))
        pulse = 0.0
        beat = (t % 3.2)
        if beat < 0.08:
            pulse = 0.09 * (1 - beat / 0.08) * math.sin(2 * math.pi * 73 * t)
        # high airy shimmer
        shimmer = 0.015 * math.sin(2 * math.pi * 523 * t) * math.sin(2 * math.pi * t / 11)
        s = (drone + mystery + pulse + shimmer) * env * swell * 0.55
        s = max(-0.95, min(0.95, s))
        frames += struct.pack("<h", int(s * 32767))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(OUT), "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(frames)
    print("wrote", OUT, "sec", DUR)


if __name__ == "__main__":
    main()
