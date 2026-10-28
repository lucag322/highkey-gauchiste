# Génère les LUT .cube des styles (entrée Rec709 niveaux vidéo -> sortie Rec709)
import numpy as np, os
OUT = "/Users/luca.grousset/Movies/highkey-gauchiste/_claude/luts"
N = 33
def write(name, fn):
    g = np.linspace(0, 1, N, dtype=np.float64)
    b, gg, r = np.meshgrid(g, g, g, indexing="ij")   # .cube : R varie le plus vite
    rgb = np.stack([r, gg, b], -1).reshape(-1, 3)
    o = np.clip(fn(rgb), 0, 1)
    with open(os.path.join(OUT, name + ".cube"), "w") as f:
        f.write('TITLE "%s"\nLUT_3D_SIZE %d\n' % (name, N))
        for v in o: f.write("%.6f %.6f %.6f\n" % tuple(v))
def luma(c): return (c @ np.array([0.2126, 0.7152, 0.0722]))[:, None]
def scurve(x, k):  # contraste autour de 0.5
    return 0.5 + (x - 0.5) * k / (1 + (k - 1) * np.abs(2 * (x - 0.5)) ** 1.0) if k != 1 else x
def sat(c, s): L = luma(c); return L + (c - L) * s
def smooth_s(x, amt):  # courbe en S douce, amt 0..1
    s = x * x * (3 - 2 * x); return x + (s - x) * amt
# 6 : footage chaud, brun, contraste doux (palette réf #463C34 #907965 #B9A38E)
write("s6_chaud", lambda c: np.clip(sat(smooth_s(c, 0.5), 0.75), 0, 1) ** 1.1 * np.array([1.05, 0.95, 0.80]) + np.array([0.025, 0.012, 0.0]))
# 1 : N&B très contrasté (palette réf #020202..#DCDEDC)
write("s1_nb", lambda c: np.repeat(np.clip(smooth_s(np.clip((luma(c) - 0.06) / 0.86, 0, 1), 1.0) ** 1.15 * 0.9 + 0.01, 0, 1), 3, 1))
# 3 : sépia lavé, noirs relevés (palette #131416 #555051 #A59C9B #E0DEE1)
def s3(c):
    L = np.clip((luma(c) - 0.03) / 0.9, 0, 1); L = smooth_s(L, 0.35)
    L = 0.07 + L * 0.82
    return L * np.array([1.03, 0.98, 0.94])[None] + (c - luma(c)) * 0.12
write("s3_sepia", s3)
# 4 : rose chaud doux, noirs relevés (palette #261B21 #674F50 #B18E8D #E3CBCB)
def s4(c):
    c = sat(smooth_s(c, 0.2), 0.9); c = 0.035 + c * 0.95
    return np.clip(c * np.array([1.03, 0.985, 0.98]), 0, 1)
write("s4_rose", s4)
# 5 : naturel, un peu de punch (palette #14181A #38363C #5F5E62 #948785 #CAC0B6)
write("s5_punch", lambda c: sat(smooth_s(c, 0.3), 0.92) * np.array([1.0, 0.99, 0.98]))
print(sorted(os.listdir(OUT)))
