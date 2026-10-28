# R4 (lot 6) — Collage ransom-note « tract brat », Jean-Luc Mélenchon, son Charli xcx – 360 (lyric video officielle, chaîne Charli xcx).
# Modèle : lot5/_claude/gen/R1/genR1.py (validé par Luca) — mêmes fonctions (découpe Vision, morceaux de texte penchés serif/sans,
# frappes, carton final), poussé plus loin : plus de couches (bandes de papier, coupures de journal en colonnes, photos duotone vert
# et N&B, scotch, déchirures, trame d'imprimerie), chiffres découpés lettre par lettre, tout calé sur les frappes réelles.
# Palette R4 (brief) : vert brat #8ACE00 + noir, papier journal ; carton final façon pochette « brat » (minuscules Arial Narrow floutées).
# Phrase (son direct, meeting de Saint-Denis 07/06/2026, chaîne JEAN-LUC MÉLENCHON, youtu.be/1dkY_JVFx9I, extrait 50:00-54:00) :
#   « Le but reste l'abrogation de la réforme des retraites à 64 ans, puis le retour à 60 ans. »
#   fichier lot1/sources/5-melenchon-saintdenis-smic.mp4 123,45-135,62 s (YouTube 3123,45-3135,62 s) ; seuls les silences et
#   applaudissements entre les membres de phrase sont raccourcis (124,32-126,46 et 130,22-132,24), aucun mot coupé.
#   Autre phrase que I1 (lot5, « Nous réparerons les dégâts, le SMIC passera à 1 700 euros ») et lot1 #5 (même phrase SMIC).
#   Les mesures empilées après le drop sont dites dans ce même discours : SMIC à 1 700 euros (105,5-107,9 s), sécurité sociale
#   intégrale (111,9-115,4 s), retraite à 60 ans (phrase entendue).
# Son : 360, 1er refrain ; sous la phrase : fin du pré-refrain (« looking like an icon / work angles / 360 ») et début du refrain
#   (« When you're in the mirror… »), musique baissée qui monte ; drop = « I'm everywhere, I'm so Julia » (kick 49,50 s) — retour Luca :
#   drop sur le moment le plus connu, jamais l'intro.
# Usage : python genR4.py [shots] [audio] [plan] [apercu] [mesure] [only=ID,ID]   (sans argument = tout sauf mesure)
import sys
sys.dont_write_bytecode = True
import os, json, subprocess, math, re
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
HG = "/Users/luca.grousset/Movies/highkey-gauchiste"
D = HG + "/lot6/_claude/gen/R4/"; OUT = D + "out/"; CACHE = D + "cache/"; os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, D)
from hits import detect_hits
FF = "/opt/homebrew/bin/ffmpeg"; SEG = HG + "/_claude/outils/segment"; FPS = 30; W, H = 1080, 1920
def fr(t): return int(round(t * FPS))
def hexc(h): h = h.lstrip("#"); return np.array([int(h[4:6], 16), int(h[2:4], 16), int(h[0:2], 16)], np.float32) / 255   # BGR
GREEN, BLACK, NEWS, WHITE, GREY, DGREEN = "#8ACE00", "#0C0C0C", "#E8E6DF", "#FAFAF7", "#B9B9B2", "#5E8F00"   # brat + papier journal
def rgb(h): h = h.lstrip("#"); return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))

# ---------------- sources (lecture seule) ----------------
URL_SD = "https://www.youtube.com/watch?v=1dkY_JVFx9I"
CTX_SD = "meeting de Saint-Denis, 07/06/2026 (chaîne JEAN-LUC MÉLENCHON)"
SRC = {
    "SD": ("lot1/sources/5-melenchon-saintdenis-smic.mp4", 30.0, URL_SD, 3000.0, CTX_SD + ", extrait 50:00-54:00"),
    "C402": ("lot3/sources/C4-melenchon-stdenis-02.mp4", 30.0, URL_SD, None, CTX_SD),
    "C404": ("lot3/sources/C4-melenchon-stdenis-04.mp4", 30.0, URL_SD, None, CTX_SD),
    "C405": ("lot3/sources/C4-melenchon-stdenis-05.mp4", 30.0, URL_SD, None, CTX_SD),
    "C408": ("lot3/sources/C4-melenchon-stdenis-08.mp4", 30.0, URL_SD, None, CTX_SD),
    "CV03": ("lot2/sources/C3-melenchon-convention-03.mp4", 60.0, "https://www.youtube.com/watch?v=Yc46p2zQZxY", None,
             "convention municipales 2026, 23/11/2025 (fond violet, logos hors détourage)"),
}

# ---------------- musique : Charli xcx – 360 ----------------
SON_FILE = HG + "/lot6/sons/R4-charlixcx-360_complet.wav"; SON_URL = "https://www.youtube.com/watch?v=O_HoOpJ60C0"
MDROP = 49.4964                       # kick sur « I'm everywhere, I'm so Julia » (Whisper « I'm » 49,48 s)
DROP = 9.30; T = 0.5                  # 120 BPM (caisses régulières à x,755 s, une par seconde)
MUSIC_IN0 = MDROP - DROP
END = 56.22 - MUSIC_IN0                # carton final tenu 1,5 s au plus (retour Luca) : fin dans « 666 with the princess… », fondu 0,35 s
# coupes (temps du morceau) : kicks du pré-refrain / refrain sous la voix, kick du drop, puis une caisse par seconde
CUT_SONG = [41.4968, 43.2466, 45.2463, 46.4966, MDROP, 50.4968, 51.7454, 52.7548, 53.7548, 54.7547]
CUT_T = [c - MUSIC_IN0 for c in CUT_SONG]
HITS_JSON = OUT + "R4-frappes.json"
def music_raw(mi, dur=END + 0.5, sr=48000):
    import soundfile as sf
    i0 = int(round(mi * sr)); x, r = sf.read(SON_FILE, start=i0, frames=int(dur * sr), dtype="float32"); assert r == sr; return x
def hits_of(h, lvl=0.015): return sorted(x[0] for x in h if x[3] > lvl)
def snap_list(hs, targets):
    out = []
    for t in targets:
        c = min(hs, key=lambda k: abs(k - t)); assert abs(c - t) < 0.04, ("pas de frappe près de", t, c); out.append(c)
    return out
def frappes():
    if os.path.exists(HITS_JSON):
        js = json.load(open(HITS_JSON))
        if js["cle"] == [MUSIC_IN0, END, CUT_T]: return js["music_in"], js["frappes"]
    best, bad = None, 9
    for off in np.arange(-0.016, 0.0165, 0.001):
        h = detect_hits(music_raw(MUSIC_IN0 + off))
        try: cuts = snap_list(hits_of(h), CUT_T)
        except AssertionError: continue                                     # frappe faible de l'intro non détectée à ce décalage
        e = max(abs(c - round(c * FPS) / FPS) for c in cuts)
        if e < bad: best, bad, hb = off, e, h
    mi = MUSIC_IN0 + best
    json.dump({"cle": [MUSIC_IN0, END, CUT_T], "music_in": mi, "frappes": hb}, open(HITS_JSON, "w")); return mi, hb
MUSIC_IN, HITS = frappes()
FINE = float(os.environ.get("R4_FINE", "0"))   # recalage fin mesuré sur l'export AAC
MUSIC_IN += FINE; HITS = [[h[0] - FINE] + list(h[1:]) for h in HITS]
CUTS = snap_list(hits_of(HITS), CUT_T); CUTF = [fr(c) for c in CUTS]
DROPF = CUTF[4]; TB = T

# ---------------- voix : 3 morceaux synchro (silences / applaudissements raccourcis) ----------------
VP = [(123.36, 124.32, 0.30), (126.46, 130.22, 1.27), (132.24, 135.66, 5.27)]     # (source in, out, timeline)
def tl_of(src):
    for a, b, t0 in VP:
        if a - 0.6 <= src <= b + 0.6: return t0 + src - a
    raise ValueError(src)
def src_of_tl(tl):
    for a, b, t0 in VP[::-1]:
        if tl >= t0 - 0.35: return a + tl - t0
    return VP[0][0] + tl - VP[0][2]
WORDS = [("LE", 123.45), ("BUT", 123.62), ("RESTE", 123.85),
         ("L'ABROGATION", 126.55), ("DE", 127.46), ("LA", 127.66), ("RÉFORME", 127.82), ("DES", 128.36), ("RETRAITES", 128.56),
         ("À", 129.06), ("64", 129.20), ("ANS", 129.80),
         ("PUIS", 132.35), ("LE", 133.97), ("RETOUR", 134.22), ("À", 134.64), ("60", 134.92), ("ANS", 135.44)]
def wt(i): return tl_of(WORDS[i][1])

# ---------------- polices ransom-note ----------------
S = "/System/Library/Fonts/Supplemental/"
FONTS = [(S + "Arial Black.ttf", 0), (S + "Georgia Bold.ttf", 0), (S + "Times New Roman Bold.ttf", 0), (S + "Impact.ttf", 0),
         (S + "Courier New Bold.ttf", 0), (S + "Rockwell.ttc", 2), (S + "AmericanTypewriter.ttc", 2), (S + "Didot.ttc", 2),
         (S + "Bodoni 72.ttc", 2), (S + "Futura.ttc", 2), (S + "Arial Narrow Bold.ttf", 0)]
FCOND = (S + "Futura.ttc", 4)
FBRAT = (S + "Arial Narrow.ttf", 0)   # pochette brat : minuscules Arial Narrow, floutées
NARROW = [(S + "Impact.ttf", 0), (S + "Arial Narrow Bold.ttf", 0), FCOND, (S + "Times New Roman Bold.ttf", 0), (S + "Didot.ttc", 2)]   # mots longs : polices étroites, plus grands
STYLES = [(rgb(GREEN), (12, 12, 12)), ((12, 12, 12), rgb(GREEN)), (rgb(NEWS), (12, 12, 12)), ((250, 250, 247), (12, 12, 12)),
          ((12, 12, 12), (250, 250, 247)), (rgb(GREY), (12, 12, 12)), (rgb(NEWS), (70, 110, 0))]
_fc = {}; AVOID = None
def font(spec, size):
    k = (spec, size)
    if k not in _fc: _fc[k] = ImageFont.truetype(spec[0], size, index=spec[1])
    return _fc[k]
def chip(txt, h, rng, fspec=None, style=None, rot=None):
    """Un morceau découpé : rectangle irrégulier + texte, RGBA PIL, légèrement penché ; parfois trame de magazine."""
    if style is None:                                                       # jamais un morceau de la couleur du fond (illisible)
        style = STYLES[rng.integers(len(STYLES))]
        while AVOID and style[0] == AVOID: style = STYLES[rng.integers(len(STYLES))]
    fspec = fspec or (NARROW[rng.integers(len(NARROW))] if len(txt) >= 7 else FONTS[rng.integers(len(FONTS))]); bg, fg = style or STYLES[rng.integers(len(STYLES))]
    size = int(h * 0.80); f = font(fspec, size)
    x0, y0, x1, y1 = f.getbbox(txt, anchor="ls"); cap = f.getbbox("H", anchor="ls")
    tw, th = x1 - x0, max(y1, 0) - min(y0, cap[1])
    px, py = int(h * (0.08 if len(txt) == 1 else 0.16)), int(h * 0.10)
    w_, h_ = tw + 2 * px, th + 2 * py
    im = Image.new("RGBA", (w_ + 12, h_ + 12), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    j = lambda: rng.integers(-4, 5)
    d.polygon([(6 + j(), 6 + j()), (6 + w_ + j(), 6 + j()), (6 + w_ + j(), 6 + h_ + j()), (6 + j(), 6 + h_ + j())], fill=bg + (255,))
    if rng.uniform() < 0.3 and sum(bg) > 300:                               # trame d'imprimerie (papier magazine)
        dot = tuple(int(c * 0.86) for c in bg) + (255,)
        for yy in range(10, h_ + 4, 9):
            for xx in range(10 + (yy // 9 % 2) * 4, w_ + 4, 9): d.ellipse([xx - 1.6, yy - 1.6, xx + 1.6, yy + 1.6], fill=dot)
    d.text((6 + px - x0, 6 + py - min(y0, cap[1])), txt, font=f, fill=fg + (255,), anchor="ls")
    a = rot if rot is not None else rng.uniform(-4, 4)
    return im.rotate(a, resample=Image.BICUBIC, expand=True)
def word_img(word, h, rng, letters=False):
    if not letters: return chip(word, h, rng)
    narrow = len(word) >= 8                                                 # nom du carton final : lettres étroites, donc plus hautes
    parts = [None if c == " " else chip(c, h * rng.uniform(0.92, 1.08), rng, rot=rng.uniform(-7, 7),
                                         fspec=(NARROW[rng.integers(len(NARROW))] if narrow else None)) for c in word]
    sp = int(h * 0.22); ov = int(h * 0.12) if narrow else 12                  # lettres du nom plus serrées (chevauchement)
    wsum = sum(p.width - ov if p is not None else sp for p in parts) + ov; hh = max(p.height for p in parts if p is not None) + 10
    im = Image.new("RGBA", (wsum, hh), (0, 0, 0, 0)); x = 0
    for p in parts:
        if p is None: x += sp; continue
        im.alpha_composite(p, (x, (hh - p.height) // 2 + int(rng.integers(-5, 6)))); x += p.width - ov
    return im
def shadowed(im):
    """Ombre portée (papier collé)."""
    a = np.asarray(im)[..., 3].astype(np.float32) / 255
    sh = cv2.GaussianBlur(a, (0, 0), 3) * 0.55
    out = np.zeros((im.height + 12, im.width + 12, 4), np.float32)
    out[9:9 + im.height, 7:7 + im.width, 3] = sh
    rgb_ = np.asarray(im)[..., :3][..., ::-1].astype(np.float32) / 255
    out[:im.height, :im.width, :3] = out[:im.height, :im.width, :3] * (1 - a[..., None]) + rgb_ * a[..., None]
    out[:im.height, :im.width, 3] = a + out[:im.height, :im.width, 3] * (1 - a)
    return out
XMIN, XMAX, YMIN, YMAX = 0.19 * W, 0.81 * W, 0.13 * H, 0.74 * H          # zone sûre TikTok (0,17-0,83 / 0,12-0,75) + marge
def board(lines, y0, seed, h=112, letters=(), maxw=XMAX - XMIN - 30, xmin=XMIN, xmax=XMAX):
    """lines = [[(mot, t_apparition), …], …] -> liste de pièces placées (img, cx, cy, t)."""
    rng = np.random.default_rng(seed); pieces = []; y = y0
    for line in lines:
        imgs = [shadowed(word_img(w, h * (1.25 if w in letters else 1.0), rng, w in letters)) for w, _ in line]
        gap = 8; tot = sum(i.shape[1] for i in imgs) + gap * (len(imgs) - 1)
        sc = min(1.0, maxw / tot); lh = max(i.shape[0] for i in imgs) * sc
        x = W / 2 - tot * sc / 2 + rng.uniform(-14, 14); x = min(max(x, xmin + 4), xmax - 4 - tot * sc)
        for (w, t), im in zip(line, imgs):
            if sc < 1: im = cv2.resize(im, (int(im.shape[1] * sc), int(im.shape[0] * sc)), interpolation=cv2.INTER_AREA)
            pieces.append((im, x + im.shape[1] / 2, y + lh / 2, t)); x += im.shape[1] + gap * sc
        y += lh - 6
    for im, cx, cy, t in pieces:
        assert xmin - 2 <= cx - im.shape[1] / 2 and cx + im.shape[1] / 2 <= xmax + 2, ("texte hors zone x", cx, im.shape)
        assert YMIN - 2 <= cy - im.shape[0] / 2 and cy + im.shape[0] / 2 <= YMAX + 2, ("texte hors zone y", cy, im.shape)
    return pieces
def big_text(lines, y0, color, spec=FCOND, maxw=XMAX - XMIN, sizes=None, contour=0, blur=0, gap=-18):
    """Texte propre (carton final / gros texte plein cadre) : lignes centrées, largeur max, retour [(img, cx, cy, t)]."""
    pieces = []; y = y0
    for k, (txt, t, col) in enumerate(lines):
        size = (sizes or [300] * len(lines))[k]; f = font(spec, size)
        while f.getlength(txt) > maxw - 2 * contour - 44: size -= 4; f = font(spec, size)
        x0, y0b, x1, y1 = f.getbbox(txt)
        im = Image.new("RGBA", (x1 - x0 + 2 * contour + 24, y1 - y0b + 2 * contour + 24), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.text((12 + contour - x0, 12 + contour - y0b), txt, font=f, fill=tuple(col) + (255,), stroke_width=contour, stroke_fill=(10, 10, 10, 255))
        if blur: im = im.filter(ImageFilter.GaussianBlur(blur))
        a = shadowed(im) if contour else np.dstack([np.asarray(im)[..., :3][..., ::-1], np.asarray(im)[..., 3]]).astype(np.float32) / 255
        pieces.append((a, W / 2, y + a.shape[0] / 2, t)); y += a.shape[0] + gap
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
    """Apparition d'une pièce : léger rebond d'échelle sur 4 images (pas de flash)."""
    if f < f0: return None
    u = min(1.0, (f - f0) / n); return 1 + amp * (1 - u) ** 2
_tex = {}
def paper(col):
    if col not in _tex:
        rng = np.random.default_rng(len(_tex) + 3)
        n = cv2.resize(rng.standard_normal((48, 27)).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC)
        n2 = cv2.GaussianBlur(rng.standard_normal((H, W)).astype(np.float32), (0, 0), 1.2)
        fib = cv2.GaussianBlur(rng.standard_normal((H, W)).astype(np.float32), (0, 0), sigmaX=9, sigmaY=0.8)   # fibres du papier
        base = hexc(col)[None, None, :]
        amp = 0.05 if col == BLACK else 1.0
        tex = base * (1 + 0.03 * n[..., None] + 0.035 * n2[..., None] + 0.03 * fib[..., None]) if col != BLACK else \
            base + amp * (0.02 * n[..., None] + 0.025 * n2[..., None] + 0.02 * fib[..., None])
        _tex[col] = np.clip(tex, 0, 1).astype(np.float32)
    return _tex[col].copy()
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

# ---------------- lecture source ----------------
def read_frames(src, t, n_out):
    path, sfps = SRC[src][0], SRC[src][1]
    need = [int(round(i * sfps / FPS)) for i in range(n_out)]
    p = subprocess.run([FF, "-v", "error", "-ss", "%.4f" % t, "-i", HG + "/" + path, "-frames:v", str(need[-1] + 1),
                        "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True)
    a = np.frombuffer(p.stdout, np.uint8).reshape(-1, 1080, 1920, 3)
    return [a[min(i, len(a) - 1)].astype(np.float32) / 255 for i in need]
def masks(key, frames, box, k=13):
    """Détourage personne (binaire segment, Vision) sur la zone box de chaque image ; cache dans cache/seg/<key>."""
    x0, y0, x1, y1 = box; d = CACHE + "seg/" + key; di, dm = d + "/in", d + "/m"
    if not (os.path.isdir(dm) and len(os.listdir(dm)) >= len(frames)):
        os.makedirs(di, exist_ok=True)
        for i, fr_ in enumerate(frames): cv2.imwrite("%s/f%04d.png" % (di, i), (fr_[y0:y1, x0:x1] * 255).astype(np.uint8))
        subprocess.run([SEG, di, dm], check=True, capture_output=True)
    out = []
    for i in range(len(frames)):
        m = cv2.imread("%s/f%04d.png" % (dm, i), 0).astype(np.float32) / 255
        m = cv2.morphologyEx(m, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))
        m = np.clip((cv2.GaussianBlur(m, (0, 0), 1.2) - 0.5) * 2.2 + 0.5, 0, 1)
        out.append(m)
    return out
def grade(x, sat=1.08):
    x = 0.82 * x + 0.18 * (x * x * (3 - 2 * x))
    L = x @ np.array([0.0722, 0.7152, 0.2126], np.float32)
    return np.clip(L[..., None] + (x - L[..., None]) * sat, 0, 1)
def bw(x, gain=1.15):
    L = x @ np.array([0.0722, 0.7152, 0.2126], np.float32)
    L = L / max(float(np.percentile(L, 99)), 0.2); L = np.clip(L, 0, 1) ** 0.75
    L = np.clip((L - 0.5) * gain + 0.5 + 0.03, 0, 1); L = 0.75 * L + 0.25 * (L * L * (3 - 2 * L))
    return np.repeat(L[..., None], 3, axis=2)
def duo(x):
    """Duotone noir -> vert brat (photo de tract imprimée en 2 couleurs)."""
    L = bw(x, 1.3)[..., :1]
    return np.clip(hexc("#101010")[None, None, :] * (1 - L) + hexc(GREEN)[None, None, :] * 1.05 * L, 0, 1)
def cutout_rgba(img, m, box, white=False):
    x0, y0, x1, y1 = box; c = grade(img[y0:y1, x0:x1])
    if white: c = np.ones_like(c) * np.array([0.96, 0.97, 0.98], np.float32)
    return np.dstack([c, m]).astype(np.float32)

# ---------------- collage : déchirures, scotch, bandes, coupures de journal ----------------
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
    col = np.array([0.80, 0.86, 0.88], np.float32)[None, None, :] * (1 + 0.04 * rng.standard_normal((h, w, 1)).astype(np.float32))
    return np.dstack([col, m * 0.72]).astype(np.float32)
def halftone(h, w, col, dot=(0.06, 0.06, 0.06), step=14):
    img = np.ones((h, w, 3), np.float32) * col[None, None, :]
    for y in range(0, h, step):
        for x in range((y // step % 2) * step // 2, w, step): cv2.circle(img, (x, y), 4, dot, -1, cv2.LINE_AA)
    return img
def newsprint(h, w, rng):
    """Coupure de journal : colonnes de lignes de texte grises (illisibles) sur papier journal."""
    img = np.ones((h, w, 3), np.float32) * hexc(NEWS)[None, None, :]
    ncol = max(1, w // 170); cw = (w - 30) // ncol
    for c in range(ncol):
        x0 = 15 + c * cw
        for y in range(18, h - 14, 15):
            x = x0
            while x < x0 + cw - 20:
                ww = int(rng.integers(12, 48)); cv2.rectangle(img, (x, y), (min(x + ww, x0 + cw - 14), y + 6), (0.42, 0.42, 0.42), -1); x += ww + 7
    return img
STRIP_COLS = [GREEN, BLACK, NEWS, WHITE, GREY, DGREEN, "news", GREEN]
def strip_rgba(w, h, rng, colhex, ht=False):
    if colhex == "news": body = newsprint(h, w, rng)
    else:
        col = hexc(colhex); body = halftone(h, w, col, dot=((0.2, 0.2, 0.2) if colhex == BLACK else (0.06, 0.06, 0.06))) if ht else np.ones((h, w, 3), np.float32) * col[None, None, :]
    body = np.clip(body * (1 + 0.035 * cv2.GaussianBlur(rng.standard_normal((h, w)).astype(np.float32), (0, 0), 1.5))[..., None], 0, 1)
    m = torn_mask(h, w, rng, rough=9, step=12)
    out = np.zeros((h + 16, w + 16, 4), np.float32)
    out[10:10 + h, 8:8 + w, 3] = cv2.GaussianBlur(m, (0, 0), 3) * 0.45
    a = m[..., None]; out[:h, :w, :3] = body * a; out[:h, :w, 3] = np.maximum(m, out[:h, :w, 3])
    return out
def make_strips(sh):
    """Bandes de papier / coupures de journal qui s'empilent une par frappe derrière la figure."""
    n = sh.get("strips", 0); rng = np.random.default_rng(skey(sh["id"]) + 5); out = []
    zones = [(150, 480), (930, 560), (120, 1250), (960, 1300), (540, 300), (540, 1700), (230, 900), (880, 1050), (300, 1600), (820, 1650)]
    for k in range(n):
        colhex = STRIP_COLS[(k + skey(sh["id"])) % len(STRIP_COLS)]
        if colhex == sh.get("bg"): colhex = STRIP_COLS[(k + 3) % len(STRIP_COLS)]
        if colhex == sh.get("bg"): colhex = "news"
        if colhex == "news": w, h = int(rng.uniform(300, 460)), int(rng.uniform(200, 330))
        else: w, h = int(rng.uniform(380, 640)), int(rng.uniform(80, 160))
        cx, cy = zones[(k * 3 + skey(sh["id"])) % len(zones)]
        out.append(dict(img=strip_rgba(w, h, rng, colhex, ht=(k % 3 == 1)), cx=cx + rng.uniform(-60, 60), cy=cy + rng.uniform(-60, 60),
                        ang=rng.uniform(-28, 28), k=k))
    return out
class Photo:
    """Photo vivante (N&B ou duotone vert) : bord papier déchiré, scotch aux coins, ombre ; elle saute un peu sur chaque frappe."""
    def __init__(self, frames, box, width, center, angle, f0, key, tone="bw", border=16):
        self.frames, self.box, self.width, self.center, self.angle, self.f0, self.key, self.tone = frames, box, width, center, angle, f0, key, tone
        x0, y0, x1, y1 = box; self.h = int(round(width * (y1 - y0) / (x1 - x0))); self.b = border
        rng = np.random.default_rng(skey(key)); M = 40
        self.M = M; hh, ww = self.h + 2 * border, width + 2 * border
        self.mask = torn_mask(hh, ww, rng, rough=5, step=11, inset=3)
        self.shadow = np.zeros((hh + 2 * M, ww + 2 * M), np.float32); self.shadow[M + 9:M + 9 + hh, M + 7:M + 7 + ww] = self.mask * 0.5
        self.shadow = cv2.GaussianBlur(self.shadow, (0, 0), 4)
        self.tapes = [(tape_rgba(int(rng.uniform(110, 150)), 38, rng), (M + int(rng.uniform(-10, 30)), M - 12), rng.uniform(-40, -25)),
                      (tape_rgba(int(rng.uniform(110, 150)), 38, rng), (M + ww - int(rng.uniform(90, 140)), M + hh - 26), rng.uniform(-40, -25))]
        self.tape_imgs = []
        for t, (tx, ty), ta in self.tapes:
            R = cv2.getRotationMatrix2D((t.shape[1] / 2, t.shape[0] / 2), ta, 1.0)
            c = np.abs(R[:, :2]) @ np.array([t.shape[1], t.shape[0]]); R[0, 2] += c[0] / 2 - t.shape[1] / 2; R[1, 2] += c[1] / 2 - t.shape[0] / 2
            self.tape_imgs.append((cv2.warpAffine(t, R, (int(c[0]), int(c[1]))), (tx, ty)))
    def rgba(self, i):
        x0, y0, x1, y1 = self.box; b, M = self.b, self.M
        src = self.frames[i][y0:y1, x0:x1]
        c = cv2.resize(duo(src) if self.tone == "duo" else bw(src), (self.width, self.h), interpolation=cv2.INTER_AREA)
        hh, ww = self.h + 2 * b, self.width + 2 * b
        out = np.zeros((hh + 2 * M, ww + 2 * M, 4), np.float32); out[..., 3] = self.shadow
        body = np.ones((hh, ww, 3), np.float32) * np.array([0.92, 0.93, 0.92], np.float32); body[b:b + self.h, b:b + self.width] = c
        a = self.mask[..., None]; reg = out[M:M + hh, M:M + ww]
        reg[..., :3] = body * a; reg[..., 3] = np.maximum(self.mask, reg[..., 3])
        for t, (tx, ty) in self.tape_imgs:
            th, tw = t.shape[:2]; ty2, tx2 = max(0, ty), max(0, tx)
            sub = out[ty2:ty2 + th, tx2:tx2 + tw]; tt = t[:sub.shape[0], :sub.shape[1]]
            ta = tt[..., 3:4]; sub[..., :3] = sub[..., :3] * (1 - ta) + tt[..., :3] * ta; sub[..., 3] = np.maximum(sub[..., 3], tt[..., 3])
        return out
def beat_grid():
    """Frappes réelles (kick + caisse nettes)."""
    g = sorted(set([round(x[0], 4) for x in HITS if x[3] > 0.1]))
    out = []
    for t in g:
        if not out or t - out[-1] > 0.2: out.append(t)
    return out
BEATS = beat_grid(); BEATF = [fr(b) for b in BEATS]
def nbeat(f): return sum(1 for b in BEATF if b <= f)
def jit(key, k, amp=8.0, ang=1.5):
    r = np.random.default_rng(skey(key) * 1000 + k); return r.uniform(-amp, amp), r.uniform(-amp, amp), r.uniform(-ang, ang)
def sticker(m, r=7):
    return cv2.dilate(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1)))
_TE = {}
def torn_edges(colhex=NEWS):
    """Bords de papier journal déchiré en haut et en bas (plan plein cadre collé comme une photo)."""
    if colhex not in _TE:
        rng = np.random.default_rng(11); out = np.zeros((H, W, 4), np.float32); col = hexc(colhex)
        for y0, y1 in ((0, 150), (H - 170, H)):
            pts = [(0, y0)] if y0 == 0 else [(0, y1)]
            ys = (lambda: rng.uniform(95, 150)) if y0 == 0 else (lambda: H - rng.uniform(110, 170))
            pts += [(x, ys()) for x in range(0, W + 12, 12)]; pts += [(W, y0)] if y0 == 0 else [(W, y1)]
            m = np.zeros((H, W), np.float32); cv2.fillPoly(m, [np.array(pts, np.int32)], 1.0, lineType=cv2.LINE_AA)
            sh_ = cv2.GaussianBlur(np.roll(m, 8 if y0 == 0 else -8, axis=0), (0, 0), 5) * 0.5
            out[..., 3] = np.maximum(out[..., 3], np.maximum(m, sh_)); out[..., :3] += m[..., None] * col
        _TE[colhex] = out
    return _TE[colhex]

# ---------------- plans ----------------
FIN2 = min(b for b in BEATS if b > CUTS[9] + 0.35) - CUTF[9] / FPS          # 2e ligne du carton sur la frappe suivante
FIN3 = min(b for b in BEATS if b > CUTF[9] / FPS + FIN2 + 0.2) - CUTF[9] / FPS   # « 2027 » (règle Luca : nom + année de l'élection) sur la frappe d'après
P1_TXT = [[("LE", wt(0)), ("BUT", wt(1))], [("RESTE", wt(2))]]
P2a_TXT = [[("L'ABROGATION", wt(3))], [("DE", wt(4)), ("LA", wt(5))], [("RÉFORME", wt(6))]]
P2b_TXT = [[("DES", wt(7)), ("RETRAITES", wt(8))], [("À", wt(9)), ("64", wt(10)), ("ANS", wt(11))]]
P3a_TXT = [[("PUIS", wt(12))]]
P3b_TXT = [[("LE", wt(13)), ("RETOUR", wt(14))], [("À", wt(15)), ("60", wt(16)), ("ANS", wt(17))]]
KEY = ("64", "60", "SMIC", "1 700 €")
WB = (560, 330, 1420, 1080)           # plan large de dos (synchro) : Mélenchon face à la foule, logo 2027 hors cadre (x > 1560)
SHOTS = [
    dict(id="P1", kind="full", src="SD", t="sync", crop=(980, 560, 1040), push=(1.0, 1.04), focus=(980, 640), tone="bw",
         txt=P1_TXT, txt_y=290, txt_h=190, strips=2, sync=True,
         why="2026 — Saint-Denis, plan large de dos synchro (« Le but reste »), Mélenchon face à la foule, N&B plein cadre collé, bords de papier journal"),
    dict(id="P2a", kind="collage", bg=GREEN, sync=True,
         photos=[("SD", "sync", WB, 640, (560, 1180), -4, 0.0, "bw"), ("C404", 3.6, (0, 300, 1300, 1080), 520, (330, 1560), 5, 0.98, "duo")],
         txt=P2a_TXT, txt_y=250, txt_h=140, strips=4,
         why="plan large de dos synchro en photo N&B vivante (« l'abrogation de la réforme des ») + foule aux drapeaux en duotone vert, sur vert brat"),
    dict(id="P2b", kind="collage", bg=BLACK, sync=True,
         photos=[("SD", "sync", (720, 360, 1240, 1000), 560, (380, 1220), 5, 0.0, "duo"), ("C408", 14.0, (0, 260, 1500, 1080), 560, (720, 1520), -5, 0.49, "bw")],
         txt=P2b_TXT, txt_y=280, txt_h=190, strips=4,
         why="même plan de dos synchro, plus serré, en duotone (« retraites à 64 ans ») + foule poings levés N&B, sur noir"),
    dict(id="P3a", kind="collage", bg=NEWS, sync=True,
         photos=[("SD", 102.0, (0, 310, 1350, 1080), 700, (540, 1160), 3, 0.0, "duo"), ("C404", 2.4, (0, 300, 1300, 1080), 480, (760, 1560), -6, 0.5, "bw")],
         txt=P3a_TXT, txt_y=330, txt_h=200, strips=4, letters=("PUIS",),
         why="foule de Saint-Denis (pas de visage qui parle sous « puis »), papier journal, photos duotone et N&B"),
    dict(id="P3b", kind="cut", src="SD", t="sync", bg=GREEN, box=(560, 60, 1700, 800), scale=(1.42, 1.48), cx=1020, sync=True,
         txt=P3b_TXT, txt_y=260, txt_h=215, strips=5,
         photos=[("C408", 18.0, (0, 260, 1500, 1080), 500, (300, 930), -6, 0.0, "duo"), ("SD", 101.0, (0, 310, 1350, 1080), 470, (790, 860), 5, 0.0, "bw")],
         why="2026 — Saint-Denis, gros plan synchro « le retour à 60 ans », Mélenchon détouré (contour autocollant) sur vert brat, coupé au bord du pupitre"),
    dict(id="D1", kind="sil", src="C405", t=4.10, bg=BLACK, box=(0, 0, 1920, 785), dest_w=2160, cx=940, push=(1.0, 1.03),
         txt=[[("LE", 0.0), ("RETOUR", 0.0)], [("À", 0.0), ("60", 0.0), ("ANS", 0.0)]], txt_y=270, txt_h=200,
         strips=4, flash=True, why="DROP — Saint-Denis, bras grands ouverts : silhouette blanche 3 images (flash) puis Mélenchon détouré en couleur sur noir, bras qui sortent du cadre"),
    dict(id="D2", kind="collage", bg=GREEN,
         photos=[("C408", 21.0, (0, 260, 1500, 1080), 620, (560, 1180), -4, 0.0, "bw"), ("C404", 6.0, (0, 300, 1300, 1080), 460, (330, 1560), 6, 0.25, "duo"),
                 ("SD", 103.5, (0, 310, 1350, 1080), 460, (790, 1580), -5, 0.5, "bw")],
         txt=[[("LE", 0.0), ("SMIC", 0.0)], [("À", 0.0), ("1 700 €", 0.0)]], txt_y=270, txt_h=200, strips=4,
         why="tract : SMIC à 1 700 euros (dit dans le même discours, 105,5-107,9 s) en lettres découpées, photos de la foule qui s'empilent"),
    dict(id="D3", kind="full", src="C402", t=3.0, crop=(1250, 540, 1080), push=(1.0, 1.04), focus=(1300, 640), tone="color",
         flash=True,
         why="2026 — Saint-Denis, mairie, basilique et place noire de monde, plein cadre couleur, bords de papier journal ; sans texte (respiration entre deux mesures)"),
    dict(id="D4", kind="cut", src="CV03", t=2.0, bg=GREEN, box=(300, 0, 1600, 1080), scale=(1.0, 1.03), cx=940, bottom=1920,
         txt=[[("LA", 0.0), ("SÉCURITÉ", 0.0)], [("SOCIALE", 0.0)], [("INTÉGRALE", 0.0)]], txt_y=250, txt_h=140, strips=5,
         photos=[("SD", 104.5, (0, 310, 1350, 1080), 420, (850, 900), 7, 0.0, "duo")],
         why="convention 2025, Mélenchon souriant détouré sur vert brat ; sécurité sociale intégrale (dit dans le même discours, 111,9-115,4 s)"),
    dict(id="D5", kind="collage", bg=BLACK,
         photos=[("SD", 98.0, (0, 310, 1350, 1080), 600, (540, 1150), 3, 0.0, "duo"), ("C408", 16.0, (0, 260, 1500, 1080), 470, (330, 1520), -6, 0.25, "bw"),
                 ("C408", 22.5, (0, 260, 1500, 1080), 470, (760, 1600), 5, 0.5, "bw")],
         strips=6,
         why="le tract se remplit : photos de Saint-Denis collées au demi-temps, sans texte (pas de redite des mesures)"),
    dict(id="FIN", kind="card", bg=GREEN, strips=3,
         txt=[[("JEAN-LUC", 0.0)], [("MÉLENCHON", 0.0)], [("2027", FIN2)]], txt_y=560, txt_h=330, letters=("JEAN-LUC", "MÉLENCHON", "2027"),
         why="carton final ransom-note (retour Luca : le carton brat flouté n'était pas beau) : le nom posé en entier, puis 2027 en grand sur la frappe suivante, en lettres découpées "
             "serif/sans, penchées, trame, scotch aux bouts des lignes, sur vert brat ; chaque ligne arrive sur une frappe et remplit la zone sûre"),
]
BOUNDS_T = [0] + CUTF + [fr(END)]
assert len(BOUNDS_T) == len(SHOTS) + 1, (len(BOUNDS_T), len(SHOTS))
for i, sh in enumerate(SHOTS):
    sh["a"], sh["bb"] = BOUNDS_T[i], BOUNDS_T[i + 1]; sh["n"] = sh["bb"] - sh["a"]; sh["clip"] = "R4_%s.mov" % sh["id"]
    if sh.get("t") == "sync": sh["t"] = src_of_tl(sh["a"] / FPS)
    sh["photos"] = [tuple(p[:1]) + ((src_of_tl(sh["a"] / FPS) if p[1] == "sync" else p[1]),) + tuple(p[2:]) for p in sh.get("photos", [])]
assert min(sh["n"] for sh in SHOTS) >= 15, [(s["id"], s["n"]) for s in SHOTS]

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
    def abs_pieces(p, timeline_abs):
        return [(im, cx, cy, (t if timeline_abs else rel(t))) for im, cx, cy, t in p]
    global AVOID
    sync = sh.get("sync", False); AVOID = rgb(sh["bg"]) if sh.get("bg") else None
    txt = abs_pieces(board(sh["txt"], sh["txt_y"], seed=skey(sh["id"]) * 7, letters=sh.get("letters", KEY), h=sh.get("txt_h", 118),
                               **(dict(xmin=0.178 * W, xmax=0.822 * W, maxw=0.644 * W - 10) if sh["kind"] == "card" else {})), sync) if sh.get("txt") else []
    big = []
    if sh.get("big"):
        card = sh["kind"] == "card"
        big = abs_pieces(big_text([(s, t, c) for s, t, c in sh["big"]], sh["big_y"], None, sizes=sh["big_sizes"], spec=(FBRAT if card else FCOND),
                                  maxw=(XMAX - XMIN) * (0.95 if card else 1.0), contour=0 if card else 10, blur=2.2 if card else 0,
                                  gap=10 if card else -18), False)
    photos = [Photo(read_frames(ps, pt, n), pbox, pw, pc, pa, fr(rel(pt0)), (sh["id"], j), tone)
              for j, (ps, pt, pbox, pw, pc, pa, pt0, tone) in enumerate(sh.get("photos", []))]
    strips = make_strips(sh)
    k0 = nbeat(a)
    if sh["kind"] in ("cut", "sil", "full"):
        raw = read_frames(sh["src"], sh["t"], n)
    if sh["kind"] in ("cut", "sil"):
        ms = masks("%s_%s_%.2f_%d" % (sh["id"], sh["src"], sh["t"], n), raw, sh["box"], k=27 if sh["kind"] == "sil" else 13)
    for i in range(n):
        f = a + i; u = i / max(n - 1, 1); kb = nbeat(f) - k0
        if sh["kind"] == "full":
            cx, cy, vh = sh["crop"]; z = sh["push"][0] + (sh["push"][1] - sh["push"][0]) * u
            s = H / vh * z; fx_, fy_ = sh["focus"]
            ccx = cx + (fx_ - cx) * (1 - 1 / z); ccy = cy + (fy_ - cy) * (1 - 1 / z)
            M = np.float32([[s, 0, W / 2 - ccx * s], [0, s, H / 2 - ccy * s]])
            im0 = cv2.warpAffine(raw[i], M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
            img = bw(im0, 1.2) if sh.get("tone") == "bw" else grade(im0, 1.1)
        else:
            img = paper(sh["bg"])
        for st in strips:                                                   # une bande de plus à chaque frappe
            if st["k"] <= kb:
                dx, dy, da = jit((sh["id"], "s", st["k"]), nbeat(f), amp=6, ang=1.2)
                s_ = pop(f, BEATF[k0 + st["k"] - 1] if st["k"] > 0 and k0 + st["k"] - 1 < len(BEATF) else a, n=4, amp=0.08) or 1.0
                if sh["kind"] == "full" and abs(st["cy"] - H / 2) < 500: continue          # plein cadre : bandes seulement sur les bords
                paste(img, st["img"], st["cx"] + dx, st["cy"] + dy, s_, st["ang"] + da)
        for ph in photos:
            s_ = pop(f, ph.f0, n=5, amp=0.10)
            if s_ is not None:
                dx, dy, da = jit(ph.key, nbeat(f), amp=9, ang=1.8)
                paste(img, ph.rgba(i), ph.center[0] + dx, ph.center[1] + dy, s_, ph.angle + da)
        if sh["kind"] == "cut":
            x0, y0, x1, y1 = sh["box"]; sc = sh["scale"][0] + (sh["scale"][1] - sh["scale"][0]) * u
            m = ms[i]; rgba = cutout_rgba(raw[i], m, sh["box"]); hh = (y1 - y0) * sc
            st_ = np.dstack([np.ones_like(rgba[..., :3]) * np.array([0.97, 0.97, 0.95], np.float32), sticker(m)])
            sd = st_.copy(); sd[..., :3] = 0; sd[..., 3] = cv2.GaussianBlur(st_[..., 3], (0, 0), 5) * 0.5
            fcx = (sh["cx"] - x0) * sc; ccx = W / 2 + ((x1 - x0) / 2 * sc - fcx); ccy = sh.get("bottom", H) - hh / 2
            paste(img, sd, ccx + 10, ccy + 8, sc); paste(img, st_, ccx, ccy, sc); paste(img, rgba, ccx, ccy, sc)
        elif sh["kind"] == "sil":
            x0, y0, x1, y1 = sh["box"]; z = sh["push"][0] + (sh["push"][1] - sh["push"][0]) * u
            sc = sh["dest_w"] / (x1 - x0) * z; hh = (y1 - y0) * sc; m = ms[i]
            ccx = W / 2 + ((x1 - x0) / 2 - (sh["cx"] - x0)) * sc; ccy = H - hh / 2
            st_ = np.dstack([np.ones((m.shape[0], m.shape[1], 3), np.float32) * hexc(GREEN), sticker(m, 9)])     # contour vert brat
            sd = st_.copy(); sd[..., :3] = 0; sd[..., 3] = cv2.GaussianBlur(st_[..., 3], (0, 0), 6) * 0.55
            paste(img, sd, ccx + 14, ccy + 10, sc)
            if i < 3: paste(img, cutout_rgba(raw[i], m, sh["box"], white=True), ccx, ccy, sc)
            else: paste(img, st_, ccx, ccy, sc); paste(img, cutout_rgba(raw[i], m, sh["box"]), ccx, ccy, sc)
        if sh["kind"] == "full":
            te = torn_edges(NEWS); img = img * (1 - te[..., 3:4]) + te[..., :3]
        draw_pieces(img, txt, f, boil=sh["id"])
        if sh["kind"] == "card":                                            # scotch aux deux bouts de chaque ligne de lettres
            lines = {}
            for im, cx, cy, t in txt: lines.setdefault(round(cy), []).append((cx - im.shape[1] / 2, cx + im.shape[1] / 2, cy - im.shape[0] / 2, t))
            for j, (cy, ps) in enumerate(sorted(lines.items())):
                if f < fr(ps[0][3]): continue
                xl, xr, top = min(p[0] for p in ps), max(p[1] for p in ps), min(p[2] for p in ps)
                paste(img, CARD_TAPES[2 * j % 4], xl + 4, cy, 0.55, 70 + 8 * j)          # bande verticale sur le bord gauche de la ligne
                paste(img, CARD_TAPES[(2 * j + 1) % 4], xr - 4, cy, 0.55, -70 - 8 * j)
        if big:
            if sh["kind"] == "card":
                z = sh["push"][0] + (sh["push"][1] - sh["push"][0]) * u
                for im, cx, cy, t in big:
                    s_ = pop(f, fr(t), amp=0.06)
                    if s_ is not None: paste(img, im, W / 2 + (cx - W / 2) * z, H / 2 + (cy - H / 2) * z, s_ * z)
            else: draw_pieces(img, big, f)
        if sh.get("flash") and i < 3: img = img + (1 - img) * [1.0, 0.6, 0.25][i]
        frames.append(finish(img, f))
    write_mov(frames, OUT + sh["clip"])
    print("  %-4s %3d im  (%s)" % (sh["id"], n, sh["kind"]))

# ---------------- audio ----------------
def make_audio():
    import soundfile as sf
    sr = 48000; N = int(round(END * sr))
    def grab(path, t, dur):
        p = subprocess.run([FF, "-v", "error", "-ss", "%.3f" % t, "-t", "%.3f" % dur, "-i", path, "-ac", "2", "-ar", str(sr), "-f", "f32le", "-"], capture_output=True)
        return np.frombuffer(p.stdout, np.float32).reshape(-1, 2).copy()
    voix = np.zeros((N, 2), np.float32); mus = np.zeros((N, 2), np.float32)
    for a, b, t0 in VP:
        v = grab(HG + "/" + SRC["SD"][0], a, b - a); env = np.ones(len(v), np.float32)
        k = int(0.03 * sr); env[:k] = np.linspace(0, 1, k); k = int(0.06 * sr); env[-k:] = np.linspace(1, 0, k)
        i0 = int(round(t0 * sr)); voix[i0:i0 + len(v)] += v * env[:, None] * 10 ** (3 / 20)
    m = music_raw(MUSIC_IN)[:N]
    t = np.arange(len(m)) / sr; vend = VP[-1][2] + VP[-1][1] - VP[-1][0]; dr = CUTS[4]
    # sous la phrase : pré-refrain à -19 dB (voix chantée sous Mélenchon), montée jusqu'à -10 dB à la fin de la phrase, pleine sur le drop
    gdb = np.interp(t, [0, 0.4, vend, dr - 0.03, dr, END], [-22, -19, -10, -6, 0, 0])
    k = int(0.35 * sr); fo = np.ones(len(m), np.float32); fo[-k:] = np.linspace(1, 0, k)
    mus[:len(m)] = m * (10 ** (gdb / 20) * fo)[:, None]
    sf.write(OUT + "R4-voix.wav", voix, sr, subtype="PCM_24"); sf.write(OUT + "R4-musique.wav", mus, sr, subtype="PCM_24")
    sf.write(D + "tmp_mix.wav", voix + mus, sr, subtype="FLOAT")
    r = subprocess.run([FF, "-hide_banner", "-i", D + "tmp_mix.wav", "-af", "loudnorm=I=-14:TP=-2.5:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    js = json.loads(r[r.rindex("{"):r.rindex("}") + 1])
    af = ("loudnorm=I=-14:TP=-2.5:LRA=11:measured_I=%s:measured_TP=%s:measured_LRA=%s:measured_thresh=%s:offset=%s:linear=true,"
          "aresample=48000" % (js["input_i"], js["input_tp"], js["input_lra"], js["input_thresh"], js["target_offset"]))
    subprocess.run([FF, "-v", "error", "-y", "-i", D + "tmp_mix.wav", "-af", af, "-c:a", "pcm_s24le", OUT + "R4-mix.wav"], check=True)
    os.remove(D + "tmp_mix.wav"); print("audio : mix avant normalisation", js["input_i"], "LUFS")

# ---------------- plan ----------------
PHRASE = "Le but reste l'abrogation de la réforme des retraites à 64 ans, puis le retour à 60 ans."
def build_plan():
    video = []
    for sh in SHOTS:
        v = {"id": sh["id"], "clip": sh["clip"], "folder": "genR4", "path": OUT + sh["clip"], "s": 0, "e": sh["n"], "rec": sh["a"], "dur": sh["n"],
             "clip_fps": FPS, "speed_pct": 100, "track": 1, "note": sh["why"], "kind": sh["kind"], "temps": round(sh["n"] / FPS / T, 2)}
        if sh.get("src"):
            path, sfps, url, off, ctx = SRC[sh["src"]]
            v["source"] = {"fichier": path, "in_s": round(sh["t"], 3), "out_s": round(sh["t"] + sh["n"] / FPS, 3), "fps": sfps, "url": url, "contexte": ctx}
            if off is not None: v["source"]["youtube_s"] = [round(off + sh["t"], 2), round(off + sh["t"] + sh["n"] / FPS, 2)]
        if sh.get("photos"):
            v["photos"] = [{"fichier": SRC[p[0]][0], "in_s": round(p[1], 3), "out_s": round(p[1] + sh["n"] / FPS, 2), "cadre_source": p[2], "ton": p[7],
                            "url": SRC[p[0]][2]} for p in sh["photos"]]
        video.append(v)
    texts = []
    for sh in SHOTS:
        for line in sh.get("txt", []): texts.append({"plan": sh["id"], "texte": " ".join(w for w, _ in line)})
        for s_, t_, c_ in sh.get("big", []): texts.append({"plan": sh["id"], "texte": s_})
    plan = {"name": "R4 - Collage ransom-note tract brat - Jean-Luc Mélenchon", "fps": FPS, "w": W, "h": H, "duree_s": END,
            "note": "Plans ProRes 9:16 composés en Python (lot6/_claude/gen/R4/out) : papier vert brat / noir / journal + grain et fibres, Mélenchon détouré "
                    "(segment/Vision), silhouette blanche au drop, photos vivantes N&B et duotone vert, coupures de journal, scotch, textes ransom-note cuits. "
                    "s/e en images du clip (30 i/s), rec en images timeline. Coupes sur les frappes réelles de 360 (out/R4-frappes.json). Aucun ralenti. Générateur : lot6/_claude/gen/R4/genR4.py",
            "phrase": {"texte": PHRASE, "url": URL_SD, "source": SRC["SD"][0], "in_s": 123.45, "out_s": 135.62, "youtube_s": [3123.45, 3135.62],
                       "morceaux_voix": [{"source_s": [a, b], "youtube_s": [round(3000 + a, 2), round(3000 + b, 2)], "timeline_s": [t0, round(t0 + b - a, 2)]} for a, b, t0 in VP],
                       "voix": "son direct ; silence (124,32-126,46) et applaudissements (130,22-132,24) raccourcis entre les membres de phrase, aucun mot coupé. "
                               "Images sous la voix : plan large de dos synchro (P1, P2), foule (P3a), gros plan synchro (P3b)",
                       "mesures_tract": {"SMIC À 1 700 €": "« le SMIC passera à 1 700 euros », même discours 105,48-107,90 s",
                                         "SÉCURITÉ SOCIALE INTÉGRALE": "« une sécurité sociale intégrale », même discours 111,94-115,42 s",
                                         "RETRAITE À 60 ANS": "phrase entendue"}},
            "musique": {"fichier": "lot6/sons/R4-charlixcx-360_complet.wav", "titre": "Charli xcx - 360", "url": SON_URL,
                        "debut_complet_s": round(MUSIC_IN, 4), "fin_complet_s": round(MUSIC_IN + END, 3), "drop_timeline_s": CUTS[4],
                        "coupes_frappes_s": CUTS, "coupes_images": CUTF},
            "textes": texts, "video": video,
            "audio": [{"id": "mix", "clip": "R4-mix.wav", "folder": "genR4", "path": OUT + "R4-mix.wav", "rec": 0, "track": 1,
                       "note": "mix -14 LUFS : voix SD en 3 morceaux (+3 dB) ; 360 dès %.3f s du complet (pré-refrain / début de refrain -19 dB sous la voix, montée à -10 dB, plein au drop sur « I'm everywhere, I'm so Julia »), fondu de fin 0,35 s" % MUSIC_IN}],
            "stems": ["lot6/_claude/gen/R4/out/R4-voix.wav", "lot6/_claude/gen/R4/out/R4-musique.wav"],
            "logos_exclus": "Saint-Denis : filigrane MELENCHON2027.fr (haut droite) hors des cadres, pupitre « Meeting Saint-Denis » sous la découpe ; convention : logos hors détourage"}
    json.dump(plan, open(D + "plan-R4.json", "w"), indent=1, ensure_ascii=False)
    son = {"id": "R4", "titre": "360", "artiste": "Charli xcx", "url": SON_URL,
           "chaine": "Charli xcx (officielle, certifiée, « Charli xcx - 360 (official lyric video) »)",
           "fichier": "lot6/sons/R4-charlixcx-360_complet.wav",
           "extrait_complet_s": {"debut": round(MUSIC_IN, 4), "fin": round(MUSIC_IN + END, 3)},
           "paroles_audibles": "sous la phrase (baissé) : fin du pré-refrain « looking like an icon, work angles, yeah, 360 » puis « When you're in the mirror, do you like what you see? When you're in the mirror, you're just looking at me » ; au drop : « I'm everywhere, I'm so Julia », « oh, oh, oh, oh », « When you're in the party… », « 666 with the princess… »",
           "bpm": 120.0, "temps_s": T,
           "drop": {"complet_s": round(MUSIC_IN + CUTS[4], 4), "timeline_s": CUTS[4], "nature": "refrain, « I'm everywhere, I'm so Julia » (moment le plus connu), musique pleine après la montée sous la voix"},
           "frappes_timeline_s": BEATS, "coupes_sur_frappes_s": CUTS,
           "mix": "lot6/_claude/gen/R4/out/R4-mix.wav"}
    json.dump(son, open(D + "son.json", "w"), indent=1, ensure_ascii=False)

# ---------------- aperçu 540x960 ----------------
def apercu():
    plan = json.load(open(D + "plan-R4.json")); ins = []; fl = []
    for i, v in enumerate(plan["video"]):
        ins += ["-i", OUT + v["clip"]]
        fl.append("[%d:v]trim=start_frame=%d:end_frame=%d,setpts=PTS-STARTPTS,scale=540:960,setsar=1[v%d]" % (i, v["s"], v["e"], i))
    k = len(plan["video"]); fl.append("".join("[v%d]" % i for i in range(k)) + "concat=n=%d:v=1:a=0[v]" % k)
    ins += ["-i", OUT + "R4-mix.wav"]; out = HG + "/preview/apercu-R4.mp4"
    subprocess.run([FF, "-v", "error", "-y"] + ins + ["-filter_complex", ";".join(fl), "-map", "[v]", "-map", "%d:a" % k,
                    "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "aac", "-b:a", "192k", "-shortest", out], check=True)
    print("aperçu", out)
# ---------------- mesure sur l'export : coupes vs frappes, LUFS / TP ----------------
def mesure():
    out = HG + "/preview/apercu-R4.mp4"
    r = subprocess.run([FF, "-v", "info", "-i", out, "-vf", "scale=135:240,select='gt(scene,0.2)',showinfo", "-an", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    cuts = [float(x) for x in re.findall(r"pts_time:([0-9.]+)", r)]
    p = subprocess.run([FF, "-v", "error", "-i", out, "-vn", "-ac", "2", "-ar", "48000", "-f", "f32le", "-"], capture_output=True)
    y = np.frombuffer(p.stdout, np.float32).reshape(-1, 2)
    print("coupes image détectées (export) :", cuts)
    worst = 0
    for c in [fr_ / FPS for fr_ in CUTF]:
        # détection locale (fenêtre de 2 s autour de la coupe) : les frappes faibles de l'intro sous la voix ressortent
        i0 = max(0, int((c - 1.0) * 48000)); hh = [(x[0] + i0 / 48000,) + tuple(x[1:]) for x in detect_hits(y[i0:i0 + int(2.0 * 48000)])]
        det = min(cuts, key=lambda x: abs(x - c)) if cuts else None
        k, typ = min(((x[0], x[1]) for x in hh), key=lambda t: abs(t[0] - c)); e = (c - k) * 1000; worst = max(worst, abs(e))
        print("  coupe %.3f (détectée %s)  frappe %.4f (%s)  écart %+.1f ms" % (c, "%.3f" % det if det is not None else "-", k, typ, e))
    print("écart max coupes/frappes : %.1f ms" % worst)
    r = subprocess.run([FF, "-hide_banner", "-i", out, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    print(r[r.rindex("Summary"):])
if __name__ == "__main__":
    args = set(a for a in sys.argv[1:] if not a.startswith("only=")) or ({"shots", "audio", "plan", "apercu"} if not any(a.startswith("only=") for a in sys.argv[1:]) else set())
    only = [x for a in sys.argv[1:] if a.startswith("only=") for x in a.split("=", 1)[1].split(",")]
    print("musique dès %.4f s ; coupes (s) :" % MUSIC_IN, [round(c, 4) for c in CUTS], "images :", CUTF)
    if "shots" in args or only:
        for sh in SHOTS:
            if not only or sh["id"] in only: render(sh)
    if "audio" in args: make_audio()
    if "plan" in args: build_plan()
    if "apercu" in args: apercu()
    if "mesure" in args: mesure()
