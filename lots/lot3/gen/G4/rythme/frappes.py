# Frappes réelles de Dark Beach (Pastel Ghost) dans le morceau complet (temps morceau) + temps timeline G4 (= morceau - MOFF).
# Kick : attaque dans la bande 30-120 Hz (enveloppe de Hilbert lissée 4 ms, pas 1 ms) = instant où la montée atteint 20 % du pic.
# Snare/clap : même méthode bande 1,5-5 kHz. Entrée pleine (synthés + caisse claire) repérée sur le profil spectral (≈ 14,7 s).
import json, sys, numpy as np, librosa, scipy.signal as ss
L3 = "/Users/luca.grousset/Movies/highkey-gauchiste/lot3"; D = L3 + "/_claude/gen/G4/rythme/"
SRC = L3 + "/sons/G4-pastel-ghost-dark-beach_complet.wav"
MOFF = float(sys.argv[1]) if len(sys.argv) > 1 else 0.0
DUR = 100.0
y, sr = librosa.load(SRC, sr=48000, mono=True, duration=DUR)
def env(lo, hi):
    x = ss.sosfiltfilt(ss.butter(4, [lo, hi], "bandpass", fs=sr, output="sos"), y)
    e = np.abs(ss.hilbert(x)); w = int(.004 * sr)
    return np.convolve(e, np.ones(w) / w, "same")[::48]
def attacks(e, rel=2.0, prom=0.35, dist=200):
    pk, _ = ss.find_peaks(e, distance=dist, prominence=np.percentile(e, 99) * prom)
    out = []
    for p in pk:
        pre = e[max(p - 120, 0):max(p - 60, 1)].mean()
        if e[p] < rel * pre: continue
        i = p
        while i > p - 120 and e[i] > pre + 0.2 * (e[p] - pre): i -= 1
        out.append(round(i / 1000, 3))
    return out
K = attacks(env(30, 120)); S = attacks(env(1500, 5000), rel=1.6, prom=0.3)
res = {"MOFF": MOFF, "kicks_morceau": K, "snares_morceau": S,
       "kicks_timeline": [round(k - MOFF, 3) for k in K if 0 <= k - MOFF <= 16],
       "snares_timeline": [round(k - MOFF, 3) for k in S if 0 <= k - MOFF <= 16]}
json.dump(res, open(D + "frappes.json", "w"), indent=1)
print("kicks", K); print("snares", S)
d = np.diff(K); print("écart médian %.4f s -> %.2f BPM" % (np.median(d), 60 / np.median(d)))
