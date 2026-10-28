# Frappes réelles (méthode A2 lot 2) : kick < 150 Hz (instant pris sur le clic 150-1500 Hz), caisse/clap > 1,5 kHz.
import sys, numpy as np, soundfile as sf, scipy.signal as ss, librosa
def detect_hits(y, sr=48000, delta=0.15):
    m = y.mean(1) if y.ndim > 1 else y; out = []
    def envel(typ, fc):
        return np.convolve(np.abs(ss.hilbert(ss.sosfiltfilt(ss.butter(4, fc, typ, fs=sr, output="sos"), m))), np.ones(96) / 96, "same")
    def attack(env, c):
        thr = 0.3 * env[c]; i = c
        while i > c - int(0.06 * sr) and i > 0 and env[i - 1] > thr: i -= 1
        return i
    clic = envel("bp", [150, 1500])
    for band, (typ, fc) in (("kick", ("lp", 150)), ("caisse", ("hp", 1500))):
        env = envel(typ, fc)
        hop = 128; e = env[::hop]; d = np.maximum(0, np.diff(e, prepend=e[0])); d /= d.max()
        for p in librosa.util.peak_pick(d, pre_max=20, post_max=20, pre_avg=40, post_avg=40, delta=delta, wait=40):
            c0 = p * hop; lo, hi = max(0, c0 - int(0.01 * sr)), min(len(env), c0 + int(0.05 * sr))
            i = attack(env, lo + int(np.argmax(env[lo:hi])))
            if band == "kick":
                lo, hi = max(0, i - int(0.06 * sr)), i + int(0.01 * sr); c = lo + int(np.argmax(clic[lo:hi]))
                if clic[c] > 2 * np.median(clic[max(0, lo - int(0.1 * sr)):lo]): i = attack(clic, c)
            pk = float(env[lo:hi].max()) if hi > lo else 0
            out.append((round(i / sr, 4), band, round(float(d[p]), 2)))
    return sorted(out)
if __name__ == "__main__":
    f, t0, t1 = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
    x, sr = sf.read(f, dtype="float32"); y = x[int(t0 * sr):int(t1 * sr)]
    for t, b, s in detect_hits(y, sr): print("%.3f %-6s %.2f" % (t + t0, b, s))
