# strips.py "fichier:t:dur" ... -> sheets/candidats.jpg (5 images par plan, une ligne par plan)
import sys, subprocess
FF = "/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg"; S = "/Users/luca.grousset/Movies/highkey-gauchiste/lot3/sources/G4-obono-"
outs = []
for i, spec in enumerate(sys.argv[1:]):
    f, t, d = spec.split(":"); o = "sheets/_c%02d.jpg" % i; outs.append(o)
    subprocess.run([FF, "-v", "error", "-y", "-ss", t, "-i", S + f + ".mp4", "-t", d, "-vf",
        "fps=%g,scale=240:-2,drawtext=text='%d %s %s+%%{pts\\:flt}':x=3:y=3:fontsize=12:fontcolor=yellow:box=1:boxcolor=black,tile=5x1:padding=2" % (5 / float(d), i + 1, f[-6:], t),
        "-frames:v", "1", "-update", "1", o], check=True)
args = [FF, "-v", "error", "-y"]
for o in outs: args += ["-i", o]
args += ["-filter_complex", "".join("[%d]" % i for i in range(len(outs))) + "vstack=inputs=%d" % len(outs), "sheets/candidats.jpg"]
subprocess.run(args, check=True)
import os; [os.remove(o) for o in outs]
