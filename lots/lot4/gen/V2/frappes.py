# Frappes réelles de Beat It (Michael Jackson, clip officiel 4K) dans l'extrait posé (temps timeline = temps morceau - MOFF).
# Le refrain (« Just beat it, beat it… ») tombe sur la frappe 87,43 s du clip (1er temps du refrain), juste après « appliquée » d'Obono.
# Temps ≈ 0,4335 s (≈ 138 BPM) ; kick sur 1/3 (30-150 Hz), caisse claire sur 2/4 (1,5-6 kHz). Partie percussive (HPSS),
# enveloppe de Hilbert lissée 4 ms, pas 1 ms, instant = 20 % de la montée, cherchée à ±45 ms de chaque temps de la grille.
import json, numpy as np, librosa, scipy.signal as ss
D = "/Users/luca.grousset/Movies/highkey-gauchiste/lot4/_claude/gen/V2/"
SONG = "/Users/luca.grousset/Movies/highkey-gauchiste/lot4/sons/V2-mj-beat-it_complet.wav"
DROP_SONG = 87.43; GAP = 7.25; BEAT = 0.43345
MOFF = round(DROP_SONG - GAP, 3); DUR = 15.0
y, sr = librosa.load(SONG, sr=48000, mono=True, offset=MOFF, duration=DUR + 0.5)
yp = librosa.effects.percussive(y, margin=2.0)
def env(lo, hi):
    x = ss.sosfiltfilt(ss.butter(4, [lo, hi], "bandpass", fs=sr, output="sos"), yp)
    e = np.abs(ss.hilbert(x)); w = int(.004 * sr); return np.convolve(e, np.ones(w) / w, "same")[::48]
EK, ES = env(30, 150), env(1500, 6000)
def attack(e, g):
    a, b = int((g - 0.045) * 1000), int((g + 0.045) * 1000)
    p = a + int(np.argmax(e[a:b])); pre = e[max(p - 90, 0):max(p - 40, 1)].mean()
    rise = e[p] / max(pre, 1e-9)
    i = p
    while i > p - 90 and e[i] > pre + 0.2 * (e[p] - pre): i -= 1
    return i / 1000, rise
# grille recalée sur la frappe du refrain
k0, _ = attack(EK + ES * (EK.max() / ES.max()), GAP)
temps = []; detail = []
for k in range(-16, 18):
    g = k0 + k * BEAT
    if g < 0.1 or g > DUR - 0.05: continue
    tk, rk = attack(EK, g); ts_, rs = attack(ES, g)
    t, r, kind = (tk, rk, "kick") if rk >= rs else (ts_, rs, "caisse")
    temps.append(round(t, 3)); detail.append({"t": round(t, 3), "type": kind, "montee": round(float(r), 2), "grille": round(g, 3)})
drop = min(temps, key=lambda t: abs(t - k0))
js = {"MOFF": MOFF, "drop_t": drop, "beat_s": BEAT, "temps_t": temps, "detail": detail,
      "note": "temps timeline V2 (0 = %.3f s du clip officiel). drop_t = 1er temps du refrain « Just beat it »" % MOFF}
json.dump(js, open(D + "frappes.json", "w"), indent=1)
print("MOFF", MOFF, "drop", drop); print([(d["t"], d["type"][0], d["montee"]) for d in detail if d["t"] >= drop - 0.01])
