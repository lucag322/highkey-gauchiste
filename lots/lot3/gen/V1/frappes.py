# Frappes réelles de Santé (Stromae) dans l'extrait posé (temps timeline = temps morceau - MOFF).
# Le refrain (« Et si on célébrait ceux qui ne célèbrent pas / Pour une fois j'aimerais lever mon verre à ceux qui n'en ont pas »)
# tombe sur le kick 38,875 s du morceau, juste après la phrase d'Aubry. Kicks : attaque 30-120 Hz ; caisse claire 1,5-6 kHz
# (enveloppe de Hilbert lissée 4 ms, pas 1 ms, instant = 20 % de la montée). Coupes = frappe réelle la plus proche de chaque temps.
import json, numpy as np, librosa, scipy.signal as ss
D = "/Users/luca.grousset/Movies/highkey-gauchiste/lot3/_claude/gen/V1/"
SONG = "/Users/luca.grousset/Movies/highkey-gauchiste/lot3/sons/V1-stromae-sante_complet.wav"
REFRAIN = 38.875; GAP = 5.93                                               # le refrain tombe à 5,93 s (0,15 s après « rien »)
MOFF = round(REFRAIN - GAP, 3); DUR = 14.4
y, sr = librosa.load(SONG, sr=48000, mono=True, offset=MOFF, duration=DUR + 0.5)
def env(lo, hi):
    x = ss.sosfiltfilt(ss.butter(4, [lo, hi], "bandpass", fs=sr, output="sos"), y)
    e = np.abs(ss.hilbert(x)); w = int(.004 * sr); return np.convolve(e, np.ones(w) / w, "same")[::48]
def hits(e, ratio=1.6, prom=0.12):
    pk, _ = ss.find_peaks(e, distance=150, prominence=np.percentile(e, 99) * prom); out = []
    for p in pk:
        pre = e[max(p - 120, 0):max(p - 60, 1)].mean()
        if e[p] < ratio * pre: continue
        i = p
        while i > p - 120 and e[i] > pre + 0.2 * (e[p] - pre): i -= 1
        out.append(round(i / 1000, 3))
    return out
sub = hits(env(30, 120)); sn = hits(env(1500, 6000)); allh = sorted(set(sub + sn))
drop = min(sub, key=lambda t: abs(t - GAP))
BEAT = 0.6525; temps = []
for k in range(14):                                                        # temps du refrain : frappe réelle la plus proche (kick d'abord)
    g = drop + k * BEAT
    c = [t for t in sub if abs(t - g) < 0.04] or [t for t in sn if abs(t - g) < 0.04]
    if c: temps.append(min(c, key=lambda t: abs(t - g)))
js = {"MOFF": MOFF, "drop_t": drop, "kicks_drop_t": temps, "cartons_t": [], "kicks_t": sub, "snares_t": sn,
      "note": "temps timeline V1 (0 = %.3f s du clip officiel). drop_t = arrivée du refrain. bpm ≈ 92 (temps 0,652 s)" % MOFF}
json.dump(js, open(D + "frappes.json", "w"), indent=1)
print("MOFF", MOFF, "refrain", drop, "temps", temps)
