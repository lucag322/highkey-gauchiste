# R10 (lot 7) — Collage ransom-note « grande silhouette + lettres de magazine », Rima Hassan, son George Michael – Freedom! '90.
# Modèle : lot6/_claude/gen/R6/genR6.py (validé, même mécanique : découpe Vision par instance, morceaux de texte penchés serif/sans,
#   double tirage tramé, photos bord déchiré + scotch, bandes, une couche de plus par temps, flash blanc 3 images au drop, carton final nom seul).
# Palette R10 (brief) : NOIR ET BLANC + UN SEUL ACCENT VERT (#00A651) — papier blanc / gris clair, découpes et photos en N&B,
#   le vert seulement sur le mot-clé de chaque carton (lettres de magazine), le double tirage tramé et une bande. Aucune couleur des R1-R6.
# Poussé : grande silhouette N&B qui monte du bas du cadre (pupitre exclu), mots-clés en lettres de magazine découpées une à une,
#   papier froissé + colonnes de magazine + feuilles déchirées, trame d'imprimerie, scotch, photos N&B vivantes qui sautent sur les temps.
# Phrase (son direct, synchro) : « Non, il n'y a pas de neutralité à avoir face au génocide, face au colonialisme, face au fascisme. »
#   (meeting « Justice pour la Palestine », Strasbourg, 17/06/2026, chaîne La France insoumise, youtu.be/lML9ZGssEac 2303,3-2311,5 s ;
#   extrait lot7/sources/R10-hassan-strasbourg-neutralite.mp4 = YouTube 2290-2326 s, phrase 13,32-21,50 s)
#   -> autre phrase que A7 (« Être de gauche, ce n'est pas une étiquette », 2293-2296 s) et C6 (« Quand un pouvoir commence à confondre… », 2384 s).
# Son : Freedom! '90 (Remastered, chaîne George Michael, « Provided to YouTube »), extrait continu 126,4-146,0 s : sous la phrase, le
#   pré-refrain baissé qui monte (« All we have to see / Is that I don't belong to you / And you don't belong to me ») ;
#   drop = attaque du 1er temps du refrain « Freedom! » (135,608 s), puis « I won't let you down / Freedom… / You gotta give for what you take ».
# Textes après le drop (règle Luca 27/10) : un groupe complet par plan, dans l'ordre de la phrase : PAS DE NEUTRALITÉ. / FACE AU GÉNOCIDE, /
#   FACE AU COLONIALISME, / FACE AU FASCISME. puis carton final RIMA HASSAN (nom seul).
# Usage : python genR10.py [shots] [audio] [plan] [apercu] [mesure] [only=ID,ID]   (sans argument = tout sauf mesure)
import sys
sys.dont_write_bytecode = True
import os, json, subprocess, math, re
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
HG = "/Users/luca.grousset/Movies/highkey-gauchiste"
D = HG + "/lot7/_claude/gen/R10/"; OUT = D + "out/"; CACHE = D + "cache/"; os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, D)
from hits import detect_hits
sys.path.insert(0, D + "tools"); from mic import mic_mask, clean as mic_clean, trim as mic_trim
sys.path.insert(0, HG + "/_claude/outils"); from decoupe import masques as dmasques, controle as dcontrole, planche as dplanche   # outil partagé obligatoire
FF = "/opt/homebrew/bin/ffmpeg"; INST = D + "tools/inst"; FPS = 30; W, H = 1080, 1920
def fr(t): return int(round(t * FPS))
def hexc(h): h = h.lstrip("#"); return np.array([int(h[4:6], 16), int(h[2:4], 16), int(h[0:2], 16)], np.float32) / 255   # BGR
def rgb(h): h = h.lstrip("#"); return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
# palette R10 : noir, blancs, gris + un seul accent vert
GREEN, INK, WHITE, PAPER, LGREY, MGREY, DGREY = "#00A651", "#121212", "#FFFFFF", "#F1EFEA", "#D8D6D1", "#9A9893", "#3A3A3A"

# ---------------- sources ----------------
SRC = {
    "PH": ("lot7/sources/R10-hassan-strasbourg-neutralite.mp4", 30.0, "https://www.youtube.com/watch?v=lML9ZGssEac", 2290.0,
           "meeting Justice pour la Palestine, Strasbourg, 17/06/2026 (chaîne La France insoumise) — plan de la phrase"),
    "SB": ("lot3/sources/A7-hassan-strasbourg-b.mp4", 30.0, "https://www.youtube.com/watch?v=lML9ZGssEac", 2368.0,
           "même meeting, Strasbourg 17/06/2026 (chaîne La France insoumise)"),
    "SC": ("lot3/sources/A7-hassan-strasbourg-c.mp4", 30.0, "https://www.youtube.com/watch?v=lML9ZGssEac", 2634.0,
           "même meeting, fin du discours, Strasbourg 17/06/2026 (chaîne La France insoumise)"),
    "SA": ("lot3/sources/A7-hassan-strasbourg-a.mp4", 30.0, "https://www.youtube.com/watch?v=lML9ZGssEac", 2195.0,
           "même meeting, Strasbourg 17/06/2026 (chaîne La France insoumise)"),
    "CO": ("lot3/sources/A7-hassan-courneuve-a.mp4", 30.0, "https://www.youtube.com/watch?v=bpYEswmz7us", 925.0,
           "meeting des municipales de La Courneuve, 16/01/2026"),
}

# ---------------- musique : George Michael – Freedom! '90 ----------------
SON_FILE = HG + "/lot7/sons/R10-freedom90_complet.wav"; SON_URL = "https://www.youtube.com/watch?v=FaEjDk3lgcI"
T = 0.6543                                # 91,7 BPM (grille ajustée sur 120-150 s)
PB = (0, 190, 1600, 1080)                 # cadre des photos de Strasbourg : logo ELA (haut droite) et plafond exclus
PW = (0, 300, 1350, 1080)                 # plans larges de la salle (PH 25-30,9 s) : scène et bannières ELA (à droite) exclues
# frappes réelles (hits.py sur le morceau complet) choisies pour les coupes : 1ers temps des mesures sous la phrase (caisse + accord),
# Sous la phrase : 1ers et 3es temps de mesure réels (caisse/kick + accord) choisis pour alterner les moments où elle regarde la salle
# (plan synchro) et ceux où elle lit ses notes (remplacés par la salle, sans parole) ; 133,969 et 134,797 = attaques réelles hors grille.
# Drop = attaque kick + caisse du 1er temps du refrain « Freedom! » (135,608), puis attaques réelles 136,932 / 138,232 / 139,519 / 140,840 / 143,469.
CUT_SONG = [127.7589, 129.0830, 130.3756, 132.9947, 133.9690, 134.7969, 135.6078, 136.9320, 138.2319, 139.5188, 140.8404, 143.4690]
IDROP = 6
MDROP = CUT_SONG[IDROP]
def _best_in(base=126.41):
    best = None
    for off in np.arange(-0.016, 0.0165, 0.0005):
        e = max(abs((c - base - off) - round((c - base - off) * FPS) / FPS) for c in CUT_SONG)
        if best is None or e < best[0]: best = (e, base + off)
    return best[1]
MUSIC_IN = round(_best_in(), 4)          # début de l'extrait dans le morceau complet
CUTS = [c - MUSIC_IN for c in CUT_SONG]; CUTF = [fr(c) for c in CUTS]
DROP = CUTS[IDROP]; DROPF = CUTF[IDROP]; TB = T
END = round(146.03 - MUSIC_IN, 3)        # fin après « You gotta give for what you take » (take 145,0-146,0), avant le « Freedom! » suivant (146,68)
def music_raw(mi, dur=None, sr=48000):
    import soundfile as sf
    dur = dur or END + 0.5
    i0 = int(round(mi * sr)); x, r = sf.read(SON_FILE, start=i0, frames=int(dur * sr), dtype="float32"); assert r == sr; return x
HITS = detect_hits(music_raw(MUSIC_IN))

# ---------------- voix ----------------
V_SRC0 = 14.08 - CUTS[0]                 # 1re coupe juste avant « il » (14,24) ; timeline = source PH - V_SRC0
V_IN, V_OUT = 13.22, 21.62               # « Non » 13,32 … « fascisme » fin 21,50 (silence avant et après)
def t_of_src(s): return s - V_SRC0
WORDS = [("NON,", 13.32), ("IL", 14.24), ("N'Y", 14.64), ("A", 14.86), ("PAS", 14.92), ("DE", 15.20), ("NEUTRALITÉ", 15.80),
         ("À", 16.74), ("AVOIR", 17.24), ("FACE", 17.64), ("AU", 18.20), ("GÉNOCIDE,", 18.32),
         ("FACE", 19.14), ("AU", 19.44), ("COLONIALISME,", 19.60), ("FACE", 20.66), ("AU", 20.86), ("FASCISME.", 20.96)]
def wt(i): return t_of_src(WORDS[i][1])
def ln(*idx): return [(WORDS[i][0], wt(i)) for i in idx]

# ---------------- polices ransom-note ----------------
S = "/System/Library/Fonts/Supplemental/"
FONTS = [(S + "Arial Black.ttf", 0), (S + "Georgia Bold.ttf", 0), (S + "Times New Roman Bold.ttf", 0), (S + "Impact.ttf", 0),
         (S + "Courier New Bold.ttf", 0), (S + "Rockwell.ttc", 2), (S + "AmericanTypewriter.ttc", 2), (S + "Didot.ttc", 2),
         (S + "Bodoni 72.ttc", 2), (S + "Futura.ttc", 2)]
STYLES = [(rgb(PAPER), rgb(INK)), (rgb(INK), (255, 255, 255)), ((255, 255, 255), rgb(INK)), (rgb(LGREY), rgb(INK)),
          (rgb(DGREY), (255, 255, 255)), ((236, 233, 224), (20, 20, 20)), (rgb(MGREY), rgb(INK))]
LFONTS = [(S + "Impact.ttf", 0), (S + "Futura.ttc", 4), (S + "Arial Narrow Bold.ttf", 0), (S + "DIN Condensed Bold.ttf", 0),
          (S + "AmericanTypewriter.ttc", 5), (S + "Bodoni 72.ttc", 2), (S + "Didot.ttc", 2), (S + "Times New Roman Bold.ttf", 0)]   # lettres de magazine (étroites + serifs)
ACCENT = [(rgb(GREEN), (255, 255, 255)), ((255, 255, 255), rgb(GREEN)), (rgb(GREEN), rgb(INK)), (rgb(INK), rgb(GREEN))]
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
    col = np.array([0.86, 0.87, 0.86], np.float32)[None, None, :] * (1 + 0.04 * rng.standard_normal((h, w, 1)).astype(np.float32))
    return np.dstack([col, m * 0.70]).astype(np.float32)
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
    px, py = int(h * (0.05 if len(txt) == 1 else 0.16)), int(h * 0.10)
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
XMIN, XMAX, YMIN, YMAX = 0.18 * W, 0.82 * W, 0.13 * H, 0.74 * H          # zone sûre TikTok (0,17-0,83 / 0,12-0,75) + marge
def word_parts(word, t, h, rng, letters, seq, tape=None, accent=False):
    """Pièces d'un mot : [(img, t)] ; lettres de magazine découpées une à une ; accent = le mot-clé vert (seul accent de couleur)."""
    if not letters:
        st = ACCENT[rng.integers(2)] if accent else None
        return [(shadowed(chip(word, h, rng, style=st, tape=tape)), t)]
    out = []
    for k, c in enumerate(word):
        st = (ACCENT[k % 2] if rng.random() < 0.75 else STYLES[rng.integers(len(STYLES))]) if accent else None
        out.append((shadowed(chip(c, h * rng.uniform(0.92, 1.08), rng, fspec=LFONTS[rng.integers(len(LFONTS))], style=st, rot=rng.uniform(-7, 7), tape=False)), t + k * seq))
    return out
def board(lines, y0, seed, h=112, letters=(), seq=0.0, maxw=XMAX - XMIN - 30, tape=None, accent=()):
    """lines = [[(mot, t), …], …] -> pièces placées [(img, cx, cy, t)] ; mots de `letters` en lettres découpées, `accent` en vert."""
    rng = np.random.default_rng(seed); pieces = []; y = y0
    for line in lines:
        words = [word_parts(w, t, h * (1.12 if w in letters else 1.0), rng, w in letters, seq, tape, w in accent) for w, t in line]
        gap = 8; ovs = [int(h * 0.19) if len(wp) > 1 else 12 for wp in words]       # lettres de magazine un peu chevauchées
        wsz = [sum(p.shape[1] for p, _ in wp) - ov * (len(wp) - 1) for wp, ov in zip(words, ovs)]
        tot = sum(wsz) + gap * (len(words) - 1)
        sc = min(1.0, maxw / tot); lh = max(p.shape[0] for wp in words for p, _ in wp) * sc
        x = W / 2 - tot * sc / 2 + rng.uniform(-14, 14); x = min(max(x, XMIN + 4), XMAX - 4 - tot * sc)
        for wp, ov in zip(words, ovs):
            for p, t in wp:
                if sc < 1: p = cv2.resize(p, (int(p.shape[1] * sc), int(p.shape[0] * sc)), interpolation=cv2.INTER_AREA)
                pieces.append((p, x + p.shape[1] / 2, y + lh / 2 + rng.uniform(-5, 5), t)); x += p.shape[1] - ov * sc
            x += (gap + ov) * sc
        y += lh - 6
    for im, cx, cy, t in pieces:
        assert XMIN - 2 <= cx - im.shape[1] / 2 and cx + im.shape[1] / 2 <= XMAX + 2, ("texte hors zone x", cx, im.shape)
        assert YMIN - 2 <= cy - im.shape[0] / 2 and cy + im.shape[0] / 2 <= YMAX + 2, ("texte hors zone y", cy, im.shape)
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
        rng = np.random.default_rng(31); y, x = np.mgrid[0:H, 0:W].astype(np.float32); acc = np.zeros((H, W), np.float32)
        for _ in range(8):
            a = rng.uniform(0, np.pi); px, py = rng.uniform(0, W), rng.uniform(0, H)
            d = (x - px) * np.sin(a) - (y - py) * np.cos(a); wdt = rng.uniform(18, 60)
            acc += rng.uniform(0.5, 1.0) * np.sign(d) * np.exp(-np.abs(d) / wdt) * rng.choice([-1, 1])
        acc += cv2.resize(rng.standard_normal((24, 14)).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC) * 0.5
        FOLDS = (1 + 0.05 * acc)[..., None].astype(np.float32)
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
_cols = None
def columns_overlay():
    """Fausses colonnes de texte de magazine (lignes grises fines) : posées en faible opacité sur certains fonds."""
    global _cols
    if _cols is None:
        rng = np.random.default_rng(77); m = np.zeros((H, W), np.float32)
        for c0 in range(60, W - 200, 250):
            for y in range(90, H - 60, 22):
                if rng.random() < 0.08: continue
                L = int(rng.uniform(150, 215)) if rng.random() > 0.12 else int(rng.uniform(40, 120))
                cv2.line(m, (c0, y), (c0 + L, y), 1.0, 7)
        _cols = cv2.GaussianBlur(m, (0, 0), 0.8)[..., None]
    return _cols
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
        VIG = (1 - 0.22 * np.clip(r, 0, 1) ** 2.4)[..., None].astype(np.float32)
    g = np.random.default_rng(1000 + f).standard_normal((H // 2, W // 2)).astype(np.float32)
    g = cv2.resize(g, (W, H), interpolation=cv2.INTER_LINEAR)[..., None] * 0.026
    return np.clip(img * VIG + g, 0, 1)

# ---------------- lecture source, détourage ----------------
def read_frames(src, t, n_out):
    path, sfps = SRC[src][0], SRC[src][1]
    need = [int(round(i * sfps / FPS)) for i in range(n_out)]
    p = subprocess.run([FF, "-v", "error", "-ss", "%.4f" % t, "-i", HG + "/" + path, "-frames:v", str(need[-1] + 1),
                        "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True)
    a = np.frombuffer(p.stdout, np.uint8).reshape(-1, 1080, 1920, 3)
    return [a[min(i, len(a) - 1)].astype(np.float32) / 255 for i in need]
def masks(key, frames, box, pt, cam, rowfill=None):
    """Découpe avec l'outil partagé decoupe.py (instance Vision x segmentation personne, une forme, lissée) + bouts de micro retirés ;
    contrôle : aucun bord gauche/droit/haut du cadre source touché (membre coupé), une seule forme."""
    ms = dmasques(frames, box, pt, CACHE + "dec/" + key)
    x0, y0, x1, y1 = box; mm = mic_mask(cam)[y0:y1, x0:x1]
    ms = [mic_trim(m, mm) for m in ms]
    if rowfill is not None:                                                  # sous les épaules : buste plein d'un bord à l'autre (fentes du micro bouchées)
        out = []
        for m in ms:
            t = m > 0.5; f = m.copy(); y0r = int(rowfill * m.shape[0])
            for yy in range(y0r, m.shape[0]):
                xs = np.where(t[yy])[0]
                if len(xs) > 1: f[yy, xs[0]:xs[-1] + 1] = 1.0
            f = cv2.GaussianBlur(f, (0, 0), 1.0); out.append(np.maximum(m, np.clip((f - 0.5) * 2.4 + 0.5, 0, 1)).astype(np.float32))
        ms = out
    cs = [dcontrole(m) for m in ms]; pire = {k: max(c[k] for c in cs) for k in cs[0]}
    assert pire["gauche"] == 0 and pire["droite"] == 0 and pire["haut"] == 0 and pire["morceaux"] == 1, (key, pire)
    os.makedirs(D + "sheets/decoupes", exist_ok=True)
    dplanche(frames, ms, box, D + "sheets/decoupes/%s.jpg" % key, n=6, larg=300)
    print("    découpe %s : %s" % (key, pire), flush=True)
    return ms
def lum(x, gain=1.15):
    L = x @ np.array([0.0722, 0.7152, 0.2126], np.float32)
    L = L / max(float(np.percentile(L, 99)), 0.2); L = np.clip(L, 0, 1) ** 0.75
    L = np.clip((L - 0.5) * gain + 0.5 + 0.03, 0, 1); return 0.75 * L + 0.25 * (L * L * (3 - 2 * L))
def bw(x, gain=1.25):
    """Noir et blanc contrasté (lumière rouge de la scène -> luminance)."""
    L = lum(x, gain); return np.repeat(L[..., None], 3, axis=2)
DUO = {"nb": (INK, "#F4F3EF"), "gris": ("#2A2A2A", "#E3E1DC"), "dur": ("#050505", "#FFFFFF")}
def duotone(x, duo):
    a, b = DUO[duo]; L = lum(x, 1.3 if duo == "dur" else 1.15)[..., None]; return hexc(a)[None, None, :] * (1 - L) + hexc(b)[None, None, :] * L
def cutout_rgba(img, m, box, white=False):
    x0, y0, x1, y1 = box; c = bw(img[y0:y1, x0:x1])
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
STRIP_COLS = [INK, WHITE, LGREY, GREEN, MGREY, PAPER, INK, DGREY]
def strip_rgba(w, h, rng, colhex, ht=False):
    col = hexc(colhex); dot = hexc(INK if colhex in (WHITE, LGREY, PAPER, MGREY, GREEN) else MGREY)
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
    greens = 0
    for k in range(n):
        w, h = int(rng.uniform(380, 660)), int(rng.uniform(80, 160))
        colhex = STRIP_COLS[(k + skey(sh["id"])) % len(STRIP_COLS)]
        if colhex == GREEN and greens: colhex = MGREY
        if colhex in (sh.get("bg"), (sh.get("sheet") or (None,))[0]): colhex = STRIP_COLS[(k + 3) % len(STRIP_COLS)]
        if colhex == GREEN: greens += 1
        cx, cy = zones[(k * 3 + skey(sh["id"])) % len(zones)]
        out.append(dict(img=strip_rgba(w, h, rng, colhex, ht=(k % 3 == 1)), cx=cx + rng.uniform(-60, 60), cy=cy + rng.uniform(-60, 60),
                        ang=rng.uniform(-28, 28), k=k))
    return out
class Photo:
    """Photo vivante N&B : bord papier déchiré, scotch aux coins, ombre ; elle saute un peu sur chaque frappe."""
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
    """Temps de la grille (91,7 BPM) comptés depuis le drop, recalés sur la frappe réelle la plus proche (< 40 ms) quand il y en a une."""
    g = []; t = DROP
    while t > 0: g.append(t); t -= T
    t = DROP + T
    while t < END: g.append(t); t += T
    hs = [h[0] for h in HITS if h[2] >= 0.3]
    out = []
    for b in g:
        c = min(hs, key=lambda x: abs(x - b)) if hs else b
        out.append(c if abs(c - b) < 0.04 else b)
    return sorted(set(out + CUTS))
BEATS = beat_grid(); BEATF = sorted(set(fr(b) for b in BEATS))
def nbeat(f): return sum(1 for b in BEATF if b <= f)
def jit(key, k, amp=8.0, ang=1.5):
    r = np.random.default_rng(skey(key) * 1000 + k); return r.uniform(-amp, amp), r.uniform(-amp, amp), r.uniform(-ang, ang)

# ---------------- plans ----------------
# Strasbourg : logo ELA x 1615-1820 / y 95-160 ; pupitre JUSTICE POUR LA PALESTINE (texte + logos) y > 875 sur les gros plans ; voisins x < 200.
PBOX = (230, 0, 1600, 870); PPT = (0.51, 0.70)          # plan de la phrase (PH 13-21,4 s) : point sur sa poitrine
KEYL = ("NON,", "NEUTRALITÉ", "GÉNOCIDE,", "COLONIALISME,", "FASCISME.")
ACC = KEYL
BRD = {"BA": ([ln(0)], 170), "BB": ([ln(1, 2, 3, 4), ln(5), ln(6)], 128), "BC": ([ln(7, 8), ln(9, 10), ln(11)], 128),
       "BD": ([ln(12, 13), ln(14)], 134), "BE": ([ln(15, 16), ln(17)], 134)}
# Tête : elle lit ses notes de 13,8 à 15,3 s, 16,8 à 18,1 s et 18,8 à 20,0 s de la source PH (planche sheets/ph_heads.jpg) -> ces passages
# sont couverts par la salle (plans sans parole) ; plans synchro seulement quand elle regarde la salle.
SHOTS = [
    dict(id="A1", kind="cut", src="PH", cam="PH", t=None, bg=PAPER, sheet=(LGREY, "bas", 0.80, -4, 1), ghost=GREEN, box=PBOX, pt=PPT,
         scale=(1.74, 1.78), cx=915, cols=True, boards=[("BA", None)], strips=3,
         photos=[("PH", 31.5, PB, 470, (250, 1150), -6, 0.0, "nb")],
         why="2026 — meeting Justice pour la Palestine, Strasbourg, son direct : « Non, » (elle regarde la salle), grande silhouette N&B qui monte du bas, double tirage tramé vert"),
    dict(id="A2", kind="collage", bg=LGREY, sheet=(WHITE, "haut", 0.10, 3, 2), boards=[("BB", None)], strips=3,
         photos=[("PH", 32.0, PB, 1000, (560, 1000), -3, 0.0, "dur"), ("SC", 5.0, PB, 740, (480, 1500), 5, 0.5 * TB, "nb")],
         why="la salle aux drapeaux (sans parole) pendant « il n'y a pas de » : elle lit ses notes à ce moment-là"),
    dict(id="A3", kind="cut", src="PH", cam="PH", t=None, bg=PAPER, sheet=(MGREY, "bas", 0.84, 5, 3), ghost=INK, box=PBOX, pt=PPT,
         scale=(1.76, 1.80), cx=915, cols=True, boards=[("BB", None)], strips=4,
         photos=[("PH", 34.8, PB, 520, (820, 1150), 5, 0.0, "gris")],
         why="plan synchro, elle regarde la salle : « neutralité », NEUTRALITÉ en lettres de magazine vertes"),
    dict(id="A4", kind="collage", bg=PAPER, sheet=(LGREY, "bas", 0.82, -4, 7), cols=True, boards=[("BC", None)], strips=5,
         photos=[("PH", 26.0, (200, 300, 1350, 1080), 980, (560, 950), -4, 0.0, "nb"), ("SB", 33.0, PB, 680, (560, 1380), 5, TB, "gris"),
                 ("SC", 8.0, PB, 760, (700, 1700), -5, 2 * TB, "nb")],
         why="la salle comble (sans parole) pendant « à avoir face au génocide » : elle lit ses notes ; une photo de plus à chaque temps"),
    dict(id="A6", kind="collage", bg=LGREY, sheet=(PAPER, "haut", 0.09, -3, 8), boards=[("BD", None)], strips=3,
         photos=[("SB", 34.0, PB, 820, (520, 960), 4, 0.0, "dur"), ("PH", 34.0, PB, 780, (660, 1480), -5, 0.5 * TB, "nb")],
         why="la salle debout (sans parole) pendant « face au colonialisme »"),
    dict(id="A7", kind="cut", src="PH", cam="PH", t=None, bg=PAPER, sheet=(LGREY, "bas", 0.78, -5, 4), ghost=GREEN, box=PBOX, pt=PPT,
         scale=(1.80, 1.85), cx=930, boards=[("BD", None), ("BE", wt(15))], strips=4,
         photos=[("SB", 36.0, PB, 500, (230, 1250), -6, 0.0, "nb")],
         why="plan synchro, elle regarde la salle : « face au fascisme », poussée avant"),
    dict(id="A8", kind="collage", bg=PAPER, sheet=(MGREY, "bas", 0.85, 4, 9), cols=True, boards=[("BE", None)], strips=4,
         photos=[("SC", 36.0, PB, 1000, (540, 980), -3, 0.0, "nb"), ("PH", 29.0, PW, 800, (440, 1520), 5, 0.5 * TB, "gris")],
         why="la salle (sans parole) sur la fin de « fascisme » et la montée avant le drop (le plan source change de caméra à 21,47 s)"),
    dict(id="B1", kind="sil", src="SC", cam="SC", t=21.40, bg=PAPER, ghost=GREEN, box=(300, 0, 1600, 1000), pt=(0.40, 0.75), dest_w=2000, cx=895,
         push=(1.0, 1.04), cols=True,
         rboards=[([[("PAS", 0.0), ("DE", 0.0)], [("NEUTRALITÉ.", 0.0)]], 0.0)], letters=("NEUTRALITÉ.",), accent=("NEUTRALITÉ.",),
         txt_y=290, txt_h=170, strips=3, flash=True,
         why="drop « Freedom! » — même meeting, fin du discours, gros plan expressif (sans le son) : silhouette blanche 3 images puis grande découpe N&B, double tirage vert"),
    dict(id="B2", kind="collage", bg=LGREY,
         photos=[("PH", 31.0, PB, 900, (540, 820), -4, 0.0, "dur"), ("SC", 35.0, PB, 780, (600, 1260), 5, 0.5 * TB, "nb"),
                 ("PH", 27.5, PW, 740, (440, 1650), -3, TB, "gris")],
         rboards=[([[("FACE", 0.0), ("AU", 0.0)], [("GÉNOCIDE,", 0.0)]], 0.0)], letters=("GÉNOCIDE,",), accent=("GÉNOCIDE,",),
         txt_y=290, txt_h=170, strips=4,
         why="collage N&B : la foule aux drapeaux et la salle debout, une photo par demi-temps"),
    dict(id="B3", kind="cut", src="SA", cam="SA", t=28.60, bg=PAPER, sheet=(INK, "bas", 0.88, -5, 5), ghost=GREEN, box=(300, 0, 1600, 875), pt=(0.47, 0.72), rowfill=0.58,
         scale=(1.60, 1.65), cx=940,
         photos=[("SB", 35.0, PB, 520, (820, 820), 5, 0.0, "nb")],
         rboards=[([[("FACE", 0.0), ("AU", 0.0)], [("COLONIALISME,", 0.0)]], 0.0)], letters=("COLONIALISME,",), accent=("COLONIALISME,",),
         txt_y=290, txt_h=170, strips=4,
         why="Strasbourg, plus tôt dans le discours (elle regarde la salle, sans le son) : grande découpe N&B, bas de feuille noire déchirée"),
    dict(id="B4", kind="cut", src="CO", cam="CO", t=14.75, bg=LGREY, sheet=(WHITE, "haut", 0.11, 4, 6), ghost=INK, box=(520, 0, 1440, 690), pt=(0.47, 0.75), rowfill=0.56,
         scale=(2.20, 2.26), cx=900, cols=True,
         photos=[("SC", 6.5, PB, 560, (270, 1180), -5, 0.0, "gris")],
         rboards=[([[("FACE", 0.0), ("AU", 0.0)], [("FASCISME.", 0.0)]], 0.0)], letters=("FASCISME.",), accent=("FASCISME.",),
         txt_y=290, txt_h=170, strips=3, flash2=True,
         why="2026 — meeting des municipales de La Courneuve (elle regarde la salle, sans le son) : autre contexte, grande découpe N&B"),
    dict(id="B5", kind="collage", bg=PAPER, cols=True,
         photos=[("PH", 33.0, PB, 860, (540, 640), -4, 0.0, "dur"), ("SB", 32.0, PB, 740, (470, 1080), 5, TB, "nb"),
                 ("SC", 34.0, PB, 740, (610, 1440), -5, 2 * TB, "gris"), ("PH", 30.5, PW, 720, (470, 1760), 4, 3 * TB, "nb")],
         strips=5,
         why="« Freedom! » : la salle debout se colle photo après photo (un temps chacune), sans texte"),
    dict(id="FIN", kind="card", bg=PAPER, push=(1.0, 1.03), cols=True,
         rboards=[([[("RIMA", 0.0)], [("HASSAN", 0.0)]], 0.0)], letters=("RIMA", "HASSAN"), accent=("HASSAN",), txt_y=600, txt_h=270, strips=2,
         why="carton final propre (papier, noir + vert) : son nom en lettres de magazine, pas de CTA"),
]
BOUNDS_T = [0] + CUTF + [fr(END)]
assert len(BOUNDS_T) == len(SHOTS) + 1, (len(BOUNDS_T), len(SHOTS))
for i, sh in enumerate(SHOTS):
    sh["a"], sh["bb"] = BOUNDS_T[i], BOUNDS_T[i + 1]; sh["n"] = sh["bb"] - sh["a"]; sh["clip"] = "R10_%s.mov" % sh["id"]
    if sh.get("src") == "PH" and sh["t"] is None: sh["t"] = V_SRC0 + sh["a"] / FPS          # plans A synchro avec la voix
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
    if sh.get("boards"):                                                   # cartons de la phrase : même tirage (seed) d'un plan à l'autre
        for j, (key, t0) in enumerate(sh["boards"]):
            lines, hh_ = BRD[key]
            boards.append((board(lines, 272, skey(key) * 7, h=hh_, letters=KEYL, seq=0.0, accent=ACC), fr(t0) if t0 is not None else a))
    elif sh.get("rboards"):                                                # cartons après le drop : un groupe de mots complet par carton
        for j, (lines, t0) in enumerate(sh["rboards"]):
            p = board(lines, sh["txt_y"], seed + j, h=sh.get("txt_h", 130), letters=sh.get("letters", ()), seq=0.0, tape=False, accent=sh.get("accent", ()))
            boards.append(([(im, cx, cy, rel(t)) for im, cx, cy, t in p], fr(rel(t0))))
    photos = [Photo(read_frames(ps, pt, n), pbox, pw, pc, pa, a + fr(pt0), (sh["id"], j), duo)          # pt0 : décalage depuis le début du plan
              for j, (ps, pt, pbox, pw, pc, pa, pt0, duo) in enumerate(sh.get("photos", []))]
    strips = make_strips(sh)
    k0 = nbeat(a)
    if sh["kind"] in ("cut", "sil"):
        raw = read_frames(sh["src"], sh["t"], n)
        ms = masks("%s_%s_%.2f_%d" % (sh["id"], sh["src"], sh["t"], n), raw, sh["box"], sh["pt"], sh["cam"], sh.get("rowfill"))
        mm = mic_mask(sh["cam"])                                            # micros effacés de l'image (inpaint) avant la découpe N&B
        raw = [mic_clean((f * 255 + 0.5).astype(np.uint8), mm, sh["box"]).astype(np.float32) / 255 for f in raw]
    for i in range(n):
        f = a + i; u = i / max(n - 1, 1); kb = nbeat(f) - k0
        img = paper(sh["bg"])
        if sh.get("cols"): img *= (1 - 0.10 * columns_overlay())
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
        if sh["kind"] == "card":
            for j, (tx, ty, ta) in enumerate(((175, 300, -32), (905, 300, 30), (175, 1540, 28), (905, 1540, -30))):
                paste(img, CARD_TAPES[j], tx, ty, 1.0, ta)
        cur = None
        for jb, (p, f0) in enumerate(boards):
            if f >= f0: cur = (jb, p)
        if cur:
            if sh["kind"] == "card":
                z = sh["push"][0] + (sh["push"][1] - sh["push"][0]) * u
                cur = (cur[0], [(im, W / 2 + (cx - W / 2) * z, H / 2 + (cy - H / 2) * z, t) for im, cx, cy, t in cur[1]])
            draw_pieces(img, cur[1], f, boil=sh["id"] + str(cur[0]))
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
    v = grab(HG + "/" + SRC["PH"][0], V_IN, V_OUT - V_IN); env = np.ones(len(v), np.float32)
    k = int(0.03 * sr); env[:k] = np.linspace(0, 1, k); k = int(0.10 * sr); env[-k:] = np.linspace(1, 0, k)
    i0 = int(round(t_of_src(V_IN) * sr)); voix[i0:i0 + len(v)] = v * env[:, None] * 10 ** (VGAIN / 20)
    m = music_raw(MUSIC_IN)[:N]
    t = np.arange(len(m)) / sr; vend = t_of_src(V_OUT); dr = DROP
    # sous la phrase : pré-refrain baissé, montée progressive, plein sur le drop « Freedom! »
    gdb = np.interp(t, [0, 0.30, 3.0, vend - 0.5, dr - 0.03, dr, END], [-26, -20, -19, -14, -8, 0, 0])
    k = int(0.40 * sr); fo = np.ones(len(m), np.float32); fo[-k:] = np.linspace(1, 0, k)
    mus[:len(m)] = m * (10 ** (gdb / 20) * fo)[:, None]
    sf.write(OUT + "R10-voix.wav", voix, sr, subtype="PCM_24"); sf.write(OUT + "R10-musique.wav", mus, sr, subtype="PCM_24")
    sf.write(D + "tmp_mix.wav", voix + mus, sr, subtype="FLOAT")
    r = subprocess.run([FF, "-hide_banner", "-i", D + "tmp_mix.wav", "-af", "loudnorm=I=-14:TP=-2.5:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    js = json.loads(r[r.rindex("{"):r.rindex("}") + 1])
    af = ("loudnorm=I=-14:TP=-2.5:LRA=11:measured_I=%s:measured_TP=%s:measured_LRA=%s:measured_thresh=%s:offset=%s:linear=true,"
          "aresample=48000" % (js["input_i"], js["input_tp"], js["input_lra"], js["input_thresh"], js["target_offset"]))
    subprocess.run([FF, "-v", "error", "-y", "-i", D + "tmp_mix.wav", "-af", af, "-c:a", "pcm_s24le", OUT + "R10-mix.wav"], check=True)
    os.remove(D + "tmp_mix.wav"); print("audio : mix avant normalisation", js["input_i"], "LUFS")

# ---------------- plan ----------------
PHR = "Non, il n'y a pas de neutralité à avoir face au génocide, face au colonialisme, face au fascisme."
def build_plan():
    video = []
    for sh in SHOTS:
        v = {"id": sh["id"], "clip": sh["clip"], "folder": "genR10", "path": OUT + sh["clip"], "s": 0, "e": sh["n"], "rec": sh["a"], "dur": sh["n"],
             "clip_fps": FPS, "speed_pct": 100, "track": 1, "note": sh["why"], "kind": sh["kind"], "temps": round(sh["n"] / FPS / T, 2)}
        if sh.get("src"):
            path, sfps, url, off, ctx = SRC[sh["src"]]
            v["source"] = {"fichier": path, "in_s": round(sh["t"], 3), "out_s": round(sh["t"] + sh["n"] / FPS, 3), "fps": sfps, "url": url, "contexte": ctx}
            if off is not None: v["source"]["youtube_t"] = round(off + sh["t"], 1)
        if sh.get("photos"):
            v["photos"] = [{"fichier": SRC[p[0]][0], "in_s": p[1], "out_s": round(p[1] + sh["n"] / FPS, 2), "cadre_source": p[2], "ton": p[7], "url": SRC[p[0]][2]} for p in sh["photos"]]
        video.append(v)
    texts = []
    for sh in SHOTS:
        for key, _ in sh.get("boards", []):
            lines = BRD[key][0]
            texts.append({"plan": sh["id"], "texte": " / ".join(" ".join(w for w, _ in line) for line in lines)})
        for lines, _ in sh.get("rboards", []): texts.append({"plan": sh["id"], "texte": " ".join(w for line in lines for w, _ in line)})
    plan = {"name": "R10 - Collage ransom-note - Rima Hassan", "fps": FPS, "w": W, "h": H, "duree_s": END,
            "note": "Plans ProRes 9:16 composés en Python (lot7/_claude/gen/R10/out) : fonds papier froissé blanc / gris + feuilles déchirées, Rima Hassan détourée "
                    "seule (instance Vision, tools/inst) en N&B, double tirage tramé vert, silhouettes blanches 3 images, photos N&B vivantes, textes ransom-note cuits "
                    "(mots-clés en lettres de magazine vertes). s/e en images du clip (30 i/s), rec en images timeline. Coupes sur les frappes réelles de Freedom! '90. "
                    "Aucun ralenti. Générateur : lot7/_claude/gen/R10/genR10.py",
            "phrase": {"texte": PHR, "url": SRC["PH"][2], "youtube_s": [2303.32, 2311.50], "source": SRC["PH"][0], "in_s": 13.32, "out_s": 21.50,
                       "timeline_s": [round(t_of_src(13.32), 2), round(t_of_src(21.50), 2)], "voix": "son direct synchro (plans A1-A4)"},
            "musique": {"fichier": "lot7/sons/R10-freedom90_complet.wav", "titre": "George Michael - Freedom! '90 (Remastered)", "url": SON_URL,
                        "debut_complet_s": round(MUSIC_IN, 4), "fin_complet_s": round(MUSIC_IN + END, 3), "drop_timeline_s": round(DROP, 4),
                        "coupes_frappes_s": [round(c, 4) for c in CUTS], "coupes_images": CUTF},
            "textes": texts, "video": video,
            "audio": [{"id": "mix", "clip": "R10-mix.wav", "folder": "genR10", "path": OUT + "R10-mix.wav", "rec": 0, "track": 1,
                       "note": "mix -14 LUFS : voix PH %.2f-%.2f s (+%.0f dB) à %.2f s ; Freedom! '90 dès %.3f s du complet, -20 dB sous la voix (pré-refrain), montée, plein au drop, fondu de fin 0,4 s"
                               % (V_IN, V_OUT, VGAIN, t_of_src(V_IN), MUSIC_IN)}],
            "stems": ["lot7/_claude/gen/R10/out/R10-voix.wav", "lot7/_claude/gen/R10/out/R10-musique.wav"],
            "logos_exclus": "Strasbourg : logo ELA (haut droite) et pupitre JUSTICE POUR LA PALESTINE hors des fenêtres de détourage ; La Courneuve : pupitre et logo hors fenêtre"}
    json.dump(plan, open(D + "plan-R10.json", "w"), indent=1, ensure_ascii=False)
    son = {"id": "R10", "titre": "Freedom! '90 (Remastered)", "artiste": "George Michael", "url": SON_URL,
           "chaine": "George Michael (officielle, « Provided to YouTube »)",
           "fichier": "lot7/sons/R10-freedom90_complet.wav",
           "extrait_complet_s": {"debut": round(MUSIC_IN, 4), "fin": round(MUSIC_IN + END, 3)},
           "paroles_audibles": "sous la phrase (baissé) : pré-refrain « All we have to see / Is that I don't belong to you… » ; au drop : refrain « Freedom! I won't let you down… » jusqu'à « …what you take »",
           "bpm": round(60 / T, 1), "temps_s": T,
           "drop": {"complet_s": MDROP, "timeline_s": round(DROP, 4), "nature": "1er temps du refrain « Freedom! » (kick + caisse + accord, après le « yeah yeah »)"},
           "frappes_timeline_s": [round(b, 4) for b in BEATS], "coupes_sur_frappes_s": [round(c, 4) for c in CUTS],
           "mix": "lot7/_claude/gen/R10/out/R10-mix.wav"}
    json.dump(son, open(D + "son.json", "w"), indent=1, ensure_ascii=False)

# ---------------- aperçu 540x960 ----------------
def apercu():
    plan = json.load(open(D + "plan-R10.json")); ins = []; fl = []
    for i, v in enumerate(plan["video"]):
        ins += ["-i", OUT + v["clip"]]
        fl.append("[%d:v]trim=start_frame=%d:end_frame=%d,setpts=PTS-STARTPTS,scale=540:960,setsar=1[v%d]" % (i, v["s"], v["e"], i))
    k = len(plan["video"]); fl.append("".join("[v%d]" % i for i in range(k)) + "concat=n=%d:v=1:a=0[v]" % k)
    ins += ["-i", OUT + "R10-mix.wav"]; out = HG + "/preview/apercu-R10.mp4"
    subprocess.run([FF, "-v", "error", "-y"] + ins + ["-filter_complex", ";".join(fl), "-map", "[v]", "-map", "%d:a" % k,
                    "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "aac", "-b:a", "192k", "-shortest", out], check=True)
    print("aperçu", out)
# ---------------- mesure sur l'export : coupes vs frappes, LUFS / TP ----------------
def mesure():
    """Coupes (images de l'export) vs frappes détectées LOCALEMENT (fenêtre ±1,2 s, hits.py) : sur l'audio de l'export, et sur le stem
    musique pour les coupes sous la voix (la voix y masque la musique baissée ; export et mix alignés à 0 ms près, vérifié par corrélation)."""
    import soundfile as sf
    out = HG + "/preview/apercu-R10.mp4"
    p = subprocess.run([FF, "-v", "error", "-i", out, "-vn", "-ac", "2", "-ar", "48000", "-f", "f32le", "-"], capture_output=True)
    y = np.frombuffer(p.stdout, np.float32).reshape(-1, 2); mus, _ = sf.read(OUT + "R10-musique.wav", dtype="float32"); sr = 48000
    a = y[48000:48000 * 5, 0]; b, _ = sf.read(OUT + "R10-mix.wav", dtype="float32", start=48000 - 2400, frames=48000 * 4 + 4800)
    off = (int(np.argmax(np.correlate(a, b[:, 0], "valid"))) - 2400) / 48
    print("décalage export / mix : %.1f ms" % off)
    worst = 0
    for f in CUTF:
        c = f / FPS; sig = mus if c < DROP - 0.1 else y
        i0 = int(max(0, c - 1.2) * sr); seg = sig[i0:i0 + int(2.4 * sr)]
        near = [h for h in detect_hits(seg) if abs(h[0] + i0 / sr - c) < 0.06]
        k = max(near, key=lambda h: h[2]) if near else None
        e = (c - (k[0] + i0 / sr)) * 1000 if k else float("nan"); worst = max(worst, abs(e)) if k else worst
        print("  coupe %.3f  %s  frappe %s  écart %+.1f ms" % (c, "musique" if sig is mus else "export ", "%.4f %s %.2f" % (k[0] + i0 / sr, k[1], k[2]) if k else "-", e))
    print("écart max coupes/frappes : %.1f ms" % worst)
    r = subprocess.run([FF, "-hide_banner", "-i", out, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    print(r[r.rindex("Summary"):].split("[")[0])
if __name__ == "__main__":
    args = set(a for a in sys.argv[1:] if not a.startswith("only=")) or {"shots", "audio", "plan", "apercu"}
    only = [x for a in sys.argv[1:] if a.startswith("only=") for x in a.split("=", 1)[1].split(",")]
    print("musique dès %.4f s ; fin %.3f s ; coupes (s) :" % (MUSIC_IN, END), [round(c, 4) for c in CUTS], "images :", CUTF)
    if "shots" in args or only:
        for sh in SHOTS:
            if not only or sh["id"] in only: render(sh)
    if "audio" in args: make_audio()
    if "plan" in args: build_plan()
    if "apercu" in args: apercu()
    if "mesure" in args: mesure()
