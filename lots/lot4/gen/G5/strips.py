# strips.py out.jpg "fichier:t:dur" ... -> une ligne de 6 images par plan candidat (sources lot2)
import sys, subprocess, os
FF = "/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg"; S = "/Users/luca.grousset/Movies/highkey-gauchiste/lot2/sources/A5"
T = "/private/tmp/claude-502/-Users-luca-grousset-Documents-GitHub-perso/a34e79cf-b36f-4413-8b7e-459475c5f14e/scratchpad/st/"
outs = []
for i, spec in enumerate(sys.argv[2:]):
    f, t, d = spec.split(":"); o = T + "_c%02d.jpg" % i; outs.append(o)
    subprocess.run([FF, "-v", "error", "-y", "-ss", t, "-i", S + f + ".mp4", "-t", d, "-vf",
        "fps=%g,scale=320:-2,drawtext=text='%s %s+%%{pts\\:flt}':x=3:y=3:fontsize=14:fontcolor=yellow:box=1:boxcolor=black,tile=6x1:padding=2" % (6 / float(d), f[-8:], t),
        "-frames:v", "1", "-update", "1", o], check=True)
args = [FF, "-v", "error", "-y"]
for o in outs: args += ["-i", o]
args += ["-filter_complex", "".join("[%d]" % i for i in range(len(outs))) + "vstack=inputs=%d" % len(outs), sys.argv[1]]
subprocess.run(args, check=True); [os.remove(o) for o in outs]
