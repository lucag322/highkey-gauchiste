# Segmente une vidéo de réf en plans (N=noir, B=blanc, I=image) avec les vrais pts (VFR ok)
import subprocess, numpy as np, sys, re
path = sys.argv[1]; thr = float(sys.argv[2]) if len(sys.argv) > 2 else 22
p = subprocess.run(["ffmpeg", "-v", "info", "-i", path, "-vf", "scale=96:96,format=gray,showinfo", "-fps_mode", "passthrough", "-f", "rawvideo", "-"], capture_output=True)
raw = np.frombuffer(p.stdout, np.uint8).reshape(-1, 96, 96).astype(np.float32)
pts = [float(x) for x in re.findall(r"pts_time:([0-9.]+)", p.stderr.decode())]
def cls(g): return "N" if g.mean() < 14 and g.std() < 10 else ("B" if g.mean() > 200 else "I")
segs = []; prev = None
for t, g in zip(pts, raw):
    c = cls(g); d = np.abs(g - prev).mean() if prev is not None else 0; prev = g
    if not segs or c != segs[-1][0] or (c == "I" and d > thr): segs.append([c, t, t])
    segs[-1][2] = t
print(len(pts), "images")
print(" ".join("%s%.2f" % (c, a) for c, a, b in segs))
