# Positions du visage principal (px source 1920x1080) sur des fenêtres candidates : python probe_faces.py fichier t0 dur [hint_x hint_y]
import sys
ROOT = "/Users/luca.grousset/Movies/highkey-gauchiste"; LOT = ROOT + "/lot2"
sys.path.insert(0, ROOT + "/_claude/outils")
import framing
framing.ROOT = LOT; framing.CACHE = LOT + "/_claude/gen/A5/cache"
src, t0, dur = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]); fps = int(sys.argv[4]) if len(sys.argv) > 4 else 25
s = int(round(t0 * fps)); n = int(round(dur * fps))
faces = framing.detect(src, s, n, fps)
for i in range(0, n, 5):
    fl = sorted(faces[i], key=lambda f: -f[3])[:4]
    print("%.2f" % ((s + i) / fps), " ".join("[x%d-%d y%d-%d h%d]" % (f[0], f[0] + f[2], f[1], f[1] + f[3], f[3]) for f in fl))
