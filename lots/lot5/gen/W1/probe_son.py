# Sonde Love Sosa : tempo + frappes (kick < 150 Hz, caisse > 1,5 kHz) autour du 1er refrain.
import sys, numpy as np, soundfile as sf, librosa, scipy.signal as ss
F = "/Users/luca.grousset/Movies/highkey-gauchiste/lot5/sons/W1-chiefkeef-lovesosa_complet.wav"
a, b = float(sys.argv[1]), float(sys.argv[2])
x, sr = sf.read(F, dtype="float32"); m = x[int(a*sr):int(b*sr)].mean(1)
tempo, beats = librosa.beat.beat_track(y=m, sr=sr, hop_length=256)
print("tempo", tempo, "beats", np.round(a + librosa.frames_to_time(beats, sr=sr, hop_length=256), 3).tolist())
for name, typ, fc in (("kick", "lp", 150), ("caisse", "hp", 1500), ("mid", "bp", [300, 1500])):
    env = np.convolve(np.abs(ss.hilbert(ss.sosfiltfilt(ss.butter(4, fc, typ, fs=sr, output="sos"), m))), np.ones(96)/96, "same")
    hop = 128; e = env[::hop]; d = np.maximum(0, np.diff(e, prepend=e[0])); d /= d.max()
    pk = librosa.util.peak_pick(d, pre_max=20, post_max=20, pre_avg=40, post_avg=40, delta=0.15, wait=30)
    print(name, [(round(a + p*hop/sr, 3), round(float(d[p]), 2)) for p in pk])
rms = librosa.feature.rms(y=m, hop_length=4800)[0]
print("rms/0.1s", " ".join("%.2f" % v for v in rms))
