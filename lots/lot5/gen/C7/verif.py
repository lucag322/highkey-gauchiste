# Vérifs de l'aperçu C7 (sur l'EXPORT) :
#  1) visages > 5 % de la hauteur qui touchent un bord (règle Luca, comme lot3/C5/bordvisages.py) ;
#  2) coupes vidéo détectées vs attaques audio mesurées dans l'export (écart < 20 ms) ;
#  3) LUFS / true peak de l'export.
# Usage : python verif.py preview/apercu-C7.mp4
import sys, os, json, subprocess, shutil, numpy as np
HK = "/Users/luca.grousset/Movies/highkey-gauchiste"
sys.path.insert(0, HK + "/lot2/_claude/gen/C1")
import temps_forts as TF
FF = "/opt/homebrew/bin/ffmpeg"; FACES = HK + "/_claude/outils/faces"
D = os.path.dirname(os.path.abspath(__file__))
src = sys.argv[1]
plan = json.load(open(D + "/plan-C7.json"))
# 1) visages au bord
d = D + "/cache/_bord"; shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
subprocess.run([FF, "-v", "error", "-i", src, "-vf", "fps=10", "-q:v", "3", d + "/f%04d.jpg"], check=True)
subprocess.run([FACES, d], check=True, capture_output=True)
js = json.load(open(d + "/faces.json")); bad = []; n = 0
for k in sorted(js):
    t = (int(k[1:5]) - 1) / 10
    for x, y, w, h in js[k]:
        if h < 0.05: continue
        n += 1
        top, bot, l, r = y - 0.4 * h, y + h * 1.08, x - 0.12 * w, x + w * 1.12
        if top < 0 or bot > 1 or l < 0 or r > 1: bad.append("%.1fs h=%.2f (haut %.2f bas %.2f g %.2f d %.2f)" % (t, h, top, bot, l, r))
shutil.rmtree(d, ignore_errors=True)
print("visages >5 %%: %d sur %d images | au bord : %d" % (n, len(js), len(bad)))
for b in bad: print("  ", b)
# 2) coupes vs frappes
v = np.frombuffer(subprocess.run([FF, "-v", "error", "-i", src, "-vf", "scale=96:170,format=gray", "-f", "rawvideo", "-"], capture_output=True).stdout, np.uint8).reshape(-1, 170, 96).astype(np.float32)
dd = np.abs(np.diff(v, axis=0)).mean((1, 2))
cuts = [(i + 1) / 30 for i in range(len(dd)) if dd[i] > 12 and dd[i] > 3 * np.median(dd[max(0, i - 5):i + 6])]
p = D + "/cache/_exp.wav"
subprocess.run([FF, "-v", "error", "-y", "-i", src, "-vn", "-ac", "1", "-ar", "48000", p], check=True)
mx = 0
print("coupes vidéo détectées :", [round(c, 3) for c in cuts])
for c in plan["musique"]["coupes_timeline_s"]:
    vc = min(cuts, key=lambda x: abs(x - c))
    _, a, s = TF.mesure(p, [vc], tol=0.06)[0]
    err = (vc - a) * 1000; mx = max(mx, abs(err))
    print("frappe prévue %.3f | coupe vidéo %.3f | attaque mesurée %.3f (score %.1f) | écart %+.0f ms" % (c, vc, a, s, err))
print("écart max %.0f ms" % mx)
os.remove(p)
# 3) loudness
r = subprocess.run([FF, "-v", "info", "-i", src, "-vn", "-af", "loudnorm=print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
j = json.loads(r[r.rindex("{"):r.rindex("}") + 1]); print("export : %s LUFS, true peak %s dBTP" % (j["input_i"], j["input_tp"]))
print(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=width,height,codec_name", "-of", "csv=p=0", src], capture_output=True, text=True).stdout)
