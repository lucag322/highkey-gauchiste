# probe.py src t0 dur [fps] : boîtes de visages (px source) toutes les 0,5 s
import sys, json
sys.path.insert(0, "/Users/luca.grousset/Movies/highkey-gauchiste/_claude/outils")
import framing
framing.ROOT = "/Users/luca.grousset/Movies/highkey-gauchiste/lot3"; framing.CACHE = framing.ROOT + "/_claude/gen/A8/cache"
src, t0, dur = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]); fps = float(sys.argv[4]) if len(sys.argv) > 4 else 25
s = int(round(t0 * fps)); n = int(dur * fps)
F = framing.detect(src, s, n, fps)
for i in range(0, n, int(fps / 2)):
    print("%.2f" % (t0 + i / fps), " ".join("[%d,%d %dx%d]" % tuple(int(v) for v in f) for f in sorted(F[i])))
