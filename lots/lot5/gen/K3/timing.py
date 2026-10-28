# K3 : frappes réelles de HUMBLE. (Kendrick Lamar) + placement de la voix de Guetté (un bloc, pauses d'origine) pour que chaque coupe
# tombe sur une frappe juste avant le premier mot du fragment, et que « change » finisse juste avant le drop « Bitch, be humble ».
import json, numpy as np, librosa
HK = "/Users/luca.grousset/Movies/highkey-gauchiste"; D = HK + "/lot5/_claude/gen/K3/"
MUS = HK + "/lot5/sons/K3-kendrick-humble_complet.wav"
SR = 48000; OFF = 40.0; HOP = 48
y, _ = librosa.load(MUS, sr=SR, mono=True, offset=OFF, duration=40)
env = librosa.onset.onset_strength(y=y, sr=SR, hop_length=HOP, n_mels=64)
tt = np.arange(len(env)) * HOP / SR + OFF
# grille : régression sur beat_track (150 BPM), frappe réelle = max d'attaque à ±40 ms de la grille
e2 = librosa.onset.onset_strength(y=y, sr=SR, hop_length=480)
_, bt = librosa.beat.beat_track(onset_envelope=e2, sr=SR, hop_length=480)
bt = bt * 480 / SR + OFF
k = np.arange(len(bt)); P, PH0 = np.polyfit(k, bt, 1)
HITS = []
for j in range(-2, 120):
    b = PH0 + j * P
    if b < OFF + 0.1 or b > OFF + 39.8: continue
    i0, i1 = int((b - .04 - OFF) * SR / HOP), int((b + .04 - OFF) * SR / HOP)
    HITS.append(float(tt[i0 + int(np.argmax(env[i0:i1]))]))
BREAK = (52.6, 55.85)                                  # pause du beat (« My left stroke just went viral ») : pas de coupe ici
DROP_C = min(HITS, key=lambda h: abs(h - 64.35))       # « Bitch, be humble » (voix mesurée : Bitch 64,35, be 64,73, hum 65,13, sit 65,93, down 66,33)
# voix : extrait K3-guette-bezons-riches.mp4 (= URL 9Cgr6La_XaE + 232 s), Whisper mot à mot
SEG = (9.88, 22.82)
FRAG = [("Ce sont les riches", 9.88), ("qui dessinent la ville", 10.92), ("ce sont les pauvres", 12.68), ("qui construisent la ville", 13.56),
        ("ce sont les riches", 15.26), ("qui privatisent les réseaux", 15.92), ("et ce sont les pauvres", 17.56), ("qui subissent les pollutions", 18.70),
        ("de ces réseaux", 20.26), ("Et il est temps que ça change", 21.18)]
CUT_FROM = 4
best = None
for M0 in [h - 0.02 for h in HITS if 48.5 < h < 51.5]:
    ends = [h for h in HITS if h > 69.8 and h - M0 <= 19.95]   # fin sur la frappe après le 2e « sit down » (down 69,53, silence 69,6-69,85)
    if not ends: continue
    for sh in np.arange(0.6, 2.5, 0.005):              # temps timeline du début de la voix (SEG[0])
        tl = lambda w: w - SEG[0] + sh
        hs = [h - M0 for h in HITS if not (BREAK[0] < h < BREAK[1])]; c = 0
        for txt, w in FRAG[CUT_FROM:]:
            x = tl(w) - min(hs, key=lambda h: abs(tl(w) - 0.06 - h))
            c += 0 if 0.0 <= x <= 0.13 else min(abs(x), abs(x - 0.13)) ** 2 * 100
        gap = (DROP_C - M0) - tl(SEG[1])
        if not (0.08 <= gap <= 0.40): continue
        c += 0.3 * abs(sh - 0.8)
        if best is None or c < best[0]: best = (c, M0, sh, max(ends))
c, M0, sh, END_C = best
print("coût %.4f  M0 %.3f  voix à %.3f s  drop %.3f  fin %.3f" % (c, M0, sh, DROP_C - M0, END_C - M0))
for txt, w in FRAG:
    t = w - SEG[0] + sh; h = min([h - M0 for h in HITS], key=lambda h: abs(t - 0.06 - h))
    print("%-30s mot %.3f  frappe %.3f  avance %+.0f ms" % (txt, t, h, (t - h) * 1000))
json.dump({"M0": M0, "voice_tl": sh, "seg": SEG, "frag": FRAG, "cut_from": CUT_FROM, "drop_c": DROP_C, "end_c": END_C, "hits_complet": HITS, "period": P, "break": BREAK},
          open(D + "timing.json", "w"), indent=1, ensure_ascii=False)
print("période %.4f s (%.1f BPM)" % (P, 60 / P)); print("frappes tl:", " ".join("%.3f" % (h - M0) for h in HITS if -0.5 < h - M0 < 21))
