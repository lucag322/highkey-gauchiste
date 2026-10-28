# Survol des attaques du morceau (Kordhell - Murder In My Mind) entre deux temps : sub (30-120 Hz) et caisse/clap (1,5-5 kHz)
import sys, numpy as np, librosa, scipy.signal as ss
F = "/Users/luca.grousset/Movies/highkey-gauchiste/lot4/sons/P2-kordhell-murder-in-my-mind_complet.wav"
a, b = float(sys.argv[1]), float(sys.argv[2])
y, sr = librosa.load(F, sr=48000, mono=True, offset=a, duration=b - a)
def env(lo, hi):
    x = ss.sosfiltfilt(ss.butter(4, [lo, hi], "bandpass", fs=sr, output="sos"), y)
    e = np.abs(ss.hilbert(x)); w = int(.004 * sr); return np.convolve(e, np.ones(w) / w, "same")[::48]
for name, (lo, hi) in {"sub": (30, 120), "mid": (1500, 5000), "cow": (500, 1200)}.items():
    e = env(lo, hi); d = np.diff(e, prepend=e[0]); d[d < 0] = 0
    pk, pr = ss.find_peaks(d, height=d.max() * 0.25, distance=150)
    print(name, " ".join("%.3f" % (a + p / 1000) for p in pk))
oe = librosa.onset.onset_strength(y=y, sr=sr); t, bt = librosa.beat.beat_track(onset_envelope=oe, sr=sr)
print("tempo", t)
