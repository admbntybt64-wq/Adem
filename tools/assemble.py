#!/usr/bin/env python3
"""Assemble 1080p30 documentary with Ken Burns, titles, ducked music."""
from __future__ import annotations

import glob
import math
import os
import re
import shutil
import subprocess
from pathlib import Path

import arabic_reshaper
from bidi.algorithm import get_display
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

ROOT = Path("/home/user/Adem")
FF = "/home/user/venv/lib/python3.11/site-packages/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2"
IMG = ROOT / "images"
AUD = ROOT / "audio"
WORK = ROOT / "build"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
W, H, FPS = 1920, 1080, 30

CHAPTERS = [
    (1, "الافتتاح", "بغداد التي صارت رمادًا"),
    (2, "النشأة", "المدينة المدوّرة"),
    (3, "بيت الحكمة", "عاصمة العلم"),
    (4, "الحياة", "أسواقٌ وقناديل"),
    (5, "الشيخوخة", "ضعف الخلافة"),
    (6, "العاصفة", "هولاكو على الأبواب"),
    (7, "الحصار", "حلقة النار"),
    (8, "السقوط", "١٠ فبراير ١٢٥٨"),
    (9, "الرماد", "اثنا عشر يومًا"),
    (10, "المعرفة", "دجلة يبتلع الكتب"),
    (11, "الخليفة", "انطفاء السراج"),
    (12, "ما بعد", "جرحٌ مفتوح"),
    (13, "الشهادة", "النهر لا ينسى"),
    (14, "النهر", "دجلة الشاهد"),
    (15, "مدينة أخرى", "بعد المغول"),
    (16, "الأسباب", "ضعفٌ وتفرّق"),
    (17, "الوعد", "حين غرق العصر"),
    (18, "الذاكرة", "نجمةٌ انطفأت"),
    (19, "الدرس", "كيف تختفي الحواضر"),
    (20, "الخاتمة", "وبقي الاسم درسًا"),
]


def ar(text: str) -> str:
    return get_display(arabic_reshaper.reshape(text))


def probe_dur(path: Path) -> float:
    p = subprocess.run([FF, "-i", str(path)], stderr=subprocess.PIPE, text=True)
    m = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", p.stderr)
    return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))


def load_font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT, size)


def make_title_card(path: Path, title: str, sub: str) -> None:
    img = Image.open(IMG / "01b_city_glow.png").convert("RGB").resize((W, H), Image.Resampling.LANCZOS)
    img = ImageEnhance.Brightness(img).enhance(0.35)
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    d.rectangle([0, 0, W, H], fill=(4, 10, 28, 110))
    # gold line
    d.rectangle([W // 2 - 220, 560, W // 2 + 220, 564], fill=(198, 150, 58, 220))
    img = Image.alpha_composite(img.convert("RGBA"), overlay)
    draw = ImageDraw.Draw(img)
    ft = load_font(86)
    fs = load_font(40)
    t, s = ar(title), ar(sub)
    tb = draw.textbbox((0, 0), t, font=ft)
    draw.text(((W - (tb[2] - tb[0])) / 2, 430), t, font=ft, fill=(236, 220, 180, 255))
    sb = draw.textbbox((0, 0), s, font=fs)
    draw.text(((W - (sb[2] - sb[0])) / 2, 580), s, font=fs, fill=(170, 200, 210, 255))
    img.convert("RGB").save(path)


def make_end_card(path: Path) -> None:
    img = Image.open(IMG / "13b_final_river.png").convert("RGB").resize((W, H), Image.Resampling.LANCZOS)
    img = ImageEnhance.Brightness(img).enhance(0.4)
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 90))
    img = Image.alpha_composite(img.convert("RGBA"), overlay)
    draw = ImageDraw.Draw(img)
    ft, fs = load_font(92), load_font(38)
    t, s = ar("النهاية"), ar("بغداد صارت رمادًا… وبقي الاسم درسًا")
    tb = draw.textbbox((0, 0), t, font=ft)
    draw.text(((W - (tb[2] - tb[0])) / 2, 430), t, font=ft, fill=(236, 220, 180, 255))
    sb = draw.textbbox((0, 0), s, font=fs)
    draw.text(((W - (sb[2] - sb[0])) / 2, 560), s, font=fs, fill=(180, 200, 210, 255))
    img.convert("RGB").save(path)


def lower_third_overlay(chapter: str, w=W, h=H) -> Image.Image:
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([70, 900, 820, 1000], radius=8, fill=(6, 14, 32, 185))
    d.rectangle([70, 900, 78, 1000], fill=(198, 150, 58, 255))
    f = load_font(36)
    d.text((100, 920), ar(chapter), font=f, fill=(236, 220, 190, 255))
    return im


def ken_burns(src: Path, dst: Path, seconds: float, mode: int, overlay_path: Path | None) -> None:
    seconds = max(3.5, min(5.0, seconds))
    frames = max(2, int(round(seconds * FPS)))
    # varied Ken Burns via zoompan
    if mode % 6 == 0:
        zexpr = "min(1.12,1.0+0.0007*on)"
        xexpr = "iw/2-(iw/zoom/2)"
        yexpr = "ih/2-(ih/zoom/2)-20+0.15*on"
    elif mode % 6 == 1:
        zexpr = "if(lte(zoom,1.0),1.12,max(1.02,zoom-0.0006))"
        xexpr = "0.3*on"
        yexpr = "ih/2-(ih/zoom/2)"
    elif mode % 6 == 2:
        zexpr = "min(1.1,1.02+0.0005*on)"
        xexpr = "iw-iw/zoom-0.35*on"
        yexpr = "ih/2-(ih/zoom/2)"
    elif mode % 6 == 3:
        zexpr = "min(1.11,1.0+0.00065*on)"
        xexpr = "iw/2-(iw/zoom/2)"
        yexpr = "ih-ih/zoom-0.2*on"
    elif mode % 6 == 4:
        zexpr = "if(lte(zoom,1.0),1.1,max(1.03,zoom-0.00045))"
        xexpr = "iw/2-(iw/zoom/2)"
        yexpr = "20+0.18*on"
    else:
        zexpr = "1.06+0.03*sin(on/40)"
        xexpr = "20+0.4*on"
        yexpr = "ih/2-(ih/zoom/2)"
    vf = (
        f"scale=2304:1296,zoompan=z='{zexpr}':x='{xexpr}':y='{yexpr}':d={frames}:s=1920x1080:fps={FPS},"
        f"vignette=PI/5"
    )
    cmd = [FF, "-y", "-loglevel", "error", "-loop", "1", "-i", str(src)]
    if overlay_path:
        cmd += ["-i", str(overlay_path)]
        vf = vf + f",overlay=0:0:enable='lt(t,3.2)'"
    cmd += ["-filter_complex", vf, "-t", f"{seconds:.3f}", "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p", "-crf", "20", str(dst)]
    subprocess.check_call(cmd)


def split_dur(total: float) -> list[float]:
    """Split into 3.5–5.0s pieces summing to total."""
    n = max(1, math.ceil(total / 5.0))
    while total / n < 3.5 and n > 1:
        n -= 1
    # prefer more shots if leftover would exceed 5
    while total / n > 5.0:
        n += 1
    base = total / n
    return [base] * n


def main():
    WORK.mkdir(exist_ok=True)
    (WORK / "clips").mkdir(exist_ok=True)

    photos = sorted([p for p in IMG.glob("*.png") if not p.name.startswith("a")])
    atmos = sorted(IMG.glob("a*.png"))
    # interleave: prefer photos, fill with atmos, never reuse
    pool = photos + atmos
    used = set()

    def take() -> Path:
        for p in pool:
            if p.name not in used:
                used.add(p.name)
                return p
        raise RuntimeError("ran out of unique images")

    make_title_card(WORK / "title_src.jpg", "بغداد التي صارت رمادًا", "سقوط حاضرة الدنيا — ٦٥٦هـ / ١٢٥٨م")
    make_end_card(WORK / "end_src.jpg")

    seq_videos = []
    # opening title 5.0s
    tdst = WORK / "clips" / "00_title.mp4"
    if not tdst.exists():
        ken_burns(WORK / "title_src.jpg", tdst, 5.0, 0, None)
    seq_videos.append(tdst)

    vo_files = []
    for i in range(1, 21):
        fs = sorted(AUD.glob(f"{i:02d}_*.mp3"))
        vo_files.append(fs[0])

    vo_durs = [probe_dur(p) for p in vo_files]
    print("VO total", sum(vo_durs))

    chapter_map = {n: name for n, name, _ in CHAPTERS}

    clip_i = 1
    for idx, (vo, dur) in enumerate(zip(vo_files, vo_durs), start=1):
        parts = split_dur(dur)
        # fix sum drift
        drift = dur - sum(parts)
        parts[-1] += drift
        parts[-1] = min(5.0, max(3.5, parts[-1]))
        # if last still not matching, absorb in previous
        if abs(sum(parts) - dur) > 0.05:
            # scale
            k = dur / sum(parts)
            parts = [max(3.5, min(5.0, x * k)) for x in parts]
            # final pad/trim handled by audio later
        ovp = WORK / f"lt_{idx:02d}.png"
        lower_third_overlay(chapter_map[idx]).save(ovp)
        for j, sec in enumerate(parts):
            src = take()
            ov = ovp if j == 0 else None
            dst = WORK / "clips" / f"{clip_i:03d}_{idx:02d}_{j}.mp4"
            print("shot", dst.name, src.name, round(sec, 2))
            ken_burns(src, dst, sec, clip_i, ov)
            seq_videos.append(dst)
            clip_i += 1

    ken_burns(WORK / "end_src.jpg", WORK / "clips" / "zz_end.mp4", 5.0, 3, None)
    seq_videos.append(WORK / "clips" / "zz_end.mp4")

    # concat video
    lst = WORK / "list.txt"
    lst.write_text("".join(f"file '{p}'\n" for p in seq_videos))
    rawv = WORK / "video_raw.mp4"
    subprocess.check_call(
        [FF, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst),
         "-c", "copy", str(rawv)]
    )

    # voice: 5s silence + vos with 0s gap + 5s silence
    sil = WORK / "sil5.wav"
    subprocess.check_call([FF, "-y", "-loglevel", "error", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono", "-t", "5", str(sil)])
    vo_list = WORK / "vo_list.txt"
    lines = [f"file '{sil}'\n"]
    for p in vo_files:
        lines.append(f"file '{p}'\n")
    lines.append(f"file '{sil}'\n")
    vo_list.write_text("".join(lines))
    vo_all = WORK / "voice.wav"
    subprocess.check_call(
        [FF, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(vo_list),
         "-ar", "44100", "-ac", "1", str(vo_all)]
    )

    vdur = probe_dur(rawv)
    adur = probe_dur(vo_all)
    print("video", vdur, "voice", adur)
    target = max(vdur, adur, 240.0)
    # pad video to target if short
    padded = WORK / "video_pad.mp4"
    subprocess.check_call(
        [FF, "-y", "-loglevel", "error", "-i", str(rawv),
         "-vf", f"tpad=stop_mode=clone:stop_duration={max(0, target-vdur):.3f}",
         "-t", f"{target:.3f}", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
         str(padded)]
    )

    music = AUD / "music_bed.wav"
    mixed = WORK / "mix.m4a"
    # voice louder ~2.2x music via weights + sidechain
    filter_complex = (
        "[1:a]volume=0.22,afade=t=in:st=0:d=2,afade=t=out:st=232:d=7[m];"
        "[0:a]asplit=2[v][sc];"
        "[m][sc]sidechaincompress=threshold=0.05:ratio=7:attack=40:release=350:makeup=2[ducked];"
        "[v]volume=1.15[vx];"
        "[vx][ducked]amix=inputs=2:duration=first:dropout_transition=0,alimiter=limit=0.95[a]"
    )
    subprocess.check_call(
        [FF, "-y", "-loglevel", "error",
         "-i", str(vo_all), "-i", str(music),
         "-filter_complex", filter_complex, "-map", "[a]",
         "-t", f"{target:.3f}", "-c:a", "aac", "-b:a", "160k", str(mixed)]
    )

    out = ROOT / "documentary_final.mp4"
    # bitrate for ~108MB: 4min * 3.6Mbps ≈ 108MB
    subprocess.check_call(
        [FF, "-y", "-loglevel", "warning",
         "-i", str(padded), "-i", str(mixed),
         "-map", "0:v", "-map", "1:a",
         "-c:v", "libx264", "-preset", "medium", "-profile:v", "high",
         "-pix_fmt", "yuv420p", "-r", "30",
         "-b:v", "3500k", "-maxrate", "3800k", "-bufsize", "7000k",
         "-c:a", "aac", "-b:a", "160k", "-ar", "44100",
         "-movflags", "+faststart",
         "-t", f"{min(target, 299):.3f}",
         str(out)]
    )
    prev = ROOT / "documentary_preview_720p.mp4"
    subprocess.check_call(
        [FF, "-y", "-loglevel", "error", "-i", str(out),
         "-vf", "scale=1280:720", "-c:v", "libx264", "-b:v", "1400k",
         "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", str(prev)]
    )
    print("OUT", out, out.stat().st_size / 1e6, "MB")
    print("PREV", prev, prev.stat().st_size / 1e6, "MB")
    print("used images", len(used))


if __name__ == "__main__":
    main()
