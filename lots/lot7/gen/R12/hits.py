# Frappes réelles de 13Organisé – Bande organisée (copie de lot5 R1/hits.py) : kick (< 150 Hz, instant pris sur le clic 150-1500 Hz) et caisse (> 1,5 kHz), attaque à 30 % (copie genA8.detect_hits)
import sys, json, numpy as np, soundfile as sf, scipy.signal as ss, librosa
SON = "/Users/luca.grousset/Movies/highkey-gauchiste/lot7/sons/R12-bande-organisee_complet.wav"
def detect_hits(y, sr=48000):
    m = y.mean(1); out = []
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
        for p in librosa.util.peak_pick(d, pre_max=20, post_max=20, pre_avg=40, post_avg=40, delta=0.15, wait=40):
            c0 = p * hop; lo, hi = max(0, c0 - int(0.01 * sr)), min(len(env), c0 + int(0.05 * sr))
            i = attack(env, lo + int(np.argmax(env[lo:hi])))
            lvl = float(env[min(len(env) - 1, i + int(0.03 * sr))])
            if band == "kick":
                lo, hi = max(0, i - int(0.06 * sr)), i + int(0.01 * sr); c = lo + int(np.argmax(clic[lo:hi]))
                if clic[c] > 2 * np.median(clic[max(0, lo - int(0.1 * sr)):lo]): i = attack(clic, c)
            out.append((round(i / sr, 4), band, round(float(d[p]), 2), round(lvl, 3)))
    return sorted(out)
def raw(t0, dur, path=SON):
    info = sf.info(path); i0 = int(round(t0 * info.samplerate))
    x, r = sf.read(path, start=i0, frames=int(dur * r if False else dur * info.samplerate), dtype="float32"); return x
if __name__ == "__main__":
    a, b = float(sys.argv[1]), float(sys.argv[2])
    for t, band, s, l in detect_hits(raw(a, b - a)):
        print("%8.4f %-6s %.2f %.3f" % (t + a, band, s, l))
