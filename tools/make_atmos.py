#!/usr/bin/env python3
"""Unique atmospheric plates matching the documentary palette (not photo repeats)."""
import math
import random
from pathlib import Path

import numpy as np
from PIL import Image

OUT = Path("/home/user/Adem/images")
W, H = 1920, 1080


def vignette(arr):
    y, x = np.ogrid[:H, :W]
    cy, cx = H / 2, W / 2
    r = np.sqrt(((x - cx) / (W * 0.72)) ** 2 + ((y - cy) / (H * 0.72)) ** 2)
    v = np.clip(1.15 - r, 0.25, 1.0)
    return arr * v[..., None]


def save(name, arr):
    arr = np.clip(vignette(arr), 0, 255).astype(np.uint8)
    Image.fromarray(arr, "RGB").save(OUT / name, optimize=True)
    print("wrote", name)


def base(seed, c0, c1):
    rng = np.random.default_rng(seed)
    yy = np.linspace(0, 1, H)[:, None]
    xx = np.linspace(0, 1, W)[None, :]
    mix = 0.45 * yy + 0.25 * xx + 0.15 * np.sin(xx * 7 + seed) * 0.5 + 0.5
    mix = np.clip(mix, 0, 1)[..., None]
    arr = c0 * (1 - mix) + c1 * mix
    noise = rng.normal(0, 7, (H, W, 3))
    return arr + noise


def stars(arr, seed, n=400):
    rng = np.random.default_rng(seed)
    for _ in range(n):
        x = int(rng.integers(0, W))
        y = int(rng.integers(0, int(H * 0.55)))
        b = float(rng.uniform(80, 220))
        arr[y, x] = np.clip(arr[y, x] + [b * 0.8, b * 0.85, b], 0, 255)
    return arr


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    navy = np.array([8, 16, 42], dtype=float)
    amber = np.array([160, 92, 28], dtype=float)
    teal = np.array([18, 90, 110], dtype=float)
    ash = np.array([40, 38, 36], dtype=float)
    gold = np.array([198, 150, 58], dtype=float)
    ink = np.array([6, 10, 18], dtype=float)

    a = base(1, navy, teal)
    a = stars(a, 11, 500)
    save("a01_star_navy.png", a)

    a = base(2, ink, amber * 0.35)
    yy = np.linspace(0, 1, H)[:, None, None]
    a = a * (1 - 0.4 * yy) + (amber * 0.5) * (yy ** 3)
    save("a02_ember_horizon.png", a)

    a = base(3, navy, teal)
    xs = np.linspace(0, 8 * math.pi, W)
    for row in range(H):
        phase = row / 40.0
        wave = (np.sin(xs + phase) * 12 + np.sin(xs * 0.35 + phase * 0.7) * 8).astype(int)
        # already in base; add highlight band
    band = (np.sin(np.linspace(0, 20, W))[None, :] * 18 + 10)
    a[:, :, 1] += band * 0.4
    a[:, :, 2] += band * 0.7
    save("a03_river_ripple.png", a)

    a = base(4, ash, navy)
    rng = np.random.default_rng(4)
    for _ in range(900):
        x = int(rng.integers(0, W))
        y = int(rng.integers(0, H))
        a[y, x] = np.clip(a[y, x] + rng.uniform(20, 90), 0, 255)
    save("a04_falling_ash.png", a)

    a = base(5, ink, gold * 0.25)
    cx, cy = W * 0.5, H * 0.42
    Y, X = np.ogrid[:H, :W]
    r = np.sqrt((X - cx) ** 2 + (Y - cy) ** 2)
    glow = np.exp(-((r / 220) ** 2))[..., None]
    a = a + glow * gold * 0.9
    save("a05_dying_sun.png", a)

    a = base(6, navy, gold * 0.2)
    # islamic-ish geometric lattice
    for i in range(0, W, 80):
        a[:, i : i + 2] = np.clip(a[:, i : i + 2] + gold * 0.15, 0, 255)
    for j in range(0, H, 80):
        a[j : j + 2, :] = np.clip(a[j : j + 2, :] + gold * 0.12, 0, 255)
    for i in range(0, W, 80):
        for j in range(0, H, 80):
            a[j : j + 6, i : i + 6] = np.clip(a[j : j + 6, i : i + 6] + gold * 0.35, 0, 255)
    save("a06_gold_lattice.png", a)

    a = base(7, teal * 0.4, ink)
    rng = np.random.default_rng(7)
    for k in range(40):
        y0 = int(rng.integers(200, 900))
        x0 = int(rng.integers(0, W))
        for t in range(300):
            x = (x0 + t * 3) % W
            y = int(y0 + 18 * math.sin(t / 12.0 + k))
            if 0 <= y < H:
                a[y : y + 2, x] = np.clip(a[y : y + 2, x] + [10, 30, 50], 0, 255)
    save("a07_ink_swirl.png", a)

    a = base(8, navy, ash)
    a = stars(a, 88, 180)
    # moon
    Y, X = np.ogrid[:H, :W]
    r = np.sqrt((X - 1500) ** 2 + (Y - 180) ** 2)
    moon = np.clip(1 - r / 70, 0, 1)[..., None]
    a = a + moon * np.array([210, 205, 180])
    save("a08_moon_watch.png", a)

    a = base(9, amber * 0.15, ink)
    rng = np.random.default_rng(9)
    for _ in range(120):
        x = int(rng.integers(0, W))
        y = int(rng.integers(400, H))
        h = int(rng.integers(8, 80))
        a[max(0, y - h) : y, x] = np.clip(a[max(0, y - h) : y, x] + amber * 0.4, 0, 255)
    save("a09_coals.png", a)

    a = base(10, navy, teal * 0.5)
    yy = np.linspace(0, 1, H)[:, None, None]
    fog = (0.35 * np.exp(-((yy - 0.7) ** 2) / 0.05))
    a = a + fog * np.array([40, 70, 80])
    save("a10_river_mist.png", a)

    a = base(11, ink, navy)
    rng = np.random.default_rng(11)
    for _ in range(60):
        x = int(rng.integers(200, 1700))
        y = int(rng.integers(100, 900))
        rw, rh = int(rng.integers(8, 40)), int(rng.integers(80, 400))
        a[y : y + rh, x : x + rw] = np.clip(a[y : y + rh, x : x + rw] + ash * 0.8, 0, 255)
    save("a11_ruin_silhouettes.png", a)

    a = base(12, navy, gold * 0.15)
    a = stars(a, 12, 260)
    save("a12_deep_night.png", a)

    a = base(13, teal * 0.3, amber * 0.2)
    save("a13_dust_gold.png", a)

    a = base(14, ink, teal)
    yy = np.linspace(0, 1, H)[:, None]
    a[:, :, 2] += (1 - yy) * 25
    save("a14_cold_current.png", a)

    a = base(15, amber * 0.4, navy)
    save("a15_fireglow_sky.png", a)

    a = base(16, navy, ash)
    a = stars(a, 16, 80)
    save("a16_ashen_sky.png", a)

    a = base(17, gold * 0.18, teal * 0.25)
    save("a17_memory_haze.png", a)

    a = base(18, ink, gold * 0.12)
    save("a18_last_ember.png", a)


if __name__ == "__main__":
    main()
