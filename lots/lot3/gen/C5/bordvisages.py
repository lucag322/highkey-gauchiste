# Règle Luca (26/10) : aucun visage visible de plus de 5 % de la hauteur ne touche le bord du cadre.
# Usage : python bordvisages.py export.mp4 [i/s=10] -> plages de temps fautives + taille du visage.
import sys, os, json, subprocess, shutil
FF = "/opt/homebrew/bin/ffmpeg"; FACES = "/Users/luca.grousset/Movies/highkey-gauchiste/_claude/outils/faces"
src = sys.argv[1]; fps = float(sys.argv[2]) if len(sys.argv) > 2 else 10
d = os.path.dirname(os.path.abspath(__file__)) + "/_bord"; shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
subprocess.run([FF, "-v", "error", "-i", src, "-vf", "fps=%g" % fps, "-q:v", "3", d + "/f%04d.jpg"], check=True)
subprocess.run([FACES, d], check=True, capture_output=True)
js = json.load(open(d + "/faces.json")); bad = []; n = 0
for k in sorted(js):
    t = (int(k[1:5]) - 1) / fps
    for x, y, w, h in js[k]:
        if h < 0.05: continue
        n += 1
        top, bot, l, r = y - 0.4 * h, y + h * 1.08, x - 0.12 * w, x + w * 1.12
        if top < 0 or bot > 1 or l < 0 or r > 1:
            bad.append((t, h, top, bot, l, r))
print("images", len(js), "| visages >5 %%: %d | au bord : %d" % (n, len(bad)))
for t, h, top, bot, l, r in bad: print("%.1fs h=%.2f (haut %.2f bas %.2f g %.2f d %.2f)" % (t, h, top, bot, l, r))
shutil.rmtree(d, ignore_errors=True)
