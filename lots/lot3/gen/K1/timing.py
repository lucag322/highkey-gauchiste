# K1 : frappes réelles de Smooth Criminal + placement de la voix (segments = phrases) pour que chaque coupe tombe sur une frappe,
# 0 à 130 ms avant le premier mot du fragment. Écrit timing.json (lu par genK1.py).
import json, numpy as np, librosa, itertools
HK = "/Users/luca.grousset/Movies/highkey-gauchiste"; D = HK + "/lot3/_claude/gen/K1/"
MUS = HK + "/lot3/sons/K1-smooth-criminal_complet.wav"
SR = 48000; OFF = 150.0; HOP = 48
y, _ = librosa.load(MUS, sr=SR, mono=True, offset=OFF, duration=34)   # 150-184 s
env = librosa.onset.onset_strength(y=y, sr=SR, hop_length=HOP, n_mels=64)
tt = np.arange(len(env)) * HOP / SR + OFF
P, PH0 = 0.5099, 152.994                   # grille ajustée sur refrain + hook (117,7 BPM)
HITS = []
for k in range(0, 60):
    b = PH0 + k * P
    if b > 180.0: break                    # (180 : frappes jusqu’à 179,495 s pour la fin rallongée)
    i0, i1 = int((b - .04 - OFF) * SR / HOP), int((b + .04 - OFF) * SR / HOP)
    j = i0 + int(np.argmax(env[i0:i1])); HITS.append(float(tt[j]))
DROP_C = 172.366                           # temps du « You've been hit by » (Whisper : you've 172,48 / hit 173,28)
END_C = 176.972                            # retour du groove après « smooth criminal » (frappe forte)
BOOM = DROP_C
# mots LCP (temps vidéo LCP d'origine) ; fragments = premiers mots
SEGS = [  # (début, fin) de chaque phrase
    (94.28, 96.92), (97.10, 98.46), (99.18, 101.64), (102.04, 103.98), (104.24, 105.86), (106.08, 107.66)]
FRAG = [  # (texte, début, segment)
    ("La jeunesse", 94.28, 0), ("vient de prendre conscience", 95.02, 0), ("d’elle-même", 96.42, 0),
    ("Vous avez été", 97.10, 1), ("trop loin", 97.94, 1),
    ("Elle s’est déjà", 99.18, 2), ("trop sacrifiée", 99.98, 2), ("pour reculer", 100.80, 2), ("maintenant", 101.32, 2),
    ("Alors monsieur le ministre", 102.04, 3), ("de l’Éducation nationale", 102.84, 3),
    ("acceptez que vous avez perdu", 104.24, 4),
    ("que les jeunes ont raison", 106.08, 5), ("depuis le début", 106.98, 5)]
CUT_FROM = 5                               # coupes à partir de « Elle s'est déjà » (plan d'ouverture long avant)
GAP = [(0, 0), (-0.30, 0.30), (-0.20, 0.30), (-0.10, 0.30), (-0.08, 0.30)]   # A->B figé (plan synchro), autres pauses ajustables
def cost_seg(si, shift, M0):
    c = 0; cuts = []
    for k, (txt, w, s) in enumerate(FRAG):
        if s != si or k < CUT_FROM: continue
        wt = w - 94.28 + shift                     # temps timeline du mot
        hs = [h - M0 for h in HITS]
        h = min(hs, key=lambda h: abs((wt - 0.06) - h))
        x = wt - h                                  # >0 : coupe avant le mot
        c += 0 if 0.0 <= x <= 0.13 else min(abs(x), abs(x - 0.13)) ** 2 * 100
        cuts.append(h)
    return c, cuts
best = None
for M0 in [h - 0.02 for h in HITS if 156.5 < h < 158.6]:
    if END_C - M0 > 19.95: continue
    for O in np.arange(0.45, 1.90, 0.01):
        sh = [O, O]                                  # segments 0 et 1
        tot = 0; ok = True; shifts = [O, O]
        # segments 2..5 : meilleur décalage indépendant dans la plage de pause (glouton, contraintes successives)
        prev = O
        for si in range(2, 6):
            lo, hi = GAP[si - 1]
            opts = [prev + d for d in np.arange(lo, hi + 1e-9, 0.01)]
            c, s = min((cost_seg(si, o, M0)[0] + 0.5 * abs(o - prev), o) for o in opts)
            tot += c; shifts.append(s); prev = s
        vend = 107.66 - 94.28 + shifts[-1]; gap = (DROP_C - M0) - vend
        if not (0.12 <= gap <= 0.5): continue
        tot += 0.3 * abs(O - 1.0)
        if best is None or tot < best[0]: best = (tot, M0, shifts)
tot, M0, shifts = best
print("coût %.3f  M0 %.3f  décalages %s" % (tot, M0, ["%.2f" % s for s in shifts]))
cuts = []
for k, (txt, w, s) in enumerate(FRAG):
    wt = w - 94.28 + shifts[s]
    line = "%-30s mot %.3f" % (txt, wt)
    if k >= CUT_FROM:
        h = min([h - M0 for h in HITS], key=lambda h: abs((wt - 0.06) - h)); cuts.append(h)
        line += "  coupe %.3f (avance %+.0f ms) image %d (quantif %+.0f ms)" % (h, (wt - h) * 1000, round(h * 30), (round(h * 30) / 30 - h) * 1000)
    print(line)
json.dump({"drop_c": DROP_C, "end_c": END_C, "M0": M0, "shifts": shifts, "hits_complet": HITS, "boom": BOOM, "segs": SEGS, "frag": FRAG, "cut_from": CUT_FROM, "period": P},
          open(D + "timing.json", "w"), indent=1, ensure_ascii=False)
print("frappes (timeline):", " ".join("%.3f" % (h - M0) for h in HITS))
