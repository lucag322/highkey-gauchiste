# Lot 3 — A6 Aura N&B : Jean-Luc Mélenchon, « Nous sommes le camp des oubliés, des sans-paroles, des humiliés. »
# (meeting de Clermont-Ferrand, 11/10/2026, mot aux 10 000 personnes restées dehors) sur Michael Jackson - They Don't Care About Us.
# Modèles : lot2/_claude/gen/A2 (frappes réelles, coupes recalées) et A5 (N&B adouci, cartons mot à mot).
# Aperçu HORS Resolve (ffmpeg/numpy). Règles : <= 15 s, 9:16 plein écran, aucun visage coupé, aucun logo (filigrane MELENCHON2027.fr
# exclu par le cadrage, pupitre hors cadre), coupes sur les frappes réelles mesurées dans la musique posée, plans >= 1 temps,
# poussée lente avant seulement, Arial Black + mot-clé rouge, jamais de guillemets, ralentis = Resolve (speed_pct).
# Usage : python genA6.py [shots] [cards] [audio] [plan] [apercu] [check] [mesure] [only=ID,ID]   (sans argument = tout)
import sys, os, json, subprocess, math, shutil
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
ROOT = "/Users/luca.grousset/Movies/highkey-gauchiste"; LOT = ROOT + "/lot3"
sys.path.insert(0, ROOT + "/_claude/outils")
import framing
from fx import gblur, motion_blur, vignette, to8, ease_out
from framing import plan_views
D = LOT + "/_claude/gen/A6/"; OUT = D + "out/"; os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, D)
from hits import detect_hits
framing.ROOT = LOT; framing.CACHE = D + "cache"
FF = "/opt/homebrew/bin/ffmpeg"; FACES = ROOT + "/_claude/outils/faces"; FPS = 30; W, H = 1080, 1920
RED = (0xE4, 0x00, 0x2B); WHITE = (255, 255, 255)
F_BLACK = "/System/Library/Fonts/Supplemental/Arial Black.ttf"
F_AURA = ("/System/Library/Fonts/Helvetica.ttc", 2)                 # Helvetica Oblique (« aura. » du test 1)
P = "A6-melenchon-clermont-"
DEH, ENT, M1680, M1870, M5100, M5340, M5410, M5680 = (P + s + ".mp4" for s in ("dehors", "entree", "1680", "1870", "5100", "5340", "5410", "5680"))
SFPS = 60                                                            # toutes les sources : 1080p60 (YouTube sBvVfHxcJp4)
SRC_OFF = {DEH: 1295, ENT: 1470, M1680: 1680, M1870: 1870, M5100: 5100, M5340: 5340, M5410: 5410, M5680: 5680}
# zones utilisables (px source) : filigrane MELENCHON2027.fr en haut à droite (x 1590-1880, y 40-170) ; pupitre (y > 830) hors cadre
B_IN = (0, 0, 1570, 830)            # gros plans au pupitre : sans le filigrane ni l'affiche du pupitre
B_TOP = (0, 180, 1920, 1080)        # plans larges : fenêtre sous le filigrane
# ---------------- musique : They Don't Care About Us (version officielle Brazil, chaîne Michael Jackson) ----------------
MFILE = LOT + "/sons/A6-mj-tdcau-full.wav"; MURL = "https://youtu.be/QNJL6nfu__Q"
# extrait continu : couplet 5 (« Beat me, bash me… you can never get me ») sous la phrase, drop = 1er temps du refrain
# « All I wanna say is that they don't really care about us » (frappe 169,651 s du complet), 2 lignes du refrain, fin après la grosse frappe 177,47 s
S0_BASE = 162.971                    # kick du complet (début de l'extrait) ; décalage sous-image choisi plus bas
END = 15.0
# coupes (temps du complet, frappes repérées par hits.py) : fin du hook, drop, puis 1 temps (2 pour le drop et le ralenti)
CUT_SONG = [164.307, 169.651, 170.988, 171.652, 172.989, 173.659, 174.328, 174.992, 175.661, 176.332, 176.996]
PULSE_SONG = 177.468                 # grosse frappe sur « us » : pulsation du carton final
def fr(t): return int(round(t * FPS))
def music_raw(s0, sr=48000, dur=END + 0.5):
    import soundfile as sf_
    x, r = sf_.read(MFILE, dtype="float32"); assert r == sr
    i0 = int(round(s0 * sr)); return x[i0:i0 + int(dur * sr)]
def choose_s0():
    """Décalage sous-image (±16 ms) qui met les frappes coupées au plus près des images ; frappes mesurées sur la musique posée."""
    js = OUT + "A6-frappes.json"
    if os.path.exists(js):
        d = json.load(open(js))
        if d.get("base") == S0_BASE and d.get("cuts") == CUT_SONG: return d["s0"], d["frappes"]
    hits = detect_hits(music_raw(S0_BASE - 0.02, dur=END + 0.6))          # temps relatifs à S0_BASE - 0,02
    hits = [(round(h[0] + S0_BASE - 0.02, 4), h[1], h[2]) for h in hits]  # -> temps du complet
    real = []
    for c in CUT_SONG + [PULSE_SONG]:
        h = min(hits, key=lambda h: abs(h[0] - c)); assert abs(h[0] - c) < 0.03, ("pas de frappe près de", c, h); real.append(h[0])
    best = None
    for k in range(-16, 17):
        s0 = S0_BASE + k / 1000.0
        err = max(abs((r - s0) - fr(r - s0) / FPS) for r in real[:-1])
        if best is None or err < best[0]: best = (err, s0)
    s0 = round(best[1], 4)
    tl = [(round(h[0] - s0, 4), h[1], h[2]) for h in hits if 0 <= h[0] - s0 <= END]
    json.dump({"base": S0_BASE, "cuts": CUT_SONG, "s0": s0, "err_max_s": round(best[0], 4), "frappes": tl,
               "coupes_complet": real[:-1], "pulse_complet": real[-1]}, open(js, "w"), indent=0)
    return s0, tl
S0, HITS = choose_s0()
_d = json.load(open(OUT + "A6-frappes.json"))
CUTS = [round(r - S0, 4) for r in _d["coupes_complet"]]            # temps timeline des frappes coupées
CUTF = [fr(c) for c in CUTS]
PULSE_T = _d["pulse_complet"] - S0
BEAT = 0.668
assert min(np.diff(CUTS)) >= BEAT - 0.02 and min(np.diff(CUTF)) >= 19, "plan < 1 temps"
DROP = CUTS[1]
# ---------------- phrase (dehors, fichier lot3/sources/A6-melenchon-clermont-dehors.mp4 = YouTube sBvVfHxcJp4 dès 1295 s) ----------------
# mots (Whisper + enveloppe de la voix) : Nous 102,15 / sommes 102,40 / le 103,68 / camp 103,88 / des 104,90 / oubliés 105,08 /
# des 105,97 / sans-paroles 106,17 / des 107,12 / humiliés 107,28-107,92 (puis « et quand on est en force… » 108,18)
F_HUM = 107.09                                       # attaque de « hu » (~107,21) posée 120 ms APRÈS le kick du drop : la frappe reste nette, la voix arrive juste derrière
def f2t(f): return f - F_HUM + DROP                                  # temps fichier « dehors » -> timeline (humiliés pile sur le drop)
# zone sûre TikTok (retour Luca : textes sous l'interface) : bloc <= 66 % de large centré (x 184-896), y 230-1440 ;
# lignes trop longues passées sur 2 lignes (hauteur de lettre >= ~90 px), bloc remonté (bas <= 1400)
TXT_W = 700; X_MIN, X_MAX = int(W * 0.17) + 6, int(W * 0.83) - 6; Y0 = 990
CARDS = [  # carton = lignes (taille max, y_centre, [(mot, t_timeline, couleur)]) ; y None = sous la ligne précédente
    [(130, Y0, [("NOUS", f2t(102.15), WHITE)]), (130, None, [("SOMMES", f2t(102.40), WHITE)]),
     (330, None, [("LE", f2t(103.68), WHITE), ("CAMP", f2t(103.88), WHITE)])],
    [(150, Y0, [("DES", f2t(104.90), WHITE)]), (330, None, [("OUBLIÉS", f2t(105.08), WHITE)])],
    [(150, Y0, [("DES", f2t(105.97), WHITE)]), (132, None, [("SANS-", f2t(106.17), WHITE)]), (132, None, [("PAROLES", f2t(106.17), WHITE)])],
    [(150, Y0, [("DES", f2t(107.12), WHITE)]), (330, None, [("HUMILIÉS", f2t(107.21), RED)])],
]
# ---------------- plans ----------------
SHOTS = {
    "long":   dict(src=DEH, t=None, fixed=(1515, 625), b=B_TOP, vh=900, zoom=(1.0, 1.08), why="de dos face aux 10 000 restés dehors, phrase synchrone"),
    "poings": dict(src=M5680, t=44.0, fixed=(1250, 640), b=B_TOP, vh=880, zoom=(1.0, 1.05), why="vu de la scène : poings levés face à la salle (fin du meeting)"),
    "poing":  dict(src=M1680, t=17.0, face=(1000, 250), b=B_IN, vh=830, zoom=(1.0, 1.05), why="poing levé au pupitre"),
    "salut":  dict(src=DEH, t=31.3, fixed=(1490, 640), b=B_TOP, vh=900, zoom=(1.0, 1.03), speed=60, why="salue la foule restée dehors (ralenti)"),
    "bras":   dict(src=M5410, t=16.4, face=(960, 250), b=B_IN, vh=830, zoom=(1.0, 1.05), why="bras grands ouverts"),
    "pointe": dict(src=M5100, t=13.0, face=(900, 250), b=B_IN, vh=830, zoom=(1.0, 1.05), why="bras tendu vers la salle"),
    "scene":  dict(src=M1680, t=5.0, fixed=(900, 600), b=(0, 180, 1570, 1080), vh=900, zoom=(1.0, 1.05), why="la salle pleine devant la scène tricolore"),
    "ouvre":  dict(src=M5340, t=13.6, face=(960, 250), b=B_IN, vh=830, zoom=(1.0, 1.05), why="bras ouverts au pupitre"),
    "tend":   dict(src=M1870, t=13.0, face=(1000, 250), b=B_IN, vh=830, zoom=(1.0, 1.05), why="bras tendu, voix forte"),
    "poing2": dict(src=M1680, t=14.6, face=(1000, 250), b=B_IN, vh=830, zoom=(1.0, 1.05), why="le poing monte"),
}
SHOTS["long"]["t"] = F_HUM - (DROP - CUTS[0])                       # synchrone : humiliés sur le drop
# montage après le drop : le plan i va de CUTS[i+1] à CUTS[i+2] ; carton final de CUTS[-1] à END
EDIT = [("poings", "drop"), ("poing", "whip"), ("salut", "whip"), ("bras", "whip"), ("pointe", "whip"),
        ("scene", "whip"), ("ouvre", "whip"), ("tend", "whip"), ("poing2", "whip")]
assert len(EDIT) == len(CUTS) - 2
# ---------------- look N&B (A5 : N&B adouci, retour Luca) ----------------
RNG = np.random.default_rng(11)
def grade(bgr, white=0.86):
    g = (0.114 * bgr[..., 0] + 0.587 * bgr[..., 1] + 0.299 * bgr[..., 2])
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
def read_frames(src, t, n_out):
    need = [int(round(i * SFPS / FPS)) for i in range(n_out)]; n_src = need[-1] + 1
    p = subprocess.run([FF, "-v", "error", "-ss", "%.4f" % t, "-i", LOT + "/sources/" + src, "-frames:v", str(n_src),
                        "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True)
    a = np.frombuffer(p.stdout, np.uint8).reshape(-1, 1080, 1920, 3)
    return [a[min(i, len(a) - 1)].astype(np.float32) / 255 for i in need], int(round(t * SFPS))
def crop_916(img, cx, cy, vh):
    vw = vh * 9 / 16; s = W / vw
    M = np.float32([[s, 0, W / 2 - cx * s], [0, s, H / 2 - cy * s]])
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
# ---------------- texte (A5 : Arial Black, contour noir + ombre douce, mot-clé rouge, mot à mot) ----------------
def font(size): return ImageFont.truetype(F_BLACK, max(8, int(size)))
def fit_size(txt, maxw, start=260):
    s = start
    while font(s).getlength(txt) + 2 * max(4, int(s * 0.045)) > maxw: s -= 2     # contour compris
    return s
def layout(card, vis=None):
    """Tailles et lignes fixées sur le carton ENTIER (pas de saut de taille), x recentré sur les mots déjà dits."""
    out = []; y_prev = None; s_prev = None; vis = vis or card
    for (size, yc, words), (_, _, vwords) in zip(card, vis):
        txt = " ".join(w for w, _, _ in words)
        size = fit_size(txt, TXT_W, start=size)
        if yc is None: yc = y_prev + s_prev * 0.5 + 40 + size * 0.5
        f = font(size); vt = " ".join(w for w, _, _ in vwords); x = (W - f.getlength(vt)) / 2
        for w, t, col in vwords:
            out.append(dict(w=w, t=t, col=col, size=size, x=x, yc=yc)); x += f.getlength(w + " ")
        y_prev, s_prev = yc, size
    return out
def draw_words(items, scale_last=1.0, alpha_last=1.0, alpha_all=1.0):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay); ds = ImageDraw.Draw(sh)
    for k, it in enumerate(items):
        last = it["t"] >= items[-1]["t"] - 1e-6; sc = scale_last if last else 1.0     # SANS- / PAROLES : même mot sur 2 lignes
        sw = max(4, int(it["size"] * 0.045)); wfull = font(it["size"]).getlength(it["w"])
        sc = min(sc, max(1.0, (X_MAX - X_MIN - 2 * sw) / wfull))                        # mot géant : agrandissement d'entrée plafonné
        f = font(it["size"] * sc); wnow = f.getlength(it["w"])
        x = min(max(it["x"] + (wfull - wnow) / 2, X_MIN + sw), X_MAX - sw - wnow)       # entrée agrandie gardée dans la zone sûre
        x0, y0, x1, y1 = d.textbbox((0, 0), it["w"], font=f); y = it["yc"] - (y1 - y0) / 2 - y0
        a = int(255 * (alpha_last if last else 1.0) * alpha_all)
        ds.text((x, y + it["size"] * 0.05), it["w"], font=f, fill=(0, 0, 0, int(a * 0.78)), stroke_width=sw * 3, stroke_fill=(0, 0, 0, int(a * 0.78)))
        d.text((x, y), it["w"], font=f, fill=it["col"] + (a,), stroke_width=sw, stroke_fill=(0, 0, 0, a))
    sh = sh.filter(ImageFilter.GaussianBlur(18))
    return np.asarray(Image.alpha_composite(sh, lay)).astype(np.float32) / 255
def text_at(t):
    """Carton visible au temps timeline t (mot à mot, ligne recentrée, entrée 3 images sans rebond)."""
    ci = None
    for i, c in enumerate(CARDS):
        if t >= c[0][2][0][1]: ci = i
    if ci is None: return None
    vis = [(sz, y, [w for w in ws if t >= w[1]]) for sz, y, ws in CARDS[ci]]
    on = layout(CARDS[ci], vis)
    k = (t - on[-1]["t"]) * FPS; e = ease_out(min(k / 3.0, 1.0))
    return draw_words(on, scale_last=1.12 - 0.12 * e, alpha_last=min(1.0, 0.35 + e))
def over_rgba(img_bgr, rgba):
    a = rgba[..., 3:4]; rgb = rgba[..., 2::-1]
    return img_bgr * (1 - a) + rgb * a
# ---------------- rendu des plans ----------------
def write_mov(frames, path, fps=FPS):
    p = subprocess.Popen([FF, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", "%dx%d" % (W, H), "-r", str(fps), "-i", "-",
                          "-c:v", "prores_ks", "-profile:v", "3", "-pix_fmt", "yuv422p10le", "-vendor", "apl0", path], stdin=subprocess.PIPE)
    for f in frames: p.stdin.write(to8(f).tobytes())
    p.stdin.close(); p.wait()
def slots():
    out = [("long", "cut", CUTF[0], CUTF[1])]
    for i, (sid, eff) in enumerate(EDIT): out.append((sid, eff, CUTF[i + 1], CUTF[i + 2]))
    return out
def render_slot(sid, eff, a, b):
    sh = SHOTS[sid]; n = b - a
    raw, s0 = read_frames(sh["src"], sh["t"], n)
    m = math.ceil(n * sh.get("speed", 100) / 100)                    # zoom terminé sur la frappe de sortie (ralenti : images vues)
    z0, z1 = sh["zoom"]; zoom = lambda f: z0 + (z1 - z0) * min(f / max(m - 1, 1), 1.0)
    if "fixed" in sh:
        views, _ = plan_views(sh["src"], s0, n, SFPS, speed=SFPS / FPS, bounds=sh["b"], vh=sh["vh"], zoom=zoom, fixed=sh["fixed"])
    else:
        views, ok = plan_views(sh["src"], s0, n, SFPS, speed=SFPS / FPS, hint=sh["face"], bounds=sh["b"], vh=sh["vh"], zoom=zoom, top=0.10)
        if not ok: print("  ! pas de visage :", sid)
    frames = []
    for i, (img, (cx, cy, vh)) in enumerate(zip(raw, views)):
        g = grade(crop_916(img, cx, cy, vh))
        if eff == "whip" and i < 3: g = motion_blur(g, 0, [220, 90, 25][i], steps=16)
        if eff == "drop" and i < 8:
            k = (1 - i / 8) ** 2; g = np.clip(g + k * 0.55 + gblur(g, 25) * k * 0.6, 0, 1)
        if sid in ("long", "poings"):                                   # phrase : mot à mot ; HUMILIÉS rouge sur le drop
            tl = text_at((a + i) / FPS)
            if tl is not None: g = over_rgba(g, tl)
        frames.append(g)
    name = "A6_%s.mov" % sid; write_mov(frames, OUT + name)
    vx, vz = views[0], views[-1]
    print("  %-7s %3d im  vue %d,%d h%d -> h%d  (x %d-%d, y %d-%d)" % (sid, n, vx[0], vx[1], vx[2], vz[2], vx[0] - vx[2] * 9 / 32, vx[0] + vx[2] * 9 / 32, vx[1] - vx[2] / 2, vx[1] + vx[2] / 2))
    return name
# ---------------- cartes « aura. » ----------------
def aura_base():
    im = Image.new("L", (W, H), 0); d = ImageDraw.Draw(im); f = ImageFont.truetype(F_AURA[0], 120, index=F_AURA[1])
    tw = d.textlength("aura.", font=f); d.text(((W - tw) / 2, H / 2 - 80), "aura.", font=f, fill=255)
    a = np.asarray(im).astype(np.float32) / 255
    return a, gblur(a, 22) * 0.9 + gblur(a, 6) * 0.5
def aura_card(n, fade_in=3, fade_out=0, pulse=None):
    a, glow = aura_base(); out = []
    for i in range(n):
        k = 1.0; p = 0.0
        if fade_in and i < fade_in: k = ease_out((i + 1) / fade_in)
        if fade_out and i >= n - fade_out: k = (n - i) / fade_out
        if pulse is not None and i >= pulse: p = max(0.0, 1 - (i - pulse) / 7.0) ** 2   # grosse frappe : halo qui gonfle puis retombe
        base = np.clip(a * 0.92 + glow * (1 + 1.6 * p) + gblur(a, 60) * 0.8 * p, 0, 0.97)
        out.append(np.repeat((0.008 + base * k)[..., None], 3, 2))
    return out
def make_cards():
    write_mov(aura_card(CUTF[0]), OUT + "A6_aura_intro.mov")
    write_mov(aura_card(fr(END) - CUTF[-1], fade_in=3, fade_out=10, pulse=fr(PULSE_T) - CUTF[-1]), OUT + "A6_aura_fin.mov")
# ---------------- plan ----------------
def build_plan():
    video = []
    def add(id_, clip, s, e, rec, kind, extra=None):
        v = {"id": id_, "clip": clip, "folder": "genA6", "s": s, "e": e, "rec": rec, "track": 1, "kind": kind, "clip_fps": FPS, "dur": e - s, "speed_pct": 100}
        if extra: v.update(extra)
        video.append(v)
    add("hook", "A6_aura_intro.mov", 0, CUTF[0], 0, "card")
    for sid, eff, a, b in slots():
        sh = SHOTS[sid]; n = b - a
        extra = {"source": "lot3/sources/%s @ %.3f s (YouTube sBvVfHxcJp4 @ %.2f s)" % (sh["src"], sh["t"], SRC_OFF[sh["src"]] + sh["t"]),
                 "effet": eff, "temps": round((b - a) / FPS / BEAT, 1), "pourquoi": sh["why"], "speed_pct": sh.get("speed", 100)}
        if sh.get("speed"): extra["retime"] = "optical_flow"
        if sid == "long": extra["texte"] = "NOUS SOMMES / LE CAMP · DES / OUBLIÉS · DES / SANS-PAROLES · DES (mot à mot, Arial Black blanc)"
        if sid == "poings": extra["texte"] = "DES / HUMILIÉS (rouge #E4002B, sur le drop)"
        add("%s_%d" % (sid, a), "A6_%s.mov" % sid, 0, n, a, "shot", extra)
    add("fin", "A6_aura_fin.mov", 0, fr(END) - CUTF[-1], CUTF[-1], "card", {"pulsation": "grosse frappe %.3f s" % PULSE_T})
    plan = {"name": "A6 - Aura N&B - Jean-Luc Mélenchon", "fps": FPS, "w": W, "h": H, "duree_s": END,
            "note": "Plans 9:16 recadrés + étalonnés N&B (lot3/_claude/gen/A6/out), vitesse normale. s/e en images du clip (30 i/s), rec en images timeline. "
                    "speed_pct < 100 : ralenti Resolve Optical Flow + Speed Warp (aperçu = setpts simple). Coupes sur les frappes réelles de la musique posée "
                    "(out/A6-frappes.json), drop = 1er temps du refrain « All I wanna say… » ; aucun plan < 1 temps (0,668 s, 89,8 BPM) ; zooms finis sur la frappe de sortie.",
            "phrase": {"texte": "Nous sommes le camp des oubliés, des sans-paroles, des humiliés.",
                       "source": "https://www.youtube.com/watch?v=sBvVfHxcJp4 (chaîne JEAN-LUC MÉLENCHON, meeting de Clermont-Ferrand 11/10/2026), 1397,15-1402,92 s",
                       "fichier": "lot3/sources/" + DEH + " 102,15-107,92 s", "timeline_s": [round(f2t(102.15), 3), round(f2t(107.92), 3)]},
            "video": video,
            "audio": [{"id": "mix", "clip": "A6-mix.wav", "folder": "genA6", "rec": 0, "track": 1, "note": "mix -14 LUFS, TP <= -1 dBTP"}],
            "stems": ["lot3/_claude/gen/A6/out/A6-voix.wav", "lot3/_claude/gen/A6/out/A6-musique.wav"],
            "musique": {"fichier": "lot3/sons/A6-mj-tdcau-full.wav", "titre": "Michael Jackson - They Don't Care About Us", "url": MURL,
                        "debut_complet_s": S0, "fin_complet_s": round(S0 + END, 3), "coupes_timeline_s": CUTS, "frappes_timeline_s": [h[0] for h in HITS]},
            "logos_exclus": "filigrane MELENCHON2027.fr (haut droite) hors fenêtre, affiche du pupitre hors cadre (y < 830)"}
    json.dump(plan, open(D + "plan-A6.json", "w"), indent=1, ensure_ascii=False)
    return plan
# ---------------- audio ----------------
V_IN, V_OUT = 101.95, 107.98                                          # phrase entière, coupée avant « et quand on est en force »
def make_audio():
    import soundfile as sf
    sr = 48000; N = int(round(END * sr))
    def place(buf, x, t, gain_db=0, fin=0.0, fout=0.0):
        g = 10 ** (gain_db / 20); n = len(x); env = np.ones(n, np.float32)
        if fin: m = int(fin * sr); env[:m] = np.linspace(0, 1, m)
        if fout: m = int(fout * sr); env[-m:] *= np.linspace(1, 0, m)
        a = int(round(t * sr)); b = min(N, a + n); buf[a:b] += x[:b - a] * env[:b - a, None] * g
    p = subprocess.run([FF, "-v", "error", "-ss", "%.3f" % V_IN, "-t", "%.3f" % (V_OUT - V_IN), "-i", LOT + "/sources/" + DEH,
                        "-ac", "2", "-ar", str(sr), "-f", "f32le", "-"], capture_output=True)
    v = np.frombuffer(p.stdout, np.float32).reshape(-1, 2).copy()
    voix = np.zeros((N, 2), np.float32); mus = np.zeros((N, 2), np.float32)
    tv0, tv1 = f2t(V_IN), f2t(V_OUT)
    place(voix, v, tv0, +4, fin=0.04, fout=0.10)
    m = music_raw(S0, sr, END + 0.1)[:N]
    t = np.arange(len(m)) / sr; g = np.ones(len(m), np.float32)
    lo, mid = 10 ** (-9 / 20), 10 ** (-4 / 20)                         # -9 dB sous la phrase, -4 dB sur « humiliés » après le drop
    def ramp(t0, t1, g0, g1):
        s = (t >= t0) & (t < t1); g[s] = g0 + (g1 - g0) * (t[s] - t0) / (t1 - t0)
    g[(t >= tv0) & (t < DROP - 0.01)] = lo; ramp(tv0 - 0.25, tv0, 1.0, lo)
    g[(t >= DROP - 0.01) & (t < tv1)] = mid; ramp(DROP - 0.01, DROP + 0.01, lo, mid); ramp(tv1, tv1 + 0.15, mid, 1.0)
    s = t > END - 0.45; g[s] *= np.clip((END - t[s]) / 0.45, 0, 1)
    fi = int(0.01 * sr); g[:fi] *= np.linspace(0, 1, fi)
    mus[:len(m)] = m * g[:, None]
    sf.write(OUT + "A6-voix.wav", voix, sr, subtype="PCM_24"); sf.write(OUT + "A6-musique.wav", mus, sr, subtype="PCM_24")
    sf.write(D + "tmp_mix.wav", voix + mus, sr, subtype="FLOAT")
    r_ = subprocess.run([FF, "-hide_banner", "-i", D + "tmp_mix.wav", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                        capture_output=True, text=True).stderr
    js = json.loads(r_[r_.rindex("{"):r_.rindex("}") + 1])
    af = ("loudnorm=I=-12.4:TP=-2:LRA=11:measured_I=%s:measured_TP=%s:measured_LRA=%s:measured_thresh=%s:offset=%s:linear=true,"
          "alimiter=limit=0.83:level=false:attack=1:release=60,aresample=48000"
          % (js["input_i"], js["input_tp"], js["input_lra"], js["input_thresh"], js["target_offset"]))
    subprocess.run([FF, "-v", "error", "-y", "-i", D + "tmp_mix.wav", "-af", af, "-c:a", "pcm_s24le", OUT + "A6-mix.wav"], check=True)
    os.remove(D + "tmp_mix.wav"); print("audio : avant normalisation", js["input_i"], "LUFS")
# ---------------- aperçu 540x960 ----------------
APERCU = ROOT + "/preview/apercu-A6.mp4"
def apercu():
    plan = json.load(open(D + "plan-A6.json")); ins = []; fl = []
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
    ins += ["-i", OUT + "A6-mix.wav"]
    subprocess.run([FF, "-v", "error", "-y"] + ins + ["-filter_complex", ";".join(fl), "-map", "[v]", "-map", "%d:a" % k,
                    "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "aac", "-b:a", "192k", "-shortest", APERCU], check=True)
    print("aperçu", APERCU)
# ---------------- contrôle visages : tout visage > 5 % de la hauteur doit être entier, dans chaque plan ----------------
def check_faces():
    plan = json.load(open(D + "plan-A6.json")); bad = []
    for v in plan["video"]:
        if v["kind"] != "shot": continue
        n = v["e"] - v["s"]
        if v.get("speed_pct", 100) < 100: n = math.ceil(n * v["speed_pct"] / 100) + 1
        d = D + "cache/chk_" + v["clip"]; shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
        subprocess.run([FF, "-v", "error", "-i", OUT + v["clip"], "-vf", "select='lt(n\\,%d)',scale=540:960" % n, "-fps_mode", "passthrough",
                        "-q:v", "3", d + "/f%04d.jpg"], check=True)
        subprocess.run([FACES, d], check=True, capture_output=True)
        js = json.load(open(d + "/faces.json")); nb = 0
        for k, fl in js.items():
            for x, y, w, h in fl:
                if h < 0.05: continue
                top, bot, l, r = y - 0.3 * h, y + h * 1.05, x - 0.08 * w, x + w * 1.08
                if top < 0 or bot > 1 or l < 0 or r > 1: nb += 1; bad.append("%s %s (%.2f %.2f %.2f %.2f h%.2f)" % (v["clip"], k, top, bot, l, r, h))
        print("  visages", v["clip"], "images", len(js), "coupés", nb)
        shutil.rmtree(d, ignore_errors=True)
    print("TOTAL visages coupés :", len(bad)); print("\n".join(bad[:30]))
# ---------------- mesure sur l'export : coupes (changement d'image) vs frappes (audio de l'export) ----------------
def mesure():
    import soundfile as sf
    p = subprocess.run([FF, "-v", "error", "-i", APERCU, "-vf", "scale=54:96", "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True)
    fr_ = np.frombuffer(p.stdout, np.uint8).reshape(-1, 96, 54).astype(np.float32)
    diff = np.abs(np.diff(fr_, axis=0)).mean((1, 2))
    cuts_exp = [ (i + 1) / FPS for i in range(len(diff)) if diff[i] > 18 and diff[i] > 2.5 * np.median(diff[max(0, i - 5):i + 6]) ]
    p = subprocess.run([FF, "-v", "error", "-i", APERCU, "-ac", "2", "-ar", "48000", "-f", "f32le", "-"], capture_output=True)
    y = np.frombuffer(p.stdout, np.float32).reshape(-1, 2)
    hits = detect_hits(y, 48000)
    print("images", len(fr_), "durée %.3f s" % (len(fr_) / FPS), "| coupes détectées :", len(cuts_exp))
    errs = []
    for c in CUTS:
        ce = min(cuts_exp, key=lambda x: abs(x - c)) if cuts_exp else None
        h = min(hits, key=lambda h: abs(h[0] - c))
        e = (ce - h[0]) * 1000 if ce is not None else float("nan"); errs.append(abs(e))
        print("  coupe prévue %.3f | image de coupe export %.3f | frappe export %.4f %s | écart %+.1f ms" % (c, ce, h[0], h[1], e))
    print("ÉCART MAX coupes/frappes : %.1f ms" % max(errs))
    r = subprocess.run([FF, "-hide_banner", "-i", APERCU, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    print("\n".join(l for l in r.splitlines()[-12:] if "I:" in l or "Peak:" in l or "LRA:" in l))
if __name__ == "__main__":
    args = set(a for a in sys.argv[1:] if not a.startswith("only=")) or {"shots", "cards", "audio", "plan", "apercu", "check", "mesure"}
    only = [x for a in sys.argv[1:] if a.startswith("only=") for x in a.split("=", 1)[1].split(",")]
    print("S0 = %.4f s du complet, coupes timeline :" % S0, CUTS)
    if "shots" in args or only:
        for sid, eff, a, b in slots():
            if not only or sid in only: render_slot(sid, eff, a, b)
    if "cards" in args: make_cards()
    if "plan" in args: build_plan()
    if "audio" in args: make_audio()
    if "apercu" in args: apercu()
    if "check" in args: check_faces()
    if "mesure" in args: mesure()
