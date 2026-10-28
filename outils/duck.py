# duck.py in.wav out.wav "t0:dB,t1:dB,..." [start] [dur] -> enveloppe linéaire en dB entre les points
import sys, subprocess
inp, out, pts = sys.argv[1], sys.argv[2], sys.argv[3]
ss = sys.argv[4] if len(sys.argv) > 4 else "0"; du = sys.argv[5] if len(sys.argv) > 5 else None
P = [tuple(map(float, p.split(":"))) for p in pts.split(",")]
expr = "%f" % P[0][1]
for (t0, d0), (t1, d1) in zip(P, P[1:]):
    expr = "if(gte(t,%f),%s,%s)" % (t0, "(%f+(%f)*min(1,(t-%f)/%f))" % (d0, d1 - d0, t0, max(t1 - t0, 1e-3)), expr)
expr = "if(gte(t,%f),%f,%s)" % (P[-1][0], P[-1][1], expr)
cmd = ["ffmpeg", "-v", "error", "-y", "-ss", ss] + (["-t", du] if du else []) + ["-i", inp, "-af",
       "volume='pow(10,(%s)/20)':eval=frame,aresample=48000" % expr, "-ac", "2", "-c:a", "pcm_s24le", out]
subprocess.run(cmd, check=True); print(out)
