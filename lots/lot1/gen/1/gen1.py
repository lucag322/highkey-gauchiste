# Style 1 — Aura N&B (réf @.magafx) en plein écran 9:16, sur le son de la réf.
# Règles Luca : 9:16 sans bande noire, tête jamais coupée (Apple Vision), aucun plan < 1 temps (0,69 s), coupes sur les temps,
# pas de flash d'1-2 images, ralentis faits dans Resolve (Optical Flow) : jamais précalculés ici.
# Usage : python gen1.py [shots] [cards] [audio] [plan] [apercu]   (sans argument = tout)
import sys, os, json, subprocess, math
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
ROOT = "/Users/luca.grousset/Movies/highkey-gauchiste"
sys.path.insert(0, ROOT + "/_claude/outils")
from fx import gblur, motion_blur, vignette, to8, ease_out
import framing
from framing import plan_views, detect
# 26/10 soir : projet rangé par lots -> ce dossier est lot1/_claude/gen/1 (avant : ROOT/_claude/gen/1, plan ROOT/_claude/plan1.json).
LOT = ROOT + "/lot1"
D = LOT + "/_claude/gen/1/"; OUT = D + "out/"; os.makedirs(OUT, exist_ok=True)
framing.ROOT = LOT; framing.CACHE = D + "cache"
FF = "/opt/homebrew/bin/ffmpeg"; FPS = 30; W, H = 1080, 1920
RED = (0xE4, 0x00, 0x2B); WHITE = (255, 255, 255)
F_BLACK = "/System/Library/Fonts/Supplemental/Arial Black.ttf"
F_AURA = ("/System/Library/Fonts/Helvetica.ttc", 2)          # Helvetica Oblique (« aura. » de la réf)
S1, S3, S5 = "1-melenchon-valence-amfis.mp4", "3-melenchon-huma-citation.mp4", "5-melenchon-saintdenis-smic.mp4"
SRCFPS = {S1: 30, S3: 50, S5: 30}
# zone source utilisable : on exclut le filigrane MELENCHON2027.fr (haut droite) => la fenêtre 9:16 ne l'atteint jamais
BOUNDS = {S1: (0, 0, 1460, 1080), S3: (0, 0, 1920, 1080), S5: (0, 0, 1580, 1080)}
# ---------------- grille musicale ----------------
MUSIC_AT = 5.0            # sons/1-.magafx_sans-voix.wav = réf 5,0-18,0 s : posé à 5,0 s, la timeline suit donc l'horloge de la réf
BEAT = 60 / 87.0; DROP = 5.49                    # kick du drop (réf 5,49 s), 87 BPM
def beat(k): return DROP + k * BEAT
def fr(t): return int(round(t * FPS))
END = 18.0
# ---------------- plans ----------------
# t = début source (s) ; face = indice visage (px source) ; fixed = centre imposé (plans de dos, foule) ; speed = % Resolve
SHOTS = {
    "long":      dict(src=S1, t=149.567, n=120, face=(900, 270), zoom=(1.0, 1.10), why="« la victoire est possible » (Valence)"),
    "pointe":    dict(src=S5, t=2.5,   n=45, face=(1020, 240), zoom=(1.0, 1.06), why="doigt pointé (Saint-Denis)"),
    "drapeaux":  dict(src=S1, t=101.0, n=45, fixed=(700, 540), zoom=(1.0, 1.06), why="drapeaux violets (Valence)"),
    "bras":      dict(src=S3, t=21.8,  n=45, face=(1200, 240), zoom=(1.0, 1.06), why="bras ouverts (Fête de l'Huma)"),
    "cri":       dict(src=S5, t=113.8, n=45, face=(900, 210), zoom=(1.0, 1.06), why="poing, voix forte (Saint-Denis)"),
    "passerelle": dict(src=S1, t=57.0, n=45, fixed=(1170, 540), zoom=(1.0, 1.04), speed=60, why="de dos vers la foule (Valence)"),
    "foule_dos": dict(src=S5, t=119.5, n=45, fixed=(975, 540), zoom=(1.0, 1.04), speed=60, why="de dos face à la foule (Saint-Denis)"),
    "index":     dict(src=S3, t=270.8, n=45, face=(990, 240), zoom=(1.0, 1.06), why="index levé, équipe autour (Huma)"),
    "poitrine":  dict(src=S3, t=91.8,  n=45, face=(1110, 150), zoom=(1.0, 1.06), why="poing sur le cœur (Huma)"),
    "pupitre":   dict(src=S1, t=156.5, n=45, fixed=(810, 540), zoom=(1.0, 1.04), speed=60, why="de dos au pupitre face à la foule (Valence)"),
}
# montage : (id, nb de temps, effet d'entrée)   -- après le drop, 16 temps = 4 mesures
EDIT = [("pointe", 1, "drop"), ("drapeaux", 1, "whip"), ("bras", 1, "whip"), ("cri", 1, "whip"),          # mesure 1
        ("passerelle", 2, "cut"), ("foule_dos", 1, "cut"), ("aura", 1, "cut"),                            # mesure 2
        ("pointe", 1, "drop"), ("drapeaux", 1, "whip"), ("bras", 1, "whip"), ("cri", 1, "whip"),          # mesure 3 (boucle)
        ("index", 1, "whip"), ("poitrine", 1, "whip"), ("pupitre", 2, "cut")]                             # mesure 4
# ---------------- look N&B ----------------
RNG = np.random.default_rng(11)
def grade(bgr):
    """N&B très contrasté + glow doux (palette réf #020202..#DCDEDC)."""
    g = (0.114 * bgr[..., 0] + 0.587 * bgr[..., 1] + 0.299 * bgr[..., 2])
    g = np.clip((g - 0.07) / 0.85, 0, 1)
    g = 0.45 * g + 0.55 * (g * g * (3 - 2 * g))                   # courbe en S
    small = cv2.resize(g, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    hi = np.clip(small - 0.55, 0, None) * 2.0
    glow = cv2.resize(cv2.GaussianBlur(hi, (0, 0), 9), (W, H)) * 0.45
    soft = cv2.resize(cv2.GaussianBlur(small, (0, 0), 4), (W, H))
    g = 1 - (1 - g) * (1 - 0.18 * soft) + glow                    # bloom (screen) + halo des hautes lumières
    g = vignette(g[..., None], 0.38, 2.4)[..., 0]
    g = 0.008 + np.clip(g, 0, 1) * 0.86                           # noirs #020202, blancs #DCDEDC
    g = g + RNG.normal(0, 0.018, g.shape).astype(np.float32)
    return np.repeat(np.clip(g, 0, 1)[..., None], 3, 2)
# ---------------- lecture source ----------------
def read_frames(src, t, n_out):
    """n_out images à 30 i/s depuis t (sources 50 i/s rééchantillonnées à l'image la plus proche, vitesse normale)."""
    sf = SRCFPS[src]; cap = cv2.VideoCapture(ROOT + "/sources/" + src)
    s0 = int(round(t * sf)); cap.set(cv2.CAP_PROP_POS_FRAMES, s0)
    need = [int(round(i * sf / FPS)) for i in range(n_out)]; buf = []; k = 0; out = []
    while k <= need[-1]:
        ok, f = cap.read()
        if not ok: break
        buf.append(f); k += 1
    for i in need: out.append(buf[min(i, len(buf) - 1)].astype(np.float32) / 255)
    return out, s0
def crop_916(img, cx, cy, vh):
    vw = vh * 9 / 16; s = W / vw
    M = np.float32([[s, 0, W / 2 - cx * s], [0, s, H / 2 - cy * s]])
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
# ---------------- texte ----------------
def font(path, size, idx=0): return ImageFont.truetype(path, size, index=idx)
def fit_size(txt, maxw, start=260):
    s = start
    while font(F_BLACK, s).getlength(txt) > maxw: s -= 4
    return s
def text_layer(lines, alpha_scale=1.0, scale=1.0):
    """lines = [(texte, couleur, taille_px, y_centre_px)] -> RGBA float (contour noir + ombre douce, lisible sur tout fond)."""
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay); ds = ImageDraw.Draw(sh)
    for txt, col, size, yc in lines:
        f = font(F_BLACK, max(8, int(size * scale)))
        x0, y0, x1, y1 = d.textbbox((0, 0), txt, font=f, stroke_width=int(size * 0.045))
        x = (W - (x1 - x0)) / 2 - x0; y = yc - (y1 - y0) / 2 - y0
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
# mots de la phrase (réalignés Whisper sur la source : la 151,34 / victoire 151,48 / est 151,94 / possible 152,12-152,58)
TXT_MAXW = 600     # largeur max d'une ligne : 600 x 1,12 (entrée du dernier mot) = 672 < 713 px
TXT_TOP = 100      # LA / EST (avant 150) : reste sous VICTOIRE / POSSIBLE (~110), lettres 72 px
WORDS = [(151.34, "LA"), (151.48, "VICTOIRE"), (151.94, "EST"), (152.12, "POSSIBLE")]
def long_text(fi, t_src):
    """Carton 1 « LA / VICTOIRE » (mot-titre géant rouge), carton 2 « EST / POSSIBLE ». Entrée 3 images, sans rebond."""
    on = [w for w in WORDS if t_src >= w[0]]
    if not on: return None
    # Zone sûre TikTok (26/10) : bloc <= 66 % de large centré (x 183-897), y <= 1440 ; avant : VICTOIRE 1000 px / POSSIBLE 960 px de large.
    sv = fit_size("VICTOIRE", TXT_MAXW); sp = fit_size("POSSIBLE", TXT_MAXW)
    if t_src < WORDS[2][0]:
        lines = [("LA", WHITE, TXT_TOP, 1130)]
        if t_src >= WORDS[1][0]: lines.append(("VICTOIRE", RED, sv, 1130 + TXT_TOP / 2 + sv * 0.62))
        last = on[-1][0]
    else:
        lines = [("EST", WHITE, TXT_TOP, 1130)]
        if t_src >= WORDS[3][0]: lines.append(("POSSIBLE", WHITE, sp, 1130 + TXT_TOP / 2 + sp * 0.62))
        last = on[-1][0]
    k = (t_src - last) * FPS                                         # images depuis l'apparition du dernier mot
    e = ease_out(min(k / 3.0, 1.0))
    base = text_layer(lines[:-1]) if len(lines) > 1 else None
    top = text_layer(lines[-1:], alpha_scale=min(1.0, 0.35 + e), scale=1.12 - 0.12 * e)
    if base is None: return top
    a = top[..., 3:4]; out = base * (1 - a) + top * a; out[..., 3:4] = np.maximum(base[..., 3:4], a); return out
# ---------------- rendu des plans ----------------
def write_mov(frames, path, fps=FPS):
    p = subprocess.Popen([FF, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", "%dx%d" % (W, H), "-r", str(fps), "-i", "-",
                          "-c:v", "prores_ks", "-profile:v", "3", "-pix_fmt", "yuv422p10le", "-vendor", "apl0", path], stdin=subprocess.PIPE)
    for f in frames: p.stdin.write(to8(f).tobytes())
    p.stdin.close(); p.wait()
def render_shot(sid):
    sh = SHOTS[sid]; src = sh["src"]; n = sh["n"]
    raw, s0 = read_frames(src, sh["t"], n)
    z0, z1 = sh["zoom"]; zoom = lambda f: z0 + (z1 - z0) * f / max(n - 1, 1)
    sf = SRCFPS[src]
    if "fixed" in sh:
        views, _ = plan_views(src, s0, n, sf, speed=sf / FPS, bounds=BOUNDS[src], vh=1080, zoom=zoom, fixed=sh["fixed"])
    else:
        views, ok = plan_views(src, s0, n, sf, speed=sf / FPS, hint=sh["face"], bounds=BOUNDS[src], vh=1080, zoom=zoom, top=0.12)
        if not ok: print("  ! pas de visage détecté :", sid)
    frames = []
    for i, (img, (cx, cy, vh)) in enumerate(zip(raw, views)):
        g = grade(crop_916(img, cx, cy, vh))
        if sid == "long":
            tl = long_text(i, sh["t"] + i / FPS)
            if tl is not None: g = over_rgba(g, tl)
        frames.append(g)
    write_mov(frames, OUT + "1_%s.mov" % sid)
    SHOTS[sid]["views"] = [(round(a), round(b), round(c)) for a, b, c in views[:1]]
    print("  plan", sid, n, "images", "vue0", SHOTS[sid]["views"][0])
# ---------------- cartes « aura. » ----------------
def aura_card(n, fade_in=3, fade_out=0):
    im = Image.new("L", (W, H), 0); d = ImageDraw.Draw(im); f = font(F_AURA[0], 120, F_AURA[1])
    tw = d.textlength("aura.", font=f); d.text(((W - tw) / 2, H / 2 - 80), "aura.", font=f, fill=255)
    a = np.asarray(im).astype(np.float32) / 255
    glow = gblur(a, 22) * 0.9 + gblur(a, 6) * 0.5
    base = np.clip(a * 0.92 + glow, 0, 0.95)
    out = []
    for i in range(n):
        k = 1.0
        if fade_in and i < fade_in: k = ease_out((i + 1) / fade_in)
        if fade_out and i >= n - fade_out: k = (n - i) / fade_out
        out.append(np.repeat((0.008 + base * k)[..., None], 3, 2))
    return out
def make_cards():
    write_mov(aura_card(fr(2.0)), OUT + "1_aura_intro.mov")                   # hook 0-2,0 s
    write_mov(aura_card(21), OUT + "1_aura.mov")                              # carton d'un temps (mesure 2)
    n_end = fr(END) - fr(beat(16)); write_mov(aura_card(n_end, fade_in=3, fade_out=12), OUT + "1_aura_fin.mov")
# ---------------- effets d'entrée (appliqués à l'aperçu ET précalculés dans des variantes ?) ----------------
# Les effets d'entrée (whip, bloom du drop) sont des transitions : on les cuit dans des copies « _whip / _drop » du plan,
# l'image 0 du fichier = première image à l'écran.
def entry_variant(sid, kind):
    path_in = OUT + "1_%s.mov" % sid; path = OUT + "1_%s_%s.mov" % (sid, kind)
    p = subprocess.run([FF, "-v", "error", "-i", path_in, "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True)
    fr_ = np.frombuffer(p.stdout, np.uint8).reshape(-1, H, W, 3).astype(np.float32) / 255
    out = []
    for i, f in enumerate(fr_):
        if kind == "whip" and i < 3:                                  # flou de mouvement vertical sur 3 images (≤ 6 images à 60 i/s)
            amt = [220, 90, 25][i]; f = motion_blur(f, 0, amt, steps=16)
        if kind == "drop" and i < 8:                                  # bloom d'exposition au drop (pas d'image blanche)
            k = (1 - i / 8) ** 2; f = np.clip(f + k * 0.55 + gblur(f, 25) * k * 0.6, 0, 1)
        out.append(f)
    write_mov(out, path)
# ---------------- plan + audio ----------------
def build_plan():
    rec = 0; video = []
    def add(id_, clip, s, e, rec, kind, extra=None):
        v = {"id": id_, "clip": clip, "folder": "gen1", "s": s, "e": e, "rec": rec, "track": 1, "kind": kind}
        if extra: v.update(extra)
        video.append(v)
    add("hook", "1_aura_intro.mov", 0, fr(2.0), 0, "card")
    add("long", "1_long.mov", 0, fr(DROP) - fr(2.0), fr(2.0), "shot",
        {"source": "%s @ %.2f s" % (S1, SHOTS["long"]["t"]), "texte": "LA / VICTOIRE (rouge) · EST / POSSIBLE"})
    k = 0
    for sid, nb, eff in EDIT:
        a, b = fr(beat(k)), fr(beat(k + nb)); n = b - a
        if sid == "aura":
            add("aura_%d" % a, "1_aura.mov", 0, n, a, "card")
        else:
            sh = SHOTS[sid]; clip = "1_%s.mov" % sid if eff == "cut" else "1_%s_%s.mov" % (sid, eff)
            extra = {"source": "%s @ %.2f s" % (sh["src"], sh["t"]), "effet": eff, "temps": nb}
            if sh.get("speed"): extra.update({"speed_pct": sh["speed"], "retime": "optical_flow"})
            add("%s_%d" % (sid, a), clip, 0, n, a, "shot", extra)
        k += nb
    add("fin", "1_aura_fin.mov", 0, fr(END) - fr(beat(16)), fr(beat(16)), "card")
    plan = {"name": "1 - Aura N&B", "fps": FPS, "w": W, "h": H,
            "note": "Plans 9:16 recadrés + étalonnés N&B (gen/1/out). s/e en images du clip (30 i/s), rec en images timeline 30 i/s. "
                    "speed_pct : ralenti Resolve Optical Flow + Speed Warp (e - s = durée timeline à vitesse normale, source raccourcie). "
                    "Coupes sur les temps (87 BPM, drop 5,49 s) ; aucun plan < 1 temps.",
            "video": video,
            "audio": [{"id": "mix", "clip": "1-mix.wav", "folder": "gen1", "rec": 0, "track": 1,
                       "note": "mix final -14 LUFS (foule + voix 0-5,6 s, musique de la réf dès 5,0 s)"}],
            "stems": ["gen/1/out/1-voix.wav", "gen/1/out/1-musique.wav"],
            "sources": {sid: {"fichier": "sources/" + v["src"], "t": v["t"], "pourquoi": v["why"]} for sid, v in SHOTS.items()},
            "sources_url": {S1: "youtube IYegq2-6-go (chaîne officielle JLM, Valence 23/08/2026)",
                            S3: "youtube 80bBtk2lTiI (chaîne officielle JLM, Fête de l'Huma 12/09/2026)",
                            S5: "chaîne officielle JLM, meeting Saint-Denis 07/06/2026 (voir derush.json)"}}
    json.dump(plan, open(LOT + "/_claude/plan1.json", "w"), indent=1, ensure_ascii=False)
    return plan
def make_audio():
    sr = 48000; N = int(END * sr)
    def grab(src, t, dur):
        p = subprocess.run([FF, "-v", "error", "-ss", "%.3f" % t, "-t", "%.3f" % dur, "-i", ROOT + "/sources/" + src, "-ac", "2", "-ar", str(sr),
                            "-f", "f32le", "-"], capture_output=True)
        return np.frombuffer(p.stdout, np.float32).reshape(-1, 2).copy()
    def place(buf, x, t, gain_db=0, fin=0.0, fout=0.0):
        g = 10 ** (gain_db / 20); n = len(x); env = np.ones(n, np.float32)
        if fin: m = int(fin * sr); env[:m] = np.linspace(0, 1, m)
        if fout: m = int(fout * sr); env[-m:] *= np.linspace(1, 0, m)
        a = int(t * sr); b = min(N, a + n); buf[a:b] += x[:b - a] * env[:b - a, None] * g
    voix = np.zeros((N, 2), np.float32); mus = np.zeros((N, 2), np.float32)
    place(voix, grab(S1, 153.3, 3.7), 0.0, -4, fin=0.5, fout=0.3)               # foule qui acclame (Valence, sans parole)
    t_long = SHOTS["long"]["t"]; t_in = 151.15                                     # son synchrone du plan long, dès la phrase
    place(voix, grab(S1, t_in, 2.45), 2.0 + (t_in - t_long), +3, fin=0.05, fout=0.45)
    p = subprocess.run([FF, "-v", "error", "-i", LOT + "/sons/1-.magafx_sans-voix.wav", "-ac", "2", "-ar", str(sr), "-f", "f32le", "-"], capture_output=True)
    m = np.frombuffer(p.stdout, np.float32).reshape(-1, 2).copy()
    place(mus, m, MUSIC_AT, 0, fout=0.8)
    import soundfile as sf
    sf.write(OUT + "1-voix.wav", voix, sr, subtype="PCM_24"); sf.write(OUT + "1-musique.wav", mus, sr, subtype="PCM_24")
    mix = voix + mus; sf.write(D + "tmp_mix.wav", mix, sr, subtype="FLOAT")
    # loudnorm 2 passes -> -14 LUFS, crête vraie -1,5 dBTP
    r = subprocess.run([FF, "-hide_banner", "-i", D + "tmp_mix.wav", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    js = json.loads(r[r.rindex("{"):r.rindex("}") + 1])
    af = ("loudnorm=I=-14:TP=-1.5:LRA=11:measured_I=%s:measured_TP=%s:measured_LRA=%s:measured_thresh=%s:offset=%s:linear=true,"
          "aresample=48000" % (js["input_i"], js["input_tp"], js["input_lra"], js["input_thresh"], js["target_offset"]))
    subprocess.run([FF, "-v", "error", "-y", "-i", D + "tmp_mix.wav", "-af", af, "-c:a", "pcm_s24le", OUT + "1-mix.wav"], check=True)
    os.remove(D + "tmp_mix.wav")
# ---------------- aperçu ffmpeg (540x960) conforme au plan ----------------
def apercu():
    plan = json.load(open(LOT + "/_claude/plan1.json")); ins = []; fl = []
    for i, v in enumerate(plan["video"]):
        n = v["e"] - v["s"]; sp = v.get("speed_pct", 100) / 100
        ins += ["-i", OUT + v["clip"]]
        if sp < 1:   # ralenti simple pour l'aperçu seulement (Resolve fera l'Optical Flow)
            used = n * sp
            fl.append("[%d:v]trim=start_frame=%d:end_frame=%d,setpts=(PTS-STARTPTS)/%.4f,fps=30,trim=end_frame=%d,setpts=PTS-STARTPTS,scale=540:960,setsar=1[v%d]"
                      % (i, v["s"], v["s"] + math.ceil(used) + 1, sp, n, i))
        else:
            fl.append("[%d:v]trim=start_frame=%d:end_frame=%d,setpts=PTS-STARTPTS,scale=540:960,setsar=1[v%d]" % (i, v["s"], v["e"], i))
    k = len(plan["video"])
    fl.append("".join("[v%d]" % i for i in range(k)) + "concat=n=%d:v=1:a=0[v]" % k)
    ins += ["-i", OUT + "1-mix.wav"]
    out = ROOT + "/preview/apercu-L1.mp4"            # L1 = edit n°1 du lot 1 (HD : hd/HD-L1-1.mp4)
    subprocess.run([FF, "-v", "error", "-y"] + ins + ["-filter_complex", ";".join(fl), "-map", "[v]", "-map", "%d:a" % k,
                    "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "aac", "-b:a", "192k", "-shortest", out], check=True)
    print("aperçu", out)
if __name__ == "__main__":
    args = set(sys.argv[1:]) or {"shots", "cards", "audio", "plan", "apercu"}
    only = [a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("only=")]
    if "shots" in args or only:
        for sid in (only or SHOTS):
            render_shot(sid)
        for sid, nb, eff in EDIT:
            if eff in ("whip", "drop") and (not only or sid in only): entry_variant(sid, eff)
    if "cards" in args: make_cards()
    if "plan" in args: build_plan()
    if "audio" in args: make_audio()
    if "apercu" in args: apercu()
