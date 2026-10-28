# Sonde des frappes de Kordhell - Live Another Day : onsets par bande (kick < 120 Hz, snare/clap 1-5 kHz) sur une fenêtre.
import sys, numpy as np, soundfile as sf, scipy.signal as ss
y, sr = sf.read("/Users/luca.grousset/Movies/highkey-gauchiste/lot5/sons/I1-kordhell-live-another-day_complet.wav"); y = y.mean(1)
a, b = float(sys.argv[1]), float(sys.argv[2])
def env(band, kind):
    s = ss.sosfiltfilt(ss.butter(4, band, btype=kind, fs=sr, output='sos'), y[int(a*sr):int(b*sr)])
    h = int(0.005*sr); return 20*np.log10(np.array([np.sqrt(np.mean(s[i:i+h]**2)) for i in range(0, len(s)-h, h)])+1e-9)
for name, band, kind, thr in (("kick", 120, "low", 7), ("snare", [1000, 5000], "band", 7), ("mid", [200, 1000], "band", 7)):
    e = env(band, kind); d = e[4:] - e[:-4]; out = []; i = 0
    while i < len(d):
        if d[i] > thr:
            j = i + int(np.argmax(d[i:i+10])); out.append((round(a + (j+4)*0.005 - 0.01, 3), round(float(d[j]), 1), round(float(e[min(j+8, len(e)-1)]), 1))); i = j + 30
        else: i += 1
    print(name, [o for o in out])
