# R7 (lot 7) — Collage ransom-note « foule d'été, pancartes brandies », Jean-Luc Mélenchon, son Gala – Freed from Desire (audio officiel).
# Modèle : lot6/_claude/gen/R6/genR6.py (validé), lui-même tiré de lot5 R1 ; recette inspis/2026-10-26 abdulelsayed.
# Poussé : mots de la phrase collés sur des PANCARTES (carton + manche) qui sont brandies (sautent et penchent sur chaque frappe),
#   foule d'été de la Fête de l'Huma en photos (couleur chaude, bichromies coquelicot / rose) bord déchiré + scotch, coquelicots en
#   papier découpé qui poussent sur les frappes, découpe Vision de Mélenchon (instance) + double tirage tramé + contour autocollant,
#   fonds papier froissé + feuille déchirée, flash blanc 3 images seulement au drop.
# Palette R7 (brief) : rouge coquelicot, rose bonbon, rose poudré, blanc, encre (cœur de coquelicot). Aucune couleur de R1-R6 en dominante.
# Phrase (son direct) : « Gouverner sans compter sur les fadaises magiques de la main invisible du marché et autres stupidités métaphysiques. »
#   (Fête de l'Humanité 12/09/2026, chaîne JEAN-LUC MÉLENCHON, youtu.be/80bBtk2lTiI 4771,86-4779,18 s
#   = lot1/sources/3-melenchon-huma-citation.mp4 61,86-69,18 s) ; « c'est-à-dire » (61,34-61,78) non gardé.
#   -> autre phrase que lot1 #3 (citation 85-95 s, « perdu d'avance » 119 s), W1 (« Qu'ils s'en aillent tous », 102 s), M1 (« nous sommes prêts », 186-192 s).
#   Plans : synchro 63,43-68,85 s (la tête baissée sur les notes après 68,9 s est couverte par la foule) (R3 avait pris 62,4-63,37 s : couvert ici par la foule pendant « Gouverner sans compter »),
#   autres moments jamais pris : 152 s, 124 s, 33 s ; foule 141, 209, 215, 225, 228, 246, 257, 259, 264, 279 s.
# Son : Freed from Desire, extrait continu ; sous la phrase, refrain sans kick « Freed from desire, mind and senses purified » baissé qui
#   monte ; drop = entrée du kick sur le « Na na na » (59,91 s du morceau), coupes toutes les 4 temps sur les kicks réels (129 BPM ; le 16e temps sans kick est sauté).
# Textes après le drop : un groupe complet par plan, dans l'ordre : GOUVERNER. / SANS COMPTER SUR LES FADAISES MAGIQUES /
#   LA MAIN INVISIBLE DU MARCHÉ / ET AUTRES STUPIDITÉS MÉTAPHYSIQUES. puis carton final JEAN-LUC MÉLENCHON + 2027.
# Usage : python genR7.py [shots] [audio] [plan] [apercu] [mesure] [only=ID,ID]   (sans argument = tout sauf mesure)
import sys
sys.dont_write_bytecode = True
import os, json, subprocess, math, re
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
HG = "/Users/luca.grousset/Movies/highkey-gauchiste"
D = HG + "/lot7/_claude/gen/R7/"; OUT = D + "out/"; CACHE = D + "cache/"; os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, D)
from hits import detect_hits
FF = "/opt/homebrew/bin/ffmpeg"; INST = D + "tools/inst"; FPS = 30; W, H = 1080, 1920
def fr(t): return int(round(t * FPS))
def hexc(h): h = h.lstrip("#"); return np.array([int(h[4:6], 16), int(h[2:4], 16), int(h[0:2], 16)], np.float32) / 255   # BGR
def rgb(h): h = h.lstrip("#"); return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
# palette R7 : coquelicot, rose bonbon, rose poudré, blanc, papier rosé, encre
POPPY, PINK, BLUSH, WHITE, PAPER, INK = "#EE2A1B", "#FF6FA8", "#FFD2E1", "#FFFFFF", "#FBF1F2", "#1C0B10"
WOOD = "#E3B98A"

# ---------------- source (lecture seule, lot 1) ----------------
SRC = {
    "HU": ("lot1/sources/3-melenchon-huma-citation.mp4", 50.0, "https://www.youtube.com/watch?v=80bBtk2lTiI", 4710.0,
           "Fête de l'Humanité, 12/09/2026 (chaîne JEAN-LUC MÉLENCHON), extrait 4710-5010 s"),
}

# ---------------- musique : Gala – Freed from Desire ----------------
SON_FILE = HG + "/lot7/sons/R7-gala-freed-from-desire_complet.wav"; SON_URL = "https://www.youtube.com/watch?v=Qvu033SBMYU"
MDROP = 59.9104                      # entrée du kick sur le « Na na na »
DROP = 8.21; T = 0.4650              # 129 BPM (kicks 59,910 -> 71,533)
MUSIC_IN0 = MDROP - DROP
PRE = [53.5725, 56.6085, 58.0490, 58.9856]    # frappes réelles du refrain sans kick (hits.py) -> 3 coupes sous la voix
STEPS = [4, 4, 4, 5, 2]              # après le drop : plans de 4 temps (5 pour le plus long carton : pas de kick au 16e temps), puis 2 temps
END = DROP + (sum(STEPS) + 5) * T    # carton final 5 temps
DI = len(PRE)                        # indice de la coupe du drop
CUT_T = [b - MUSIC_IN0 for b in PRE] + [DROP]
for s_ in STEPS: CUT_T.append(CUT_T[-1] + s_ * T)
HITS_JSON = OUT + "R7-frappes.json"
def music_raw(mi, dur=None, sr=48000):
    import soundfile as sf
    dur = dur or END + 0.5
    i0 = int(round(mi * sr)); x, r = sf.read(SON_FILE, start=i0, frames=int(dur * sr), dtype="float32"); assert r == sr; return x
def hits_all(mi):
    """Frappes de l'extrait + frappes du refrain sans kick détectées sur ce passage seul (sinon écrasées par la normalisation)."""
    h = detect_hits(music_raw(mi)); pre = detect_hits(music_raw(mi, dur=DROP - 0.25))
    return sorted([x for x in h if x[0] >= DROP - 0.25] + pre)
def kicks_of(h): return [x[0] for x in h if x[1] == "kick" and x[3] > 0.12]
def snap_list(h, targets):
    ks, al = kicks_of(h), [x[0] for x in h]; out = []
    for i, t in enumerate(targets):
        if i > DI: t = out[-1] + STEPS[i - DI - 1] * T                   # après le drop : n temps après la coupe précédente réelle
        pool = al if i < DI else ks
        c = min(pool, key=lambda k: abs(k - t)); assert abs(c - t) < 0.04, ("pas de frappe près de", t, c); out.append(c)
    return out
def frappes():
    if os.path.exists(HITS_JSON):
        js = json.load(open(HITS_JSON))
        if js["cle"] == [MUSIC_IN0, END, CUT_T]: return js["music_in"], js["frappes"]
    best, bad = None, 9
    for off in np.arange(-0.016, 0.0165, 0.001):
        h = hits_all(MUSIC_IN0 + off)
        try: cuts = snap_list(h, CUT_T)
        except AssertionError: continue                                   # frappe non détectée à ce décalage
        e = max(abs(c - round(c * FPS) / FPS) for c in cuts)
        if e < bad: best, bad, hb = off, e, h
    mi = MUSIC_IN0 + best
    json.dump({"cle": [MUSIC_IN0, END, CUT_T], "music_in": mi, "frappes": hb}, open(HITS_JSON, "w")); return mi, hb
MUSIC_IN, HITS = frappes()
FINE = -0.012                         # recalage fin mesuré sur l'export AAC (voix + musique) : écart max coupes/frappes minimal
MUSIC_IN += FINE; HITS = [[h[0] - FINE] + list(h[1:]) for h in HITS]
KICKS = kicks_of(HITS)
CUTS = snap_list(HITS, CUT_T); CUTF = [fr(c) for c in CUTS]
DROPF = CUTF[DI]; TB = T

# ---------------- voix ----------------
V_SRC0 = 61.56                        # source Huma à t = 0 (« gouverner » 61,86 -> 0,30 s ; « métaphysiques » fin 69,18 -> 7,62 s)
V_IN, V_OUT = 61.80, 69.50            # après « c'est-à-dire » (fin 61,76) … « métaphysiques. » + début de l'ovation, fondu avant le drop
def t_of_src(s): return s - V_SRC0
WORDS = [("GOUVERNER", 61.86), ("SANS", 62.38), ("COMPTER", 62.92), ("SUR", 63.60), ("LES", 64.08), ("FADAISES", 64.28),
         ("MAGIQUES", 64.98), ("DE", 65.46), ("LA", 65.86), ("MAIN", 66.00), ("INVISIBLE", 66.16), ("DU", 66.54), ("MARCHÉ", 66.70),
         ("ET", 67.08), ("AUTRES", 67.52), ("STUPIDITÉS", 67.76), ("MÉTAPHYSIQUES", 68.46)]
def wt(i): return t_of_src(WORDS[i][1])
def ln(*idx): return [(WORDS[i][0], wt(i)) for i in idx]

# ---------------- polices ransom-note ----------------
S = "/System/Library/Fonts/Supplemental/"
FONTS = [(S + "Arial Black.ttf", 0), (S + "Georgia Bold.ttf", 0), (S + "Times New Roman Bold.ttf", 0), (S + "Impact.ttf", 0),
         (S + "Courier New Bold.ttf", 0), (S + "Rockwell.ttc", 2), (S + "AmericanTypewriter.ttc", 2), (S + "Didot.ttc", 2),
         (S + "Bodoni 72.ttc", 2), (S + "Futura.ttc", 2)]
STYLES = [(rgb(PAPER), rgb(INK)), (rgb(POPPY), (255, 255, 255)), (rgb(PINK), rgb(INK)), (rgb(INK), rgb(PINK)),
          ((255, 255, 255), rgb(POPPY)), (rgb(BLUSH), rgb(POPPY)), (rgb(INK), (255, 255, 255)), (rgb(POPPY), rgb(INK))]
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
sys.path.insert(0, HG + "/_claude/outils")
from decoupe import masques as dec_masques, controle as dec_controle, planche as dec_planche
CTRL = {}
def masks(key, frames, box, pt, k=13):
    """Découpe propre de Mélenchon seul (outil partagé _claude/outils/decoupe.py : instance Vision x segmentation personne, sans
    pupitre ni micro). Le bas du box est remonté à la dernière ligne du buste (haut du pupitre) : ce bord est posé sur le bas du cadre."""
    ms = dec_masques(frames, box, pt, CACHE + "dec/" + key)
    x0, y0, x1, y1 = box; ell = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (29, 29))
    for i, m in enumerate(ms):                      # en plus : pied / tête de micro qui dépasse du corps (sombre et plus fin que 29 px) retiré
        b = (m > 0.5).astype(np.uint8); L = frames[i][y0:y1, x0:x1] @ np.array([0.0722, 0.7152, 0.2126], np.float32)
        thin = ((b > 0) & (cv2.morphologyEx(b, cv2.MORPH_OPEN, ell) == 0) & (L < 0.25)).astype(np.uint8)
        if thin.any():
            keep = 1 - cv2.dilate(thin, np.ones((7, 7), np.uint8)); b2 = b & keep
            n_, lab, st, _ = cv2.connectedComponentsWithStats(b2, 8)
            if n_ > 1: b2 = (lab == 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))).astype(np.uint8)
            ms[i] = m * cv2.GaussianBlur(b2.astype(np.float32), (0, 0), 1.0)
    yb = min(int(np.where((m > 0.5).any(1))[0][-1]) for m in ms)
    x0, y0, x1, y1 = box; bx = (x0, y0, x1, y0 + yb + 1); ms = [m[:yb + 1] for m in ms]
    cs = [dec_controle(m) for m in ms]
    CTRL[key] = {c: max(x[c] for x in cs) for c in ("gauche", "droite", "haut", "morceaux", "bas_net")} | {"bas_min": min(x["bas"] for x in cs), "box": bx}
    os.makedirs(D + "planches", exist_ok=True); dec_planche(frames, ms, bx, D + "planches/%s.jpg" % key.split("_")[0], n=6)
    print("   découpe", key, CTRL[key], flush=True)
    return ms, bx
def grade(x, sat=1.10):
    x = 0.82 * x + 0.18 * (x * x * (3 - 2 * x))
    L = x @ np.array([0.0722, 0.7152, 0.2126], np.float32)
    return np.clip(L[..., None] + (x - L[..., None]) * sat, 0, 1)
def lum(x, gain=1.15):
    L = x @ np.array([0.0722, 0.7152, 0.2126], np.float32)
    L = L / max(float(np.percentile(L, 99)), 0.2); L = np.clip(L, 0, 1) ** 0.75
    L = np.clip((L - 0.5) * gain + 0.5 + 0.03, 0, 1); return 0.75 * L + 0.25 * (L * L * (3 - 2 * L))
DUO = {"coq": ("#2A060B", "#FF5A3F"), "rose": ("#B3123C", "#FFC6D8"), "encre": (INK, BLUSH)}
def duotone(x, duo):
    if duo == "couleur":                                                  # tirage couleur chaud d'été
        c = grade(x, 1.18); return np.clip(c * np.array([0.92, 0.99, 1.08], np.float32) + 0.02, 0, 1)
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
def strip_rgba(w, h, rng, colhex, ht=False):
    col = hexc(colhex); dot = hexc(INK if colhex in (PINK, WHITE, BLUSH, PAPER) else PINK)
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
    """Photo vivante (couleur chaude ou bichromie coquelicot / rose) : bord papier déchiré, scotch aux coins, ombre ; elle saute un peu sur chaque frappe."""
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
    g = [k for k in KICKS if k >= CUTS[DI] - 0.05]; t = CUTS[DI] - T
    while t > 0: g.append(t); t -= T
    return sorted(g)
BEATS = beat_grid(); BEATF = [fr(b) for b in BEATS]
def nbeat(f): return sum(1 for b in BEATF if b <= f)
def jit(key, k, amp=8.0, ang=1.5):
    r = np.random.default_rng(skey(key) * 1000 + k); return r.uniform(-amp, amp), r.uniform(-amp, amp), r.uniform(-ang, ang)

# ---------------- coquelicots en papier, bandes ----------------
def poppy_rgba(r, rng):
    """Coquelicot en papier découpé : 4 pétales coquelicot (plis plus sombres), cœur encre et étamines, ombre portée."""
    s = int(r * 2.6); c = s // 2; img = np.zeros((s, s, 3), np.float32); a = np.zeros((s, s), np.float32)
    base = hexc(POPPY); dark = base * 0.72
    a0 = rng.uniform(0, 90)
    for k in range(4):
        ang = math.radians(a0 + 90 * k + rng.uniform(-12, 12)); d = r * 0.48
        px, py = int(c + d * math.cos(ang)), int(c + d * math.sin(ang))
        m = np.zeros((s, s), np.float32); cv2.ellipse(m, (px, py), (int(r * 0.62), int(r * 0.55)), math.degrees(ang), 0, 360, 1.0, -1, cv2.LINE_AA)
        shade = 1 - 0.18 * (k % 2)
        img = img * (1 - m[..., None]) + (base * shade)[None, None, :] * m[..., None]; a = np.maximum(a, m)
        cv2.line(img, (c, c), (px, py), tuple(float(v) for v in dark), 2, cv2.LINE_AA)
    cv2.circle(img, (c, c), int(r * 0.22), tuple(float(v) for v in hexc(INK)), -1, cv2.LINE_AA)
    for k in range(10):
        ang = 2 * math.pi * k / 10; cv2.circle(img, (int(c + r * 0.33 * math.cos(ang)), int(c + r * 0.33 * math.sin(ang))), max(2, r // 22),
                                                tuple(float(v) for v in hexc(INK)), -1, cv2.LINE_AA)
    img = np.clip(img * (1 + 0.05 * cv2.GaussianBlur(rng.standard_normal((s, s)).astype(np.float32), (0, 0), 2))[..., None], 0, 1)
    out = np.zeros((s + 14, s + 14, 4), np.float32)
    out[10:10 + s, 8:8 + s, 3] = cv2.GaussianBlur(a, (0, 0), 3) * 0.45
    out[:s, :s, :3] = img * a[..., None]; out[:s, :s, 3] = np.maximum(a, out[:s, :s, 3])
    return out
STRIP_COLS = [PINK, WHITE, POPPY, BLUSH, INK, PAPER, PINK, POPPY]
def make_strips(sh):
    """Bandes de papier déchiré + coquelicots : une couche de plus à chaque temps."""
    n = sh.get("strips", 0); rng = np.random.default_rng(skey(sh["id"]) + 5); out = []
    zones = [(150, 480), (930, 560), (120, 1250), (960, 1300), (540, 300), (540, 1700), (230, 900), (880, 1050), (300, 1600), (820, 1750)]
    for k in range(n):
        w, h = int(rng.uniform(380, 660)), int(rng.uniform(80, 150))
        colhex = STRIP_COLS[(k + skey(sh["id"])) % len(STRIP_COLS)]
        if colhex in (sh.get("bg"), (sh.get("sheet") or (None,))[0]): colhex = STRIP_COLS[(k + 3) % len(STRIP_COLS)]
        cx, cy = zones[(k * 3 + skey(sh["id"])) % len(zones)]
        out.append(dict(img=strip_rgba(w, h, rng, colhex, ht=(k % 3 == 1)), cx=cx + rng.uniform(-60, 60), cy=cy + rng.uniform(-60, 60),
                        ang=rng.uniform(-28, 28), k=k))
    pz = [(110, 330), (980, 420), (90, 1500), (990, 1620), (170, 1830), (930, 1850), (60, 900), (1030, 1100)]
    for j in range(sh.get("poppies", 0)):
        x, y = pz[(j * 5 + skey(sh["id"])) % len(pz)]
        out.append(dict(img=poppy_rgba(int(rng.uniform(70, 120)), rng), cx=x + rng.uniform(-30, 30), cy=y + rng.uniform(-30, 30),
                        ang=rng.uniform(0, 360), k=j + (1 if n else 0)))
    return out

# ---------------- pancartes brandies ----------------
_plc = {}
def placard(pieces, key, colhex):
    """Pancarte en carton peint (bords irréguliers, ombre, scotch) + manche en bois qui descend hors cadre, taillée sur les morceaux de texte.
    Renvoie (rgba, cx, cy) ; le manche est dans la même image (posé derrière la découpe)."""
    if key in _plc: return _plc[key]
    rng = np.random.default_rng(skey(key))
    x0 = min(cx - im.shape[1] / 2 for im, cx, cy, t in pieces) - 34; x1 = max(cx + im.shape[1] / 2 for im, cx, cy, t in pieces) + 34
    y0 = min(cy - im.shape[0] / 2 for im, cx, cy, t in pieces) - 30; y1 = max(cy + im.shape[0] / 2 for im, cx, cy, t in pieces) + 30
    pw, ph = int(x1 - x0), int(y1 - y0); stick_h = int(H - y1 + 260); sw = 40
    tw, th = pw + 40, ph + stick_h + 40
    out = np.zeros((th, tw, 4), np.float32)
    # manche
    st = np.zeros((th, tw), np.float32); sx = tw // 2 + int(rng.uniform(-30, 30)); cv2.rectangle(st, (sx - sw // 2, 20 + ph - 20), (sx + sw // 2, th), 1.0, -1)
    wood = hexc(WOOD)[None, None, :] * (1 + 0.10 * cv2.GaussianBlur(rng.standard_normal((th, tw)).astype(np.float32), (0, 0), sigmaX=1.0, sigmaY=14))[..., None]
    sh_ = cv2.GaussianBlur(np.roll(np.roll(st, 10, 0), 8, 1), (0, 0), 5) * 0.45
    out[..., 3] = sh_; out[..., :3] = wood * st[..., None]; out[..., 3] = np.maximum(out[..., 3], st)
    # carton
    m = torn_mask(ph, pw, rng, rough=5, step=16, inset=4)
    body = paper(colhex)[:ph, :pw] if ph <= H and pw <= W else np.ones((ph, pw, 3), np.float32) * hexc(colhex)
    edge = cv2.GaussianBlur(m, (0, 0), 1.0) - cv2.GaussianBlur(cv2.erode(m, np.ones((9, 9), np.uint8)), (0, 0), 2.0)
    body = body * (1 - 0.25 * np.clip(edge, 0, 1)[..., None])
    psh = np.zeros((th, tw), np.float32); psh[20 + 12:20 + 12 + ph, 20 + 10:20 + 10 + pw] = m; psh = cv2.GaussianBlur(psh, (0, 0), 6) * 0.5
    reg = out[20:20 + ph, 20:20 + pw]
    a = np.maximum(out[..., 3], psh); out[..., 3] = a
    reg[..., :3] = reg[..., :3] * (1 - m[..., None]) + body * m[..., None]; reg[..., 3] = np.maximum(reg[..., 3], m)
    for (tx, ty) in ((20 + int(rng.uniform(0, 30)), 6), (20 + pw - int(rng.uniform(110, 150)), 6)):
        over(out, rot_rgba(tape_rgba(int(rng.uniform(110, 150)), 36, rng), rng.uniform(-20, 20)), tx, ty)
    res = (out, x0 - 20 + tw / 2, y0 - 20 + th / 2); _plc[key] = res; return res
def brandish(f, key):
    """Pancarte brandie : saute vers le haut sur chaque frappe puis retombe, penche d'un côté puis de l'autre."""
    k = nbeat(f); fb = BEATF[k - 1] if k > 0 else 0; u = min(1.0, (f - fb) / 7.0)
    dy = -16 * (1 - u) ** 2; r = np.random.default_rng(skey(key) * 100 + k); ang = (1.0 if k % 2 else -1.0) + r.uniform(-0.2, 0.2)
    return r.uniform(-4, 4), dy, ang
def rot_pt(x, y, cx, cy, ang):
    a = math.radians(-ang); dx, dy = x - cx, y - cy
    return cx + dx * math.cos(a) - dy * math.sin(a), cy + dx * math.sin(a) + dy * math.cos(a)

# ---------------- plans ----------------
HBOX = (400, 40, 1580, 815)            # Huma, gros plan pupitre : pupitre écrit (FÊTE DE L'HUMA, MELENCHON2027.fr, y > 815) hors fenêtre
HPT = (0.51, 0.72)                     # point sur sa poitrine
C_225 = (240, 300, 1680, 1080); C_257 = (200, 430, 1720, 1080); C_141 = (0, 330, 1600, 1080); C_215 = (300, 380, 1920, 1080)
C_209 = (200, 470, 1720, 1080); C_264 = (200, 300, 1720, 1080); C_246 = (0, 460, 1920, 1080); C_279 = (200, 470, 1720, 1080)
C_228 = (300, 300, 1700, 1080); C_259 = (300, 430, 1820, 1080)
KEYL = ("FADAISES", "MAGIQUES", "MARCHÉ")
SHOTS = [
    dict(id="A0", kind="collage", bg=POPPY, sheet=(PINK, "bas", 0.80, -4, 1),
         photos=[("HU", 225.0, C_225, 820, (540, 1080), -5, 0.0, "couleur"), ("HU", 257.0, C_257, 760, (520, 1530), 4, 3 * T, "rose")],
         boards=[([ln(0), ln(1, 2)], None, BLUSH)], txt_h=128, strips=2, poppies=3,
         why="2026 — Fête de l'Huma, la foule au soleil (sans parole) sous « Gouverner sans compter » : photos collées, pancarte brandie"),
    dict(id="A1", kind="cut", src="HU", t=None, bg=PINK, sheet=(WHITE, "haut", 0.11, 3, 2), ghost=POPPY, box=HBOX, pt=HPT,
         scale=(1.42, 1.45), cx=1000,
         boards=[([ln(3, 4), ln(5), ln(6)], None, WHITE), ([ln(7, 8, 9), ln(10)], wt(7), PINK)], txt_h=128, strips=2, poppies=1,
         photos=[("HU", 141.0, C_141, 520, (220, 1180), -7, 0.0, "coq")],
         why="Fête de l'Huma, son direct synchro : « sur les fadaises magiques de la main invisible », Mélenchon détouré seul sur rose, double tirage tramé coquelicot"),
    dict(id="A2", kind="cut", src="HU", t=None, bg=BLUSH, sheet=(POPPY, "bas", 0.86, 5, 3), ghost=PINK, box=HBOX, pt=HPT,
         scale=(1.45, 1.49), cx=1000,
         boards=[([ln(8, 9, 10), ln(11, 12)], None, BLUSH), ([ln(13, 14), ln(15)], wt(13), WHITE)], txt_h=124, strips=3, poppies=2,
         photos=[("HU", 215.0, C_215, 540, (870, 1150), 6, 2 * T, "rose")],
         why="même plan synchro : « du marché et autres stupidités », une 2e pancarte remplace la 1re sur « et autres »"),
    dict(id="A3", kind="cut", src="HU", t=None, bg=POPPY, sheet=(BLUSH, "haut", 0.10, -3, 4), ghost=INK, box=HBOX, pt=HPT,
         scale=(1.49, 1.53), cx=1000,
         boards=[([ln(15), ln(16)], None, PINK)], txt_h=128, strips=3, poppies=2,
         photos=[("HU", 209.0, C_209, 560, (240, 1250), -5, 0.0, "couleur"), ("HU", 264.0, C_264, 520, (860, 1300), 6, 2 * T, "coq")],
         bseed="A3", why="même plan synchro : « stupidités métaphysiques », coupé avant qu'il baisse la tête sur ses notes (68,9 s)"),
    dict(id="A4", kind="collage", bg=PINK, sheet=(POPPY, "bas", 0.82, 4, 9),
         photos=[("HU", 211.5, C_209, 800, (540, 1000), -4, 0.0, "couleur"), ("HU", 262.5, C_264, 740, (520, 1480), 5, T, "coq")],
         boards=[([ln(15), ln(16)], None, PINK)], bseed="A3", txt_h=128, strips=2, poppies=3,
         why="Fête de l'Huma, la foule (sans parole) sur la fin de « métaphysiques » et l'ovation, jusqu'au drop : même pancarte qui continue"),
    dict(id="B1", kind="sil", src="HU", t=152.0, bg=PINK, ghost=POPPY, box=(420, 30, 1660, 755), pt=(0.46, 0.75), dest_w=1900, cx=1000, push=(1.0, 1.04),
         rboards=[([[("GOUVERNER.", 0.0)]], 0.0, WHITE)], txt_y=330, txt_h=170, strips=3, poppies=3, flash=True,
         why="DROP « Na na na » — Fête de l'Huma (152 s, poing serré, sans le son) : silhouette blanche 3 images puis Mélenchon en couleur, contour autocollant"),
    dict(id="B2", kind="collage", bg=PAPER, sheet=(PINK, "bas", 0.84, -5, 6),
         photos=[("HU", 228.0, C_228, 760, (520, 900), -4, 0.0, "couleur"), ("HU", 259.0, C_259, 700, (560, 1280), 5, T, "rose"),
                 ("HU", 246.0, C_246, 720, (500, 1640), -3, 2 * T, "coq"), ("HU", 279.0, C_279, 560, (330, 560), 6, 3 * T, "couleur")],
         rboards=[([[("SANS", 0.0), ("COMPTER", 0.0), ("SUR", 0.0)], [("LES", 0.0), ("FADAISES", 0.0)], [("MAGIQUES", 0.0)]], 0.0, BLUSH)],
         txt_y=330, txt_h=130, strips=2, poppies=4,
         why="collage de foule d'été : la Fête de l'Huma en photos (couleur, rose, coquelicot) qui se collent une par temps, pancarte brandie"),
    dict(id="B3", kind="cut", src="HU", t=124.0, bg=POPPY, sheet=(PINK, "bas", 0.78, -6, 7), ghost=PINK, box=(420, 30, 1640, 815), pt=(0.47, 0.72),
         scale=(1.36, 1.40), cx=1030,
         photos=[("HU", 226.5, C_225, 560, (230, 1250), -6, 0.0, "rose")],
         rboards=[([[("LA", 0.0), ("MAIN", 0.0)], [("INVISIBLE", 0.0)], [("DU", 0.0), ("MARCHÉ", 0.0)]], 0.0, WHITE)], txt_y=320, txt_h=140,
         strips=3, poppies=2,
         why="Fête de l'Huma (124 s, bras tendu vers la foule, sans le son) : détouré sur coquelicot + feuille rose déchirée"),
    dict(id="B4", kind="cut", src="HU", t=33.0, bg=BLUSH, sheet=(POPPY, "haut", 0.12, 4, 8), ghost=POPPY, box=(420, 30, 1660, 815), pt=(0.46, 0.72),
         scale=(1.36, 1.40), cx=1040,
         photos=[("HU", 258.0, C_259, 560, (820, 1220), 6, 0.0, "coq"), ("HU", 265.5, C_264, 520, (250, 1330), -5, 2 * T, "couleur")],
         rboards=[([[("ET", 0.0), ("AUTRES", 0.0)], [("STUPIDITÉS", 0.0)], [("MÉTAPHYSIQUES.", 0.0)]], 0.0, PINK)], txt_y=320, txt_h=118,
         strips=3, poppies=2, flash2=True,
         why="Fête de l'Huma (33 s, index pointé, sans le son) : détouré sur rose poudré, photos de la foule collées derrière"),
    dict(id="B5", kind="collage", bg=POPPY,
         photos=[("HU", 210.5, C_209, 780, (540, 700), 3, 0.0, "couleur"), ("HU", 229.0, C_228, 720, (480, 1150), -5, 0.5 * T, "rose"),
                 ("HU", 260.0, C_259, 720, (600, 1560), 4, T, "coq")],
         strips=2, poppies=5,
         why="collage qui se remplit photo après photo (demi-temps) : la foule de la Fête de l'Huma, coquelicots qui poussent"),
    dict(id="FIN", kind="card", bg=BLUSH, push=(1.0, 1.035), poppies=4,
         big=[("JEAN-LUC", 0.0, rgb(POPPY)), ("MÉLENCHON", TB, rgb(POPPY))], big_y=520, big_sizes=[300, 360],
         rboards=[([[("2027", 2 * TB)]], 2 * TB, WHITE)], txt_y=1040, txt_h=190, letters=("2027",),
         why="carton final propre (rose poudré, coquelicot + encre) : son nom et 2027 sur une pancarte, pas de CTA"),
]
BOUNDS_T = [0] + CUTF + [fr(END)]
assert len(BOUNDS_T) == len(SHOTS) + 1, (len(BOUNDS_T), len(SHOTS))
for i, sh in enumerate(SHOTS):
    sh["a"], sh["bb"] = BOUNDS_T[i], BOUNDS_T[i + 1]; sh["n"] = sh["bb"] - sh["a"]; sh["clip"] = "R7_%s.mov" % sh["id"]
    if sh.get("src") == "HU" and sh["t"] is None: sh["t"] = V_SRC0 + sh["a"] / FPS          # plans A synchro avec la voix
assert min(sh["n"] for sh in SHOTS) >= 18, [(s["id"], s["n"]) for s in SHOTS]
assert SHOTS[1]["t"] > 63.40, ("plan synchro dans les images de R3 (62,4-63,37 s)", SHOTS[1]["t"])

def write_mov(frames, path):
    p = subprocess.Popen([FF, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", "%dx%d" % (W, H), "-r", str(FPS), "-i", "-",
                          "-c:v", "prores_ks", "-profile:v", "3", "-pix_fmt", "yuv422p10le", "-vendor", "apl0", path], stdin=subprocess.PIPE)
    for f in frames: p.stdin.write((np.clip(f, 0, 1) * 255 + 0.5).astype(np.uint8).tobytes())
    p.stdin.close(); p.wait()
def draw_placard(img, pieces, f_abs, key, colhex, layer):
    """layer 'fond' = carton + manche (derrière la découpe) ; 'texte' = morceaux de texte qui suivent la pancarte."""
    pl, pcx, pcy = placard(pieces, key, colhex); dx, dy, ang = brandish(f_abs, key)
    if layer == "fond":
        s0 = pop(f_abs, fr(min(t for _, _, _, t in pieces)), n=4, amp=0.06)
        if s0 is not None: paste(img, pl, pcx + dx, pcy + dy, s0, ang)
        return
    for im, cx, cy, t in pieces:
        s = pop(f_abs, fr(t))
        if s is None: continue
        x, y = rot_pt(cx, cy, pcx, pcy, ang); paste(img, im, x + dx, y + dy, s, ang)
CARD_TAPES = [tape_rgba(170, 46, np.random.default_rng(40 + j)) for j in range(4)]
def render(sh):
    n = sh["n"]; a = sh["a"]; frames = []
    rel = lambda t: sh["a"] / FPS + t
    seed = skey(sh["id"]) * 7
    boards = []                                                             # [(pièces en temps timeline, f_début, couleur pancarte)]
    if sh.get("boards"):
        for j, (lines, t0, col) in enumerate(sh["boards"]):
            p = board(lines, 300, skey(sh.get("bseed", sh["id"])) * 7 + j, h=sh.get("txt_h", 130), letters=KEYL, seq=0.0, tape=False)
            p = [(im, cx, cy, max(t, a / FPS)) for im, cx, cy, t in p]
            boards.append((p, fr(t0) if t0 is not None else a, col))
    if sh.get("rboards"):                                                   # cartons après le drop : un groupe de mots complet par carton
        for j, (lines, t0, col) in enumerate(sh["rboards"]):
            p = board(lines, sh["txt_y"], seed + j, h=sh.get("txt_h", 130), letters=sh.get("letters", ()), seq=0.0, tape=False)
            boards.append(([(im, cx, cy, rel(t)) for im, cx, cy, t in p], fr(rel(t0)), col))
    big = []
    if sh.get("big"):
        big = [(im, cx, cy, rel(t)) for im, cx, cy, t in big_text(sh["big"], sh["big_y"], (S + "Impact.ttf", 0), (XMAX - XMIN) * 0.92, sh["big_sizes"])]
    photos = [Photo(read_frames(ps, pt, n), pbox, pw, pc, pa, fr(rel(pt0)), (sh["id"], j), duo)
              for j, (ps, pt, pbox, pw, pc, pa, pt0, duo) in enumerate(sh.get("photos", []))]
    strips = make_strips(sh)
    k0 = nbeat(a)
    if sh["kind"] in ("cut", "sil"):
        raw = read_frames(sh["src"], sh["t"], n)
        ms, BX = masks("%s_%s_%.2f_%d" % (sh["id"], sh["src"], sh["t"], n), raw, sh["box"], sh["pt"])
    for i in range(n):
        f = a + i; u = i / max(n - 1, 1); kb = nbeat(f) - k0
        img = paper(sh["bg"])
        if sh.get("sheet"): apply_sheet(img, sh["sheet"])
        for st in strips:                                                   # une bande / un coquelicot de plus à chaque temps
            if st["k"] <= kb:
                dx, dy, da = jit((sh["id"], "s", st["k"]), nbeat(f), amp=6, ang=1.2)
                s_ = pop(f, BEATF[k0 + st["k"] - 1] if st["k"] > 0 and 0 <= k0 + st["k"] - 1 < len(BEATF) else a, n=4, amp=0.10) or 1.0
                paste(img, st["img"], st["cx"] + dx, st["cy"] + dy, s_, st["ang"] + da)
        for ph in photos:
            s_ = pop(f, ph.f0, n=5, amp=0.10)
            if s_ is not None:
                dx, dy, da = jit(ph.key, nbeat(f), amp=9, ang=1.8)
                paste(img, ph.rgba(i), ph.center[0] + dx, ph.center[1] + dy, s_, ph.angle + da)
        cur = None
        for jb, (p, f0, col) in enumerate(boards):
            if f >= f0: cur = (jb, p, col)
        if cur: draw_placard(img, cur[1], f, (sh.get("bseed", sh["id"]), cur[0]), cur[2], "fond")
        if sh["kind"] in ("cut", "sil"):
            x0, y0, x1, y1 = BX; m = ms[i]
            if sh["kind"] == "cut":
                sc = sh["scale"][0] + (sh["scale"][1] - sh["scale"][0]) * u; hh = (y1 - y0) * sc
                ccx = W / 2 + ((x1 - x0) / 2 - (sh["cx"] - x0)) * sc; ccy = H - hh / 2; r_ = 7
            else:
                z = sh["push"][0] + (sh["push"][1] - sh["push"][0]) * u
                sc = sh["dest_w"] / (x1 - x0) * z; hh = (y1 - y0) * sc
                ccx = W / 2 + ((x1 - x0) / 2 - (sh["cx"] - x0)) * sc; ccy = H - hh / 2; r_ = 9
            if sh.get("ghost"):                                             # double tirage tramé, décalé, qui saute sur les temps
                gdx, gdy, gda = jit((sh["id"], "g"), nbeat(f), amp=10, ang=1.0)
                g = ghost_rgba(raw[i], m, BX, 1.0, sh["ghost"])
                paste(img, g, ccx + 46 + gdx, ccy - 34 + gdy, sc * 1.10, -2.5 + gda)
            st_ = np.dstack([np.ones((m.shape[0], m.shape[1], 3), np.float32) * np.array([0.97, 0.97, 0.96], np.float32), sticker(m, r_)])
            sd = st_.copy(); sd[..., :3] = 0; sd[..., 3] = cv2.GaussianBlur(st_[..., 3], (0, 0), 6) * 0.55
            paste(img, sd, ccx + 14, ccy + 10, sc)
            if sh["kind"] == "sil" and i < 3: paste(img, cutout_rgba(raw[i], m, BX, white=True), ccx, ccy, sc)   # silhouette blanche 3 images
            else: paste(img, st_, ccx, ccy, sc); paste(img, cutout_rgba(raw[i], m, BX), ccx, ccy, sc)
        if sh["kind"] == "card":
            for j, (tx, ty, ta) in enumerate(((175, 300, -32), (905, 300, 30), (175, 1540, 28), (905, 1540, -30))):
                paste(img, CARD_TAPES[j], tx, ty, 1.0, ta)
            z = sh["push"][0] + (sh["push"][1] - sh["push"][0]) * u
            for im, cx, cy, t in big:
                s_ = pop(f, fr(t))
                if s_ is not None: paste(img, im, W / 2 + (cx - W / 2) * z, H / 2 + (cy - H / 2) * z, s_ * z)
        if cur: draw_placard(img, cur[1], f, (sh.get("bseed", sh["id"]), cur[0]), cur[2], "texte")
        if sh.get("flash") and i < 3: img = img + (1 - img) * [1.0, 0.6, 0.25][i]       # flash blanc 3 images (drop)
        if sh.get("flash2") and i < 2: img = img + (1 - img) * [0.7, 0.3][i]
        frames.append(finish(img, f))
    write_mov(frames, OUT + sh["clip"])
    print("  %-4s %3d im  (%s)" % (sh["id"], n, sh["kind"]), flush=True)

# ---------------- audio ----------------
VGAIN = 4.0
def make_audio():
    import soundfile as sf
    sr = 48000; N = int(round(END * sr))
    def grab(path, t, dur):
        p = subprocess.run([FF, "-v", "error", "-ss", "%.3f" % t, "-t", "%.3f" % dur, "-i", path, "-ac", "2", "-ar", str(sr), "-f", "f32le", "-"], capture_output=True)
        return np.frombuffer(p.stdout, np.float32).reshape(-1, 2).copy()
    voix = np.zeros((N, 2), np.float32); mus = np.zeros((N, 2), np.float32)
    v = grab(HG + "/" + SRC["HU"][0], V_IN, V_OUT - V_IN); env = np.ones(len(v), np.float32)
    k = int(0.03 * sr); env[:k] = np.linspace(0, 1, k); k = int(0.30 * sr); env[-k:] = np.linspace(1, 0, k)
    i0 = int(round(t_of_src(V_IN) * sr)); voix[i0:i0 + len(v)] = v * env[:, None] * 10 ** (VGAIN / 20)
    m = music_raw(MUSIC_IN)[:N]
    t = np.arange(len(m)) / sr; vend = t_of_src(69.18); dr = CUTS[DI]
    # sous la phrase : refrain sans kick « Freed from desire » baissé, montée sur la fin de la phrase et l'ovation, plein sur le drop « Na na na »
    gdb = np.interp(t, [0, 0.25, 4.0, vend - 0.4, dr - 0.03, dr, END], [-22, -19, -18, -12, -7, 0, 0])
    k = int(0.40 * sr); fo = np.ones(len(m), np.float32); fo[-k:] = np.linspace(1, 0, k)
    mus[:len(m)] = m * (10 ** (gdb / 20) * fo)[:, None]
    sf.write(OUT + "R7-voix.wav", voix, sr, subtype="PCM_24"); sf.write(OUT + "R7-musique.wav", mus, sr, subtype="PCM_24")
    sf.write(D + "tmp_mix.wav", voix + mus, sr, subtype="FLOAT")
    r = subprocess.run([FF, "-hide_banner", "-i", D + "tmp_mix.wav", "-af", "loudnorm=I=-14:TP=-2.5:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    js = json.loads(r[r.rindex("{"):r.rindex("}") + 1])
    af = ("loudnorm=I=-14:TP=-2.5:LRA=11:measured_I=%s:measured_TP=%s:measured_LRA=%s:measured_thresh=%s:offset=%s:linear=true,"
          "aresample=48000" % (js["input_i"], js["input_tp"], js["input_lra"], js["input_thresh"], js["target_offset"]))
    subprocess.run([FF, "-v", "error", "-y", "-i", D + "tmp_mix.wav", "-af", af, "-c:a", "pcm_s24le", OUT + "R7-mix.wav"], check=True)
    os.remove(D + "tmp_mix.wav"); print("audio : mix avant normalisation", js["input_i"], "LUFS")

# ---------------- plan ----------------
PHR = "Gouverner sans compter sur les fadaises magiques de la main invisible du marché et autres stupidités métaphysiques."
def build_plan():
    video = []
    for sh in SHOTS:
        v = {"id": sh["id"], "clip": sh["clip"], "folder": "genR7", "path": OUT + sh["clip"], "s": 0, "e": sh["n"], "rec": sh["a"], "dur": sh["n"],
             "clip_fps": FPS, "speed_pct": 100, "track": 1, "note": sh["why"], "kind": sh["kind"], "temps": round(sh["n"] / FPS / T, 2)}
        if sh.get("src"):
            path, sfps, url, off, ctx = SRC[sh["src"]]
            v["source"] = {"fichier": path, "in_s": round(sh["t"], 3), "out_s": round(sh["t"] + sh["n"] / FPS, 3), "fps": sfps, "url": url, "contexte": ctx,
                           "youtube_t": round(off + sh["t"], 1), "synchro": sh["id"].startswith("A")}
        if sh.get("photos"):
            v["photos"] = [{"fichier": SRC[p[0]][0], "in_s": p[1], "out_s": round(p[1] + sh["n"] / FPS, 2), "cadre_source": p[2], "tirage": p[7],
                            "url": SRC[p[0]][2], "synchro": False} for p in sh["photos"]]
        video.append(v)
    texts = []
    for sh in SHOTS:
        for lines, _, _ in sh.get("boards", []): texts.append({"plan": sh["id"], "texte": " ".join(w for line in lines for w, _ in line), "temps": "mot à mot sur la voix"})
        for lines, _, _ in sh.get("rboards", []): texts.append({"plan": sh["id"], "texte": " ".join(w for line in lines for w, _ in line)})
        for s_, t_, c_ in sh.get("big", []): texts.append({"plan": sh["id"], "texte": s_})
    plan = {"name": "R7 - Collage ransom-note pancartes - Jean-Luc Mélenchon", "fps": FPS, "w": W, "h": H, "duree_s": round(END, 3),
            "note": "Plans ProRes 9:16 composés en Python (lot7/_claude/gen/R7/out) : fonds papier froissé + feuille déchirée, Mélenchon détouré seul "
                    "(instance Vision, tools/inst), double tirage tramé, silhouette blanche 3 images au drop, photos de foule vivantes (couleur / bichromies), "
                    "pancartes brandies (texte ransom-note cuit), coquelicots en papier. s/e en images du clip (30 i/s), rec en images timeline. "
                    "Coupes sur les frappes réelles de Freed from Desire (out/R7-frappes.json). Aucun ralenti. Générateur : lot7/_claude/gen/R7/genR7.py",
            "phrase": {"texte": PHR, "url": SRC["HU"][2], "source": SRC["HU"][0], "in_s": 61.86, "out_s": 69.18, "youtube_s": [4771.86, 4779.18],
                       "timeline_s": [round(t_of_src(61.86), 2), round(t_of_src(69.18), 2)],
                       "voix": "son direct ; plans A0 et A4 = foule (sans parole), plans A1-A3 synchro (A3 coupé avant la tête baissée sur les notes) ; « c'est-à-dire » (61,34-61,78) non gardé"},
            "musique": {"fichier": "lot7/sons/R7-gala-freed-from-desire_complet.wav", "titre": "Gala - Freed from Desire", "url": SON_URL,
                        "debut_complet_s": round(MUSIC_IN, 4), "fin_complet_s": round(MUSIC_IN + END, 3), "drop_timeline_s": CUTS[DI],
                        "coupes_frappes_s": CUTS, "coupes_images": CUTF},
            "textes": texts, "video": video,
            "audio": [{"id": "mix", "clip": "R7-mix.wav", "folder": "genR7", "path": OUT + "R7-mix.wav", "rec": 0, "track": 1,
                       "note": "mix -14 LUFS : voix Huma %.2f-%.2f s (+%.0f dB) à %.2f s ; Freed from Desire dès %.3f s du complet, -19 dB sous la voix, montée, plein au drop, fondu de fin 0,4 s"
                               % (V_IN, V_OUT, VGAIN, t_of_src(V_IN), MUSIC_IN)}],
            "stems": ["lot7/_claude/gen/R7/out/R7-voix.wav", "lot7/_claude/gen/R7/out/R7-musique.wav"],
            "logos_exclus": "pupitre écrit (FÊTE DE L'HUMA, MELENCHON2027.fr) hors des fenêtres de détourage ; photos de foule recadrées sous les banderoles et le chapiteau écrit"}
    json.dump(plan, open(D + "plan-R7.json", "w"), indent=1, ensure_ascii=False)
    son = {"id": "R7", "titre": "Freed from Desire", "artiste": "Gala", "url": SON_URL,
           "chaine": "Gala (chaîne officielle, « Provided to YouTube by Do It Yourself », label Do It Yourself Multimedia Group)",
           "fichier": "lot7/sons/R7-gala-freed-from-desire_complet.wav",
           "extrait_complet_s": {"debut": round(MUSIC_IN, 4), "fin": round(MUSIC_IN + END, 3)},
           "paroles_audibles": "sous la phrase (baissé) : refrain sans kick « Freed from desire, mind and senses purified » ; au drop : le « Na na na » avec le kick",
           "bpm": round(60 / T, 1), "temps_s": T,
           "drop": {"complet_s": round(MUSIC_IN + CUTS[DI], 4), "timeline_s": CUTS[DI], "nature": "entrée du kick sur le « Na na na »"},
           "frappes_timeline_s": [round(k, 4) for k in KICKS], "coupes_sur_frappes_s": CUTS,
           "mix": "lot7/_claude/gen/R7/out/R7-mix.wav"}
    json.dump(son, open(D + "son.json", "w"), indent=1, ensure_ascii=False)

# ---------------- aperçu 540x960 ----------------
def apercu():
    plan = json.load(open(D + "plan-R7.json")); ins = []; fl = []
    for i, v in enumerate(plan["video"]):
        ins += ["-i", OUT + v["clip"]]
        fl.append("[%d:v]trim=start_frame=%d:end_frame=%d,setpts=PTS-STARTPTS,scale=540:960,setsar=1[v%d]" % (i, v["s"], v["e"], i))
    k = len(plan["video"]); fl.append("".join("[v%d]" % i for i in range(k)) + "concat=n=%d:v=1:a=0[v]" % k)
    ins += ["-i", OUT + "R7-mix.wav"]; out = HG + "/preview/apercu-R7.mp4"
    subprocess.run([FF, "-v", "error", "-y"] + ins + ["-filter_complex", ";".join(fl), "-map", "[v]", "-map", "%d:a" % k,
                    "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "aac", "-b:a", "192k", "-shortest", out], check=True)
    print("aperçu", out)
# ---------------- mesure sur l'export : coupes vs frappes, LUFS / TP ----------------
def mesure():
    out = HG + "/preview/apercu-R7.mp4"
    p = subprocess.run([FF, "-v", "error", "-i", out, "-vn", "-ac", "2", "-ar", "48000", "-f", "f32le", "-"], capture_output=True)
    y = np.frombuffer(p.stdout, np.float32).reshape(-1, 2)
    hh = detect_hits(y); hp = detect_hits(y[:int((CUTS[DI] - 0.25) * 48000)])
    worst = 0
    for i, c in enumerate([fr_ / FPS for fr_ in CUTF]):
        pool = [x[0] for x in hh if (x[1] == "kick" and x[3] > 0.03)] if i >= DI else [x[0] for x in hp]
        k = min(pool, key=lambda t: abs(t - c)); e = (c - k) * 1000; worst = max(worst, abs(e))
        print("  coupe %.3f  frappe %.4f  écart %+.1f ms" % (c, k, e))
    print("écart max coupes/frappes : %.1f ms" % worst)
    r = subprocess.run([FF, "-hide_banner", "-i", out, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    print(r[r.rindex("Summary"):])
if __name__ == "__main__":
    args = set(a for a in sys.argv[1:] if not a.startswith("only=")) or {"shots", "audio", "plan", "apercu"}
    only = [x for a in sys.argv[1:] if a.startswith("only=") for x in a.split("=", 1)[1].split(",")]
    print("musique dès %.4f s ; coupes (s) :" % MUSIC_IN, [round(c, 4) for c in CUTS], "images :", CUTF, "fin %.3f" % END)
    if "shots" in args or only:
        for sh in SHOTS:
            if not only or sh["id"] in only: render(sh)
    if "audio" in args: make_audio()
    if "plan" in args: build_plan()
    if "apercu" in args: apercu()
    if "mesure" in args: mesure()
