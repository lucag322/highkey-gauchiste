# mesure.py : sur l'export preview/apercu-A9.mp4, coupes (scdet) vs attaques réelles des kicks retrouvées dans le son de l'export ; LUFS / true peak.
import sys, subprocess, re, json, numpy as np
sys.argv = [sys.argv[0], "none"]
exec(open(__file__.replace("mesure.py", "genA9.py")).read().split("# ---------------- plans ----------------")[0])
AP = ROOT + "/preview/apercu-A9.mp4"; FFF = "/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg"
r = subprocess.run([FFF, "-i", AP, "-vf", "scdet=threshold=5", "-an", "-f", "null", "-"], capture_output=True, text=True).stderr
cuts = [float(x) for x in re.findall(r"lavfi.scd.time: ([0-9.]+)", r)]
p = subprocess.run([FF, "-v", "error", "-i", AP, "-ac", "2", "-ar", "48000", "-f", "f32le", "-"], capture_output=True)
y = np.frombuffer(p.stdout, np.float32).reshape(-1, 2)
plan = json.load(open(D + "plan-A9.json")); exp = sorted(set(v["rec"] / FPS for v in plan["video"]))[1:]
print("coupes attendues (plan) :", [round(e, 3) for e in exp])
worst = 0
for e in exp:
    if abs(e - PF / FPS) < 0.02: print("  %.3f  coupe hook -> phrase (la voix entre, pas une frappe)" % e); continue
    cs = [c for c in cuts if abs(c - e) <= 1.5 / FPS]
    if not cs: print("  %.3f  coupe non détectée par scdet (plans proches)" % e); c = e
    else: c = min(cs, key=lambda c: abs(c - e))
    k = kick_attacks(y, [c])[0]
    d = (c - k[0]) * 1000; worst = max(worst, abs(d))
    print("  coupe %.3f  kick %.4f (niv %.2f, +%.0f dB)  écart %+.1f ms" % (c, k[0], k[1], k[2], d))
print("écart max coupes/frappes : %.1f ms" % worst)
for f in (AP, OUT + "A9-mix.wav"):
    r = subprocess.run([FF, "-hide_banner", "-i", f, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    print(f.split("/")[-1], ":", " ".join(re.findall(r"(I:\s+-?[0-9.]+ LUFS|Peak:\s+-?[0-9.]+ dBFS)", r)[-2:]))
