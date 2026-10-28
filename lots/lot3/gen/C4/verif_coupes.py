# Mesure sur l'export : coupes vidéo (différence d'images) vs frappes audio (retour basse au drop, claps 3-12 kHz ensuite).
import sys, subprocess, json, numpy as np, scipy.signal as ss
FF = "/opt/homebrew/bin/ffmpeg"; src = sys.argv[1]
v = np.frombuffer(subprocess.run([FF, "-v", "error", "-i", src, "-vf", "scale=96:170,format=gray", "-f", "rawvideo", "-"], capture_output=True).stdout, np.uint8).reshape(-1, 170, 96).astype(np.float32)
d = np.abs(np.diff(v, axis=0)).mean((1, 2)); cuts = [(i + 1) / 30 for i in range(len(d)) if d[i] > 18 and d[i] > 3 * np.median(d[max(0, i - 5):i + 6])]
sr = 48000
a = np.frombuffer(subprocess.run([FF, "-v", "error", "-i", src, "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"], capture_output=True).stdout, np.float32)
plan = json.load(open(sys.argv[2])); C = plan["musique"]["coupes_timeline_s"]
def onset(sig, t, w=0.12):
    h = int(sr * 0.005); s0 = int((t - w) * sr); seg = sig[s0:s0 + int(2 * w * sr)]
    e = 20 * np.log10(np.array([np.sqrt(np.mean(seg[i:i + h] ** 2)) for i in range(0, len(seg) - h, h)]) + 1e-9)
    dd = e[2:] - e[:-2]; i = int(np.argmax(dd)); return t - w + (i + 2) * 0.005, dd[i]
lo = ss.filtfilt(*ss.butter(4, 100 / (sr / 2), "low"), a); hi = ss.filtfilt(*ss.butter(4, [3000 / (sr / 2), 12000 / (sr / 2)], "band"), a)
print("coupes vidéo détectées :", [round(c, 3) for c in cuts])
mx = 0
for k, c in enumerate(C[:-1]):
    vc = min(cuts, key=lambda x: abs(x - c)) if cuts else None
    ao, r = onset(lo if k == 0 else hi, c)
    err = (vc - ao) * 1000; mx = max(mx, abs(err))
    print("frappe %.3f prévue | coupe vidéo %.3f | frappe mesurée %.3f (+%.0f dB) | écart %+.0f ms" % (c, vc, ao, r, err))
print("écart max %.0f ms" % mx)
