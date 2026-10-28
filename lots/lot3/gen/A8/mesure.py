# mesure.py : sur l'export preview/apercu-A8.mp4, coupes (scdet) vs frappes réelles détectées dans le son de l'export ; LUFS / true peak.
import sys, subprocess, re, json, numpy as np
sys.argv = [sys.argv[0]]
exec(open(__file__.replace("mesure.py", "genA8.py")).read().split("# ---------------- plans ----------------")[0].split("# montage après le drop")[0])
AP = ROOT + "/preview/apercu-A8.mp4"; FFF = "/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg"
r = subprocess.run([FFF, "-i", AP, "-vf", "scdet=threshold=5", "-an", "-f", "null", "-"], capture_output=True, text=True).stderr
cuts = [float(x) for x in re.findall(r"lavfi.scd.time: ([0-9.]+)", r)]
p = subprocess.run([FF, "-v", "error", "-i", AP, "-ac", "2", "-ar", "48000", "-f", "f32le", "-"], capture_output=True)
y = np.frombuffer(p.stdout, np.float32).reshape(-1, 2)
hits = detect_hits(y)
plan = json.load(open(D + "plan-A8.json")); exp = sorted(set(v["rec"] / FPS for v in plan["video"]))[1:]
print("coupes attendues (plan) :", [round(e, 3) for e in exp])
worst = 0
for e in exp:                                   # coupe du plan retrouvée dans l'export (scdet ±1 image ; flashs/flous d'entrée ignorés)
    if abs(e - PF / FPS) < 0.02: print("  %.3f  coupe hook -> phrase (la voix entre, pas une frappe)" % e); continue
    cs = [c for c in cuts if abs(c - e) <= 1.5 / FPS]
    if not cs: print("  %.3f  coupe non détectée par scdet (plans proches)" % e); c = e
    else: c = min(cs, key=lambda c: abs(c - e))
    if abs(e - next(v["rec"] for v in plan["video"] if v["id"].startswith("drapeau")) / FPS) < 0.02:              # frappe du break (pas de kick) : attaque large bande, 30 % du sommet local
        mm = y.mean(1); a0 = int((c - 0.15) * 48000); seg = mm[a0:a0 + int(0.3 * 48000)]
        r = np.sqrt(np.convolve(seg ** 2, np.ones(240) / 240, "same"))          # RMS glissant 5 ms
        i = next(i for i in range(2880, len(r)) if r[i] > 1.8 * r[i - 2880:i - 480].mean())   # +5 dB sur les 60 ms d'avant
        h = (c - 0.15 + i / 48000, "break large bande")
    else: h = min(hits, key=lambda h: abs(h[0] - c))
    d = (c - h[0]) * 1000; worst = max(worst, abs(d))
    print("  coupe %.3f  frappe %.4f (%s)  écart %+.1f ms" % (c, h[0], h[1], d))
print("écart max coupes/frappes : %.1f ms" % worst)
r = subprocess.run([FF, "-hide_banner", "-i", AP, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
print("export :", " ".join(re.findall(r"(I:\s+-?[0-9.]+ LUFS|Peak:\s+-?[0-9.]+ dBFS)", r)[-2:]))
r = subprocess.run([FF, "-hide_banner", "-i", OUT + "A8-mix.wav", "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
print("mix wav :", " ".join(re.findall(r"(I:\s+-?[0-9.]+ LUFS|Peak:\s+-?[0-9.]+ dBFS)", r)[-2:]))
