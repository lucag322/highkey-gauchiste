# A7 (lot 3) — Aura N&B, Rima Hassan (eurodéputée LFI), son « Billie Jean » (Michael Jackson, vidéo officielle Zi_XLOBDo_Y).
# Modèle : lot2/_claude/gen/A5/genA5.py (aura validée : N&B adouci, Arial Black, mot-clé rouge, carte « aura. » Helvetica Oblique).
# Aperçu HORS Resolve (ffmpeg/numpy). Règles : 9:16 plein écran, aucun visage coupé, aucun logo (ELA en haut à droite et bas du
# pupitre à Strasbourg, logo LFI + pupitre « Aly2026 » à La Courneuve, exclus par les fenêtres), coupes sur les VRAIES frappes
# (kick / caisse claire détectés, hits.py), plans >= 1 temps, poussée lente avant seulement, <= 15 s, pas de ralenti précalculé.
# Structure (retour Luca 26/10 : drop sur le refrain) : fin du pré-refrain « …told me, be careful who you love » (80,4 s du titre) =
# carte « aura. » puis la phrase de Rima Hassan (voix audible, musique baissée dessous), la montée reprend après la phrase,
# carte « aura. » sur le dernier temps, DROP sur « Billie Jean » du 1er refrain (87,07 s du titre), coupes sur les frappes.
# Usage : python genA7.py [shots] [cards] [audio] [plan] [apercu] [only=id]   (sans argument = tout)
import sys, os, json, subprocess, math, functools
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
ROOT = "/Users/luca.grousset/Movies/highkey-gauchiste"; LOT = ROOT + "/lot3"
sys.path.insert(0, ROOT + "/_claude/outils")
import framing
from framing import plan_views
from fx import gblur, motion_blur, vignette, to8, ease_out
D = LOT + "/_claude/gen/A7/"; OUT = D + "out/"; os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, D)
framing.ROOT = LOT; framing.CACHE = D + "cache"
framing.head_box = lambda f: (f[0] - 0.12 * f[2], f[1] - 0.5 * f[3], f[0] + 1.12 * f[2], f[1] + 1.2 * f[3])
framing.view_for = functools.partial(framing.view_for, margin=0.04)
FF = "/opt/homebrew/bin/ffmpeg"; FPS = 30; W, H = 1080, 1920
RED = (0xE4, 0x00, 0x2B); WHITE = (255, 255, 255)
F_BLACK = "/System/Library/Fonts/Supplemental/Arial Black.ttf"
F_AURA = ("/System/Library/Fonts/Helvetica.ttc", 2)
SA, SB, SC, SP = ("A7-hassan-strasbourg-a.mp4", "A7-hassan-strasbourg-b.mp4", "A7-hassan-strasbourg-c.mp4", "A7-hassan-strasbourg-phrase.mp4")
CA = "A7-hassan-courneuve-a.mp4"
YT = {SA: ("lML9ZGssEac", 2195), SB: ("lML9ZGssEac", 2368), SC: ("lML9ZGssEac", 2634), SP: ("lML9ZGssEac", 2286), CA: ("bpYEswmz7us", 925)}
SFPS = {SA: 30, SB: 30, SC: 30, SP: 30, CA: 30}
# fenêtres source sans logo : Strasbourg = logo ELA x 1615-1820 / y 95-160, pupitre (texte + logos) y > 912 coupé entièrement ; voisine de scène x < 130.
# La Courneuve = logo LFI x > 1690 en haut, pupitre (Aly2026 + logo LFI) y > 715.
B_ST = (130, 0, 1600, 912); B_WIDE = (0, 0, 1600, 1080); B_CO = (300, 0, 1680, 715)
# ---------------- son : vraies frappes ----------------
SON_FULL = LOT + "/sons/A7-billie-jean-full.wav"; SON_EXT = LOT + "/sons/A7-billie-jean.wav"
HITS_JS = D + "cache/hits-refrain.json"
MUS_T0 = 80.377                                           # frappe où démarre l'extrait (13 temps avant « Billie Jean » 87,07 s ; « be careful who you love » 81,0 s)
def load_hits():
    if not os.path.exists(HITS_JS):
        import hits as HT
        _, b0, P = HT.hits(SON_FULL, MUS_T0, 32)                  # grille ajustée (tempo de la boîte à rythmes)
        h = HT.template_hits(SON_FULL, b0 + np.arange(32) * P)       # frappe réelle de chaque temps (gabarit, robuste à la voix)
        os.makedirs(D + "cache", exist_ok=True)
        json.dump({"hits": [round(float(x), 4) for x in h], "b0": float(b0), "P": float(P)}, open(HITS_JS, "w"))
    return json.load(open(HITS_JS))
HJ = load_hits(); HITS = HJ["hits"]; BEAT = HJ["P"]
MUS_OFF = HITS[0] - 0.02                                  # 1re frappe de l'extrait à 0,02 s (attaque intacte)
def beat(k): return HITS[k] - MUS_OFF                     # temps k de la timeline (vraie frappe)
def fr(t): return int(round(t * FPS))
DROP_K = 13; END_K = 28; END = beat(END_K)                # « Billie Jean » au temps 13 ; fin 14,4 s
# ---------------- phrase (Whisper sur A7-hassan-strasbourg-phrase.mp4 = YouTube lML9ZGssEac + 2286 s) ----------------
# Être 7,02 · de 7,56 · gauche 7,84 · ce 8,52 · n'est 8,84 · pas 9,00 · une 9,22 · étiquette 9,66-10,22 · (C'est 10,42 : coupé)
W_ETIQ = 9.66
PH_OFF = beat(3) + 0.10 - 7.02                            # timeline = temps fichier + PH_OFF (« Être » 100 ms après la coupe du temps 3)
# ---------------- plans ----------------
SHOTS = {
    "long":    dict(src=SP, face=(940, 300), b=B_ST, vh=1000, zoom=(1.0, 1.07), top=0.08, white=0.86,
                    why="Être de gauche, ce n'est pas une étiquette. (pupitre JUSTICE POUR LA PALESTINE, Strasbourg 17/06/2026)"),
    "dos":     dict(src=SA, t=8.00, fixed=(1020, 540), b=B_WIDE, vh=1080, zoom=(1.0, 1.04), white=0.86, why="de dos au pupitre face à la salle"),
    "poing":   dict(src=SB, t=43.40, face=(920, 365), b=B_ST, vh=1000, zoom=(1.0, 1.05), top=0.10, white=0.86, why="poing levé"),
    "salle":   dict(src=SA, t=33.00, fixed=(960, 560), b=B_WIDE, vh=1080, zoom=(1.0, 1.04), white=0.86, why="salle comble debout"),
    "courneuve": dict(src=CA, t=12.30, face=(910, 260), b=B_CO, vh=715, zoom=(1.0, 1.04), top=0.10, white=0.86, why="poing levé, meeting de La Courneuve 16/01/2026"),
    "rire":    dict(src=SC, t=32.60, face=(640, 290), b=B_ST, vh=1000, zoom=(1.0, 1.05), top=0.10, white=0.86, why="grand sourire, main levée vers la salle"),
    "salle2":  dict(src=SB, t=28.00, fixed=(960, 560), b=B_WIDE, vh=1080, zoom=(1.0, 1.04), white=0.86, why="salle, mains levées"),
    "emotion": dict(src=SC, t=12.60, face=(885, 305), b=B_ST, vh=1000, zoom=(1.0, 1.05), top=0.10, white=0.86, why="émue sous les « Rima ! Rima ! »"),
    "salut":   dict(src=SC, t=25.30, face=(920, 290), b=B_ST, vh=1000, zoom=(1.0, 1.05), top=0.10, white=0.86, why="salue la salle"),
    "geste":   dict(src=SP, t=3.00, face=(940, 300), b=B_ST, vh=1000, zoom=(1.0, 1.05), top=0.10, white=0.86, why="au pupitre, geste vers la salle"),
    "main":    dict(src=SC, t=26.80, face=(1000, 325), b=B_ST, vh=1000, zoom=(1.0, 1.04), top=0.10, white=0.86, speed=60, why="sourire, main levée"),
    "ovation": dict(src=SC, t=41.00, fixed=(1110, 560), b=B_WIDE, vh=1080, zoom=(1.0, 1.04), white=0.86, why="scène debout, ovation"),
    "eclat":   dict(src=SC, t=29.00, face=(1000, 270), b=B_ST, vh=1000, zoom=(1.0, 1.05), top=0.10, white=0.86, why="éclat de rire"),
    "sourire": dict(src=SA, t=5.00, face=(960, 300), b=B_ST, vh=1000, zoom=(1.0, 1.04), top=0.10, white=0.86, why="sourire au pupitre"),
}
EDIT = [("long", 7, "cut"),                                             # temps 3-10 : la phrase, musique baissée
        ("geste", 1, "cut"), ("sourire", 1, "whip"), ("aura", 1, "cut"),  # la montée reprend, « aura. » juste avant le drop
        ("dos", 1, "drop"), ("poing", 1, "whip"), ("salle", 1, "whip"), ("rire", 1, "whip"),   # drop « Billie Jean » (temps 13)
        ("courneuve", 2, "cut"), ("emotion", 1, "whip"), ("salut", 1, "whip"),
        ("main", 2, "cut"), ("ovation", 1, "whip"), ("eclat", 1, "whip")]
HOOK_K = 3; FIN_K = 25
# ---------------- look N&B (identique à A5 lot 2, validé) ----------------
RNG = np.random.default_rng(7)
def grade(bgr, white=0.87):
    # éclairage magenta/rouge de Strasbourg : un peu plus de rouge dans la luminance (peau moins sombre), sinon recette A5
    g = (0.10 * bgr[..., 0] + 0.52 * bgr[..., 1] + 0.38 * bgr[..., 2])
    g = np.clip((g - 0.02) / 0.96, 0, 1)
    g = g ** 0.82
    g = 0.78 * g + 0.22 * (g * g * (3 - 2 * g))
    g = g / (1 + 0.18 * g) * 1.18
    small = cv2.resize(g, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    hi = np.clip(small - 0.70, 0, None) * 1.5
    glow = cv2.resize(cv2.GaussianBlur(hi, (0, 0), 9), (W, H)) * 0.25
    soft = cv2.resize(cv2.GaussianBlur(small, (0, 0), 4), (W, H))
    g = 1 - (1 - g) * (1 - 0.10 * soft) + glow
    g = vignette(g[..., None], 0.30, 2.4)[..., 0]
    g = 0.035 + np.clip(g, 0, 1) * (white - 0.035)
    g = g + RNG.normal(0, 0.016, g.shape).astype(np.float32)
    return np.repeat(np.clip(g, 0, 1)[..., None], 3, 2)
# ---------------- lecture source ----------------
def read_frames(src, t, n_out, speed=1.0):
    sf = SFPS[src]; need = [int(round(i * speed * sf / FPS)) for i in range(n_out)]; n_src = need[-1] + 1
    p = subprocess.run([FF, "-v", "error", "-ss", "%.4f" % t, "-i", LOT + "/sources/" + src, "-frames:v", str(n_src),
                        "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True)
    a = np.frombuffer(p.stdout, np.uint8).reshape(-1, 1080, 1920, 3)
    return [a[min(i, len(a) - 1)].astype(np.float32) / 255 for i in need], int(round(t * sf))
def crop_916(img, cx, cy, vh):
    vw = vh * 9 / 16; s = W / vw
    M = np.float32([[s, 0, W / 2 - cx * s], [0, s, H / 2 - cy * s]])
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
# ---------------- texte (Arial Black, contour noir + ombre douce, mot-clé rouge, jamais de guillemets) ----------------
def font(size): return ImageFont.truetype(F_BLACK, max(8, int(size)))
def fit_size(txt, maxw, start=260):
    s = start
    while font(s).getlength(txt) + 2 * max(4, int(s * 0.045)) > maxw: s -= 2     # contour compris
    return s
# zone sûre TikTok (retour Luca : textes sous l'interface) : bloc <= 66 % de large centré (x 184-896), y 230-1440.
# La phrase ne tient plus en un bloc sous le visage : 2 cartons (ÊTRE DE / GAUCHE, puis CE N'EST / PAS UNE / ÉTIQUETTE),
# lignes coupées en 2, hauteur de lettre >= ~70 px, bloc sous le menton (haut ~1020) et bas <= 1400.
TXT_W = 700; X_MIN, X_MAX = int(W * 0.17) + 6, int(W * 0.83) - 6; Y0 = 1060
CARDS = [[(118, Y0, [("ÊTRE", 7.02, WHITE), ("DE", 7.56, WHITE)]), (118, None, [("GAUCHE", 7.84, RED)])],
         [(100, Y0, [("CE", 8.52, WHITE), ("N'EST", 8.84, WHITE)]), (100, None, [("PAS", 9.00, WHITE), ("UNE", 9.22, WHITE)]),
          (170, None, [("ÉTIQUETTE", W_ETIQ, WHITE)])]]
def layout(card):
    out = []; y_prev = None; s_prev = None
    for size, yc, words in card:
        txt = " ".join(w for w, _, _ in words)
        size = fit_size(txt, TXT_W, start=size)
        if yc is None: yc = y_prev + s_prev * 0.5 + 34 + size * 0.5
        f = font(size); total = f.getlength(txt); x = (W - total) / 2
        for w, t, col in words:
            out.append(dict(w=w, t=t, col=col, size=size, x=x, yc=yc)); x += f.getlength(w + " ")
        y_prev, s_prev = yc, size
    return out
FULLS = [layout(c) for c in CARDS]
def draw_words(items, scale_last=1.0, alpha_last=1.0):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay); ds = ImageDraw.Draw(sh)
    for k, it in enumerate(items):
        last = k == len(items) - 1; sc = scale_last if last else 1.0
        sw = max(4, int(it["size"] * 0.045)); wfull = font(it["size"]).getlength(it["w"])
        sc = min(sc, max(1.0, (X_MAX - X_MIN - 2 * sw) / wfull))                        # mot géant : agrandissement d'entrée plafonné
        f = font(it["size"] * sc); wnow = f.getlength(it["w"])
        x = min(max(it["x"] + (wfull - wnow) / 2, X_MIN + sw), X_MAX - sw - wnow)       # entrée agrandie gardée dans la zone sûre
        x0, y0, x1, y1 = d.textbbox((0, 0), it["w"], font=f); y = it["yc"] - (y1 - y0) / 2 - y0
        a = int(255 * (alpha_last if last else 1.0))
        ds.text((x, y + it["size"] * 0.05), it["w"], font=f, fill=(0, 0, 0, int(a * 0.78)), stroke_width=sw * 3, stroke_fill=(0, 0, 0, int(a * 0.78)))
        d.text((x, y), it["w"], font=f, fill=it["col"] + (a,), stroke_width=sw, stroke_fill=(0, 0, 0, a))
    sh = sh.filter(ImageFilter.GaussianBlur(18))
    return np.asarray(Image.alpha_composite(sh, lay)).astype(np.float32) / 255
def long_text(t_src):
    full = FULLS[1] if t_src >= FULLS[1][0]["t"] - 0.02 else FULLS[0]
    on = [it for it in full if t_src >= it["t"] - 0.02]        # mots posés à leur place finale, apparition au mot prononcé
    if not on: return None
    k = (t_src - on[-1]["t"]) * FPS; e = ease_out(min(k / 3.0, 1.0))
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
    out = []; k = HOOK_K
    for sid, nb, eff in EDIT:
        out.append((sid, nb, eff, k, fr(beat(k)), fr(beat(k + nb)))); k += nb
    assert k == FIN_K, k
    return out
def src_t(sid, a):
    sh = SHOTS[sid]
    return a / FPS - PH_OFF if sid == "long" else sh["t"]       # le plan parlé est synchrone de la voix
def render_slot(sid, eff, a, b):
    sh = SHOTS[sid]; n = b - a; t0 = src_t(sid, a)
    raw, s0 = read_frames(sh["src"], t0, n)
    z0, z1 = sh["zoom"]; zoom = lambda f: z0 + (z1 - z0) * f / max(n - 1, 1)
    sf = SFPS[sh["src"]]
    if "fixed" in sh:
        views, _ = plan_views(sh["src"], s0, n, sf, speed=sf / FPS, bounds=sh["b"], vh=sh["vh"], zoom=zoom, fixed=sh["fixed"])
    else:
        views, ok = plan_views(sh["src"], s0, n, sf, speed=sf / FPS, hint=sh["face"], bounds=sh["b"], vh=sh["vh"], zoom=zoom, top=sh["top"])
        if not ok: print("  ! pas de visage :", sid)
    drop_i = 0 if eff == "drop" else None
    frames = []
    for i, (img, (cx, cy, vh)) in enumerate(zip(raw, views)):
        g = grade(crop_916(img, cx, cy, vh), sh.get("white", 0.87))
        if sid == "long":
            tl = long_text(t0 + i / FPS)
            if tl is not None: g = over_rgba(g, tl)
        if eff == "whip" and i < 3: g = motion_blur(g, 0, [220, 90, 25][i], steps=16)
        if drop_i is not None and 0 <= i - drop_i < 8:
            k = (1 - (i - drop_i) / 8) ** 2; g = np.clip(g + k * 0.55 + gblur(g, 25) * k * 0.6, 0, 1)
        frames.append(g)
    name = "A7_%s.mov" % sid; write_mov(frames, OUT + name)
    vx = views[0]; vz = views[-1]
    print("  %-9s %3d im  src %.2f  vue %d,%d h%d -> h%d  (x %d-%d)" % (sid, n, t0, vx[0], vx[1], vx[2], vz[2], vx[0] - vx[2] * 9 / 32, vx[0] + vx[2] * 9 / 32))
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
    write_mov(aura_card(fr(beat(HOOK_K))), OUT + "A7_aura_intro.mov")
    a, b = [(x[4], x[5]) for x in slots() if x[0] == "aura"][0]
    write_mov(aura_card(b - a), OUT + "A7_aura.mov")
    write_mov(aura_card(fr(END) - fr(beat(FIN_K)), fade_in=3, fade_out=14), OUT + "A7_aura_fin.mov")
# ---------------- plan ----------------
def yt(src, t): vid, off = YT[src]; return "https://youtu.be/%s?t=%d (%.2f s)" % (vid, int(off + t), off + t)
def build_plan():
    video = []
    def add(id_, clip, n, rec, kind, extra=None):
        v = {"id": id_, "clip": clip, "folder": "A7", "path": OUT + clip, "s": 0, "e": n, "clip_fps": 30, "rec": rec, "dur": n,
             "track": 1, "kind": kind}
        if extra: v.update(extra)
        video.append(v)
    add("hook", "A7_aura_intro.mov", fr(beat(HOOK_K)), 0, "card", {"note": "carte aura. (Helvetica Oblique, halo doux) sur la batterie seule"})
    for sid, nb, eff, k, a, b in slots():
        if sid == "aura": add("aura_%d" % a, "A7_aura.mov", b - a, a, "card", {"temps": nb}); continue
        sh = SHOTS[sid]; t0 = src_t(sid, a)
        extra = {"temps": nb, "effet": eff, "note": sh["why"],
                 "source": {"fichier": "lot3/sources/" + sh["src"], "in_s": round(t0, 3), "out_s": round(t0 + (b - a) / FPS, 3), "youtube": yt(sh["src"], t0)}}
        if sid == "long": extra["texte"] = "ÊTRE DE GAUCHE (GAUCHE rouge) / CE N'EST PAS UNE / ÉTIQUETTE (sur le drop, flash) — mot à mot, Arial Black"
        if sh.get("speed"): extra.update({"speed_pct": sh["speed"], "retime": "optical_flow"})
        add("%s_%d" % (sid, a), "A7_%s.mov" % sid, b - a, a, "shot", extra)
    add("fin", "A7_aura_fin.mov", fr(END) - fr(beat(FIN_K)), fr(beat(FIN_K)), "card", {"note": "carte aura. finale, fondu au noir"})
    plan = {"name": "A7 - Aura N&B - Rima Hassan", "fps": FPS, "w": W, "h": H, "duree_s": round(fr(END) / FPS, 3),
            "note": "Aperçu lot 3. Plans ProRes 9:16 recadrés (visage suivi) + N&B A5, texte et effets cuits, vitesse normale. s/e en images du clip (30 i/s), "
                    "rec en images timeline. speed_pct : ralenti Resolve Optical Flow (aperçu = setpts simple). Coupes sur les vraies frappes (cache/hits.json). "
                    "Générateur : lot3/_claude/gen/A7/genA7.py",
            "phrase": {"texte": "Être de gauche, ce n'est pas une étiquette.", "source": yt(SP, 7.02) + " -> 2296,22 s, meeting LFI de soutien à la Palestine, Strasbourg, 17/06/2026 (chaîne La France insoumise)",
                       "timeline_s": [round(7.02 + PH_OFF, 3), round(10.22 + PH_OFF, 3)]},
            "musique": {"fichier": "lot3/sons/A7-billie-jean.wav", "debut_dans_complet_s": round(MUS_OFF, 3), "fin_dans_complet_s": round(MUS_OFF + END, 3),
                        "drop_timeline_s": round(beat(DROP_K), 3), "bpm": round(60 / BEAT, 2)},
            "video": video,
            "audio": [{"id": "mix", "clip": "A7-mix.wav", "folder": "A7", "path": OUT + "A7-mix.wav", "rec": 0, "track": 1,
                       "note": "mix -14 LUFS : Billie Jean du début à la fin (fin du pré-refrain puis 1er refrain), voix synchrone de la phrase, musique baissée -9 dB sous la phrase puis reprise, drop sur « Billie Jean » du refrain"}],
            "stems": [OUT + "A7-voix.wav", OUT + "A7-musique.wav"],
            "logos_exclus": "ELA (haut droite) et logos du bas du pupitre à Strasbourg ; logo LFI et pupitre Aly2026 à La Courneuve"}
    json.dump(plan, open(D + "plan-A7.json", "w"), indent=1, ensure_ascii=False)
    son = {"titre": "Billie Jean", "artiste": "Michael Jackson", "url": "https://youtu.be/Zi_XLOBDo_Y", "chaine": "Michael Jackson (officielle)",
           "fichier_complet": "lot3/sons/A7-billie-jean-full.wav", "fichier_extrait": "lot3/sons/A7-billie-jean.wav",
           "extrait": {"debut_s": round(MUS_OFF, 3), "fin_s": round(MUS_OFF + END, 3)}, "bpm": round(60 / BEAT, 2),
           "drop": {"description": "« Billie Jean » du 1er refrain (après la montée du pré-refrain « And mother always told me… »)", "dans_complet_s": round(HITS[DROP_K], 3), "timeline_s": round(beat(DROP_K), 3)},
           "frappes_dans_complet_s": HITS[:END_K + 1], "frappes_timeline_s": [round(beat(k), 3) for k in range(END_K + 1)],
           "pre_refrain_dans_complet_s": 70.68, "refrain_billie_jean_dans_complet_s": round(HITS[DROP_K], 3),
           "paroles_audibles": "« be careful who you love, be careful what you do, 'cause the lie becomes the truth » sous la phrase (-9 dB) puis « Billie Jean is not my lover, she's just a girl (who claims…) » après le drop"}
    json.dump(son, open(D + "son.json", "w"), indent=1, ensure_ascii=False)
    return plan
# ---------------- audio ----------------
def lufs(path):
    r_ = subprocess.run([FF, "-hide_banner", "-i", path, "-af", "loudnorm=print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
    return json.loads(r_[r_.rindex("{"):r_.rindex("}") + 1])
def make_audio():
    import soundfile as sf
    sr = 48000; N = int(round(fr(END) / FPS * sr))
    def grab(path, t, dur):
        p = subprocess.run([FF, "-v", "error", "-ss", "%.4f" % t, "-t", "%.4f" % dur, "-i", path, "-ac", "2", "-ar", str(sr), "-f", "f32le", "-"], capture_output=True)
        return np.frombuffer(p.stdout, np.float32).reshape(-1, 2).copy()
    def place(buf, x, t, gain_db=0, fin=0.0, fout=0.0):
        g = 10 ** (gain_db / 20); n = len(x); env = np.ones(n, np.float32)
        if fin: m = int(fin * sr); env[:m] = np.linspace(0, 1, m)
        if fout: m = int(fout * sr); env[-m:] *= np.linspace(1, 0, m)
        a = int(round(t * sr)); b = min(N, a + n); buf[a:b] += x[:b - a] * env[:b - a, None] * g
    # extrait de la chanson (gardé tel quel)
    ext = grab(SON_FULL, MUS_OFF, END + 0.3)
    sf.write(SON_EXT, ext, sr, subtype="PCM_24")
    voix = np.zeros((N, 2), np.float32); mus = np.zeros((N, 2), np.float32)
    v_in, v_out = 6.99, 10.36                                   # « Être de gauche, ce n'est pas une étiquette. » (C'est à 10,42 : coupé avant)
    vx = grab(LOT + "/sources/" + SP, v_in, v_out - v_in)
    # niveaux : voix ~ +2 LU au-dessus de la musique baissée
    sf.write(D + "tmp_v.wav", vx, sr); sf.write(D + "tmp_m.wav", ext[int((v_in + PH_OFF) * sr):int((v_out + PH_OFF) * sr)], sr)
    lv = float(lufs(D + "tmp_v.wav")["input_i"]); lm = float(lufs(D + "tmp_m.wav")["input_i"]); os.remove(D + "tmp_v.wav"); os.remove(D + "tmp_m.wav")
    gv = (lm - lv) + 1.0
    print("  voix %.1f LUFS, musique %.1f LUFS -> gain voix %+.1f dB" % (lv, lm, gv))
    place(voix, vx, v_in + PH_OFF, gv, fin=0.04, fout=0.12)
    place(mus, ext, 0.0, 0.0, fin=0.0, fout=0.6)
    # ducking (règle lot 3 : voix de la figure audible, musique baissée dessous puis reprise) : -9 dB sous toute la phrase,
    # remontée en 0,35 s après « étiquette » : la fin du pré-refrain repart pleine vers le drop
    env = np.ones(N, np.float32); r = int(0.10 * sr); r2 = int(0.35 * sr)
    d0 = int((beat(3) + 0.04) * sr) + r; d2 = int((v_out + PH_OFF) * sr); lo = 10 ** (-9 / 20)   # la frappe du temps 3 passe entière
    env[d0:d2] = lo; env[d0 - r:d0] = np.linspace(1, lo, r); env[d2:d2 + r2] = np.linspace(lo, 1, r2)
    mus *= env[:, None]
    sf.write(OUT + "A7-voix.wav", voix, sr, subtype="PCM_24"); sf.write(OUT + "A7-musique.wav", mus, sr, subtype="PCM_24")
    sf.write(D + "tmp_mix.wav", voix + mus, sr, subtype="FLOAT")
    js = lufs(D + "tmp_mix.wav")
    af = ("loudnorm=I=-14:TP=-1.5:LRA=11:measured_I=%s:measured_TP=%s:measured_LRA=%s:measured_thresh=%s:offset=%s:linear=true,alimiter=limit=0.85:level=false:attack=1:release=60,aresample=48000"
          % (js["input_i"], js["input_tp"], js["input_lra"], js["input_thresh"], js["target_offset"]))
    subprocess.run([FF, "-v", "error", "-y", "-i", D + "tmp_mix.wav", "-af", af, "-c:a", "pcm_s24le", OUT + "A7-mix.wav"], check=True)
    os.remove(D + "tmp_mix.wav")
    m = lufs(OUT + "A7-mix.wav"); print("  mix %s LUFS, TP %s dBTP" % (m["input_i"], m["input_tp"]))
# ---------------- aperçu 540x960 ----------------
def apercu():
    plan = json.load(open(D + "plan-A7.json")); ins = []; fl = []
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
    ins += ["-i", OUT + "A7-mix.wav"]
    out = ROOT + "/preview/apercu-A7.mp4"
    subprocess.run([FF, "-v", "error", "-y"] + ins + ["-filter_complex", ";".join(fl), "-map", "[v]", "-map", "%d:a" % k,
                    "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "aac", "-b:a", "192k", "-shortest", out], check=True)
    print("aperçu", out)
if __name__ == "__main__":
    args = set(a for a in sys.argv[1:] if "=" not in a) or {"shots", "cards", "audio", "plan", "apercu"}
    only = [a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("only=")]
    if "shots" in args or only:
        for sid, nb, eff, k, a, b in slots():
            if sid != "aura" and (not only or sid in only): render_slot(sid, eff, a, b)
    if "cards" in args: make_cards()
    if "plan" in args: build_plan()
    if "audio" in args: make_audio()
    if "apercu" in args: apercu()
