# Frappes réelles de Chief Keef ft. Lil Reese - I Don't Like (fichier complet lot5/sons). Attaque = instant où l'enveloppe (Hilbert, pas 1 ms)
# atteint 20 % de la montée vers le pic. Bandes : sub 30-120 Hz (808), mid 1,5-5 kHz (clap/snare/hats), low 120-400 Hz (kick).
# Sortie : frappes_morceau.json (temps MORCEAU), converti en temps timeline par genP3.py (t - MOFF). (Méthode reprise de lot4 P2.)
import json, numpy as np, librosa, scipy.signal as ss
F = "/Users/luca.grousset/Movies/highkey-gauchiste/lot5/sons/P3-chief-keef-i-dont-like_complet.wav"
R = "/Users/luca.grousset/Movies/highkey-gauchiste/lot5/_claude/gen/P3/rythme/"
A, B = 20.0, 60.0
y, sr = librosa.load(F, sr=48000, mono=True, offset=A, duration=B - A)
def env(lo, hi):
    x = ss.sosfiltfilt(ss.butter(4, [lo, hi], "bandpass", fs=sr, output="sos"), y)
    e = np.abs(ss.hilbert(x)); w = int(.004 * sr); return np.convolve(e, np.ones(w) / w, "same")[::48]
def attacks(e, rel=0.25):
    d = np.diff(e, prepend=e[0]); d[d < 0] = 0
    pk, _ = ss.find_peaks(d, height=d.max() * rel, distance=120)
    out = []
    for q in pk:
        p = q + int(np.argmax(e[q:q + 40])); pre = e[max(p - 80, 0):max(p - 30, 1)].mean(); i = p
        while i > p - 100 and e[i] > pre + 0.2 * (e[p] - pre): i -= 1
        out.append(round(A + i / 1000, 3))
    return sorted(set(out))
res = {k: attacks(env(*b)) for k, b in {"sub": (30, 120), "mid": (1500, 5000), "low": (120, 400)}.items()}
json.dump(res, open(R + "frappes_morceau.json", "w"), indent=0)
for k, v in res.items(): print(k, v)
