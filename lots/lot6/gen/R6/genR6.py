# R6 (lot 6) — Collage ransom-note poussé (modèle lot5 R1, recette inspis/2026-10-26 abdulelsayed), Sébastien Delogu, son Aya Nakamura – Djadja (clip officiel).
# Idée du brief : « Du quartier à l'Assemblée », photos découpées qui se superposent ; palette bleu, jaune, blanc (aucune couleur de R1).
# Poussé par rapport à R1 : découpes de personnes isolées par instance (Vision VNGeneratePersonInstanceMaskRequest, tools/inst) même
#   devant les députés assis derrière lui, double tirage en trame d'imprimerie derrière chaque découpe, fond en papier froissé (plis) +
#   feuille déchirée d'une 2e couleur, photos en bichromie (bleu / jaune) bord déchiré + scotch, morceaux de texte parfois déchirés ou
#   scotchés, mots-clés qui arrivent lettre par lettre, une couche de plus à chaque frappe, flash blanc 3 images seulement au drop.
# Phrase (son direct, synchro) : « J'ai été sanctionné, intimidé, menacé et même moqué. Je vous ai vu vous moquer car je trébuchais sur
#   des mots, mais moi au moins, mes valeurs n'ont pas titubé. » (QAG Gaza, 28/05/2025, chaîne La France insoumise à l'Assemblée
#   nationale, youtu.be/gEZLJe_uJUs 5,60-15,26 s) -> autre phrase que A8 (132,7 s, « du mauvais côté du règlement ») et P2 (meeting
#   Quartiers Nord, « passé du quartier à l'Assemblée »). Début de la phrase « Comme tant d'autres Français, » (4,08-5,42) non gardé.
# Son : Djadja, extrait continu ; la phrase est posée sur le pont sans basse (« Putain mais tu déconnes… », 78,8-88,2 s du morceau),
#   drop = retour du kick sur le refrain « Oh Djadja » (88,19 s), puis coupes toutes les 2 temps sur les kicks réels (98 BPM).
# Textes après le drop (retour Luca 27/10) : cartons qui se lisent seuls, dans l'ordre de la phrase : SANCTIONNÉ. / INTIMIDÉ. / MENACÉ. / MOQUÉ.
#   (un par temps) puis MAIS MOI AU MOINS / MES VALEURS N'ONT PAS TITUBÉ., puis le carton final (nom seul) ; B5-B6 sans texte.
# Usage : python genR6.py [shots] [audio] [plan] [apercu] [mesure] [only=ID,ID]   (sans argument = tout sauf mesure)
import sys
sys.dont_write_bytecode = True
import os, json, subprocess, math, re
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
HG = "/Users/luca.grousset/Movies/highkey-gauchiste"
D = HG + "/lot6/_claude/gen/R6/"; OUT = D + "out/"; CACHE = D + "cache/"; os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, D)
from hits import detect_hits
FF = "/opt/homebrew/bin/ffmpeg"; INST = D + "tools/inst"; FPS = 30; W, H = 1080, 1920
def fr(t): return int(round(t * FPS))
def hexc(h): h = h.lstrip("#"); return np.array([int(h[4:6], 16), int(h[2:4], 16), int(h[0:2], 16)], np.float32) / 255   # BGR
def rgb(h): h = h.lstrip("#"); return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
# palette R6 : bleu cobalt, bleu ciel, jaune, blanc, papier, encre
BLUE, SKY, YELLOW, WHITE, PAPER, INK = "#1F45D1", "#62C3F0", "#FFD21A", "#FFFFFF", "#F3F0E6", "#0D1B3E"

# ---------------- sources (lecture seule, lot 3) ----------------
SRC = {
    "QAG": ("lot3/sources/A8-delogu-qag-gaza-2025.mp4", 25.0, "https://www.youtube.com/watch?v=gEZLJe_uJUs", 0.0,
            "QAG Gaza, 28/05/2025 (chaîne La France insoumise à l'Assemblée nationale)"),
    "LF": ("lot3/sources/A8-delogu-drapeau-lfian.mp4", 25.0, "https://www.youtube.com/watch?v=iHBkHUaUUTc", None,
           "hémicycle, QAG du 28/05/2024 (chaîne La France insoumise à l'Assemblée nationale)"),
    "NA": ("lot3/sources/A8-delogu-quartiers-nord-a.mp4", 25.0, "https://www.youtube.com/watch?v=oKStIbwdqHc", 4680.0,
           "meeting Quartiers Nord, liste Marseille fière et populaire, 08/02/2026 (chaîne Sébastien Delogu)"),
    "NB": ("lot3/sources/A8-delogu-quartiers-nord-b.mp4", 25.0, "https://www.youtube.com/watch?v=oKStIbwdqHc", 5240.0,
           "meeting Quartiers Nord, 08/02/2026 (chaîne Sébastien Delogu)"),
    "LA": ("lot3/sources/A8-delogu-lancement-a.mp4", 25.0, "https://www.youtube.com/watch?v=jJa6EONNokI", 1050.0,
           "lancement de campagne, Marseille, 08/12/2025 (chaîne Sébastien Delogu)"),
}

# ---------------- musique : Aya Nakamura – Djadja ----------------
SON_FILE = HG + "/lot6/sons/R6-aya-djadja_complet.wav"; SON_URL = "https://www.youtube.com/watch?v=iPGgnzc34tY"
MDROP = 88.1851                      # retour du kick après le pont sans basse, refrain « Oh Djadja »
DROP = 10.20; T = 0.61218            # 98 BPM (kicks 88,185 -> 98,592)
MUSIC_IN0 = MDROP - DROP
END = 19.55                          # fin juste après « tu dead ça » (97,06 s) ; règle lot 6 : 20 s max
BRK = [81.5536, 85.8455]             # caisses réelles dans le pont (hits.py) -> 2 coupes sous la voix
CUT_T = [b - MUSIC_IN0 for b in BRK] + [DROP] + [DROP + 2 * k * T for k in range(1, 7)]
HITS_JSON = OUT + "R6-frappes.json"
def hits_all(mi):
    """Frappes de l'extrait entier + caisses du pont détectées sur le pont seul (sinon écrasées par la normalisation sur le refrain)."""
    h = detect_hits(music_raw(mi)); pre = [x for x in detect_hits(music_raw(mi, dur=DROP - 0.25)) if x[1] == "caisse"]
    return sorted([x for x in h if not (x[1] == "caisse" and x[0] < DROP - 0.25)] + pre)
def music_raw(mi, dur=END + 0.5, sr=48000):
    import soundfile as sf
    i0 = int(round(mi * sr)); x, r = sf.read(SON_FILE, start=i0, frames=int(dur * sr), dtype="float32"); assert r == sr; return x
def kicks_of(h): return [x[0] for x in h if x[1] == "kick" and x[3] > 0.12]
def snares_of(h): return [x[0] for x in h if x[1] == "caisse"]
def snap_list(h, targets):
    ks, cs = kicks_of(h), snares_of(h); out = []
    for i, t in enumerate(targets):
        if i > 2: t = out[-1] + 2 * T                                      # après le drop : 2 temps après la coupe précédente réelle
        pool = cs if i < 2 else ks
        c = min(pool, key=lambda k: abs(k - t)); assert abs(c - t) < 0.04, ("pas de frappe près de", t, c); out.append(c)
    return out
def frappes():
    if os.path.exists(HITS_JSON):
        js = json.load(open(HITS_JSON))
        if js["cle"] == [MUSIC_IN0, END, CUT_T]: return js["music_in"], js["frappes"]
    best, bad = None, 9
    for off in np.arange(-0.016, 0.0165, 0.001):
        h = hits_all(MUSIC_IN0 + off); cuts = snap_list(h, CUT_T)
        e = max(abs(c - round(c * FPS) / FPS) for c in cuts)
        if e < bad: best, bad, hb = off, e, h
    mi = MUSIC_IN0 + best
    json.dump({"cle": [MUSIC_IN0, END, CUT_T], "music_in": mi, "frappes": hb}, open(HITS_JSON, "w")); return mi, hb
MUSIC_IN, HITS = frappes()
FINE = 0.0                            # recalage fin éventuel mesuré sur l'export AAC
MUSIC_IN += FINE; HITS = [[h[0] - FINE] + list(h[1:]) for h in HITS]
KICKS = kicks_of(HITS)
CUTS = snap_list(HITS, CUT_T); CUTF = [fr(c) for c in CUTS]
DROPF = CUTF[2]; TB = T

# ---------------- voix ----------------
V_SRC0 = 5.31                         # source QAG à t = 0 (« j'ai » 5,60 -> 0,29 s ; « titubé » fin 15,26 -> 9,95 s, avant le drop)
V_IN, V_OUT = 5.53, 15.42             # après « Français, » (fin 5,42) … « titubé » (fin 15,26) ; « Ah, vous qui… » (15,64) non gardé
def t_of_src(s): return s - V_SRC0
WORDS = [("J'AI", 5.60), ("ÉTÉ", 5.74), ("SANCTIONNÉ", 5.94), ("INTIMIDÉ", 7.04), ("MENACÉ", 8.10), ("ET", 8.72), ("MÊME", 9.12),
         ("MOQUÉ", 9.32), ("JE", 9.92), ("VOUS", 10.20), ("AI", 10.42), ("VU", 10.54), ("VOUS", 10.68), ("MOQUER", 10.86), ("CAR", 11.16),
         ("JE", 11.38), ("TRÉBUCHAIS", 11.60), ("SUR", 12.02), ("DES", 12.24), ("MOTS", 12.38), ("MAIS", 12.78), ("MOI", 13.00),
         ("AU", 13.18), ("MOINS", 13.30), ("MES", 13.68), ("VALEURS", 13.98), ("N'ONT", 14.32), ("PAS", 14.48), ("TITUBÉ", 14.66)]
def wt(i): return t_of_src(WORDS[i][1])
def ln(*idx): return [(WORDS[i][0], wt(i)) for i in idx]

# ---------------- polices ransom-note ----------------
S = "/System/Library/Fonts/Supplemental/"
FONTS = [(S + "Arial Black.ttf", 0), (S + "Georgia Bold.ttf", 0), (S + "Times New Roman Bold.ttf", 0), (S + "Impact.ttf", 0),
         (S + "Courier New Bold.ttf", 0), (S + "Rockwell.ttc", 2), (S + "AmericanTypewriter.ttc", 2), (S + "Didot.ttc", 2),
         (S + "Bodoni 72.ttc", 2), (S + "Futura.ttc", 2)]
FCOND = (S + "Futura.ttc", 4)
STYLES = [(rgb(PAPER), rgb(INK)), (rgb(INK), rgb(YELLOW)), (rgb(YELLOW), rgb(INK)), (rgb(BLUE), (255, 255, 255)),
          ((255, 255, 255), rgb(BLUE)), (rgb(SKY), rgb(INK)), (rgb(INK), (255, 255, 255)), ((236, 233, 224), (20, 20, 20))]
_fc = {}
def font(spec, size):
    k = (spec, size)
    if k not in _fc: _fc[k] = ImageFont.truetype(spec[0], size, index=spec[1])
    return _fc[k]

# ---------------- papier : déchirures, scotch, trames ----------------
def skey(x): return sum((i + 1) * ord(c) for i, c in enumerate(str(x)))
def torn_mask(h, w, rng, rough=7, step=14, inset=8):
    pts = []
    for x in np.arange(inset, w - inset, step): pts.append((x, inset + rng.uniform(-rough, rough)))
    for y in np.arange(inset, h - inset, step): pts.append((w - inset + rng.uniform(-rough, rough), y))
    for x in np.arange(w - inset, inset, -step): pts.append((x, h - inset + rng.uniform(-rough, rough)))
    for y in np.arange(h - inset, inset, -step): pts.append((inset + rng.uniform(-rough, rough), y))
    m = np.zeros((h, w), np.float32); cv2.fillPoly(m, [np.array(pts, np.int32)], 1.0, lineType=cv2.LINE_AA)
    return m
def tape_rgba(w, h, rng):
    m = np.ones((h, w), np.float32)
    for y in range(h):
        a = int(rng.integers(0, 7)); b = int(rng.integers(0, 7)); m[y, :a] = 0; m[y, w - b:] = 0
    col = np.array([0.80, 0.88, 0.90], np.float32)[None, None, :] * (1 + 0.04 * rng.standard_normal((h, w, 1)).astype(np.float32))
    return np.dstack([col, m * 0.72]).astype(np.float32)
def rot_rgba(t, ang):
    R = cv2.getRotationMatrix2D((t.shape[1] / 2, t.shape[0] / 2), ang, 1.0)
    c = np.abs(R[:, :2]) @ np.array([t.shape[1], t.shape[0]]); R[0, 2] += c[0] / 2 - t.shape[1] / 2; R[1, 2] += c[1] / 2 - t.shape[0] / 2
    return cv2.warpAffine(t, R, (int(c[0]), int(c[1])))
def over(dst, src, x, y):
    """Colle src (BGRA float) dans dst (BGRA float) au coin (x, y), en restant dans dst."""
    h, w = src.shape[:2]; x0, y0 = max(0, x), max(0, y); x1, y1 = min(dst.shape[1], x + w), min(dst.shape[0], y + h)
    if x1 <= x0 or y1 <= y0: return
    s = src[y0 - y:y1 - y, x0 - x:x1 - x]; d = dst[y0:y1, x0:x1]; a = s[..., 3:4]
    d[..., :3] = d[..., :3] * (1 - a) + s[..., :3] * a; d[..., 3] = np.maximum(d[..., 3], s[..., 3])

def chip(txt, h, rng, fspec=None, style=None, rot=None, torn=None, tape=None):
    """Un morceau découpé : rectangle irrégulier (ou déchiré) + texte, RGBA PIL, légèrement penché ; parfois un bout de scotch."""
    fspec = fspec or FONTS[rng.integers(len(FONTS))]; bg, fg = style or STYLES[rng.integers(len(STYLES))]
    size = int(h * 0.80); f = font(fspec, size)
    x0, y0, x1, y1 = f.getbbox(txt, anchor="ls"); cap = f.getbbox("H", anchor="ls")
    tw, th = x1 - x0, max(y1, 0) - min(y0, cap[1])
    px, py = int(h * (0.08 if len(txt) == 1 else 0.16)), int(h * 0.10)
    w_, h_ = tw + 2 * px, th + 2 * py
    im = Image.new("RGBA", (w_ + 12, h_ + 12), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    j = lambda: rng.integers(-4, 5)
    d.polygon([(6 + j(), 6 + j()), (6 + w_ + j(), 6 + j()), (6 + w_ + j(), 6 + h_ + j()), (6 + j(), 6 + h_ + j())], fill=bg + (255,))
    d.text((6 + px - x0, 6 + py - min(y0, cap[1])), txt, font=f, fill=fg + (255,), anchor="ls")
    if torn if torn is not None else rng.random() < 0.35:                     # bord déchiré
        a = np.asarray(im).copy(); m = torn_mask(a.shape[0], a.shape[1], rng, rough=4, step=9, inset=5)
        a[..., 3] = (a[..., 3] * m).astype(np.uint8); im = Image.fromarray(a)
    a = rot if rot is not None else rng.uniform(-4, 4)
    im = im.rotate(a, resample=Image.BICUBIC, expand=True)
    if tape if tape is not None else (len(txt) > 2 and rng.random() < 0.22):    # scotch sur un coin
        t = (rot_rgba(tape_rgba(int(h * 0.9), int(h * 0.26), rng), rng.uniform(-50, -30)) * 255).astype(np.uint8)
        t = Image.fromarray(np.dstack([t[..., 2], t[..., 1], t[..., 0], t[..., 3]]))
        big = Image.new("RGBA", (im.width + t.width // 2, im.height + t.height // 2), (0, 0, 0, 0))
        big.alpha_composite(im, (t.width // 4, t.height // 4)); big.alpha_composite(t, (int(rng.uniform(0, 0.15) * im.width), 0)); im = big
    return im
def shadowed(im):
    a = np.asarray(im)[..., 3].astype(np.float32) / 255
    sh = cv2.GaussianBlur(a, (0, 0), 3) * 0.55
    out = np.zeros((im.height + 12, im.width + 12, 4), np.float32)
    out[9:9 + im.height, 7:7 + im.width, 3] = sh
    rgb_ = np.asarray(im)[..., :3][..., ::-1].astype(np.float32) / 255
    out[:im.height, :im.width, :3] = out[:im.height, :im.width, :3] * (1 - a[..., None]) + rgb_ * a[..., None]
    out[:im.height, :im.width, 3] = a + out[:im.height, :im.width, 3] * (1 - a)
    return out
XMIN, XMAX, YMIN, YMAX = 0.19 * W, 0.81 * W, 0.13 * H, 0.74 * H          # zone sûre TikTok (0,17-0,83 / 0,12-0,75) + marge
def word_parts(word, t, h, rng, letters, seq, tape=None):
    """Pièces d'un mot : [(img, t)] ; lettres découpées une à une (seq = intervalle entre lettres, 0 = toutes ensemble)."""
    if not letters: return [(shadowed(chip(word, h, rng, tape=tape)), t)]
    return [(shadowed(chip(c, h * rng.uniform(0.92, 1.08), rng, rot=rng.uniform(-7, 7), tape=False)), t + k * seq) for k, c in enumerate(word)]
def board(lines, y0, seed, h=112, letters=(), seq=0.0, maxw=XMAX - XMIN - 30, tape=None):
    """lines = [[(mot, t), …], …] -> pièces placées [(img, cx, cy, t)] ; mots de `letters` en lettres découpées."""
    rng = np.random.default_rng(seed); pieces = []; y = y0
    for line in lines:
        words = [word_parts(w, t, h * (1.12 if w in letters else 1.0), rng, w in letters, seq, tape) for w, t in line]
        gap, ov = 8, 12
        wsz = [sum(p.shape[1] for p, _ in wp) - ov * (len(wp) - 1) for wp in words]
        tot = sum(wsz) + gap * (len(words) - 1)
        sc = min(1.0, maxw / tot); lh = max(p.shape[0] for wp in words for p, _ in wp) * sc
        x = W / 2 - tot * sc / 2 + rng.uniform(-14, 14); x = min(max(x, XMIN + 4), XMAX - 4 - tot * sc)
        for wp in words:
            for p, t in wp:
                if sc < 1: p = cv2.resize(p, (int(p.shape[1] * sc), int(p.shape[0] * sc)), interpolation=cv2.INTER_AREA)
                pieces.append((p, x + p.shape[1] / 2, y + lh / 2 + rng.uniform(-5, 5), t)); x += p.shape[1] - ov * sc
            x += (gap + ov) * sc
        y += lh - 6
    for im, cx, cy, t in pieces:
        assert XMIN - 2 <= cx - im.shape[1] / 2 and cx + im.shape[1] / 2 <= XMAX + 2, ("texte hors zone x", cx, im.shape)
        assert YMIN - 2 <= cy - im.shape[0] / 2 and cy + im.shape[0] / 2 <= YMAX + 2, ("texte hors zone y", cy, im.shape)
    return pieces
def big_text(lines, y0, spec, maxw, sizes):
    pieces = []; y = y0
    for k, (txt, t, col) in enumerate(lines):
        size = sizes[k]; f = font(spec, size)
        while f.getlength(txt) > maxw - 44: size -= 4; f = font(spec, size)
        x0, y0b, x1, y1 = f.getbbox(txt)
        im = Image.new("RGBA", (x1 - x0 + 24, y1 - y0b + 24), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.text((12 - x0, 12 - y0b), txt, font=f, fill=tuple(col) + (255,))
        a = np.dstack([np.asarray(im)[..., :3][..., ::-1], np.asarray(im)[..., 3]]).astype(np.float32) / 255
        pieces.append((a, W / 2, y + a.shape[0] / 2, t)); y += a.shape[0] - 18
    for im, cx, cy, t in pieces:
        assert XMIN - 2 <= cx - im.shape[1] / 2 and YMIN - 2 <= cy - im.shape[0] / 2 and cy + im.shape[0] / 2 <= YMAX + 2, ("hors zone", cy)
    return pieces

# ---------------- compositing ----------------
def paste(dst, rgba, cx, cy, scale=1.0, angle=0.0):
    h, w = rgba.shape[:2]
    M = cv2.getRotationMatrix2D((w / 2, h / 2), angle, scale); M[0, 2] += cx - w / 2; M[1, 2] += cy - h / 2
    c = np.array([[0, 0, 1], [w, 0, 1], [0, h, 1], [w, h, 1]], np.float32) @ M.T
    x0, y0 = max(0, int(c[:, 0].min()) - 1), max(0, int(c[:, 1].min()) - 1)
    x1, y1 = min(W, int(c[:, 0].max()) + 2), min(H, int(c[:, 1].max()) + 2)
    if x1 <= x0 or y1 <= y0: return
    M2 = M.copy(); M2[0, 2] -= x0; M2[1, 2] -= y0
    r = cv2.warpAffine(rgba, M2, (x1 - x0, y1 - y0), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    a = r[..., 3:4]; dst[y0:y1, x0:x1] = dst[y0:y1, x0:x1] * (1 - a) + r[..., :3] * a
def pop(f, f0, n=4, amp=0.12):
    if f < f0: return None
    u = min(1.0, (f - f0) / n); return 1 + amp * (1 - u) ** 2
FOLDS = None
def folds():
    """Papier froissé : quelques plis (arêtes claires / ombres douces) multipliés sur les fonds."""
    global FOLDS
    if FOLDS is None:
        rng = np.random.default_rng(21); y, x = np.mgrid[0:H, 0:W].astype(np.float32); acc = np.zeros((H, W), np.float32)
        for _ in range(7):
            a = rng.uniform(0, np.pi); px, py = rng.uniform(0, W), rng.uniform(0, H)
            d = (x - px) * np.sin(a) - (y - py) * np.cos(a); wdt = rng.uniform(18, 60)
            acc += rng.uniform(0.5, 1.0) * np.sign(d) * np.exp(-np.abs(d) / wdt) * rng.choice([-1, 1])
        acc += cv2.resize(rng.standard_normal((24, 14)).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC) * 0.5
        FOLDS = (1 + 0.045 * acc)[..., None].astype(np.float32)
    return FOLDS
_tex = {}
def paper(col):
    if col not in _tex:
        rng = np.random.default_rng(len(_tex) + 3)
        n = cv2.resize(rng.standard_normal((48, 27)).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC)
        n2 = cv2.GaussianBlur(rng.standard_normal((H, W)).astype(np.float32), (0, 0), 1.2)
        fib = cv2.GaussianBlur(rng.standard_normal((H, W)).astype(np.float32), (0, 0), sigmaX=6, sigmaY=0.8)   # fibres
        _tex[col] = np.clip(hexc(col)[None, None, :] * (1 + 0.025 * n[..., None] + 0.03 * n2[..., None] + 0.05 * fib[..., None]) * folds(), 0, 1).astype(np.float32)
    return _tex[col].copy()
_sheets = {}
def torn_sheet(colhex, side, frac, ang, seed):
    """Feuille déchirée d'une 2e couleur qui couvre le haut ou le bas du fond (bord déchiré en biais + ombre)."""
    k = (colhex, side, frac, ang, seed)
    if k not in _sheets:
        rng = np.random.default_rng(seed); y0 = H * frac; pts = []
        for x in range(-20, W + 40, 16):
            pts.append((x, y0 + (x - W / 2) * math.tan(math.radians(ang)) + rng.uniform(-11, 11) + 9 * math.sin(x / 37.0)))
        pts = pts + ([(W + 40, H + 20), (-20, H + 20)] if side == "bas" else [(W + 40, -20), (-20, -20)])
        m = np.zeros((H, W), np.float32); cv2.fillPoly(m, [np.array(pts, np.int32)], 1.0, lineType=cv2.LINE_AA)
        edge = cv2.GaussianBlur(m, (0, 0), 1.0) - cv2.GaussianBlur(cv2.erode(m, np.ones((7, 7), np.uint8)), (0, 0), 2.0)
        sh = cv2.GaussianBlur(np.roll(m, -10 if side == "bas" else 10, axis=0), (0, 0), 7) * 0.40
        col = paper(colhex); white = np.clip(np.ones_like(col) * 0.96 * folds(), 0, 1)       # fibres blanches au bord déchiré
        _sheets[k] = (m, sh, col, np.clip(edge, 0, 1), white)
    return _sheets[k]
def apply_sheet(img, spec):
    m, sh, col, edge, white = torn_sheet(*spec)
    img *= (1 - sh[..., None]); img[:] = img * (1 - m[..., None]) + col * m[..., None]; img[:] = img * (1 - edge[..., None]) + white * edge[..., None]
VIG = None
def finish(img, f):
    global VIG
    if VIG is None:
        y, x = np.mgrid[0:H, 0:W].astype(np.float32)
        r = np.sqrt(((x - W / 2) / (W / 2)) ** 2 + ((y - H / 2) / (H / 2)) ** 2) / np.sqrt(2)
        VIG = (1 - 0.24 * np.clip(r, 0, 1) ** 2.4)[..., None].astype(np.float32)
    g = np.random.default_rng(1000 + f).standard_normal((H // 2, W // 2)).astype(np.float32)
    g = cv2.resize(g, (W, H), interpolation=cv2.INTER_LINEAR)[..., None] * 0.024
    return np.clip(img * VIG + g, 0, 1)

# ---------------- lecture source, détourage ----------------
def read_frames(src, t, n_out):
    path, sfps = SRC[src][0], SRC[src][1]
    need = [int(round(i * sfps / FPS)) for i in range(n_out)]
    p = subprocess.run([FF, "-v", "error", "-ss", "%.4f" % t, "-i", HG + "/" + path, "-frames:v", str(need[-1] + 1),
                        "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True)
    a = np.frombuffer(p.stdout, np.uint8).reshape(-1, 1080, 1920, 3)
    return [a[min(i, len(a) - 1)].astype(np.float32) / 255 for i in need]
def masks(key, frames, box, pt, k=13):
    """Détourage de LA personne visée (instance Vision qui contient le point pt, normalisé dans box) ; cache dans cache/seg/<key>."""
    x0, y0, x1, y1 = box; d = CACHE + "seg/" + key; di, dm = d + "/in", d + "/m"
    if not (os.path.isdir(dm) and len(os.listdir(dm)) >= len(frames)):
        os.makedirs(di, exist_ok=True)
        for i, fr_ in enumerate(frames): cv2.imwrite("%s/f%04d.png" % (di, i), (fr_[y0:y1, x0:x1] * 255).astype(np.uint8))
        subprocess.run([INST, di, dm, str(pt[0]), str(pt[1])], check=True, capture_output=True)
    out = []
    for i in range(len(frames)):
        m = cv2.imread("%s/f%04d.png" % (dm, i), 0)
        m = m.astype(np.float32) / 255 if m is not None else (out[-1] if out else np.zeros((y1 - y0, x1 - x0), np.float32))
        m = cv2.morphologyEx(m, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))
        b = (m > 0.35).astype(np.uint8); cs, _ = cv2.findContours(b, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if cs:                                                              # trous bouchés (micro devant lui) : seule la plus grande forme, pleine
            fill = np.zeros_like(b); cv2.drawContours(fill, [max(cs, key=cv2.contourArea)], -1, 1, -1)
            m = np.where(fill > 0, np.maximum(m, cv2.erode(fill, np.ones((5, 5), np.uint8)).astype(np.float32)), 0).astype(np.float32)
        m = np.clip((cv2.GaussianBlur(m, (0, 0), 1.2) - 0.5) * 2.2 + 0.5, 0, 1)
        out.append(m)
    return out
def grade(x, sat=1.10):
    x = 0.82 * x + 0.18 * (x * x * (3 - 2 * x))
    L = x @ np.array([0.0722, 0.7152, 0.2126], np.float32)
    return np.clip(L[..., None] + (x - L[..., None]) * sat, 0, 1)
def lum(x, gain=1.15):
    L = x @ np.array([0.0722, 0.7152, 0.2126], np.float32)
    L = L / max(float(np.percentile(L, 99)), 0.2); L = np.clip(L, 0, 1) ** 0.75
    L = np.clip((L - 0.5) * gain + 0.5 + 0.03, 0, 1); return 0.75 * L + 0.25 * (L * L * (3 - 2 * L))
DUO = {"bleu": (INK, "#DCE8FF"), "cobalt": (BLUE, WHITE), "jaune": (INK, YELLOW), "ciel": ("#12307F", SKY)}
def duotone(x, duo):
    a, b = DUO[duo]; L = lum(x)[..., None]; return hexc(a)[None, None, :] * (1 - L) + hexc(b)[None, None, :] * L
def cutout_rgba(img, m, box, white=False):
    x0, y0, x1, y1 = box; c = grade(img[y0:y1, x0:x1])
    if white: c = np.ones_like(c) * np.array([0.97, 0.97, 0.97], np.float32)
    return np.dstack([c, m]).astype(np.float32)
_scr = {}
def screen(h, w, cell=13):
    if (h, w) not in _scr:
        y, x = np.mgrid[0:h, 0:w].astype(np.float32); u, v = (x + y) / 1.4142, (x - y) / 1.4142
        _scr[(h, w)] = (np.cos(2 * np.pi * u / cell) + np.cos(2 * np.pi * v / cell)) / 4 + 0.5
    return _scr[(h, w)]
def ghost_rgba(img, m, box, sc, colhex):
    """Double tirage en trame d'imprimerie (points à 45°) de la découpe, couleur unie : posé derrière la découpe principale."""
    x0, y0, x1, y1 = box; w, h = int((x1 - x0) * sc), int((y1 - y0) * sc)
    L = cv2.resize(lum(img[y0:y1, x0:x1], 1.3), (w, h), interpolation=cv2.INTER_AREA); mm = cv2.resize(m, (w, h), interpolation=cv2.INTER_AREA)
    ink = np.clip(((1 - L) * 0.9 + 0.08 - screen(h, w)) * 6, 0, 1) * mm
    return np.dstack([np.ones((h, w, 3), np.float32) * hexc(colhex)[None, None, :], ink * 0.95]).astype(np.float32)
def sticker(m, r=7):
    return cv2.dilate(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1)))

# ---------------- couches de collage ----------------
def halftone(h, w, col, dot, step=14):
    img = np.ones((h, w, 3), np.float32) * col[None, None, :]
    for y in range(0, h, step):
        for x in range((y // step % 2) * step // 2, w, step): cv2.circle(img, (x, y), 4, tuple(float(v) for v in dot), -1, cv2.LINE_AA)
    return img
STRIP_COLS = [YELLOW, WHITE, BLUE, SKY, INK, PAPER, YELLOW, SKY]
def strip_rgba(w, h, rng, colhex, ht=False):
    col = hexc(colhex); dot = hexc(INK if colhex in (YELLOW, WHITE, SKY, PAPER) else SKY)
    body = halftone(h, w, col, dot) if ht else np.ones((h, w, 3), np.float32) * col[None, None, :]
    body = np.clip(body * (1 + 0.035 * cv2.GaussianBlur(rng.standard_normal((h, w)).astype(np.float32), (0, 0), 1.5))[..., None], 0, 1)
    m = torn_mask(h, w, rng, rough=9, step=12)
    out = np.zeros((h + 16, w + 16, 4), np.float32)
    out[10:10 + h, 8:8 + w, 3] = cv2.GaussianBlur(m, (0, 0), 3) * 0.45
    a = m[..., None]; out[:h, :w, :3] = body * a; out[:h, :w, 3] = np.maximum(m, out[:h, :w, 3])
    return out
def make_strips(sh):
    n = sh.get("strips", 0); rng = np.random.default_rng(skey(sh["id"]) + 5); out = []
    zones = [(150, 480), (930, 560), (120, 1250), (960, 1300), (540, 300), (540, 1700), (230, 900), (880, 1050), (300, 1600), (820, 1750)]
    for k in range(n):
        w, h = int(rng.uniform(380, 660)), int(rng.uniform(80, 160))
        colhex = STRIP_COLS[(k + skey(sh["id"])) % len(STRIP_COLS)]
        if colhex in (sh.get("bg"), (sh.get("sheet") or (None,))[0]): colhex = STRIP_COLS[(k + 3) % len(STRIP_COLS)]
        cx, cy = zones[(k * 3 + skey(sh["id"])) % len(zones)]
        out.append(dict(img=strip_rgba(w, h, rng, colhex, ht=(k % 3 == 1)), cx=cx + rng.uniform(-60, 60), cy=cy + rng.uniform(-60, 60),
                        ang=rng.uniform(-28, 28), k=k))
    return out
class Photo:
    """Photo vivante en bichromie (bleu ou jaune) : bord papier déchiré, scotch aux coins, ombre ; elle saute un peu sur chaque frappe."""
    def __init__(self, frames, box, width, center, angle, f0, key, duo, border=16):
        self.frames, self.box, self.width, self.center, self.angle, self.f0, self.key, self.duo = frames, box, width, center, angle, f0, key, duo
        x0, y0, x1, y1 = box; self.h = int(round(width * (y1 - y0) / (x1 - x0))); self.b = border
        rng = np.random.default_rng(skey(key)); M = 40
        self.M = M; hh, ww = self.h + 2 * border, width + 2 * border
        self.mask = torn_mask(hh, ww, rng, rough=6, step=11, inset=3)
        self.shadow = np.zeros((hh + 2 * M, ww + 2 * M), np.float32); self.shadow[M + 9:M + 9 + hh, M + 7:M + 7 + ww] = self.mask * 0.5
        self.shadow = cv2.GaussianBlur(self.shadow, (0, 0), 4)
        self.tapes = []
        for (tx, ty) in ((M + int(rng.uniform(-10, 30)), M - 12), (M + ww - int(rng.uniform(90, 140)), M + hh - 26)):
            self.tapes.append((rot_rgba(tape_rgba(int(rng.uniform(110, 150)), 38, rng), rng.uniform(-40, -25)), (tx, ty)))
    def rgba(self, i):
        x0, y0, x1, y1 = self.box; b, M = self.b, self.M
        c = cv2.resize(duotone(self.frames[i][y0:y1, x0:x1], self.duo), (self.width, self.h), interpolation=cv2.INTER_AREA)
        hh, ww = self.h + 2 * b, self.width + 2 * b
        out = np.zeros((hh + 2 * M, ww + 2 * M, 4), np.float32); out[..., 3] = self.shadow
        body = np.ones((hh, ww, 3), np.float32) * np.array([0.95, 0.95, 0.94], np.float32); body[b:b + self.h, b:b + self.width] = c
        a = self.mask[..., None]; reg = out[M:M + hh, M:M + ww]
        reg[..., :3] = body * a; reg[..., 3] = np.maximum(self.mask, reg[..., 3])
        for t, (tx, ty) in self.tapes: over(out, t, tx, ty)
        return out
def beat_grid():
    """Temps : kicks réels après le drop + grille d'un temps comptée à rebours depuis le drop dans le pont sans kick."""
    g = [k for k in KICKS if k >= CUTS[2] - 0.05]; t = CUTS[2] - T
    while t > 0: g.append(t); t -= T
    return sorted(g)
BEATS = beat_grid(); BEATF = [fr(b) for b in BEATS]
def nbeat(f): return sum(1 for b in BEATF if b <= f)
def jit(key, k, amp=8.0, ang=1.5):
    r = np.random.default_rng(skey(key) * 1000 + k); return r.uniform(-amp, amp), r.uniform(-amp, amp), r.uniform(-ang, ang)

# ---------------- plans ----------------
QBOX = (330, 40, 1590, 800)           # QAG : logo LFI (haut gauche), chrono AN (haut droite) et sous-titres incrustés (y > 805) hors fenêtre
QPT = (0.452, 0.737)                  # point sur sa poitrine (instance Vision = lui seul, pas les députés derrière)
KEYL = ("MOQUÉ", "MENACÉ", "TITUBÉ", "MOTS", "VU")
SHOTS = [
    dict(id="A1", kind="cut", src="QAG", t=None, bg=BLUE, sheet=(YELLOW, "bas", 0.80, -4, 1), ghost=YELLOW, box=QBOX, pt=QPT,
         scale=(1.45, 1.48), cx=890,
         boards=[([ln(0, 1), ln(2), ln(3), ln(4)], None)], txt_h=118, strips=4,
         photos=[("QAG", 49.0, (0, 250, 1920, 790), 560, (250, 1240), -6, wt(3) , "cobalt")],
         why="2025 — QAG Gaza, son direct : « J'ai été sanctionné, intimidé, menacé », Delogu détouré seul (instance) sur fond cobalt, double tirage tramé jaune, hémicycle en photo"),
    dict(id="A2", kind="cut", src="QAG", t=None, bg=YELLOW, sheet=(WHITE, "haut", 0.11, 3, 2), ghost=BLUE, box=QBOX, pt=QPT,
         scale=(1.48, 1.51), cx=890,
         boards=[([ln(5, 6), ln(7)], None), ([ln(8, 9), ln(10, 11), ln(12, 13)], wt(8)), ([ln(14, 15), ln(16), ln(17, 18, 19)], wt(14))],
         txt_h=128, strips=4,
         photos=[("LF", 161.0, (60, 280, 1860, 1000), 600, (800, 1180), 5, 0.0, "bleu")],
         why="même plan synchro : « et même moqué. Je vous ai vu vous moquer car je trébuchais sur des mots », 3 tableaux qui se remplacent, hémicycle 2024 en photo bleue"),
    dict(id="A3", kind="cut", src="QAG", t=None, bg=PAPER, sheet=(SKY, "bas", 0.83, 5, 3), ghost=BLUE, box=QBOX, pt=QPT,
         scale=(1.51, 1.56), cx=890,
         boards=[([ln(20, 21), ln(22, 23)], None), ([ln(24, 25), ln(26, 27), ln(28)], wt(24))], txt_h=140, strips=6,
         photos=[("NB", 284.0, (0, 200, 1920, 1080), 520, (230, 1000), -6, 0.0, "jaune"), ("NB", 241.0, (0, 150, 1920, 1080), 500, (850, 930), 5, wt(24), "jaune")],
         why="même plan synchro : « mais moi au moins, mes valeurs n'ont pas titubé » ; les photos du meeting des quartiers Nord se collent derrière lui (du quartier à l'Assemblée)"),
    dict(id="B1", kind="sil", src="NB", t=414.0, bg=YELLOW, ghost=BLUE, box=(380, 0, 1640, 1080), pt=(0.47, 0.75), dest_w=1500, cx=980, push=(1.0, 1.04),
         rboards=[([[("SANCTIONNÉ.", 0.0)]], 0.0), ([[("INTIMIDÉ.", TB)]], TB)], txt_y=330, txt_h=150, strips=3, flash=True,
         why="2026 — meeting Quartiers Nord, gros plan intense : silhouette blanche 3 images (flash du drop) puis Delogu détouré en couleur, contour autocollant, double tirage tramé bleu"),
    dict(id="B2", kind="collage", bg=BLUE,
         photos=[("NB", 432.5, (0, 120, 1920, 1080), 700, (500, 820), -4, 0.0, "jaune"), ("LF", 163.0, (60, 280, 1860, 1000), 640, (600, 1260), 5, TB, "ciel"),
                 ("NB", 288.0, (0, 200, 1920, 1080), 560, (380, 1600), -3, 1.5 * TB, "jaune")],
         rboards=[([[("MENACÉ.", 0.0)]], 0.0), ([[("MOQUÉ.", TB)]], TB)], txt_y=300, letters=("MENACÉ.", "MOQUÉ."), txt_h=170, strips=3,
         why="collage : la salle des quartiers Nord (drapeaux) et l'hémicycle se superposent, une photo par temps, sur fond cobalt"),
    dict(id="B3", kind="cut", src="LA", t=12.0, bg=SKY, sheet=(YELLOW, "bas", 0.72, -6, 4), ghost=INK, box=(420, 60, 1440, 900), pt=(0.5, 0.55),
         scale=(1.24, 1.28), cx=930,
         photos=[("QAG", 50.5, (0, 250, 1920, 790), 600, (520, 760), 4, 0.0, "cobalt")],
         rboards=[([[("MAIS", 0.0), ("MOI", 0.0)], [("AU", 0.0), ("MOINS", 0.0)]], 0.0)], txt_y=300, txt_h=150, strips=3,
         why="2025 — lancement de campagne à Marseille, au pupitre : détouré sur fond ciel + feuille jaune déchirée, hémicycle tramé derrière"),
    dict(id="B4", kind="cut", src="QAG", t=112.0, bg=YELLOW, sheet=(WHITE, "bas", 0.78, 4, 5), ghost=BLUE, box=(300, 40, 1500, 800), pt=(0.53, 0.75),
         scale=(1.40, 1.45), cx=930,
         photos=[("NB", 241.5, (0, 150, 1920, 1080), 560, (270, 820), -5, 0.0, "bleu"), ("NB", 433.0, (0, 120, 1920, 1080), 520, (820, 700), 6, TB, "bleu")],
         rboards=[([[("MES", 0.0), ("VALEURS", 0.0)], [("N'ONT", 0.0), ("PAS", 0.0)], [("TITUBÉ.", 0.0)]], 0.0)], txt_y=300, letters=("TITUBÉ.",), txt_h=140, strips=3, flash2=True,
         why="2025 — QAG Gaza (fin de la question, sans le son) : l'Assemblée devant les photos bleues de la salle des quartiers Nord"),
    dict(id="B5", kind="collage", bg=PAPER,
         photos=[("QAG", 51.5, (0, 250, 1920, 790), 720, (560, 640), -3, 0.0, "cobalt"), ("NB", 285.5, (0, 200, 1920, 1080), 600, (330, 1060), 5, 0.5 * TB, "jaune"),
                 ("LF", 165.0, (60, 280, 1860, 1000), 600, (760, 1380), -5, TB, "bleu"), ("NB", 434.0, (0, 120, 1920, 1080), 560, (420, 1640), 4, 1.5 * TB, "jaune")],
         strips=3,
         why="collage qui se remplit photo après photo (demi-temps) : hémicycle, salle des quartiers Nord, hémicycle, drapeaux — du quartier à l'Assemblée"),
    dict(id="B6", kind="sil", src="NA", t=195.6, bg=BLUE, ghost=YELLOW, box=(480, 0, 1800, 1080), pt=(0.57, 0.75), dest_w=1450, cx=1240, push=(1.0, 1.035),
         photos=[("NB", 289.0, (0, 200, 1920, 1080), 560, (300, 1180), -6, 0.0, "jaune")],
         strips=3,
         why="2026 — meeting Quartiers Nord, grand sourire (sans parole) : silhouette blanche 3 images puis Delogu en couleur sur fond cobalt, double tirage tramé jaune"),
    dict(id="FIN", kind="card", bg=PAPER, push=(1.0, 1.035),
         big=[("SÉBASTIEN", 0.0, rgb(BLUE)), ("DELOGU", TB, rgb(BLUE))], big_y=560, big_sizes=[330, 400],
         
         why="carton final propre (papier, bleu + jaune) : son nom et ses mots, pas de CTA"),
]
BOUNDS_T = [0] + CUTF + [fr(END)]
assert len(BOUNDS_T) == len(SHOTS) + 1, (len(BOUNDS_T), len(SHOTS))
for i, sh in enumerate(SHOTS):
    sh["a"], sh["bb"] = BOUNDS_T[i], BOUNDS_T[i + 1]; sh["n"] = sh["bb"] - sh["a"]; sh["clip"] = "R6_%s.mov" % sh["id"]
    if sh.get("src") == "QAG" and sh["t"] is None: sh["t"] = V_SRC0 + sh["a"] / FPS          # plans A synchro avec la voix
assert min(sh["n"] for sh in SHOTS) >= 18, [(s["id"], s["n"]) for s in SHOTS]

def write_mov(frames, path):
    p = subprocess.Popen([FF, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", "%dx%d" % (W, H), "-r", str(FPS), "-i", "-",
                          "-c:v", "prores_ks", "-profile:v", "3", "-pix_fmt", "yuv422p10le", "-vendor", "apl0", path], stdin=subprocess.PIPE)
    for f in frames: p.stdin.write((np.clip(f, 0, 1) * 255 + 0.5).astype(np.uint8).tobytes())
    p.stdin.close(); p.wait()
def draw_pieces(img, pieces, f_abs, boil=None):
    k = nbeat(f_abs)
    for j, (im, cx, cy, t) in enumerate(pieces):
        s = pop(f_abs, fr(t))
        if s is None: continue
        dx, dy, da = jit((boil, j), k, amp=4, ang=1.0) if boil else (0, 0, 0)
        paste(img, im, cx + dx, cy + dy, s, da)
CARD_TAPES = [tape_rgba(170, 46, np.random.default_rng(40 + j)) for j in range(4)]
def render(sh):
    n = sh["n"]; a = sh["a"]; frames = []
    rel = lambda t: sh["a"] / FPS + t
    seed = skey(sh["id"]) * 7
    boards = []                                                             # [(pièces, f_début)] en temps timeline
    if sh.get("boards"):
        for j, (lines, t0) in enumerate(sh["boards"]):
            boards.append((board(lines, 272, seed + j, h=sh.get("txt_h", 130), letters=KEYL, seq=0.0), fr(t0) if t0 is not None else a))
    elif sh.get("rboards"):                                                # cartons après le drop : un groupe de mots complet par carton, il remplace le précédent
        for j, (lines, t0) in enumerate(sh["rboards"]):
            p = board(lines, sh["txt_y"], seed + j, h=sh.get("txt_h", 130), letters=sh.get("letters", ()), seq=0.0, tape=False)   # pas de scotch sur les lettres
            boards.append(([(im, cx, cy, rel(t)) for im, cx, cy, t in p], fr(rel(t0))))
    elif sh.get("txt"):
        p = board(sh["txt"], sh["txt_y"], seed, h=sh.get("txt_h", 130), letters=sh.get("letters", ()), seq=sh.get("seq", 0.0))
        boards.append(([(im, cx, cy, rel(t)) for im, cx, cy, t in p], a))
    big = []
    if sh.get("big"):
        big = [(im, cx, cy, rel(t)) for im, cx, cy, t in big_text(sh["big"], sh["big_y"], (S + "Impact.ttf", 0), (XMAX - XMIN) * 0.92, sh["big_sizes"])]
    photos = [Photo(read_frames(ps, pt, n), pbox, pw, pc, pa, fr(rel(pt0)) if pt0 > 0 or sh["id"].startswith("B") else a, (sh["id"], j), duo)
              for j, (ps, pt, pbox, pw, pc, pa, pt0, duo) in enumerate(sh.get("photos", []))]
    if sh["id"].startswith("A"):                                             # plans A : apparition au temps absolu du mot
        for ph, spec in zip(photos, sh.get("photos", [])): ph.f0 = max(a, fr(spec[6])) if spec[6] > 0 else a
    strips = make_strips(sh)
    k0 = nbeat(a)
    if sh["kind"] in ("cut", "sil"):
        raw = read_frames(sh["src"], sh["t"], n)
        ms = masks("%s_%s_%.2f_%d" % (sh["id"], sh["src"], sh["t"], n), raw, sh["box"], sh["pt"], k=27 if sh["kind"] == "sil" else 13)
    for i in range(n):
        f = a + i; u = i / max(n - 1, 1); kb = nbeat(f) - k0
        img = paper(sh["bg"])
        if sh.get("sheet"): apply_sheet(img, sh["sheet"])
        for st in strips:                                                   # une bande de plus à chaque temps
            if st["k"] <= kb:
                dx, dy, da = jit((sh["id"], "s", st["k"]), nbeat(f), amp=6, ang=1.2)
                s_ = pop(f, BEATF[k0 + st["k"] - 1] if st["k"] > 0 and 0 <= k0 + st["k"] - 1 < len(BEATF) else a, n=4, amp=0.08) or 1.0
                paste(img, st["img"], st["cx"] + dx, st["cy"] + dy, s_, st["ang"] + da)
        for ph in photos:
            s_ = pop(f, ph.f0, n=5, amp=0.10)
            if s_ is not None:
                dx, dy, da = jit(ph.key, nbeat(f), amp=9, ang=1.8)
                paste(img, ph.rgba(i), ph.center[0] + dx, ph.center[1] + dy, s_, ph.angle + da)
        if sh["kind"] in ("cut", "sil"):
            x0, y0, x1, y1 = sh["box"]; m = ms[i]
            if sh["kind"] == "cut":
                sc = sh["scale"][0] + (sh["scale"][1] - sh["scale"][0]) * u; hh = (y1 - y0) * sc
                ccx = W / 2 + ((x1 - x0) / 2 - (sh["cx"] - x0)) * sc; ccy = H - hh / 2; r_ = 7
            else:
                z = sh["push"][0] + (sh["push"][1] - sh["push"][0]) * u
                sc = sh["dest_w"] / (x1 - x0) * z; hh = (y1 - y0) * sc
                ccx = W / 2 + ((x1 - x0) / 2 - (sh["cx"] - x0)) * sc; ccy = H - hh / 2; r_ = 9
            if sh.get("ghost"):                                             # double tirage tramé, décalé, qui saute sur les temps
                gdx, gdy, gda = jit((sh["id"], "g"), nbeat(f), amp=10, ang=1.0)
                g = ghost_rgba(raw[i], m, sh["box"], 1.0, sh["ghost"])
                paste(img, g, ccx + 46 + gdx, ccy - 34 + gdy, sc * 1.10, -2.5 + gda)
            st_ = np.dstack([np.ones((m.shape[0], m.shape[1], 3), np.float32) * np.array([0.97, 0.97, 0.96], np.float32), sticker(m, r_)])
            sd = st_.copy(); sd[..., :3] = 0; sd[..., 3] = cv2.GaussianBlur(st_[..., 3], (0, 0), 6) * 0.55
            paste(img, sd, ccx + 14, ccy + 10, sc)
            if sh["kind"] == "sil" and i < 3: paste(img, cutout_rgba(raw[i], m, sh["box"], white=True), ccx, ccy, sc)   # silhouette blanche 3 images
            else: paste(img, st_, ccx, ccy, sc); paste(img, cutout_rgba(raw[i], m, sh["box"]), ccx, ccy, sc)
        cur = None
        for jb, (p, f0) in enumerate(boards):
            if f >= f0: cur = (jb, p)
        if cur: draw_pieces(img, cur[1], f, boil=sh["id"] + str(cur[0]))
        if sh["kind"] == "card":
            for j, (tx, ty, ta) in enumerate(((175, 300, -32), (905, 300, 30), (175, 1540, 28), (905, 1540, -30))):
                paste(img, CARD_TAPES[j], tx, ty, 1.0, ta)
            z = sh["push"][0] + (sh["push"][1] - sh["push"][0]) * u
            for im, cx, cy, t in big:
                s_ = pop(f, fr(t))
                if s_ is not None: paste(img, im, W / 2 + (cx - W / 2) * z, H / 2 + (cy - H / 2) * z, s_ * z)
        if sh.get("flash") and i < 3: img = img + (1 - img) * [1.0, 0.6, 0.25][i]       # flash blanc 3 images (drop)
        if sh.get("flash2") and i < 2: img = img + (1 - img) * [0.7, 0.3][i]
        frames.append(finish(img, f))
    write_mov(frames, OUT + sh["clip"])
    print("  %-4s %3d im  (%s)" % (sh["id"], n, sh["kind"]), flush=True)

# ---------------- audio ----------------
def make_audio():
    import soundfile as sf
    sr = 48000; N = int(round(END * sr))
    def grab(path, t, dur):
        p = subprocess.run([FF, "-v", "error", "-ss", "%.3f" % t, "-t", "%.3f" % dur, "-i", path, "-ac", "2", "-ar", str(sr), "-f", "f32le", "-"], capture_output=True)
        return np.frombuffer(p.stdout, np.float32).reshape(-1, 2).copy()
    voix = np.zeros((N, 2), np.float32); mus = np.zeros((N, 2), np.float32)
    v = grab(HG + "/" + SRC["QAG"][0], V_IN, V_OUT - V_IN); env = np.ones(len(v), np.float32)
    k = int(0.03 * sr); env[:k] = np.linspace(0, 1, k); k = int(0.08 * sr); env[-k:] = np.linspace(1, 0, k)
    i0 = int(round(t_of_src(V_IN) * sr)); voix[i0:i0 + len(v)] = v * env[:, None] * 10 ** (VGAIN / 20)
    m = music_raw(MUSIC_IN)[:N]
    t = np.arange(len(m)) / sr; vend = t_of_src(V_OUT); dr = CUTS[2]
    # sous la phrase : pont sans basse baissé, montée progressive, plein sur le drop « Oh Djadja »
    gdb = np.interp(t, [0, 0.25, 4.0, vend - 0.6, dr - 0.03, dr, END], [-22, -19, -18, -12, -8, 0, 0])
    k = int(0.40 * sr); fo = np.ones(len(m), np.float32); fo[-k:] = np.linspace(1, 0, k)
    mus[:len(m)] = m * (10 ** (gdb / 20) * fo)[:, None]
    sf.write(OUT + "R6-voix.wav", voix, sr, subtype="PCM_24"); sf.write(OUT + "R6-musique.wav", mus, sr, subtype="PCM_24")
    sf.write(D + "tmp_mix.wav", voix + mus, sr, subtype="FLOAT")
    r = subprocess.run([FF, "-hide_banner", "-i", D + "tmp_mix.wav", "-af", "loudnorm=I=-14:TP=-2.5:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    js = json.loads(r[r.rindex("{"):r.rindex("}") + 1])
    af = ("loudnorm=I=-14:TP=-2.5:LRA=11:measured_I=%s:measured_TP=%s:measured_LRA=%s:measured_thresh=%s:offset=%s:linear=true,"
          "aresample=48000" % (js["input_i"], js["input_tp"], js["input_lra"], js["input_thresh"], js["target_offset"]))
    subprocess.run([FF, "-v", "error", "-y", "-i", D + "tmp_mix.wav", "-af", af, "-c:a", "pcm_s24le", OUT + "R6-mix.wav"], check=True)
    os.remove(D + "tmp_mix.wav"); print("audio : mix avant normalisation", js["input_i"], "LUFS")
VGAIN = 4.0

# ---------------- plan ----------------
def build_plan():
    video = []
    for sh in SHOTS:
        v = {"id": sh["id"], "clip": sh["clip"], "folder": "genR6", "path": OUT + sh["clip"], "s": 0, "e": sh["n"], "rec": sh["a"], "dur": sh["n"],
             "clip_fps": FPS, "speed_pct": 100, "track": 1, "note": sh["why"], "kind": sh["kind"], "temps": round(sh["n"] / FPS / T, 2)}
        if sh.get("src"):
            path, sfps, url, off, ctx = SRC[sh["src"]]
            v["source"] = {"fichier": path, "in_s": round(sh["t"], 3), "out_s": round(sh["t"] + sh["n"] / FPS, 3), "fps": sfps, "url": url, "contexte": ctx}
            if off is not None: v["source"]["youtube_t"] = round(off + sh["t"], 1)
        if sh.get("photos"):
            v["photos"] = [{"fichier": SRC[p[0]][0], "in_s": p[1], "out_s": round(p[1] + sh["n"] / FPS, 2), "cadre_source": p[2], "bichromie": p[7], "url": SRC[p[0]][2]} for p in sh["photos"]]
        video.append(v)
    texts = []
    for sh in SHOTS:
        for lines, _ in sh.get("boards", []):
            for line in lines: texts.append({"plan": sh["id"], "texte": " ".join(w for w, _ in line)})
        for line in sh.get("txt", []): texts.append({"plan": sh["id"], "texte": " ".join(w for w, _ in line)})
        for lines, _ in sh.get("rboards", []): texts.append({"plan": sh["id"], "texte": " ".join(w for line in lines for w, _ in line)})
        for s_, t_, c_ in sh.get("big", []): texts.append({"plan": sh["id"], "texte": s_})
    PHR = "J'ai été sanctionné, intimidé, menacé et même moqué. Je vous ai vu vous moquer car je trébuchais sur des mots, mais moi au moins, mes valeurs n'ont pas titubé."
    plan = {"name": "R6 - Collage ransom-note - Sébastien Delogu", "fps": FPS, "w": W, "h": H, "duree_s": END,
            "note": "Plans ProRes 9:16 composés en Python (lot6/_claude/gen/R6/out) : fonds papier froissé + feuille déchirée, Delogu détouré seul "
                    "(instance Vision, tools/inst), double tirage tramé, silhouettes blanches 3 images, photos vivantes en bichromie, textes ransom-note cuits. "
                    "s/e en images du clip (30 i/s), rec en images timeline. Coupes sur les frappes réelles de Djadja (out/R6-frappes.json). Aucun ralenti. "
                    "Générateur : lot6/_claude/gen/R6/genR6.py",
            "phrase": {"texte": PHR, "url": SRC["QAG"][2], "source": SRC["QAG"][0], "in_s": 5.60, "out_s": 15.26,
                       "timeline_s": [round(t_of_src(5.60), 2), round(t_of_src(15.26), 2)],
                       "voix": "son direct synchro (plans A1-A3) ; la phrase commence dans la source par « Comme tant d'autres Français, » (4,08-5,42), non gardé"},
            "musique": {"fichier": "lot6/sons/R6-aya-djadja_complet.wav", "titre": "Aya Nakamura - Djadja", "url": SON_URL,
                        "debut_complet_s": round(MUSIC_IN, 4), "fin_complet_s": round(MUSIC_IN + END, 3), "drop_timeline_s": CUTS[2],
                        "coupes_frappes_s": CUTS, "coupes_images": CUTF},
            "textes": texts, "video": video,
            "audio": [{"id": "mix", "clip": "R6-mix.wav", "folder": "genR6", "path": OUT + "R6-mix.wav", "rec": 0, "track": 1,
                       "note": "mix -14 LUFS : voix QAG %.2f-%.2f s (+%.0f dB) à %.2f s ; Djadja dès %.3f s du complet, -19 dB sous la voix (pont sans basse), montée, plein au drop, fondu de fin 0,4 s"
                               % (V_IN, V_OUT, VGAIN, t_of_src(V_IN), MUSIC_IN)}],
            "stems": ["lot6/_claude/gen/R6/out/R6-voix.wav", "lot6/_claude/gen/R6/out/R6-musique.wav"],
            "logos_exclus": "QAG : logo LFI, chrono AN et sous-titres incrustés hors des fenêtres (détourage et photos) ; hémicycle 2024 : logo et chrono hors cadre photo ; "
                            "meetings : fond rouge, affiches et logo LFI supprimés par le détourage"}
    json.dump(plan, open(D + "plan-R6.json", "w"), indent=1, ensure_ascii=False)
    son = {"id": "R6", "titre": "Djadja", "artiste": "Aya Nakamura", "url": SON_URL,
           "chaine": "Aya Nakamura (officielle, certifiée, « Aya Nakamura - Djadja (Clip officiel) »)",
           "fichier": "lot6/sons/R6-aya-djadja_complet.wav",
           "extrait_complet_s": {"debut": round(MUSIC_IN, 4), "fin": round(MUSIC_IN + END, 3)},
           "paroles_audibles": "sous la phrase (baissé) : fin de « C'est pas comme ça qu'on fait les choses » puis le pont « Putain mais tu déconnes / C'est pas comme ça qu'on fait les choses » x2 ; "
                               "au drop : refrain « Oh Djadja, y a pas moyen Djadja, j'suis pas ta catin Djadja, genre… »",
           "bpm": 98.0, "temps_s": T,
           "drop": {"complet_s": round(MUSIC_IN + CUTS[2], 4), "timeline_s": CUTS[2], "nature": "retour du kick après le pont sans basse, refrain « Oh Djadja »"},
           "frappes_timeline_s": [round(k, 4) for k in KICKS], "coupes_sur_frappes_s": CUTS,
           "mix": "lot6/_claude/gen/R6/out/R6-mix.wav"}
    json.dump(son, open(D + "son.json", "w"), indent=1, ensure_ascii=False)

# ---------------- aperçu 540x960 ----------------
def apercu():
    plan = json.load(open(D + "plan-R6.json")); ins = []; fl = []
    for i, v in enumerate(plan["video"]):
        ins += ["-i", OUT + v["clip"]]
        fl.append("[%d:v]trim=start_frame=%d:end_frame=%d,setpts=PTS-STARTPTS,scale=540:960,setsar=1[v%d]" % (i, v["s"], v["e"], i))
    k = len(plan["video"]); fl.append("".join("[v%d]" % i for i in range(k)) + "concat=n=%d:v=1:a=0[v]" % k)
    ins += ["-i", OUT + "R6-mix.wav"]; out = HG + "/preview/apercu-R6.mp4"
    subprocess.run([FF, "-v", "error", "-y"] + ins + ["-filter_complex", ";".join(fl), "-map", "[v]", "-map", "%d:a" % k,
                    "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "aac", "-b:a", "192k", "-shortest", out], check=True)
    print("aperçu", out)
# ---------------- mesure sur l'export : coupes vs frappes, LUFS / TP ----------------
def mesure():
    out = HG + "/preview/apercu-R6.mp4"
    r = subprocess.run([FF, "-v", "info", "-i", out, "-vf", "scale=135:240,select='gt(scene,0.2)',showinfo", "-an", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    cuts = [float(x) for x in re.findall(r"pts_time:([0-9.]+)", r)]
    p = subprocess.run([FF, "-v", "error", "-i", out, "-vn", "-ac", "2", "-ar", "48000", "-f", "f32le", "-"], capture_output=True)
    y = np.frombuffer(p.stdout, np.float32).reshape(-1, 2)
    hh = detect_hits(y)
    worst = 0
    for i, c in enumerate([fr_ / FPS for fr_ in CUTF]):
        det = min(cuts, key=lambda x: abs(x - c)) if cuts else None
        pool = [x[0] for x in hh if (x[1] == "kick" and x[3] > 0.03)] if i >= 2 else [x[0] for x in hh]
        k = min(pool, key=lambda t: abs(t - c)); e = (c - k) * 1000; worst = max(worst, abs(e))
        print("  coupe %.3f (détectée %s)  frappe %.4f  écart %+.1f ms" % (c, "%.3f" % det if det is not None else "-", k, e))
    print("écart max coupes/frappes : %.1f ms" % worst)
    r = subprocess.run([FF, "-hide_banner", "-i", out, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    print(r[r.rindex("Summary"):])
if __name__ == "__main__":
    args = set(a for a in sys.argv[1:] if not a.startswith("only=")) or {"shots", "audio", "plan", "apercu"}
    only = [x for a in sys.argv[1:] if a.startswith("only=") for x in a.split("=", 1)[1].split(",")]
    print("musique dès %.4f s ; coupes (s) :" % MUSIC_IN, [round(c, 4) for c in CUTS], "images :", CUTF)
    if "shots" in args or only:
        for sh in SHOTS:
            if not only or sh["id"] in only: render(sh)
    if "audio" in args: make_audio()
    if "plan" in args: build_plan()
    if "apercu" in args: apercu()
    if "mesure" in args: mesure()
