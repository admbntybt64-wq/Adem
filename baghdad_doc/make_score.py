# -*- coding: utf-8 -*-
"""موسيقى تصويرية وثائقية نفسية — تتغير مع فصول الفيلم:
1) غموض وترقب  2) دفء البناء  3) إشراق العصر الذهبي
4) توتر وطبول الحرب  5) حزن ورثاء  6) أمل ونهوض
"""
import numpy as np, wave, os

SR = 44100
BASE = os.path.dirname(os.path.abspath(__file__))
# حدود الفصول (من المونتاج النهائي)
BOUNDS = [0.0, 36.7, 77.0, 115.6, 156.6, 188.6, 239.33]
TOTAL = BOUNDS[-1]
N = int(TOTAL * SR)
t = np.arange(N) / SR
L = np.zeros(N); R = np.zeros(N)

def note(f): return f  # هرتز

# ترددات (ري مينور كأساس)
D2, F2, G2, A2, Bb2, C3, D3, E3, F3, G3, A3, Bb3, C4, D4, E4, F4, Fs4, G4, A4, D5 = \
 73.42,87.31,98.0,110.0,116.54,130.81,146.83,164.81,174.61,196.0,220.0,233.08,261.63,293.66,329.63,349.23,369.99,392.0,440.0,587.33

def pad(freq, start, dur, amp=1.0, attack=3.0, release=4.0, vib=0.15, detune=0.0015):
    """طبقة باد دافئة: توافقيات + اهتزاز بطيء + ستيريو منفصل"""
    i0, i1 = int(start*SR), min(N, int((start+dur)*SR))
    n = i1 - i0
    if n <= 0: return
    tt = np.arange(n) / SR
    env = np.minimum(1, tt/attack) * np.minimum(1, (dur-tt)/release)
    env = np.clip(env, 0, 1)
    lfo = 1 + 0.12*np.sin(2*np.pi*vib*tt)
    for k, (h, a) in enumerate([(1,1.0),(2,0.42),(3,0.16),(4,0.07)]):
        ph = k*1.7
        L[i0:i1] += amp*a*env*lfo*np.sin(2*np.pi*freq*h*(1-detune)*tt+ph)
        R[i0:i1] += amp*a*env*lfo*np.sin(2*np.pi*freq*h*(1+detune)*tt+ph+0.5)

def drum(start, freq=55, amp=1.0, dur=1.1):
    """ضربة طبل حربي عميقة (انزلاق التردد للأسفل + اضمحلال أسي)"""
    i0 = int(start*SR); n = min(int(dur*SR), N-i0)
    if n <= 0: return
    tt = np.arange(n)/SR
    f = freq*np.exp(-tt*2.2)+34
    phase = 2*np.pi*np.cumsum(f)/SR
    env = np.exp(-tt*4.5)
    s = amp*env*np.sin(phase)
    s += amp*0.25*env*np.random.RandomState(int(start*100)).randn(n)*np.exp(-tt*22)
    L[i0:i0+n] += s; R[i0:i0+n] += s*0.92

def bell(start, freq, amp=0.5, dur=5.0):
    """جرس/رنين حزين بتوافقيات غير منسجمة"""
    i0 = int(start*SR); n = min(int(dur*SR), N-i0)
    if n <= 0: return
    tt = np.arange(n)/SR
    env = np.exp(-tt*0.9)
    s = amp*env*(np.sin(2*np.pi*freq*tt)+0.5*np.sin(2*np.pi*freq*2.76*tt)*np.exp(-tt*1.8)+0.25*np.sin(2*np.pi*freq*5.4*tt)*np.exp(-tt*3.5))
    L[i0:i0+n] += s*0.8; R[i0:i0+n] += s
    
def shimmer(start, dur, scale, amp=0.09, seed=7, rate=0.55):
    """لمعان نغمي خفيف (نوتات عالية متناثرة) للعصر الذهبي"""
    rng = np.random.RandomState(seed)
    ti = start
    while ti < start+dur:
        f = scale[rng.randint(len(scale))]
        bell(ti, f, amp*(0.6+0.4*rng.rand()), 3.0)
        ti += rate*(0.7+0.6*rng.rand())

def riser(start, dur, f0=60, f1=400, amp=0.30):
    """تصاعد توتري قبل الكارثة"""
    i0 = int(start*SR); n = min(int(dur*SR), N-i0)
    if n <= 0: return
    tt = np.arange(n)/SR
    f = f0*(f1/f0)**(tt/dur)
    phase = 2*np.pi*np.cumsum(f)/SR
    env = (tt/dur)**2
    s = amp*env*np.sin(phase)*(1+0.4*np.sin(2*np.pi*8*tt*tt/dur))
    L[i0:i0+n] += s; R[i0:i0+n] += s

# ============ الفصل 1: غموض وترقب (0 - 36.7) ============
s0, e0 = BOUNDS[0], BOUNDS[1]
pad(D2, s0, e0-s0, 0.55, attack=5, vib=0.08)
pad(A2, s0, e0-s0, 0.30, attack=7, vib=0.11)
pad(D3, s0+8, e0-s0-8, 0.18, attack=6)
pad(F3, s0+18, e0-s0-18, 0.12, attack=6)          # لمسة مينور حزينة
for i, ti in enumerate(np.arange(s0+4, e0-4, 3.4)):  # نبض قلب خافت
    drum(ti, 48, 0.16, 0.8); drum(ti+0.42, 46, 0.10, 0.6)
bell(s0+2.5, A3, 0.22, 7); bell(s0+20, D4, 0.16, 7)

# ============ الفصل 2: دفء البناء (36.7 - 77.0) ============
s1, e1 = BOUNDS[1], BOUNDS[2]
prog2 = [(D2,F3,A3),(Bb2,D3,F3),(F2,A3,C4),(C3,E3,G3)]  # Dm Bb F C
seg = (e1-s1)/len(prog2)
for j,(a,b,c) in enumerate(prog2):
    st = s1+j*seg
    pad(a, st, seg+3, 0.45, attack=2.5); pad(b, st, seg+3, 0.22, attack=3); pad(c, st, seg+3, 0.15, attack=3.5)
for ti in np.arange(s1+2, e1-2, 1.7):               # نبض بناء منتظم
    drum(ti, 60, 0.13, 0.5)

# ============ الفصل 3: إشراق العصر الذهبي (77.0 - 115.6) ============
s2, e2 = BOUNDS[2], BOUNDS[3]
prog3 = [(F2,C4,F4),(C3,G3,E4),(D3,A3,F4),(Bb2,F3,D4)]  # F C Dm Bb
seg = (e2-s2)/len(prog3)
for j,(a,b,c) in enumerate(prog3):
    st = s2+j*seg
    pad(a, st, seg+3, 0.42, attack=2.5); pad(b, st, seg+3, 0.20); pad(c, st, seg+3, 0.13)
shimmer(s2+3, e2-s2-6, [D4,F4,G4,A4,D5,C4], amp=0.10, seed=11)

# ============ الفصل 4: طبول الحرب (115.6 - 156.6) ============
s3, e3 = BOUNDS[3], BOUNDS[4]
pad(D2, s3, e3-s3, 0.50, attack=1.5, vib=0.3)
pad(E3*0.5, s3+4, e3-s3-4, 0.28, attack=2)          # نغمة متنافرة (نصف تون فوق ري)
pad(Bb2, s3+10, e3-s3-12, 0.22)
ti = s3+1.0; gap = 2.0
while ti < e3-6:                                      # طبول تتسارع
    drum(ti, 62, 0.55, 1.2); drum(ti+gap*0.5, 50, 0.30, 0.9)
    prog = (ti-s3)/(e3-s3); gap = 2.0-1.1*prog
    ti += gap
riser(e3-9, 8, 55, 500, 0.30)                         # تصاعد نحو ذروة السقوط
drum(e3-0.9, 70, 0.85, 2.0)                           # الضربة الكبرى

# ============ الفصل 5: رثاء تحت الرماد (156.6 - 188.6) ============
s4, e4 = BOUNDS[4], BOUNDS[5]
pad(D2, s4, e4-s4, 0.40, attack=4, vib=0.06)
pad(F3, s4+3, e4-s4-3, 0.16, attack=5)
pad(E3, s4+10, 10, 0.10, attack=4)                    # add9 حزينة
for j, ti in enumerate(np.arange(s4+2, e4-5, 6.5)):   # أجراس رثاء بعيدة
    bell(ti, A3 if j%2==0 else D4, 0.30, 8)

# ============ الفصل 6: أمل ونهوض (188.6 - 239.3) ============
s5, e5 = BOUNDS[5], BOUNDS[6]
prog6 = [(D3,Fs4*0.5,A3),(G2,D3,G3),(Bb2,D3,F3),(A2,E3,A3),(D3,Fs4*0.5,A3)]  # ري ماجور مشرقة
seg = (e5-s5-6)/len(prog6)
for j,(a,b,c) in enumerate(prog6):
    st = s5+j*seg
    amp = 0.40+0.06*j                                  # تصاعد تدريجي للأمل
    pad(a, st, seg+4, amp, attack=2.5); pad(b, st, seg+4, amp*0.5); pad(c, st, seg+4, amp*0.35)
shimmer(s5+8, e5-s5-14, [D4,Fs4,A4,D5,E4], amp=0.11, seed=23, rate=0.8)
for ti in np.arange(s5+4, e5-8, 2.1):
    drum(ti, 58, 0.12, 0.6)                            # نبض حياة هادئ
pad(D2, e5-8, 8, 0.5, attack=3, release=5)             # الوتر الختامي
bell(e5-7, D4, 0.35, 7); bell(e5-5, A4, 0.2, 6)

# ============ الإخراج ============
mix = np.stack([L, R], axis=1)
# فيد عام + تطبيع
fade_in = np.minimum(1, t/6); fade_out = np.minimum(1, (TOTAL-t)/8)
mix *= (fade_in*fade_out)[:, None]
mix /= np.abs(mix).max() * 1.15
# ضغط لطيف (soft clip)
mix = np.tanh(mix*1.4)/np.tanh(1.4)
data = (mix*32767*0.9).astype(np.int16)
out = os.path.join(BASE, "audio", "score.wav")
with wave.open(out, "w") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(data.tobytes())
print("score written:", out, f"{TOTAL:.1f}s")
