# Glow des yeux rendu directement dans l'espace 1080x1920 final (fond noir, posé en V2 en mode Écran)
import json, numpy as np, cv2, os, sys
sys.path.insert(0, "/Users/luca.grousset/Movies/highkey-gauchiste/_claude/outils")
from fx import encode
D = os.path.dirname(os.path.abspath(__file__)); os.chdir(D)
eyes = json.load(open("eyeframes/eyes.json")); F_EYE0 = 5950
IN = 5563; E0, E1 = 5841, 6027; G0 = round(239.55 * 25)
prev = (782, 373); track = {}
for i in range(78):
    faces = eyes.get("f%04d.png" % i, [])
    if not faces: continue
    best = min(faces, key=lambda f: (((f[0] + f[2]) / 2 - prev[0]) ** 2 + ((f[1] + f[3]) / 2 - prev[1]) ** 2))
    c = ((best[0] + best[2]) / 2, (best[1] + best[3]) / 2)
    if (c[0] - prev[0]) ** 2 + (c[1] - prev[1]) ** 2 < 120 ** 2: track[F_EYE0 + i] = best; prev = c
PIV = (782, 373); CROP_X0 = 312; SC = 1080 / 1240; TOP = 1920 * (1 - 0.505) - 1080 * SC / 2
def to_out(x, y, sf):
    s = 1.0 + 0.12 * (sf - IN - (E0 - IN)) / ((E1 - IN - 1) - (E0 - IN))
    x = PIV[0] + (x - PIV[0]) * s; y = PIV[1] + (y - PIV[1]) * s
    return (x - CROP_X0) * SC, TOP + y * SC, s * SC
W, H = 1080, 1920
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
col = np.array([200, 240, 255], np.float32)
r0 = round((G0 - IN) / 25 * 30); r1 = round((E1 - IN) / 25 * 30)
os.makedirs("glowv", exist_ok=True); last = None
for k, f in enumerate(range(r0, r1)):
    sf = IN + int((f + 0.001) / 30 * 25)       # image source affichée à cette image timeline
    e = track.get(sf) or last; last = e
    img = np.zeros((H, W, 3), np.float32)
    if e:
        kk = min(1.0, (k + 1) / 5) * (0.92 + 0.08 * np.sin(f * 1.7))
        inten = np.zeros((H, W), np.float32)
        for (x, y) in ((e[0], e[1]), (e[2], e[3])):
            ox, oy, sc = to_out(x, y, sf); fw = e[4] * sc
            d2 = (xx - ox) ** 2 + (yy - oy) ** 2
            inten += np.exp(-d2 / (2 * (0.035 * fw) ** 2)) * 1.0 + np.exp(-d2 / (2 * (0.16 * fw) ** 2)) * 0.45
            inten += np.exp(-((xx - ox) ** 2) / (2 * (0.55 * fw) ** 2) - ((yy - oy) ** 2) / (2 * 2.0 ** 2)) * 0.6
        img = np.clip(inten * kk, 0, 1)[..., None] * col
    cv2.imwrite("glowv/f%04d.png" % k, img.astype(np.uint8))
os.makedirs("out", exist_ok=True)
encode(os.path.join(D, "glowv"), os.path.join(D, "out", "2_glow.mov"))
print("rec", r0, "frames", r1 - r0)
