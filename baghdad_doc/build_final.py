# -*- coding: utf-8 -*-
"""تجميع نهائي على مراحل (اقتصادي في الذاكرة):
A) دمج لقطات كل فصل مع انتقالات xfade + فيد أسود بين الفصول
B) ضم الفصول الستة (concat بدون إعادة ترميز)
C) مزج الصوت كاملاً (تعليق + موسيقى) في ملف مستقل
D) تركيب الصوت على الصورة
"""
import subprocess, os, re

FF = os.path.expanduser("~/.local/bin/ffmpeg")
BASE = os.path.dirname(os.path.abspath(__file__))
AUD, CLP = os.path.join(BASE, "audio"), os.path.join(BASE, "clips")
OUT = os.path.join(BASE, "..", "بغداد_تحت_الرماد.mp4")
XF = 0.9

def dur(path):
    err = subprocess.run([FF, "-i", path, "-f", "null", "-"], capture_output=True, text=True).stderr
    h, m, s = re.findall(r"time=(\d+):(\d+):([\d.]+)", err)[-1]
    return int(h)*3600 + int(m)*60 + float(s)

def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr[-2500:]); raise SystemExit(1)

SEGS = [
    ("seg1.mp3", 5, 3.2, 1.2),
    ("seg2.mp3", 4, 0.4, 1.2),
    ("seg3.mp3", 5, 0.4, 1.2),
    ("seg4.mp3", 5, 0.6, 2.0),
    ("seg5.mp3", 3, 0.5, 1.5),
    ("seg6.mp3", 5, 0.5, 6.5),
]

# مدد الفصول
info = []
for aud, n, pre, post in SEGS:
    d = dur(os.path.join(AUD, aud))
    info.append({"aud": aud, "n": n, "pre": pre, "post": post, "adur": d, "vdur": pre + d + post})
total = sum(s["vdur"] for s in info)
print(f"TOTAL: {total:.1f}s = {total/60:.2f} min")

# ---- المرحلة A: فيديو كل فصل ----
ci = 0
seg_files = []
for si, s in enumerate(info):
    n = s["n"]; slot = s["vdur"] / n
    ins, fc = [], []
    for k in range(n):
        ins += ["-i", os.path.join(CLP, f"clip{ci+k:02d}.mp4")]
    prev, off = "[0:v]", 0.0
    for k in range(1, n):
        off += slot
        lbl = f"[v{k}]"
        fc.append(f"{prev}[{k}:v]xfade=transition=fade:duration={XF}:offset={off-XF:.3f}{lbl}")
        prev = lbl
    # فيد أسود عند حدود الفصول + بداية/نهاية الفيلم
    fin = 1.2 if si == 0 else 0.5
    fout = 2.5 if si == len(info)-1 else 0.5
    fc.append(f"{prev}trim=duration={s['vdur']:.3f},setpts=PTS-STARTPTS,"
              f"fade=t=in:st=0:d={fin},fade=t=out:st={s['vdur']-fout:.3f}:d={fout}[vout]")
    outp = os.path.join(CLP, f"segv{si}.mp4")
    run([FF, "-y"] + ins + ["-filter_complex", ";".join(fc), "-map", "[vout]",
         "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-r", "25", outp])
    seg_files.append(outp); ci += n
    print(f"segment video {si+1}/6 done ({s['vdur']:.1f}s)")

# ---- المرحلة B: ضم الفصول ----
lst = os.path.join(CLP, "list.txt")
with open(lst, "w") as f:
    for p in seg_files:
        f.write(f"file '{p}'\n")
full_v = os.path.join(CLP, "full_video.mp4")
run([FF, "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", full_v])
print("concat done")

# ---- المرحلة C: مزج الصوت ----
ins, fc, labels = [], [], []
t = 0.0
for si, s in enumerate(info):
    ins += ["-i", os.path.join(AUD, s["aud"])]
    dms = int(round((t + s["pre"]) * 1000))
    fc.append(f"[{si}:a]adelay={dms}|{dms},apad=whole_dur={total:.3f}[n{si}]")
    labels.append(f"[n{si}]")
    t += s["vdur"]
ins += ["-i", os.path.join(AUD, "music_bed.mp3")]
mi = len(info)
fc.append(f"[{mi}:a]volume=0.30,atrim=0:{total:.3f},apad=whole_dur={total:.3f},"
          f"afade=t=out:st={total-6:.3f}:d=6[mus]")
fc.append("".join(labels) + f"amix=inputs={len(labels)}:normalize=0[nar]")
fc.append("[nar][mus]amix=inputs=2:normalize=0,alimiter=limit=0.95,"
          "loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000[aout]")
mix = os.path.join(CLP, "mix.m4a")
run([FF, "-y"] + ins + ["-filter_complex", ";".join(fc), "-map", "[aout]",
     "-c:a", "aac", "-b:a", "192k", mix])
print("audio mix done")

# ---- المرحلة D: التركيب النهائي ----
run([FF, "-y", "-i", full_v, "-i", mix, "-map", "0:v", "-map", "1:a",
     "-c:v", "copy", "-c:a", "copy", "-movflags", "+faststart",
     "-t", f"{total:.3f}", OUT])
print("FINAL DONE:", OUT)
