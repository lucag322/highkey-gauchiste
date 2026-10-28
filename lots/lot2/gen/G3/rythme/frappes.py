# Frappes réelles de TENDU telles que posées dans G3 (temps timeline = temps extrait - MOFF).
# Kicks 808 : attaque dans la bande 30-120 Hz (enveloppe de Hilbert, pas 1 ms) = instant où la montée atteint 20 % du pic qui suit.
# Repérage visuel sur rythme/enveloppes.png puis affinage automatique. Sortie : rythme/frappes.json
import json, numpy as np, librosa, scipy.signal as ss
LOT = "/Users/luca.grousset/Movies/highkey-gauchiste/lot2"; G3 = LOT + "/_claude/gen/G3/rythme/"
MOFF = 6.247 - 5.40; DUR = 15.0
y, sr = librosa.load(LOT + "/sons/G3-josman-tendu.wav", sr=48000, mono=True, offset=MOFF, duration=DUR)
def env(lo, hi):
    x = ss.sosfiltfilt(ss.butter(4, [lo, hi], "bandpass", fs=sr, output="sos"), y)
    e = np.abs(ss.hilbert(x)); w = int(.004 * sr)                              # enveloppe de Hilbert lissée 4 ms (pas d'ondulation à 2f)
    return np.convolve(e, np.ones(w) / w, "same")[::48]                        # 1 valeur / ms
sub = env(30, 120)
# montées nettes du sub : pic local > 2× le niveau 60 ms avant
pk, _ = ss.find_peaks(sub, distance=200, prominence=np.percentile(sub, 99) * 0.35)
kicks = []
for p in pk:
    pre = sub[max(p - 120, 0):max(p - 60, 1)].mean()
    if sub[p] < 2.0 * pre or p < 3000: continue
    i = p
    while i > p - 120 and sub[i] > pre + 0.2 * (sub[p] - pre): i -= 1
    kicks.append(round(i / 1000, 3))
json.dump({"MOFF": round(MOFF, 3), "kicks_808": kicks, "note": "temps timeline G3"}, open(G3 + "frappes.json", "w"), indent=1)
print(kicks)
