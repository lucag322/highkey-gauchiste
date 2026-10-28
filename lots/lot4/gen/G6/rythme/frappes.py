# Frappes réelles d'Experience (Ludovico Einaudi) dans le morceau complet (temps morceau).
# Pas de batterie : frappes = attaques de notes. Basse (30-200 Hz, enveloppe de Hilbert lissée 4 ms, pas 1 ms) = notes de basse
# des cordes/piano (temps forts) ; « large » (200-4000 Hz) = attaques du piano. Instant d'attaque = montée à 20 % du pic.
import json, sys, numpy as np, librosa, scipy.signal as ss
L4 = "/Users/luca.grousset/Movies/highkey-gauchiste/lot4"; D = L4 + "/_claude/gen/G6/rythme/"
SRC = L4 + "/sons/G6-einaudi-experience_complet.wav"
T0, DUR = 95.0, 40.0
y, sr = librosa.load(SRC, sr=48000, mono=True, offset=T0, duration=DUR)
def env(lo, hi):
    x = ss.sosfiltfilt(ss.butter(4, [lo, hi], "bandpass", fs=sr, output="sos"), y)
    e = np.abs(ss.hilbert(x)); w = int(.004 * sr)
    return np.convolve(e, np.ones(w) / w, "same")[::48]
def attacks(e, rel=1.6, prom=0.25, dist=90):
    pk, pr = ss.find_peaks(e, distance=dist, prominence=np.percentile(e, 99) * prom)
    out = []
    for p in pk:
        pre = e[max(p - 60, 0):max(p - 25, 1)].min()
        if e[p] < rel * pre: continue
        i = p
        while i > p - 80 and e[i] > pre + 0.2 * (e[p] - pre): i -= 1
        out.append((round(T0 + i / 1000, 3), round(float(e[p] / np.percentile(e, 99)), 2)))
    return out
B = attacks(env(30, 200)); P = attacks(env(200, 4000), rel=1.3, prom=0.12, dist=60)
json.dump({"basse": B, "piano": P}, open(D + "attaques.json", "w"), indent=0)
print("basse", B); print("piano", len(P))
