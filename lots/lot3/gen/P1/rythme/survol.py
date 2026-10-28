import numpy as np, librosa, scipy.signal as ss, sys
y, sr = librosa.load(sys.argv[1], sr=22050, mono=True)
tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
print("tempo", tempo, "dur", len(y)/sr)
sub = ss.sosfiltfilt(ss.butter(4, [30, 120], "bandpass", fs=sr, output="sos"), y)
hi = ss.sosfiltfilt(ss.butter(4, 2000, "high", fs=sr, output="sos"), y)
for t in np.arange(0, len(y)/sr, 1.0):
    a, b = int(t*sr), int((t+1)*sr)
    r = lambda x: 20*np.log10(np.sqrt(np.mean(x[a:b]**2))+1e-9)
    print("%5.1f all %6.1f sub %6.1f hi %6.1f" % (t, r(y), r(sub), r(hi)))
