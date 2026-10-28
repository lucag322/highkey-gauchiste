import numpy as np, librosa, scipy.signal as ss, sys
f, t0, t1 = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
y, sr = librosa.load(f, sr=48000, mono=True, offset=t0, duration=t1-t0)
def env(lo, hi):
    x = ss.sosfiltfilt(ss.butter(4, [lo, hi], "bandpass", fs=sr, output="sos"), y)
    e = np.abs(ss.hilbert(x)); w = int(.004*sr); return np.convolve(e, np.ones(w)/w, "same")[::48]
for lo, hi, n in [(30,120,"sub"),(1500,5000,"mid-hi"),(6000,14000,"hats")]:
    e = env(lo, hi); pk, pr = ss.find_peaks(e, distance=90, prominence=np.percentile(e, 99)*0.3)
    out = []
    for p in pk:
        pre = e[max(p-60,0):max(p-25,1)].mean()
        if e[p] < 1.6*pre: continue
        i = p
        while i > p-80 and e[i] > pre + 0.2*(e[p]-pre): i -= 1
        out.append("%.3f(%.2f)" % (t0 + i/1000, e[p]/np.percentile(e,99)))
    print(n, len(out)); print(" ".join(out))
