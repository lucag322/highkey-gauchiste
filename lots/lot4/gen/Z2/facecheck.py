# Règle Luca : aucun visage (principal, ou secondaire >= 5 % de la hauteur) ne touche le bord. faces (Apple Vision) à 10 i/s sur l'aperçu.
import sys, os, json, subprocess, shutil
FF = "/opt/homebrew/bin/ffmpeg"; FACES = "/Users/luca.grousset/Movies/highkey-gauchiste/_claude/outils/faces"
src = sys.argv[1]; plan = json.load(open(sys.argv[2]))
d = os.path.dirname(os.path.abspath(__file__)) + "/cache/chk"; shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
subprocess.run([FF, "-v", "error", "-i", src, "-vf", "fps=10", "-q:v", "3", d + "/f%04d.jpg"], check=True)
subprocess.run([FACES, d], check=True, capture_output=True)
js = json.load(open(d + "/faces.json")); bad = []
def shot(t):
    for v in plan["video"]:
        if v["rec"] / 30 <= t < (v["rec"] + v["dur"]) / 30: return v["id"]
for k in sorted(js):
    t = (int(k[1:5]) - 1) / 10
    for x, y, w, h in js[k]:
        if h < 0.05: continue                                # visage < 5 % de la hauteur : foule lointaine, ignoré
        top, bot, l, r = y - 0.4 * h, y + h * 1.08, x - 0.12 * w, x + w * 1.12
        if top < 0 or bot > 1 or l < 0 or r > 1:
            bad.append("%.1fs %s (h %.3f, haut %.2f bas %.2f g %.2f d %.2f)" % (t, shot(t), h, top, bot, l, r))
shutil.rmtree(d)
print("images", len(js), "| visages >= 5 %% au bord : %d" % len(bad)); print("\n".join(bad[:60]))
