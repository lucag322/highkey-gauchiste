# Suivi du micro (bonnette) par template matching multi-échelle ; sortie : t, x, y, échelle, score
import cv2, numpy as np, subprocess, sys, json
src, t0, dur, step = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4])
tpl_t, tx, ty, tr = float(sys.argv[5]), int(sys.argv[6]), int(sys.argv[7]), int(sys.argv[8])
def frames(t, d):
    p = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-t", str(d), "-i", src, "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True)
    return np.frombuffer(p.stdout, np.uint8).reshape(-1, 1080, 1920)
g = frames(tpl_t, 0.04)[0]; tpl = g[ty - tr:ty + tr, tx - tr:tx + tr]
fs = frames(t0, dur); n = int(round(step * 30)); out = []
for i in range(0, len(fs), n):
    best = None
    for s in np.arange(0.7, 1.75, 0.05):
        T = cv2.resize(tpl, None, fx=s, fy=s)
        r = cv2.matchTemplate(fs[i], T, cv2.TM_CCOEFF_NORMED); _, mv, _, ml = cv2.minMaxLoc(r)
        if best is None or mv > best[0]: best = (mv, ml[0] + T.shape[1] / 2, ml[1] + T.shape[0] / 2, s)
    out.append([round(t0 + i / 30, 3), round(best[1]), round(best[2]), round(best[3], 2), round(best[0], 2)])
    print(*out[-1], flush=True)
