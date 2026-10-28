# Vraies frappes de Billie Jean : grille ajustée sur l'enveloppe d'attaques (percussions), puis affinage local de chaque frappe.
import sys, numpy as np, librosa
SR = 48000; HOP = 48
def envelope(path, off, dur):
    y, _ = librosa.load(path, sr=SR, mono=True, offset=off, duration=dur)
    yp = librosa.effects.percussive(y, margin=2.0)
    # bandes sans la voix de MJ : kick (< 130 Hz) + caisse claire / charleston (> 5 kHz)
    S = np.abs(librosa.stft(yp, n_fft=1024, hop_length=HOP)); f = librosa.fft_frequencies(sr=SR, n_fft=1024)
    def flux(band):
        x = np.log1p(100 * S[band]); return np.maximum(x[:, 2:] - x[:, :-2], 0).mean(0)
    e = flux(f < 130) / 1.0 + flux(f > 5000)
    e = np.concatenate([[0, 0], e])
    t = np.arange(len(e)) * HOP / SR + off
    return e / (e.max() + 1e-9), t
def fit_grid(e, t, t0, n, bpm_range=(115.5, 118.5)):
    best = None
    for bpm in np.arange(bpm_range[0], bpm_range[1], 0.02):
        P = 60 / bpm
        for b0 in np.arange(t0 - 0.03, t0 + 0.03, 0.001):
            g = b0 + np.arange(n) * P; idx = np.clip(np.searchsorted(t, g), 0, len(t) - 1)
            sc = sum(e[max(0, i - 2):i + 3].max() for i in idx)
            if best is None or sc > best[0]: best = (sc, b0, P)
    return best[1], best[2]
def hits(path, t0, n, win=0.04):
    e, t = envelope(path, max(0, t0 - 1), n * 0.52 + 3)
    b0, P = fit_grid(e, t, t0, n)
    out = []
    for k in range(n):
        g = b0 + k * P; m = (t > g - win) & (t < g + win)
        out.append(t[np.argmax(np.where(m, e, -1))])
    return np.array(out), b0, P
if __name__ == "__main__":
    h, b0, P = hits(sys.argv[1], float(sys.argv[2]), int(sys.argv[3]))
    print("b0 %.4f P %.4f bpm %.2f" % (b0, P, 60 / P)); print(np.round(h, 3)); print(np.round((h - (b0 + np.arange(len(h)) * P)) * 1000).astype(int))
# ---- méthode gabarit (robuste à la voix) : la boîte à rythmes est régulière, chaque temps a la même signature
# (kick ou caisse claire + charleston). On moyenne l'enveloppe des aigus (> 5 kHz) sur tous les temps, on recale chaque
# temps sur ce gabarit par corrélation (±40 ms), et l'attaque du gabarit (50 % de son max) donne la frappe.
import scipy.signal as ss
def hp_env(path, off, dur):
    y, _ = librosa.load(path, sr=SR, mono=True, offset=off, duration=dur)
    sos = ss.butter(4, 5000, btype="high", fs=SR, output="sos"); x = np.abs(ss.hilbert(ss.sosfiltfilt(sos, y)))
    x = np.convolve(x, np.ones(48) / 48, "same")
    return x
def template_hits(path, grid, off=None, pre=0.08, post=0.12, lag=0.04, parity=True):
    grid = np.asarray(grid, float); off = max(0.0, grid[0] - 0.5) if off is None else off
    x = hp_env(path, off, grid[-1] - off + 0.5)
    a, b, L = int(pre * SR), int(post * SR), int(lag * SR)
    x = np.concatenate([np.zeros(a + L), x, np.zeros(b + L)])        # marge (1re frappe à 0,02 s dans l'export)
    segs = []
    for g in grid:
        i = int(round((g - off) * SR)) + a + L; segs.append(x[i - a - L:i + b + L])
    segs = np.array(segs)
    out = np.zeros(len(grid))
    for par in ((0, 1) if parity else (None,)):              # gabarits séparés temps pairs (kick) / impairs (caisse claire)
        idx = [k for k in range(len(grid)) if par is None or k % 2 == par]
        tpl = np.median(segs[idx][:, L:L + a + b], 0)
        att = np.argmax(tpl >= 0.5 * tpl.max()) / SR - pre    # attaque du gabarit par rapport à la grille
        for _ in range(2):                                    # 2 passes : on réaligne puis on recalcule le gabarit
            lags = []
            for k in idx:
                c = np.correlate(segs[k], tpl, "valid"); lags.append((np.argmax(c) - L) / SR)
            al = np.array([segs[k][L + int(round(l * SR)):L + int(round(l * SR)) + a + b] for k, l in zip(idx, lags)])
            tpl = np.median(al, 0); att = np.argmax(tpl >= 0.5 * tpl.max()) / SR - pre
        for k, l in zip(idx, lags): out[k] = grid[k] + l + att
    return out
