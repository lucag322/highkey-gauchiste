# A3 — Aura N&B, Sophia Chikirou (remplace Rima Hassan), lot 2. Modèle : _claude/gen/1/gen1.py (test 1 validé par Luca).
# Aperçu HORS Resolve : plans ProRes 9:16 recadrés (visage suivi, Apple Vision), N&B contrasté + bloom + grain, texte cuit sur le plan parlé.
# Ralentis PAS précalculés : clip à vitesse normale, speed_pct + retime optical_flow dans plan-A3.json (aperçu = setpts simple).
# Usage : python genA3.py [shots] [cards] [audio] [plan] [apercu]   (sans argument = tout)
import sys, os, json, subprocess, math
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
ROOT = "/Users/luca.grousset/Movies/highkey-gauchiste"; LOT = ROOT + "/lot2"
sys.path.insert(0, ROOT + "/_claude/outils")
import framing
from framing import plan_views
from fx import gblur, motion_blur, vignette, to8, ease_out
D = LOT + "/_claude/gen/A3/"; OUT = D + "out/"; os.makedirs(OUT, exist_ok=True)
framing.ROOT = LOT; framing.CACHE = D + "cache"                    # detect() lit LOT/sources/<src>
FF = "/opt/homebrew/bin/ffmpeg"; FPS = 30; W, H = 1080, 1920
RED = (0xE4, 0x00, 0x2B); WHITE = (255, 255, 255)
F_BLACK = "/System/Library/Fonts/Supplemental/Arial Black.ttf"
F_AURA = ("/System/Library/Fonts/Helvetica.ttc", 2)                # Helvetica Oblique (« aura. » du test 1)
SA, SC = "A3-chikirou-paris-a.mp4", "A3-chikirou-paris-c.mp4"     # (paris-b.mp4 = Manuel Bompard, mauvais fichier : non utilisé)
SRCFPS = {SA: 30000 / 1001, SC: 30000 / 1001}
BOUNDS = {SA: (0, 0, 1540, 1080), SC: (0, 0, 1540, 1080)}          # exclut le logo MÉLENCHON 2027 (haut droite, x > 1560)
# ---------------- grille musicale (sons-lot2.json A3 : DVRST Close Eyes, 96,2 BPM, drop 6,027 s dans l'extrait) ----------------
SON = [x for x in json.load(open(LOT + "/_claude/sons-lot2.json"))["sons"] if x["id"] == "A3"][0]
MUS_IN = SON["downbeats_s"][0]                                     # on démarre l'extrait sur un downbeat (1,035 s) : intro plus courte
BEATS = [b - MUS_IN for b in SON["beats_s"] if b >= MUS_IN - 0.01]
DROP = SON["drop_s"] - MUS_IN                                      # 4,992 s timeline
BEAT = 60 / SON["bpm"]
def beat(k): return DROP + k * BEAT                                # k entier = temps après le drop (k % 4 == 0 = downbeat)
def fr(t): return int(round(t * FPS))
END = beat(16)                                                     # 14,97 s (règle Luca : 15 s max)
# ---------------- phrase (derush-AG A3, mot à mot) ----------------
PH = json.load(open(LOT + "/_claude/derush-AG.json"))["figures"]["A3"]["phrase"]
WORDS = [(w["start"], w["w"].rstrip(".").upper()) for w in PH["mots"]]   # NOUS APPELONS AU DÉBORDEMENT POPULAIRE
LONG_END = 27.90                                                   # coupe régie à 27,93 s dans paris-c : on s'arrête avant
LONG_T0 = LONG_END - (DROP - beat(-6))                             # plan long = 6 temps avant le drop (après la carte « aura. » de 2 temps)
# ---------------- plans ----------------
SHOTS = {
    "long":      dict(src=SC, t=LONG_T0, face=(980, 300), zoom=(1.0, 1.08), why="« Nous appelons au débordement populaire. » (bras ouverts, pupitre PARIS)"),
    "pointe":    dict(src=SA, t=50.75, face=(960, 300), zoom=(1.0, 1.06), why="doigt pointé vers la salle"),
    "drapeaux":  dict(src=SA, t=4.0,   fixed=(860, 540), zoom=(1.0, 1.05), why="salle, drapeaux tricolores levés"),
    "bras":      dict(src=SC, t=22.95, face=(1000, 300), zoom=(1.0, 1.06), why="bras levé, feuilles en main"),
    "foule":     dict(src=SC, t=12.0,  fixed=(960, 540), zoom=(1.0, 1.05), why="salle comble"),
    "scene":     dict(src=SC, t=29.0,  fixed=(940, 470), zoom=(1.35, 1.42), speed=60, why="plan large de la scène, pupitre"),
    "index":     dict(src=SA, t=30.9,  face=(960, 300), zoom=(1.0, 1.06), why="index levé"),
    "mains":     dict(src=SC, t=6.0,   face=(980, 300), zoom=(1.0, 1.06), why="gros plan, mains jointes"),
    "foule_fond": dict(src=SC, t=35.0, fixed=(960, 540), zoom=(1.0, 1.04), speed=60, why="salle depuis le fond, lumières"),
    "sourire":   dict(src=SC, t=43.6,  face=(980, 300), zoom=(1.0, 1.06), why="sourire, mains jointes"),
    "foule2":    dict(src=SA, t=41.0,  fixed=(960, 540), zoom=(1.0, 1.05), why="salle immense"),
    "parle":     dict(src=SA, t=47.5,  face=(960, 300), zoom=(1.0, 1.06), why="parole, regard salle"),
    "scene2":    dict(src=SA, t=57.0,  fixed=(960, 430), zoom=(1.35, 1.42), why="plan large de la scène éclairée"),
}
# montage après le drop : (id, nb de temps, effet d'entrée) -- 16 temps = 4 mesures, structure du test 1
EDIT = [("pointe", 1, "drop"), ("drapeaux", 1, "whip"), ("bras", 1, "whip"), ("foule", 1, "whip"),       # mesure 1
        ("scene", 2, "cut"), ("aura", 1, "cut"), ("index", 1, "cut"),                                   # mesure 2
        ("mains", 1, "drop"), ("foule_fond", 1, "whip"), ("sourire", 1, "whip"), ("foule2", 1, "whip"), # mesure 3
        ("parle", 1, "whip"), ("scene2", 1, "whip"), ("fin", 2, "cut")]                                 # mesure 4 (carte de fin)
# ---------------- look N&B (identique au test 1) ----------------
RNG = np.random.default_rng(11)
def grade(bgr):
    g = (0.114 * bgr[..., 0] + 0.587 * bgr[..., 1] + 0.299 * bgr[..., 2])
    g = np.clip((g - 0.07) / 0.85, 0, 1) ** 0.85          # gamma 0,85 : salle sombre, on remonte un peu les visages
    g = 0.45 * g + 0.55 * (g * g * (3 - 2 * g))
    small = cv2.resize(g, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    hi = np.clip(small - 0.55, 0, None) * 2.0
    glow = cv2.resize(cv2.GaussianBlur(hi, (0, 0), 9), (W, H)) * 0.45
    soft = cv2.resize(cv2.GaussianBlur(small, (0, 0), 4), (W, H))
    g = 1 - (1 - g) * (1 - 0.18 * soft) + glow
    g = vignette(g[..., None], 0.38, 2.4)[..., 0]
    g = 0.008 + np.clip(g, 0, 1) * 0.86
    g = g + RNG.normal(0, 0.018, g.shape).astype(np.float32)
    return np.repeat(np.clip(g, 0, 1)[..., None], 3, 2)
# ---------------- lecture source ----------------
def read_frames(src, t, n_out):
    sf = SRCFPS[src]; cap = cv2.VideoCapture(LOT + "/sources/" + src)
    s0 = int(round(t * sf)); cap.set(cv2.CAP_PROP_POS_FRAMES, s0)
    need = [int(round(i * sf / FPS)) for i in range(n_out)]; buf = []; k = 0
    while k <= need[-1]:
        ok, f = cap.read()
        if not ok: break
        buf.append(f); k += 1
    return [buf[min(i, len(buf) - 1)].astype(np.float32) / 255 for i in need], s0
def crop_916(img, cx, cy, vh):
    vw = vh * 9 / 16; s = W / vw
    M = np.float32([[s, 0, W / 2 - cx * s], [0, s, H / 2 - cy * s]])
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
# ---------------- texte (Arial Black, mot-clé rouge, contour noir + ombre douce, sans guillemets) ----------------
def font(path, size, idx=0): return ImageFont.truetype(path, size, index=idx)
def fit_size(txt, maxw, start=260):
    s = start
    while font(F_BLACK, s).getlength(txt) > maxw: s -= 4
    return s
def text_layer(lines, alpha_scale=1.0, scale=1.0):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay); ds = ImageDraw.Draw(sh)
    for txt, col, size, yc in lines:
        f = font(F_BLACK, max(8, int(size * scale)))
        sw = max(4, int(size * 0.045))
        x0, y0, x1, y1 = d.textbbox((0, 0), txt, font=f, stroke_width=sw)
        x = (W - (x1 - x0)) / 2 - x0; y = yc - (y1 - y0) / 2 - y0
        ds.text((x, y + size * 0.05), txt, font=f, fill=(0, 0, 0, 200), stroke_width=sw * 3, stroke_fill=(0, 0, 0, 200))
        d.text((x, y), txt, font=f, fill=col + (255,), stroke_width=sw, stroke_fill=(0, 0, 0, 255))
    sh = sh.filter(ImageFilter.GaussianBlur(18))
    a = np.asarray(Image.alpha_composite(sh, lay)).astype(np.float32) / 255
    a[..., 3] *= alpha_scale
    return a
def over_rgba(img_bgr, rgba):
    a = rgba[..., 3:4]; rgb = rgba[..., 2::-1]
    return img_bgr * (1 - a) + rgb * a
SB = fit_size("DÉBORDEMENT", 1000)                                  # mot-clé rouge pleine largeur
SP = min(fit_size("POPULAIRE", 1000), int(SB * 1.2))
SA_ = fit_size("APPELONS", 960)
Y0 = 1080
def layout(card):
    """Carton 1 : NOUS / APPELONS. Carton 2 : AU / DÉBORDEMENT (rouge) / POPULAIRE. (temps d'apparition, ligne)"""
    if card == 1:
        return [(WORDS[0][0], ("NOUS", WHITE, 115, Y0)), (WORDS[1][0], ("APPELONS", WHITE, SA_, Y0 + 60 + SA_ * 0.6))]
    sa = int(SB * 0.8); y1 = Y0 + sa * 0.5 + 30 + SB * 0.55
    return [(WORDS[2][0], ("AU", WHITE, sa, Y0)), (WORDS[3][0], ("DÉBORDEMENT", RED, SB, y1)),
            (WORDS[4][0], ("POPULAIRE", WHITE, SP, y1 + SB * 0.55 + 22 + SP * 0.55))]
def long_text(t_src):
    card = 1 if t_src < WORDS[2][0] else 2
    items = [(t0, ln) for t0, ln in layout(card) if t_src >= t0]
    if not items: return None
    last = items[-1][0]; k = (t_src - last) * FPS; e = ease_out(min(k / 3.0, 1.0))       # entrée 3 images, sans rebond
    top = text_layer([items[-1][1]], alpha_scale=min(1.0, 0.35 + e), scale=1.12 - 0.12 * e)
    if len(items) == 1: return top
    base = text_layer([ln for _, ln in items[:-1]])
    a = top[..., 3:4]; out = base * (1 - a) + top * a; out[..., 3:4] = np.maximum(base[..., 3:4], a); return out
# ---------------- rendu ----------------
def write_mov(frames, path, fps=FPS):
    p = subprocess.Popen([FF, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", "%dx%d" % (W, H), "-r", str(fps), "-i", "-",
                          "-c:v", "prores_ks", "-profile:v", "3", "-pix_fmt", "yuv422p10le", "-vendor", "apl0", path], stdin=subprocess.PIPE)
    for f in frames: p.stdin.write(to8(f).tobytes())
    p.stdin.close(); p.wait()
def timeline():
    """[(id, shot, rec, n, effet, temps)] : intro carte, plan long, puis EDIT sur la grille."""
    tl = [("hook", "aura", 0, fr(beat(-6)), "card", 2), ("long", "long", fr(beat(-6)), fr(DROP) - fr(beat(-6)), "cut", 6)]
    k = 0
    for sid, nb, eff in EDIT:
        a, b = fr(beat(k)), fr(beat(k + nb)); tl.append((sid if sid not in ("aura", "fin") else "%s_%d" % (sid, a), sid, a, b - a, eff, nb)); k += nb
    return tl
def render_shot(sid, n, eff):
    sh = SHOTS[sid]; src = sh["src"]; sf = SRCFPS[src]
    raw, s0 = read_frames(src, sh["t"], n)
    z0, z1 = sh["zoom"]; zoom = lambda f: z0 + (z1 - z0) * f / max(n - 1, 1)
    if "fixed" in sh:
        views, _ = plan_views(src, s0, n, sf, speed=sf / FPS, bounds=BOUNDS[src], vh=1080, zoom=zoom, fixed=sh["fixed"])
    else:
        views, ok = plan_views(src, s0, n, sf, speed=sf / FPS, hint=sh["face"], bounds=BOUNDS[src], vh=1080, zoom=zoom, top=0.12)
        if not ok: print("  ! pas de visage détecté :", sid)
    frames = []
    for i, (img, (cx, cy, vh)) in enumerate(zip(raw, views)):
        g = grade(crop_916(img, cx, cy, vh))
        if sid == "long":
            tl_ = long_text(sh["t"] + i / FPS)
            if tl_ is not None: g = over_rgba(g, tl_)
        if eff == "whip" and i < 3: g = motion_blur(g, 0, [220, 90, 25][i], steps=16)       # flou de filé vertical 3 images
        if eff == "drop" and i < 8:                                                         # bloom d'exposition au drop (pas de blanc)
            k = (1 - i / 8) ** 2; g = np.clip(g + k * 0.55 + gblur(g, 25) * k * 0.6, 0, 1)
        frames.append(g)
    write_mov(frames, OUT + "A3_%s.mov" % sid)
    print("  plan", sid, n, "images, vue0", tuple(round(v) for v in views[0]), "vue fin", tuple(round(v) for v in views[-1]))
def aura_card(n, fade_in=3, fade_out=0):
    im = Image.new("L", (W, H), 0); d = ImageDraw.Draw(im); f = font(F_AURA[0], 120, F_AURA[1])
    tw = d.textlength("aura.", font=f); d.text(((W - tw) / 2, H / 2 - 80), "aura.", font=f, fill=255)
    a = np.asarray(im).astype(np.float32) / 255
    base = np.clip(a * 0.92 + gblur(a, 22) * 0.9 + gblur(a, 6) * 0.5, 0, 0.95)
    out = []
    for i in range(n):
        k = 1.0
        if fade_in and i < fade_in: k = ease_out((i + 1) / fade_in)
        if fade_out and i >= n - fade_out: k = (n - i) / fade_out
        out.append(np.repeat((0.008 + base * k)[..., None], 3, 2))
    return out
def make_cards():
    for id_, sid, rec, n, eff, nb in timeline():
        if sid == "aura": write_mov(aura_card(n), OUT + "A3_%s.mov" % id_)
        if sid == "fin": write_mov(aura_card(n, fade_in=3, fade_out=7), OUT + "A3_%s.mov" % id_)   # sortie 7 images max
# ---------------- plan ----------------
def build_plan():
    video = []
    for id_, sid, rec, n, eff, nb in timeline():
        v = {"id": id_, "clip": "A3_%s.mov" % id_, "folder": "A3", "path": OUT + "A3_%s.mov" % id_, "s": 0, "e": n, "clip_fps": FPS,
             "rec": rec, "dur": n, "track": 1, "temps": nb}
        if sid in SHOTS:
            sh = SHOTS[sid]
            v.update({"kind": "shot", "effet": eff, "note": sh["why"],
                      "source": {"fichier": "lot2/sources/" + sh["src"], "in_s": round(sh["t"], 3), "out_s": round(sh["t"] + n / FPS, 3)}})
            if sh.get("speed"): v.update({"speed_pct": sh["speed"], "retime": "optical_flow"})
        else:
            v.update({"kind": "card", "note": "carte aura. (Helvetica Oblique, halo doux)"})
        video.append(v)
    plan = {"name": "A3 - Aura N&B - Chikirou", "fps": FPS, "w": W, "h": H, "duree_s": round(END, 3),
            "note": "Aperçu lot 2. Plans ProRes 9:16 prêts (recadrés visage suivi, N&B test 1, texte cuit, effets whip/drop cuits). "
                    "Ralentis : speed_pct + Optical Flow dans Resolve (e-s = images à vitesse normale). Générateur : lot2/_claude/gen/A3/genA3.py",
            "musique": {"fichier": "lot2/" + SON["fichier"], "in_extrait_s": MUS_IN, "gain_db": SON["niveau"]["gain_conseille_db_vers_moins14LUFS"],
                        "drop_timeline_s": round(DROP, 3), "bpm": SON["bpm"], "coupes": "sur chaque temps après le drop, changements de mesure sur les downbeats"},
            "citations": [{"source": "lot2/sources/%s %.2f-%.2f s (YouTube MZ7maKdeQTE, +1305 s)" % (SC, PH["mots"][0]["start"], PH["mots"][-1]["end"]),
                           "texte": PH["texte"], "timeline_s": round(PH["mots"][0]["start"] - (LONG_T0 - beat(-6)), 2)}],
            "textes": [{"lignes": ["NOUS", "APPELONS"], "rouge": []}, {"lignes": ["AU", "DÉBORDEMENT", "POPULAIRE"], "rouge": ["DÉBORDEMENT"]}],
            "video": video,
            "audio": [{"id": "mix", "clip": "A3-mix.wav", "folder": "A3", "path": OUT + "A3-mix.wav", "rec": 0, "track": 1,
                       "note": "mix final -14 LUFS : musique du début à la fin (extrait dès 1,035 s), voix synchrone de la phrase sur le plan long (+6 dB), musique -5 dB sous la voix"}],
            "stems": [OUT + "A3-voix.wav", OUT + "A3-musique.wav"]}
    json.dump(plan, open(D + "plan-A3.json", "w"), indent=1, ensure_ascii=False)
    return plan
# ---------------- audio ----------------
def make_audio():
    sr = 48000; N = int(round(END * sr))
    def dec(path, ss=0.0, dur=None):
        cmd = [FF, "-v", "error", "-ss", "%.3f" % ss] + (["-t", "%.3f" % dur] if dur else []) + ["-i", path, "-ac", "2", "-ar", str(sr), "-f", "f32le", "-"]
        return np.frombuffer(subprocess.run(cmd, capture_output=True).stdout, np.float32).reshape(-1, 2).copy()
    def place(buf, x, t, gain_db=0, fin=0.0, fout=0.0):
        g = 10 ** (gain_db / 20); n = min(len(x), N - int(t * sr)); x = x[:n]; env = np.ones(n, np.float32)
        if fin: m = int(fin * sr); env[:m] = np.linspace(0, 1, m)
        if fout: m = int(fout * sr); env[-m:] *= np.linspace(1, 0, m)
        a = int(t * sr); buf[a:a + n] += x * env[:, None] * g
    voix = np.zeros((N, 2), np.float32); mus = np.zeros((N, 2), np.float32)
    v_in, v_out = PH["in"], LONG_END                                  # 25,40 -> 27,90 s (avant la suite « Nous appelons à ce que... »)
    s0 = round(LONG_T0 * SRCFPS[SC]) / SRCFPS[SC]                          # calé sur la 1re image du plan long (synchro labiale)
    place(voix, dec(LOT + "/sources/" + SC, v_in, v_out - v_in), fr(beat(-6)) / FPS + (v_in - s0), +6, fin=0.04, fout=0.06)
    place(mus, dec(LOT + "/" + SON["fichier"], MUS_IN), 0.0, SON["niveau"]["gain_conseille_db_vers_moins14LUFS"], fout=0.4)
    t_v = fr(beat(-6)) / FPS + (v_in - s0); duck = np.ones(N, np.float32)                 # musique -5 dB sous la phrase, remontée au drop
    a, b = int((t_v - 0.1) * sr), int((DROP - 0.03) * sr); r = int(0.1 * sr); g = 10 ** (-5 / 20)
    duck[a:b] = g; duck[a:a + r] = np.linspace(1, g, r); duck[b - int(0.02 * sr):b] = np.linspace(g, 1, int(0.02 * sr)); mus *= duck[:, None]
    import soundfile as sf
    sf.write(OUT + "A3-voix.wav", voix, sr, subtype="PCM_24"); sf.write(OUT + "A3-musique.wav", mus, sr, subtype="PCM_24")
    sf.write(D + "tmp_mix.wav", voix + mus, sr, subtype="FLOAT")
    r = subprocess.run([FF, "-hide_banner", "-i", D + "tmp_mix.wav", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    js = json.loads(r[r.rindex("{"):r.rindex("}") + 1])
    af = ("loudnorm=I=-14:TP=-1.5:LRA=11:measured_I=%s:measured_TP=%s:measured_LRA=%s:measured_thresh=%s:offset=%s:linear=true,"
          "aresample=48000" % (js["input_i"], js["input_tp"], js["input_lra"], js["input_thresh"], js["target_offset"]))
    subprocess.run([FF, "-v", "error", "-y", "-i", D + "tmp_mix.wav", "-af", af, "-c:a", "pcm_s24le", OUT + "A3-mix.wav"], check=True)
    os.remove(D + "tmp_mix.wav")
# ---------------- aperçu ffmpeg 540x960 ----------------
def apercu():
    plan = json.load(open(D + "plan-A3.json")); ins = []; fl = []
    for i, v in enumerate(plan["video"]):
        n = v["e"] - v["s"]; sp = v.get("speed_pct", 100) / 100
        ins += ["-i", v["path"]]
        if sp < 1:   # ralenti simple pour l'aperçu seulement (Resolve fera l'Optical Flow)
            fl.append("[%d:v]trim=start_frame=%d:end_frame=%d,setpts=(PTS-STARTPTS)/%.4f,fps=30,trim=end_frame=%d,setpts=PTS-STARTPTS,scale=540:960,setsar=1[v%d]"
                      % (i, v["s"], v["s"] + math.ceil(n * sp) + 1, sp, n, i))
        else:
            fl.append("[%d:v]trim=start_frame=%d:end_frame=%d,setpts=PTS-STARTPTS,scale=540:960,setsar=1[v%d]" % (i, v["s"], v["e"], i))
    k = len(plan["video"])
    fl.append("".join("[v%d]" % i for i in range(k)) + "concat=n=%d:v=1:a=0[v]" % k)
    ins += ["-i", OUT + "A3-mix.wav"]
    out = LOT + "/exports/apercu-A3.mp4"
    subprocess.run([FF, "-v", "error", "-y"] + ins + ["-filter_complex", ";".join(fl), "-map", "[v]", "-map", "%d:a" % k,
                    "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "aac", "-b:a", "192k", "-shortest", out], check=True)
    print("aperçu", out)
if __name__ == "__main__":
    args = set(sys.argv[1:]) or {"shots", "cards", "audio", "plan", "apercu"}
    only = [a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("only=")]
    only = only[0].split(",") if only else []
    if "shots" in args or only:
        for id_, sid, rec, n, eff, nb in timeline():
            if sid in SHOTS and (not only or sid in only): render_shot(sid, n, eff)
    if "cards" in args: make_cards()
    if "plan" in args: build_plan()
    if "audio" in args: make_audio()
    if "apercu" in args: apercu()
