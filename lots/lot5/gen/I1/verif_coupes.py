# Mesure sur l'export : coupes vidéo (différence d'images) vs frappes audio réelles (flux spectral graves+bas-médium+aigus) près de chaque coupe prévue.
import sys, subprocess, json, numpy as np, librosa
FF = "/opt/homebrew/bin/ffmpeg"; src = sys.argv[1]
v = np.frombuffer(subprocess.run([FF, "-v", "error", "-i", src, "-vf", "scale=96:170,format=gray", "-f", "rawvideo", "-"], capture_output=True).stdout, np.uint8).reshape(-1, 170, 96).astype(np.float32)
d = np.abs(np.diff(v, axis=0)).mean((1, 2)); cuts = [(i + 1) / 30 for i in range(len(d)) if d[i] > 12 and d[i] > 3 * np.median(d[max(0, i - 5):i + 6])]
sr = 48000
a = np.frombuffer(subprocess.run([FF, "-v", "error", "-i", src, "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"], capture_output=True).stdout, np.float32)
S = np.abs(librosa.stft(a, n_fft=1024, hop_length=128)); f = librosa.fft_frequencies(sr=sr, n_fft=1024)
def flux(m):
    L = np.log1p(100 * S[m]); dd = np.maximum(0, np.diff(L, axis=1)).sum(0); return dd / np.percentile(dd, 99)
x = flux(f < 150) + flux((f > 150) & (f < 600)) + flux(f > 6000); t = (np.arange(len(x)) + 1) * 128 / sr
plan = json.load(open(sys.argv[2])); C = plan["musique"]["coupes_timeline_s"][:-1]
mx = 0
for c in C:
    if c < plan["musique"]["drop_timeline_s"] - 2.5: continue          # coupes sous la voix du début : frappes masquées (musique -11 dB)
    vc = min(cuts, key=lambda z: abs(z - c)); m = (t > c - 0.04) & (t < c + 0.04); ao = float(t[m][np.argmax(x[m])])
    err = (vc - ao) * 1000; mx = max(mx, abs(err))
    print("coupe prévue %.3f | coupe vidéo %.3f | frappe mesurée %.3f | écart %+.0f ms" % (c, vc, ao, err))
print("écart max %.0f ms" % mx)
