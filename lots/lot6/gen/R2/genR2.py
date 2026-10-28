# R2 (lot 6) — Collage ransom-note poussé (modèle lot5 R1, inspi @abdulelsayed), Jean-Luc Mélenchon, son Kendrick Lamar – Not Like Us.
# Palette : rouge, noir, papier journal (fond journal à fausses colonnes de texte, découpes N&B à rouge sélectif, photos N&B).
# Plus que R1 : fond papier journal, puces de texte en papier journal, écho rouge/noir décalé derrière chaque découpe (mauvais
#   repérage d'imprimerie), bandes déchirées trame/colonnes, plein cadre en bichromie noir-rouge-papier, flash blanc 3 images
#   seulement au drop et à l'entrée du plein cadre.
# Phrase (son direct, synchro) : « Ils en ont fait 1200 milliards de dettes. Alors ils sont les derniers à pouvoir venir nous
#   donner des leçons » (meeting de Clermont-Ferrand, 11/10/2026, chaîne JEAN-LUC MÉLENCHON, youtu.be/sBvVfHxcJp4 2635,0-2644,5 s)
#   -> autre phrase que A6 (camp des oubliés), M1, S1, C3, W1 ; plans nouveaux (extrait lot6/sources/R2-melenchon-clermont-2600).
# Son : Not Like Us (piste officielle, chaîne Kendrick Lamar) : la phrase passe sur la fin du couplet puis le break « A minor »,
#   drop = retour du beat (73,69 s) juste avant « They not like us » (74,52 s), coupes sur les claps réels toutes les 2 temps.
# Usage : python genR2.py [shots] [audio] [plan] [apercu] [mesure] [only=ID,ID]   (sans argument = tout sauf mesure)
import sys
sys.dont_write_bytecode = True
import os, json, subprocess, math, re
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
HG = "/Users/luca.grousset/Movies/highkey-gauchiste"
D = HG + "/lot6/_claude/gen/R2/"; OUT = D + "out/"; CACHE = D + "cache/"; os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, D)
from hits import detect_hits
FF = "/opt/homebrew/bin/ffmpeg"; SEG = HG + "/_claude/outils/segment"; FPS = 30; W, H = 1080, 1920
def fr(t): return int(round(t * FPS))
def hexc(h): h = h.lstrip("#"); return np.array([int(h[4:6], 16), int(h[2:4], 16), int(h[0:2], 16)], np.float32) / 255   # BGR
def rgb(h): h = h.lstrip("#"); return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
RED, BLACK, NEWS, NEWSD, GREY, WHITE = "#D0161B", "#141414", "#E7E1D0", "#CFC7B2", "#7D7A73", "#F7F5EF"

# ---------------- sources (lecture seule) ----------------
SRC = {
    "CL": ("lot6/sources/R2-melenchon-clermont-2600.mp4", 60.0, "https://www.youtube.com/watch?v=sBvVfHxcJp4", 2600.0,
           "meeting de Clermont-Ferrand, 11/10/2026 (chaîne JEAN-LUC MÉLENCHON), extrait 2600-2680 s"),
    "FIN": ("lot3/sources/A6-melenchon-clermont-5680.mp4", 60.0, "https://www.youtube.com/watch?v=sBvVfHxcJp4", 5680.0,
            "meeting de Clermont-Ferrand, 11/10/2026 (chaîne JEAN-LUC MÉLENCHON), fin du meeting"),
}
CAM_CUT = 39.50                       # CL : coupe caméra pupitre -> plan large de la salle (scène détectée)

# ---------------- musique : Kendrick Lamar – Not Like Us ----------------
SON_FILE = HG + "/lot6/sons/R2-kendrick-not-like-us_complet.wav"; SON_URL = "https://www.youtube.com/watch?v=T6eK-2OQtew"
T = 0.59406                           # 101,0 BPM (claps 62,40 -> 81,41 s, grille vérifiée)
B0 = 67.1529                          # clap mesuré (fin de « A minor ») ; grille b_k = B0 + k T, valable à travers le break
MDROP = 73.690                        # retour du beat (kick + clap) après le break « A minor » ; « They not like us » 74,52
M_END = 82.95                         # avant « You think the bag… » (82,96) : fin sur le 6e « They not like us »
# coupes (temps du morceau) : claps mesurés, 2 notes réelles du riff dans le break (onsets 68,371 / 70,751), drop, puis claps
CUT_M = [64.7767, 67.1529, 68.371, 70.751, MDROP, 74.2817, 75.4698, 76.658, 77.846, 79.0522, 80.2222]
MUSIC_IN0 = B0 - 6 * T                # départ sur un temps (63,59 s)
def music_raw(mi, dur, sr=48000):
    import soundfile as sf
    i0 = int(round(mi * sr)); x, r = sf.read(SON_FILE, start=i0, frames=int(dur * sr), dtype="float32"); assert r == sr; return x
def best_in():
    """Décalage fin (±16 ms) du départ musique pour que chaque coupe tombe au plus près d'un bord d'image."""
    best, bad = 0.0, 9
    for off in np.arange(-0.016, 0.0165, 0.001):
        e = max(abs((m - MUSIC_IN0 - off) - fr(m - MUSIC_IN0 - off) / FPS) for m in CUT_M)
        if e < bad: best, bad = off, e
    return MUSIC_IN0 + best
FINE = 0.0                            # recalage mesuré sur l'export AAC (voir mesure)
MUSIC_IN = best_in() + FINE
CUTS = [m - MUSIC_IN for m in CUT_M]; CUTF = [fr(c) for c in CUTS]
DROPF = CUTF[4]; DROP = CUTS[4]
END = M_END - MUSIC_IN
BEATS = [B0 + k * T - MUSIC_IN for k in range(-6, 28)]; BEATF = [fr(b) for b in BEATS]
def nbeat(f): return sum(1 for b in BEATF if b <= f)

# ---------------- voix ----------------
V_SRC0 = CAM_CUT + 0.02 - CUTF[2] / FPS     # source CL à t = 0 : la coupe A3/B1 tombe juste après la coupe caméra (39,50 s)
V_IN, V_OUT = 34.98, 44.50            # « Ils » (35,04) … « leçons » (fin 44,45) ; « surtout que » (44,58) non gardé
def t_of_src(s): return s - V_SRC0
WORDS = [("ILS", 35.04), ("EN", 35.24), ("ONT", 35.36), ("FAIT", 35.52), ("1 200", 36.04), ("MILLIARDS", 37.52), ("DE", 38.24),
         ("DETTES", 38.40), ("ALORS", 39.36), ("ILS", 39.76), ("SONT", 39.88), ("LES", 40.08), ("DERNIERS", 40.24), ("À", 41.44),
         ("POUVOIR", 41.64), ("VENIR", 42.12), ("NOUS", 43.20), ("DONNER", 43.40), ("DES", 43.72), ("LEÇONS", 43.84)]
def wt(i): return t_of_src(WORDS[i][1])
assert t_of_src(44.45) < DROP - 0.25, ("la phrase déborde sur le drop", t_of_src(44.45), DROP)

# ---------------- polices ransom-note ----------------
S = "/System/Library/Fonts/Supplemental/"
FONTS = [(S + "Arial Black.ttf", 0), (S + "Georgia Bold.ttf", 0), (S + "Times New Roman Bold.ttf", 0), (S + "Impact.ttf", 0),
         (S + "Courier New Bold.ttf", 0), (S + "Rockwell.ttc", 2), (S + "AmericanTypewriter.ttc", 2), (S + "Didot.ttc", 2),
         (S + "Bodoni 72.ttc", 2), (S + "Futura.ttc", 2), (S + "BigCaslon.ttf", 0), (S + "Baskerville.ttc", 1)]
FCOND = (S + "Futura.ttc", 4)
FIMP = (S + "Impact.ttf", 0)
TEX = "TEX"                           # fond « papier journal » (colonnes de faux texte)
STYLES = [(rgb(NEWS), rgb(BLACK)), (rgb(BLACK), rgb(NEWS)), (rgb(RED), rgb(WHITE)), (rgb(WHITE), rgb(RED)),
          (TEX, rgb(BLACK)), (rgb(NEWSD), rgb(BLACK)), (TEX, rgb(RED)), (rgb(BLACK), rgb(RED))]
_fc = {}
def font(spec, size):
    k = (spec, size)
    if k not in _fc: _fc[k] = ImageFont.truetype(spec[0], size, index=spec[1])
    return _fc[k]

# ---------------- papier journal ----------------
_news = {}
def news_texture(w, h, seed, base=NEWS, dark=False):
    """Page de journal : colonnes de faux texte (barres grises, aucune lettre lisible -> rien pour l'OCR TikTok), intertitres, filets."""
    k = (w, h, seed, base, dark)
    if k in _news: return _news[k].copy()
    rng = np.random.default_rng(seed); ink = np.zeros((h, w), np.float32)
    m = 26; ncol = max(1, int(round(w / 240))); g = 16; cw = (w - 2 * m - (ncol - 1) * g) / ncol
    for c in range(ncol):
        x0 = m + c * (cw + g); y = m + rng.uniform(0, 40); first = True
        if c > 0: cv2.line(ink, (int(x0 - g / 2), m), (int(x0 - g / 2), h - m), 0.45, 1)
        while y < h - m - 8:
            if rng.random() < 0.05 or first:                              # intertitre : barres épaisses
                first = False; hh = int(rng.uniform(13, 20)); nl = int(rng.integers(1, 3))
                for _ in range(nl):
                    x = x0
                    while True:
                        ww = int(rng.uniform(26, 80))
                        if x + ww > x0 + cw: break
                        cv2.rectangle(ink, (int(x), int(y)), (int(x + ww), int(y + hh)), 0.85, -1); x += ww + rng.uniform(7, 11)
                    y += hh + 8
                y += 8; continue
            x = x0 + (14 if rng.random() < 0.1 else 0); lim = x0 + cw * (rng.uniform(0.3, 0.9) if rng.random() < 0.08 else 1.0)
            while True:
                ww = int(rng.uniform(7, 46))
                if x + ww > lim: break
                cv2.rectangle(ink, (int(x), int(y)), (int(x + ww), int(y + 4)), 0.62, -1); x += ww + rng.uniform(4, 7)
            y += 10 + (7 if rng.random() < 0.07 else 0)
    ink = cv2.GaussianBlur(ink, (0, 0), 0.7)
    n = cv2.resize(rng.standard_normal((max(2, h // 40), max(2, w // 40))).astype(np.float32), (w, h), interpolation=cv2.INTER_CUBIC)
    n2 = cv2.GaussianBlur(rng.standard_normal((h, w)).astype(np.float32), (0, 0), 1.1)
    b = hexc(base)[None, None, :] * (1 + 0.03 * n[..., None] + 0.035 * n2[..., None])
    inkc = (hexc(NEWS) * 0.9 if dark else np.array([0.20, 0.19, 0.18], np.float32))[None, None, :]
    a = (ink * (0.42 if dark else 0.55))[..., None]
    out = np.clip(b * (1 - a) + inkc * a, 0, 1).astype(np.float32); _news[k] = out
    return out.copy()
TEX_PIL = None
def tex_pil():
    global TEX_PIL
    if TEX_PIL is None:
        t = news_texture(900, 420, 7); TEX_PIL = Image.fromarray((t[..., ::-1] * 255).astype(np.uint8))
    return TEX_PIL

def chip(txt, h, rng, fspec=None, style=None, rot=None, styles=None):
    """Un morceau découpé : rectangle irrégulier (uni ou papier journal) + texte, RGBA PIL, légèrement penché."""
    styles = styles or STYLES
    fspec = fspec or FONTS[rng.integers(len(FONTS))]; bg, fg = style or styles[rng.integers(len(styles))]
    size = int(h * 0.80); f = font(fspec, size)
    x0, y0, x1, y1 = f.getbbox(txt, anchor="ls"); cap = f.getbbox("H", anchor="ls")
    tw, th = x1 - x0, max(y1, 0) - min(y0, cap[1])
    px, py = int(h * (0.08 if len(txt) == 1 else 0.16)), int(h * 0.10)
    w_, h_ = tw + 2 * px, th + 2 * py
    im = Image.new("RGBA", (w_ + 12, h_ + 12), (0, 0, 0, 0)); j = lambda: rng.integers(-4, 5)
    poly = [(6 + j(), 6 + j()), (6 + w_ + j(), 6 + j()), (6 + w_ + j(), 6 + h_ + j()), (6 + j(), 6 + h_ + j())]
    if bg == TEX:
        t = tex_pil(); ox, oy = int(rng.integers(0, max(1, t.width - im.width))), int(rng.integers(0, max(1, t.height - im.height)))
        crop = t.crop((ox, oy, ox + im.width, oy + im.height)).convert("RGBA")
        mk = Image.new("L", im.size, 0); ImageDraw.Draw(mk).polygon(poly, fill=255); im.paste(crop, (0, 0), mk)
    else:
        ImageDraw.Draw(im).polygon(poly, fill=bg + (255,))
    ImageDraw.Draw(im).text((6 + px - x0, 6 + py - min(y0, cap[1])), txt, font=f, fill=fg + (255,), anchor="ls")
    a = rot if rot is not None else rng.uniform(-4, 4)
    return im.rotate(a, resample=Image.BICUBIC, expand=True)
def word_img(word, h, rng, letters=False, styles=None):
    if not letters: return chip(word, h, rng, styles=styles)
    parts = [chip(c, h * rng.uniform(0.92, 1.06), rng, rot=rng.uniform(-7, 7), styles=styles) for c in word if c != " "]
    wsum = sum(p.width for p in parts) - 12 * (len(parts) - 1) + (int(h * 0.25) if " " in word else 0); hh = max(p.height for p in parts) + 10
    im = Image.new("RGBA", (wsum, hh), (0, 0, 0, 0)); x = 0; k = 0
    for c in word:
        if c == " ": x += int(h * 0.25); continue
        p = parts[k]; k += 1
        im.alpha_composite(p, (x, (hh - p.height) // 2 + int(rng.integers(-5, 6)))); x += p.width - 12
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
    return out                                                              # BGR + alpha, float
XMIN, XMAX, YMIN, YMAX = 0.19 * W, 0.81 * W, 0.13 * H, 0.74 * H          # zone sûre TikTok (0,17-0,83 / 0,12-0,75) + marge
def board(lines, y0, seed, h=112, letters=(), maxw=XMAX - XMIN - 30, bg=None):
    """lines = [[(mot, t_apparition), …], …] -> liste de pièces placées (img, cx, cy, t). Pas de puce de la couleur du fond."""
    rng = np.random.default_rng(seed); pieces = []; y = y0
    clash = {RED: (rgb(RED),), BLACK: (rgb(BLACK),), "NEWS": (TEX, rgb(NEWS), rgb(NEWSD)), "RN": (rgb(RED), TEX, rgb(NEWS), rgb(NEWSD))}.get(bg, ())
    styles = [st for st in STYLES if st[0] not in clash]
    for line in lines:
        imgs = [shadowed(word_img(w, h * (1.12 if w in letters else 1.0), rng, w in letters, styles)) for w, _ in line]
        gap = 8; tot = sum(i.shape[1] for i in imgs) + gap * (len(imgs) - 1)
        sc = min(1.0, maxw / tot); lh = max(i.shape[0] for i in imgs) * sc
        x = W / 2 - tot * sc / 2 + rng.uniform(-14, 14); x = min(max(x, XMIN + 4), XMAX - 4 - tot * sc)
        for (w, t), im in zip(line, imgs):
            if sc < 1: im = cv2.resize(im, (int(im.shape[1] * sc), int(im.shape[0] * sc)), interpolation=cv2.INTER_AREA)
            pieces.append((im, x + im.shape[1] / 2, y + lh / 2, t)); x += im.shape[1] + gap * sc
        y += lh - 6
    for im, cx, cy, t in pieces:                                            # zone sûre (texte)
        assert XMIN - 2 <= cx - im.shape[1] / 2 and cx + im.shape[1] / 2 <= XMAX + 2, ("texte hors zone x", cx, im.shape)
        assert YMIN - 2 <= cy - im.shape[0] / 2 and cy + im.shape[0] / 2 <= YMAX + 2, ("texte hors zone y", cy, im.shape)
    return pieces
def big_text(lines, y0, spec=FCOND, maxw=XMAX - XMIN, sizes=None, contour=0, gap=-18):
    """Texte propre (carton final / gros mots plein cadre) : lignes centrées, largeur max, retour [(img, cx, cy, t)]."""
    pieces = []; y = y0
    for k, (txt, t, col) in enumerate(lines):
        size = (sizes or [300] * len(lines))[k]; f = font(spec, size)
        while f.getlength(txt) > maxw - 2 * contour - 44: size -= 4; f = font(spec, size)
        x0, y0b, x1, y1 = f.getbbox(txt)
        im = Image.new("RGBA", (x1 - x0 + 2 * contour + 24, y1 - y0b + 2 * contour + 24), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.text((12 + contour - x0, 12 + contour - y0b), txt, font=f, fill=tuple(col) + (255,), stroke_width=contour, stroke_fill=(10, 10, 10, 255))
        a = shadowed(im) if contour else np.dstack([np.asarray(im)[..., :3][..., ::-1], np.asarray(im)[..., 3]]).astype(np.float32) / 255
        pieces.append((a, W / 2, y + a.shape[0] / 2, t)); y += a.shape[0] + gap
    for im, cx, cy, t in pieces:
        assert XMIN - 2 <= cx - im.shape[1] / 2 and YMIN - 2 <= cy - im.shape[0] / 2 and cy + im.shape[0] / 2 <= YMAX + 2, ("hors zone", cy, im.shape)
    return pieces

# ---------------- compositing ----------------
def paste(dst, rgba, cx, cy, scale=1.0, angle=0.0):
    """Colle une image BGRA float (h,w,4) centrée en (cx,cy), échelle + rotation, dans la région utile seulement."""
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
        _tex[col] = np.clip(hexc(col)[None, None, :] * (1 + 0.03 * n[..., None] + 0.035 * n2[..., None]), 0, 1).astype(np.float32)
        if col in (RED, BLACK):                                             # pli de papier : un filet clair en diagonale
            m = np.zeros((H, W), np.float32); cv2.line(m, (0, int(H * 0.62)), (W, int(H * 0.48)), 1.0, 2, cv2.LINE_AA)
            m = cv2.GaussianBlur(m, (0, 0), 1.5) * 0.10; _tex[col] = np.clip(_tex[col] + m[..., None], 0, 1)
    return _tex[col].copy()
def background(bg, key):
    return news_texture(W, H, 100 + key) if bg == "NEWS" else paper(bg)
VIG = None
def finish(img, f):
    global VIG
    if VIG is None:
        y, x = np.mgrid[0:H, 0:W].astype(np.float32)
        r = np.sqrt(((x - W / 2) / (W / 2)) ** 2 + ((y - H / 2) / (H / 2)) ** 2) / np.sqrt(2)
        VIG = (1 - 0.26 * np.clip(r, 0, 1) ** 2.4)[..., None].astype(np.float32)
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
        m = cv2.morphologyEx(m, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))   # micros (tiges fines) retirés
        m = np.clip((cv2.GaussianBlur(m, (0, 0), 1.2) - 0.5) * 2.2 + 0.5, 0, 1)
        out.append(m)
    return out
LW = np.array([0.0722, 0.7152, 0.2126], np.float32)
def bw(x, gain=1.2):
    L = x @ LW
    L = L / max(float(np.percentile(L, 99)), 0.2); L = np.clip(L, 0, 1) ** 0.8
    L = np.clip((L - 0.5) * gain + 0.5 + 0.02, 0, 1); L = 0.75 * L + 0.25 * (L * L * (3 - 2 * L))
    return np.repeat(L[..., None], 3, axis=2) * np.array([0.97, 0.99, 1.0], np.float32)       # N&B légèrement chaud (papier)
def red_keep(x):
    """N&B contrasté, seul le rouge (cravate, drapeaux) garde sa couleur, poussé vers le rouge de la palette."""
    hsv = cv2.cvtColor((np.clip(x, 0, 1) * 255).astype(np.uint8), cv2.COLOR_BGR2HSV).astype(np.float32)
    hh, ss, vv = hsv[..., 0], hsv[..., 1] / 255, hsv[..., 2] / 255
    m = (((hh < 8) | (hh > 170)) & (ss > 0.62) & (vv < 0.74) & (vv > 0.15)).astype(np.float32)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    m = cv2.GaussianBlur(m, (0, 0), 1.5)[..., None]
    g = bw(x, 1.25); L = (x @ LW)[..., None]
    rr = np.clip(hexc(RED)[None, None, :] * (0.55 + 0.9 * L), 0, 1)
    return g * (1 - m) + rr * m
def duo(x):
    """Bichromie noir -> rouge -> papier (plein cadre)."""
    L = x @ LW; L = L / max(float(np.percentile(L, 99.5)), 0.2); L = np.clip(L, 0, 1) ** 0.85
    k = np.array([0.0, 0.5, 1.0], np.float32); cols = np.stack([hexc(BLACK), hexc(RED), hexc(NEWS)])
    out = np.stack([np.interp(L, k, cols[:, c]) for c in range(3)], -1)
    return out.astype(np.float32)

# ---------------- collage poussé : déchirures, scotch, bandes de papier, couches qui sautent sur les frappes ----------------
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
    """Morceau de scotch beige translucide, bouts dentelés."""
    m = np.ones((h, w), np.float32)
    for y in range(h):
        a = int(rng.integers(0, 7)); b = int(rng.integers(0, 7)); m[y, :a] = 0; m[y, w - b:] = 0
    col = np.array([0.72, 0.84, 0.90], np.float32)[None, None, :] * (1 + 0.04 * rng.standard_normal((h, w, 1)).astype(np.float32))
    return np.dstack([col, m * 0.75]).astype(np.float32)
def halftone(h, w, col, dot=(0.08, 0.08, 0.08), step=14, r=4):
    img = np.ones((h, w, 3), np.float32) * col[None, None, :]
    for y in range(0, h, step):
        for x in range((y // step % 2) * step // 2, w, step): cv2.circle(img, (x, y), r, tuple(float(v) for v in dot), -1, cv2.LINE_AA)
    return img
STRIP_KINDS = [(RED, "plain"), ("NEWS", "tex"), (BLACK, "plain"), (RED, "ht"), (NEWSD, "plain"), ("NEWS", "tex"), (WHITE, "plain"), (BLACK, "htred")]
def strip_rgba(w, h, rng, colhex, kind):
    """Bande de papier déchiré : couleur pleine, trame d'imprimerie ou papier journal ; ombre portée."""
    if kind == "tex": body = news_texture(w, h, int(rng.integers(1000)))
    elif kind == "ht": body = halftone(h, w, hexc(RED), dot=tuple(hexc(BLACK)))
    elif kind == "htred": body = halftone(h, w, hexc(BLACK), dot=tuple(hexc(RED)), step=16, r=5)
    else: body = np.ones((h, w, 3), np.float32) * hexc(colhex)[None, None, :]
    body = np.clip(body * (1 + 0.035 * cv2.GaussianBlur(rng.standard_normal((h, w)).astype(np.float32), (0, 0), 1.5))[..., None], 0, 1)
    m = torn_mask(h, w, rng, rough=10, step=12)
    out = np.zeros((h + 16, w + 16, 4), np.float32)
    out[10:10 + h, 8:8 + w, 3] = cv2.GaussianBlur(m, (0, 0), 3) * 0.45
    a = m[..., None]; out[:h, :w, :3] = body * a; out[:h, :w, 3] = np.maximum(m, out[:h, :w, 3])
    return out
def make_strips(sh):
    """Bandes de papier qui s'empilent une par frappe derrière la figure (stop-motion)."""
    n = sh.get("strips", 0); rng = np.random.default_rng(skey(sh["id"]) + 5); out = []
    zones = [(150, 470), (930, 560), (540, 300), (120, 1250), (960, 1320), (230, 900), (880, 1050), (800, 220), (300, 1600), (540, 1720)]
    for k in range(n):
        w, h = int(rng.uniform(380, 680)), int(rng.uniform(90, 180))
        colhex, kind = STRIP_KINDS[(k + skey(sh["id"])) % len(STRIP_KINDS)]
        if colhex == sh.get("bg"): colhex, kind = STRIP_KINDS[(k + 3 + skey(sh["id"])) % len(STRIP_KINDS)]
        if colhex == sh.get("bg"): colhex, kind = NEWSD, "plain"
        cx, cy = zones[(k + skey(sh["id"])) % 3] if k < 3 else zones[(k * 3 + skey(sh["id"])) % len(zones)]   # les 3 premières en haut (visibles)
        out.append(dict(img=strip_rgba(w, h, rng, colhex, kind), cx=cx + rng.uniform(-60, 60), cy=cy + rng.uniform(-60, 60),
                        ang=rng.uniform(-28, 28), k=k))
    return out
class Photo:
    """Photo N&B (vidéo vivante) : bord papier déchiré, scotch aux coins, ombre ; elle saute un peu sur chaque frappe."""
    def __init__(self, frames, box, width, center, angle, f0, key, border=16):
        self.frames, self.box, self.width, self.center, self.angle, self.f0, self.key = frames, box, width, center, angle, f0, key
        x0, y0, x1, y1 = box; self.h = int(round(width * (y1 - y0) / (x1 - x0))); self.b = border
        rng = np.random.default_rng(skey(key)); M = 40
        self.M = M; hh, ww = self.h + 2 * border, width + 2 * border
        self.mask = torn_mask(hh, ww, rng, rough=6, step=11, inset=3)
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
        c = cv2.resize(bw(self.frames[i][y0:y1, x0:x1]), (self.width, self.h), interpolation=cv2.INTER_AREA)
        hh, ww = self.h + 2 * b, self.width + 2 * b
        out = np.zeros((hh + 2 * M, ww + 2 * M, 4), np.float32); out[..., 3] = self.shadow
        body = np.ones((hh, ww, 3), np.float32) * hexc(NEWS); body[b:b + self.h, b:b + self.width] = c
        a = self.mask[..., None]; reg = out[M:M + hh, M:M + ww]
        reg[..., :3] = body * a; reg[..., 3] = np.maximum(self.mask, reg[..., 3])
        for t, (tx, ty) in self.tape_imgs:
            th, tw = t.shape[:2]; ty2, tx2 = max(0, ty), max(0, tx)
            sub = out[ty2:ty2 + th, tx2:tx2 + tw]; tt = t[:sub.shape[0], :sub.shape[1]]
            ta = tt[..., 3:4]; sub[..., :3] = sub[..., :3] * (1 - ta) + tt[..., :3] * ta; sub[..., 3] = np.maximum(sub[..., 3], tt[..., 3])
        return out
def jit(key, k, amp=8.0, ang=1.5):
    r = np.random.default_rng(skey(key) * 1000 + k); return r.uniform(-amp, amp), r.uniform(-amp, amp), r.uniform(-ang, ang)
def sticker(m, r=7):
    return cv2.dilate(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1)))
TORN_EDGES = None
def torn_edges():
    """Bords de papier journal déchiré en haut et en bas (plan plein cadre collé comme une coupure)."""
    global TORN_EDGES
    if TORN_EDGES is None:
        rng = np.random.default_rng(11); out = np.zeros((H, W, 4), np.float32); tex = paper(NEWSD)   # papier uni (pas de faux texte : l'OCR TikTok y lisait « WEE »)
        for y0, y1 in ((0, 150), (H - 170, H)):
            pts = [(0, y0)] if y0 == 0 else [(0, y1)]
            ys = (lambda: rng.uniform(95, 150)) if y0 == 0 else (lambda: H - rng.uniform(110, 170))
            pts += [(x, ys()) for x in range(0, W + 12, 12)]; pts += [(W, y0)] if y0 == 0 else [(W, y1)]
            m = np.zeros((H, W), np.float32); cv2.fillPoly(m, [np.array(pts, np.int32)], 1.0, lineType=cv2.LINE_AA)
            sh_ = cv2.GaussianBlur(np.roll(m, 8 if y0 == 0 else -8, axis=0), (0, 0), 5) * 0.5
            out[..., 3] = np.maximum(out[..., 3], np.maximum(m, sh_)); out[..., :3] += m[..., None] * tex
        TORN_EDGES = out
    return TORN_EDGES

# ---------------- plans ----------------
KEY = ("1 200", "MILLIARDS", "LEÇONS", "DETTES")
PUP = (200, 20, 1580, 812)            # CL au pupitre : coupé au bord du pupitre (affiche « meeting Clermont-Ferrand » et filigrane hors découpe)
CROWD = (0, 190, 1560, 1080)          # foule / salle : sous le filigrane MELENCHON2027.fr (haut droite)
HALL = (0, 200, 1560, 1080)
STAGE = (300, 20, 1560, 900)
A1_TXT = [[("ILS", wt(0))], [("EN", wt(1)), ("ONT", wt(2)), ("FAIT", wt(3))]]
A2_TXT = [[("1 200", wt(4))], [("MILLIARDS", wt(5))]]
A3_TXT = [[("DE", 0.0), ("DETTES", 0.0)]]
B1_TXT = [[("ALORS", 0.0)], [("ILS", wt(9)), ("SONT", wt(10))], [("LES", wt(11)), ("DERNIERS", wt(12))], [("À", wt(13)), ("POUVOIR", wt(14))]]
# après le drop (règle Luca 27/10) : un carton complet par plan, dans l'ordre de la phrase, jamais répété :
# « 1 200 MILLIARDS DE DETTES » (C1 + C2, même carton qui reste) / « ILS SONT LES DERNIERS » (C3) / « À NOUS DONNER DES LEÇONS » (C4)
DROP_TXT = [[("1 200", 0.0)], [("MILLIARDS", 0.0)], [("DE", 0.0), ("DETTES", 0.0)]]
B2_TXT = [[("VENIR", wt(15))], [("NOUS", wt(16)), ("DONNER", wt(17))], [("DES", wt(18)), ("LEÇONS", wt(19))]]
SHOTS = [
    dict(id="A1", kind="cut", src="CL", t=None, bg=RED, box=PUP, scale=(1.56, 1.59), cx=990, txt=A1_TXT, txt_y=260, txt_h=175, sync=True,
         strips=6, why="2026 — meeting de Clermont-Ferrand, au pupitre : « Ils en ont fait… » en son direct, Mélenchon détouré N&B (rouge gardé), écho noir décalé, fond rouge"),
    dict(id="A2", kind="cut", src="CL", t=None, bg="NEWS", box=PUP, scale=(1.59, 1.66), cx=1000, txt=A2_TXT, txt_y=255, txt_h=165, sync=True,
         strips=7, why="même plan synchro : « …1200 milliards… », fond papier journal, chiffres en lettres découpées une par une"),
    dict(id="A3", kind="cut", src="CL", t=None, bg=BLACK, box=PUP, scale=(1.66, 1.70), cx=1000, txt=A3_TXT, txt_y=270, txt_h=185, sync=True,
         strips=4, why="même plan synchro : « …de dettes. », fond noir, écho rouge décalé"),
    dict(id="B1", kind="collage", bg="NEWS", sync=True,
         photos=[("CL", None, HALL, 900, (540, 1150), -3, 0.0, True), ("CL", 7.2, CROWD, 520, (330, 1490), 6, 2 * T, False)],
         txt=B1_TXT, txt_y=255, txt_h=140, strips=6,
         why="même moment, la caméra passe sur la salle : photo N&B vivante du plan large (synchro), « Alors ils sont les derniers à pouvoir… »"),
    dict(id="B2", kind="collage", bg=RED, sync=True,
         photos=[("CL", 6.6, CROWD, 640, (360, 1060), -5, 0.0, False), ("CL", 8.0, (700, 190, 1560, 1080), 520, (760, 1260), 6, 2 * T, False),
                 ("CL", 12.4, STAGE, 620, (520, 1530), -3, 4 * T, False)],
         txt=B2_TXT, txt_y=255, txt_h=140, strips=6,
         why="la foule qui écoute (elle ne parle pas) + scène tricolore, collées sur fond rouge pendant le break : « …venir nous donner des leçons »"),
    dict(id="C1", kind="cut", src="CL", t=50.05, bg=RED, box=PUP, scale=(1.50, 1.52), cx=1075, white3=True, flash=True,
         txt=DROP_TXT, txt_y=255, txt_h=150, txt_seed=4242, txt_bg="RN", strips=3,
         why="DROP (retour du beat avant « They not like us ») : flash 3 images, silhouette blanche puis Mélenchon index levé, fond rouge"),
    dict(id="C2", kind="collage", bg="NEWS",
         photos=[("CL", 7.6, CROWD, 660, (380, 760), -4, 0.0, False), ("CL", 44.2, HALL, 620, (720, 1170), 5, T / 2, False),
                 ("CL", 14.0, STAGE, 560, (400, 1560), -6, T, False)],
         txt=[[(w, -1.0) for w, _ in l] for l in DROP_TXT], txt_y=255, txt_h=150, txt_seed=4242, txt_bg="RN", strips=3,
         why="collage papier journal : foule de Clermont, salle pleine, scène tricolore, une photo par demi-temps"),
    dict(id="C3", kind="full", src="CL", t=12.6, crop=(960, 540, 1080), push=(1.0, 1.05), focus=(960, 470), flash=True,
         big=[("ILS SONT", 0.0, (247, 245, 239)), ("LES DERNIERS", 0.0, (247, 245, 239))], big_y=980, big_sizes=[150, 150],
         why="plein cadre en bichromie noir-rouge-papier : la scène tricolore et la salle, bords de journal déchirés, gros texte avec contour"),
    dict(id="C4", kind="cut", src="CL", t=53.25, bg=BLACK, box=PUP, scale=(1.52, 1.56), cx=1080,
         txt=[[("À", 0.0), ("NOUS", 0.0), ("DONNER", 0.0)], [("DES", 0.0), ("LEÇONS", 0.0)]], txt_y=260, txt_h=160, strips=4,
         why="Mélenchon bras tendu vers la salle (musique seule), N&B rouge gardé, écho rouge, fond noir"),
    dict(id="C5", kind="collage", bg=RED,
         photos=[("FIN", 25.0, CROWD, 720, (520, 640), -4, 0.0, False), ("CL", 9.9, CROWD, 580, (340, 1120), 5, T / 2, False),
                 ("CL", 42.8, HALL, 620, (720, 1520), -5, T, False)],
         strips=3, why="collage sans texte : l'équipe de dos face à la salle (fin du meeting), la foule, la salle pleine"),
    dict(id="C6", kind="cut", src="CL", t=1.0, bg="NEWS", box=(60, 20, 1560, 812), scale=(1.24, 1.28), cx=810, white3=True,
         photos=[("CL", 8.6, CROWD, 700, (540, 560), 3, 0.0, False)], strips=4,
         why="Mélenchon bras grands ouverts au pupitre (musique seule) : silhouette blanche 3 images puis découpe, photo de la foule au-dessus"),
    dict(id="FIN", kind="card", bg="NEWS", push=(1.0, 1.035),
         big=[("JEAN-LUC", 0.0, rgb(BLACK)), ("MÉLENCHON", T, rgb(RED)), ("2027", 2 * T, rgb(BLACK))],
         big_y=650, big_sizes=[220, 220, 220],
         why="carton final propre (papier journal, noir + rouge) : son nom + 2027 (règle Luca pour toutes les vidéos de Mélenchon), même style que le nom, pas de CTA"),
]
BOUNDS_T = [0] + CUTF + [fr(END)]
assert len(BOUNDS_T) == len(SHOTS) + 1, (len(BOUNDS_T), len(SHOTS))
for i, sh in enumerate(SHOTS):
    sh["a"], sh["bb"] = BOUNDS_T[i], BOUNDS_T[i + 1]; sh["n"] = sh["bb"] - sh["a"]; sh["clip"] = "R2_%s.mov" % sh["id"]
    if sh.get("src") == "CL" and sh["t"] is None: sh["t"] = V_SRC0 + sh["a"] / FPS          # plans synchro avec la voix
assert min(sh["n"] for sh in SHOTS) >= 17, [(s["id"], s["n"]) for s in SHOTS]
for sh in SHOTS[:3]: assert sh["t"] + (sh["n"] - 1) / FPS < CAM_CUT, ("plan synchro après la coupe caméra", sh["id"])

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
        dx, dy, da = jit((boil, j), k, amp=4, ang=1.0) if boil else (0, 0, 0)       # les découpes « bougent » sur chaque frappe
        paste(img, im, cx + dx, cy + dy, s, da)
CARD_TAPES = [tape_rgba(170, 46, np.random.default_rng(40 + j)) for j in range(4)]
CARD = None
def card_panel():
    """Feuille de papier propre déchirée, collée sur la page de journal (carton final)."""
    global CARD
    if CARD is None:
        rng = np.random.default_rng(5); w, h = 900, 1180
        m = torn_mask(h, w, rng, rough=9, step=12, inset=6)
        out = np.zeros((h + 20, w + 20, 4), np.float32); out[12:12 + h, 10:10 + w, 3] = cv2.GaussianBlur(m, (0, 0), 5) * 0.5
        body = paper(WHITE)[:h, :w]; out[:h, :w, :3] = body * m[..., None]; out[:h, :w, 3] = np.maximum(m, out[:h, :w, 3])
        CARD = out
    return CARD
def render(sh):
    n = sh["n"]; a = sh["a"]; frames = []
    rel = lambda t: sh["a"] / FPS + t
    def abs_pieces(p, timeline_abs):
        return [(im, cx, cy, (max(t, a / FPS) if timeline_abs else rel(t))) for im, cx, cy, t in p]
    sync = sh.get("sync", False)
    txt = abs_pieces(board(sh["txt"], sh["txt_y"], seed=sh.get("txt_seed", skey(sh["id"]) * 7), letters=KEY, h=sh.get("txt_h", 118), bg=sh.get("txt_bg", sh.get("bg"))), sync) if sh.get("txt") else []
    big = []
    if sh.get("big"):
        big = abs_pieces(big_text([(s, t, c) for s, t, c in sh["big"]], sh["big_y"], sizes=sh["big_sizes"],
                                  spec=(FIMP if sh["kind"] == "card" else FCOND),
                                  maxw=(XMAX - XMIN) * (0.92 if sh["kind"] == "card" else 1.0),
                                  contour=10 if sh["kind"] == "full" else 0, gap=(-6 if sh["kind"] == "card" else -18)), False)
    # photos : (src, t (None = synchro), box, largeur, (cx, cy), angle, apparition en s dans le plan, synchro)
    photos = []
    for j, (ps, pt, pbox, pw, pc, pa, pt0, psync) in enumerate(sh.get("photos", [])):
        tt = V_SRC0 + a / FPS if psync else pt
        if psync: assert tt >= CAM_CUT, ("photo synchro avant la coupe caméra", tt)
        photos.append(Photo(read_frames(ps, tt, n), pbox, pw, pc, pa, fr(rel(pt0)), (sh["id"], j)))
        sh.setdefault("_photo_t", []).append(round(tt, 3))
    strips = make_strips(sh)
    k0 = nbeat(a)
    if sh["kind"] in ("cut", "full"):
        raw = read_frames(sh["src"], sh["t"], n)
    if sh["kind"] == "cut":
        ms = masks("%s_%s_%.3f_%d" % (sh["id"], sh["src"], sh["t"], n), raw, sh["box"], k=13)
    for i in range(n):
        f = a + i; u = i / max(n - 1, 1); kb = nbeat(f) - k0
        if sh["kind"] == "full":
            cx, cy, vh = sh["crop"]; z = sh["push"][0] + (sh["push"][1] - sh["push"][0]) * u
            s = H / vh * z; fx_, fy_ = sh["focus"]
            ccx = cx + (fx_ - cx) * (1 - 1 / z); ccy = cy + (fy_ - cy) * (1 - 1 / z)
            M = np.float32([[s, 0, W / 2 - ccx * s], [0, s, H / 2 - ccy * s]])
            img = duo(cv2.warpAffine(raw[i], M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE))
        else:
            img = background(sh["bg"], skey(sh["id"]) % 50)
        for st in strips:                                                   # une bande de plus à chaque frappe
            if st["k"] <= kb + 2:                                          # 3 bandes dès le début du plan, puis une par frappe
                dx, dy, da = jit((sh["id"], "s", st["k"]), nbeat(f), amp=6, ang=1.2)
                kk = k0 + st["k"] - 3
                s_ = pop(f, BEATF[kk] if st["k"] > 2 and kk < len(BEATF) else a, n=4, amp=0.08) or 1.0
                paste(img, st["img"], st["cx"] + dx, st["cy"] + dy, s_, st["ang"] + da)
        for ph in photos:
            s_ = pop(f, ph.f0, n=5, amp=0.10)
            if s_ is not None:
                dx, dy, da = jit(ph.key, nbeat(f), amp=9, ang=1.8)
                paste(img, ph.rgba(i), ph.center[0] + dx, ph.center[1] + dy, s_, ph.angle + da)
        if sh["kind"] == "cut":
            x0, y0, x1, y1 = sh["box"]; sc = sh["scale"][0] + (sh["scale"][1] - sh["scale"][0]) * u
            m = ms[i]; hh = (y1 - y0) * sc
            fcx = (sh["cx"] - x0) * sc; ccx = W / 2 + ((x1 - x0) / 2 * sc - fcx); ccy = H - hh / 2
            body = red_keep(raw[i][y0:y1, x0:x1])
            white = np.ones_like(body) * np.array([0.96, 0.96, 0.95], np.float32)
            st_ = np.dstack([white, sticker(m, 8)])
            sd = st_.copy(); sd[..., :3] = 0; sd[..., 3] = cv2.GaussianBlur(st_[..., 3], (0, 0), 6) * 0.5
            ecol = hexc(BLACK) if sh["bg"] == RED else hexc(RED)
            echo = np.dstack([np.ones_like(body) * ecol, sticker(m, 4) * 0.96])
            ex, ey, _ = jit((sh["id"], "echo"), nbeat(f), amp=10, ang=0)    # écho décalé qui saute sur les frappes (mauvais repérage)
            paste(img, sd, ccx + 14, ccy + 10, sc)
            paste(img, echo, ccx - 34 + ex, ccy - 18 + ey, sc * 1.015)
            if sh.get("white3") and i < 3: paste(img, np.dstack([white, m]), ccx, ccy, sc)    # silhouette blanche : 3 images
            else: paste(img, st_, ccx, ccy, sc); paste(img, np.dstack([body, m]), ccx, ccy, sc)
        if sh["kind"] == "full":
            te = torn_edges(); img = img * (1 - te[..., 3:4]) + te[..., :3]
        if sh["kind"] == "card":
            z = sh["push"][0] + (sh["push"][1] - sh["push"][0]) * u
            paste(img, card_panel(), W / 2, H / 2 - 40, z, -1.5)
            for j, (tx, ty, ta) in enumerate(((190, 420, -32), (890, 420, 30), (190, 1450, 28), (890, 1450, -30))):
                paste(img, CARD_TAPES[j], W / 2 + (tx - W / 2) * z, H / 2 + (ty - H / 2) * z, 1.0, ta)
            for im, cx, cy, t in big:
                s_ = pop(f, fr(t))
                if s_ is not None: paste(img, im, W / 2 + (cx - W / 2) * z, H / 2 + (cy - H / 2) * z, s_ * z)
        else:
            draw_pieces(img, txt, f, boil=sh["id"])
            if big: draw_pieces(img, big, f)
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
    v = grab(HG + "/" + SRC["CL"][0], V_IN, V_OUT - V_IN); env = np.ones(len(v), np.float32)
    k = int(0.03 * sr); env[:k] = np.linspace(0, 1, k); k = int(0.05 * sr); env[-k:] = np.linspace(1, 0, k)
    i0 = int(round(t_of_src(V_IN) * sr)); voix[i0:i0 + len(v)] = v * env[:, None] * 10 ** (3 / 20)
    m = music_raw(MUSIC_IN, END + 0.1)[:N]
    t = np.arange(len(m)) / sr; brk = 68.05 - MUSIC_IN; vend = t_of_src(V_OUT); dr = DROP
    # sous la phrase : -18 dB (fin du couplet), montée dans le break « A minor » (-18 -> -7 dB), plein sur le retour du beat
    gdb = np.interp(t, [0, 0.25, brk, vend, dr - 0.03, dr, END], [-26, -18, -18, -7, -5, 0, 0])
    k = int(0.30 * sr); fo = np.ones(len(m), np.float32); fo[-k:] = np.linspace(1, 0, k)
    mus[:len(m)] = m * (10 ** (gdb / 20) * fo)[:, None]
    sf.write(OUT + "R2-voix.wav", voix, sr, subtype="PCM_24"); sf.write(OUT + "R2-musique.wav", mus, sr, subtype="PCM_24")
    sf.write(D + "tmp_mix.wav", voix + mus, sr, subtype="FLOAT")
    r = subprocess.run([FF, "-hide_banner", "-i", D + "tmp_mix.wav", "-af", "loudnorm=I=-14:TP=-2.5:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    js = json.loads(r[r.rindex("{"):r.rindex("}") + 1])
    af = ("loudnorm=I=-14:TP=-2.5:LRA=11:measured_I=%s:measured_TP=%s:measured_LRA=%s:measured_thresh=%s:offset=%s:linear=true,"
          "aresample=48000" % (js["input_i"], js["input_tp"], js["input_lra"], js["input_thresh"], js["target_offset"]))
    subprocess.run([FF, "-v", "error", "-y", "-i", D + "tmp_mix.wav", "-af", af, "-c:a", "pcm_s24le", OUT + "R2-mix.wav"], check=True)
    os.remove(D + "tmp_mix.wav"); print("audio : mix avant normalisation", js["input_i"], "LUFS")

# ---------------- plan ----------------
PHRASE = "Ils en ont fait 1200 milliards de dettes. Alors ils sont les derniers à pouvoir venir nous donner des leçons"
def build_plan():
    video = []
    for sh in SHOTS:
        v = {"id": sh["id"], "clip": sh["clip"], "folder": "genR2", "path": OUT + sh["clip"], "s": 0, "e": sh["n"], "rec": sh["a"], "dur": sh["n"],
             "clip_fps": FPS, "speed_pct": 100, "track": 1, "note": sh["why"], "kind": sh["kind"], "temps": round(sh["n"] / FPS / T, 2)}
        if sh.get("src"):
            path, sfps, url, off, ctx = SRC[sh["src"]]
            v["source"] = {"fichier": path, "in_s": round(sh["t"], 3), "out_s": round(sh["t"] + sh["n"] / FPS, 3), "fps": sfps,
                           "url": url, "t_youtube_s": round(off + sh["t"], 2), "contexte": ctx}
        if sh.get("photos"):
            v["photos_nb"] = []
            for p in sh["photos"]:
                tt = V_SRC0 + sh["a"] / FPS if p[7] else p[1]
                v["photos_nb"].append({"fichier": SRC[p[0]][0], "in_s": round(tt, 3), "out_s": round(tt + sh["n"] / FPS, 3), "cadre_source": p[2],
                                       "url": SRC[p[0]][2], "t_youtube_s": round(SRC[p[0]][3] + tt, 2), "synchro": p[7]})
        video.append(v)
    texts = []
    for sh in SHOTS:
        for line in sh.get("txt", []): texts.append({"plan": sh["id"], "texte": " ".join(w for w, _ in line)})
        for s_, t_, c_ in sh.get("big", []): texts.append({"plan": sh["id"], "texte": s_})
    plan = {"name": "R2 - Collage ransom-note - Jean-Luc Mélenchon (Kendrick Lamar - Not Like Us)", "fps": FPS, "w": W, "h": H, "duree_s": round(fr(END) / FPS, 3),
            "note": "Plans ProRes 9:16 composés en Python (lot6/_claude/gen/R2/out) : fonds rouge / noir / papier journal (colonnes de faux texte), "
                    "Mélenchon détouré (segment/Vision) en N&B à rouge gardé + écho décalé, photos N&B vivantes collées (scotch, bords déchirés), "
                    "plein cadre en bichromie, textes ransom-note cuits. s/e en images du clip (30 i/s), rec en images timeline. "
                    "Coupes sur les claps et notes réelles de Not Like Us (son.json). Aucun ralenti. Générateur : lot6/_claude/gen/R2/genR2.py",
            "phrase": {"texte": PHRASE, "url": SRC["CL"][2], "source": SRC["CL"][0], "in_s": 35.04, "out_s": 44.45,
                       "t_youtube_s": [2635.04, 2644.45], "timeline_s": [round(t_of_src(35.04), 2), round(t_of_src(44.45), 2)],
                       "avant": "« … la dernière fois, ils nous reprochaient la création possible et effrayante de 100 milliards de dettes. »",
                       "voix": "son direct synchro (A1-A3 au pupitre, B1 plan large de la salle au même moment), B2 sur la foule qui écoute ; "
                               "la phrase continue (« surtout que ces 1200 milliards… ») : coupure après « leçons », sens intact"},
            "musique": {"fichier": "lot6/sons/R2-kendrick-not-like-us_complet.wav", "titre": "Kendrick Lamar - Not Like Us", "url": SON_URL,
                        "debut_complet_s": round(MUSIC_IN, 4), "fin_complet_s": round(MUSIC_IN + fr(END) / FPS, 3), "drop_timeline_s": round(DROP, 4),
                        "coupes_s": [round(c, 4) for c in CUTS], "coupes_images": CUTF},
            "textes": texts, "video": video,
            "audio": [{"id": "mix", "clip": "R2-mix.wav", "folder": "genR2", "path": OUT + "R2-mix.wav", "rec": 0, "track": 1,
                       "note": "mix -14 LUFS : voix CL %.2f-%.2f s (+3 dB) à %.2f s ; Not Like Us dès %.3f s du complet, -18 dB sous la voix, montée dans le break, plein au drop, fondu de fin 0,3 s"
                               % (V_IN, V_OUT, t_of_src(V_IN), MUSIC_IN)}],
            "stems": ["lot6/_claude/gen/R2/out/R2-voix.wav", "lot6/_claude/gen/R2/out/R2-musique.wav"],
            "logos_exclus": "filigrane MELENCHON2027.fr (haut droite) hors des cadres photo et hors des détourages ; affiche du pupitre sous la découpe ; drapeaux LFI de la salle (plans 66-79 s de l'extrait) non utilisés"}
    json.dump(plan, open(D + "plan-R2.json", "w"), indent=1, ensure_ascii=False)
    son = {"id": "R2", "titre": "Not Like Us", "artiste": "Kendrick Lamar", "url": SON_URL,
           "chaine": "Kendrick Lamar (chaîne officielle vérifiée, piste « Not Like Us » de la chaîne de l'artiste)",
           "fichier": "lot6/sons/R2-kendrick-not-like-us_complet.wav",
           "extrait_complet_s": {"debut": round(MUSIC_IN, 4), "fin": round(MUSIC_IN + fr(END) / FPS, 3)},
           "paroles_audibles": "sous la voix (-18 dB) : fin du couplet 1 jusqu'à « …probably A minor » (63,6-68,0 s), puis le break ; "
                               "au drop : « They not like us » x6 (74,5-82,9 s) ; fin avant « You think the bag… » (82,96 s)",
           "bpm": round(60 / T, 2), "temps_s": T,
           "drop": {"complet_s": MDROP, "timeline_s": round(DROP, 4), "nature": "retour du beat (kick + clap) après le break « A minor », « They not like us » 0,83 s après"},
           "frappes_timeline_s": [round(b, 4) for b in BEATS if 0 <= b <= END],
           "coupes_sur_frappes_s": [round(c, 4) for c in CUTS],
           "coupes_nature": ["clap", "clap", "note du riff (break)", "note du riff (break)", "drop kick+clap", "clap", "clap", "clap", "clap", "clap", "clap"],
           "mix": "lot6/_claude/gen/R2/out/R2-mix.wav"}
    json.dump(son, open(D + "son.json", "w"), indent=1, ensure_ascii=False)

# ---------------- aperçu 540x960 ----------------
def apercu():
    plan = json.load(open(D + "plan-R2.json")); ins = []; fl = []
    for i, v in enumerate(plan["video"]):
        ins += ["-i", OUT + v["clip"]]
        fl.append("[%d:v]trim=start_frame=%d:end_frame=%d,setpts=PTS-STARTPTS,scale=540:960,setsar=1[v%d]" % (i, v["s"], v["e"], i))
    k = len(plan["video"]); fl.append("".join("[v%d]" % i for i in range(k)) + "concat=n=%d:v=1:a=0[v]" % k)
    ins += ["-i", OUT + "R2-mix.wav"]; out = HG + "/preview/apercu-R2.mp4"
    subprocess.run([FF, "-v", "error", "-y"] + ins + ["-filter_complex", ";".join(fl), "-map", "[v]", "-map", "%d:a" % k,
                    "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "aac", "-b:a", "192k", "-shortest", out], check=True)
    print("aperçu", out)
# ---------------- mesure sur l'export : coupes vs frappes (claps / kicks / notes), LUFS / TP ----------------
def mesure():
    """Coupes détectées sur l'export (changement de plan) ; décalage audio de l'export (AAC) mesuré par corrélation avec le mix ;
    frappes réelles (claps / kicks, notes du riff dans le break) mesurées dans le stem musique tel qu'il est dans le mix."""
    import librosa, soundfile as sf
    out = HG + "/preview/apercu-R2.mp4"
    r = subprocess.run([FF, "-v", "info", "-i", out, "-vf", "scale=135:240,select='gt(scene,0.2)',showinfo", "-an", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    cuts = [float(x) for x in re.findall(r"pts_time:([0-9.]+)", r)]
    p = subprocess.run([FF, "-v", "error", "-i", out, "-vn", "-ac", "1", "-ar", "48000", "-f", "f32le", "-"], capture_output=True)
    ye = np.frombuffer(p.stdout, np.float32)
    ymx, _ = sf.read(OUT + "R2-mix.wav", dtype="float32"); ymx = ymx.mean(1)
    n = min(len(ye), len(ymx)); A = np.fft.rfft(ye[:n], 2 * n); B = np.fft.rfft(ymx[:n], 2 * n)
    xc = np.fft.irfft(A * np.conj(B)); lags = np.r_[0:2000, -2000:0]; lag = lags[np.argmax(np.r_[xc[:2000], xc[-2000:]])] / 48000
    ym, _ = sf.read(OUT + "R2-musique.wav", dtype="float32")
    h = [x[0] for x in detect_hits(music_raw(MUSIC_IN, END)) if x[2] > 0.15]   # même morceau, même calage que le stem (gain non appliqué : pics pré-drop détectables)
    mono = librosa.resample(ym.mean(1), orig_sr=48000, target_sr=22050)
    env = librosa.onset.onset_strength(y=mono, sr=22050, hop_length=64)
    print("décalage audio export / mix : %+.1f ms" % (lag * 1000))
    print("coupes image détectées (export) :", cuts)
    worst = 0
    for j, c in enumerate([fr_ / FPS for fr_ in CUTF]):
        det = min(cuts, key=lambda x: abs(x - c)) if cuts else None
        if j in (2, 3):                                                    # note du riff : pic d'onset près de la note attendue
            lo, hi = int((CUTS[j] - 0.06) * 22050 / 64), int((CUTS[j] + 0.06) * 22050 / 64)
            k = (lo + int(np.argmax(env[lo:hi]))) * 64 / 22050; kind = "note"
        else:
            k = min(h, key=lambda t: abs(t - CUTS[j])); kind = "frappe"
        k += lag; e = ((det if det is not None else c) - k) * 1000; worst = max(worst, abs(e))
        print("  coupe %.3f (détectée %s)  %s %.4f  écart %+.1f ms" % (c, "%.3f" % det if det is not None else "-", kind, k, e))
    print("écart max coupes/frappes : %.1f ms" % worst)
    r = subprocess.run([FF, "-hide_banner", "-i", out, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    print(r[r.rindex("Summary"):])
if __name__ == "__main__":
    args = set(a for a in sys.argv[1:] if not a.startswith("only=")) or {"shots", "audio", "plan", "apercu"}
    only = [x for a in sys.argv[1:] if a.startswith("only=") for x in a.split("=", 1)[1].split(",")]
    print("musique dès %.4f s ; V_SRC0 %.3f ; coupes (s) :" % (MUSIC_IN, V_SRC0), [round(c, 3) for c in CUTS], "images :", CUTF, "fin", fr(END))
    if "shots" in args or only:
        for sh in SHOTS:
            if not only or sh["id"] in only: render(sh)
    if "audio" in args: make_audio()
    if "plan" in args: build_plan()
    if "apercu" in args: apercu()
    if "mesure" in args: mesure()
