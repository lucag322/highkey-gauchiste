# probe.py : visages (px source) sur les moments candidats (cache A9)
import sys
sys.path.insert(0, "/Users/luca.grousset/Movies/highkey-gauchiste/_claude/outils")
import framing
framing.ROOT = "/Users/luca.grousset/Movies/highkey-gauchiste/lot4"; framing.CACHE = framing.ROOT + "/_claude/gen/A9/cache"
C = [("A9-boyard-meeting-npp-a.mp4", 2.55, 3.9), ("A9-boyard-meeting-npp-a.mp4", 49.0, 1.4), ("A9-boyard-meeting-npp-b.mp4", 24.2, 0.7),
     ("A9-boyard-meeting-npp-a.mp4", 19.0, 0.7), ("A9-boyard-meeting-npp-a.mp4", 57.0, 0.7), ("A9-boyard-an-santementale.mp4", 30.0, 0.7),
     ("A9-boyard-meeting-npp-a.mp4", 22.4, 0.7), ("A9-boyard-meeting-npp-a.mp4", 26.4, 0.7), ("A9-boyard-meeting-npp-b.mp4", 26.2, 0.7),
     ("A9-boyard-meeting-npp-a.mp4", 40.3, 0.7), ("A9-boyard-meeting-npp-a.mp4", 55.0, 0.9)]
for src, t, d in C:
    s = int(round(t * 25)); n = int(round(d * 25)) + 2
    fs = framing.detect(src, s, n, 25)
    print(src[3:], t)
    for i in range(0, n, 5):
        print("   %5.2f" % ((s + i) / 25), [tuple(int(v) for v in f) for f in fs[i] if f[3] > 30])
