# Temps forts RÉELS d'un audio (attaques mesurées, pas de grille) : saut d'énergie multi-bandes.
# Fenêtres de 5 ms ; score = 0,4 × saut graves (<120 Hz) + saut médiums (120 Hz-1 kHz) + saut aigus (>1 kHz),
# saut = moyenne des 40 ms après − moyenne des 80 ms avant (dB). Attaque = pic local du score.
# Usage : python temps_forts.py fichier.wav [t0] [t1] [seuil=6]      -> "t score"
#         python temps_forts.py fichier.wav mesure t1,t2,...           -> attaque mesurée la plus proche (±60 ms) et écart
import sys, subprocess, numpy as np
from scipy.signal import butter, sosfiltfilt
FF = "/opt/homebrew/bin/ffmpeg"; SR = 48000; W = int(0.005 * SR)
def load(p, t0=0.0, d=None):
    cmd = [FF, "-v", "error", "-ss", "%.4f" % t0, "-i", p] + (["-t", "%.4f" % d] if d else []) + ["-f", "f32le", "-ac", "1", "-ar", str(SR), "-"]
    return np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, np.float32).astype(np.float64)
def score(x):
    bands = [butter(4, 120, "low", fs=SR, output="sos"), butter(4, [120, 1000], "band", fs=SR, output="sos"), butter(4, 1000, "high", fs=SR, output="sos")]
    n = len(x) // W
    E = np.array([10 * np.log10((sosfiltfilt(b, x)[:n * W].reshape(n, W) ** 2).mean(1) + 1e-12) for b in bands])
    J = np.zeros_like(E)
    for i in range(16, n - 8): J[:, i] = E[:, i:i + 8].mean(1) - E[:, i - 16:i].mean(1)
    return np.arange(n) * W / SR, J[0] * 0.4 + J[1] + J[2]
def attaques(x, t0=0.0, seuil=6.0, half=0.25):
    t, s = score(x); w = int(half * SR / W); out = []
    for i in range(w, len(s) - w):
        if s[i] >= seuil and s[i] == s[i - w:i + w + 1].max(): out.append((t0 + t[i], float(s[i])))
    return out
def mesure(p, temps, tol=0.06):
    a, b = max(min(temps) - 1.0, 0), max(temps) + 1.0
    t, s = score(load(p, a, b - a)); t = t + a; res = []
    for c in temps:
        m = (t > c - tol) & (t < c + tol); i = np.where(m)[0][np.argmax(s[m])]
        res.append((c, float(t[i]), float(s[i])))
    return res
if __name__ == "__main__":
    p = sys.argv[1]
    if len(sys.argv) > 2 and sys.argv[2] == "mesure":
        for c, a, s in mesure(p, [float(v) for v in sys.argv[3].split(",")]): print("%.3f -> %.3f  écart %+.0f ms  score %.1f" % (c, a, (a - c) * 1000, s))
    else:
        t0 = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0; t1 = float(sys.argv[3]) if len(sys.argv) > 3 else None
        seuil = float(sys.argv[4]) if len(sys.argv) > 4 else 6.0
        for a, s in attaques(load(p, t0, (t1 - t0) if t1 else None), t0, seuil): print("%.3f %.1f" % (a, s))
