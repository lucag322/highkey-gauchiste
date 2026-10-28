# Balayage : contrôle de découpe (outil partagé decoupe.py) sur des plans candidats, 1 image sur 3.
import sys, os, json, subprocess, numpy as np
HG = "/Users/luca.grousset/Movies/highkey-gauchiste"; sys.path.insert(0, HG + "/_claude/outils")
from decoupe import masques, controle, planche
SRC = {"EG": "lot7/sources/R16-guiraud-lcp-eglise.mp4", "RUE": "lot7/sources/R16-guiraud-lcp-rue.mp4", "TAG": "lot7/sources/R16-guiraud-lcp-tag.mp4",
       "BRI": "lot7/sources/R16-guiraud-lcp-brique.mp4", "AFF": "lot7/sources/R16-guiraud-lcp-affiche.mp4"}
def frames(src, t, dur, step=3):
    p = subprocess.run(["ffmpeg", "-v", "error", "-ss", "%.3f" % t, "-t", "%.3f" % dur, "-i", HG + "/" + SRC[src], "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True)
    a = np.frombuffer(p.stdout, np.uint8).reshape(-1, 1080, 1920, 3); return [a[i] for i in range(0, len(a), step)]
for c in json.loads(sys.argv[1]):
    src, t, dur, box, pt = c; fs = frames(src, t, dur); key = "%s_%.1f_%d_%d" % (src, t, box[0], box[2])
    ms = masques(fs, tuple(box), tuple(pt), HG + "/lot7/_claude/gen/R16/cache/scan/" + key)
    cs = [controle(m) for m in ms]; w = {k: max(x[k] for x in cs) for k in ("gauche", "droite", "haut", "bas_net", "morceaux")}
    planche(fs, ms, tuple(box), HG + "/lot7/_claude/gen/R16/cache/scan/%s.jpg" % key)
    print(key, w, flush=True)
