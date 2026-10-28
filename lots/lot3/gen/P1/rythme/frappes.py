# Frappes réelles de MONTAGEM TOMADA telles que posées dans P1 (temps timeline = temps morceau - MOFF).
# Attaque = instant où l'enveloppe (Hilbert, pas 1 ms) atteint 20 % de la montée vers le pic, bande 1,5-5 kHz (caisse claire / clap)
# et 30-120 Hz (808). Drop = entrée de la basse 808 après le break (morceau 44,33 s). Sortie : rythme/frappes.json
import json, numpy as np, librosa, scipy.signal as ss
LOT = "/Users/luca.grousset/Movies/highkey-gauchiste/lot3"; R = LOT + "/_claude/gen/P1/rythme/"
MOFF = 36.232; DUR = 15.0
y, sr = librosa.load(LOT + "/sons/P1-mxzi-montagem-tomada_complet.wav", sr=48000, mono=True, offset=MOFF, duration=DUR)
def env(lo, hi):
    x = ss.sosfiltfilt(ss.butter(4, [lo, hi], "bandpass", fs=sr, output="sos"), y)
    e = np.abs(ss.hilbert(x)); w = int(.004 * sr); return np.convolve(e, np.ones(w) / w, "same")[::48]
mid, sub = env(1500, 5000), env(30, 120)
def att(e, t, win=0.10):
    a, b = int((t - win) * 1000), int((t + win) * 1000); p = a + int(np.argmax(e[a:b]))
    pre = e[max(p - 80, 0):max(p - 30, 1)].mean(); i = p
    while i > p - 100 and e[i] > pre + 0.2 * (e[p] - pre): i -= 1
    return round(i / 1000, 3)
# frappes fortes du passage (grille 130 BPM = 0,4615 s, repérées à l'enveloppe) : drop puis caisses claires à +4 et +8 temps
coupes = [att(mid, 44.33 - MOFF), att(mid, 46.17 - MOFF), att(mid, 48.02 - MOFF)]
grille = [att(mid, 44.33 - MOFF + k * 0.4615) for k in range(0, 15)]
json.dump({"MOFF": MOFF, "coupes_tl": coupes, "drop_808_sub_tl": att(sub, 44.34 - MOFF), "temps_tl": grille, "bpm": 130,
           "note": "temps timeline P1 ; coupes = drop + 2 caisses claires fortes"}, open(R + "frappes.json", "w"), indent=1)
print(coupes, grille)
