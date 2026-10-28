# Mesure sur l'export : coupes (saut d'image) et écart à la frappe la plus proche (rythme/frappes_tl.json (toutes les attaques réelles : 808, clap, cloche)). usage : mesure.py export.mp4
import sys, json, subprocess, numpy as np
FF = "/opt/homebrew/bin/ffmpeg"; R = "/Users/luca.grousset/Movies/highkey-gauchiste/lot5/_claude/gen/P3/rythme/"
K = json.load(open(R + "frappes_tl.json"))["frappes_tl"]
w, h = 180, 320
raw = subprocess.run([FF, "-v", "error", "-i", sys.argv[1], "-vf", "scale=%d:%d,format=gray" % (w, h), "-f", "rawvideo", "-"], capture_output=True).stdout
fr = np.frombuffer(raw, np.uint8).reshape(-1, h, w).astype(np.float32); fps = 30.0
d = np.abs(np.diff(fr, axis=0)).mean(axis=(1, 2)); med = np.median(d)
cuts = [i + 1 for i in range(len(d)) if d[i] > max(5 * med, 8) and d[i] == d[max(i - 2, 0):i + 3].max()]
print("images", len(fr), "durée %.3f s | coupes" % (len(fr) / fps), len(cuts)); errs = []
for c in cuts:
    t = c / fps; k = min(K, key=lambda x: abs(x - t)); errs.append(t - k)
    print("  coupe %6.3f s (img %3d) -> frappe %6.3f : %+4.0f ms" % (t, c, k, (t - k) * 1000))
print("écart max %.0f ms" % (max(abs(e) for e in errs) * 1000 if errs else 0))
