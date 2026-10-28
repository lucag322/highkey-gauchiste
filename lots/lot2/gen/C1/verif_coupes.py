# Vérifie sur l'export : coupes détectées dans l'image (différence entre images) vs attaques mesurées dans le son de l'export.
import sys, json, subprocess, numpy as np
sys.path.insert(0, "/Users/luca.grousset/Movies/highkey-gauchiste/lot2/_claude/gen/C1")
from temps_forts import mesure
FF = "/opt/homebrew/bin/ffmpeg"
p = sys.argv[1]; plan = json.load(open(sys.argv[2])); stem = sys.argv[3] if len(sys.argv) > 3 else None
raw = subprocess.run([FF, "-v", "error", "-i", p, "-vf", "scale=135:240,format=gray", "-f", "rawvideo", "-"], capture_output=True, check=True).stdout
F = np.frombuffer(raw, np.uint8).reshape(-1, 240, 135).astype(np.float32)
d = np.abs(np.diff(F, axis=0)).mean((1, 2))                    # d[i] = changement entre image i et i+1 -> coupe au temps (i+1)/30
prevu = [v["rec"] for v in plan["video"] if v["rec"] > 0]
coupes = []
for r in prevu:
    w = range(max(r - 3, 1), min(r + 3, len(d)))
    i = max(w, key=lambda k: d[k - 1]); coupes.append(i / 30)
print("coupes image (s) :", " ".join("%.3f" % c for c in coupes), "| prévues :", " ".join("%.3f" % (r / 30) for r in prevu))
ids = [v["id"] for v in plan["video"] if v["rec"] > 0]
for src, nom in [(p, "export"), (stem, "musique posée")]:
    if not src: continue
    res = mesure(src, coupes); e = [abs(a - c) * 1000 for c, a, s in res]
    print("--", nom)
    for (c, a, s), i in zip(res, ids): print("  %-4s coupe %.3f  attaque %.3f  écart %+5.1f ms  (score %.1f)" % (i, c, a, (a - c) * 1000, s))
    print("  écart max %.1f ms, moyen %.1f ms" % (max(e), sum(e) / len(e)))
