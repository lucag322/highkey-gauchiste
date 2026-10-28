# facescan.py src t dur : visages (px source 1920x1080) sur la durée du plan, 6 i/s -> min/max x0,x1,y0,y1 par visage (h >= 70 px)
import sys, os, json, subprocess, shutil
FF = "/opt/homebrew/bin/ffmpeg"; FACES = "/Users/luca.grousset/Movies/highkey-gauchiste/_claude/outils/faces"
src, t, dur = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
d = "/private/tmp/claude-502/z3/fs"; shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
subprocess.run([FF, "-v", "error", "-ss", str(t), "-i", src, "-t", str(dur), "-vf", "fps=6,scale=960:-2", "-q:v", "3", d + "/f%04d.jpg"], check=True)
subprocess.run([FACES, d], check=True, capture_output=True)
js = json.load(open(d + "/faces.json")); boxes = []
for k in sorted(js):
    for x, y, w, h in js[k]:
        X0, X1 = (x - 0.12 * w) * 1920, (x + 1.12 * w) * 1920; Y0, Y1 = (y - 0.4 * h) * 1080, (y + 1.08 * h) * 1080
        if h * 1080 >= 40: boxes.append((k, int(X0), int(X1), int(Y0), int(Y1), int(h * 1080)))
for b in boxes: print(*b)
