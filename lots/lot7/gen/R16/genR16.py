# R16 (lot 7) — Collage ransom-note « béton de quartier », David Guiraud, son Heuss L'enfoiré – Moulaga (feat. JuL) (clip officiel).
# Modèle : lot6/_claude/gen/R6/genR6.py (validé, lui-même tiré de lot5 R1) : découpe Vision par instance (tools/inst), double tirage
#   tramé, morceaux de texte penchés serif/sans, bandes déchirées, photos bichromie + scotch, frappes réelles, carton final.
# Poussé pour R16 : fonds en BÉTON (banches, trous de coffrage, pores, coulures) alternés avec des affiches jaune fluo collées ;
#   affiches déchirées qui se recouvrent, scotch toilé gris, trait de bombe jaune fluo derrière la découpe, photos de Roubaix
#   (briques, cités, affiche de campagne, tag « VOTEZ DIMANCHE ») tirées en bichromie fluo / béton.
# Palette R16 (brief) : jaune fluo #E8FF1A + gris béton (#9C9C97 / #5A5C5E / #CFCDC6) + encre noire. Aucune couleur des R1-R6.
# Phrase (son direct, voix off sur des plans où il ne parle pas : au meeting il lit ses notes tête baissée) : « À Roubaix, aucune menace, aucune intimidation ne nous fera reculer » (meeting de Roubaix,
#   31/01/2026, chaîne JEAN-LUC MÉLENCHON, youtu.be/o-1R3UFtXiQ 2944,08-2948,72 s = lot5/sources/V3-guiraud-roubaix-final.mp4 49,08-53,72 s)
#   -> autre phrase que A4 (« cette population devient invincible », 1684 s) et V3 (« on vous empêchera de dormir », 3061 s).
#   Suite « car nous avons dans nos corps… » (54,10 s) non gardée.
# Son : Moulaga, extrait continu ; la phrase passe sur la fin du couplet instrumental (140,4-144,1 s) puis la coupure de basse
#   (144,1-145,9 s) = montée ; drop = retour du kick à 145,94 s sur « En survêt dans l'carré » (le passage des TikToks).
#   Coupes sur les caisses claires réelles (toutes les 2 temps, 125 BPM : 0,96 s).
# Textes après le drop : À ROUBAIX / AUCUNE MENACE / AUCUNE INTIMIDATION / NE NOUS FERA RECULER. (un groupe par plan, dans l'ordre),
#   puis carton final DAVID GUIRAUD + MAIRE DE ROUBAIX (élu le 22/03/2026, 53,19 %).
# Usage : python genR16.py [shots] [audio] [plan] [apercu] [mesure] [only=ID,ID]   (sans argument = tout sauf mesure)
import sys
sys.dont_write_bytecode = True
import os, json, subprocess, math, re
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
HG = "/Users/luca.grousset/Movies/highkey-gauchiste"
D = HG + "/lot7/_claude/gen/R16/"; OUT = D + "out/"; CACHE = D + "cache/"; os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, D)
from hits import detect_hits
sys.path.insert(0, HG + "/_claude/outils"); from decoupe import masques as dmasques, controle, bas_dechire, planche
FF = "/opt/homebrew/bin/ffmpeg"; INST = D + "tools/inst"; FPS = 30; W, H = 1080, 1920
def fr(t): return int(round(t * FPS))
def hexc(h): h = h.lstrip("#"); return np.array([int(h[4:6], 16), int(h[2:4], 16), int(h[0:2], 16)], np.float32) / 255   # BGR
def rgb(h): h = h.lstrip("#"); return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
# palette R16 : jaune fluo, bétons (moyen, sombre, clair), encre, blanc cassé
FLUO, BETON, BETON_D, BETON_L, INK, WHITE = "#E8FF1A", "#9C9C97", "#5A5C5E", "#CFCDC6", "#111214", "#F4F3EE"
PAPER = WHITE; YELLOW = FLUO; BLUE = BETON_D; SKY = BETON_L

# ---------------- sources (lecture seule pour les lots 1-6 ; extraits LCP téléchargés dans lot7/sources) ----------------
LCPU = "https://www.youtube.com/watch?v=I3VFkqdyiHU"; LCPC = "LCP - Assemblée nationale, « La France insoumise : la conquête de Roubaix | En immersion », 26/03/2026"
SRC = {
    "FN": ("lot5/sources/V3-guiraud-roubaix-final.mp4", 30.0, "https://www.youtube.com/watch?v=o-1R3UFtXiQ", 2895.0,
           "meeting de Roubaix, 31/01/2026 (chaîne JEAN-LUC MÉLENCHON)"),
    "EG": ("lot7/sources/R16-guiraud-lcp-eglise.mp4", 25.0, LCPU, 25.0, LCPC + " — Grand-Place, hôtel de ville"),
    "RUE": ("lot7/sources/R16-guiraud-lcp-rue.mp4", 25.0, LCPU, 690.0, LCPC + " — marché, cités en brique"),
    "AFF": ("lot7/sources/R16-guiraud-lcp-affiche.mp4", 25.0, LCPU, 795.0, LCPC + " — réunion publique, affiche de campagne"),
    "BRI": ("lot7/sources/R16-guiraud-lcp-brique.mp4", 25.0, LCPU, 1058.0, LCPC + " — rues de briques"),
    "TAG": ("lot7/sources/R16-guiraud-lcp-tag.mp4", 25.0, LCPU, 1455.0, LCPC + " — militants, tag « Votez dimanche »"),
    "T1": ("lot2/sources/A4-guiraud-roubaix-1ertour.mp4", 30.0, "https://www.youtube.com/watch?v=p8W_23AWUVA", None,
           "soir du 1er tour, 15/03/2026 (chaîne David Guiraud)"),
}

# ---------------- musique : Heuss L'enfoiré – Moulaga (feat. JuL) ----------------
SON_FILE = HG + "/lot7/sons/R16-heuss-moulaga_complet.wav"; SON_URL = "https://www.youtube.com/watch?v=5OAysfkcMjg"
MDROP = 145.9355                     # retour du kick après la coupure de basse, « En survêt dans l'carré »
T = 0.48                             # 125 BPM ; caisses claires toutes les 2 temps (0,96 s)
MUSIC_IN0 = 140.444                  # « À » de la phrase à 0,35 s ; caisses réelles 141,614 / 143,534 juste avant « aucune » / « aucune »
DROP = MDROP - MUSIC_IN0
END = 159.40 - MUSIC_IN0             # fin du passage « en survêt » (coupure de basse à 159,4 s) ; règle lot 7 : 20 s max
SNARES_M = [141.614, 143.534, 147.374, 149.294, 151.214, 153.134, 154.094, 155.054, 156.974]
CUT_T = [s - MUSIC_IN0 for s in SNARES_M[:2]] + [DROP] + [s - MUSIC_IN0 for s in SNARES_M[2:]]
HITS_JSON = OUT + "R16-frappes.json"
def music_raw(mi, dur=None, sr=48000):
    import soundfile as sf
    dur = dur or END + 0.5
    i0 = int(round(mi * sr)); x, r = sf.read(SON_FILE, start=i0, frames=int(dur * sr), dtype="float32"); assert r == sr; return x
def hits_all(mi): return detect_hits(music_raw(mi))
def kicks_of(h): return [x[0] for x in h if x[1] == "kick" and x[3] > 0.3]
def snares_of(h): return [x[0] for x in h if x[1] == "caisse" and x[2] > 0.45]
def snap_list(h, targets):
    ks, cs = kicks_of(h), snares_of(h); out = []
    for i, t in enumerate(targets):
        pool = ks if i == 2 else cs                                         # drop = kick, sinon caisses claires
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
        except AssertionError: continue
        e = max(abs(c - round(c * FPS) / FPS) for c in cuts)
        if e < bad: best, bad, hb = off, e, h
    mi = MUSIC_IN0 + best
    json.dump({"cle": [MUSIC_IN0, END, CUT_T], "music_in": mi, "frappes": hb}, open(HITS_JSON, "w")); return mi, hb
MUSIC_IN, HITS = frappes()
FINE = 0.0                            # recalage fin éventuel mesuré sur l'export AAC
MUSIC_IN += FINE; HITS = [[h[0] - FINE] + list(h[1:]) for h in HITS]
KICKS = kicks_of(HITS); SNARES = snares_of(HITS)
CUTS = snap_list(HITS, CUT_T); CUTF = [fr(c) for c in CUTS]
DROPF = CUTF[2]; TB = 2 * T            # un « temps » de carton = 2 temps (caisse à caisse)

# ---------------- voix ----------------
V_SRC0 = 48.73 + (MUSIC_IN - MUSIC_IN0)   # source FN à t = 0 (« À » 49,08 -> 0,35 s ; « reculer » fin 53,72 -> 4,99 s)
V_IN, V_OUT = 48.95, 53.92            # après « cœur. » (fin 48,20) … « reculer, » (fin 53,72) ; « car » (54,10) non gardé
def t_of_src(s): return s - V_SRC0
WORDS = [("À", 49.08), ("ROUBAIX", 49.22), ("AUCUNE", 49.94), ("MENACE", 50.76), ("AUCUNE", 51.84), ("INTIMIDATION", 52.10),
         ("NE", 52.76), ("NOUS", 52.92), ("FERA", 53.06), ("RECULER", 53.26)]
def wt(i): return t_of_src(WORDS[i][1])
def ln(*idx): return [(WORDS[i][0], wt(i)) for i in idx]

# ---------------- polices ransom-note ----------------
S = "/System/Library/Fonts/Supplemental/"
FONTS = [(S + "Arial Black.ttf", 0), (S + "Georgia Bold.ttf", 0), (S + "Times New Roman Bold.ttf", 0), (S + "Impact.ttf", 0),
         (S + "Courier New Bold.ttf", 0), (S + "Rockwell.ttc", 2), (S + "AmericanTypewriter.ttc", 2), (S + "Didot.ttc", 2),
         (S + "Bodoni 72.ttc", 2), (S + "Futura.ttc", 2)]
FCOND = (S + "Futura.ttc", 4)
STYLES = [(rgb(FLUO), rgb(INK)), (rgb(INK), rgb(FLUO)), (rgb(WHITE), rgb(INK)), (rgb(BETON_D), rgb(FLUO)),
          (rgb(BETON_L), rgb(INK)), (rgb(INK), rgb(WHITE)), (rgb(FLUO), rgb(INK)), ((236, 233, 224), (20, 20, 20))]
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
    weave = 0.05 * np.sin(np.arange(w, dtype=np.float32) * 1.9)[None, :, None] + 0.04 * np.sin(np.arange(h, dtype=np.float32) * 2.3)[:, None, None]
    col = np.array([0.66, 0.67, 0.68], np.float32)[None, None, :] * (1 + weave + 0.05 * rng.standard_normal((h, w, 1)).astype(np.float32))
    return np.dstack([np.clip(col, 0, 1), m * 0.90]).astype(np.float32)
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
_bet = {}
def beton(col):
    """Mur en béton banché : grain, pores, trous de coffrage, joints de banches, coulures et taches."""
    if col not in _bet:
        rng = np.random.default_rng(77 + len(_bet)); y, x = np.mgrid[0:H, 0:W].astype(np.float32)
        lo = cv2.resize(rng.standard_normal((20, 12)).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC)
        mid = cv2.resize(rng.standard_normal((160, 90)).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC)
        fine = cv2.GaussianBlur(rng.standard_normal((H, W)).astype(np.float32), (0, 0), 0.8)
        v = 1 + 0.07 * lo + 0.04 * mid + 0.06 * fine
        pores = np.zeros((H, W), np.float32)
        for _ in range(1400):
            cv2.circle(pores, (int(rng.uniform(0, W)), int(rng.uniform(0, H))), int(rng.integers(1, 4)), float(rng.uniform(0.3, 1.0)), -1, cv2.LINE_AA)
        v -= 0.30 * cv2.GaussianBlur(pores, (0, 0), 0.7)
        for yy in (430, 1010, 1590):                                         # joints de banches + trous de coffrage
            v -= 0.10 * np.exp(-((y - yy - 4 * np.sin(x / 90)) / 3.0) ** 2); v += 0.05 * np.exp(-((y - yy - 7) / 4.0) ** 2)
            for xx in (150, 540, 930):
                hole = np.exp(-(((x - xx) ** 2 + (y - yy + 230) ** 2) / (2 * 15.0 ** 2)))
                v -= 0.45 * hole; v += 0.10 * np.exp(-(((x - xx - 6) ** 2 + (y - yy + 236) ** 2) / (2 * 22.0 ** 2))) * (1 - hole)
        for _ in range(9):                                                   # coulures sombres verticales
            cx = rng.uniform(0, W); y0 = rng.uniform(0, H * 0.7); ln_ = rng.uniform(200, 700); wd = rng.uniform(6, 22)
            v -= 0.08 * np.exp(-((x - cx) / wd) ** 2) * np.clip((y - y0) / 40, 0, 1) * np.clip(1 - (y - y0) / ln_, 0, 1)
        _bet[col] = np.clip(hexc(col)[None, None, :] * v[..., None], 0, 1).astype(np.float32)
    return _bet[col].copy()
def bgimg(col): return beton(col) if col in (BETON, BETON_D, BETON_L) else paper(col)
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
        col = bgimg(colhex); white = np.clip(np.ones_like(col) * 0.96 * folds(), 0, 1)       # fibres blanches au bord déchiré
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
DUO = {"fluo": (INK, FLUO), "beton": ("#26282A", "#E2E0D8"), "betfluo": (BETON_D, FLUO), "encre": (INK, BETON_L)}
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
STRIP_COLS = [FLUO, WHITE, BETON_D, BETON_L, INK, FLUO, WHITE, BETON_D]
def strip_rgba(w, h, rng, colhex, ht=False):
    col = hexc(colhex); dot = hexc(INK if colhex in (FLUO, WHITE, BETON_L) else FLUO)
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
    """Temps : caisses claires réelles + kick du drop + kicks réels à mi-chemin (temps 1 de chaque groupe de 2 temps)."""
    g = list(SNARES) + [CUTS[2]]
    for s_ in SNARES:
        k = [x for x in KICKS if abs(x - (s_ - T)) < 0.03]
        if k: g.append(k[0])
    return sorted(set(round(x, 4) for x in g if 0 < x < END))
BEATS = beat_grid(); BEATF = [fr(b) for b in BEATS]
def nbeat(f): return sum(1 for b in BEATF if b <= f)
def jit(key, k, amp=8.0, ang=1.5):
    r = np.random.default_rng(skey(key) * 1000 + k); return r.uniform(-amp, amp), r.uniform(-amp, amp), r.uniform(-ang, ang)

# ---------------- plans ----------------
FNBOX = (450, 0, 1550, 750)           # meeting, plan de face : pupitre « MEETING ROUBAIX » (y > 754) et logo LFI (x > 1690) hors fenêtre
FNPT = (0.49, 0.77)                   # point sur sa poitrine
PH = (300, 140, 1920, 1000)           # photos LCP : logo LCP (haut gauche) et pastille « en immersion » (bas gauche, x < 270) hors cadre
POSTER = (1210, 60, 1850, 620)        # affiche de campagne « FIERS DE ROUBAIX ! avec DAVID » (entrée de la réunion publique)
GRAF = (420, 40, 1920, 1000)          # tag « VOTEZ DIMANCHE de 8h à 18h » sur un mur de briques, caddie
MILIT = (300, 60, 1500, 1000)         # militants avec le tract, Guiraud au centre
SALLE = (0, 150, 1680, 1080)          # salle du meeting debout (logo LFI en haut à droite hors cadre)
KEYL = ("MENACE", "RECULER")
SHOTS = [
    dict(id="A1", kind="collage", bg=BETON, sheet=(FLUO, "bas", 0.86, -4, 1), spray=True,
         boards=[([ln(0, 1)], None)], txt_h=200, strips=3,
         photos=[("FN", 70.5, SALLE, 780, (540, 900), -3, 0.0, "fluo"), ("RUE", 33.0, PH, 560, (520, 1480), 5, 0.0, "beton")],
         why="voix sur la salle du meeting debout (plan où il ne parle pas) : « À Roubaix, », mur de béton, trait de bombe fluo, cité en brique"),
    dict(id="A2", kind="cut", src="BRI", t=0.3, bg=FLUO, sheet=(BETON_L, "haut", 0.11, 3, 2), ghost=INK, box=(300, 0, 1500, 1080), pt=(0.42, 0.65),
         scale=(1.24, 1.28), cx=908,
         boards=[([ln(2), ln(3)], None)], txt_h=175, strips=4,
         photos=[("TAG", 10.5, GRAF, 560, (540, 1000), 5, 0.0, "encre")],
         why="voix sur un plan où il ne parle pas : « aucune menace, », il marche en souriant dans une rue de briques (LCP), tag « VOTEZ DIMANCHE » collé derrière"),
    dict(id="A3", kind="collage", bg=BETON_D, sheet=(FLUO, "bas", 0.86, 5, 3),
         boards=[([ln(4), ln(5)], None), ([ln(6, 7), ln(8, 9)], wt(6))], txt_h=150, strips=5,
         photos=[("AFF", 0.3, POSTER, 560, (540, 980), -4, 0.0, "fluo"), ("TAG", 3.5, MILIT, 560, (540, 1290), 5, wt(6), "beton"),
                 ("RUE", 73.5, PH, 620, (520, 1680), -4, wt(8), "encre")],
         why="voix sur son affiche de campagne puis les militants au tract (plans où il ne parle pas) : « aucune intimidation ne nous fera reculer »"),
    dict(id="B1", kind="sil", src="TAG", t=0.0, bg=FLUO, ghost=INK, box=(0, 0, 1500, 1080), pt=(0.58, 0.79), dest_w=1750, cx=866, push=(1.0, 1.04),
         rboards=[([[("À", 0.0), ("ROUBAIX", 0.0)]], 0.0)], txt_y=330, txt_h=170, strips=3, flash=True, spray=True,
         photos=[("RUE", 48.0, PH, 600, (300, 1050), -6, 0.0, "beton")],
         why="dans la rue au marché, blouson (LCP) : silhouette blanche 3 images (flash du drop) puis Guiraud en couleur, contour autocollant, double tirage noir"),
    dict(id="B2", kind="collage", bg=BETON,
         photos=[("RUE", 47.0, PH, 680, (520, 830), -4, 0.0, "fluo"), ("BRI", 6.0, PH, 640, (600, 1250), 5, T, "beton"),
                 ("EG", 23.0, PH, 600, (430, 1640), -3, 2 * T, "fluo")],
         rboards=[([[("AUCUNE", 0.0)], [("MENACE", 0.0)]], 0.0)], txt_y=300, letters=("MENACE",), txt_h=170, strips=4,
         why="collage sur béton : cités en brique, rue de Roubaix, hôtel de ville, une photo par temps"),
    dict(id="B3", kind="cut", src="RUE", t=12.0, bg=BETON_L, sheet=(FLUO, "bas", 0.76, -5, 4), ghost=INK, box=(0, 0, 1920, 1080), pt=(0.57, 0.8),
         scale=(1.17, 1.21), cx=1118,
         photos=[("EG", 27.0, PH, 600, (520, 860), 4, 0.0, "betfluo")],
         rboards=[([[("AUCUNE", 0.0)], [("INTIMIDATION", 0.0)]], 0.0)], txt_y=300, txt_h=150, strips=3,
         why="au marché, devant les briques (LCP) : détouré sur béton clair + feuille fluo déchirée, Grand-Place derrière"),
    dict(id="B4", kind="collage", bg=FLUO, sheet=(BETON, "bas", 0.82, 4, 5),
         photos=[("TAG", 4.5, MILIT, 700, (540, 940), -3, 0.0, "beton"), ("TAG", 11.5, GRAF, 520, (540, 1300), 5, T, "encre"),
                 ("FN", 72.5, SALLE, 620, (520, 1680), -4, 2 * T, "betfluo")],
         rboards=[([[("NE", 0.0), ("NOUS", 0.0)], [("FERA", 0.0)], [("RECULER.", 0.0)]], 0.0)], txt_y=290, letters=("RECULER.",), txt_h=140, strips=3, flash2=True,
         why="collage sur affiche fluo : militants au tract autour de lui, tag « VOTEZ DIMANCHE », salle debout"),
    dict(id="B5", kind="collage", bg=BETON_D,
         photos=[("EG", 24.0, PH, 740, (540, 700), -3, 0.0, "fluo"), ("RUE", 52.0, PH, 600, (560, 1200), 5, 0.5 * T, "beton")],
         strips=3,
         why="collage au demi-temps : hôtel de ville, façades de briques"),
    dict(id="B6", kind="cut", src="AFF", t=9.4, bg=BETON, ghost=FLUO, box=(500, 0, 1560, 1080), pt=(0.61, 0.6), scale=(1.23, 1.26), cx=1150, spray=True,
         photos=[("AFF", 0.3, POSTER, 520, (420, 950), -6, 0.0, "betfluo")], strips=3,
         why="réunion publique de quartier, de profil avant de prendre le micro (LCP) : détouré sur béton, son affiche derrière"),
    dict(id="B7", kind="collage", bg=FLUO, sheet=(BETON_L, "haut", 0.14, -3, 6),
         photos=[("FN", 73.5, SALLE, 740, (540, 760), 4, 0.0, "beton"), ("TAG", 5.0, MILIT, 600, (540, 1200), -5, T, "fluo"),
                 ("BRI", 10.0, PH, 600, (560, 1640), 3, 2 * T, "encre")],
         strips=4,
         why="collage final avant le carton : la salle debout, les militants au tract, une rue de briques"),
    dict(id="FIN", kind="card", bg=FLUO, sheet=(BETON, "bas", 0.83, -3, 7), push=(1.0, 1.035),
         big=[("DAVID", 0.0, rgb(INK)), ("GUIRAUD", T, rgb(INK))], big_y=520, big_sizes=[300, 380],
         rboards=[([[("MAIRE", 0.0), ("DE", 0.0), ("ROUBAIX", 0.0)]], 2 * T)], txt_y=1130, txt_h=110,
         why="carton final : son nom en grand sur affiche fluo + MAIRE DE ROUBAIX en lettres découpées (élu le 22/03/2026)"),
]
BOUNDS_T = [0] + CUTF + [fr(END)]
assert len(BOUNDS_T) == len(SHOTS) + 1, (len(BOUNDS_T), len(SHOTS))
for i, sh in enumerate(SHOTS):
    sh["a"], sh["bb"] = BOUNDS_T[i], BOUNDS_T[i + 1]; sh["n"] = sh["bb"] - sh["a"]; sh["clip"] = "R16_%s.mov" % sh["id"]
    if sh.get("src") == "FN" and sh["t"] is None: sh["t"] = V_SRC0 + sh["a"] / FPS          # plans A synchro avec la voix
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
_spr = {}
def spray_on(img, seed):
    """Trait de bombe jaune fluo sur le mur (gribouillis épais, bord poudré, postillons, coulures), posé avant les affiches."""
    if seed not in _spr:
        rng = np.random.default_rng(seed); m = np.zeros((H, W), np.float32)
        y0 = rng.uniform(820, 1150); pts = []
        for k in range(7):
            pts.append((int(-60 + k * 200 + rng.uniform(-30, 30)), int(y0 + (1 if k % 2 else -1) * rng.uniform(80, 200))))
        cv2.polylines(m, [np.array(pts, np.int32)], False, 1.0, int(rng.uniform(55, 80)), cv2.LINE_AA)
        core = cv2.GaussianBlur(m, (0, 0), 5); halo = cv2.GaussianBlur(m, (0, 0), 26)
        dots = (rng.random((H, W)) < 0.012 * np.clip(halo * 3, 0, 1)).astype(np.float32)
        a = np.clip(core * 1.1 + 0.35 * cv2.GaussianBlur(dots, (0, 0), 0.8) * 3, 0, 0.92)
        for _ in range(6):                                                  # coulures sous le trait
            x = int(rng.uniform(40, W - 40)); ys = np.where(core[:, x] > 0.5)[0]
            if len(ys): cv2.line(a, (x, int(ys.max())), (x, int(ys.max() + rng.uniform(60, 260))), 0.8, int(rng.integers(5, 10)), cv2.LINE_AA)
        _spr[seed] = cv2.GaussianBlur(a, (0, 0), 1.0)[..., None]
    a = _spr[seed]; img[:] = img * (1 - a) + hexc(FLUO)[None, None, :] * a
CARD_TAPES = [tape_rgba(170, 46, np.random.default_rng(40 + j)) for j in range(4)]
CTRL = {}
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
    photos = [Photo([read_frames(ps, pt, 1)[0]] * n if pbox == POSTER else read_frames(ps, pt, n), pbox, pw, pc, pa, fr(rel(pt0)) if pt0 > 0 or sh["id"].startswith("B") else a, (sh["id"], j), duo)
              for j, (ps, pt, pbox, pw, pc, pa, pt0, duo) in enumerate(sh.get("photos", []))]
    if sh["id"].startswith("A"):                                             # plans A : apparition au temps absolu du mot
        for ph, spec in zip(photos, sh.get("photos", [])): ph.f0 = max(a, fr(spec[6])) if spec[6] > 0 else a
    strips = make_strips(sh)
    k0 = nbeat(a); tear = None
    if False:                                                       # bas de la découpe = bord de papier déchiré net (au-dessus des micros)
        bx0, by0, bx1, by1 = sh["box"]; hh_, ww_ = by1 - by0, bx1 - bx0; trng = np.random.default_rng(skey(sh["id"]) + 9)
        xs = np.arange(0, ww_ + 12, 12); ys = hh_ - 16 + trng.uniform(-9, 9, len(xs)) + 5 * np.sin(xs / 41.0)
        prof = np.interp(np.arange(ww_), xs, ys)
        tear = (np.arange(hh_)[:, None] < prof[None, :]).astype(np.float32)
        tear = cv2.GaussianBlur(tear, (0, 0), 0.8)
    if sh["kind"] in ("cut", "sil"):
        raw = read_frames(sh["src"], sh["t"], n)
        key = "%s_%s_%.2f_%d" % (sh["id"], sh["src"], sh["t"], n)
        ms = dmasques(raw, sh["box"], sh["pt"], CACHE + "dec/" + key)            # outil partagé : la personne seule (sans micro, pupitre, voisin)
        if sh.get("tear"): ms = [bas_dechire(m_, seed=skey(sh["id"])) for m_ in ms]   # buste coupé au-dessus des micros -> bord de papier déchiré
        cs = [controle(m_) for m_ in ms]
        worst = {k_: max(c[k_] for c in cs) for k_ in ("gauche", "droite", "haut", "bas", "bas_net", "morceaux")}
        CTRL[sh["id"]] = worst; print("  contrôle découpe", sh["id"], worst, flush=True)
        os.makedirs(CACHE + "planches", exist_ok=True); planche(raw, ms, sh["box"], CACHE + "planches/%s.jpg" % sh["id"])
    for i in range(n):
        f = a + i; u = i / max(n - 1, 1); kb = nbeat(f) - k0
        img = bgimg(sh["bg"])
        if sh.get("spray"): spray_on(img, skey(sh["id"]))
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
            x0, y0, x1, y1 = sh["box"]; m = ms[i] * tear if tear is not None else ms[i]
            if sh["kind"] == "cut":
                sc = sh["scale"][0] + (sh["scale"][1] - sh["scale"][0]) * u; hh = (y1 - y0) * sc
                ccx = W / 2 + ((x1 - x0) / 2 - (sh["cx"] - x0)) * sc; ccy = sh.get("bot", H) - hh / 2; r_ = 7
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
    v = grab(HG + "/" + SRC["FN"][0], V_IN, V_OUT - V_IN); env = np.ones(len(v), np.float32)
    k = int(0.03 * sr); env[:k] = np.linspace(0, 1, k); k = int(0.08 * sr); env[-k:] = np.linspace(1, 0, k)
    i0 = int(round(t_of_src(V_IN) * sr)); voix[i0:i0 + len(v)] = v * env[:, None] * 10 ** (VGAIN / 20)
    m = music_raw(MUSIC_IN)[:N]
    t = np.arange(len(m)) / sr; vend = t_of_src(V_OUT); dr = CUTS[2]
    # sous la phrase : fin du couplet instrumental baissée, montée progressive (coupure de basse), plein sur le drop « En survêt »
    gdb = np.interp(t, [0, 0.25, vend - 0.8, vend, dr - 0.03, dr, END], [-23, -20, -15, -10, -5, 0, 0])
    k = int(0.40 * sr); fo = np.ones(len(m), np.float32); fo[-k:] = np.linspace(1, 0, k)
    mus[:len(m)] = m * (10 ** (gdb / 20) * fo)[:, None]
    sf.write(OUT + "R16-voix.wav", voix, sr, subtype="PCM_24"); sf.write(OUT + "R16-musique.wav", mus, sr, subtype="PCM_24")
    sf.write(D + "tmp_mix.wav", voix + mus, sr, subtype="FLOAT")
    r = subprocess.run([FF, "-hide_banner", "-i", D + "tmp_mix.wav", "-af", "loudnorm=I=-14:TP=-2.5:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    js = json.loads(r[r.rindex("{"):r.rindex("}") + 1])
    af = ("loudnorm=I=-14:TP=-2.5:LRA=11:measured_I=%s:measured_TP=%s:measured_LRA=%s:measured_thresh=%s:offset=%s:linear=true,"
          "aresample=48000" % (js["input_i"], js["input_tp"], js["input_lra"], js["input_thresh"], js["target_offset"]))
    subprocess.run([FF, "-v", "error", "-y", "-i", D + "tmp_mix.wav", "-af", af, "-c:a", "pcm_s24le", OUT + "R16-mix.wav"], check=True)
    os.remove(D + "tmp_mix.wav"); print("audio : mix avant normalisation", js["input_i"], "LUFS")
VGAIN = 4.0

# ---------------- plan ----------------
PHR = "À Roubaix, aucune menace, aucune intimidation ne nous fera reculer"
PAROLES = ("sous la phrase (baissé) : fin de la partie instrumentale du morceau (140,4-144,1 s, sans paroles) puis coupure de basse ; "
           "au drop : « En survêt dans l'carré… » (4 lignes, 145,7-159,4 s)")
def build_plan():
    video = []
    for sh in SHOTS:
        v = {"id": sh["id"], "clip": sh["clip"], "folder": "genR16", "path": OUT + sh["clip"], "s": 0, "e": sh["n"], "rec": sh["a"], "dur": sh["n"],
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
            texts.append({"plan": sh["id"], "texte": " / ".join(" ".join(w for w, _ in line) for line in lines)})
        for lines, _ in sh.get("rboards", []): texts.append({"plan": sh["id"], "texte": " ".join(w for line in lines for w, _ in line)})
        for s_, t_, c_ in sh.get("big", []): texts.append({"plan": sh["id"], "texte": s_})
    plan = {"name": "R16 - Collage ransom-note béton - David Guiraud", "fps": FPS, "w": W, "h": H, "duree_s": round(END, 3),
            "note": "Plans ProRes 9:16 composés en Python (lot7/_claude/gen/R16/out) : murs de béton banché / affiches jaune fluo, feuilles déchirées, "
                    "Guiraud détouré seul (instance Vision, tools/inst), double tirage tramé, trait de bombe fluo, silhouettes blanches 3 images, "
                    "photos vivantes en bichromie + scotch toilé, textes ransom-note cuits. s/e en images du clip (30 i/s), rec en images timeline. "
                    "Coupes sur les caisses claires réelles de Moulaga (out/R16-frappes.json). Aucun ralenti. Générateur : lot7/_claude/gen/R16/genR16.py",
            "phrase": {"texte": PHR, "url": SRC["FN"][2], "source": SRC["FN"][0], "in_s": 49.08, "out_s": 53.72, "youtube_s": [2944.08, 2948.72],
                       "timeline_s": [round(t_of_src(49.08), 2), round(t_of_src(53.72), 2)],
                       "voix": "voix off sur des plans où il ne parle pas (A1 salle debout, A2 il marche dans une rue de briques, A3 son affiche et ses militants) : au meeting il lit ses notes tête baissée sur ce passage (règle Luca) ; suite « car nous avons dans nos corps… » (54,10 s) non gardée"},
            "musique": {"fichier": "lot7/sons/R16-heuss-moulaga_complet.wav", "titre": "Heuss L'enfoiré - Moulaga (feat. JuL)", "url": SON_URL,
                        "debut_complet_s": round(MUSIC_IN, 4), "fin_complet_s": round(MUSIC_IN + END, 3), "drop_timeline_s": CUTS[2],
                        "coupes_frappes_s": CUTS, "coupes_images": CUTF},
            "textes": texts, "video": video,
            "audio": [{"id": "mix", "clip": "R16-mix.wav", "folder": "genR16", "path": OUT + "R16-mix.wav", "rec": 0, "track": 1,
                       "note": "mix -14 LUFS : voix meeting %.2f-%.2f s (+%.0f dB) à %.2f s ; Moulaga dès %.3f s du complet, -20 dB sous la voix, montée, plein au drop, fondu de fin 0,4 s"
                               % (V_IN, V_OUT, VGAIN, t_of_src(V_IN), MUSIC_IN)}],
            "stems": ["lot7/_claude/gen/R16/out/R16-voix.wav", "lot7/_claude/gen/R16/out/R16-musique.wav"],
            "logos_exclus": "meeting : logo LFI et pupitre hors fenêtre du détourage ; LCP : logo LCP et pastille « en immersion » hors des cadres photo, "
                            "détourages = la personne seule ; 1er tour : bonnettes de micros tenues par d'autres hors de l'instance détourée"}
    json.dump(plan, open(D + "plan-R16.json", "w"), indent=1, ensure_ascii=False)
    son = {"id": "R16", "titre": "Moulaga (feat. JuL)", "artiste": "Heuss L'enfoiré", "url": SON_URL,
           "chaine": "Heuss L'Enfoiré (chaîne officielle de l'artiste, « Heuss L'enfoiré (ft. JuL) - Moulaga (Clip Officiel) »)",
           "fichier": "lot7/sons/R16-heuss-moulaga_complet.wav",
           "extrait_complet_s": {"debut": round(MUSIC_IN, 4), "fin": round(MUSIC_IN + END, 3)},
           "paroles_audibles": PAROLES, "bpm": 125.0, "temps_s": T,
           "drop": {"complet_s": round(MUSIC_IN + CUTS[2], 4), "timeline_s": CUTS[2], "nature": "retour du kick après la coupure de basse, « En survêt dans l'carré »"},
           "frappes_timeline_s": [round(k, 4) for k in BEATS], "coupes_sur_frappes_s": CUTS,
           "mix": "lot7/_claude/gen/R16/out/R16-mix.wav"}
    json.dump(son, open(D + "son.json", "w"), indent=1, ensure_ascii=False)

# ---------------- aperçu 540x960 ----------------
def apercu():
    plan = json.load(open(D + "plan-R16.json")); ins = []; fl = []
    for i, v in enumerate(plan["video"]):
        ins += ["-i", OUT + v["clip"]]
        fl.append("[%d:v]trim=start_frame=%d:end_frame=%d,setpts=PTS-STARTPTS,scale=540:960,setsar=1[v%d]" % (i, v["s"], v["e"], i))
    k = len(plan["video"]); fl.append("".join("[v%d]" % i for i in range(k)) + "concat=n=%d:v=1:a=0[v]" % k)
    ins += ["-i", OUT + "R16-mix.wav"]; out = HG + "/preview/apercu-R16.mp4"
    subprocess.run([FF, "-v", "error", "-y"] + ins + ["-filter_complex", ";".join(fl), "-map", "[v]", "-map", "%d:a" % k,
                    "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "aac", "-b:a", "192k", "-shortest", out], check=True)
    print("aperçu", out)
# ---------------- mesure sur l'export : coupes vs frappes, LUFS / TP ----------------
def mesure():
    out = HG + "/preview/apercu-R16.mp4"
    r = subprocess.run([FF, "-v", "info", "-i", out, "-vf", "scale=135:240,select='gt(scene,0.2)',showinfo", "-an", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    cuts = [float(x) for x in re.findall(r"pts_time:([0-9.]+)", r)]
    p = subprocess.run([FF, "-v", "error", "-i", out, "-vn", "-ac", "2", "-ar", "48000", "-f", "f32le", "-"], capture_output=True)
    y = np.frombuffer(p.stdout, np.float32).reshape(-1, 2)
    sr = 48000; nd = int((CUTS[2] - 0.2) * sr)
    hh = [x for x in detect_hits(y) if x[0] >= CUTS[2] - 0.2] + detect_hits(y[:nd])      # avant le drop : musique baissée, détection à part
    worst = 0
    for i, c in enumerate([fr_ / FPS for fr_ in CUTF]):
        det = min(cuts, key=lambda x: abs(x - c)) if cuts else None
        pool = [x[0] for x in hh if x[1] == ("kick" if i == 2 else "caisse")]                # coupes sur caisses claires, drop sur le kick
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
