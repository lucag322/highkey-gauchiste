# Frappes réelles de Bad (Michael Jackson, clip officiel « Shortened Version », chaîne Michael Jackson) dans l'extrait posé
# (temps timeline = temps morceau - MOFF). Le refrain « Because I'm BAD, I'm bad » : 1er temps du refrain = « bad » (≈ 69,86 s du clip),
# posé juste après « dormir » de Guiraud. Temps ≈ 0,534 s (≈ 112,4 BPM, beat_track librosa) ; kick 30-150 Hz, caisse claire 1,5-6 kHz.
# Partie percussive (HPSS), enveloppe de Hilbert lissée 4 ms, pas 1 ms, instant = 20 % de la montée, cherché à ±45 ms de chaque temps.
import json, numpy as np, librosa, scipy.signal as ss
D = "/Users/luca.grousset/Movies/highkey-gauchiste/lot5/_claude/gen/V3/"
SONG = "/Users/luca.grousset/Movies/highkey-gauchiste/lot5/sons/V3-mj-bad_complet.wav"
DROP_SONG = 69.861; GAP = 7.17; BEAT = 60 / 112.347
MOFF0 = round(DROP_SONG - GAP, 3); DUR = 15.5
y, sr = librosa.load(SONG, sr=48000, mono=True, offset=MOFF0, duration=DUR + 0.5)
yp = librosa.effects.percussive(y, margin=2.0)
def env(lo, hi):
    x = ss.sosfiltfilt(ss.butter(4, [lo, hi], "bandpass", fs=sr, output="sos"), yp)
    e = np.abs(ss.hilbert(x)); w = int(.004 * sr); return np.convolve(e, np.ones(w) / w, "same")[::48]
EK, ES = env(30, 150), env(1500, 6000)
def attack(e, g):
    a, b = int((g - 0.045) * 1000), int((g + 0.045) * 1000)
    p = a + int(np.argmax(e[a:b])); pre = e[max(p - 90, 0):max(p - 40, 1)].mean()
    rise = e[p] / max(pre, 1e-9); i = p
    while i > p - 90 and e[i] > pre + 0.2 * (e[p] - pre): i -= 1
    return i / 1000, rise, float(e[p])
k0, _, _ = attack(EK + ES * (EK.max() / ES.max()), GAP)
temps = []; detail = []
for k in range(-14, 17):
    g = k0 + k * BEAT
    if g < 0.1 or g > DUR - 0.05: continue
    tk, rk, ak = attack(EK, g); ts_, rs, as_ = attack(ES, g)
    t, r, kind = (tk, rk, "kick") if rk >= rs else (ts_, rs, "caisse")
    temps.append(round(t, 3)); detail.append({"t": round(t, 3), "type": kind, "montee": round(float(r), 2), "kick_amp": round(ak, 4), "caisse_amp": round(as_, 4), "grille": round(g, 3)})
drop = min(temps, key=lambda t: abs(t - k0))
# MOFF recalé pour que le drop tombe exactement à GAP (temps entiers d'images inutiles : on garde la précision ms)
shift = round(drop - GAP, 3); MOFF = round(MOFF0 + shift, 3)
temps = [round(t - shift, 3) for t in temps]
for d in detail: d["t"] = round(d["t"] - shift, 3); d["grille"] = round(d["grille"] - shift, 3)
js = {"MOFF": MOFF, "drop_t": GAP, "beat_s": round(BEAT, 5), "temps_t": temps, "detail": detail,
      "note": "temps timeline V3 (0 = %.3f s du clip officiel). drop_t = 1er temps du refrain « Because I'm BAD »" % MOFF}
json.dump(js, open(D + "frappes.json", "w"), indent=1)
print("MOFF", MOFF, "drop", GAP)
for d in detail: print(d["t"], d["type"], d["montee"], d["kick_amp"], d["caisse_amp"])
