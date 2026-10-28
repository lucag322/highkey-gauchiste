# Mesure sur l'export : coupes détectées dans l'image vs frappes réelles détectées dans le son EXPORTÉ (méthode gabarit de hits.py).
import sys, json, subprocess, numpy as np
sys.path.insert(0, "/Users/luca.grousset/Movies/highkey-gauchiste/lot3/_claude/gen/A7"); import hits as HT
FF = "/opt/homebrew/bin/ffmpeg"; src = sys.argv[1]; D = "/Users/luca.grousset/Movies/highkey-gauchiste/lot3/_claude/gen/A7/"
p = subprocess.run([FF, "-v", "error", "-i", src, "-vf", "scale=135:240,format=gray", "-f", "rawvideo", "-"], capture_output=True)
v = np.frombuffer(p.stdout, np.uint8).reshape(-1, 240, 135).astype(np.float32)
d = np.abs(np.diff(v, axis=0)).mean((1, 2))
cuts = [i + 1 for i in range(len(d)) if d[i] > 18 and d[i] > 2.5 * np.median(d[max(0, i - 6):i + 7])]
wav = "/private/tmp/claude-502/apercu-A7-audio.wav"
subprocess.run([FF, "-v", "error", "-y", "-i", src, "-vn", "-ac", "1", "-ar", "48000", wav], check=True)
H = json.load(open(D + "cache/hits-refrain.json"))["hits"]; tl = np.array(H) - (H[0] - 0.02)
tl = tl[tl < len(v) / 30 - 0.15]
eh = HT.template_hits(wav, tl, off=0.0)                         # frappes mesurées dans l'export
errs = []
for c in cuts:
    k = int(np.argmin(np.abs(tl - c / 30))); e = (c / 30 - eh[k]) * 1000; errs.append(e)
    print("coupe image %3d  %.3f s  temps %2d  frappe export %.3f s  écart %+.1f ms" % (c, c / 30, k, eh[k], e))
print("coupes : %d | écart max %.1f ms | médiane %.1f ms" % (len(cuts), max(abs(x) for x in errs), np.median(np.abs(errs))))
if len(sys.argv) > 2:
    plan = json.load(open(sys.argv[2])); rec = sorted(set(x["rec"] for x in plan["video"]) - {0})
    print("coupes prévues :", len(rec), "| manquantes :", sorted(set(rec) - set(cuts)), "| en trop :", sorted(set(cuts) - set(rec)))
