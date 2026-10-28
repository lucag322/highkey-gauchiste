# mesure.py : sur l'export preview/apercu-W1.mp4, coupes (scdet) vs attaques réelles retrouvées dans le son de l'export ; LUFS / true peak.
import sys, subprocess, re, json, numpy as np
src = open(__file__.replace("mesure.py", "genW1.py")).read().split("MUSIC_IN, CC, PREH = frappes()")[0]
exec(src)
AP = ROOT + "/preview/apercu-W1.mp4"; FFF = "/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg"
r = subprocess.run([FFF, "-i", AP, "-vf", "scdet=threshold=5", "-an", "-f", "null", "-"], capture_output=True, text=True).stderr
cuts = [float(x) for x in re.findall(r"lavfi.scd.time: ([0-9.]+)", r)]
p = subprocess.run([FF, "-v", "error", "-i", AP, "-ac", "2", "-ar", "48000", "-f", "f32le", "-"], capture_output=True)
y = np.frombuffer(p.stdout, np.float32).reshape(-1, 2)
plan = json.load(open(D + "plan-W1.json")); exp = sorted(set(v["rec"] / FPS for v in plan["video"]))[1:]
import soundfile as sf_
ym, _ = sf_.read(OUT + "W1-musique.wav", dtype="float32")        # avant le drop : voix + clameur par-dessus, on mesure sur la piste musique posée
worst = 0; worst_post = 0
for e in exp:
    cs = [c for c in cuts if abs(c - e) <= 1.5 / FPS]
    c = min(cs, key=lambda c: abs(c - e)) if cs else e
    k = attacks(y if e > DROP - 0.1 else ym, [c])[0]; d = (c - k[0]) * 1000; worst = max(worst, abs(d))
    if e > DROP - 0.1: worst_post = max(worst_post, abs(d))
    print("  coupe %.3f%s  frappe %.4f (%s, +%.0f dB)  écart %+.1f ms" % (c, "" if cs else " (non détectée)", k[0], k[1], k[2], d))
print("écart max coupes/frappes : %.1f ms (après le drop : %.1f ms)" % (worst, worst_post))
for f in (AP, OUT + "W1-mix.wav"):
    r = subprocess.run([FF, "-hide_banner", "-i", f, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    print(f.split("/")[-1], ":", " ".join(re.findall(r"(I:\s+-?[0-9.]+ LUFS|Peak:\s+-?[0-9.]+ dBFS)", r)[-2:]))
print("durée", subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",AP],capture_output=True,text=True).stdout.strip())
