# Lot 2 — A1 Aura N&B : Mathilde Panot, « Désormais, plus rien ne passera. » sur AURA (Ogryzek). Modèle : _claude/gen/1/gen1.py.
# Règles : 15 s max, 9:16 plein écran, aucun visage coupé (même secondaire > 5 % de la hauteur), plans ≥ 1 temps sur la grille,
# pas de dézoom (poussée lente avant), Arial Black + mot-clé rouge, jamais de guillemets, ralentis = Resolve (speed_pct).
# Usage : python genA1.py [shots] [cards] [audio] [plan] [apercu] [check]   (sans argument = tout)  |  only=<id> pour un plan
import sys, os, json, subprocess, math, shutil
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
HG = "/Users/luca.grousset/Movies/highkey-gauchiste"; L2 = HG + "/lot2"
sys.path.insert(0, HG + "/_claude/outils")
from fx import gblur, motion_blur, vignette, to8, ease_out
import framing
framing.ROOT = L2; framing.CACHE = L2 + "/_claude/cache/faces"          # sources du lot 2, cache visages du lot 2
from framing import plan_views
D = L2 + "/_claude/gen/A1/"; OUT = D + "out/"; os.makedirs(OUT, exist_ok=True)
FF = "/opt/homebrew/bin/ffmpeg"; FACES = HG + "/_claude/outils/faces"; FPS = 30; W, H = 1080, 1920
RED = (0xE4, 0x00, 0x2B); WHITE = (255, 255, 255)
F_BLACK = "/System/Library/Fonts/Supplemental/Arial Black.ttf"
F_AURA = ("/System/Library/Fonts/Helvetica.ttc", 2)
SA, SB, SC, SQ = "A1-panot-rochefort-a.mp4", "A1-panot-rochefort-b.mp4", "A1-panot-rochefort-c.mp4", "A1-panot-lcp-qag-2025-12.mp4"
SRCFPS = {SA: 30, SB: 30, SC: 30, SQ: 25}
# filigrane MELENCHON2027.fr en haut à droite (Rochefort) ; logo LCP en haut à gauche (QAG) : la fenêtre 9:16 reste hors de ces zones
BOUNDS = {SA: (0, 0, 1560, 1080), SB: (0, 0, 1560, 1080), SC: (0, 0, 1560, 1080), SQ: (300, 0, 1920, 1080)}
# ---------------- grille : AURA (Ogryzek), extrait sons/A1-ogryzek-aura.wav posé à 0, 90 BPM, 808 du drop à 5,46 s ----------------
BEAT = 60 / 90.0; DROP = 5.464
def beat(k): return DROP + k * BEAT
def fr(t): return int(round(t * FPS))
END = 15.0; HOOK_END = beat(-6)                                     # 1,464 s (premier temps fort de l'extrait)
# ---------------- plans ----------------
SHOTS = {
    "long":     dict(src=SA, t=15.924, n=130, face=(900, 250), zoom=(1.0, 1.10), why="phrase « Désormais, plus rien ne passera. » (Rochefort, 22/10/2026)"),
    "bras":     dict(src=SA, t=51.7,  n=45, face=(900, 250), zoom=(1.0, 1.05), why="bras grands ouverts (Rochefort)"),
    "poing":    dict(src=SB, t=27.2,  n=45, face=(900, 250), zoom=(1.0, 1.05), why="bras levé, sourire (Rochefort)"),
    "salle":    dict(src=SC, t=52.15, n=45, fixed=(780, 540), zoom=(1.0, 1.04), why="salle debout, drapeaux (Rochefort)"),
    "dessine":  dict(src=SC, t=16.3,  n=45, face=(900, 250), zoom=(1.0, 1.05), why="mains qui dessinent (Rochefort, autre caméra)"),
    "mains":    dict(src=SB, t=57.2,  n=45, face=(900, 250), zoom=(1.0, 1.05), why="deux mains levées (Rochefort, avant le bandeau nom)"),
    "index":    dict(src=SB, t=100.2, n=45, face=(900, 250), zoom=(1.0, 1.05), why="index levé (Rochefort)"),
    "regard":   dict(src=SA, t=42.3,  n=45, face=(900, 250), zoom=(1.0, 1.04), speed=60, why="regard de côté, tribune (Rochefort)"),
    "face":     dict(src=SB, t=80.8,  n=45, face=(900, 250), zoom=(1.0, 1.05), why="de face, voix forte (Rochefort)"),
    "cri":      dict(src=SQ, t=62.3,  n=45, face=(900, 300), zoom=(1.0, 1.05), why="cri final, applaudissements (QAG LCP)"),
    "hemicycle": dict(src=SQ, t=31.3, n=45, face=(850, 300), zoom=(1.0, 1.05), why="bras tendu, voix forte (QAG LCP)"),
}
# après le drop : 13 temps jusqu'à 14,131 s puis carton final. Mesures : temps forts à 6,798 / 9,464 / 12,131
EDIT = [("bras", 1, "drop"), ("salle", 1, "whip"),
        ("poing", 1, "whip"), ("dessine", 1, "whip"), ("mains", 1, "whip"), ("index", 1, "whip"),
        ("regard", 2, "cut"), ("face", 1, "whip"), ("cri", 1, "whip"),
        ("bras", 1, "whip"), ("poing", 1, "whip"), ("hemicycle", 1, "whip")]
# ---------------- look N&B (identique au style 1 validé) ----------------
RNG = np.random.default_rng(11)
def grade(bgr):
    g = (0.114 * bgr[..., 0] + 0.587 * bgr[..., 1] + 0.299 * bgr[..., 2])
    g = np.clip((g - 0.07) / 0.85, 0, 1)
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
def read_frames(src, t, n_out):
    sf = SRCFPS[src]; cap = cv2.VideoCapture(L2 + "/sources/" + src)
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
# ---------------- texte (Arial Black, contour noir, mot-clé rouge, sans guillemets ni ponctuation) ----------------
def font(path, size, idx=0): return ImageFont.truetype(path, size, index=idx)
def fit_size(txt, maxw, start=260):
    s = start
    while font(F_BLACK, s).getlength(txt) > maxw: s -= 4
    return s
# zone sûre TikTok (1080×1920) : texte centré dans x 0,17-0,83 (≤ 66 % de la largeur), y 0,12-0,75 ; marge prise pour l'entrée à 112 %
SAFE_L, SAFE_R, SAFE_BOT = 192, 888, 1400
def safe_size(txt, start, pop=1.12):
    s = start
    while s > 8:
        f = font(F_BLACK, s); sw = max(4, int(s * 0.045)); x0, _, x1, _ = f.getbbox(txt, stroke_width=sw)
        if (x1 - x0) * pop <= SAFE_R - SAFE_L: return s
        s -= 2
    return s
def text_layer(lines, alpha_scale=1.0, scale=1.0):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay); ds = ImageDraw.Draw(sh)
    for ln in lines:
        txt, col, size, yc = ln[:4]; xc = ln[4] if len(ln) > 4 else W / 2
        f = font(F_BLACK, max(8, int(size * scale)))
        x0, y0, x1, y1 = d.textbbox((0, 0), txt, font=f, stroke_width=int(size * 0.045))
        x = xc - (x1 - x0) / 2 - x0; y = yc - (y1 - y0) / 2 - y0
        sw = max(4, int(size * 0.045))
        ds.text((x, y + size * 0.05), txt, font=f, fill=(0, 0, 0, 200), stroke_width=sw * 3, stroke_fill=(0, 0, 0, 200))
        d.text((x, y), txt, font=f, fill=col + (255,), stroke_width=sw, stroke_fill=(0, 0, 0, 255))
    sh = sh.filter(ImageFilter.GaussianBlur(18))
    a = np.asarray(Image.alpha_composite(sh, lay)).astype(np.float32) / 255
    a[..., 3] *= alpha_scale
    return a
def over_rgba(img_bgr, rgba):
    a = rgba[..., 3:4]; rgb = rgba[..., 2::-1]
    return img_bgr * (1 - a) + rgb * a
# mots (dérush AG, Whisper) : Désormais 17,76 / plus 18,64 / rien 18,80 / ne 19,08 / passera 19,30-19,72
WORDS = [(17.76, "DÉSORMAIS"), (18.64, "PLUS"), (18.80, "RIEN"), (19.08, "NE"), (19.30, "PASSERA")]
Y0 = 1130
def card_lines(t):
    on = [w for w in WORDS if t >= w[0]]
    if not on: return None, None
    if t < WORDS[1][0]:                                                       # carton 1
        return [("DÉSORMAIS", WHITE, safe_size("DÉSORMAIS", 260), Y0 + 120)], on[-1][0]
    # carton 2 (jusqu'au drop) : PLUS / RIEN (mot-clé géant rouge) / NE / PASSERA, chaque mot à son temps.
    # NE PASSERA sur 2 lignes pour rester dans la zone sûre TikTok avec des lettres ≥ 70 px ; bloc posé au-dessus de y 0,73.
    sp, sr, sz = 140, safe_size("RIEN", 210), safe_size("PASSERA", 130)
    cap = lambda s: 0.716 * s                                                 # hauteur des capitales Arial Black
    yb = SAFE_BOT - cap(sz) / 2; yn = yb - cap(sz) - 30                       # PASSERA, NE
    yr = yn - cap(sz) / 2 - 0.27 * sr - cap(sr) / 2; yp = yr - cap(sr) / 2 - 0.34 * sr - cap(sp) / 2
    ls = [("PLUS", WHITE, sp, yp)]
    if t >= WORDS[2][0]: ls.append(("RIEN", RED, sr, yr))
    if t >= WORDS[3][0]: ls.append(("NE", WHITE, sz, yn))
    if t >= WORDS[4][0]: ls.append(("PASSERA", WHITE, sz, yb))
    return ls, on[-1][0]
def long_text(t_src):
    lines, last = card_lines(t_src)
    if lines is None: return None
    e = ease_out(min((t_src - last) * FPS / 3.0, 1.0))                         # entrée 3 images, forte décélération, sans rebond
    top = text_layer(lines[-1:], alpha_scale=min(1.0, 0.35 + e), scale=1.12 - 0.12 * e)
    if len(lines) == 1: return top
    base = text_layer(lines[:-1]); a = top[..., 3:4]
    out = base * (1 - a) + top * a; out[..., 3:4] = np.maximum(base[..., 3:4], a); return out
# ---------------- rendu ----------------
def write_mov(frames, path, fps=FPS):
    p = subprocess.Popen([FF, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", "%dx%d" % (W, H), "-r", str(fps), "-i", "-",
                          "-c:v", "prores_ks", "-profile:v", "3", "-pix_fmt", "yuv422p10le", "-vendor", "apl0", path], stdin=subprocess.PIPE)
    for f in frames: p.stdin.write(to8(f).tobytes())
    p.stdin.close(); p.wait()
def views_for(sid):
    sh = SHOTS[sid]; src = sh["src"]; n = sh["n"]; sf = SRCFPS[src]; s0 = int(round(sh["t"] * sf))
    z0, z1 = sh["zoom"]; zoom = lambda f: z0 + (z1 - z0) * f / max(n - 1, 1)
    if "fixed" in sh:
        return plan_views(src, s0, n, sf, speed=sf / FPS, bounds=BOUNDS[src], vh=1080, zoom=zoom, fixed=sh["fixed"])
    return plan_views(src, s0, n, sf, speed=sf / FPS, hint=sh["face"], bounds=BOUNDS[src], vh=1080, zoom=zoom, top=0.12)
def render_shot(sid):
    sh = SHOTS[sid]; raw, s0 = read_frames(sh["src"], sh["t"], sh["n"])
    views, ok = views_for(sid)
    if not ok and "fixed" not in sh: print("  ! pas de visage :", sid)
    frames = []
    for i, (img, (cx, cy, vh)) in enumerate(zip(raw, views)):
        g = grade(crop_916(img, cx, cy, vh))
        if sid == "long":
            tl = long_text(sh["t"] + i / FPS)
            if tl is not None: g = over_rgba(g, tl)
        frames.append(g)
    write_mov(frames, OUT + "A1_%s.mov" % sid)
    print("  plan", sid, sh["n"], "vue0", tuple(round(x) for x in views[0]), "vh fin", round(views[-1][2]))
def entry_variant(sid, kind):
    p = subprocess.run([FF, "-v", "error", "-i", OUT + "A1_%s.mov" % sid, "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True)
    frs = np.frombuffer(p.stdout, np.uint8).reshape(-1, H, W, 3).astype(np.float32) / 255; out = []
    for i, f in enumerate(frs):
        if kind == "whip" and i < 3: f = motion_blur(f, 0, [220, 90, 25][i], steps=16)
        if kind == "drop" and i < 8:
            k = (1 - i / 8) ** 2; f = np.clip(f + k * 0.55 + gblur(f, 25) * k * 0.6, 0, 1)
        out.append(f)
    write_mov(out, OUT + "A1_%s_%s.mov" % (sid, kind))
def aura_card(n, fade_in=3, fade_out=0):
    im = Image.new("L", (W, H), 0); d = ImageDraw.Draw(im); f = font(F_AURA[0], 120, F_AURA[1])
    tw = d.textlength("aura.", font=f); d.text(((W - tw) / 2, H / 2 - 80), "aura.", font=f, fill=255)
    a = np.asarray(im).astype(np.float32) / 255
    base = np.clip(a * 0.92 + gblur(a, 22) * 0.9 + gblur(a, 6) * 0.5, 0, 0.95); out = []
    for i in range(n):
        k = 1.0
        if fade_in and i < fade_in: k = ease_out((i + 1) / fade_in)
        if fade_out and i >= n - fade_out: k = (n - i) / fade_out
        out.append(np.repeat((0.008 + base * k)[..., None], 3, 2))
    return out
def make_cards():
    write_mov(aura_card(fr(HOOK_END)), OUT + "A1_aura_intro.mov")
    write_mov(aura_card(fr(END) - fr(beat(13)), fade_in=3, fade_out=12), OUT + "A1_aura_fin.mov")
# ---------------- plan ----------------
def build_plan():
    video = []
    def add(id_, clip, n, rec, kind, extra=None):
        v = {"id": id_, "clip": clip, "folder": "genA1", "s": 0, "e": n, "rec": rec, "track": 1, "kind": kind}
        if extra: v.update(extra)
        video.append(v)
    add("hook", "A1_aura_intro.mov", fr(HOOK_END), 0, "card")
    add("long", "A1_long.mov", fr(DROP) - fr(HOOK_END), fr(HOOK_END), "shot",
        {"source": "%s @ %.2f s" % (SA, SHOTS["long"]["t"]), "texte": "DÉSORMAIS · PLUS / RIEN (rouge) / NE / PASSERA"})
    k = 0
    for sid, nb, eff in EDIT:
        a, b = fr(beat(k)), fr(beat(k + nb)); sh = SHOTS[sid]
        clip = "A1_%s.mov" % sid if eff == "cut" else "A1_%s_%s.mov" % (sid, eff)
        extra = {"source": "%s @ %.2f s" % (sh["src"], sh["t"]), "effet": eff, "temps": nb}
        if sh.get("speed"): extra.update({"speed_pct": sh["speed"], "retime": "optical_flow"})
        add("%s_%d" % (sid, a), clip, b - a, a, "shot", extra); k += nb
    add("fin", "A1_aura_fin.mov", fr(END) - fr(beat(k)), fr(beat(k)), "card")
    plan = {"name": "A1 - Panot aura N&B", "fps": FPS, "w": W, "h": H, "duree_s": END,
            "note": "Plans 9:16 recadrés + N&B (gen/A1/out). s/e en images du clip (30 i/s), rec en images timeline 30 i/s. "
                    "speed_pct : ralenti Resolve Optical Flow + Speed Warp (e - s = durée timeline à vitesse normale). "
                    "Coupes sur les temps (90 BPM, drop 5,464 s), aucun plan < 1 temps.",
            "video": video,
            "audio": [{"id": "mix", "clip": "A1-mix.wav", "folder": "genA1", "rec": 0, "track": 1,
                       "note": "AURA (Ogryzek) de 0 à 15 s, voix de Panot 3,14-5,4 s (musique baissée dessous), -14 LUFS"}],
            "stems": ["lot2/_claude/gen/A1/out/A1-voix.wav", "lot2/_claude/gen/A1/out/A1-musique.wav"],
            "sources": {sid: {"fichier": "lot2/sources/" + v["src"], "t": v["t"], "pourquoi": v["why"]} for sid, v in SHOTS.items()},
            "sources_url": {SA: "youtube 4l2dx1n-UFo (chaîne Mathilde Panot, meeting Rochefort 22/10/2026), offset_yt 1545 s",
                            SB: "youtube 4l2dx1n-UFo, offset_yt 20 s", SC: "youtube 4l2dx1n-UFo, offset_yt 1980 s",
                            SQ: "youtube mqeo_ILV2_w (LCP, QAG 04/12/2025)"}}
    json.dump(plan, open(D + "plan-A1.json", "w"), indent=1, ensure_ascii=False)
# ---------------- audio ----------------
def make_audio():
    import soundfile as sf
    sr = 48000; N = int(END * sr)
    def dec(path, t=None, dur=None):
        cmd = [FF, "-v", "error"] + (["-ss", "%.3f" % t, "-t", "%.3f" % dur] if t is not None else []) + ["-i", path, "-ac", "2", "-ar", str(sr), "-f", "f32le", "-"]
        return np.frombuffer(subprocess.run(cmd, capture_output=True).stdout, np.float32).reshape(-1, 2).copy()
    voix = np.zeros((N, 2), np.float32); mus = np.zeros((N, 2), np.float32)
    t_in, t_out = 17.62, 19.92                     # « Désormais, plus rien ne passera. » entier, avant la reprise « Plus rien… »
    v = dec(L2 + "/sources/" + SA, t_in, t_out - t_in); env = np.ones(len(v), np.float32)
    m = int(0.03 * sr); env[:m] = np.linspace(0, 1, m); m = int(0.15 * sr); env[-m:] = np.linspace(1, 0, m)
    a = int((3.3 - (17.76 - t_in)) * sr); voix[a:a + len(v)] += v * env[:, None]
    mu = dec(L2 + "/sons/A1-ogryzek-aura.wav")[:N]; mus[:len(mu)] = mu
    t = np.arange(N) / sr; g = np.ones(N, np.float32)                       # musique baissée sous la voix (-9 dB), fondu final
    duck = 10 ** (-9 / 20); g = np.where((t > 3.0) & (t < 5.3), duck, 1.0)
    for t0, t1, g0, g1 in ((2.8, 3.0, 1.0, duck), (5.3, 5.45, duck, 1.0)):
        s = (t >= t0) & (t < t1); g[s] = g0 + (g1 - g0) * (t[s] - t0) / (t1 - t0)
    s = t > END - 0.7; g[s] *= (END - t[s]) / 0.7
    mus *= g[:, None].astype(np.float32); voix *= 10 ** (6 / 20)
    sf.write(OUT + "A1-voix.wav", voix, sr, subtype="PCM_24"); sf.write(OUT + "A1-musique.wav", mus, sr, subtype="PCM_24")
    sf.write(D + "tmp_mix.wav", voix + mus, sr, subtype="FLOAT")
    r = subprocess.run([FF, "-hide_banner", "-i", D + "tmp_mix.wav", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    js = json.loads(r[r.rindex("{"):r.rindex("}") + 1])
    af = ("loudnorm=I=-14:TP=-1.5:LRA=11:measured_I=%s:measured_TP=%s:measured_LRA=%s:measured_thresh=%s:offset=%s:linear=true,aresample=48000"
          % (js["input_i"], js["input_tp"], js["input_lra"], js["input_thresh"], js["target_offset"]))
    subprocess.run([FF, "-v", "error", "-y", "-i", D + "tmp_mix.wav", "-af", af, "-c:a", "pcm_s24le", OUT + "A1-mix.wav"], check=True)
    os.remove(D + "tmp_mix.wav")
# ---------------- aperçu ffmpeg 540x960 ----------------
def apercu():
    plan = json.load(open(D + "plan-A1.json")); ins = []; fl = []
    for i, v in enumerate(plan["video"]):
        n = v["e"] - v["s"]; sp = v.get("speed_pct", 100) / 100; ins += ["-i", OUT + v["clip"]]
        if sp < 1:
            fl.append("[%d:v]trim=start_frame=%d:end_frame=%d,setpts=(PTS-STARTPTS)/%.4f,fps=30,trim=end_frame=%d,setpts=PTS-STARTPTS,scale=540:960,setsar=1[v%d]"
                      % (i, v["s"], v["s"] + math.ceil(n * sp) + 1, sp, n, i))
        else:
            fl.append("[%d:v]trim=start_frame=%d:end_frame=%d,setpts=PTS-STARTPTS,scale=540:960,setsar=1[v%d]" % (i, v["s"], v["e"], i))
    k = len(plan["video"]); fl.append("".join("[v%d]" % i for i in range(k)) + "concat=n=%d:v=1:a=0[v]" % k)
    out = HG + "/preview/apercu-A1.mp4"
    subprocess.run([FF, "-v", "error", "-y"] + ins + ["-i", OUT + "A1-mix.wav", "-filter_complex", ";".join(fl), "-map", "[v]", "-map", "%d:a" % k,
                    "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "aac", "-b:a", "192k", "-shortest", out], check=True)
    print("aperçu", out)
# ---------------- contrôle visages : tout visage > 5 % de la hauteur doit être entier, dans chaque plan ----------------
def check_faces():
    plan = json.load(open(D + "plan-A1.json")); bad = []; seen = set()
    for v in plan["video"]:
        if v["kind"] != "shot" or v["clip"] in seen: continue
        seen.add(v["clip"]); n = v["e"] - v["s"]
        if v.get("speed_pct"): n = math.ceil(n * v["speed_pct"] / 100) + 1
        d = "/private/tmp/claude-502/a1/chk_" + v["clip"]; shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
        subprocess.run([FF, "-v", "error", "-i", OUT + v["clip"], "-vf", "select='lt(n\\,%d)*not(mod(n\\,2))',scale=540:960" % n, "-fps_mode", "passthrough",
                        "-q:v", "3", d + "/f%04d.jpg"], check=True)
        subprocess.run([FACES, d], check=True, capture_output=True)
        js = json.load(open(d + "/faces.json")); nb = 0
        for k, fl in js.items():
            for x, y, w, h in fl:
                if h < 0.05: continue                                             # visages < 5 % de la hauteur ignorés
                top, bot, l, r = y - 0.3 * h, y + h * 1.05, x - 0.08 * w, x + w * 1.08
                if top < 0 or bot > 1 or l < 0 or r > 1: nb += 1; bad.append("%s %s (%.2f %.2f %.2f %.2f)" % (v["clip"], k, top, bot, l, r))
        print("  visages", v["clip"], "images", len(js), "coupés", nb)
    print("TOTAL visages coupés :", len(bad)); print("\n".join(bad[:30]))
if __name__ == "__main__":
    args = set(a for a in sys.argv[1:] if "=" not in a) or {"shots", "cards", "audio", "plan", "apercu", "check"}
    only = [a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("only=")]
    if "shots" in args or only:
        for sid in (only or SHOTS): render_shot(sid)
        done = set()
        for sid, nb, eff in EDIT:
            if eff in ("whip", "drop") and (sid, eff) not in done and (not only or sid in only): entry_variant(sid, eff); done.add((sid, eff))
    if "cards" in args: make_cards()
    if "plan" in args: build_plan()
    if "audio" in args: make_audio()
    if "apercu" in args: apercu()
    if "check" in args: check_faces()
