import sys, subprocess, numpy as np
sys.path.insert(0, "/Users/luca.grousset/Movies/highkey-gauchiste/_claude/outils")
from decoupe import masques, controle, planche
src = sys.argv[1]; t = float(sys.argv[2]); n = int(sys.argv[3]); box = tuple(int(x) for x in sys.argv[4].split(",")); pt = tuple(float(x) for x in sys.argv[5].split(",")); out = sys.argv[6]
p = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", src, "-frames:v", str(n), "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True)
fr = list(np.frombuffer(p.stdout, np.uint8).reshape(-1, 1080, 1920, 3))
ms = masques(fr, box, pt, out + "_d")
for i in range(0, n, max(1, n // 6)): print(i, controle(ms[i]))
planche(fr, ms, box, out + ".jpg", n=6, larg=400)
