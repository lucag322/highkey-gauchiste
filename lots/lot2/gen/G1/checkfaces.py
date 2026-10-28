# Règle Luca (26/10) : aucun visage visible ne touche le bord (personne principale, ou visage secondaire >= 5 % de la hauteur).
# Usage : python checkfaces.py export.mp4 [fps=10]  -> défauts par plan de genG1.SHOTS
import sys, os, json, subprocess, shutil
from collections import defaultdict
FF = "/opt/homebrew/bin/ffmpeg"; FACES = "/Users/luca.grousset/Movies/highkey-gauchiste/_claude/outils/faces"
src = sys.argv[1]; fps = CHK_FPS = float(sys.argv[2]) if len(sys.argv) > 2 else 10   # genG1 écrase « fps »
d = "/tmp/claude-502/chkG1_" + os.path.basename(src); shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
subprocess.run([FF, "-v", "error", "-i", src, "-vf", "fps=%g" % fps, "-q:v", "3", d + "/f%04d.jpg"], check=True)
subprocess.run([FACES, d], check=True, capture_output=True)
js = json.load(open(d + "/faces.json"))
sys.argv = ["genG1"]
exec(open(os.path.dirname(os.path.abspath(__file__)) + "/genG1.py").read().split("if __name__")[0])
bad = defaultdict(list); nf = defaultdict(int); fps = CHK_FPS
for k in sorted(js):
    t = (int(k[1:5]) - 1 + 0.5) / fps                     # milieu de l'échantillon
    sh = [s for s in SHOTS if s["a"] <= t < s["b"]]
    if not sh: continue
    sid = sh[0]["id"]; nf[sid] += 1
    for x, y, w, h in js[k]:
        if h * 1.48 < 0.05: continue                       # tête entière = boîte Vision x 1,48 (cheveux + menton) : >= 5 % de la hauteur
        top, bot, l, r = y - 0.4 * h, y + h * 1.08, x - 0.12 * w, x + w * 1.12
        if top < 0 or bot > 1 or l < 0 or r > 1:
            bad[sid].append("%.1fs h%.2f (%.2f %.2f %.2f %.2f)" % (t, h, top, bot, l, r))
for s in SHOTS:
    b = bad.get(s["id"], [])
    print(s["id"], "%.2f-%.2f" % (s["a"], s["b"]), "images", nf[s["id"]], "| bord :", len(b), ("; ".join(b[:3]) if b else ""))
print("TOTAL défauts :", sum(len(v) for v in bad.values()))
