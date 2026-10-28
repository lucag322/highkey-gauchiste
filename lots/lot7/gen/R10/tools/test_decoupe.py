# Contrôle des découpes candidates avec l'outil partagé _claude/outils/decoupe.py (planche magenta + controle)
import sys, subprocess, numpy as np, cv2
HG = "/Users/luca.grousset/Movies/highkey-gauchiste"; sys.path.insert(0, HG + "/_claude/outils")
from decoupe import masques, controle, planche
C = [("PH_A1", "lot7/sources/R10-hassan-strasbourg-neutralite.mp4", 12.72, 41, (230, 0, 1600, 870), (0.51, 0.70)),
     ("PH_A3", "lot7/sources/R10-hassan-strasbourg-neutralite.mp4", 15.40, 39, (230, 0, 1600, 870), (0.51, 0.70)),
     ("PH_A7", "lot7/sources/R10-hassan-strasbourg-neutralite.mp4", 20.29, 25, (230, 0, 1600, 870), (0.51, 0.70)),
     ("SC_B1", "lot3/sources/A7-hassan-strasbourg-c.mp4", 21.40, 40, (300, 0, 1600, 1000), (0.40, 0.75)),
     ("SA_B3", "lot3/sources/A7-hassan-strasbourg-a.mp4", 28.60, 39, (300, 0, 1600, 875), (0.47, 0.72)),
     ("SB_B4", "lot3/sources/A7-hassan-strasbourg-b.mp4", 4.95, 40, (300, 0, 1600, 875), (0.47, 0.72))]
only = sys.argv[1:]
for key, src, t, n, box, pt in C:
    if only and key not in only: continue
    p = subprocess.run(["ffmpeg", "-v", "error", "-ss", "%.3f" % t, "-i", HG + "/" + src, "-frames:v", str(n), "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True)
    fr = list(np.frombuffer(p.stdout, np.uint8).reshape(-1, 1080, 1920, 3))
    ms = masques(fr, box, pt, "cache/dec/%s_%.2f_%d" % (key, t, n))
    cs = [controle(m) for m in ms]
    worst = {k: max(c[k] for c in cs) for k in cs[0]}
    print(key, "pire :", worst)
    planche(fr, ms, box, "sheets/dec_%s.jpg" % key, n=4, larg=480)
