# R15 (lot 7) — Collage ransom-note « pop chic », photos tramées (modèle lot6 R6 / lot5 R1, recette inspis/2026-10-26 abdulelsayed),
#   Mathilde Panot, son Sabrina Carpenter – Espresso (audio officiel, chaîne Sabrina Carpenter).
# Palette R15 (brief) : cerise + vert sapin, crème, encre (aucune couleur de R1-R6 ni des autres R du lot 7).
# Poussé par rapport à R6 : photos en trame d'imprimerie visible (points ronds à 45°, encre sapin ou cerise sur crème), double tirage
#   tramé derrière chaque découpe, fonds papier froissé + feuille déchirée, bandes tramées, scotch, morceaux de texte serif chic / sans
#   mélangés, mots-clés lettre par lettre, une couche de plus à chaque frappe, flash blanc 3 images seulement au drop.
# Phrase (son direct, synchro) : « Plus vous nous tapez, plus nous sortons de l'ombre en nombre. Plus vous nous ciblez, plus des gens
#   viennent nous rejoindre pour mener le combat. » (meeting de Rochefort, 22/10/2026, chaîne Mathilde Panot, youtu.be/4l2dx1n-UFo
#   120,04-127,84 s = lot2/sources/A1-panot-rochefort-b.mp4 100,04-107,84 s)
#   -> autre phrase que A1 (« Désormais, plus rien ne passera. ») et A10 (« Ils ne viendront pas à bout de nous. »).
# Son : Espresso, extrait continu ; la phrase passe sur la fin du pré-refrain (complet 54,9-63,8 s, filtré et baissé, qui s'ouvre =
#   montée), drop = 1er temps du 2e refrain (kick 63,77 s du complet), fin à 74,41 s (fin de la 1re moitié du refrain) ;
#   coupes sur les kicks réels (104 BPM, une coupe toutes les 2 ou 4 temps). Aucune parole du morceau écrite ici (consigne Luca).
# Textes après le drop (règle Luca 27/10) : groupes complets dans l'ordre de la phrase, un par plan : PLUS VOUS NOUS TAPEZ, /
#   PLUS NOUS SORTONS DE L'OMBRE EN NOMBRE. / PLUS VOUS NOUS CIBLEZ, / PLUS DES GENS VIENNENT NOUS REJOINDRE / POUR MENER LE COMBAT.
#   puis carton final MATHILDE PANOT.
# Usage : python genR15.py [shots] [audio] [plan] [apercu] [mesure] [only=ID,ID]   (sans argument = tout sauf mesure)
import sys
sys.dont_write_bytecode = True
import os, json, subprocess, math, re
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
HG = "/Users/luca.grousset/Movies/highkey-gauchiste"
D = HG + "/lot7/_claude/gen/R15/"; OUT = D + "out/"; CACHE = D + "cache/"; os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, D)
from hits import detect_hits
FF = "/opt/homebrew/bin/ffmpeg"; FPS = 30; W, H = 1080, 1920
def fr(t): return int(round(t * FPS))
def hexc(h): h = h.lstrip("#"); return np.array([int(h[4:6], 16), int(h[2:4], 16), int(h[0:2], 16)], np.float32) / 255   # BGR
def rgb(h): h = h.lstrip("#"); return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
# palette R15 : cerise, vert sapin, mousse (vert clair), crème, encre, blanc
CHERRY, SAPIN, MOSS, CREAM, INK, WHITE = "#B5163C", "#123F2E", "#7FA88A", "#F3EADB", "#17120F", "#FFFFFF"
PAPER = CREAM

# ---------------- sources (lecture seule, lot 2) ----------------
URL_R = "https://www.youtube.com/watch?v=4l2dx1n-UFo"; CTX_R = "meeting de Rochefort, 22/10/2026 (chaîne Mathilde Panot)"
SRC = {
    "RB": ("lot2/sources/A1-panot-rochefort-b.mp4", 30.0, URL_R, 20.0, CTX_R),
    "RA": ("lot2/sources/A1-panot-rochefort-a.mp4", 30.0, URL_R, 1545.0, CTX_R),
    "RC": ("lot2/sources/A1-panot-rochefort-c.mp4", 30.0, URL_R, 1980.0, CTX_R),
    "QAG": ("lot2/sources/A1-panot-lcp-qag-2025-12.mp4", 25.0, "https://www.youtube.com/watch?v=mqeo_ILV2_w", 0.0,
            "questions au gouvernement, 04/12/2025 (LCP - Assemblée nationale)"),
}

# ---------------- musique : Sabrina Carpenter – Espresso ----------------
SON_FILE = HG + "/lot7/sons/R15-sabrina-espresso_complet.wav"; SON_URL = "https://www.youtube.com/watch?v=51zjlMhdSTE"
MDROP = 63.7721                      # kick du 1er temps du 2e refrain (juste après le pré-refrain)
DROP = 8.90; T = 0.57699             # 104 BPM (kicks forts 52,233 -> 75,312 : 20 x 2 temps)
MUSIC_IN0 = MDROP - DROP
END0 = DROP + 10.64                  # fenêtre d'analyse des frappes (clé du cache out/R15-frappes.json)
END = END0                           # fin réelle : recalculée après les coupes (carton final 1,5 s, retour Luca)
BRK = [59.1532, 61.4274]             # kicks réels du pré-refrain -> 2 coupes sous la voix
PER = [1, 2, 1, 2, 1]                # après le drop : durée des plans en x 2 temps (FIN = le reste)
CUT_T = [b - MUSIC_IN0 for b in BRK] + [DROP] + [DROP + 2 * T * sum(PER[:k + 1]) for k in range(len(PER))]
HITS_JSON = OUT + "R15-frappes.json"
def hits_all(mi): return detect_hits(music_raw(mi))
def music_raw(mi, dur=END + 0.5, sr=48000):
    import soundfile as sf
    i0 = int(round(mi * sr)); x, r = sf.read(SON_FILE, start=i0, frames=int(dur * sr), dtype="float32"); assert r == sr; return x
def kicks_of(h, lvl=0.45): return [x[0] for x in h if x[1] == "kick" and x[3] > lvl]
def snares_of(h): return [x[0] for x in h if x[1] == "caisse"]
def snap_list(h, targets):
    ks = kicks_of(h); out = []
    for i, t in enumerate(targets):
        if i > 2: t = out[-1] + 2 * T * PER[i - 3]                          # après le drop : depuis la coupe précédente réelle
        c = min(ks, key=lambda k: abs(k - t)); assert abs(c - t) < 0.08, ("pas de frappe près de", t, c); out.append(c)
    return out
def frappes():
    if os.path.exists(HITS_JSON):
        js = json.load(open(HITS_JSON))
        if js["cle"] == [MUSIC_IN0, END0, CUT_T]: return js["music_in"], js["frappes"]
    best, bad = None, 9
    for off in np.arange(-0.016, 0.0165, 0.001):
        h = hits_all(MUSIC_IN0 + off); cuts = snap_list(h, CUT_T)
        e = max(abs(c - round(c * FPS) / FPS) for c in cuts)
        if e < bad: best, bad, hb = off, e, h
    mi = MUSIC_IN0 + best
    json.dump({"cle": [MUSIC_IN0, END0, CUT_T], "music_in": mi, "frappes": hb}, open(HITS_JSON, "w")); return mi, hb
MUSIC_IN, HITS = frappes()
FINE = 0.0                            # recalage fin éventuel mesuré sur l'export AAC
MUSIC_IN += FINE; HITS = [[h[0] - FINE] + list(h[1:]) for h in HITS]
KICKS = kicks_of(HITS)
CUTS = snap_list(HITS, CUT_T); CUTF = [fr(c) for c in CUTS]
DROPF = CUTF[2]; TB = 2 * T            # un carton / une photo par demi-mesure
END = (CUTF[-1] + 45) / FPS            # carton final tenu 1,5 s (retour Luca lot 6 R4) puis fondu musique 0,4 s
FINP = min(k for k in KICKS if k > CUTS[-1] + 0.4) - CUTF[-1] / FPS   # PANOT sur la frappe suivante (temps relatif au carton)

# ---------------- voix ----------------
V_SRC0 = 108.26 - CUTS[2]             # source RB à t = 0 ; la régie passe sur la salle à 108,30 s : le dernier plan synchro s'arrête avant
V_IN, V_OUT = 99.98, 107.98           # « Plus » 100,04 … « combat. » fin 107,84
def t_of_src(s): return s - V_SRC0
WORDS = [("PLUS", 100.04), ("VOUS", 100.48), ("NOUS", 100.72), ("TAPEZ,", 100.88), ("PLUS", 101.52), ("NOUS", 101.86), ("SORTONS", 102.06),
         ("DE", 102.50), ("L'OMBRE", 102.64), ("EN", 102.96), ("NOMBRE.", 103.12),
         ("PLUS", 103.70), ("VOUS", 104.02), ("NOUS", 104.22), ("CIBLEZ,", 104.42), ("PLUS", 105.10), ("DES", 105.44), ("GENS", 105.70),
         ("VIENNENT", 105.86), ("NOUS", 106.12), ("REJOINDRE", 106.30), ("POUR", 106.80), ("MENER", 107.04), ("LE", 107.32), ("COMBAT.", 107.48)]
def wt(i): return t_of_src(WORDS[i][1])
def ln(*idx): return [(WORDS[i][0], wt(i)) for i in idx]

# ---------------- polices ransom-note (serif chic + sans) ----------------
S = "/System/Library/Fonts/Supplemental/"
FONTS = [(S + "Didot.ttc", 2), (S + "Bodoni 72.ttc", 2), (S + "Futura.ttc", 2), (S + "Arial Black.ttf", 0), (S + "Georgia Bold.ttf", 0),
         (S + "Didot.ttc", 1), (S + "Futura.ttc", 4), (S + "Rockwell.ttc", 2), (S + "Times New Roman Bold.ttf", 0), (S + "AmericanTypewriter.ttc", 2)]
FCOND = (S + "Futura.ttc", 4)
NARROW = [(S + "Impact.ttf", 0), (S + "Arial Narrow Bold.ttf", 0), FCOND, (S + "Didot.ttc", 2), (S + "Bodoni 72.ttc", 2),
          (S + "Times New Roman Bold.ttf", 0)]   # carton final : polices étroites (serif / sans mélangés), lettres plus hautes
NARROW = [f for f in NARROW if "Bodoni" not in f[0] and "Didot" not in f[0]] + [(S + "Times New Roman Bold.ttf", 0), (S + "Georgia Bold.ttf", 0)]
STYLES = [(rgb(CREAM), rgb(INK)), (rgb(CHERRY), rgb(WHITE)), (rgb(SAPIN), rgb(CREAM)), (rgb(WHITE), rgb(CHERRY)),
          (rgb(INK), rgb(CREAM)), (rgb(MOSS), rgb(INK)), (rgb(CREAM), rgb(SAPIN)), (rgb(WHITE), rgb(SAPIN))]
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

def chip(txt, h, rng, fspec=None, style=None, rot=None, torn=None, tape=None, trame=False):
    """Un morceau découpé : rectangle irrégulier (ou déchiré) + texte, RGBA PIL, légèrement penché ; parfois un bout de scotch."""
    fspec = fspec or FONTS[rng.integers(len(FONTS))]; bg, fg = style or STYLES[rng.integers(len(STYLES))]
    size = int(h * 0.80); f = font(fspec, size)
    x0, y0, x1, y1 = f.getbbox(txt, anchor="ls"); cap = f.getbbox("H", anchor="ls")
    tw, th = x1 - x0, max(y1, 0) - min(y0, cap[1])
    px, py = int(h * (0.035 if trame else 0.08 if len(txt) == 1 else 0.16)), int(h * (0.06 if trame else 0.10))
    w_, h_ = tw + 2 * px, th + 2 * py
    im = Image.new("RGBA", (w_ + 12, h_ + 12), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    j = lambda: rng.integers(-4, 5)
    d.polygon([(6 + j(), 6 + j()), (6 + w_ + j(), 6 + j()), (6 + w_ + j(), 6 + h_ + j()), (6 + j(), 6 + h_ + j())], fill=bg + (255,))
    if trame and rng.random() < 0.45:                                       # trame d'imprimerie (papier magazine) sur le morceau
        dot = tuple(int(c * 0.82) for c in bg) + (255,) if sum(bg) > 300 else tuple(min(255, int(c * 1.35) + 18) for c in bg) + (255,)
        for yy in range(10, h_ + 4, 9):
            for xx in range(10 + (yy // 9 % 2) * 4, w_ + 4, 9): d.ellipse([xx - 1.7, yy - 1.7, xx + 1.7, yy + 1.7], fill=dot)
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
def word_parts(word, t, h, rng, letters, seq, tape=None, narrow=False):
    """Pièces d'un mot : [(img, t)] ; lettres découpées une à une (seq = intervalle entre lettres, 0 = toutes ensemble)."""
    if not letters: return [(shadowed(chip(word, h, rng, tape=tape)), t)]
    return [(shadowed(chip(c, h * rng.uniform(0.92, 1.08), rng, rot=rng.uniform(-4, 4) if narrow else rng.uniform(-7, 7), tape=False,
                           fspec=NARROW[rng.integers(len(NARROW))] if narrow else None, trame=narrow)), t + k * seq) for k, c in enumerate(word)]
def board(lines, y0, seed, h=112, letters=(), seq=0.0, maxw=XMAX - XMIN - 30, tape=None, narrow=False, xmin=XMIN, xmax=XMAX):
    """lines = [[(mot, t), …], …] -> pièces placées [(img, cx, cy, t)] ; mots de `letters` en lettres découpées."""
    rng = np.random.default_rng(seed); pieces = []; y = y0
    for line in lines:
        words = [word_parts(w, t, h * (1.12 if w in letters else 1.0), rng, w in letters, seq, tape, narrow) for w, t in line]
        gap, ov = 8, (int(h * 0.17) if narrow else 12)
        wsz = [sum(p.shape[1] for p, _ in wp) - ov * (len(wp) - 1) for wp in words]
        tot = sum(wsz) + gap * (len(words) - 1)
        sc = min(1.0, maxw / tot); lh = max(p.shape[0] for wp in words for p, _ in wp) * sc
        x = W / 2 - tot * sc / 2 + rng.uniform(-14, 14); x = min(max(x, xmin + 4), xmax - 4 - tot * sc)
        for wp in words:
            for p, t in wp:
                if sc < 1: p = cv2.resize(p, (int(p.shape[1] * sc), int(p.shape[0] * sc)), interpolation=cv2.INTER_AREA)
                pieces.append((p, x + p.shape[1] / 2, y + lh / 2 + rng.uniform(-5, 5), t)); x += p.shape[1] - ov * sc
            x += (gap + ov) * sc
        y += lh - 6
    for im, cx, cy, t in pieces:
        assert xmin - 2 <= cx - im.shape[1] / 2 and cx + im.shape[1] / 2 <= xmax + 2, ("texte hors zone x", cx, im.shape)
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
sys.path.insert(0, HG + "/_claude/outils")
from decoupe import masques, controle, bas_dechire, planche as planche_decoupe
def masks(key, frames, box, pt, sid=""):
    """Découpe de LA personne visée avec l'outil partagé _claude/outils/decoupe.py (instance Vision x segmentation personne : sans pupitre,
    micro ni voisin, une seule forme, lissée) ; cache dans cache/seg/<key>. controle() : gauche/droite/haut = 0 et 1 morceau exigés ;
    le bas (bord du box, coupé net) est posé sur le bas du cadre 9:16 dans render(). Planche de contrôle : cache/decoupe-<id>.jpg."""
    ms = [une_forme(m) for m in masques(frames, box, pt, CACHE + "seg/" + key)]
    cs = [controle(m) for m in ms]
    pire = {k: max(c[k] for c in cs) for k in ("gauche", "droite", "haut", "morceaux", "bas_net", "bas")}
    print("  découpe %-3s %s" % (sid, pire), flush=True)
    planche_decoupe(frames, ms, box, CACHE + "decoupe-%s.jpg" % sid, n=8)
    mauvais = [i for i, c in enumerate(cs) if c["gauche"] or c["droite"] or c["haut"] or c["morceaux"] != 1]
    if mauvais: planche_decoupe([frames[i] for i in mauvais], [ms[i] for i in mauvais], box, CACHE + "decoupe-%s-mauvais.jpg" % sid, n=8)
    assert not mauvais, ("découpe pas propre", sid, pire, "images", mauvais[:5], "...", mauvais[-3:], len(mauvais))
    return ms
def une_forme(m):
    """Après le lissage temporel de l'outil, un bout de manche peut se détacher quelques images : on ne garde que la plus grande forme."""
    n, lab, st, _ = cv2.connectedComponentsWithStats((m > 0.5).astype(np.uint8), 8)
    if n <= 2: return m
    k = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
    return (m * cv2.dilate((lab == k).astype(np.uint8), np.ones((5, 5), np.uint8))).astype(np.float32)
def auto_cx(ms, box):
    """x (source) du centre de la tête : milieu de l'amplitude, sur le plan, du centre des pixels du haut de la découpe (15 % : la tête,
    pas le poing levé) -> la tête bouge le moins possible vers la colonne de boutons ou le bord gauche."""
    xs = []
    for m in ms:
        t = m > 0.5; ys = np.where(t.any(1))[0]
        if len(ys) == 0: continue
        top = t[ys[0]:ys[0] + max(1, int((ys[-1] - ys[0]) * 0.15))]; xs.append(np.where(top.any(0))[0].mean())
    return box[0] + (min(xs) + max(xs)) / 2
def grade(x, sat=1.10):
    x = 0.82 * x + 0.18 * (x * x * (3 - 2 * x))
    L = x @ np.array([0.0722, 0.7152, 0.2126], np.float32)
    return np.clip(L[..., None] + (x - L[..., None]) * sat, 0, 1)
def lum(x, gain=1.15):
    L = x @ np.array([0.0722, 0.7152, 0.2126], np.float32)
    L = L / max(float(np.percentile(L, 99)), 0.2); L = np.clip(L, 0, 1) ** 0.75
    L = np.clip((L - 0.5) * gain + 0.5 + 0.03, 0, 1); return 0.75 * L + 0.25 * (L * L * (3 - 2 * L))
DUO = {"sapin": (SAPIN, CREAM), "cerise": (CHERRY, CREAM), "encre": (INK, CREAM), "mousse": (SAPIN, "#E3EDE2")}
def duotone(x, duo):
    a, b = DUO[duo]; L = lum(x)[..., None]; return hexc(a)[None, None, :] * (1 - L) + hexc(b)[None, None, :] * L
def trame(x, duo, cell=9.0):
    """Photo tramée : points d'encre ronds à 45° (taille selon le gris, trame d'imprimerie visible) + 25 % de ton continu pour garder les visages lisibles."""
    a, b = DUO[duo]; L = lum(x, 1.25); h, w = L.shape
    ink = np.clip(((1 - L) * 1.08 - screen(h, w, cell)) * 3.2 + 0.5, 0, 1)
    ink = 0.75 * ink + 0.25 * (1 - L)
    return hexc(b)[None, None, :] * (1 - ink[..., None]) + hexc(a)[None, None, :] * ink[..., None]
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
STRIP_COLS = [CHERRY, CREAM, SAPIN, MOSS, WHITE, CHERRY, INK, SAPIN]
def strip_rgba(w, h, rng, colhex, ht=False):
    col = hexc(colhex); dot = hexc(SAPIN if colhex in (CREAM, WHITE, MOSS) else (CREAM if colhex != CHERRY else "#E46A86"))
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
    """Photo vivante tramée (encre sapin / cerise sur crème) : bord papier déchiré, scotch aux coins, ombre ; elle saute un peu sur chaque frappe."""
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
        c = trame(cv2.resize(self.frames[i][y0:y1, x0:x1], (self.width, self.h), interpolation=cv2.INTER_AREA), self.duo)
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
RBOX = (200, 20, 1660, 790)           # Rochefort, caméra pupitre : buste entier jusqu'au haut du pupitre (retour Luca : jamais tête + épaules ;
                                      #   bout de micro accepté), bas posé sur le bas du cadre ; filigrane (haut droite) hors fenêtre
RPT = (0.508, 0.30)                   # point sur son visage (instance Vision = elle ; le box s'arrête au-dessus de la poitrine)
WIDE = (0, 200, 1650, 1080)           # salle : filigrane (haut droite) hors cadre photo
HEMI = (0, 120, 1920, 1080)           # hémicycle large (QAG 0-4 s) : logo LCP hors cadre photo
KEYL = ("TAPEZ,", "NOMBRE.", "CIBLEZ,", "COMBAT.")
SHOTS = [
    dict(id="A1", kind="cut", src="RB", t=None, bg=CHERRY, sheet=(CREAM, "bas", 0.80, -4, 1), ghost=SAPIN, box=RBOX, pt=RPT,
         scale=(1.52, 1.56), cx=1000,
         boards=[([ln(0, 1), ln(2, 3)], None), ([ln(4, 5, 6), ln(7, 8), ln(9, 10)], wt(4))], txt_h=158, strips=4,
         photos=[("QAG", 1.0, HEMI, 560, (250, 1250), -6, wt(3), "sapin"), ("RC", 3.0, WIDE, 560, (830, 1160), 5, wt(10), "encre")],
         why="2026 — Rochefort, son direct : « Plus vous nous tapez, plus nous sortons de l'ombre en nombre. », Panot détourée sur fond cerise, double tirage tramé sapin ; l'hémicycle tramé arrive sur TAPEZ, la salle sur NOMBRE"),
    dict(id="A2", kind="cut", src="RB", t=None, bg=SAPIN, sheet=(CHERRY, "haut", 0.11, 3, 2), ghost=CHERRY, box=RBOX, pt=RPT,
         scale=(1.56, 1.59), cx=1000, dx=-110,                # dx : décalage à gauche (visage hors colonne de boutons, zones_tiktok HD à 5,0 s)
         boards=[([ln(11, 12), ln(13, 14), ln(15, 16, 17)], None)], txt_h=158, strips=4,
         photos=[("RB", 34.0, WIDE, 540, (820, 1250), 5, wt(15), "cerise")],
         why="même plan synchro : « Plus vous nous ciblez, plus des gens », fond sapin + feuille cerise déchirée, la salle tramée cerise arrive sur PLUS DES GENS"),
    dict(id="A3", kind="cut", src="RB", t=None, bg=CREAM, sheet=(SAPIN, "bas", 0.83, 5, 3), ghost=CHERRY, box=RBOX, pt=RPT,
         scale=(1.59, 1.62), cx=1000,
         boards=[([ln(18, 19), ln(20)], None), ([ln(21, 22), ln(23, 24)], wt(21))], txt_h=158, strips=5,
         photos=[("RA", 23.0, WIDE, 520, (240, 1050), -6, 0.0, "sapin"), ("RB", 75.0, WIDE, 500, (850, 960), 5, wt(21), "cerise")],
         why="même plan synchro : « viennent nous rejoindre pour mener le combat. » (s'arrête avant le passage régie sur la salle à 108,30 s), salles tramées collées derrière elle"),
    dict(id="B1", kind="collage", bg=CHERRY, sheet=(CREAM, "bas", 0.86, -3, 6),
         photos=[("QAG", 50.6, (300, 40, 1620, 1080), 900, (540, 1140), -3, 0.0, "sapin")],
         rboards=[([[("PLUS", 0.0), ("VOUS", 0.0)], [("NOUS", 0.0), ("TAPEZ,", 0.0)]], 0.0)], txt_y=300, txt_h=150, letters=("TAPEZ,",), strips=3, flash=True,
         why="2025 — QAG à l'Assemblée, elle pointe le banc du gouvernement (sans le son) : grande photo tramée sapin collée sur fond cerise, flash blanc 3 images au drop (pas de découpe : micro et voisines devant elle)"),
    dict(id="B2", kind="collage", bg=SAPIN, sheet=(CREAM, "haut", 0.30, 4, 7),
         photos=[("RB", 5.0, WIDE, 700, (520, 860), -4, 0.0, "cerise"), ("RB", 71.0, WIDE, 640, (600, 1260), 5, 0.5 * TB, "encre"),
                 ("RC", 5.0, WIDE, 600, (420, 1620), -3, TB, "cerise"), ("RA", 25.5, WIDE, 560, (760, 1700), 6, 1.5 * TB, "encre")],
         rboards=[([[("PLUS", 0.0), ("NOUS", 0.0)], [("SORTONS", 0.0), ("DE", 0.0)], [("L'OMBRE", 0.0)], [("EN", TB), ("NOMBRE.", TB)]], 0.0)],
         txt_y=280, letters=("NOMBRE.",), txt_h=128, strips=3,
         why="collage : la salle comble de Rochefort (drapeaux, applaudissements) se colle photo après photo, en trame cerise et encre — en nombre"),
    dict(id="B3", kind="collage", bg=CREAM, sheet=(CHERRY, "bas", 0.78, -5, 8),
         rboards=[([[("PLUS", 0.0), ("VOUS", 0.0)], [("NOUS", 0.0), ("CIBLEZ,", 0.0)]], 0.0)], txt_y=300, txt_h=150, letters=("CIBLEZ,",), strips=3,
         photos=[("QAG", 2.5, HEMI, 520, (790, 1560), 5, 0.0, "sapin"), ("QAG", 54.5, (200, 40, 1700, 1080), 900, (540, 1110), 4, 0.0, "cerise")],
         why="2025 — QAG, bras levé, feuilles à la main (sans le son) : grande photo tramée cerise collée sur crème + feuille cerise, hémicycle tramé sapin (pas de découpe : micro devant elle)"),
    dict(id="B4", kind="cut", src="RB", t=21.0, bg=MOSS, sheet=(SAPIN, "bas", 0.80, 4, 9), ghost=CHERRY, box=RBOX, pt=RPT,
         scale=(1.52, 1.58), cx=990,
         photos=[("RB", 8.0, WIDE, 560, (270, 820), -5, 0.0, "cerise"), ("RA", 22.0, WIDE, 520, (830, 700), 6, 0.5 * TB, "encre"),
                 ("RC", 1.0, WIDE, 500, (300, 1180), 4, TB, "cerise")],
         rboards=[([[("PLUS", 0.0), ("DES", 0.0), ("GENS", 0.0)], [("VIENNENT", 0.0), ("NOUS", 0.0)], [("REJOINDRE", 0.0)]], 0.0)], txt_y=290, txt_h=138, strips=3,
         why="2026 — Rochefort, sourire (sans parole, début de l'intervention) : détourée sur fond mousse, les photos de la salle s'empilent derrière elle (des gens viennent nous rejoindre)"),
    dict(id="B5", kind="sil", src="RA", t=46.0, bg=SAPIN, ghost=CHERRY, box=(440, 0, 1600, 800), pt=(0.509, 0.33), dest_w=1800, cx=1000, push=(1.0, 1.04),
         sheet=(CHERRY, "haut", 0.12, -3, 10),
         rboards=[([[("POUR", 0.0), ("MENER", 0.0)], [("LE", 0.0), ("COMBAT.", 0.0)]], 0.0)], txt_y=300, txt_h=150, letters=("COMBAT.",), strips=3,
         why="2026 — Rochefort, autre moment (buste), regard déterminé (sans parole) : silhouette blanche 3 images puis Panot en couleur sur fond sapin"),
    dict(id="FIN", kind="card", bg=CREAM, sheet=(SAPIN, "bas", 0.84, -4, 11), strips=3,
         cboard=[[("MATHILDE", 0.0)], [("PANOT", FINP)]], txt_y=600, txt_h=380, seq=0.035,
         why="carton final ransom-note (comme lot6 R4 v2) : MATHILDE lettre par lettre sur la coupe, PANOT sur la frappe suivante, lettres découpées "
             "serif/sans étroites, penchées, tramées, scotch aux bouts des lignes, pleine largeur de la zone sûre ; 1,5 s"),
]
BOUNDS_T = [0] + CUTF + [fr(END)]
assert len(BOUNDS_T) == len(SHOTS) + 1, (len(BOUNDS_T), len(SHOTS))
for i, sh in enumerate(SHOTS):
    sh["a"], sh["bb"] = BOUNDS_T[i], BOUNDS_T[i + 1]; sh["n"] = sh["bb"] - sh["a"]; sh["clip"] = "R15_%s.mov" % sh["id"]
    if sh.get("src") == "RB" and sh["t"] is None: sh["t"] = V_SRC0 + sh["a"] / FPS           # plans A synchro avec la voix
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
    elif sh.get("cboard"):                                                 # carton final : lettres découpées pleine largeur
        p = board(sh["cboard"], sh["txt_y"], seed, h=sh["txt_h"], letters=("MATHILDE", "PANOT"), seq=sh["seq"], tape=False, narrow=True,
                  maxw=0.65 * W - 10, xmin=0.175 * W, xmax=0.825 * W)       # pleine largeur de la zone sûre (0,17-0,83)
        boards.append(([(im, cx, cy, rel(t)) for im, cx, cy, t in p], a))
    elif sh.get("txt"):
        p = board(sh["txt"], sh["txt_y"], seed, h=sh.get("txt_h", 130), letters=sh.get("letters", ()), seq=sh.get("seq", 0.0))
        boards.append(([(im, cx, cy, rel(t)) for im, cx, cy, t in p], a))
    big = []
    if sh.get("big"):
        big = [(im, cx, cy, rel(t)) for im, cx, cy, t in big_text(sh["big"], sh["big_y"], (S + "Didot.ttc", 2), (XMAX - XMIN) * 0.92, sh["big_sizes"])]
    photos = [Photo(read_frames(ps, pt, n), pbox, pw, pc, pa, fr(rel(pt0)) if pt0 > 0 or sh["id"].startswith("B") else a, (sh["id"], j), duo)
              for j, (ps, pt, pbox, pw, pc, pa, pt0, duo) in enumerate(sh.get("photos", []))]
    if sh["id"].startswith("A"):                                             # plans A : apparition au temps absolu du mot
        for ph, spec in zip(photos, sh.get("photos", [])): ph.f0 = max(a, fr(spec[6])) if spec[6] > 0 else a
    strips = make_strips(sh)
    k0 = nbeat(a)
    if sh["kind"] in ("cut", "sil"):
        raw = read_frames(sh["src"], sh["t"], n)
        ms = masks("%s_%s_%.2f_%d_%s" % (sh["id"], sh["src"], sh["t"], n, "-".join(map(str, sh["box"]))), raw, sh["box"], sh["pt"], sh["id"])
        sh["cx"] = auto_cx(ms, sh["box"])                                    # tête au centre du cadre
        if sh.get("bottom", H) < H:                                         # buste posé plus haut que le bas du cadre (visage hors interface TikTok) :
            ms = [bas_dechire(m, seed=skey(sh["id"])) for m in ms]           #   bord bas en papier déchiré (même déchirure sur tout le plan)
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
                ccx = W / 2 + ((x1 - x0) / 2 - (sh["cx"] - x0)) * sc + sh.get("dx", 0); ccy = sh.get("bottom", H) - hh / 2; r_ = 7
            else:
                z = sh["push"][0] + (sh["push"][1] - sh["push"][0]) * u
                sc = sh["dest_w"] / (x1 - x0) * z; hh = (y1 - y0) * sc
                ccx = W / 2 + ((x1 - x0) / 2 - (sh["cx"] - x0)) * sc; ccy = sh.get("bottom", H) - hh / 2; r_ = 9
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
            lines = {}                                                      # scotch aux deux bouts de chaque ligne de lettres
            for im, cx, cy, t in boards[0][0]: lines.setdefault(round(cy / 40), []).append((cx - im.shape[1] / 2, cx + im.shape[1] / 2, cy, t))
            for j, (_, ps) in enumerate(sorted(lines.items())):
                t_last = max(p[3] for p in ps)
                if f < fr(t_last): continue
                xl, xr, cy = min(p[0] for p in ps), max(p[1] for p in ps), sum(p[2] for p in ps) / len(ps)
                paste(img, CARD_TAPES[2 * j % 4], xl + 6, cy, 0.6, 70 + 8 * j); paste(img, CARD_TAPES[(2 * j + 1) % 4], xr - 6, cy, 0.6, -70 - 8 * j)
        if sh.get("flash") and i < 3: img = img + (1 - img) * [1.0, 0.6, 0.25][i]       # flash blanc 3 images (drop)
        if sh.get("flash2") and i < 2: img = img + (1 - img) * [0.7, 0.3][i]
        frames.append(finish(img, f))
    write_mov(frames, OUT + sh["clip"])
    print("  %-4s %3d im  (%s)" % (sh["id"], n, sh["kind"]), flush=True)

# ---------------- audio ----------------
def make_audio():
    import soundfile as sf, scipy.signal as ss
    sr = 48000; N = int(round(END * sr))
    def grab(path, t, dur):
        p = subprocess.run([FF, "-v", "error", "-ss", "%.3f" % t, "-t", "%.3f" % dur, "-i", path, "-ac", "2", "-ar", str(sr), "-f", "f32le", "-"], capture_output=True)
        return np.frombuffer(p.stdout, np.float32).reshape(-1, 2).copy()
    voix = np.zeros((N, 2), np.float32); mus = np.zeros((N, 2), np.float32)
    v = grab(HG + "/" + SRC["RB"][0], V_IN, V_OUT - V_IN); env = np.ones(len(v), np.float32)      # son direct synchro des plans A1-A3
    k = int(0.03 * sr); env[:k] = np.linspace(0, 1, k); k = int(0.08 * sr); env[-k:] = np.linspace(1, 0, k)
    i0 = int(round(t_of_src(V_IN) * sr)); voix[i0:i0 + len(v)] = v * env[:, None] * 10 ** (VGAIN / 20)
    m = music_raw(MUSIC_IN)[:N]
    t = np.arange(len(m)) / sr; vend = t_of_src(V_OUT); dr = CUTS[2]
    # sous la phrase : fin du pré-refrain filtrée (passe-bas 1,8 kHz : garde le clic du kick) et baissée, le filtre s'ouvre et le niveau monte, plein au drop (refrain)
    lp = ss.sosfiltfilt(ss.butter(2, 1800, "lp", fs=sr, output="sos"), m, axis=0).astype(np.float32)
    wo = np.interp(t, [0, vend - 1.2, dr - 0.6, dr - 0.03, dr], [0, 0.15, 0.55, 0.8, 1.0])[:, None]
    m = lp * (1 - wo) + m * wo
    gdb = np.interp(t, [0, 0.25, 4.0, vend - 0.6, dr - 0.03, dr, END], [-20, -17, -16, -11, -7, 0, 0])
    k = int(0.40 * sr); fo = np.ones(len(m), np.float32); fo[-k:] = np.linspace(1, 0, k)
    mus[:len(m)] = m * (10 ** (gdb / 20) * fo)[:, None]
    sf.write(OUT + "R15-voix.wav", voix, sr, subtype="PCM_24"); sf.write(OUT + "R15-musique.wav", mus, sr, subtype="PCM_24")
    sf.write(D + "tmp_mix.wav", voix + mus, sr, subtype="FLOAT")
    r = subprocess.run([FF, "-hide_banner", "-i", D + "tmp_mix.wav", "-af", "loudnorm=I=-14:TP=-2.5:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    js = json.loads(r[r.rindex("{"):r.rindex("}") + 1])
    af = ("loudnorm=I=-14:TP=-2.5:LRA=11:measured_I=%s:measured_TP=%s:measured_LRA=%s:measured_thresh=%s:offset=%s:linear=true,"
          "aresample=48000" % (js["input_i"], js["input_tp"], js["input_lra"], js["input_thresh"], js["target_offset"]))
    subprocess.run([FF, "-v", "error", "-y", "-i", D + "tmp_mix.wav", "-af", af, "-c:a", "pcm_s24le", OUT + "R15-mix.wav"], check=True)
    os.remove(D + "tmp_mix.wav"); print("audio : mix avant normalisation", js["input_i"], "LUFS")
VGAIN = 4.0

# ---------------- plan ----------------
def build_plan():
    video = []
    for sh in SHOTS:
        v = {"id": sh["id"], "clip": sh["clip"], "folder": "genR15", "path": OUT + sh["clip"], "s": 0, "e": sh["n"], "rec": sh["a"], "dur": sh["n"],
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
    PHR = ("Plus vous nous tapez, plus nous sortons de l'ombre en nombre. "
           "Plus vous nous ciblez, plus des gens viennent nous rejoindre pour mener le combat.")
    off = SRC["RB"][3]
    plan = {"name": "R15 - Collage ransom-note pop chic - Mathilde Panot", "fps": FPS, "w": W, "h": H, "duree_s": END,
            "note": "Plans ProRes 9:16 composés en Python (lot7/_claude/gen/R15/out) : fonds papier froissé + feuille déchirée, Panot détourée seule "
                    "(instance Vision, tools/inst), double tirage tramé, silhouettes blanches 3 images, photos vivantes en trame d'imprimerie "
                    "(cerise / sapin / encre sur crème), bandes tramées, scotch, textes ransom-note cuits. s/e en images du clip (30 i/s), rec en "
                    "images timeline. Coupes sur les frappes réelles d'Espresso (out/R15-frappes.json). Aucun ralenti. Générateur : lot7/_claude/gen/R15/genR15.py",
            "phrase": {"texte": PHR, "url": URL_R, "source": SRC["RB"][0], "in_s": 100.04, "out_s": 107.84,
                       "youtube_s": [round(off + 100.04, 2), round(off + 107.84, 2)],
                       "timeline_s": [round(t_of_src(100.04), 2), round(t_of_src(107.84), 2)],
                       "contexte": CTX_R, "voix": "son direct synchro (plans A1-A3, même source, même moment)"},
            "musique": {"fichier": "lot7/sons/R15-sabrina-espresso_complet.wav", "titre": "Sabrina Carpenter - Espresso", "url": SON_URL,
                        "debut_complet_s": round(MUSIC_IN, 4), "fin_complet_s": round(MUSIC_IN + END, 3), "drop_timeline_s": CUTS[2],
                        "coupes_frappes_s": CUTS, "coupes_images": CUTF},
            "textes": texts, "video": video,
            "audio": [{"id": "mix", "clip": "R15-mix.wav", "folder": "genR15", "path": OUT + "R15-mix.wav", "rec": 0, "track": 1,
                       "note": "mix -14 LUFS : voix Rochefort %.2f-%.2f s (+%.0f dB) à %.2f s ; Espresso dès %.3f s du complet, fin du pré-refrain "
                               "filtrée et baissée sous la voix, le filtre s'ouvre (montée), plein au drop (refrain), fondu de fin 0,4 s"
                               % (V_IN, V_OUT, VGAIN, t_of_src(V_IN), MUSIC_IN)}],
            "stems": ["lot7/_claude/gen/R15/out/R15-voix.wav", "lot7/_claude/gen/R15/out/R15-musique.wav"],
            "logos_exclus": "Rochefort : filigrane MELENCHON2027.fr (haut droite) et pupitre ROCHEFORT hors des fenêtres (détourage, cadres photo) ; "
                            "QAG : logo LCP hors cadre (détourage, hémicycle recadré)"}
    json.dump(plan, open(D + "plan-R15.json", "w"), indent=1, ensure_ascii=False)
    son = {"id": "R15", "titre": "Espresso", "artiste": "Sabrina Carpenter", "url": SON_URL,
           "chaine": "Sabrina Carpenter (officielle)",
           "fichier": "lot7/sons/R15-sabrina-espresso_complet.wav",
           "extrait_complet_s": {"debut": round(MUSIC_IN, 4), "fin": round(MUSIC_IN + END, 3)},
           "passages": "sous la phrase (filtré, baissé) : fin du pré-refrain, complet %.2f-%.2f s ; au drop : 2e refrain, complet %.2f-%.2f s "
                       "(paroles non recopiées, consigne Luca)" % (MUSIC_IN, MUSIC_IN + CUTS[2], MUSIC_IN + CUTS[2], MUSIC_IN + END),
           "bpm": 104.0, "temps_s": T,
           "drop": {"complet_s": round(MUSIC_IN + CUTS[2], 4), "timeline_s": CUTS[2], "nature": "1er temps du 2e refrain, après le pré-refrain"},
           "frappes_timeline_s": [round(k, 4) for k in KICKS], "coupes_sur_frappes_s": CUTS,
           "mix": "lot7/_claude/gen/R15/out/R15-mix.wav"}
    json.dump(son, open(D + "son.json", "w"), indent=1, ensure_ascii=False)
# ---------------- aperçu 540x960 ----------------
def apercu():
    plan = json.load(open(D + "plan-R15.json")); ins = []; fl = []
    for i, v in enumerate(plan["video"]):
        ins += ["-i", OUT + v["clip"]]
        fl.append("[%d:v]trim=start_frame=%d:end_frame=%d,setpts=PTS-STARTPTS,scale=540:960,setsar=1[v%d]" % (i, v["s"], v["e"], i))
    k = len(plan["video"]); fl.append("".join("[v%d]" % i for i in range(k)) + "concat=n=%d:v=1:a=0[v]" % k)
    ins += ["-i", OUT + "R15-mix.wav"]; out = HG + "/preview/apercu-R15.mp4"
    subprocess.run([FF, "-v", "error", "-y"] + ins + ["-filter_complex", ";".join(fl), "-map", "[v]", "-map", "%d:a" % k,
                    "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "aac", "-b:a", "192k", "-shortest", out], check=True)
    print("aperçu", out)
# ---------------- mesure sur l'export : coupes vs frappes, LUFS / TP ----------------
def mesure():
    out = HG + "/preview/apercu-R15.mp4"
    r = subprocess.run([FF, "-v", "info", "-i", out, "-vf", "scale=135:240,select='gt(scene,0.2)',showinfo", "-an", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    cuts = [float(x) for x in re.findall(r"pts_time:([0-9.]+)", r)]
    p = subprocess.run([FF, "-v", "error", "-i", out, "-vn", "-ac", "2", "-ar", "48000", "-f", "f32le", "-"], capture_output=True)
    y = np.frombuffer(p.stdout, np.float32).reshape(-1, 2)
    hh = detect_hits(y); hh0 = detect_hits(y[:int((CUTS[2] - 0.05) * 48000)])   # avant le drop : frappes cherchées sur ce passage seul (sinon écrasées par le refrain)
    worst = 0
    for i, c in enumerate([fr_ / FPS for fr_ in CUTF]):
        det = min(cuts, key=lambda x: abs(x - c)) if cuts else None
        pool = [x[0] for x in hh if (x[1] == "kick" and x[3] > 0.03)] if i >= 2 else [x[0] for x in hh0 if x[1] == "kick"]
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
