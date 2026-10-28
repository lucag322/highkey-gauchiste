# Yeux qui brillent sur « vous démissionnez » (Bompard), séquence RGBA 1920x1080 alignée sur l'item E (source 5841..6026)
import json, numpy as np, cv2, os
D = os.path.dirname(os.path.abspath(__file__)); os.chdir(D)
eyes = json.load(open("eyeframes/eyes.json"))
E0, E1 = 5563, 6685; F_EYE0 = 5950           # eyeframes/f0000 = source frame 5950 (238,0 s)
G0 = round(239.55 * 25)                      # début du glow
prev = (782, 373); track = {}
for i in range(78):
    faces = eyes.get("f%04d.png" % i, [])
    if not faces: continue
    best = min(faces, key=lambda f: (((f[0] + f[2]) / 2 - prev[0]) ** 2 + ((f[1] + f[3]) / 2 - prev[1]) ** 2))
    c = ((best[0] + best[2]) / 2, (best[1] + best[3]) / 2)
    if (c[0] - prev[0]) ** 2 + (c[1] - prev[1]) ** 2 < 120 ** 2:
        track[F_EYE0 + i] = best; prev = c
H, W = 1080, 1920
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
col = np.array([200, 240, 255], np.float32) / 255   # BGR blanc chaud
os.makedirs("glow", exist_ok=True)
last = None; n_on = 0
for f in range(E0, E1):
    img = np.zeros((H, W, 4), np.float32)
    if G0 <= f < 6027 and (track.get(f) or last):
        e = track.get(f) or last; last = e
        k = min(1.0, (f - G0 + 1) / 4) * (0.92 + 0.08 * np.sin(f * 1.7))
        fw = e[4]; inten = np.zeros((H, W), np.float32)
        for (x, y) in ((e[0], e[1]), (e[2], e[3])):
            d2 = (xx - x) ** 2 + (yy - y) ** 2
            inten += np.exp(-d2 / (2 * (0.035 * fw) ** 2)) * 1.0          # coeur
            inten += np.exp(-d2 / (2 * (0.16 * fw) ** 2)) * 0.45         # halo
            inten += np.exp(-((xx - x) ** 2) / (2 * (0.55 * fw) ** 2) - ((yy - y) ** 2) / (2 * 2.2 ** 2)) * 0.6  # trait horizontal
        a = np.clip(inten * k, 0, 1)
        img[..., :3] = col; img[..., 3] = a; n_on += 1
    cv2.imwrite("glow/glow_%04d.png" % (f - E0), (img * 255).astype(np.uint8))
print("frames", E1 - E0, "glow on", n_on, "tracked", len(track))
