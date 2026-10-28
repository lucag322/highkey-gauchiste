# Style 5 : cartons de texte (ProRes 4444 alpha), mix audio, plan5.json et aperçu ffmpeg 540x960.
# usage : python assemble5.py [txt] [audio] [plan] [preview]   (sans argument : tout)
import sys, os, json, subprocess, re
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
ROOT = "/Users/luca.grousset/Movies/highkey-gauchiste"; D = ROOT + "/_claude/gen/5"; OUT = D + "/out"
FF = "/opt/homebrew/bin/ffmpeg"; FPS = 30; W, H = 1080, 1920
sys.path.insert(0, D); sys.path.insert(0, ROOT + "/_claude/outils")
from gen5 import timeline, SLOW, SFPS
from fx import ease_out
SHOTS, TOTAL = timeline()
DROP = 5.99
# ---- voix : Mélenchon, Saint-Denis 7/06/2026, source 102,30-108,10 s, posée à 0,20 s (temps montage = source - 102,10)
V_IN, V_OUT, V_REC = 102.30, 108.10, 0.20
OFF = V_IN - V_REC
# Cartons = phrase réelle mot à mot : « Nous réparerons les dégâts, le SMIC passera à 1 700 euros »
# temps source (Whisper corrigé sur l'enveloppe du signal), rouge = mot-clé
CARDS = [
    ([("NOUS", 102.40, 0), ("RÉPARERONS", 102.62, 0)], 103.72),
    ([("LES", 103.75, 0), ("DÉGÂTS", 103.98, 0)], 105.25),
    ([("LE", 105.28, 0), ("SMIC", 105.40, 1)], 105.80),
    ([("PASSERA", 105.82, 0), ("À", 106.45, 0)], 106.72),
    ([("1\u202f700", 106.75, 1), ("EUROS", 107.50, 1)], OFF + DROP),
]
FONT = "/System/Library/Fonts/Supplemental/DIN Condensed Bold.ttf"
RED = (0xE4, 0x00, 0x2B, 255); WHITE = (255, 255, 255, 255)
YC = 1180; EM_MAX = 230; MAXW = 0.86 * W; STROKE = 10
def card_layout(words):
    em = EM_MAX
    while True:
        f = ImageFont.truetype(FONT, em); sp = f.getlength(" ")
        ws = [f.getlength(w) for w, _, _ in words]; tot = sum(ws) + sp * (len(ws) - 1)
        if tot <= MAXW or em < 80: break
        em -= 6
    x = W / 2 - tot / 2; pos = []
    for wd in ws: pos.append(x + wd / 2); x += wd + sp
    return em, pos
def render_txt():
    n = int(round(DROP * FPS)); d = D + "/seq_txt"; os.makedirs(d, exist_ok=True)
    for f in os.listdir(d): os.remove(os.path.join(d, f))
    lays = [card_layout(w) for w, _ in CARDS]
    for i in range(n):
        t = i / FPS + OFF
        im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sh = Image.new("L", (W, H), 0)
        dr = ImageDraw.Draw(im); ds = ImageDraw.Draw(sh)
        for (words, end), (em, pos) in zip(CARDS, lays):
            if not (words[0][1] <= t < end): continue
            for (w, ts, red), cx in zip(words, pos):
                if t < ts: continue
                k = (t - ts) * FPS
                sc = 1 + 0.22 * (1 - ease_out(k / 4))           # entrée 4 images, forte décélération, sans rebond
                f = ImageFont.truetype(FONT, max(10, int(round(em * sc))))
                dr.text((cx, YC), w, font=f, fill=RED if red else WHITE, anchor="mm", stroke_width=STROKE, stroke_fill=(0, 0, 0, 255))
                ds.text((cx + 6, YC + 8), w, font=f, fill=200, anchor="mm", stroke_width=STROKE + 6)
        sh = sh.filter(ImageFilter.GaussianBlur(10))
        base = Image.new("RGBA", (W, H), (0, 0, 0, 0)); base.putalpha(sh)
        Image.alpha_composite(base, im).save(d + "/f%04d.png" % i)
    subprocess.run([FF, "-v", "error", "-y", "-framerate", "30", "-i", d + "/f%04d.png", "-c:v", "prores_ks", "-profile:v", "4444",
                    "-pix_fmt", "yuva444p10le", "-vendor", "apl0", OUT + "/5_TXT.mov"], check=True)
    print("txt", n, "images")
# ---- audio
MUS = ROOT + "/sons/5-eclipser_depuis-ref.wav"; SRC = ROOT + "/sources/5-melenchon-saintdenis-smic.mp4"
G_VOICE = 12.4       # voix (-20,4 LUFS) -> ~ -8 : 2,4 dB sous la musique après le drop (-5,6 LUFS à -3 dB)
def lufs(path):
    o = subprocess.run([FF, "-hide_banner", "-nostats", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    s = o[o.rfind("Summary"):]
    return float(re.search(r"I:\s+(-?[\d.]+)", s).group(1)), float(re.search(r"Peak:\s+(-?[\d.]+)", s).group(1))
def render_audio():
    dur = TOTAL / FPS
    voice = OUT + "/5-voix.wav"; mus = OUT + "/5-musique.wav"; mix = OUT + "/5-mix.wav"
    vd = V_OUT - V_IN
    subprocess.run([FF, "-v", "error", "-y", "-ss", "%.3f" % V_IN, "-t", "%.3f" % vd, "-i", SRC, "-vn", "-af",
                    "afade=t=in:d=0.04,afade=t=out:st=%.3f:d=0.08,volume=%.1fdB,adelay=%d|%d,apad,atrim=0:%.4f,aresample=48000" % (vd - 0.08, G_VOICE, V_REC * 1000, V_REC * 1000, dur),
                    "-ac", "2", "-c:a", "pcm_s24le", voice], check=True)
    # musique -3 dB ; -4 dB de plus sous la voix (0,15-5,85 s), retour plein au drop ; fondu de 70 ms à la dernière image
    duck = "if(lt(t,0.15),0,if(lt(t,5.85),-4,if(lt(t,5.97),-4+4*(t-5.85)/0.12,0)))"
    subprocess.run([FF, "-v", "error", "-y", "-t", "%.4f" % dur, "-i", MUS, "-af",
                    "volume=-3dB,volume='pow(10,(%s)/20)':eval=frame,afade=t=out:st=%.4f:d=0.07,aresample=48000" % (duck, dur - 0.07),
                    "-ac", "2", "-c:a", "pcm_s24le", mus], check=True)
    tmp = OUT + "/_mix_raw.wav"
    subprocess.run([FF, "-v", "error", "-y", "-i", voice, "-i", mus, "-filter_complex", "amix=inputs=2:normalize=0:duration=longest",
                    "-c:a", "pcm_s24le", tmp], check=True)
    I, P = lufs(tmp); g = -14.0 - I
    subprocess.run([FF, "-v", "error", "-y", "-i", tmp, "-af", "volume=%.2fdB,alimiter=limit=0.84:level=false:attack=1:release=40" % g,
                    "-c:a", "pcm_s24le", "-ar", "48000", mix], check=True)
    os.remove(tmp)
    I2, P2 = lufs(mix); print("mix : gain %.1f dB -> %.1f LUFS, crête vraie %.1f dBFS" % (g, I2, P2))
    return g
# ---- plan5.json
SRCNAME = {"5-melenchon-saintdenis-smic.mp4": "Saint-Denis 07/06/2026 (YouTube JLM officielle 1dkY_JVFx9I)",
           "1-melenchon-valence-amfis.mp4": "Valence, AMFiS (chaîne JLM officielle)",
           "3-melenchon-huma-citation.mp4": "Fête de l'Huma (chaîne JLM officielle)"}
def write_plan(mix_gain=None):
    v = []
    for s in SHOTS:
        it = {"id": s["id"], "clip": "5_%s.mov" % s["id"], "folder": "gen5", "s": 0, "e": s["n"], "rec": s["rec"], "track": 1,
              "fx": "cuit dans le ProRes : recadrage 9:16 + étalonnage + " + s["fx"], "note": s["note"]}
        if s["src"]:
            it["source"] = "sources/" + s["src"]; it["source_desc"] = SRCNAME[s["src"]]
            it["source_tc_s"] = round(s["t"], 3); it["source_fps"] = SFPS[s["src"]]
        if s["id"] in SLOW:
            it["speed_pct"] = SLOW[s["id"]]; it["speed"] = SLOW[s["id"]]; it["retime"] = "optical_flow"
            it["note"] += " ; ProRes à vitesse normale (%d images), Resolve : SetSpeed %d %% + Optical Flow / Speed Warp" % (s["n"], SLOW[s["id"]])
        v.append(it)
    v.append({"id": "TXT", "clip": "5_TXT.mov", "folder": "gen5", "s": 0, "e": int(round(DROP * FPS)), "rec": 0, "track": 2, "composite": "Normal",
              "fx": "cartons mot à mot, alpha ProRes 4444", "note": "« Nous réparerons les dégâts, le SMIC passera à 1 700 euros » (SMIC, 1 700 EUROS en rouge)"})
    plan = {"name": "5 - Phonk infographie", "fps": FPS, "width": 1080, "height": 1920, "duration_frames": TOTAL,
            "ref": "refs/5-nvidia.rtx.2060.mp4", "music": {"file": "sons/5-eclipser_depuis-ref.wav", "gain_db": -3, "drop_s": DROP, "bpm": 145},
            "voice": {"source": "sources/5-melenchon-saintdenis-smic.mp4", "in_s": V_IN, "out_s": V_OUT, "rec_s": V_REC,
                      "texte": "Nous réparerons les dégâts, le SMIC passera à 1 700 euros"},
            "video": v,
            "audio": [{"id": "mix", "clip": "5-mix.wav", "folder": "gen5", "rec": 0, "track": 1, "note": "mix final -14 LUFS, crête < -1 dBFS"},
                      {"id": "voix", "clip": "5-voix.wav", "folder": "gen5", "rec": 0, "track": 2, "mute": True, "note": "stem (déjà dans le mix)"},
                      {"id": "musique", "clip": "5-musique.wav", "folder": "gen5", "rec": 0, "track": 3, "mute": True, "note": "stem (déjà dans le mix)"}],
            "gen_folder": "_claude/gen/5/out"}
    if mix_gain is not None: plan["mix_gain_db"] = round(mix_gain, 2)
    json.dump(plan, open(ROOT + "/_claude/plan5.json", "w"), indent=1, ensure_ascii=False)
    print("plan5.json", len(v), "items")
# ---- aperçu ffmpeg 540x960 (ralenti de l'aperçu seulement : setpts)
def preview():
    args = [FF, "-v", "error", "-y"]; fl = []; k = 0
    for s in SHOTS:
        args += ["-i", OUT + "/5_%s.mov" % s["id"]]
        if s["id"] in SLOW:
            f = SLOW[s["id"]] / 100.0; m = int(round(s["n"] * f))
            fl.append("[%d:v]trim=end_frame=%d,setpts=(PTS-STARTPTS)/%g,fps=30,trim=end_frame=%d,setpts=PTS-STARTPTS,scale=540:960,setsar=1[v%d]" % (k, m, f, s["n"], k))
        else:
            fl.append("[%d:v]trim=end_frame=%d,setpts=PTS-STARTPTS,scale=540:960,setsar=1[v%d]" % (k, s["n"], k))
        k += 1
    fl.append("".join("[v%d]" % i for i in range(k)) + "concat=n=%d:v=1:a=0,format=yuv420p[cv]" % k)
    args += ["-i", OUT + "/5_TXT.mov", "-i", OUT + "/5-mix.wav"]
    fl.append("[%d:v]scale=540:960,format=yuva420p[tx];[cv][tx]overlay=0:0:eof_action=pass:format=auto,format=yuv420p[ov]" % k)
    out = ROOT + "/exports/apercu-5-phonk.mp4"
    args += ["-filter_complex", ";".join(fl), "-map", "[ov]", "-map", "%d:a" % (k + 1), "-r", "30", "-c:v", "libx264", "-crf", "18", "-preset", "medium",
             "-c:a", "aac", "-b:a", "256k", "-shortest", "-movflags", "+faststart", out]
    subprocess.run(args, check=True); print(out)
if __name__ == "__main__":
    a = set(sys.argv[1:]) or {"txt", "audio", "plan", "preview"}
    g = None
    if "txt" in a: render_txt()
    if "audio" in a: g = render_audio()
    if "plan" in a: write_plan(g)
    if "preview" in a: preview()
