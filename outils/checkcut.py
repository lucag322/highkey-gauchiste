# Vérifie un export : visages (Apple Vision) à 10 i/s ; signale toute tête (cheveux/menton inclus) qui touche un bord.
import sys, os, json, subprocess, shutil
FF = "/opt/homebrew/bin/ffmpeg"; FACES = "/Users/luca.grousset/Movies/highkey-gauchiste/_claude/outils/faces"
src = sys.argv[1]; fps = float(sys.argv[2]) if len(sys.argv) > 2 else 10
d = "/tmp/claude-502/chk_" + os.path.basename(src); shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
subprocess.run([FF, "-v", "error", "-i", src, "-vf", "fps=%g" % fps, "-q:v", "3", d + "/f%04d.jpg"], check=True)
subprocess.run([FACES, d], check=True, capture_output=True)
js = json.load(open(d + "/faces.json")); bad = []
for k in sorted(js):
    t = (int(k[1:5]) - 1) / fps
    for x, y, w, h in js[k]:
        if w < 0.06: continue          # petits visages de foule ignorés
        top, bot, l, r = y - 0.4 * h, y + h * 1.08, x - 0.12 * w, x + w * 1.12
        if top < 0 or bot > 1 or l < 0 or r > 1:
            bad.append("%.1fs (haut %.2f bas %.2f g %.2f d %.2f)" % (t, top, bot, l, r))
print("images", len(js), "| têtes coupées :", len(bad)); print("\n".join(bad[:40]))
