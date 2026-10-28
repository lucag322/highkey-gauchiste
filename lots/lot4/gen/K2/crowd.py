# Recherche d'un cadrage 9:16 de foule sans visage coupé (détection pleine résolution, critère de checkcut.py).
import sys, os, json, subprocess, numpy as np
THR = 0.058
FF = "/opt/homebrew/bin/ffmpeg"; FACES = "/Users/luca.grousset/Movies/highkey-gauchiste/_claude/outils/faces"
D = "/Users/luca.grousset/Movies/highkey-gauchiste/lot4/_claude/gen/K2/"
def detect_full(path, t, n, tag, step=3):
    """Visages (px source) sur n images à 30 i/s depuis t (une image sur step analysée)."""
    d = D + "cache/full/%s_%.2f_%d" % (tag, t, n)
    if not os.path.exists(d + "/faces.json"):
        os.makedirs(d, exist_ok=True)
        subprocess.run([FF, "-v", "error", "-y", "-ss", "%.4f" % t, "-i", path, "-vf", "fps=30,select='not(mod(n\\,%d))'" % step, "-fps_mode", "passthrough",
                        "-frames:v", str((n + step - 1) // step), "-start_number", "0", "-q:v", "2", d + "/f%04d.jpg"], check=True)
        subprocess.run([FACES, d], check=True, capture_output=True)
    js = json.load(open(d + "/faces.json"))
    wh = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=p=0", path], capture_output=True, text=True).stdout.strip().split(",")
    SW, SH = int(wh[0]), int(wh[1])
    return [[(b[0] * SW, b[1] * SH, b[2] * SW, b[3] * SH) for b in js.get("f%04d.jpg" % i, [])] for i in range((n + step - 1) // step)]
def bad_count(faces, cx, cy, v, z1=1.06):
    bad = 0; m = len(faces)
    for i, fl in enumerate(faces):
        vv = v / (1 + (z1 - 1) * i / max(m - 1, 1)); vw = vv * 9 / 16
        x0, y0, x1, y1 = cx - vw / 2, cy - vv / 2, cx + vw / 2, cy + vv / 2
        for x, y, w, h in fl:
            if w / vw < THR: continue
            hx0, hy0, hx1, hy1 = x - 0.16 * w, y - 0.45 * h, x + 1.16 * w, y + 1.12 * h
            inside = hx0 >= x0 and hx1 <= x1 and hy0 >= y0 and hy1 <= y1
            outside = hx1 <= x0 or hx0 >= x1 or hy1 <= y0 or hy0 >= y1
            if not inside and not outside: bad += 1
    return bad
def search(faces, bd, z1=1.06, scales=(1.0, 0.9, 0.8, 0.7, 0.6, 0.5)):
    vmax = min(bd[3] - bd[1], (bd[2] - bd[0]) * 16 / 9); best = None
    for vs in scales:
        v0 = vmax * vs; vw0 = v0 * 9 / 16
        for cy in np.arange(bd[1] + v0 / 2, bd[3] - v0 / 2 + 1, max(8, (bd[3] - bd[1] - v0) / 6 or 8)):
            for cx in np.arange(bd[0] + vw0 / 2, bd[2] - vw0 / 2 + 1, 8):
                b = bad_count(faces, cx, cy, v0, z1)
                sc = b * 1000 + (1 - vs) * 3 + abs(cx - (bd[0] + bd[2]) / 2) / 800
                if best is None or sc < best[0]: best = (sc, b, cx, cy, v0, vs)
    return best
if __name__ == "__main__":
    path, bd = sys.argv[1], tuple(map(int, sys.argv[2].split(","))); n = int(sys.argv[3])
    for t in map(float, sys.argv[4:]):
        f = detect_full(path, t, n, os.path.basename(path)[:-4])
        print(t, "visages/img %.1f" % np.mean([len(x) for x in f]), search(f, bd)[1:])
