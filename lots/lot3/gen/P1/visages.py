# Variante de checkcut : visages touchant un bord, avec leur hauteur (fraction de l'image). Règle : > 5 % de la hauteur = doit être entier.
import sys, os, json, subprocess, shutil
FF = "/opt/homebrew/bin/ffmpeg"; FACES = "/Users/luca.grousset/Movies/highkey-gauchiste/_claude/outils/faces"
src = sys.argv[1]; fps = float(sys.argv[2]) if len(sys.argv) > 2 else 10
d = "/tmp/claude-502/vis_" + os.path.basename(src); shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
subprocess.run([FF, "-v", "error", "-i", src, "-vf", "fps=%g" % fps, "-q:v", "3", d + "/f%04d.jpg"], check=True)
subprocess.run([FACES, d], check=True, capture_output=True)
js = json.load(open(d + "/faces.json")); n = 0
for k in sorted(js):
    t = (int(k[1:5]) - 1) / fps
    for x, y, w, h in js[k]:
        top, bot, l, r = y - 0.4 * h, y + h * 1.08, x - 0.12 * w, x + w * 1.12
        if top < 0 or bot > 1 or l < 0 or r > 1:
            if h * 1.5 > 0.05: n += 1
            print("%.2fs h=%.3f (tête %.3f) %s  x %.2f-%.2f y %.2f-%.2f" % (t, h, h * 1.5, ">5%" if h * 1.5 > 0.05 else "", l, r, top, bot))
print("visages > 5 % coupés :", n)
