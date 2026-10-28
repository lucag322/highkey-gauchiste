# Planche de vérification des fenêtres 9:16 : framecheck.py out.jpg "src|t|fx|fy|h|top" ...
import sys, subprocess, os
sys.path.insert(0, os.path.dirname(__file__))
ROOT = "/Users/luca.grousset/Movies/highkey-gauchiste/sources/"
FF = "/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg"
exec(open(os.path.join(os.path.dirname(__file__), "compkit.py")).read())
out = sys.argv[1]; tiles = []
for i, spec in enumerate(sys.argv[2:]):
    src, t, fx, fy, h, top = spec.split("|"); x0, y0, w, hh = win916(float(fx), float(fy), float(h), float(top))
    p = "/tmp/claude-502/fc_%02d.png" % i
    subprocess.run([FF, "-v", "error", "-y", "-ss", t, "-i", ROOT + src, "-frames:v", "1", "-vf",
                    "crop=%d:%d:%d:%d,scale=180:320,drawtext=fontfile=/System/Library/Fonts/Supplemental/Arial.ttf:text='%s %s':x=3:y=3:fontsize=14:fontcolor=yellow:box=1:boxcolor=black" % (w, hh, x0, y0, src[:6], t), p])
    tiles.append(p)
n = len(tiles)
subprocess.run([FF, "-v", "error", "-y"] + sum([["-i", p] for p in tiles], []) + ["-filter_complex", "hstack=inputs=%d" % n if n > 1 else "null", out])
print(out)
