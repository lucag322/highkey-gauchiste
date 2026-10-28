# A5 (v2, sources A5b) — Aura N&B, Bally Bagayoko (maire LFI de Saint-Denis), son « Freeze Raël » (Freeze Corleone, nettoyé).
# v1 (rassemblement CLPRESS, voix saturée) refusée par Luca : genA5_v1.py / plan-A5_v1.json / out/_v1.
# Aperçu HORS Resolve (ffmpeg/numpy). Règles : 9:16 plein écran, aucun visage coupé, aucun logo (filigrane MELENCHON2027.fr en haut
# à droite du meeting, logo LE MÉDIA en haut à gauche exclus par le cadrage), coupes sur les temps (68,5 BPM, drop 808 à 6,22 s
# de l'extrait), plans >= 1 temps, poussée lente avant seulement, <= 15 s, N&B adouci (fond blanc au soleil tenu).
# Usage : python genA5.py [shots] [cards] [audio] [plan] [apercu]   (sans argument = tout)
import sys, os, json, subprocess, math, functools
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
ROOT = "/Users/luca.grousset/Movies/highkey-gauchiste"; LOT = ROOT + "/lot2"
sys.path.insert(0, ROOT + "/_claude/outils")
import framing
from framing import plan_views
from fx import gblur, motion_blur, vignette, to8, ease_out
D = LOT + "/_claude/gen/A5/"; OUT = D + "out/"; os.makedirs(OUT, exist_ok=True)
framing.ROOT = LOT; framing.CACHE = D + "cache"
framing.head_box = lambda f: (f[0] - 0.12 * f[2], f[1] - 0.5 * f[3], f[0] + 1.12 * f[2], f[1] + 1.2 * f[3])
framing.view_for = functools.partial(framing.view_for, margin=0.04)
FF = "/opt/homebrew/bin/ffmpeg"; FPS = 30; W, H = 1080, 1920
RED = (0xE4, 0x00, 0x2B); WHITE = (255, 255, 255)
F_BLACK = "/System/Library/Fonts/Supplemental/Arial Black.ttf"
F_AURA = ("/System/Library/Fonts/Helvetica.ttc", 2)
MA, MB, MC = "A5b-bagayoko-meeting-a.mp4", "A5b-bagayoko-meeting-b.mp4", "A5b-bagayoko-meeting-c.mp4"
LA, LB = "A5b-bagayoko-lemedia-a.mp4", "A5b-bagayoko-lemedia-b.mp4"
SFPS = {MA: 30, MB: 30, MC: 30, LA: 25, LB: 25}
# zones source utilisables : meeting = filigrane MELENCHON2027.fr x 1590-1890 / y 60-170 -> fenêtre à gauche de x 1570 ;
# Le Média = logo x 90-360 / y 45-105 -> fenêtre à droite de x 380.
B_MT = (0, 0, 1570, 1080); B_LMD = (380, 0, 1920, 1080)
# ---------------- grille musicale (sons-lot2.json, A5) ----------------
SON = json.load(open(LOT + "/_claude/sons-lot2.json"))["sons"]
SON = next(s for s in (SON.values() if isinstance(SON, dict) else SON) if s["id"] == "A5")
BEATS = SON["beats_s"]; MUS_OFF = BEATS[2]                 # la musique démarre 2 temps dans l'extrait -> drop (temps 7) à T = 4,38 s
def beat(k): return BEATS[2 + k] - MUS_OFF                 # temps k de la timeline (s)
def fr(t): return int(round(t * FPS))
DROP_K = 5; END_K = 17; END = beat(END_K)                   # 14,90 s
# ---------------- plans ----------------
# white = blanc de sortie (fond blanc en plein soleil du meeting tenu plus bas pour garder la matière)
SHOTS = {
    "long":   dict(src=MB, t=16.37, face=(945, 300), b=B_MT, vh=760, zoom=(1.0, 1.06), top=0.10, white=0.80,
                   why="« Eh oui, on va gagner ! » gros plan au pupitre SAINT-DENIS, son synchrone, la foule hurle après"),
    "foule":  dict(src=MB, t=3.00, fixed=(860, 600), b=B_MT, vh=760, zoom=(1.0, 1.05), white=0.84, why="place noire de monde devant l'hôtel de ville"),
    "sourire": dict(src=MC, t=39.30, face=(1000, 290), b=B_MT, vh=820, zoom=(1.0, 1.05), top=0.10, white=0.80, why="sourire, main levée vers la foule"),
    "place":  dict(src=MC, t=25.00, fixed=(800, 620), b=B_MT, vh=700, zoom=(1.0, 1.05), white=0.84, why="foule en liesse, drapeaux"),
    "pupitre": dict(src=MC, t=50.30, face=(885, 330), b=B_MT, vh=820, zoom=(1.0, 1.05), top=0.10, white=0.80, why="au pupitre, regard sur la foule"),
    "dos":    dict(src=MB, t=29.60, fixed=(960, 600), b=B_MT, vh=960, zoom=(1.0, 1.04), speed=60, white=0.82, why="de dos au pupitre face à la mer de drapeaux"),
    "pointe": dict(src=MC, t=42.00, face=(980, 230), b=B_MT, vh=820, zoom=(1.0, 1.05), top=0.10, white=0.80, why="index levé, éclat de rire"),
    "basilique": dict(src=MB, t=23.00, fixed=(820, 640), b=B_MT, vh=700, zoom=(1.0, 1.05), white=0.84, why="place pleine devant la basilique"),
    "rire":   dict(src=MC, t=38.40, face=(1000, 250), b=B_MT, vh=820, zoom=(1.0, 1.05), top=0.10, white=0.80, why="sourire de face, seul au pupitre"),
}
EDIT = [("long", 3, "cut"),
        ("foule", 1, "drop"), ("sourire", 1, "whip"), ("place", 1, "whip"), ("pupitre", 1, "whip"),
        ("dos", 2, "cut"), ("aura", 1, "cut"),
        ("pointe", 1, "drop"), ("basilique", 1, "whip"), ("rire", 1, "whip")]
# Le Média écarté : le logo LE MÉDIA est imprimé sur la bonnette du micro, collée au visage (impossible à sortir du cadre).
# ---------------- look N&B (identique au test 1) ----------------
RNG = np.random.default_rng(11)
def grade(bgr, white=0.87):
    """N&B adouci (retour Luca 26/10 : contraste pas trop appuyé) : courbe en S légère, ombres relevées (détail du visage
    à l'ombre), blancs tenus sous ~#E6, glow/bloom réduits. Avant : (g-0,07)/0,85, S 55 %, sortie 0,008-0,87."""
    g = (0.114 * bgr[..., 0] + 0.587 * bgr[..., 1] + 0.299 * bgr[..., 2])
    g = np.clip((g - 0.02) / 0.96, 0, 1)
    g = g ** 0.82                                                # relève les ombres (visage à contre-jour)
    g = 0.78 * g + 0.22 * (g * g * (3 - 2 * g))                  # S léger
    g = g / (1 + 0.18 * g) * 1.18                                # épaule douce : hautes lumières compressées, pas brûlées
    small = cv2.resize(g, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    hi = np.clip(small - 0.70, 0, None) * 1.5
    glow = cv2.resize(cv2.GaussianBlur(hi, (0, 0), 9), (W, H)) * 0.25
    soft = cv2.resize(cv2.GaussianBlur(small, (0, 0), 4), (W, H))
    g = 1 - (1 - g) * (1 - 0.10 * soft) + glow
    g = vignette(g[..., None], 0.30, 2.4)[..., 0]
    g = 0.035 + np.clip(g, 0, 1) * (white - 0.035)                          # noirs ~#090909 (pas écrasés), blancs ~#E6
    g = g + RNG.normal(0, 0.016, g.shape).astype(np.float32)
    return np.repeat(np.clip(g, 0, 1)[..., None], 3, 2)
# ---------------- lecture source (ffmpeg, image exacte) ----------------
def read_frames(src, t, n_out, speed=1.0):
    """n_out images à 30 i/s depuis t ; speed < 1 = ralenti simple (aperçu seulement, image la plus proche)."""
    sf = SFPS[src]; need = [int(round(i * speed * sf / FPS)) for i in range(n_out)]; n_src = need[-1] + 1
    p = subprocess.run([FF, "-v", "error", "-ss", "%.4f" % t, "-i", LOT + "/sources/" + src, "-frames:v", str(n_src),
                        "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True)
    a = np.frombuffer(p.stdout, np.uint8).reshape(-1, 1080, 1920, 3)
    return [a[min(i, len(a) - 1)].astype(np.float32) / 255 for i in need], int(round(t * sf))
def crop_916(img, cx, cy, vh):
    vw = vh * 9 / 16; s = W / vw
    M = np.float32([[s, 0, W / 2 - cx * s], [0, s, H / 2 - cy * s]])
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
# ---------------- texte (Arial Black, contour noir + ombre douce, mot-clé rouge) ----------------
def font(size): return ImageFont.truetype(F_BLACK, max(8, int(size)))
def fit_size(txt, maxw, start=260):
    s = start
    while font(s).getlength(txt) > maxw: s -= 4
    return s
# mots réels (derush-AG A5b, Whisper) : Eh 17,12 / oui 17,86 / on 18,10 / va 18,16 / gagner 18,26-18,56 (puis clameur)
# Zone sûre TikTok (26/10) : bloc <= 66 % de large centré (x 183-897), y 0,12-0,75 (230-1440) ; lettres >= 70 px.
# « EH OUI ON VA » sur une ligne ne tenait qu'à 82 px (lettres 59 px) -> 2 lignes, GAGNER rouge en 3e ligne.
TXT_MAXW = 600     # largeur max d'une ligne (marge pour le contour et l'entrée à 112 % du dernier mot : 600 x 1,12 = 672 < 713)
CARDS = [  # carton = lignes ; ligne = (taille, y_centre, [(mot, t_apparition, couleur)]) ; jamais de guillemets
    [(120, 1000, [("EH", 17.12, WHITE), ("OUI", 17.86, WHITE)]), (120, 1150, [("ON", 18.10, WHITE), ("VA", 18.16, WHITE)]),
     (None, None, [("GAGNER", 18.26, RED)])],
]
def layout(card):
    """positions finales de chaque mot (la ligne ne bouge pas quand un mot apparaît)."""
    out = []; y_prev = None; s_prev = None
    for size, yc, words in card:
        txt = " ".join(w for w, _, _ in words)
        if size is None: size = min(fit_size(txt, TXT_MAXW), 300); yc = y_prev + s_prev * 0.5 + 40 + size * 0.5
        else: size = fit_size(txt, TXT_MAXW, start=size)
        f = font(size); total = f.getlength(txt); x = (W - total) / 2
        for w, t, col in words:
            out.append(dict(w=w, t=t, col=col, size=size, x=x, yc=yc)); x += f.getlength(w + " ")
        y_prev, s_prev = yc, size
    return out
LAY = [layout(c) for c in CARDS]
def draw_words(items, scale_last=1.0, alpha_last=1.0):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay); ds = ImageDraw.Draw(sh)
    for k, it in enumerate(items):
        last = k == len(items) - 1; sc = scale_last if last else 1.0
        f = font(it["size"] * sc); sw = max(4, int(it["size"] * 0.045))
        wfull = font(it["size"]).getlength(it["w"]); wnow = f.getlength(it["w"])
        x = it["x"] + (wfull - wnow) / 2
        x0, y0, x1, y1 = d.textbbox((0, 0), it["w"], font=f); y = it["yc"] - (y1 - y0) / 2 - y0
        a = int(255 * (alpha_last if last else 1.0))
        ds.text((x, y + it["size"] * 0.05), it["w"], font=f, fill=(0, 0, 0, int(a * 0.78)), stroke_width=sw * 3, stroke_fill=(0, 0, 0, int(a * 0.78)))
        d.text((x, y), it["w"], font=f, fill=it["col"] + (a,), stroke_width=sw, stroke_fill=(0, 0, 0, a))
    sh = sh.filter(ImageFilter.GaussianBlur(18))
    return np.asarray(Image.alpha_composite(sh, lay)).astype(np.float32) / 255
def long_text(t_src):
    ci = 1 if len(CARDS) > 1 and t_src >= CARDS[1][0][2][0][1] else 0
    vis = [(sz, y, [w for w in ws if t_src >= w[1]]) for sz, y, ws in CARDS[ci]]
    vis = [l for l in vis if l[2]]
    if not vis: return None
    on = layout(vis)                                                   # ligne recentrée à chaque mot (pas de mot seul collé à gauche)
    if not on: return None
    k = (t_src - on[-1]["t"]) * FPS; e = ease_out(min(k / 3.0, 1.0))      # entrée 3 images, sans rebond
    return draw_words(on, scale_last=1.12 - 0.12 * e, alpha_last=min(1.0, 0.35 + e))
def over_rgba(img_bgr, rgba):
    a = rgba[..., 3:4]; rgb = rgba[..., 2::-1]
    return img_bgr * (1 - a) + rgb * a
# ---------------- rendu ----------------
def write_mov(frames, path, fps=FPS):
    p = subprocess.Popen([FF, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", "%dx%d" % (W, H), "-r", str(fps), "-i", "-",
                          "-c:v", "prores_ks", "-profile:v", "3", "-pix_fmt", "yuv422p10le", "-vendor", "apl0", path], stdin=subprocess.PIPE)
    for f in frames: p.stdin.write(to8(f).tobytes())
    p.stdin.close(); p.wait()
def slots():
    out = []; k = 2
    for sid, nb, eff in EDIT:
        out.append((sid, nb, eff, k, fr(beat(k)), fr(beat(k + nb)))); k += nb
    return out
def render_slot(sid, eff, a, b):
    sh = SHOTS[sid]; n = b - a
    raw, s0 = read_frames(sh["src"], sh["t"], n)          # vitesse normale (le ralenti est fait à l'aperçu / dans Resolve)
    z0, z1 = sh["zoom"]; zoom = lambda f: z0 + (z1 - z0) * f / max(n - 1, 1)
    if "fixed" in sh:
        sf = SFPS[sh["src"]]; views, _ = plan_views(sh["src"], s0, n, sf, speed=sf / FPS, bounds=sh["b"], vh=sh["vh"], zoom=zoom, fixed=sh["fixed"])
    else:
        sf = SFPS[sh["src"]]; views, ok = plan_views(sh["src"], s0, n, sf, speed=sf / FPS, hint=sh["face"], bounds=sh["b"], vh=sh["vh"], zoom=zoom, top=sh["top"])
        if not ok: print("  ! pas de visage :", sid)
    frames = []
    for i, (img, (cx, cy, vh)) in enumerate(zip(raw, views)):
        g = grade(crop_916(img, cx, cy, vh), sh.get("white", 0.87))
        if sid == "long":
            tl = long_text(sh["t"] + i / FPS)
            if tl is not None: g = over_rgba(g, tl)
        if eff == "whip" and i < 3: g = motion_blur(g, 0, [220, 90, 25][i], steps=16)
        if eff == "drop" and i < 8:
            k = (1 - i / 8) ** 2; g = np.clip(g + k * 0.55 + gblur(g, 25) * k * 0.6, 0, 1)
        frames.append(g)
    name = "A5_%s_%s.mov" % (sid, eff); write_mov(frames, OUT + name)
    vx = views[0]; vz = views[-1]
    print("  %-7s %3d im  vue %d,%d h%d -> h%d  (x %d-%d)" % (sid, n, vx[0], vx[1], vx[2], vz[2], vx[0] - vx[2] * 9 / 32, vx[0] + vx[2] * 9 / 32))
    return name
def aura_card(n, fade_in=3, fade_out=0):
    im = Image.new("L", (W, H), 0); d = ImageDraw.Draw(im); f = ImageFont.truetype(F_AURA[0], 120, index=F_AURA[1])
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
    write_mov(aura_card(fr(beat(2))), OUT + "A5_aura_intro.mov")
    write_mov(aura_card(fr(beat(1)) + 2), OUT + "A5_aura.mov")
    write_mov(aura_card(fr(END) - fr(beat(15)), fade_in=3, fade_out=12), OUT + "A5_aura_fin.mov")
# ---------------- plan ----------------
def build_plan():
    video = []
    def add(id_, clip, s, e, rec, kind, extra=None):
        v = {"id": id_, "clip": clip, "folder": "genA5", "s": s, "e": e, "rec": rec, "track": 1, "kind": kind}
        if extra: v.update(extra)
        video.append(v)
    add("hook", "A5_aura_intro.mov", 0, fr(beat(2)), 0, "card")
    for sid, nb, eff, k, a, b in slots():
        if sid == "aura": add("aura_%d" % a, "A5_aura.mov", 0, b - a, a, "card"); continue
        sh = SHOTS[sid]; extra = {"source": "lot2/sources/%s @ %.2f s" % (sh["src"], sh["t"]), "effet": eff, "temps": nb, "pourquoi": sh["why"]}
        if sid == "long": extra["texte"] = "CE / COMBAT (rouge) · NOUS ALLONS / LE GAGNER (mot à mot, Arial Black)"
        if sh.get("speed"): extra.update({"speed_pct": sh["speed"], "retime": "optical_flow"})
        add("%s_%d" % (sid, a), "A5_%s_%s.mov" % (sid, eff), 0, b - a, a, "shot", extra)
    add("fin", "A5_aura_fin.mov", 0, fr(END) - fr(beat(15)), fr(beat(15)), "card")
    plan = {"name": "A5 - Aura N&B - Bally Bagayoko", "fps": FPS, "w": W, "h": H, "duree_s": round(END, 3),
            "note": "Plans 9:16 recadrés + étalonnés N&B (lot2/_claude/gen/A5/out), vitesse normale. s/e en images du clip (30 i/s), rec en images timeline. "
                    "speed_pct : ralenti Resolve Optical Flow + Speed Warp (aperçu = setpts simple). Coupes sur les temps (68,5 BPM, 0,876 s), drop 808 à 4,38 s.",
            "phrase": {"texte": "Eh oui, on va gagner !", "source": "lot2/sources/" + MB + " 17,12-18,56 s, clameur jusqu'à 20,3 s (YouTube 1dkY_JVFx9I, chaîne officielle JLM, meeting de Saint-Denis 07/06/2026)",
                       "timeline_s": [round(beat(2) + 17.12 - SHOTS["long"]["t"], 2), round(beat(2) + 18.56 - SHOTS["long"]["t"], 2)]},
            "video": video,
            "audio": [{"id": "mix", "clip": "A5-mix.wav", "folder": "genA5", "rec": 0, "track": 1, "note": "mix -14 LUFS"}],
            "musique": {"fichier": "lot2/sons/A5-freeze-rael.wav", "debut_dans_extrait_s": round(MUS_OFF, 3),
                        "debut_dans_complet_s": round(SON["extrait"]["debut_dans_complet_s"] + MUS_OFF, 3), "gain_db": SON["niveau"]["gain_conseille_db_vers_moins14LUFS"],
                        "titre": "Freeze Raël - Freeze Corleone (%s)" % SON["url"]},
            "stems": ["lot2/_claude/gen/A5/out/A5-voix.wav", "lot2/_claude/gen/A5/out/A5-musique.wav"],
            "logos_exclus": "filigrane MELENCHON2027.fr (fenêtre x <= 1570), logo LE MÉDIA en haut à gauche (fenêtre x >= 380)",
            "version": "v2 (sources A5b) ; v1 refusée : plan-A5_v1.json"}
    json.dump(plan, open(D + "plan-A5.json", "w"), indent=1, ensure_ascii=False)
    return plan
# ---------------- audio ----------------
def make_audio():
    import soundfile as sf
    sr = 48000; N = int(round(END * sr))
    def grab(path, t, dur):
        p = subprocess.run([FF, "-v", "error", "-ss", "%.3f" % t, "-t", "%.3f" % dur, "-i", path, "-ac", "2", "-ar", str(sr), "-f", "f32le", "-"], capture_output=True)
        return np.frombuffer(p.stdout, np.float32).reshape(-1, 2).copy()
    def place(buf, x, t, gain_db=0, fin=0.0, fout=0.0):
        g = 10 ** (gain_db / 20); n = len(x); env = np.ones(n, np.float32)
        if fin: m = int(fin * sr); env[:m] = np.linspace(0, 1, m)
        if fout: m = int(fout * sr); env[-m:] *= np.linspace(1, 0, m)
        a = int(t * sr); b = min(N, a + n); buf[a:b] += x[:b - a] * env[:b - a, None] * g
    voix = np.zeros((N, 2), np.float32); mus = np.zeros((N, 2), np.float32)
    v_in, v_out = 17.00, 20.34                                   # « Eh oui, on va gagner ! » + clameur de la foule (non coupée net)
    t_v = beat(2) + v_in - SHOTS["long"]["t"]
    place(voix, grab(LOT + "/sources/" + MB, v_in, v_out - v_in), t_v, +3, fin=0.05, fout=0.9)
    place(mus, grab(LOT + "/" + SON["fichier"], MUS_OFF, END + 0.1), 0.0, SON["niveau"]["gain_conseille_db_vers_moins14LUFS"], fin=0.02, fout=0.7)
    # ducking de la musique sous la phrase (-9 dB) jusqu'au drop : la clameur continue sous le 808
    env = np.ones(N, np.float32); d0, d1, r = int((t_v - 0.1) * sr), int((beat(DROP_K) - 0.04) * sr), int(0.12 * sr)
    lo = 10 ** (-9 / 20); env[d0:d1] = lo; env[d0 - r:d0] = np.linspace(1, lo, r); env[d1:d1 + r] = np.linspace(lo, 1, r)
    mus *= env[:, None]
    sf.write(OUT + "A5-voix.wav", voix, sr, subtype="PCM_24"); sf.write(OUT + "A5-musique.wav", mus, sr, subtype="PCM_24")
    sf.write(D + "tmp_mix.wav", voix + mus, sr, subtype="FLOAT")
    r_ = subprocess.run([FF, "-hide_banner", "-i", D + "tmp_mix.wav", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                        capture_output=True, text=True).stderr
    js = json.loads(r_[r_.rindex("{"):r_.rindex("}") + 1])
    af = ("loudnorm=I=-14:TP=-1.5:LRA=11:measured_I=%s:measured_TP=%s:measured_LRA=%s:measured_thresh=%s:offset=%s:linear=true,alimiter=limit=0.85:level=false:attack=1:release=60,aresample=48000"
          % (js["input_i"], js["input_tp"], js["input_lra"], js["input_thresh"], js["target_offset"]))
    subprocess.run([FF, "-v", "error", "-y", "-i", D + "tmp_mix.wav", "-af", af, "-c:a", "pcm_s24le", OUT + "A5-mix.wav"], check=True)
    os.remove(D + "tmp_mix.wav")
# ---------------- aperçu 540x960 ----------------
def apercu():
    plan = json.load(open(D + "plan-A5.json")); ins = []; fl = []
    for i, v in enumerate(plan["video"]):
        n = v["e"] - v["s"]; sp = v.get("speed_pct", 100) / 100
        ins += ["-i", OUT + v["clip"]]
        if sp < 1:
            fl.append("[%d:v]trim=start_frame=%d:end_frame=%d,setpts=(PTS-STARTPTS)/%.4f,fps=30,trim=end_frame=%d,setpts=PTS-STARTPTS,scale=540:960,setsar=1[v%d]"
                      % (i, v["s"], v["s"] + math.ceil(n * sp) + 1, sp, n, i))
        else:
            fl.append("[%d:v]trim=start_frame=%d:end_frame=%d,setpts=PTS-STARTPTS,scale=540:960,setsar=1[v%d]" % (i, v["s"], v["e"], i))
    k = len(plan["video"])
    fl.append("".join("[v%d]" % i for i in range(k)) + "concat=n=%d:v=1:a=0[v]" % k)
    ins += ["-i", OUT + "A5-mix.wav"]
    out = ROOT + "/preview/apercu-A5.mp4"          # Luca 26/10 : aperçus dans ~/Movies/highkey-gauchiste/preview
    subprocess.run([FF, "-v", "error", "-y"] + ins + ["-filter_complex", ";".join(fl), "-map", "[v]", "-map", "%d:a" % k,
                    "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "aac", "-b:a", "192k", "-shortest", out], check=True)
    print("aperçu", out)
if __name__ == "__main__":
    args = set(sys.argv[1:]) or {"shots", "cards", "audio", "plan", "apercu"}
    only = [a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("only=")]
    if "shots" in args or only:
        for sid, nb, eff, k, a, b in slots():
            if sid != "aura" and (not only or sid in only): render_slot(sid, eff, a, b)
    if "cards" in args: make_cards()
    if "plan" in args: build_plan()
    if "audio" in args: make_audio()
    if "apercu" in args: apercu()
