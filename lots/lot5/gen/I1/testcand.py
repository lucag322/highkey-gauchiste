# Teste des plans candidats : recadrage fixe 9:16, 5 images sur 0,55 s, visages au bord (règle >= 5 % de hauteur) + bande de vignettes.
# Usage : python testcand.py  (liste CANDS ci-dessous)
import sys, os, json, subprocess, shutil, numpy as np, cv2
sys.path.insert(0, "/Users/luca.grousset/Movies/highkey-gauchiste/_claude/outils"); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fx import crop_view
D = os.path.dirname(os.path.abspath(__file__)) + "/"
FF = "/opt/homebrew/bin/ffmpeg"; FACES = "/Users/luca.grousset/Movies/highkey-gauchiste/_claude/outils/faces"
HK = "/Users/luca.grousset/Movies/highkey-gauchiste"
SRC = {"SD": "lot1/sources/5-melenchon-saintdenis-smic.mp4", "IS": "lot3/sources/C4-melenchon-intersyndicale.mp4"}
for i in range(1, 9): SRC["SD%d" % i] = "lot3/sources/C4-melenchon-stdenis-0%d.mp4" % i
CANDS = [l.split() for l in open(sys.argv[1]).read().strip().splitlines()]   # id src t cx cy y0 y1 [zoom]
out = D + "cache/cand"; shutil.rmtree(out, ignore_errors=True); os.makedirs(out)
strips = []
for c in CANDS:
    cid, src, t, cx, cy, y0, y1 = c[:7]; z = float(c[7]) if len(c) > 7 else 1.0
    t, cx, cy, y0, y1 = float(t), float(cx), float(cy), float(y0), float(y1)
    vh = (y1 - y0) / z; vw = vh * 9 / 16; cx = min(max(cx, vw / 2), 1570 - vw / 2); cy = min(max(cy, y0 + vh / 2), y1 - vh / 2)
    row = []
    for k in range(5):
        fr = np.frombuffer(subprocess.run([FF, "-v", "error", "-ss", "%.3f" % (t + k * 0.13), "-i", HK + "/" + SRC[src], "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True).stdout, np.uint8).reshape(1080, 1920, 3)
        img = crop_view(fr.astype(np.float32) / 255, cx, cy, vw, 540, 960)
        im8 = (np.clip(img, 0, 1) * 255).astype(np.uint8); cv2.imwrite(out + "/%s_%d.jpg" % (cid, k), im8); row.append(cv2.resize(im8, (135, 240)))
    strip = np.hstack(row); cv2.putText(strip, cid, (4, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2); strips.append(strip)
subprocess.run([FACES, out], check=True, capture_output=True)
js = json.load(open(out + "/faces.json"))
subprocess.run([HK + "/_claude/outils/texts", out], check=True, capture_output=True); tx = json.load(open(out + "/texts.json"))
sys.path.insert(0, HK + "/_claude/outils"); from zones_tiktok import hors_zone
for c in CANDS:
    n = 0; worst = ""
    for k in range(5):
        for x, y, w, h in js.get("%s_%d.jpg" % (c[0], k), []):
            if h * 1.48 < 0.05: continue
            top, bot, l, r = y - 0.4 * h, y + h * 1.08, x - 0.12 * w, x + w * 1.12
            if top < 0 or bot > 1 or l < 0 or r > 1: n += 1; worst = "h%.2f (%.2f %.2f %.2f %.2f)" % (h, top, bot, l, r)
    tt = [b[4] for k in range(5) for b in tx.get("%s_%d.jpg" % (c[0], k), []) if hors_zone(*b[:4])]
    print(c[0], "bord:", n, worst, "| textes hors zone:", tt)
rows = [np.hstack(strips[i:i + 2] + [np.zeros_like(strips[0])] * (2 - len(strips[i:i + 2]))) for i in range(0, len(strips), 2)]
cv2.imwrite(D + "sheets/cand.jpg", np.vstack(rows))
