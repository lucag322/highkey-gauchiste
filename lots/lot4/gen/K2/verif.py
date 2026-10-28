# Vérif de l'export : coupes (différence d'images) vs frappes mesurées dans l'audio de l'export ; LUFS / true peak.
import sys, json, subprocess, numpy as np, librosa
EXP = "/Users/luca.grousset/Movies/highkey-gauchiste/preview/apercu-K2.mp4"; FF = "/opt/homebrew/bin/ffmpeg"
D = "/Users/luca.grousset/Movies/highkey-gauchiste/lot4/_claude/gen/K2/"
raw = subprocess.run([FF, "-v", "error", "-i", EXP, "-vf", "scale=90:160", "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True).stdout
fr = np.frombuffer(raw, np.uint8).reshape(-1, 160, 90).astype(np.float32)
dif = np.abs(np.diff(fr, axis=0)).mean(axis=(1, 2))
plan = json.load(open(D + "plan-K2.json")); recs = [v["rec"] for v in plan["video"]][1:]
cuts = []
for r in recs:   # coupe attendue à l'image r : chercher le pic de différence à ±2 images
    k = max(range(r - 3, r + 2), key=lambda i: dif[i]); cuts.append((k + 1) / 30)
sr = 48000
y = np.frombuffer(subprocess.run([FF, "-v", "error", "-i", EXP, "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"], capture_output=True).stdout, np.float32)
mus = np.frombuffer(subprocess.run([FF, "-v", "error", "-i", D + "out/K2-musique.wav", "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"], capture_output=True).stdout, np.float32)
hop = 48; worst = 0; lines = []
import scipy.signal as ss
b_, a_ = ss.butter(4, 110 / (sr / 2)); ylo = ss.filtfilt(b_, a_, y).astype(np.float32)
for name, sig in (("export", y), ("export < 110 Hz (kick/basse)", ylo), ("musique seule", mus)):
    env = librosa.onset.onset_strength(y=sig, sr=sr, hop_length=hop, n_mels=64)
    errs = []
    for c in cuts:
        i0, i1 = int((c - 0.06) * sr / hop), int((c + 0.06) * sr / hop)
        p = (i0 + int(np.argmax(env[i0:i1]))) * hop / sr; errs.append((c - p) * 1000)
    lines.append("%s : écarts coupe-frappe (ms) %s ; max |%.0f|" % (name, " ".join("%+.0f" % e for e in errs), max(abs(e) for e in errs)))
print("coupes (s) :", " ".join("%.3f" % c for c in cuts)); print("\n".join(lines))
r = subprocess.run([FF, "-v", "info", "-i", EXP, "-af", "loudnorm=print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
js = json.loads(r[r.rindex("{"):r.rindex("}") + 1]); print("export : %s LUFS, true peak %s dBTP" % (js["input_i"], js["input_tp"]))
print("durée", subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", EXP], capture_output=True, text=True).stdout.strip())
