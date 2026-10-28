# Mesure sur un export G6 : coupes (saut d image) et écart au frappe réelle le plus proche (rythme/frappes.json) ; --zoom : poussées.
# usage : mesure.py export.mp4 [--zoom]
import sys, json, subprocess, numpy as np, cv2
FF = "/opt/homebrew/bin/ffmpeg"; G3 = "/Users/luca.grousset/Movies/highkey-gauchiste/lot4/_claude/gen/G6/rythme/"
K = json.load(open(G3 + "frappes.json"))["frappes_timeline"]
src = sys.argv[1]; w, h = 180, 320
raw = subprocess.run([FF, "-v", "error", "-i", src, "-vf", "scale=%d:%d,format=gray" % (w, h), "-f", "rawvideo", "-"], capture_output=True).stdout
fr = np.frombuffer(raw, np.uint8).reshape(-1, h, w).astype(np.float32)
fps = 30.0
d = np.abs(np.diff(fr, axis=0)).mean(axis=(1, 2))
med = np.median(d); cuts = [i + 1 for i in range(len(d)) if d[i] > max(5 * med, 8) and d[i] == d[max(i - 2, 0):i + 3].max()]
print("images", len(fr), "| coupes", len(cuts))
errs = []
for c in cuts:
    t = c / fps; k = min(K, key=lambda x: abs(x - t)); errs.append(t - k)
    print("  coupe %5.3f s (img %3d) -> kick %6.3f : %+4.0f ms" % (t, c, k, (t - k) * 1000))
print("écart max %.0f ms" % (max(abs(e) for e in errs) * 1000 if errs else 0))
if "--zoom" in sys.argv:   # échelle relative image à image (ORB + affine partielle), hors coupes
    orb = cv2.ORB_create(800); bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True); sc = []
    for i in range(1, len(fr)):
        if i in cuts: sc.append(np.nan); continue
        a, b = fr[i - 1].astype(np.uint8), fr[i].astype(np.uint8)
        ka, da = orb.detectAndCompute(a, None); kb, db = orb.detectAndCompute(b, None)
        if da is None or db is None: sc.append(np.nan); continue
        m = bf.match(da, db)
        if len(m) < 12: sc.append(np.nan); continue
        A, _ = cv2.estimateAffinePartial2D(np.float32([ka[x.queryIdx].pt for x in m]), np.float32([kb[x.trainIdx].pt for x in m]))
        sc.append(np.hypot(A[0, 0], A[1, 0]) - 1 if A is not None else np.nan)
    sc = np.array(sc)
    bounds = [0] + cuts + [len(fr)]
    for a, b in zip(bounds, bounds[1:]):
        seg = sc[a:b - 1]; t0 = a / fps
        if len(seg) < 4: continue
        moving = [i for i, v in enumerate(seg) if not np.isnan(v) and v > 0.0008]
        if not moving: print("  plan %.3f : fixe" % t0); continue
        stop = (a + moving[-1] + 2) / fps
        print("  plan %5.3f-%5.3f : poussée %.1f %%/s au début, s'arrête ~%.3f s (kick le plus proche %.3f)" % (
            t0, b / fps, np.nanmean(seg[:4]) * fps * 100, stop, min(K + [b / fps], key=lambda x: abs(x - stop))))
