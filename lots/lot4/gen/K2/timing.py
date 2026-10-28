# K2 : frappes réelles de La grenade + placement de la voix (un seul bloc, pauses d'origine) pour que chaque coupe tombe
# sur une frappe juste avant le premier mot du fragment, et que « beaucoup » finisse juste avant le drop « Prends garde ».
import json, numpy as np, librosa
HK = "/Users/luca.grousset/Movies/highkey-gauchiste"; D = HK + "/lot4/_claude/gen/K2/"
MUS = HK + "/lot4/sons/K2-la-grenade_complet.wav"
SR = 48000; OFF = 24.0; HOP = 48
y, _ = librosa.load(MUS, sr=SR, mono=True, offset=OFF, duration=28)
env = librosa.onset.onset_strength(y=y, sr=SR, hop_length=HOP, n_mels=64)
tt = np.arange(len(env)) * HOP / SR + OFF
# grille : régression sur les temps de beat_track (130,4 BPM), puis frappe réelle = max d'attaque à ±40 ms
e2 = librosa.onset.onset_strength(y=y, sr=SR, hop_length=480)
_, bt = librosa.beat.beat_track(onset_envelope=e2, sr=SR, hop_length=480)
bt = bt * 480 / SR + OFF
k = np.arange(len(bt)); P, PH0 = np.polyfit(k, bt, 1)[0], np.polyfit(k, bt, 1)[1]
HITS = []
for j in range(-2, 80):
    b = PH0 + j * P
    if b < OFF + 0.1 or b > OFF + 27.8: continue
    i0, i1 = int((b - .04 - OFF) * SR / HOP), int((b + .04 - OFF) * SR / HOP)
    HITS.append(float(tt[i0 + int(np.argmax(env[i0:i1]))]))
DROP_C = min(HITS, key=lambda h: abs(h - 41.91))     # « Prends garde » (Whisper : Prends 41,88)
END_C = min(HITS, key=lambda h: abs(h - 47.45))      # frappe après « grenade » (46,06-47,00)
# voix : extrait K2-coquerel-hemicycle-plf-texte.mp4 (= URL v6HH2QrtogU + 470 s)
SEG = (35.88, 43.40)
FRAG = [("L’essence du texte", 35.88), ("n’a pas changé", 37.22), ("Il demandait", 38.14), ("toujours trop", 38.64),
        ("à ceux qui ont peu", 39.48), ("et toujours trop peu", 40.84), ("à ceux qui ont beaucoup", 42.16)]
CUT_FROM = 2
best = None
for M0 in [h - 0.02 for h in HITS if 31.6 < h < 33.3]:
    if END_C - M0 > 19.9: continue
    for sh in np.arange(0.8, 3.0, 0.005):                  # temps timeline du début de la voix (35,88)
        tl = lambda w: w - SEG[0] + sh
        hs = [h - M0 for h in HITS]; c = 0
        for txt, w in FRAG[CUT_FROM:]:
            x = tl(w) - min(hs, key=lambda h: abs(tl(w) - 0.06 - h))
            c += 0 if 0.0 <= x <= 0.13 else min(abs(x), abs(x - 0.13)) ** 2 * 100
        gap = (DROP_C - M0) - tl(SEG[1])
        if not (0.10 <= gap <= 0.35): continue
        c += 0.3 * abs(sh - 1.9)
        if best is None or c < best[0]: best = (c, M0, sh)
c, M0, sh = best
print("coût %.4f  M0 %.3f  voix à %.3f s  drop %.3f  fin %.3f" % (c, M0, sh, DROP_C - M0, END_C - M0))
for txt, w in FRAG:
    t = w - SEG[0] + sh; h = min([h - M0 for h in HITS], key=lambda h: abs(t - 0.06 - h))
    print("%-26s mot %.3f  frappe %.3f  avance %+.0f ms" % (txt, t, h, (t - h) * 1000))
json.dump({"M0": M0, "voice_tl": sh, "seg": SEG, "frag": FRAG, "cut_from": CUT_FROM, "drop_c": DROP_C, "end_c": END_C, "hits_complet": HITS, "period": P},
          open(D + "timing.json", "w"), indent=1, ensure_ascii=False)
print("période %.4f s (%.1f BPM)" % (P, 60 / P)); print("frappes tl:", " ".join("%.3f" % (h - M0) for h in HITS if -0.5 < h - M0 < 16))
