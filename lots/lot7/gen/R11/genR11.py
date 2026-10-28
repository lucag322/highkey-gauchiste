# R11 (lot 7) — Collage ransom-note « plateaux télé collés », Danièle Obono, son Doja Cat – Paint The Town Red (Provided to YouTube, Kemosabe/RCA).
# Modèle : lot6/_claude/gen/R6/genR6.py (validé) — mêmes fonctions (découpe Vision par instance tools/inst, morceaux de texte penchés serif/sans,
#   papier froissé, feuilles déchirées, double tirage tramé, bandes, scotch, frappes, carton final), poussé vers l'idée du brief :
#   les plateaux télé (LCI, BFMTV) découpés comme des ÉCRANS collés (marge papier déchirée, cadre noir arrondi, lignes de balayage, reflet,
#   scotch), Obono qui SORT de l'écran (plans « tv »), et un arrêt sur image découpé sous « Cause… » avant le drop.
# Palette R11 (brief) : bordeaux #6A0F24, rose pâle #F6D3DA (+ vieux rose #E39AAD, crème, encre lie-de-vin) — aucune couleur de R1-R6.
# Phrase (son direct, plans synchro A1-A4) : « Absolument pas, je viens de vous dire que je pense, et nous pensons, et nous ne changeons pas
#   d'avis là-dessus, ne vous en déplaise, que c'est immoral d'avoir autant d'argent. » (LCI, 24/09/2026, chaîne Danièle Obono,
#   youtu.be/wn6qL6YseFY 1523,16-1530,80 s = lot3/sources/G4-obono-lci-2026-09-24-a.mp4 123,16-130,80 s)
#   -> autre phrase que G4 (1540 s, « Ce que les gens ne supportent pas… ») et V2 (1008 s, « c'est de la responsabilité des politiques… »).
# Son : extrait continu du 3e refrain ; sous la phrase, fin du 3e couplet baissé qui monte, puis « Cause bitch? » juste après « argent »,
#   le silence, et le drop = « I said what I said » (173,757 s du morceau) ; coupes sur les claps réels (toutes les 2 temps, 100 BPM).
# Usage : python genR11.py [shots] [audio] [plan] [apercu] [mesure] [only=ID,ID]   (sans argument = tout sauf mesure)
import sys
sys.dont_write_bytecode = True
import os, json, subprocess, math, re
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
HG = "/Users/luca.grousset/Movies/highkey-gauchiste"
D = HG + "/lot7/_claude/gen/R11/"; OUT = D + "out/"; CACHE = D + "cache/"; os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, D)
from hits import detect_hits
FF = "/opt/homebrew/bin/ffmpeg"; INST = D + "tools/inst"; FPS = 30; W, H = 1080, 1920
def fr(t): return int(round(t * FPS))
def hexc(h): h = h.lstrip("#"); return np.array([int(h[4:6], 16), int(h[2:4], 16), int(h[0:2], 16)], np.float32) / 255   # BGR
def rgb(h): h = h.lstrip("#"); return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
# palette R11 : bordeaux, rose pâle, vieux rose, crème, encre lie-de-vin
WINE, ROSE, BLUSH, CREAM, DEEP, WHITE = "#6A0F24", "#F6D3DA", "#E39AAD", "#FBF2EE", "#2E0510", "#FFFFFF"
PAPER, INK = CREAM, DEEP

# ---------------- sources (lecture seule, lot 3) ----------------
SRC = {
    "LA": ("lot3/sources/G4-obono-lci-2026-09-24-a.mp4", 30.0, "https://www.youtube.com/watch?v=wn6qL6YseFY", 1400.0,
           "LCI, Rochebin soir, 24/09/2026 (chaîne Danièle Obono, « L'EXTRÊME richesse est immorale »)"),
    "LB": ("lot3/sources/G4-obono-lci-2026-09-24-b.mp4", 30.0, "https://www.youtube.com/watch?v=wn6qL6YseFY", 870.0,
           "LCI, Rochebin soir, 24/09/2026 (chaîne Danièle Obono)"),
    "BF": ("lot3/sources/G4-obono-bfmtv-2026-09-04.mp4", 30.0, "https://www.youtube.com/watch?v=XDCpNQsFZWc", 1500.0,
           "BFMTV, 04/09/2026 (chaîne Danièle Obono, « Les macronistes MENTENT, le RN VOLE, LFI c'est carré »)"),
}

# ---------------- musique : Doja Cat – Paint The Town Red ----------------
SON_FILE = HG + "/lot7/sons/R11-doja-paint-the-town-red_complet.wav"; SON_URL = "https://www.youtube.com/watch?v=fGe8drSjqHI"
MDROP = 173.757                      # 1re attaque après le silence : « I said what I said » (3e refrain)
DROP = 8.85; T = 0.60                # 100 BPM
MUSIC_IN0 = MDROP - DROP
END = 19.95                          # fin sur « I said what I said » (2e fois) ; règle lot 7 : 20 s max
# coupes visées (timeline) + type de frappe : claps du couplet sous la voix, attaque du drop, puis claps toutes les 2 temps
CUT_T = [(2.879, "caisse"), (4.100, "caisse"), (6.499, "caisse"), (DROP, "drop")] + [(DROP + 1.249 + 1.2 * k, "caisse") for k in range(7)]
HITS_JSON = OUT + "R11-frappes.json"
def music_raw(mi, dur=END + 0.5, sr=48000):
    import soundfile as sf
    i0 = int(round(mi * sr)); x, r = sf.read(SON_FILE, start=i0, frames=int(dur * sr), dtype="float32"); assert r == sr; return x
def hits_all(mi):
    """Frappes de l'extrait + claps du couplet détectés sur le couplet seul (sinon écrasés par la normalisation sur le refrain)
    + attaque du drop détectée sur une fenêtre autour du silence."""
    h = detect_hits(music_raw(mi)); pre = [x for x in detect_hits(music_raw(mi, dur=DROP - 0.25)) if x[1] == "caisse"]
    x = music_raw(mi + DROP - 0.30, dur=0.8); dr = [(round(t + DROP - 0.30, 4), "drop", s, l) for t, b, s, l in detect_hits(x)]
    return sorted([x for x in h if not (x[1] == "caisse" and x[0] < DROP - 0.25)] + pre + dr)
def kicks_of(h): return [x[0] for x in h if x[1] == "kick" and x[3] > 0.12]
def snares_of(h): return [x[0] for x in h if x[1] == "caisse"]
def snap_list(h, targets):
    out = []
    for t, kind in targets:
        pool = [x[0] for x in h if x[1] == kind]
        c = min(pool, key=lambda k: abs(k - t)); assert abs(c - t) < 0.04, ("pas de frappe près de", t, kind, c); out.append(c)
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
HITS = [list(h) for h in HITS]
KICKS = kicks_of(HITS)
CUTS = snap_list(HITS, CUT_T); CUTF = [fr(c) for c in CUTS]
DROPF = CUTF[3]; TB = T

# ---------------- voix ----------------
V_SRC0 = 123.07                       # source LA à t = 0 (« Absolument » 123,16 -> 0,09 s ; « d'argent » fin 130,80 -> 7,73 s)
V_IN, V_OUT = 123.12, 130.80          # « Absolument pas, … autant d'argent. » ; « Ce que je dis… » (130,80) non gardé
def t_of_src(s): return s - V_SRC0
WORDS = [("ABSOLUMENT", 123.16), ("PAS.", 123.52), ("JE", 123.82), ("VIENS", 123.90), ("DE", 124.04), ("VOUS", 124.18), ("DIRE", 124.32),
         ("QUE", 124.64), ("JE", 124.86), ("PENSE,", 125.08), ("ET", 125.40), ("NOUS", 125.56), ("PENSONS,", 125.70), ("ET", 126.08),
         ("NOUS", 126.24), ("NE", 126.36), ("CHANGEONS", 126.46), ("PAS", 126.80), ("D'AVIS", 126.92), ("LÀ-DESSUS,", 127.28),
         ("NE", 128.02), ("VOUS", 128.22), ("EN", 128.42), ("DÉPLAISE,", 128.56), ("QUE", 129.08), ("C'EST", 129.32), ("IMMORAL", 129.62),
         ("D'AVOIR", 130.02), ("AUTANT", 130.28), ("D'ARGENT.", 130.48)]
def wt(i): return t_of_src(WORDS[i][1])
def ln(*idx): return [(WORDS[i][0], wt(i)) for i in idx]
FREEZE = 7.76                         # arrêt sur image après « argent » (elle continue de parler dans la source)
# ---------------- polices ransom-note ----------------
S = "/System/Library/Fonts/Supplemental/"
FONTS = [(S + "Arial Black.ttf", 0), (S + "Georgia Bold.ttf", 0), (S + "Times New Roman Bold.ttf", 0), (S + "Impact.ttf", 0),
         (S + "Courier New Bold.ttf", 0), (S + "Rockwell.ttc", 2), (S + "AmericanTypewriter.ttc", 2), (S + "Didot.ttc", 2),
         (S + "Bodoni 72.ttc", 2), (S + "Futura.ttc", 2)]
FCOND = (S + "Futura.ttc", 4)
STYLES = [(rgb(CREAM), rgb(WINE)), (rgb(WINE), rgb(ROSE)), (rgb(ROSE), rgb(WINE)), (rgb(DEEP), rgb(ROSE)),
          ((255, 255, 255), rgb(DEEP)), (rgb(BLUSH), rgb(DEEP)), (rgb(WINE), (255, 255, 255)), ((240, 232, 228), (30, 12, 16))]
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
from decoupe import masques as dc_masques, controle as dc_controle, planche as dc_planche
def masks(key, frames, box, pt, k=13):
    """Découpe de LA personne visée : outil partagé _claude/outils/decoupe.py (instance Vision x segmentation personne, sans micro
    ni voisin, une seule forme, lissée) ; cache dans cache/dc/<key>."""
    return dc_masques(frames, box, pt, CACHE + "dc/" + key)
def grade(x, sat=1.10):
    x = 0.82 * x + 0.18 * (x * x * (3 - 2 * x))
    L = x @ np.array([0.0722, 0.7152, 0.2126], np.float32)
    return np.clip(L[..., None] + (x - L[..., None]) * sat, 0, 1)
def lum(x, gain=1.15):
    L = x @ np.array([0.0722, 0.7152, 0.2126], np.float32)
    L = L / max(float(np.percentile(L, 99)), 0.2); L = np.clip(L, 0, 1) ** 0.75
    L = np.clip((L - 0.5) * gain + 0.5 + 0.03, 0, 1); return 0.75 * L + 0.25 * (L * L * (3 - 2 * L))
DUO = {"vin": (DEEP, ROSE), "rose": (WINE, CREAM), "blush": (DEEP, BLUSH)}
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
STRIP_COLS = [ROSE, WINE, CREAM, BLUSH, DEEP, ROSE, WINE, BLUSH]
def strip_rgba(w, h, rng, colhex, ht=False):
    col = hexc(colhex); dot = hexc(WINE if colhex in (ROSE, CREAM, BLUSH) else BLUSH)
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

# ---------------- écrans télé découpés ----------------
def rrect(h, w, inset, r):
    """Masque rectangle à coins arrondis (anti-crénelé)."""
    m = np.zeros((h * 2, w * 2), np.uint8); i, r2 = inset * 2, r * 2
    cv2.rectangle(m, (i + r2, i), (w * 2 - i - r2, h * 2 - i), 255, -1); cv2.rectangle(m, (i, i + r2), (w * 2 - i, h * 2 - i - r2), 255, -1)
    for cx, cy in ((i + r2, i + r2), (w * 2 - i - r2, i + r2), (i + r2, h * 2 - i - r2), (w * 2 - i - r2, h * 2 - i - r2)):
        cv2.circle(m, (cx, cy), r2, 255, -1, cv2.LINE_AA)
    return cv2.resize(m, (w, h), interpolation=cv2.INTER_AREA).astype(np.float32) / 255
class Screen:
    """Plateau télé découpé comme un écran collé : marge papier déchirée, cadre noir arrondi, image en bichromie (ou couleur)
    avec lignes de balayage, vignettage et reflet ; scotch sur deux coins, ombre portée. Saute un peu sur chaque temps."""
    def __init__(self, frames, box, width, center, angle, f0, key, duo, bz=24, mg=16):
        self.frames, self.box, self.width, self.center, self.angle, self.f0, self.key, self.duo = frames, box, width, center, angle, f0, key, duo
        x0, y0, x1, y1 = box; self.h = int(round(width * (y1 - y0) / (x1 - x0))); self.bz, self.mg = bz, mg
        rng = np.random.default_rng(skey(key)); M = 40; self.M = M
        hh, ww = self.h + 2 * (bz + mg), width + 2 * (bz + mg); self.hh, self.ww = hh, ww
        self.mask = torn_mask(hh, ww, rng, rough=6, step=11, inset=3)
        self.bez = rrect(hh, ww, mg, 30); self.scr = rrect(hh, ww, mg + bz, 20)
        y, x = np.mgrid[0:hh, 0:ww].astype(np.float32)
        hl = np.clip(1 - y / hh, 0, 1) * 0.10                                        # cadre : léger dégradé (plastique)
        self.bezcol = hexc("#140306")[None, None, :] + hl[..., None]
        sl = np.where((np.arange(self.h) % 4) < 1, 0.80, 1.0).astype(np.float32)[:, None, None]
        yy, xx = np.mgrid[0:self.h, 0:width].astype(np.float32)
        r = np.sqrt(((xx - width / 2) / (width / 2)) ** 2 + ((yy - self.h / 2) / (self.h / 2)) ** 2) / np.sqrt(2)
        self.glass = (sl * (1 - 0.30 * np.clip(r, 0, 1) ** 2)[..., None]).astype(np.float32)
        d = (xx / width - yy / self.h * 0.5); self.glare = (np.exp(-((d - 0.18) / 0.06) ** 2) * 0.10)[..., None].astype(np.float32)
        self.shadow = np.zeros((hh + 2 * M, ww + 2 * M), np.float32); self.shadow[M + 10:M + 10 + hh, M + 8:M + 8 + ww] = self.mask * 0.5
        self.shadow = cv2.GaussianBlur(self.shadow, (0, 0), 5)
        self.tapes = []
        for (tx, ty) in ((M + int(rng.uniform(-10, 30)), M - 14), (M + ww - int(rng.uniform(100, 150)), M + hh - 28)):
            self.tapes.append((rot_rgba(tape_rgba(int(rng.uniform(120, 160)), 40, rng), rng.uniform(-40, -25)), (tx, ty)))
    def rgba(self, i):
        x0, y0, x1, y1 = self.box; M, b = self.M, self.bz + self.mg
        src = self.frames[min(i, len(self.frames) - 1)][y0:y1, x0:x1]
        c = duotone(src, self.duo) if self.duo else grade(src, 0.85)
        c = cv2.resize(c, (self.width, self.h), interpolation=cv2.INTER_AREA)
        c = np.clip(c * self.glass + self.glare, 0, 1)
        out = np.zeros((self.hh + 2 * M, self.ww + 2 * M, 4), np.float32); out[..., 3] = self.shadow
        body = np.ones((self.hh, self.ww, 3), np.float32) * hexc(CREAM)[None, None, :]
        body = body * (1 - self.bez[..., None]) + self.bezcol * self.bez[..., None]
        inner = np.zeros_like(body); inner[b:b + self.h, b:b + self.width] = c
        body = body * (1 - self.scr[..., None]) + inner * self.scr[..., None]
        a = self.mask[..., None]; reg = out[M:M + self.hh, M:M + self.ww]
        reg[..., :3] = body * a; reg[..., 3] = np.maximum(self.mask, reg[..., 3])
        for t, (tx, ty) in self.tapes: over(out, t, tx, ty)
        return out
def beat_grid():
    """Temps : grille d'un temps comptée à rebours depuis le drop (couplet), puis claps réels + demi-mesures après le drop."""
    g = []; t = CUTS[3] - T
    while t > 0: g.append(t); t -= T
    t = CUTS[3]
    while t < END: g.append(t); t += T
    return sorted(g)
BEATS = beat_grid(); BEATF = [fr(b) for b in BEATS]
def nbeat(f): return sum(1 for b in BEATF if b <= f)
def jit(key, k, amp=8.0, ang=1.5):
    r = np.random.default_rng(skey(key) * 1000 + k); return r.uniform(-amp, amp), r.uniform(-amp, amp), r.uniform(-ang, ang)

# ---------------- plans ----------------
# Cadres source (sans logo LCI / BFMTV, sans bandeaux ni filigrane « Rochebin soir ») :
LA_BOX = (800, 150, 1910, 800)        # plan à deux LCI : Obono (droite), buste jusqu'à la taille ; logo LCI au-dessus de y 145, bandeau sous y 805
LA_PT = (0.441, 0.63); LA_CX = 1390   # point poitrine ; centre du visage (x source) -> centre du cadre
LA_TV = (820, 150, 1910, 800)         # sa moitié du plan à deux en écran (zone sûre : aucun visage au bord)
BFBOX = (330, 195, 1890, 790)         # BFMTV plan à deux (logo BFMTV x < 300, y < 190 ; bandeaux sous y 795)
BF_TV = (900, 195, 1890, 790)         # BFMTV : sa moitié du plan à deux en écran
WIDE_A = (500, 300, 1560, 765); WIDE_B150 = (0, 300, 1380, 765); WIDE_B89 = (0, 300, 1560, 765)   # plateaux larges LCI
CU = (200, 0, 1560, 765)              # gros plans LCI
KEYL = ("IMMORAL",)
# Découpes (règles Luca 27/10) : outil decoupe.py, buste au moins jusqu'à mi-poitrine posé sur le bas du cadre (plans cut / sil) ou bord
# déchiré au bas de l'écran (plans tv) ; visage dans la zone sûre TikTok (bas du visage < 75 % de la hauteur, centré).
SHOTS = [
    dict(id="A1", kind="cut", src="LA", t=None, bg=WINE, sheet=(ROSE, "bas", 0.82, -4, 1), ghost=BLUSH, box=LA_BOX, pt=LA_PT,
         scale=(1.48, 1.53), cx=LA_CX,
         boards=[([ln(0), ln(1)], None), ([ln(2, 3, 4), ln(5, 6)], wt(2)), ([ln(7, 8, 9), ln(10, 11, 12)], wt(7))], txt_h=138, strips=3,
         screens=[("LB", 89.0, WIDE_B89, 860, (430, 760), -5, 0.0, "vin")],
         why="LCI 24/09/2026, son direct : « Absolument pas, je viens de vous dire que je pense, et nous pensons », Obono détourée (decoupe.py) sur bordeaux, double tirage tramé vieux rose, plateau LCI en écran collé"),
    dict(id="A2", kind="tv", src="LA", t=None, bg=ROSE, sheet=(WINE, "bas", 0.86, 3, 2), box=LA_BOX, pt=LA_PT, cx=LA_CX,
         sbox=LA_TV, sw=820, sc=(540, 1180), sang=-2.0, duo="vin", popk=1.80,
         boards=[([ln(13, 14, 15), ln(16), ln(17, 18)], None)], txt_h=138, strips=3,
         why="même plan synchro : « et nous ne changeons pas d'avis », le plateau LCI en écran bichromie et Obono en couleur qui sort de l'écran (bas en papier déchiré)"),
    dict(id="A3", kind="cut", src="LA", t=None, bg=BLUSH, sheet=(CREAM, "bas", 0.80, 5, 3), ghost=WINE, box=LA_BOX, pt=LA_PT,
         scale=(1.62, 1.68), cx=LA_CX,
         boards=[([ln(19)], None), ([ln(20, 21, 22), ln(23)], wt(20)), ([ln(24, 25), ln(26)], wt(24))], txt_h=140, strips=4,
         screens=[("BF", 2.0, BFBOX, 560, (560, 820), -6, 0.0, "rose")],
         why="même plan synchro, plus serré : « là-dessus, ne vous en déplaise, que c'est », plateau BFMTV en écran derrière elle"),
    dict(id="A4", kind="cut", src="LA", t=None, bg=WINE, sheet=(BLUSH, "haut", 0.12, -3, 4), ghost=ROSE, box=LA_BOX, pt=LA_PT,
         scale=(1.54, 1.58), cx=LA_CX, freeze=FREEZE,
         boards=[([ln(24, 25), ln(26)], None), ([ln(27, 28), ln(29)], wt(27))], txt_h=140, strips=3,
         screens=[("LA", 100.5, WIDE_A, 600, (300, 800), -6, FREEZE, "rose"), ("LB", 150.0, WIDE_B150, 600, (790, 760), 5, FREEZE + 0.55, "blush")],
         why="même plan synchro : « immoral d'avoir autant d'argent », puis arrêt sur image découpé (elle continue de parler dans la source) ; deux plateaux collés sur « Cause… » et le silence"),
    dict(id="B1", kind="sil", src="LB", t=86.0, bg=ROSE, ghost=WINE, box=(380, 0, 1560, 770), pt=(0.49, 0.72), dest_w=1820, cx=940, push=(1.0, 1.04),
         rboards=[([[("ABSOLUMENT", 0.0)], [("PAS.", 0.0)]], 0.0)], txt_y=300, txt_h=150, letters=("PAS.",), strips=3, flash=True,
         why="drop « I said what I said » : LCI, elle répond (mains, buste), silhouette blanche 3 images puis couleur, contour autocollant, double tirage bordeaux"),
    dict(id="B2", kind="collage", bg=WINE,
         screens=[("BF", 88.0, BFBOX, 820, (540, 720), -4, 0.0, "vin"), ("LB", 31.0, (300, 0, 1560, 709), 560, (330, 1130), 5, TB, None),
                  ("LA", 103.5, CU, 520, (760, 1260), -3, 1.5 * TB, "rose")],
         rboards=[([[("JE", 0.0), ("PENSE,", 0.0)], [("ET", 0.0), ("NOUS", 0.0), ("PENSONS,", 0.0)]], 0.0)], txt_y=300, txt_h=140, strips=3,
         why="collage d'écrans : BFMTV, LCI, LCI, un écran par temps"),
    dict(id="B3", kind="cut", src="LB", t=29.0, bg=CREAM, sheet=(WINE, "bas", 0.78, -5, 5), ghost=BLUSH, box=(380, 0, 1560, 765), pt=(0.52, 0.70),
         scale=(1.46, 1.51), cx=931,
         screens=[("LB", 150.0, WIDE_B150, 640, (800, 900), 6, 0.0, "blush")],
         rboards=[([[("ET", 0.0), ("NOUS", 0.0), ("NE", 0.0)], [("CHANGEONS", 0.0)], [("PAS", 0.0), ("D'AVIS", 0.0)]], 0.0)], txt_y=300, txt_h=128,
         letters=("D'AVIS",), strips=3,
         why="LCI, elle argumente (sans son, musique seule) : détourée sur crème + feuille bordeaux déchirée, plateau large en écran"),
    dict(id="B4", kind="sil", src="LA", t=114.8, bg=BLUSH, ghost=WINE, box=(850, 0, 1800, 800), pt=(0.526, 0.625), dest_w=1450, cx=1380, push=(1.0, 1.035),
         rboards=[([[("NE", 0.0), ("VOUS", 0.0), ("EN", 0.0)], [("DÉPLAISE,", 0.0)]], 0.0)], txt_y=300, txt_h=150, strips=3, flash2=True,
         why="LCI plan à deux, elle répond mains ouvertes (buste jusqu'à la taille) : silhouette blanche 3 images puis couleur sur vieux rose, double tirage bordeaux"),
    dict(id="B5", kind="tv", src="BF", t=92.0, bg=CREAM, sheet=(ROSE, "haut", 0.14, 4, 6), box=(900, 60, 1890, 790), pt=(0.545, 0.685), cx=1420,
         sbox=BF_TV, sw=760, sc=(540, 1180), sang=2.5, duo="vin", popk=1.80, strips=4,
         why="BFMTV en écran bichromie, Obono en couleur qui sort de l'écran (bas en papier déchiré, sans texte)"),
    dict(id="B6", kind="cut", src="LB", t=50.0, bg=WINE, sheet=(ROSE, "bas", 0.80, 4, 7), ghost=CREAM, box=(450, 0, 1500, 770), pt=(0.43, 0.73),
         scale=(1.42, 1.47), cx=920,
         rboards=[([[("C'EST", 0.0)], [("IMMORAL", 0.0)], [("D'AVOIR", 0.0), ("AUTANT", 0.0)], [("D'ARGENT.", 0.0)]], 0.0)], txt_y=280, txt_h=122,
         letters=(), strips=3,
         why="LCI, buste, regard ferme : la conclusion de la phrase en carton"),
    dict(id="B7", kind="collage", bg=ROSE,
         screens=[("BF", 26.0, BFBOX, 760, (520, 640), 3, 0.0, "rose"), ("LA", 15.0, (300, 60, 1560, 769), 560, (330, 1110), -6, 0.5 * TB, None),
                  ("LB", 131.5, CU, 560, (760, 1330), 5, TB, "blush"), ("BF", 2.0, BFBOX, 440, (560, 1690), -4, 1.5 * TB, "vin")],
         strips=3,
         why="collage qui se remplit écran après écran (demi-temps) : BFMTV, LCI, LCI, BFMTV"),
    dict(id="FIN", kind="card", bg=ROSE, push=(1.0, 1.035),
         big=[("DANIÈLE", 0.0, rgb(WINE)), ("OBONO", TB, rgb(WINE))], big_y=600, big_sizes=[300, 400],
         why="carton final propre (rose pâle, bordeaux) : son nom, pas de CTA"),
]
BOUNDS_T = [0] + CUTF + [fr(END)]
assert len(BOUNDS_T) == len(SHOTS) + 1, (len(BOUNDS_T), len(SHOTS))
for i, sh in enumerate(SHOTS):
    sh["a"], sh["bb"] = BOUNDS_T[i], BOUNDS_T[i + 1]; sh["n"] = sh["bb"] - sh["a"]; sh["clip"] = "R11_%s.mov" % sh["id"]
    if sh.get("src") == "LA" and sh["t"] is None: sh["t"] = V_SRC0 + sh["a"] / FPS          # plans A synchro avec la voix
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
def cut_layer(img, raw_i, m, box, sc, ccx, ccy, r_, ghost, gkey, f, white=False, duo=None):
    if ghost:
        gdx, gdy, gda = jit(gkey, nbeat(f), amp=10, ang=1.0)
        paste(img, ghost_rgba(raw_i, m, box, 1.0, ghost), ccx + 46 + gdx, ccy - 34 + gdy, sc * 1.10, -2.5 + gda)
    st_ = np.dstack([np.ones((m.shape[0], m.shape[1], 3), np.float32) * np.array([0.97, 0.97, 0.96], np.float32), sticker(m, r_)])
    sd = st_.copy(); sd[..., :3] = 0; sd[..., 3] = cv2.GaussianBlur(st_[..., 3], (0, 0), 6) * 0.55
    paste(img, sd, ccx + 14, ccy + 10, sc)
    if white: paste(img, cutout_rgba(raw_i, m, box, white=True), ccx, ccy, sc); return
    paste(img, st_, ccx, ccy, sc)
    if duo:
        x0, y0, x1, y1 = box; paste(img, np.dstack([duotone(raw_i[y0:y1, x0:x1], duo), m]).astype(np.float32), ccx, ccy, sc)
    else: paste(img, cutout_rgba(raw_i, m, box), ccx, ccy, sc)
from decoupe import bas_dechire as dc_bas_dechire
def keep_largest(m):
    """Une seule forme (le bout de micro détaché du buste est retiré)."""
    b = (m > 0.5).astype(np.uint8); n, lab, st, _ = cv2.connectedComponentsWithStats(b, 8)
    if n <= 2: return m
    k = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA])); return (m * cv2.dilate((lab == k).astype(np.uint8), np.ones((5, 5), np.uint8))).astype(np.float32)
def tear_masks(sh, ms):
    """Règle Luca 27/10 : la découpe ne garde que la personne et finit dans un bord de papier déchiré propre, au-dessus du micro
    ou d'un voisin : coupe à plat à la ligne source sh['tear'], puis bas_dechire (outil partagé) et seule la plus grande forme."""
    if not sh.get("tear"): return ms
    x0, y0, x1, y1 = sh["box"]; yt = sh["tear"] - y0; out = []
    for m in ms:
        m = m.copy(); m[yt:] = 0; m = dc_bas_dechire(m, seed=skey(sh["id"]))
        b = (m > 0.5).astype(np.uint8); n, lab, st, _ = cv2.connectedComponentsWithStats(b, 8)
        if n > 2:
            k = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA])); keep = cv2.dilate((lab == k).astype(np.uint8), np.ones((5, 5), np.uint8))
            m = m * keep
        out.append(m.astype(np.float32))
    return out
def render(sh):
    n = sh["n"]; a = sh["a"]; frames = []
    rel = lambda t: sh["a"] / FPS + t
    seed = skey(sh["id"]) * 7
    boards = []                                                             # [(pièces, f_début)] en temps timeline
    if sh.get("boards"):
        for j, (lines, t0) in enumerate(sh["boards"]):
            boards.append((board(lines, 272, seed + j, h=sh.get("txt_h", 130), letters=KEYL, seq=0.0), fr(t0) if t0 is not None else a))
    elif sh.get("rboards"):                                                # cartons après le drop : un groupe de mots complet par carton
        for j, (lines, t0) in enumerate(sh["rboards"]):
            p = board(lines, sh["txt_y"], seed + j, h=sh.get("txt_h", 130), letters=sh.get("letters", ()), seq=0.0, tape=False)
            boards.append(([(im, cx, cy, rel(t)) for im, cx, cy, t in p], fr(rel(t0))))
    big = []
    if sh.get("big"):
        big = [(im, cx, cy, rel(t)) for im, cx, cy, t in big_text(sh["big"], sh["big_y"], (S + "Impact.ttf", 0), (XMAX - XMIN) * 0.92, sh["big_sizes"])]
    screens = []
    for j, (ps, pt, pbox, pw, pc, pa, pt0, duo) in enumerate(sh.get("screens", [])):
        f0 = max(a, fr(pt0)) if sh["id"].startswith("A") else fr(rel(pt0))
        screens.append(Screen(read_frames(ps, pt, n), pbox, pw, pc, pa, f0, (sh["id"], j), duo))
    strips = make_strips(sh)
    k0 = nbeat(a)
    fz = n if not sh.get("freeze") else fr(sh["freeze"]) - a
    if sh["kind"] in ("cut", "sil", "tv"):
        raw = read_frames(sh["src"], sh["t"], min(n, fz + 1))
        ms = masks("%s_%s_%.2f_%d" % (sh["id"], sh["src"], sh["t"], len(raw)), raw, sh["box"], sh["pt"], k=27 if sh["kind"] == "sil" else 13)
        ms = tear_masks(sh, ms)
        if sh["kind"] == "tv": ms = [keep_largest(dc_bas_dechire(m, seed=skey(sh["id"]))) for m in ms]
        cs = [dc_controle(m) for m in ms]
        print("  %s controle : gauche %.3f droite %.3f haut %.3f morceaux %d bas_net %.3f" % (sh["id"], max(c["gauche"] for c in cs),
              max(c["droite"] for c in cs), max(c["haut"] for c in cs), max(c["morceaux"] for c in cs), max(c["bas_net"] for c in cs)), flush=True)
        os.makedirs(D + "sheets", exist_ok=True); dc_planche(raw, ms, sh["box"], D + "sheets/decoupe_%s.png" % sh["id"])
    if sh["kind"] == "tv":
        tv = Screen(raw, sh["sbox"], sh["sw"], sh["sc"], sh["sang"], a, (sh["id"], "tv"), sh["duo"])
    for i in range(n):
        f = a + i; u = i / max(n - 1, 1); kb = nbeat(f) - k0; ii = min(i, fz)
        img = paper(sh["bg"])
        if sh.get("sheet"): apply_sheet(img, sh["sheet"])
        for st in strips:                                                   # une bande de plus à chaque temps
            if st["k"] <= kb:
                dx, dy, da = jit((sh["id"], "s", st["k"]), nbeat(f), amp=6, ang=1.2)
                s_ = pop(f, BEATF[k0 + st["k"] - 1] if st["k"] > 0 and 0 <= k0 + st["k"] - 1 < len(BEATF) else a, n=4, amp=0.08) or 1.0
                paste(img, st["img"], st["cx"] + dx, st["cy"] + dy, s_, st["ang"] + da)
        for sc_ in screens:
            s_ = pop(f, sc_.f0, n=5, amp=0.10)
            if s_ is not None:
                dx, dy, da = jit(sc_.key, nbeat(f), amp=9, ang=1.8)
                paste(img, sc_.rgba(ii if sh.get("freeze") else i), sc_.center[0] + dx, sc_.center[1] + dy, s_, sc_.angle + da)
        if sh["kind"] in ("cut", "sil"):
            x0, y0, x1, y1 = sh["box"]; m = ms[ii]
            if sh["kind"] == "cut":
                sc = sh["scale"][0] + (sh["scale"][1] - sh["scale"][0]) * min(u, fz / max(n - 1, 1)); hh = (y1 - y0) * sc
                ccx = W / 2 + ((x1 - x0) / 2 - (sh["cx"] - x0)) * sc; ccy = H - hh / 2 if not sh.get("tear") else sh.get("tear_at", H - 60) - (sh["tear"] - (y0 + y1) / 2) * sc; r_ = 7
            else:
                z = sh["push"][0] + (sh["push"][1] - sh["push"][0]) * u
                sc = sh["dest_w"] / (x1 - x0) * z; hh = (y1 - y0) * sc
                ccx = W / 2 + ((x1 - x0) / 2 - (sh["cx"] - x0)) * sc; ccy = H - hh / 2 if not sh.get("tear") else sh.get("tear_at", H - 60) - (sh["tear"] - (y0 + y1) / 2) * sc; r_ = 9
            if sh.get("freeze") and i >= fz:                                  # arrêt sur image : la découpe saute un peu sur le temps
                dx, dy, da = jit((sh["id"], "fz"), nbeat(f), amp=6, ang=0.8); ccx += dx; ccy += abs(dy)
            cut_layer(img, raw[ii], m, sh["box"], sc, ccx, ccy, r_, sh.get("ghost"), (sh["id"], "g"), f, white=(sh["kind"] == "sil" and i < 3))
        if sh["kind"] == "tv":
            dx, dy, da = jit((sh["id"], "tv"), nbeat(f), amp=6, ang=0.8)
            z = 1.0 + 0.03 * u
            paste(img, tv.rgba(i), sh["sc"][0] + dx, sh["sc"][1] + dy, z, sh["sang"] + da)
            x0, y0, x1, y1 = sh["box"]; sx0, sy0, sx1, sy1 = sh["sbox"]; ks = sh["sw"] / (sx1 - sx0) * z
            k = ks * sh["popk"] * (1 + 0.03 * u)
            xh = sh["sc"][0] + dx + (sh["cx"] - (sx0 + sx1) / 2) * ks
            ybot = sh["sc"][1] + dy + (sy1 - (sy0 + sy1) / 2) * ks - 4                      # bas intérieur de l'écran
            ccx = xh + ((x1 - x0) / 2 - (sh["cx"] - x0)) * k; ccy = ybot - (sh.get("tear", y1) - (y0 + y1) / 2) * k
            cut_layer(img, raw[i], ms[i], sh["box"], k, ccx, ccy, 8, None, None, f, duo=sh.get("cutduo"))
        cur = None
        for jb, (p, f0) in enumerate(boards):
            if f >= f0: cur = (jb, p)
        if cur: draw_pieces(img, cur[1], f, boil=sh["id"] + str(cur[0]))
        if sh["kind"] == "card":
            for j, (tx, ty, ta) in enumerate(((175, 380, -32), (905, 380, 30), (175, 1460, 28), (905, 1460, -30))):
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
VGAIN = 12.5                          # voix LCI à -22 LUFS : remontée pour passer devant le couplet baissé
def make_audio():
    import soundfile as sf
    sr = 48000; N = int(round(END * sr))
    def grab(path, t, dur):
        p = subprocess.run([FF, "-v", "error", "-ss", "%.3f" % t, "-t", "%.3f" % dur, "-i", path, "-ac", "2", "-ar", str(sr), "-f", "f32le", "-"], capture_output=True)
        return np.frombuffer(p.stdout, np.float32).reshape(-1, 2).copy()
    voix = np.zeros((N, 2), np.float32); mus = np.zeros((N, 2), np.float32)
    v = grab(HG + "/" + SRC["LA"][0], V_IN, V_OUT - V_IN); env = np.ones(len(v), np.float32)
    k = int(0.03 * sr); env[:k] = np.linspace(0, 1, k); k = int(0.06 * sr); env[-k:] = np.linspace(1, 0, k)
    i0 = int(round(t_of_src(V_IN) * sr)); voix[i0:i0 + len(v)] = v * env[:, None] * 10 ** (VGAIN / 20)
    m = music_raw(MUSIC_IN)[:N]
    t = np.arange(len(m)) / sr; vend = t_of_src(V_OUT); dr = CUTS[3]
    # sous la phrase : fin du 3e couplet baissé qui monte ; « Cause bitch? » à découvert juste après la phrase ; silence ; plein au drop
    gdb = np.interp(t, [0, 0.25, 4.0, vend - 0.5, vend + 0.02, dr - 0.05, dr, END], [-23, -20, -18, -14, -3, -2, 0, 0])
    k = int(0.30 * sr); fo = np.ones(len(m), np.float32); fo[-k:] = np.linspace(1, 0, k)
    mus[:len(m)] = m * (10 ** (gdb / 20) * fo)[:, None]
    sf.write(OUT + "R11-voix.wav", voix, sr, subtype="PCM_24"); sf.write(OUT + "R11-musique.wav", mus, sr, subtype="PCM_24")
    sf.write(D + "tmp_mix.wav", voix + mus, sr, subtype="FLOAT")
    r = subprocess.run([FF, "-hide_banner", "-i", D + "tmp_mix.wav", "-af", "loudnorm=I=-14:TP=-2.5:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    js = json.loads(r[r.rindex("{"):r.rindex("}") + 1])
    af = ("loudnorm=I=-14:TP=-2.5:LRA=11:measured_I=%s:measured_TP=%s:measured_LRA=%s:measured_thresh=%s:offset=%s:linear=true,"
          "aresample=48000" % (js["input_i"], js["input_tp"], js["input_lra"], js["input_thresh"], js["target_offset"]))
    subprocess.run([FF, "-v", "error", "-y", "-i", D + "tmp_mix.wav", "-af", af, "-c:a", "pcm_s24le", OUT + "R11-mix.wav"], check=True)
    os.remove(D + "tmp_mix.wav"); print("audio : mix avant normalisation", js["input_i"], "LUFS")

# ---------------- plan ----------------
PHR = ("Absolument pas, je viens de vous dire que je pense, et nous pensons, et nous ne changeons pas d'avis là-dessus, "
       "ne vous en déplaise, que c'est immoral d'avoir autant d'argent.")
def build_plan():
    video = []
    for sh in SHOTS:
        v = {"id": sh["id"], "clip": sh["clip"], "folder": "genR11", "path": OUT + sh["clip"], "s": 0, "e": sh["n"], "rec": sh["a"], "dur": sh["n"],
             "clip_fps": FPS, "speed_pct": 100, "track": 1, "note": sh["why"], "kind": sh["kind"], "temps": round(sh["n"] / FPS / T, 2)}
        if sh.get("src"):
            path, sfps, url, off, ctx = SRC[sh["src"]]
            used = sh["n"] / FPS if not sh.get("freeze") else (fr(sh["freeze"]) - sh["a"]) / FPS
            v["source"] = {"fichier": path, "in_s": round(sh["t"], 3), "out_s": round(sh["t"] + used, 3), "fps": sfps, "url": url, "contexte": ctx,
                           "youtube_t": round(off + sh["t"], 2)}
            if sh.get("freeze"): v["source"]["arret_sur_image_timeline_s"] = sh["freeze"]
        if sh.get("screens"):
            v["ecrans"] = [{"fichier": SRC[p[0]][0], "in_s": p[1], "out_s": round(p[1] + sh["n"] / FPS, 2), "cadre_source": p[2], "bichromie": p[7] or "couleur",
                            "url": SRC[p[0]][2]} for p in sh["screens"]]
        if sh["kind"] == "tv":
            v["ecran_principal"] = {"cadre_source": sh["sbox"], "bichromie": sh["duo"], "decoupe": sh["box"], "decoupe_bichromie": sh.get("cutduo") or "couleur"}
        video.append(v)
    texts = []
    for sh in SHOTS:
        for lines, _ in sh.get("boards", []):
            for line in lines: texts.append({"plan": sh["id"], "texte": " ".join(w for w, _ in line)})
        for lines, _ in sh.get("rboards", []): texts.append({"plan": sh["id"], "texte": " ".join(w for line in lines for w, _ in line)})
        for s_, t_, c_ in sh.get("big", []): texts.append({"plan": sh["id"], "texte": s_})
    plan = {"name": "R11 - Collage ransom-note - Danièle Obono", "fps": FPS, "w": W, "h": H, "duree_s": END,
            "note": "Plans ProRes 9:16 composés en Python (lot7/_claude/gen/R11/out) : fonds papier froissé + feuille déchirée, Obono détourée seule "
                    "(instance Vision, tools/inst), double tirage tramé, silhouettes blanches 3 images, plateaux télé en écrans collés (bichromie, "
                    "balayage, scotch), textes ransom-note cuits. s/e en images du clip (30 i/s), rec en images timeline. Coupes sur les frappes réelles "
                    "de Paint The Town Red (out/R11-frappes.json). Aucun ralenti. A4 : arrêt sur image cuit dans le clip. Générateur : lot7/_claude/gen/R11/genR11.py",
            "phrase": {"texte": PHR, "url": SRC["LA"][2], "source": SRC["LA"][0], "in_s": 123.16, "out_s": 130.80, "youtube_s": [1523.16, 1530.80],
                       "timeline_s": [round(t_of_src(123.16), 2), round(t_of_src(130.80), 2)],
                       "voix": "son direct synchro (plans A1-A4, même plan à deux LCI) ; arrêt sur image après « argent » (elle enchaîne « Ce que je dis… », non gardé)"},
            "musique": {"fichier": "lot7/sons/R11-doja-paint-the-town-red_complet.wav", "titre": "Doja Cat - Paint The Town Red", "url": SON_URL,
                        "debut_complet_s": round(MUSIC_IN, 4), "fin_complet_s": round(MUSIC_IN + END, 3), "drop_timeline_s": CUTS[3],
                        "coupes_frappes_s": CUTS, "coupes_images": CUTF},
            "textes": texts, "video": video,
            "audio": [{"id": "mix", "clip": "R11-mix.wav", "folder": "genR11", "path": OUT + "R11-mix.wav", "rec": 0, "track": 1,
                       "note": "mix -14 LUFS : voix LCI %.2f-%.2f s à %.2f s ; Paint The Town Red dès %.3f s du complet, -20 dB sous la voix qui monte à -14, "
                               "« Cause bitch? » à -3 dB juste après la phrase, silence, plein au drop, fondu de fin 0,3 s" % (V_IN, V_OUT, t_of_src(V_IN), MUSIC_IN)}],
            "stems": ["lot7/_claude/gen/R11/out/R11-voix.wav", "lot7/_claude/gen/R11/out/R11-musique.wav"],
            "logos_exclus": "LCI : logo + heure (haut droite) et bandeaux bas hors des cadres, filigrane « Rochebin soir » (haut gauche du plan à deux) exclu ; "
                            "BFMTV : logo (haut gauche) et bandeaux hors cadre"}
    json.dump(plan, open(D + "plan-R11.json", "w"), indent=1, ensure_ascii=False)
    son = {"id": "R11", "titre": "Paint The Town Red", "artiste": "Doja Cat", "url": SON_URL,
           "chaine": "Doja Cat (chaîne officielle, « Provided to YouTube by Kemosabe Records/RCA Records »)",
           "fichier": "lot7/sons/R11-doja-paint-the-town-red_complet.wav",
           "extrait_complet_s": {"debut": round(MUSIC_IN, 4), "fin": round(MUSIC_IN + END, 3)},
           "paroles_audibles": "sous la phrase (baissé) : fin du 3e couplet ; juste après la phrase : « Cause bitch? » puis silence ; "
                               "au drop : 3e refrain « I said what I said… I paint the town red », fin sur « I said what I said »",
           "bpm": 100.0, "temps_s": T,
           "drop": {"complet_s": round(MUSIC_IN + CUTS[3], 4), "timeline_s": CUTS[3], "nature": "1re attaque après le silence, refrain « I said what I said »"},
           "frappes_timeline_s": [round(h[0], 4) for h in HITS if h[1] in ("kick", "caisse") and h[2] >= 0.3], "coupes_sur_frappes_s": CUTS,
           "mix": "lot7/_claude/gen/R11/out/R11-mix.wav"}
    json.dump(son, open(D + "son.json", "w"), indent=1, ensure_ascii=False)

# ---------------- aperçu 540x960 ----------------
def apercu():
    plan = json.load(open(D + "plan-R11.json")); ins = []; fl = []
    for i, v in enumerate(plan["video"]):
        ins += ["-i", OUT + v["clip"]]
        fl.append("[%d:v]trim=start_frame=%d:end_frame=%d,setpts=PTS-STARTPTS,scale=540:960,setsar=1[v%d]" % (i, v["s"], v["e"], i))
    k = len(plan["video"]); fl.append("".join("[v%d]" % i for i in range(k)) + "concat=n=%d:v=1:a=0[v]" % k)
    ins += ["-i", OUT + "R11-mix.wav"]; out = HG + "/preview/apercu-R11.mp4"
    subprocess.run([FF, "-v", "error", "-y"] + ins + ["-filter_complex", ";".join(fl), "-map", "[v]", "-map", "%d:a" % k,
                    "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "aac", "-b:a", "192k", "-shortest", out], check=True)
    print("aperçu", out)
# ---------------- mesure sur l'export : coupes vs frappes, LUFS / TP ----------------
def mesure():
    out = HG + "/preview/apercu-R11.mp4"
    r = subprocess.run([FF, "-v", "info", "-i", out, "-vf", "scale=135:240,select='gt(scene,0.2)',showinfo", "-an", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    cuts = [float(x) for x in re.findall(r"pts_time:([0-9.]+)", r)]
    p = subprocess.run([FF, "-v", "error", "-i", out, "-vn", "-ac", "2", "-ar", "48000", "-f", "f32le", "-"], capture_output=True)
    y = np.frombuffer(p.stdout, np.float32).reshape(-1, 2)
    sr = 48000; worst = 0
    for i, c in enumerate([fr_ / FPS for fr_ in CUTF]):                     # frappes détectées sur une fenêtre de ± 0,3 s de l'export
        det = min(cuts, key=lambda x: abs(x - c)) if cuts else None; a0 = c - 0.3
        pool = [t + a0 for t, b, s_, l in detect_hits(y[int(a0 * sr):int((c + 0.3) * sr)]) if (b == "caisse" or i == 3)]
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
