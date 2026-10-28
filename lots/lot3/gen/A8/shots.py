# shots.py src : liste des plans (scdet) + planche d'une image au milieu de chaque plan
import sys, subprocess, re, os
FF = "/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg"; SRC = "/Users/luca.grousset/Movies/highkey-gauchiste/lot3/sources/"
src = sys.argv[1]; P = os.path.dirname(os.path.abspath(__file__)) + "/peek/"
dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", SRC + src], capture_output=True, text=True).stdout)
r = subprocess.run([FF, "-i", SRC + src, "-vf", "scale=320:-2,scdet=threshold=12", "-an", "-f", "null", "-"], capture_output=True, text=True).stderr
cuts = [0.0] + [float(x) for x in re.findall(r"lavfi.scd.time: ([0-9.]+)", r)] + [dur]
shots = [(a, b) for a, b in zip(cuts, cuts[1:]) if b - a > 0.3]
for a, b in shots: print("%.2f-%.2f (%.2f)" % (a, b, b - a))
ins = []; fl = []
for i, (a, b) in enumerate(shots):
    ins += ["-ss", "%.2f" % ((a + b) / 2), "-i", SRC + src]
    fl.append("[%d:v]trim=end_frame=1,scale=320:-2,drawtext=text='%.1f-%.1f':x=3:y=3:fontsize=18:fontcolor=yellow:box=1:boxcolor=black[v%d]" % (i, a, b, i))
cols = 8; n = len(shots); rows = (n + cols - 1) // cols
fl.append("".join("[v%d]" % i for i in range(n)) + "xstack=inputs=%d:layout=%s:fill=black[o]" % (n, "|".join("%d_%d" % ((i % cols) * 320, (i // cols) * 180) for i in range(n))) if n > 1 else "[v0]null[o]")
subprocess.run([FF, "-v", "error", "-y"] + ins + ["-filter_complex", ";".join(fl), "-map", "[o]", "-frames:v", "1", P + "shots_" + src.replace(".mp4", ".jpg")], check=True)
