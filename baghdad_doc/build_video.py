# -*- coding: utf-8 -*-
"""
مونتاج الفيلم الوثائقي: بغداد.. المدينة التي دُفنت تحت الرماد
- حركة كاميرا (Ken Burns) متنوعة على كل صورة
- انتقالات مزج ناعمة + فواصل سوداء بين الفصول
- مزامنة دقيقة: صور كل فصل تُعرض بالضبط أثناء الكلام المتعلق بها
- موسيقى خلفية هادئة تحت التعليق
"""
import subprocess, os, json, math, glob

FF = os.path.expanduser("~/.local/bin/ffmpeg")
BASE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(BASE, "images")
AUD = os.path.join(BASE, "audio")
CLP = os.path.join(BASE, "clips")
os.makedirs(CLP, exist_ok=True)

W, H, FPS = 1920, 1080, 25
XF = 0.9  # مدة الانتقال

def dur(path):
    out = subprocess.run([FF, "-i", path, "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    import re
    m = re.findall(r"time=(\d+):(\d+):([\d.]+)", out)
    h, mi, s = m[-1]
    return int(h)*3600 + int(mi)*60 + float(s)

# ---- الفصول: (ملف الصوت، الصور، فترة قبل الكلام، فترة بعد الكلام) ----
SEGS = [
    ("seg1.mp3", ["title.jpg", "s1_01.jpg", "s1_02.jpg", "s1_03.jpg", "s1_04.jpg"], 3.2, 1.2),
    ("seg2.mp3", ["s2_01.jpg", "s2_02.jpg", "s2_03.jpg", "s2_04.jpg"],              0.4, 1.2),
    ("seg3.mp3", ["s3_01.jpg", "s3_02.jpg", "s3_03.jpg", "s3_04.jpg", "s3_05.jpg"], 0.4, 1.2),
    ("seg4.mp3", ["s4_01.jpg", "s4_02.jpg", "s4_03.jpg", "s4_04.jpg", "s4_05.jpg"], 0.6, 2.0),
    ("seg5.mp3", ["s5_01.jpg", "s5_02.jpg", "s5_03.jpg"],                            0.5, 1.5),
    ("seg6.mp3", ["s6_01.jpg", "s6_02.jpg", "s6_03.jpg", "s6_04.jpg", "outro.jpg"], 0.5, 6.5),
]

# حركات الكاميرا المتنوعة (تتناوب حتى لا يملّ المشاهد)
MOVES = [
    # zoom in (مركز)
    lambda N: f"z='1+0.13*on/{N}':x='(iw-iw/zoom)/2':y='(ih-ih/zoom)/2'",
    # zoom out
    lambda N: f"z='1.14-0.13*on/{N}':x='(iw-iw/zoom)/2':y='(ih-ih/zoom)/2'",
    # pan يمين -> يسار مع زوم خفيف
    lambda N: f"z='1.10':x='(iw-iw/zoom)*(1-on/{N})':y='(ih-ih/zoom)/2'",
    # pan يسار -> يمين
    lambda N: f"z='1.10':x='(iw-iw/zoom)*(on/{N})':y='(ih-ih/zoom)/2'",
    # zoom in نحو الأعلى (مآذن/سماء)
    lambda N: f"z='1+0.12*on/{N}':x='(iw-iw/zoom)/2':y='(ih-ih/zoom)*(1-on/{N})'",
    # pan نزول بطيء
    lambda N: f"z='1.10':x='(iw-iw/zoom)/2':y='(ih-ih/zoom)*(on/{N})'",
]

def make_clip(img_path, out_path, seconds, move_idx):
    N = max(2, int(round(seconds * FPS)))
    move = MOVES[move_idx % len(MOVES)](N)
    vf = (
        f"scale=2400:1350:force_original_aspect_ratio=increase,"
        f"crop=2400:1350,setsar=1,"
        f"zoompan={move}:d={N}:s={W}x{H}:fps={FPS},"
        f"format=yuv420p"
    )
    subprocess.run([FF, "-y", "-loop", "1", "-i", img_path,
                    "-vf", vf, "-t", f"{seconds:.3f}",
                    "-r", str(FPS), "-c:v", "libx264", "-preset", "veryfast",
                    "-crf", "19", out_path],
                   check=True, capture_output=True)

def main():
    # 1) حساب مدد الفصول من الصوت
    seg_info = []
    for (aud, imgs, pre, post) in SEGS:
        d = dur(os.path.join(AUD, aud))
        seg_info.append({"aud": aud, "imgs": imgs, "pre": pre, "post": post,
                         "adur": d, "vdur": pre + d + post})
        print(f"{aud}: narration={d:.2f}s  segment={pre+d+post:.2f}s")

    total = sum(s["vdur"] for s in seg_info)
    print(f"TOTAL video: {total:.1f}s = {total/60:.2f} min")

    # 2) بناء قائمة اللقطات العالمية مع مدة كل لقطة (slot)
    clips = []      # (img, slot, is_chapter_end)
    for si, s in enumerate(seg_info):
        n = len(s["imgs"])
        slot = s["vdur"] / n
        for ii, im in enumerate(s["imgs"]):
            clips.append({"img": os.path.join(IMG, im), "slot": slot,
                          "chapter_end": (ii == n-1 and si < len(seg_info)-1)})

    # 3) توليد اللقطات مع حركة كاميرا متنوعة (المدة = slot + مدة الانتقال)
    move = 0
    files = []
    for i, c in enumerate(clips):
        extra = XF if i < len(clips)-1 else 0.0
        out = os.path.join(CLP, f"clip{i:02d}.mp4")
        if not os.path.exists(out):
            make_clip(c["img"], out, c["slot"] + extra, move)
            print(f"clip {i+1}/{len(clips)} done: {os.path.basename(c['img'])}")
        files.append(out)
        move += 1

    # 4) سلسلة xfade
    inputs = []
    for f in files:
        inputs += ["-i", f]
    fc = []
    prev = "[0:v]"
    offset = 0.0
    for i in range(1, len(files)):
        offset += clips[i-1]["slot"]
        trans = "fadeblack" if clips[i-1]["chapter_end"] else "fade"
        outlbl = f"[v{i}]"
        fc.append(f"{prev}[{i}:v]xfade=transition={trans}:duration={XF}:offset={offset-XF:.3f}{outlbl}")
        prev = outlbl
    fc.append(f"{prev}fade=t=in:st=0:d=1.2,fade=t=out:st={total-2.5:.3f}:d=2.5[vout]")

    # 5) الصوت: التعليق في مواضعه الدقيقة + الموسيقى
    a_inputs = []
    idx0 = len(files)
    t = 0.0
    amix_labels = []
    for si, s in enumerate(seg_info):
        a_inputs += ["-i", os.path.join(AUD, s["aud"])]
        delay_ms = int(round((t + s["pre"]) * 1000))
        fc.append(f"[{idx0+si}:a]adelay={delay_ms}|{delay_ms},apad=whole_dur={total:.3f}[na{si}]")
        amix_labels.append(f"[na{si}]")
        t += s["vdur"]
    a_inputs += ["-i", os.path.join(AUD, "music_bed.mp3")]
    mi = idx0 + len(seg_info)
    fc.append(f"[{mi}:a]volume=0.30,atrim=0:{total:.3f},apad=whole_dur={total:.3f},"
              f"afade=t=out:st={total-6:.3f}:d=6[mus]")
    fc.append("".join(amix_labels) + f"amix=inputs={len(amix_labels)}:normalize=0[nar]")
    fc.append(f"[nar][mus]amix=inputs=2:normalize=0,alimiter=limit=0.95,"
              f"loudnorm=I=-16:TP=-1.5:LRA=11[aout]")

    cmd = [FF, "-y"] + inputs + a_inputs + [
        "-filter_complex", ";".join(fc),
        "-map", "[vout]", "-map", "[aout]",
        "-c:v", "libx264", "-preset", "medium", "-crf", "19",
        "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
        "-t", f"{total:.3f}",
        os.path.join(BASE, "..", "بغداد_تحت_الرماد.mp4")
    ]
    print("Rendering final video...")
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr[-3000:])
        raise SystemExit(1)
    print("DONE")

if __name__ == "__main__":
    main()
