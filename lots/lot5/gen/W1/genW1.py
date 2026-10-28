# W1 (lot 5) — Aura « mots power » (NOUVEAU style, inspi .magafx), Jean-Luc Mélenchon, son « Love Sosa » (Chief Keef, audio officiel UMG).
# Recette (inspis/2026-10-26 magafx), cartes « murmure » retirées (Luca 27/10 : illisibles, on ouvre directement sur Mélenchon synchro),
# plan long parlé, drop -> montage flash N&B contrasté + grain, 1 mot power (<= 4 lettres, capitales, fonte grasse abîmée, blanc, centré)
# tenu 1-2 s sur les plans forts, flou de mouvement sur les coupes, fin en fondu noir total. Pas de flash < 1 temps (Luca), 9:16.
# Phrase : « Qu'ils s'en aillent tous, nous allons les remplacer partout » (Fête de l'Humanité 12/09/2026, chaîne JEAN-LUC MÉLENCHON,
#          youtube 80bBtk2lTiI @ 4812,12-4815,10 s = lot1/sources/3-melenchon-huma-citation.mp4 102,12-105,10 s). Autre phrase que lot1/M1.
# Plans : Huma (autres moments que lot1/M1), Valence (autres moments que lot1/M1), Saint-Denis (autres moments que lot1/M1/C4).
# Sources = liens lot5/sources/W1-* vers lot1/sources (rien de copié ni modifié).
# Usage : python genW1.py [shots] [cards] [audio] [plan] [apercu] [only=ID,ID]   (sans argument = tout)
import sys, os, json, subprocess, math, functools
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
ROOT = "/Users/luca.grousset/Movies/highkey-gauchiste"; LOT = ROOT + "/lot5"
sys.path.insert(0, ROOT + "/_claude/outils")
import framing
from framing import plan_views
from fx import gblur, motion_blur, vignette, to8, ease_out
D = LOT + "/_claude/gen/W1/"; OUT = D + "out/"; os.makedirs(OUT, exist_ok=True)
framing.ROOT = LOT; framing.CACHE = D + "cache"
framing.head_box = lambda f: (f[0] - 0.12 * f[2], f[1] - 0.5 * f[3], f[0] + 1.12 * f[2], f[1] + 1.2 * f[3])
framing.view_for = functools.partial(framing.view_for, margin=0.04)
FF = "/opt/homebrew/bin/ffmpeg"; FPS = 30; W, H = 1080, 1920
RED = (0xE4, 0x00, 0x2B); WHITE = (255, 255, 255)
F_BLACK = "/System/Library/Fonts/Supplemental/Arial Black.ttf"
F_MURMURE = ("/System/Library/Fonts/Supplemental/Didot.ttc", 1)          # Didot Italic (serif fine)
HU, VA, SD = "W1-melenchon-huma.mp4", "W1-melenchon-valence.mp4", "W1-melenchon-saintdenis.mp4"
REAL = {HU: "lot1/sources/3-melenchon-huma-citation.mp4", VA: "lot1/sources/1-melenchon-valence-amfis.mp4", SD: "lot1/sources/5-melenchon-saintdenis-smic.mp4"}
SFPS = {HU: 50, VA: 30, SD: 30}
URLS = {HU: ("https://www.youtube.com/watch?v=80bBtk2lTiI", 4710.0, "JEAN-LUC MÉLENCHON (Fête de l'Humanité)", "2026-09-12"),
        VA: ("https://www.youtube.com/watch?v=IYegq2-6-go", 1620.0, "JEAN-LUC MÉLENCHON (meeting de Valence, AMFiS)", "2026-08"),
        SD: ("https://www.youtube.com/watch?v=1dkY_JVFx9I", 3000.0, "JEAN-LUC MÉLENCHON (meeting de Saint-Denis)", "2026-06-07")}
# zones utilisables (px source 1920x1080) : pupitres écrits (FÊTE DE L'HUMA / VALENCE / SAINT-DENIS, y > ~810) et filigrane MELENCHON2027.fr (haut droite, x > 1590) hors fenêtre
B_CLOSE = (0, 0, 1590, 790); B_FULL = (0, 0, 1590, 1080)
# ---------------- musique ----------------
SON_FILE = LOT + "/sons/W1-chiefkeef-lovesosa_complet.wav"
SON_URL = "https://www.youtube.com/watch?v=OrYjTUbyLZ4"
BEAT = 60 / 132.35                               # 0,4533 s (claps tous les 2 temps mesurés 72,64 -> 81,71)
MDROP = 71.28                                    # entrée de la batterie + 808 sur « (These bitches) love Sosa », 1er refrain (complet)
def fr(t): return int(round(t * FPS))
PRE = 9                                          # temps avant le drop : plan long synchro dès l'image 0 (~7 temps), foule (2 temps)
DROP = PRE * BEAT                                # 4,08 s
NPOST = 20
END_T = DROP + NPOST * BEAT                      # 13,15 s (aura <= 15 s)
MUSIC_IN0 = MDROP - DROP
# ---------------- phrase ----------------
V_OUT = 105.85                     # voix : « Qu'ils » 102,12 … « partout » ~105,10, puis clameur de la salle jusqu'au drop
# montage : (id, effet d'entrée, nb de temps, mot power) ; coupes = frappes réelles (claps 2/4 et kicks) sur la grille du drop
EDIT = [("dos", "drop", 3, None), ("rue", "whip", 2, None), ("index", "whip", 2, None), ("drone", "whip", 2, None), ("crie", "whip", 2, None),
        ("mains", "whip", 3, None), ("foule2", "whip", 1, None), ("main", "whip", 1, None), ("doigt", "whip", 1, None), ("poing", "whip", 3, None)]
# mots en grand (retours Luca 27/10) : morceaux de la phrase, dans son ordre, un seul à l'écran, chacun posé sur la frappe de coupe de son plan
# (temps k depuis le drop) ; lus seuls ils redisent le message : QU'ILS S'EN AILLENT · TOUS. · ON LES REMPLACE · PARTOUT.
WORDS = [("QU’ILS S’EN\nAILLENT", 0, 3), ("TOUS.", 5, 7), ("ON LES\nREMPLACE", 11, 14), ("PARTOUT.", 17, 20)]   # textes dictés par Luca (27/10), un par plan
assert sum(e[2] for e in EDIT) == NPOST
PRE_K = [-9, -2]                                 # plan long, foule (temps relatifs au drop)
CUT_K = [0]
for _, _, nb, _ in EDIT: CUT_K.append(CUT_K[-1] + nb)
HITS_JSON = OUT + "W1-frappes.json"
def music_raw(mi, sr=48000, dur=None):
    import soundfile as sf_
    x, r = sf_.read(SON_FILE, dtype="float32"); assert r == sr
    i0 = int(round(mi * sr)); return x[i0:i0 + int(((dur or END_T) + 0.5) * sr)]
def attacks(y, grid, sr=48000):
    """Attaque réelle de la frappe la plus nette près de chaque temps attendu (±45 ms) : kick/808 (< 150 Hz) ou clap/caisse (> 1,5 kHz).
    Plus forte montée de l'enveloppe (5 ms) puis instant où elle franchit la moitié entre le creux d'avant et le sommet."""
    import scipy.signal as ss
    m = y.mean(1); out = []; q = int(0.005 * sr)
    envs = {b: np.convolve(np.abs(ss.hilbert(ss.sosfiltfilt(ss.butter(4, fc, t, fs=sr, output="sos"), m))), np.ones(48) / 48, "same")
            for b, (t, fc) in {"kick": ("lp", 150), "clap": ("hp", 1500)}.items()}
    for g in grid:
        cand = []
        for b, env in envs.items():
            a = max(q + int(0.03 * sr), int((g - 0.045) * sr)); e = min(len(env) - int(0.04 * sr), int((g + 0.045) * sr))
            seg = env[a:e]; dd = seg[q:] - seg[:-q]; i = a + int(np.argmax(dd)) + q // 2
            pk = i + int(np.argmax(env[i:i + int(0.03 * sr)])); lo_ = i - int(0.03 * sr) + int(np.argmin(env[i - int(0.03 * sr):i + 1]))
            thr = env[lo_] + 0.5 * (env[pk] - env[lo_]); j = pk
            while j > lo_ and env[j - 1] > thr: j -= 1
            db = float(20 * np.log10(env[pk] / max(env[lo_], 1e-6)))
            cand.append((round(j / sr, 4), b, round(db, 1)))
        fortes = [c for c in cand if c[2] >= 15]                   # frappe perçue = la plus tôt des attaques nettes (kick avant clap/charleston)
        out.append(min(fortes) if fortes else max(cand, key=lambda c: c[2]))
    return out
def frappes():
    cle = [MUSIC_IN0, END_T, CUT_K, PRE_K, "v4"]
    if os.path.exists(HITS_JSON):
        js = json.load(open(HITS_JSON))
        if js.get("cle") == cle: return js["music_in"], js["coupes"], js["pre"]
    y0 = music_raw(MUSIC_IN0)
    ks = [a[0] for a in attacks(y0, [DROP + k * BEAT for k in CUT_K[:-1]])]
    best = min(np.arange(-0.016, 0.0165, 0.001), key=lambda off: max(abs((t - off) - round((t - off) * FPS) / FPS) for t in ks))
    mi = MUSIC_IN0 + best; y = music_raw(mi)
    cc = attacks(y, [t - best for t in ks]); pre = attacks(y, [DROP + k * BEAT - 0 for k in PRE_K[1:]])
    json.dump({"cle": cle, "music_in": mi, "coupes": cc, "pre": pre}, open(HITS_JSON, "w")); return mi, cc, pre
MUSIC_IN, CC, PREH = frappes()
CUTS = [c[0] for c in CC]
# k = 7 : double attaque (flam) 9,036 / 9,073 s ; sur le mix limité l'attaque perçue est la 1re (mesure.py) -> coupe sur 9,036 s
CC[3] = [round(CC[3][0] - 0.0368, 4), CC[3][1], CC[3][2]]; CUTS[3] = CC[3][0]
CUTF = [fr(c) for c in CUTS] + [fr(END_T)]
DROPF = CUTF[0]
# avant le drop (intro sans batterie) : coupes sur les seules attaques nettes de l'intro, mesurées (probe_son.py) : 66,296 s (synthé, carte 2),
# re-mesurées sur la piste musique posée (mesure.py)
PRE_T = [70.3789 - MUSIC_IN]                     # clap mesuré dans le complet 2 temps avant le drop (coupe plan long -> foule)
PREF = [0] + [fr(t) for t in PRE_T] + [DROPF]
SRC_OFF = 105.15 - PREF[1] / FPS                 # timeline = source Huma - SRC_OFF (plan long fini avant le changement de caméra de la régie à 105,22 s)
V_IN = SRC_OFF                                   # voix dès l'image 0 (« Qu'ils » 102,12 s ; « … grand ménage. » fini avant)
assert min(CUTF[i + 1] - CUTF[i] for i in range(len(EDIT))) >= 13
# ---------------- plans ----------------
SHOTS = {
    "long":  dict(src=HU, t=PREF[0] / FPS + SRC_OFF, face=(870, 225), b=B_CLOSE, vh=790, zoom=(1.0, 1.04), top=0.12, track=True, dx=0.10,
                  why="Fête de l'Humanité : « Qu'ils s'en aillent tous, nous allons les remplacer partout » (son synchrone), bras tendu"),
    "foule": dict(src=VA, t=166.0, fixed=(800, 640), b=B_FULL, vh=860, zoom=(1.0, 1.04), why="Valence : la foule et les drapeaux, clameur sous « partout »"),
    "dos":   dict(src=VA, t=272.9, fixed=(905, 600), b=B_FULL, vh=1080, zoom=(1.0, 1.05), why="Valence : de dos au pupitre face à la foule"),
    "rue":   dict(src=SD, t=233.3, fixed=(900, 700), b=B_FULL, vh=760, zoom=(1.0, 1.05), why="Saint-Denis : la place noire de monde vue d'en haut"),
    "poing": dict(src=HU, t=132.15, face=(1170, 270), b=B_CLOSE, vh=790, zoom=(1.0, 1.04), top=0.12, dx=0.06, why="Huma : poing levé près du visage, crie (fondu noir)"),
    "drone": dict(src=VA, t=245.5, fixed=(1150, 560), b=B_FULL, vh=1080, zoom=(1.0, 1.05), why="Valence : vue aérienne de la foule au bord du lac"),
    "crie":  dict(src=SD, t=54.0, face=(1140, 330), b=B_CLOSE, vh=790, zoom=(1.0, 1.05), top=0.12, track=True, why="Saint-Denis : crie, poing serré"),
    "mains": dict(src=SD, t=227.6, face=(1110, 330), b=B_CLOSE, vh=790, zoom=(1.0, 1.04), top=0.12, track=True, why="Saint-Denis : crie, mains levées près du visage"),
    "foule2": dict(src=VA, t=229.0, fixed=(1000, 690), b=B_FULL, vh=780, zoom=(1.0, 1.05), why="Valence : foule et drapeaux"),
    "main":  dict(src=HU, t=136.65, face=(1080, 210), b=B_CLOSE, vh=790, zoom=(1.0, 1.05), top=0.12, track=True, dx=-0.12, why="Huma : bras tendu vers la salle"),
    "doigt": dict(src=VA, t=186.3, face=(930, 210), b=B_CLOSE, vh=790, zoom=(1.0, 1.05), top=0.12, track=True, dx=-0.10, why="Valence : index levé, crie"),
    "index": dict(src=VA, t=178.05, face=(930, 210), b=B_CLOSE, vh=790, zoom=(1.0, 1.04), top=0.12, dx=0.0, why="Valence : crie, de profil (index levé hors cadre : pupitre écrit en dessous)"),
}
# ---------------- look N&B contrasté + grain (recette magafx, base genA9) ----------------
RNG = np.random.default_rng(5)
def grade(bgr, white=0.93):
    g = (0.114 * bgr[..., 0] + 0.587 * bgr[..., 1] + 0.299 * bgr[..., 2])
    g = np.clip((g - 0.03) / 0.94, 0, 1)
    g = g ** 0.9
    g = 0.55 * g + 0.45 * (g * g * (3 - 2 * g))                  # S plus marqué : contraste élevé
    small = cv2.resize(g, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    hi = np.clip(small - 0.72, 0, None) * 1.5
    glow = cv2.resize(cv2.GaussianBlur(hi, (0, 0), 9), (W, H)) * 0.22
    g = g + glow
    g = vignette(g[..., None], 0.32, 2.4)[..., 0]
    g = 0.02 + np.clip(g, 0, 1) * (white - 0.02)
    gr = cv2.resize(RNG.normal(0, 1, (H // 2, W // 2)).astype(np.float32), (W, H))   # grain filmique (2 px)
    g = g + gr * 0.028
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
def face_heights(src, s0, n, hint, b):
    sf = SFPS[src]; n_src = int(n * sf / FPS) + 2
    heads = framing.pick(framing.detect(src, s0, n_src, sf), hint, b)
    if not heads: return None
    hs = np.array([f[3] for f in heads], np.float32)
    k = 15; pad = np.pad(hs, (k // 2, k // 2), mode="edge"); hs = np.convolve(pad, np.ones(k) / k, "valid")
    return [float(hs[min(int(f * sf / FPS), len(hs) - 1)]) for f in range(n)]
# ---------------- texte : phrase mot à mot (Arial Black, contour + ombre, mot-clé rouge, jamais de guillemets) ----------------
def font(size): return ImageFont.truetype(F_BLACK, max(8, int(size)))
def fit_size(txt, maxw, start=150):
    s = start
    while font(s).getlength(txt) > maxw: s -= 4
    return s
# mots (Whisper turbo, mots horodatés, source Huma) : Qu'ils 102,12 / s'en 102,42 / aillent 102,66 / tous 102,90 / nous 103,38 / allons 103,72 /
# les 103,98 / remplacer 104,14 / partout 104,74
CARDS = [
    [(120, 1180, [("QU’ILS", 102.12, WHITE), ("S’EN", 102.42, WHITE)]),
     (None, None, [("AILLENT", 102.66, WHITE), ("TOUS", 102.90, RED)])],
    [(120, 1180, [("NOUS", 103.38, WHITE), ("ALLONS", 103.72, WHITE)]),
     (None, None, [("LES", 103.98, WHITE), ("REMPLACER", 104.14, WHITE)]),
     (None, None, [("PARTOUT", 104.74, RED)])],
]
TXT_W = 630                                       # zone sûre TikTok : bloc <= 66 % de 1080 (entrée à 112 % comprise), bas du bloc <= 1440 px
def layout(card):
    out = []; y_prev = None; s_prev = None
    for size, yc, words in card:
        txt = " ".join(w for w, _, _ in words)
        if size is None: size = min(fit_size(txt, TXT_W, start=s_prev), s_prev); yc = y_prev + s_prev * 0.5 + 30 + size * 0.5
        else: size = fit_size(txt, TXT_W, start=size)
        f = font(size); x = (W - f.getlength(txt)) / 2
        for w, t, col in words:
            out.append(dict(w=w, t=t, col=col, size=size, x=x, yc=yc)); x += f.getlength(w + " ")
        y_prev, s_prev = yc, size
    return out
def draw_words(items, scale_last=1.0, alpha_last=1.0):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay); ds = ImageDraw.Draw(sh)
    for k, it in enumerate(items):
        last = k == len(items) - 1; sc = scale_last if last else 1.0
        f = font(it["size"] * sc); sw = max(4, int(it["size"] * 0.045))
        x = it["x"] + (font(it["size"]).getlength(it["w"]) - f.getlength(it["w"])) / 2
        x0, y0, x1, y1 = d.textbbox((0, 0), it["w"], font=f); y = it["yc"] - (y1 - y0) / 2 - y0
        a = int(255 * (alpha_last if last else 1.0))
        ds.text((x, y + it["size"] * 0.05), it["w"], font=f, fill=(0, 0, 0, int(a * 0.78)), stroke_width=sw * 3, stroke_fill=(0, 0, 0, int(a * 0.78)))
        d.text((x, y), it["w"], font=f, fill=it["col"] + (a,), stroke_width=sw, stroke_fill=(0, 0, 0, a))
    sh = sh.filter(ImageFilter.GaussianBlur(18))
    return np.asarray(Image.alpha_composite(sh, lay)).astype(np.float32) / 255
def phrase_text(t_src):
    ci = max([i for i, c in enumerate(CARDS) if t_src >= c[0][2][0][1]], default=None)
    if ci is None: return None
    card = CARDS[ci]; fixed = [(it["size"], it["yc"]) for it in layout(card)]; k = 0; vis = []
    for size, yc, words in card:
        ws = []
        for w in words:
            if t_src >= w[1]: ws.append((w, fixed[k]))
            k += 1
        if ws: vis.append(ws)
    items = []
    for ws in vis:
        size, yc = ws[0][1]; f = font(size); x = (W - f.getlength(" ".join(w[0] for w, _ in ws))) / 2
        for (w, t, col), _ in ws:
            items.append(dict(w=w, t=t, col=col, size=size, x=x, yc=yc)); x += f.getlength(w + " ")
    last = max(items, key=lambda it: it["t"]); items.remove(last); items.append(last)
    e = ease_out(min((t_src - last["t"]) * FPS / 3.0, 1.0))
    return draw_words(items, scale_last=1.12 - 0.12 * e, alpha_last=min(1.0, 0.35 + e))
def over_rgba(img_bgr, rgba, k=1.0):
    a = rgba[..., 3:4] * k; rgb = rgba[..., 2::-1]
    return img_bgr * (1 - a) + rgb * a
# ---------------- mot power : capitales, Arial Black abîmée (texture érodée), blanc, centré à mi-hauteur ----------------
@functools.lru_cache(None)
def power_layer(word):
    lines = word.split("\n")                                  # 1 ou 2 lignes, même taille, bloc <= 600 px de large centré à 56 % de la hauteur
    size = min(fit_size(l, 600, start=300 if len(lines) == 1 else 190) for l in lines); f = font(size)
    im = Image.new("L", (W, H), 0); d = ImageDraw.Draw(im)
    gap = size * 0.12; hs = []
    for l in lines: x0, y0, x1, y1 = d.textbbox((0, 0), l, font=f); hs.append((x0, y0, x1, y1))
    tot = sum(b[3] - b[1] for b in hs) + gap * (len(lines) - 1); y = H * 0.56 - tot / 2
    for l, (x0, y0, x1, y1) in zip(lines, hs):
        d.text(((W - (x1 - x0)) / 2 - x0, y - y0), l, font=f, fill=255); y += (y1 - y0) + gap
    a = np.asarray(im).astype(np.float32) / 255
    rng = np.random.default_rng(sum(map(ord, word)))
    n1 = cv2.GaussianBlur(rng.random((H, W)).astype(np.float32), (0, 0), 2.2)          # trous fins (encre usée)
    n2 = cv2.GaussianBlur(rng.random((H // 8, W // 8)).astype(np.float32), (0, 0), 1.5)
    n2 = cv2.resize(n2, (W, H))                                                          # zones plus pâles (tampon)
    holes = np.clip((n1 - 0.535) * 30, 0, 1)
    wear = np.clip((n2 - 0.56) * 6, 0, 0.55)
    edge = cv2.GaussianBlur(a, (0, 0), 3.0); rough = np.clip((edge + (n1 - 0.5) * 0.9 - 0.45) * 6, 0, 1)   # bords rongés
    alpha = np.clip(a * rough * (1 - holes) * (1 - wear), 0, 1)
    sh = np.clip(cv2.GaussianBlur(a, (0, 0), 14) * 1.1, 0, 0.85)                                          # ombre douce pour la lisibilité
    return alpha, sh
def put_power(img, word, i):
    alpha, sh = power_layer(word)
    e = ease_out(min((i + 1) / 3.0, 1.0)); s = 1.10 - 0.10 * e                              # entrée 3 images, sans rebond
    if s != 1.0:
        M = cv2.getRotationMatrix2D((W / 2, H * 0.56), 0, s)
        alpha = cv2.warpAffine(alpha, M, (W, H)); sh = cv2.warpAffine(sh, M, (W, H))
    img = img * (1 - sh[..., None] * e)
    return img * (1 - alpha[..., None] * e) + 1.0 * alpha[..., None] * e
# ---------------- rendu ----------------
def write_mov(frames, path, fps=FPS):
    p = subprocess.Popen([FF, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", "%dx%d" % (W, H), "-r", str(fps), "-i", "-",
                          "-c:v", "prores_ks", "-profile:v", "3", "-pix_fmt", "yuv422p10le", "-vendor", "apl0", path], stdin=subprocess.PIPE)
    for f in frames: p.stdin.write(to8(f).tobytes())
    p.stdin.close(); p.wait()
def slots():
    out = [("long", "cut", PREF[0], PREF[1], None), ("foule", "cut", PREF[1], PREF[2], None)]
    for i, (sid, eff, nb, word) in enumerate(EDIT): out.append((sid, eff, CUTF[i], CUTF[i + 1], word))
    return out
def clip_name(sid): return "W1_%s.mov" % sid
FADE_N = 14                                                    # fondu noir total sur les 14 dernières images
def render_slot(sid, eff, a, b, word):
    sh = SHOTS[sid]; n = b - a
    raw, s0 = read_frames(sh["src"], sh["t"], n)
    z0, z1 = sh["zoom"]; push = lambda f: z0 + (z1 - z0) * min(f / max(n - 1, 1), 1.0)
    zoom = push
    if sh.get("track"):
        hs = face_heights(sh["src"], s0, n, sh["face"], sh["b"])
        if hs: h0 = hs[0]; zoom = lambda f: push(f) * max(1.0, h0 / hs[f])
    sf = SFPS[sh["src"]]
    if "fixed" in sh:
        views, _ = plan_views(sh["src"], s0, n, sf, speed=sf / FPS, bounds=sh["b"], vh=sh["vh"], zoom=zoom, fixed=sh["fixed"])
    else:
        dx = sh.get("dx", 0)
        views, ok = plan_views(sh["src"], s0, n, sf, speed=sf / FPS, hint=sh["face"], bounds=sh["b"], vh=sh["vh"], zoom=zoom, top=sh["top"],
                               shake=(lambda f: (dx, 0)) if dx else None)
        if not ok: print("  ! pas de visage :", sid)
    last = sid == EDIT[-1][0]; frames = []
    for i, (img, (cx, cy, vh)) in enumerate(zip(raw, views)):
        g = grade(crop_916(img, cx, cy, vh))
        if sid in ("long", "foule"):
            tl = phrase_text(SRC_OFF + (a + i) / FPS)
            if tl is not None: g = over_rgba(g, tl)
        for wd, k0, k1 in WORDS:
            f0, f1 = CUTF[CUT_K.index(k0)], CUTF[CUT_K.index(k1)]
            if f0 <= a + i < f1: g = put_power(g, wd, a + i - f0)
        if eff == "whip" and i < 3: g = motion_blur(g, [220, 90, 25][i], 0, steps=16)
        if eff == "drop" and i < 8:
            k = (1 - i / 8) ** 2; g = np.clip(g + k * 0.6 + gblur(g, 25) * k * 0.6, 0, 1)
        if last and i >= n - FADE_N: g = g * ((n - 1 - i) / FADE_N) ** 1.5
        frames.append(g)
    write_mov(frames, OUT + clip_name(sid))
    vx = views[0]; vz = views[-1]
    print("  %-7s %3d im  vue %d,%d h%d -> h%d  (x %d-%d, y %d-%d)" % (sid, n, vx[0], vx[1], vx[2], vz[2], vx[0] - vx[2] * 9 / 32, vx[0] + vx[2] * 9 / 32,
                                                                vx[1] - vx[2] / 2, vx[1] + vx[2] / 2))
def murmure_card(txt, n):
    """Carte « murmure » : fond #F5F5F5, minuscule italique serif fine #C8C8C8, petite, centrée ; grain léger."""
    im = Image.new("L", (W, H), 0xF5); d = ImageDraw.Draw(im); f = ImageFont.truetype(F_MURMURE[0], 64, index=F_MURMURE[1])
    x0, y0, x1, y1 = d.textbbox((0, 0), txt, font=f)
    d.text(((W - (x1 - x0)) / 2 - x0, H * 0.47 - (y1 - y0) / 2 - y0), txt, font=f, fill=0xC8)
    base = np.asarray(im).astype(np.float32) / 255; out = []
    for i in range(n):
        g = base + cv2.resize(RNG.normal(0, 1, (H // 2, W // 2)).astype(np.float32), (W, H)) * 0.012
        out.append(np.repeat(np.clip(g, 0, 1)[..., None], 3, 2))
    return out
def make_cards():
    write_mov(murmure_card("jean-luc", PREF[1] - PREF[0]), OUT + "W1_murmure1.mov")
    write_mov(murmure_card("mélenchon", PREF[2] - PREF[1]), OUT + "W1_murmure2.mov")
# ---------------- plan ----------------
def build_plan():
    video = []
    def add(id_, clip, n, rec, kind, extra=None):
        v = {"id": id_, "clip": clip, "folder": "genW1", "s": 0, "e": n, "rec": rec, "dur": n, "clip_fps": FPS, "track": 1, "kind": kind, "speed_pct": 100}
        if extra: v.update(extra)
        video.append(v)
    for sid, eff, a, b, word in slots():
        sh = SHOTS[sid]; u = URLS[sh["src"]]
        extra = {"source": "%s @ %.2f s (= lot5/sources/%s)" % (REAL[sh["src"]], sh["t"], sh["src"]), "source_fps": SFPS[sh["src"]],
                 "url": u[0], "temps_url_s": round(u[1] + sh["t"], 2), "chaine": u[2], "date": u[3], "effet": eff, "pourquoi": sh["why"],
                 "temps": round((b - a) / FPS / BEAT, 2)}
        ws = [wd for wd, k0, k1 in WORDS if CUTF[CUT_K.index(k0)] < b and CUTF[CUT_K.index(k1)] > a]
        if ws: extra["mot_en_grand"] = ws[0].replace("\n", " / ") + " (Arial Black abîmée, blanc, centré à 56 % de la hauteur, sous le visage, entrée 3 images sur la frappe)"
        if sid == "long": extra["texte"] = "QU’ILS S’EN / AILLENT TOUS (rouge) · NOUS ALLONS / LES REMPLACER / PARTOUT (rouge), mot à mot, Arial Black"
        if sid == EDIT[-1][0]: extra["fin"] = "fondu au noir total sur les %d dernières images" % FADE_N
        add("%s_%d" % (sid, a), clip_name(sid), b - a, a, "shot", extra)
    plan = {"name": "W1 - Aura mots power - Jean-Luc Mélenchon (Chief Keef - Love Sosa)", "fps": FPS, "w": W, "h": H, "duree_s": round(CUTF[-1] / FPS, 3),
            "note": "Style NOUVEAU (inspi .magafx) : ouverture directe sur le plan long synchro (cartes murmure retirées, Luca), drop, drop, montage flash N&B contrasté + grain, mots power abîmés, fondu noir. "
                    "Plans 9:16 recadrés + étalonnés N&B (lot5/_claude/gen/W1/out), vitesse normale, s/e en images du clip (30 i/s), rec en images timeline. "
                    "Coupes sur les frappes réelles de Love Sosa mesurées dans la musique posée (out/W1-frappes.json) : drop = entrée batterie + 808 du 1er refrain "
                    "(71,28 s du complet = %.3f s timeline, image %d), 1 temps = %.4f s (132,35 BPM), aucun plan < 1 temps." % (CUTS[0], DROPF, BEAT),
            "phrase": {"texte": "Qu'ils s'en aillent tous, nous allons les remplacer partout",
                       "suite_non_utilisee": "« … à tous les étages. » (après 1 s de clameur, hors extrait : le sens reste entier)",
                       "source": "%s 102,12-105,10 s (YouTube 80bBtk2lTiI @ 4812,12-4815,10 s, chaîne JEAN-LUC MÉLENCHON, Fête de l'Humanité du 12/09/2026)" % REAL[HU],
                       "timeline_s": [round(102.12 - SRC_OFF, 2), round(105.10 - SRC_OFF, 2)]},
            "mots_en_grand": [{"mot": wd.replace("\n", " "), "debut_s": round(CUTF[CUT_K.index(k0)] / FPS, 3), "fin_s": round(CUTF[CUT_K.index(k1)] / FPS, 3),
                               "frappe_s": CC[CUT_K.index(k0)][0] if k0 < NPOST else None} for wd, k0, k1 in WORDS],
            "video": video,
            "audio": [{"id": "mix", "clip": "W1-mix.wav", "folder": "genW1", "rec": 0, "track": 1,
                       "note": "mix -14 LUFS : musique de 0 à la fin (complet lu en continu dès %.3f s), voix + clameur Huma %.2f-%.2f s timeline, musique -7 dB sous la voix puis remontée sur la clameur jusqu'au drop" % (MUSIC_IN, V_IN - SRC_OFF, V_OUT - SRC_OFF)}],
            "stems": ["lot5/_claude/gen/W1/out/W1-voix.wav", "lot5/_claude/gen/W1/out/W1-musique.wav"],
            "musique": {"fichier": "lot5/sons/W1-chiefkeef-lovesosa_complet.wav", "titre": "Chief Keef - Love Sosa (%s)" % SON_URL,
                        "debut_complet_s": round(MUSIC_IN, 4), "fin_complet_s": round(MUSIC_IN + CUTF[-1] / FPS, 3),
                        "frappes_coupes_s": CC, "coupes_images": CUTF},
            "logos_exclus": "pupitres FÊTE DE L'HUMA / VALENCE / SAINT-DENIS et filigrane MELENCHON2027.fr hors fenêtre"}
    json.dump(plan, open(D + "plan-W1.json", "w"), indent=1, ensure_ascii=False)
    return plan
# ---------------- audio ----------------
def lufs(path):
    r = subprocess.run([FF, "-hide_banner", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    import re
    return float(re.findall(r"I:\s+(-?[0-9.]+) LUFS", r)[-1])
def make_audio():
    import soundfile as sf
    sr = 48000; N = int(round(CUTF[-1] / FPS * sr))
    def grab(path, t, dur):
        p = subprocess.run([FF, "-v", "error", "-ss", "%.3f" % t, "-t", "%.3f" % dur, "-i", path, "-ac", "2", "-ar", str(sr), "-f", "f32le", "-"], capture_output=True)
        return np.frombuffer(p.stdout, np.float32).reshape(-1, 2).copy()
    def place(buf, x, t, gain_db=0, fin=0.0, fout=0.0):
        g = 10 ** (gain_db / 20); n = len(x); env = np.ones(n, np.float32)
        if fin: m = int(fin * sr); env[:m] = np.linspace(0, 1, m)
        if fout: m = int(fout * sr); env[-m:] *= np.linspace(1, 0, m)
        a = int(round(t * sr)); b = min(N, a + n); buf[a:b] += x[:b - a] * env[:b - a, None] * g
    vx = grab(LOT + "/sources/" + HU, V_IN, V_OUT - V_IN)
    m = music_raw(MUSIC_IN, sr)[:N]
    tv0, tv1 = V_IN - SRC_OFF, V_OUT - SRC_OFF
    # voix calée 1 dB sous le refrain (mesuré sur 4 s après le drop)
    sf.write(D + "tmp_v.wav", vx[:int(3.2 * sr)], sr, subtype="FLOAT"); i0 = int(DROP * sr); sf.write(D + "tmp_d.wav", m[i0:i0 + 4 * sr], sr, subtype="FLOAT")
    vg = (lufs(D + "tmp_d.wav") - 1.0) - lufs(D + "tmp_v.wav"); os.remove(D + "tmp_v.wav"); os.remove(D + "tmp_d.wav")
    voix = np.zeros((N, 2), np.float32); mus = np.zeros((N, 2), np.float32)
    place(voix, vx, tv0, vg, fin=0.04, fout=0.35)
    duck = np.ones(len(m), np.float32); g = 10 ** (-7 / 20)
    a0, a1, b0, b1 = [int(t * sr) for t in (0.0, 0.0, 105.12 - SRC_OFF, DROP - 0.02)]   # remontée après « partout », sur la clameur
    duck[a0:a1] = np.linspace(1, g, a1 - a0); duck[a1:b0] = g; duck[b0:b1] = np.linspace(g, 1, b1 - b0)
    place(mus, m * duck[:, None], 0.0, 0.0, fin=0.02, fout=0.45)
    sf.write(OUT + "W1-voix.wav", voix, sr, subtype="PCM_24"); sf.write(OUT + "W1-musique.wav", mus, sr, subtype="PCM_24")
    sf.write(D + "tmp_mix.wav", voix + mus, sr, subtype="FLOAT")
    r = subprocess.run([FF, "-hide_banner", "-i", D + "tmp_mix.wav", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    js = json.loads(r[r.rindex("{"):r.rindex("}") + 1])
    af = ("loudnorm=I=-14:TP=-1.5:LRA=11:measured_I=%s:measured_TP=%s:measured_LRA=%s:measured_thresh=%s:offset=%s:linear=true,"
          "alimiter=limit=0.70:level=false:attack=1:release=60,aresample=48000" % (js["input_i"], js["input_tp"], js["input_lra"], js["input_thresh"], js["target_offset"]))
    subprocess.run([FF, "-v", "error", "-y", "-i", D + "tmp_mix.wav", "-af", af, "-c:a", "pcm_s24le", OUT + "W1-mix.wav"], check=True)
    os.remove(D + "tmp_mix.wav"); print("audio : gain voix %+.1f dB, mix avant normalisation %s LUFS" % (vg, js["input_i"]))
# ---------------- aperçu 540x960 ----------------
def apercu():
    plan = json.load(open(D + "plan-W1.json")); ins = []; fl = []
    for i, v in enumerate(plan["video"]):
        ins += ["-i", OUT + v["clip"]]
        fl.append("[%d:v]trim=start_frame=%d:end_frame=%d,setpts=PTS-STARTPTS,scale=540:960,setsar=1[v%d]" % (i, v["s"], v["e"], i))
    k = len(plan["video"])
    fl.append("".join("[v%d]" % i for i in range(k)) + "concat=n=%d:v=1:a=0[v]" % k)
    ins += ["-i", OUT + "W1-mix.wav"]
    out = ROOT + "/preview/apercu-W1.mp4"
    subprocess.run([FF, "-v", "error", "-y"] + ins + ["-filter_complex", ";".join(fl), "-map", "[v]", "-map", "%d:a" % k,
                    "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "aac", "-b:a", "192k", "-shortest", out], check=True)
    print("aperçu", out)
if __name__ == "__main__":
    args = set(a for a in sys.argv[1:] if not a.startswith("only=")) or {"shots", "cards", "audio", "plan", "apercu"}
    only = [x for a in sys.argv[1:] if a.startswith("only=") for x in a.split("=", 1)[1].split(",")]
    print("musique dès %.4f s du complet ; coupes :" % MUSIC_IN, CC, "\n images :", CUTF, " pré-drop :", PREF, PREH)
    if "shots" in args or only:
        for sid, eff, a, b, word in slots():
            if not only or sid in only: render_slot(sid, eff, a, b, word)
    if "plan" in args: build_plan()
    if "audio" in args: make_audio()
    if "apercu" in args: apercu()
