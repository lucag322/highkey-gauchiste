# R1 (lot 5) — Collage ransom-note (NOUVEAU, inspi @abdulelsayed), Manon Aubry, son Daft Punk – One More Time (clip officiel).
# Recette (fiche inspis/2026-10-26 abdulelsayed) : texte ransom-note (chaque mot dans son rectangle penché, serif/sans mélangés,
# capitales, mots-clés lettre par lettre comme les découpes de l'inspi), slogans qui s'accumulent mot après mot, photos N&B de
# meeting collées sur fond coloré uni (scrapbook), silhouette détourée en aplat blanc sur fond sombre, carton final propre
# (fond crème, bold bleu + rouge). Recadrage 9:16 obligatoire. À ne pas recopier : flashs 1-2 images (ici plans >= 2 temps,
# apparitions animées sur 4 images), gros texte sans contour (B3 : contour + ombre), CTA US (carton final = ses propres mots).
# Phrase (son direct) : « Bientôt, quand le vent aura tourné et que nous serons au pouvoir, nous assumerons de taxer les riches,
#   de bloquer les prix des produits essentiels » (plénière, état de l'Union, 16/09/2026, chaîne Manon Aubry, youtu.be/nwc4Hd8pO8o
#   71,08-78,24 s) -> autre phrase que G2 (20-28 s), M2 (87-92 s) et V1 (meeting Strasbourg).
# Son : One More Time, extrait continu ; la phrase finit dans le break filtré (59,75-63,55 s du morceau), drop = retour du kick
#   avec « One more time, we're gonna celebrate » (63,58 s), puis coupes toutes les 2 temps sur les kicks réels.
# Usage : python genR1.py [shots] [audio] [plan] [apercu] [mesure] [only=ID,ID]   (sans argument = tout sauf mesure)
import sys
sys.dont_write_bytecode = True
import os, json, subprocess, math, re
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
HG = "/Users/luca.grousset/Movies/highkey-gauchiste"
D = HG + "/lot5/_claude/gen/R1/"; OUT = D + "out/"; CACHE = D + "cache/"; os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, D)
from hits import detect_hits
FF = "/opt/homebrew/bin/ffmpeg"; SEG = HG + "/_claude/outils/segment"; FPS = 30; W, H = 1080, 1920
def fr(t): return int(round(t * FPS))
def hexc(h): h = h.lstrip("#"); return np.array([int(h[4:6], 16), int(h[2:4], 16), int(h[0:2], 16)], np.float32) / 255   # BGR
PURPLE, BLUE, NAVY, RED, CREAM, LBLUE = "#4A2070", "#1B3472", "#1B2B5C", "#CC2030", "#F2EDE0", "#C5D0E8"   # couleurs mesurées de l'inspi

# ---------------- sources (lecture seule) ----------------
SRC = {
    "SOT": ("lot2/sources/G2-aubry-sotEU-2026.mp4", 25.0, "https://www.youtube.com/watch?v=nwc4Hd8pO8o", 0.0,
            "plénière de Strasbourg, débat sur l'état de l'Union, 16/09/2026 (chaîne Manon Aubry)"),
    "MA": ("lot3/sources/V1-aubry-strasbourg-a.mp4", 25.0, "https://www.youtube.com/watch?v=c-KnJoiz928", None,
           "meeting « Justice pour la Palestine », Strasbourg, 17/06/2026 (chaîne Manon Aubry)"),
    "MB": ("lot3/sources/V1-aubry-strasbourg-b.mp4", 25.0, "https://www.youtube.com/watch?v=c-KnJoiz928", None,
           "meeting « Justice pour la Palestine », Strasbourg, 17/06/2026 (chaîne Manon Aubry)"),
    "MC": ("lot3/sources/V1-aubry-strasbourg-c.mp4", 25.0, "https://www.youtube.com/watch?v=c-KnJoiz928", None,
           "meeting « Justice pour la Palestine », Strasbourg, 17/06/2026 (chaîne Manon Aubry)"),
    "SOIR": ("lot4/sources/M2-aubry-soiree2024-c.mp4", 30.0, "https://www.youtube.com/watch?v=KnUCA72LZAY", None,
             "soirée électorale des européennes, 09/06/2024 (chaîne La France insoumise)"),
}

# ---------------- musique : Daft Punk – One More Time ----------------
SON_FILE = HG + "/lot5/sons/R1-daftpunk-one-more-time_complet.wav"; SON_URL = "https://www.youtube.com/watch?v=FGBhQbmPwH8"
MDROP = 63.58                        # retour du kick après le break filtré, « One more time » (Whisper 63,96)
DROP = 7.90; T = 60 / 123.0          # 123 BPM
MUSIC_IN0 = MDROP - DROP
END = 17.20
CUT_T = [2.05, 3.516, DROP] + [DROP + 2 * k * T for k in range(1, 8)]     # 2 coupes avant le break, drop, puis toutes les 2 temps
HITS_JSON = OUT + "R1-frappes.json"
def music_raw(mi, dur=END + 0.5, sr=48000):
    import soundfile as sf
    i0 = int(round(mi * sr)); x, r = sf.read(SON_FILE, start=i0, frames=int(dur * sr), dtype="float32"); assert r == sr; return x
def kicks_of(h): return [x[0] for x in h if x[1] == "kick" and x[3] > 0.12]
def snap_list(ks, targets):
    out = []
    for i, t in enumerate(targets):
        if i > 3: t = out[-1] + 2 * T                                      # après le drop : 2 temps après la coupe précédente réelle
        c = min(ks, key=lambda k: abs(k - t)); assert abs(c - t) < 0.04, ("pas de kick près de", t, c); out.append(c)
    return out
def frappes():
    if os.path.exists(HITS_JSON):
        js = json.load(open(HITS_JSON))
        if js["cle"] == [MUSIC_IN0, END, CUT_T]: return js["music_in"], js["frappes"]
    best, bad = None, 9
    for off in np.arange(-0.016, 0.0165, 0.001):
        h = detect_hits(music_raw(MUSIC_IN0 + off)); cuts = snap_list(kicks_of(h), CUT_T)
        e = max(abs(c - round(c * FPS) / FPS) for c in cuts)
        if e < bad: best, bad, hb = off, e, h
    mi = MUSIC_IN0 + best
    json.dump({"cle": [MUSIC_IN0, END, CUT_T], "music_in": mi, "frappes": hb}, open(HITS_JSON, "w")); return mi, hb
MUSIC_IN, HITS = frappes()
FINE = 0.004                          # recalage fin (+4 ms dans le morceau) mesuré sur l'export AAC : écart max coupes/kicks < 20 ms
MUSIC_IN += FINE; HITS = [[h[0] - FINE] + list(h[1:]) for h in HITS]
KICKS = kicks_of(HITS)
CUTS = snap_list(KICKS, CUT_T); CUTF = [fr(c) for c in CUTS]
DROPF = CUTF[2]; TB = T                                                    # temps (s)

# ---------------- voix ----------------
V_SRC0 = 70.70                        # source SOT à t = 0 (« bientôt » 71,08 -> 0,38 s)
V_IN, V_OUT = 71.00, 78.36            # « bientôt » … « essentiels » (fin 78,24) ; « de geler » (78,42) non gardé
def t_of_src(s): return s - V_SRC0
WORDS = [("BIENTÔT", 71.08), ("QUAND", 71.46), ("LE", 71.62), ("VENT", 71.78), ("AURA", 71.94), ("TOURNÉ", 72.18),
         ("ET", 72.54), ("QUE", 72.92), ("NOUS", 73.06), ("SERONS", 73.18), ("AU", 73.50), ("POUVOIR", 73.64),
         ("NOUS", 74.26), ("ASSUMERONS", 74.46), ("DE", 75.04), ("TAXER", 75.18), ("LES", 75.58), ("RICHES", 75.72),
         ("DE", 76.30), ("BLOQUER", 76.48), ("LES", 76.80), ("PRIX", 76.94), ("DES", 77.14), ("PRODUITS", 77.28), ("ESSENTIELS", 77.58)]
def wt(i): return t_of_src(WORDS[i][1])
BOARD_B_T = wt(18)                    # « de bloquer » : le 2e tableau remplace le 1er dans le dernier plan (pas de coupe : break sans kick)

# ---------------- polices ransom-note (accents vérifiés : cache/test/fonts.png) ----------------
S = "/System/Library/Fonts/Supplemental/"
FONTS = [(S + "Arial Black.ttf", 0), (S + "Georgia Bold.ttf", 0), (S + "Times New Roman Bold.ttf", 0), (S + "Impact.ttf", 0),
         (S + "Courier New Bold.ttf", 0), (S + "Rockwell.ttc", 2), (S + "AmericanTypewriter.ttc", 2), (S + "Didot.ttc", 2),
         (S + "Bodoni 72.ttc", 2), (S + "Futura.ttc", 2)]
FCOND = (S + "Futura.ttc", 4)         # Futura Condensed ExtraBold (carton final, gros texte B3)
STYLES = [((236, 233, 224), (20, 20, 20)), ((18, 18, 18), (245, 245, 240)), ((204, 32, 48), (250, 248, 240)),
          ((27, 52, 114), (250, 248, 240)), ((242, 237, 224), (27, 52, 114)), ((200, 198, 190), (15, 15, 15)), ((250, 250, 250), (204, 32, 48))]
_fc = {}
def font(spec, size):
    k = (spec, size)
    if k not in _fc: _fc[k] = ImageFont.truetype(spec[0], size, index=spec[1])
    return _fc[k]
def chip(txt, h, rng, fspec=None, style=None, rot=None):
    """Un morceau découpé : rectangle irrégulier + texte, RGBA PIL, légèrement penché."""
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
    a = rot if rot is not None else rng.uniform(-4, 4)
    return im.rotate(a, resample=Image.BICUBIC, expand=True)
def word_img(word, h, rng, letters=False):
    if not letters: return chip(word, h, rng)
    parts = [chip(c, h * rng.uniform(0.92, 1.06), rng, rot=rng.uniform(-6, 6)) for c in word]
    wsum = sum(p.width for p in parts) - 12 * (len(parts) - 1); hh = max(p.height for p in parts) + 10
    im = Image.new("RGBA", (wsum, hh), (0, 0, 0, 0)); x = 0
    for p in parts:
        im.alpha_composite(p, (x, (hh - p.height) // 2 + int(rng.integers(-4, 5)))); x += p.width - 12
    return im
def shadowed(im):
    """Ombre portée (papier collé)."""
    a = np.asarray(im)[..., 3].astype(np.float32) / 255
    sh = cv2.GaussianBlur(a, (0, 0), 3) * 0.55
    out = np.zeros((im.height + 12, im.width + 12, 4), np.float32)
    out[9:9 + im.height, 7:7 + im.width, 3] = sh
    rgb = np.asarray(im)[..., :3][..., ::-1].astype(np.float32) / 255
    out[:im.height, :im.width, :3] = out[:im.height, :im.width, :3] * (1 - a[..., None]) + rgb * a[..., None]
    out[:im.height, :im.width, 3] = a + out[:im.height, :im.width, 3] * (1 - a)
    return out                                                              # BGR + alpha, float
XMIN, XMAX, YMIN, YMAX = 0.19 * W, 0.81 * W, 0.13 * H, 0.74 * H          # zone sûre TikTok (0,17-0,83 / 0,12-0,75) + marge
def board(lines, y0, seed, h=112, letters=(), maxw=XMAX - XMIN - 30):
    """lines = [[(mot, t_apparition), …], …] -> liste de pièces placées (img, cx, cy, t)."""
    rng = np.random.default_rng(seed); pieces = []; y = y0
    for line in lines:
        imgs = [shadowed(word_img(w, h * (1.12 if w in letters else 1.0), rng, w in letters)) for w, _ in line]
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
def big_text(lines, y0, color, spec=FCOND, maxw=XMAX - XMIN, sizes=None, contour=0):
    """Texte propre (carton final / gros mot B3) : lignes centrées, largeur max, retour [(img, cx, cy, t)]."""
    pieces = []; y = y0
    for k, (txt, t, col) in enumerate(lines):
        size = (sizes or [300] * len(lines))[k]; f = font(spec, size)
        while f.getlength(txt) > maxw - 2 * contour - 44: size -= 4; f = font(spec, size)
        x0, y0b, x1, y1 = f.getbbox(txt)
        im = Image.new("RGBA", (x1 - x0 + 2 * contour + 24, y1 - y0b + 2 * contour + 24), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.text((12 + contour - x0, 12 + contour - y0b), txt, font=f, fill=tuple(col) + (255,), stroke_width=contour, stroke_fill=(10, 10, 20, 255))
        a = shadowed(im) if contour else np.dstack([np.asarray(im)[..., :3][..., ::-1], np.asarray(im)[..., 3]]).astype(np.float32) / 255
        pieces.append((a, W / 2, y + a.shape[0] / 2, t)); y += a.shape[0] - 18
    for im, cx, cy, t in pieces:
        assert XMIN - 2 <= cx - im.shape[1] / 2 and YMIN - 2 <= cy - im.shape[0] / 2 and cy + im.shape[0] / 2 <= YMAX + 2, ("hors zone", cy)
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
        _tex[col] = np.clip(hexc(col)[None, None, :] * (1 + 0.025 * n[..., None] + 0.03 * n2[..., None]), 0, 1).astype(np.float32)
    return _tex[col].copy()
VIG = None
def finish(img, f):
    global VIG
    if VIG is None:
        y, x = np.mgrid[0:H, 0:W].astype(np.float32)
        r = np.sqrt(((x - W / 2) / (W / 2)) ** 2 + ((y - H / 2) / (H / 2)) ** 2) / np.sqrt(2)
        VIG = (1 - 0.28 * np.clip(r, 0, 1) ** 2.4)[..., None].astype(np.float32)
    g = np.random.default_rng(1000 + f).standard_normal((H // 2, W // 2)).astype(np.float32)
    g = cv2.resize(g, (W, H), interpolation=cv2.INTER_LINEAR)[..., None] * 0.022
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
def grade(x, sat=1.08):
    x = 0.82 * x + 0.18 * (x * x * (3 - 2 * x))
    L = x @ np.array([0.0722, 0.7152, 0.2126], np.float32)
    return np.clip(L[..., None] + (x - L[..., None]) * sat, 0, 1)
def bw(x, gain=1.15):
    L = x @ np.array([0.0722, 0.7152, 0.2126], np.float32)
    L = L / max(float(np.percentile(L, 99)), 0.2); L = np.clip(L, 0, 1) ** 0.75
    L = np.clip((L - 0.5) * gain + 0.5 + 0.03, 0, 1); L = 0.75 * L + 0.25 * (L * L * (3 - 2 * L))
    return np.repeat(L[..., None], 3, axis=2)
def photo_rgba(img, box, width, border=14):
    x0, y0, x1, y1 = box; c = bw(img[y0:y1, x0:x1]); h = int(round(width * (y1 - y0) / (x1 - x0)))
    c = cv2.resize(c, (width, h), interpolation=cv2.INTER_AREA)
    out = np.zeros((h + 2 * border + 10, width + 2 * border + 10, 4), np.float32)
    out[9:9 + h + 2 * border, 8:8 + width + 2 * border, 3] = 0.45                               # ombre
    out[..., 3] = cv2.GaussianBlur(out[..., 3], (0, 0), 3)
    out[:h + 2 * border, :width + 2 * border, :3] = np.array([0.90, 0.92, 0.93], np.float32)    # bord papier photo
    out[:h + 2 * border, :width + 2 * border, 3] = 1
    out[border:border + h, border:border + width, :3] = c
    return out
def cutout_rgba(img, m, box, white=False):
    x0, y0, x1, y1 = box; c = grade(img[y0:y1, x0:x1])
    if white: c = np.ones_like(c) * np.array([0.96, 0.97, 0.98], np.float32)
    return np.dstack([c, m]).astype(np.float32)


# ---------------- collage poussé (retour Luca 27/10) : déchirures, scotch, bandes de papier, couches qui sautent sur les frappes ----------------
def skey(x): return sum((i + 1) * ord(c) for i, c in enumerate(str(x)))
def torn_mask(h, w, rng, rough=7, step=14, inset=8):
    """Masque de papier déchiré : contour du rectangle avec bords irréguliers."""
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
    col = np.array([0.74, 0.86, 0.91], np.float32)[None, None, :] * (1 + 0.04 * rng.standard_normal((h, w, 1)).astype(np.float32))
    return np.dstack([col, m * 0.78]).astype(np.float32)
def halftone(h, w, col, dot=(0.12, 0.10, 0.10), step=14):
    img = np.ones((h, w, 3), np.float32) * col[None, None, :]
    for y in range(0, h, step):
        for x in range((y // step % 2) * step // 2, w, step): cv2.circle(img, (x, y), 4, dot, -1, cv2.LINE_AA)
    return img
STRIP_COLS = [RED, CREAM, BLUE, "#E9C46A", LBLUE, PURPLE, NAVY, "#FFFFFF"]
def strip_rgba(w, h, rng, colhex, ht=False):
    """Bande de papier déchiré (couleur pleine, parfois trame d'imprimerie), ombre portée."""
    col = hexc(colhex); body = halftone(h, w, col) if ht else np.ones((h, w, 3), np.float32) * col[None, None, :]
    body = np.clip(body * (1 + 0.035 * cv2.GaussianBlur(rng.standard_normal((h, w)).astype(np.float32), (0, 0), 1.5))[..., None], 0, 1)
    m = torn_mask(h, w, rng, rough=9, step=12)
    out = np.zeros((h + 16, w + 16, 4), np.float32)
    out[10:10 + h, 8:8 + w, 3] = cv2.GaussianBlur(m, (0, 0), 3) * 0.45
    a = m[..., None]; out[:h, :w, :3] = body * a; out[:h, :w, 3] = np.maximum(m, out[:h, :w, 3])
    out[:h, :w, :3] = out[:h, :w, :3] + 0 * (1 - a)
    return out
def make_strips(sh):
    """Bandes de papier qui s'empilent une par frappe derrière la figure (stop-motion)."""
    n = sh.get("strips", 0); rng = np.random.default_rng(skey(sh["id"]) + 5); out = []
    zones = [(150, 480), (930, 560), (120, 1250), (960, 1300), (540, 300), (540, 1700), (230, 900), (880, 1050)]
    for k in range(n):
        w, h = int(rng.uniform(380, 640)), int(rng.uniform(90, 170))
        colhex = STRIP_COLS[(k + skey(sh["id"])) % len(STRIP_COLS)]
        if colhex == sh.get("bg"): colhex = STRIP_COLS[(k + 3) % len(STRIP_COLS)]
        cx, cy = zones[(k * 3 + skey(sh["id"])) % len(zones)]
        out.append(dict(img=strip_rgba(w, h, rng, colhex, ht=(k % 3 == 1)), cx=cx + rng.uniform(-60, 60), cy=cy + rng.uniform(-60, 60),
                        ang=rng.uniform(-28, 28), k=k))
    return out
class Photo:
    """Photo N&B (vidéo vivante) : bord papier déchiré, scotch aux coins, ombre ; elle saute un peu sur chaque frappe."""
    def __init__(self, frames, box, width, center, angle, f0, key, border=16):
        self.frames, self.box, self.width, self.center, self.angle, self.f0, self.key = frames, box, width, center, angle, f0, key
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
        c = cv2.resize(bw(self.frames[i][y0:y1, x0:x1]), (self.width, self.h), interpolation=cv2.INTER_AREA)
        hh, ww = self.h + 2 * b, self.width + 2 * b
        out = np.zeros((hh + 2 * M, ww + 2 * M, 4), np.float32); out[..., 3] = self.shadow
        body = np.ones((hh, ww, 3), np.float32) * np.array([0.90, 0.92, 0.93], np.float32); body[b:b + self.h, b:b + self.width] = c
        a = self.mask[..., None]; reg = out[M:M + hh, M:M + ww]
        reg[..., :3] = body * a; reg[..., 3] = np.maximum(self.mask, reg[..., 3])
        for t, (tx, ty) in self.tape_imgs:
            th, tw = t.shape[:2]; ty2, tx2 = max(0, ty), max(0, tx)
            sub = out[ty2:ty2 + th, tx2:tx2 + tw]; tt = t[:sub.shape[0], :sub.shape[1]]
            ta = tt[..., 3:4]; sub[..., :3] = sub[..., :3] * (1 - ta) + tt[..., :3] * ta; sub[..., 3] = np.maximum(sub[..., 3], tt[..., 3])
        return out
def beat_grid():
    """Frappes réelles (kicks) + grille d'un temps prolongée dans le break filtré (sans kick) jusqu'au drop."""
    g = sorted(KICKS); last = max(k for k in g if k < CUTS[2] - 0.5); t = last + T
    while t < CUTS[2] - 0.15: g.append(t); t += T
    return sorted(g)
BEATS = beat_grid(); BEATF = [fr(b) for b in BEATS]
def nbeat(f): return sum(1 for b in BEATF if b <= f)
def jit(key, k, amp=8.0, ang=1.5):
    r = np.random.default_rng(skey(key) * 1000 + k); return r.uniform(-amp, amp), r.uniform(-amp, amp), r.uniform(-ang, ang)
def sticker(m, r=7):
    """Contour blanc d'autocollant autour d'une découpe (masque dilaté)."""
    return cv2.dilate(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1)))
TORN_EDGES = None
def torn_edges():
    """Bords de papier déchiré crème en haut et en bas (plan plein cadre B3 collé comme une photo)."""
    global TORN_EDGES
    if TORN_EDGES is None:
        rng = np.random.default_rng(11); out = np.zeros((H, W, 4), np.float32); col = hexc(CREAM)
        for y0, y1 in ((0, 150), (H - 170, H)):
            pts = [(0, y0)] if y0 == 0 else [(0, y1)]
            ys = (lambda: rng.uniform(95, 150)) if y0 == 0 else (lambda: H - rng.uniform(110, 170))
            pts += [(x, ys()) for x in range(0, W + 12, 12)]; pts += [(W, y0)] if y0 == 0 else [(W, y1)]
            m = np.zeros((H, W), np.float32); cv2.fillPoly(m, [np.array(pts, np.int32)], 1.0, lineType=cv2.LINE_AA)
            sh_ = cv2.GaussianBlur(np.roll(m, 8 if y0 == 0 else -8, axis=0), (0, 0), 5) * 0.5
            out[..., 3] = np.maximum(out[..., 3], np.maximum(m, sh_)); out[..., :3] += m[..., None] * col
        TORN_EDGES = out
    return TORN_EDGES

# ---------------- plans ----------------
# Tableaux de texte (mot à mot sur la voix) — dans la zone sûre, au-dessus de la tête
A1_TXT = [[("BIENTÔT", wt(0))], [("QUAND", wt(1)), ("LE", wt(2))], [("VENT", wt(3)), ("AURA", wt(4))], [("TOURNÉ", wt(5))]]
A2_TXT = [[("ET", wt(6)), ("QUE", wt(7))], [("NOUS", wt(8))], [("SERONS", wt(9)), ("AU", wt(10))], [("POUVOIR", wt(11))]]
A3a_TXT = [[("NOUS", wt(12))], [("ASSUMERONS", wt(13))], [("DE", wt(14)), ("TAXER", wt(15))], [("LES", wt(16)), ("RICHES", wt(17))]]
A3b_TXT = [[("DE", wt(18)), ("BLOQUER", wt(19))], [("LES", wt(20)), ("PRIX", wt(21))], [("DES", wt(22)), ("PRODUITS", wt(23))], [("ESSENTIELS", wt(24))]]
KEY = ("TOURNÉ", "POUVOIR", "RICHES", "PRIX", "TAXER", "BIENTÔT")
SOT_BOX = (520, 60, 1530, 724)        # Aubry au pupitre, coupée au bord du pupitre (logo et drapeau UE hors champ)
SHOTS = [
    dict(id="A1", kind="cut", src="SOT", t=V_SRC0, bg=PURPLE, box=SOT_BOX, scale=(1.72, 1.74), cx=1026, txt=A1_TXT, txt_y=250, txt_h=150,
         strips=4, why="2026 — plénière, état de l'Union : « Bientôt, quand le vent aura tourné… » en son direct, Aubry détourée sur fond violet uni"),
    dict(id="A2", kind="cut", src="SOT", t=None, bg=BLUE, box=SOT_BOX, scale=(1.74, 1.765), cx=1026, txt=A2_TXT, txt_y=250, txt_h=150,
         photos=[("MA", 0.30, (0, 120, 1560, 1080), 520, (300, 720), -5, 0.0), ("SOIR", 10.5, (500, 140, 1420, 450), 540, (790, 640), 4, 0.0)],
         strips=3, why="même plan synchro : « …et que nous serons au pouvoir », fond bleu + photos N&B du meeting de Strasbourg et de la soirée 2024"),
    dict(id="A3", kind="cut", src="SOT", t=None, bg=CREAM, box=SOT_BOX, scale=(1.765, 1.82), cx=1026, txt=A3a_TXT, txt_y=250, txt_h=150,
         txt2=A3b_TXT, txt2_t=BOARD_B_T, txt2_y=250,
         photos=[("MB", 21.0, (0, 100, 1560, 1080), 500, (270, 1020), -6, 0.0), ("MA", 12.5, (0, 140, 1560, 1080), 500, (820, 980), 5, 0.49),
                 ("MC", 36.0, (0, 140, 1560, 1080), 460, (200, 1500), 4, 0.98)],
         strips=7, why="même plan synchro : « nous assumerons de taxer les riches, de bloquer les prix des produits essentiels » ; les slogans s'accumulent, scrapbook qui se remplit pendant le break"),
    dict(id="B1", kind="sil", src="MC", t=13.0, bg=NAVY, box=(420, 0, 1560, 1080), dest_w=1180, cx=960, push=(1.0, 1.04),
         txt=[[("TAXER", 0.0)], [("LES", TB)], [("RICHES", TB)]], txt_y=250, txt_h=150,
         strips=3, flash=True, why="2026 — meeting de Strasbourg, bras levé : silhouette blanche 3 images (flash du drop) puis Aubry détourée en couleur, contour autocollant, sur fond sombre"),
    dict(id="B2", kind="collage", bg=PURPLE,
         photos=[("MA", 0.30, (0, 120, 1560, 1080), 700, (520, 760), -4, 0.0), ("MA", 27.5, (560, 0, 1440, 1000), 470, (330, 1240), 5, 0.24),
                 ("SOIR", 11.0, (500, 140, 1420, 450), 600, (650, 1520), -3, 0.49)],
         txt=[[("BLOQUER", 0.0)], [("LES", TB), ("PRIX", TB)]], txt_y=250, txt_h=150,
         strips=3, why="collage : photos N&B (salle de Strasbourg mains levées, Aubry en gros plan, scène de la soirée 2024) collées sur fond violet"),
    dict(id="B3", kind="full", src="MB", t=30.4, crop=(878, 540, 1080), push=(1.0, 1.05), focus=(878, 400),
         big=[("AU", 0.0, (250, 250, 250)), ("POUVOIR", TB, (250, 250, 250))], big_y=1000, big_sizes=[150, 210], flash=True,
         why="2026 — meeting de Strasbourg, plein cadre couleur, bras ouverts face à la salle ; gros texte blanc avec contour (lisible sur fond variable)"),
    dict(id="B4", kind="cut", src="SOT", t=79.0, bg=RED, box=SOT_BOX, scale=(1.74, 1.79), cx=1015,
         photos=[("MB", 21.5, (0, 100, 1560, 1080), 560, (300, 820), -5, 0.0), ("MA", 13.0, (0, 140, 1560, 1080), 520, (800, 700), 6, 0.0)],
         txt=[[("NOUS", 0.0)], [("ASSUMERONS", TB)]], txt_y=250, txt_h=150,
         strips=2, why="2026 — plénière (autre moment, sans le son), Aubry détourée sur fond rouge + photos N&B de la salle"),
    dict(id="B5", kind="cut", src="MC", t=16.2, bg=BLUE, box=(380, 0, 1560, 1080), scale=(1.05, 1.09), cx=935, bottom=1920,
         photos=[("SOIR", 12.0, (500, 140, 1420, 450), 640, (540, 600), -3, 0.0)],
         txt=[[("LE", 0.0), ("VENT", 0.0)], [("AURA", TB)], [("TOURNÉ", TB)]], txt_y=250, txt_h=140,
         strips=3, why="2026 — meeting de Strasbourg, Aubry détourée en couleur sur fond bleu, photo N&B de la soirée 2024 derrière"),
    dict(id="B6", kind="collage", bg=LBLUE,
         photos=[("MC", 40.0, (0, 140, 1560, 1080), 640, (430, 560), 4, 0.0), ("MB", 33.0, (520, 0, 1400, 1000), 460, (760, 900), -6, 0.16),
                 ("SOIR", 9.0, (500, 140, 1420, 450), 640, (480, 1240), 3, 0.33), ("MA", 28.5, (560, 0, 1440, 1000), 420, (330, 1500), -4, 0.49)],
         strips=3, why="collage qui se remplit photo après photo (demi-temps) : salle, Aubry, scène 2024 — sans texte"),
    dict(id="B7", kind="sil", src="MC", t=9.2, bg=PURPLE, box=(0, 0, 1500, 1080), dest_w=1500, cx=880, push=(1.0, 1.03),
         txt=[[("BIENTÔT", 0.0)]], txt_y=300, letters=True, txt_h=190,
         strips=3, why="2026 — meeting de Strasbourg, de profil, bras tendu vers la salle : silhouette blanche 3 images puis Aubry en couleur, contour autocollant, sur fond violet"),
    dict(id="FIN", kind="card", bg=CREAM, push=(1.0, 1.035),
         big=[("MANON", 0.0, (27, 52, 114)), ("AUBRY", TB, (27, 52, 114)), ("TAXER LES RICHES", 2 * TB, (204, 32, 48))],
         big_y=470, big_sizes=[400, 400, 170], big_font="impact",
         why="carton final propre (fond crème, bold bleu + rouge) : son nom et ses mots, pas de CTA de vote"),
]
BOUNDS_T = [0] + CUTF + [fr(END)]
assert len(BOUNDS_T) == len(SHOTS) + 1, (len(BOUNDS_T), len(SHOTS))
for i, sh in enumerate(SHOTS):
    sh["a"], sh["bb"] = BOUNDS_T[i], BOUNDS_T[i + 1]; sh["n"] = sh["bb"] - sh["a"]; sh["clip"] = "R1_%s.mov" % sh["id"]
    if sh.get("src") == "SOT" and sh["t"] is None: sh["t"] = V_SRC0 + sh["a"] / FPS          # plans A synchro avec la voix
assert min(sh["n"] for sh in SHOTS) >= 15, [(s["id"], s["n"]) for s in SHOTS]

def write_mov(frames, path):
    p = subprocess.Popen([FF, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", "%dx%d" % (W, H), "-r", str(FPS), "-i", "-",
                          "-c:v", "prores_ks", "-profile:v", "3", "-pix_fmt", "yuv422p10le", "-vendor", "apl0", path], stdin=subprocess.PIPE)
    for f in frames: p.stdin.write((np.clip(f, 0, 1) * 255 + 0.5).astype(np.uint8).tobytes())
    p.stdin.close(); p.wait()
def draw_pieces(img, pieces, tl, f_abs, boil=None):
    k = nbeat(f_abs)
    for j, (im, cx, cy, t) in enumerate(pieces):
        s = pop(f_abs, fr(t))
        if s is None: continue
        dx, dy, da = jit((boil, j), k, amp=4, ang=1.0) if boil else (0, 0, 0)       # les découpes « bougent » sur chaque frappe
        paste(img, im, cx + dx, cy + dy, s, da)
CARD_TAPES = [tape_rgba(170, 46, np.random.default_rng(40 + j)) for j in range(4)]                                     # flash blanc 3 images sur les transitions fortes (drop, plein cadre)
def render(sh):
    n = sh["n"]; a = sh["a"]; frames = []
    rel = lambda t: sh["a"] / FPS + t                                       # temps relatifs au plan -> timeline
    def abs_pieces(p, timeline_abs):
        return [(im, cx, cy, (t if timeline_abs else rel(t))) for im, cx, cy, t in p]
    sync = sh["id"].startswith("A")
    txt = abs_pieces(board(sh["txt"], sh["txt_y"], seed=sum(map(ord, sh["id"])) * 7, letters=(KEY if not sh.get("letters") else ("BIENTÔT",)),
                           h=sh.get("txt_h", 118)), sync) if sh.get("txt") else []
    txt2 = abs_pieces(board(sh["txt2"], sh["txt2_y"], seed=77, letters=KEY, h=150), True) if sh.get("txt2") else []
    big = []
    if sh.get("big"):
        big = abs_pieces(big_text([(s, t, c) for s, t, c in sh["big"]], sh["big_y"], None, sizes=sh["big_sizes"], spec=((S + "Impact.ttf", 0) if sh.get("big_font") else FCOND),
                                  maxw=(XMAX - XMIN) * (0.86 if sh["kind"] == "card" else 1.0),
                                  contour=10 if sh["kind"] == "full" else 0), False)
    # photos : (src, t, box, largeur, (cx, cy), angle, apparition en s dans le plan) — vidéo N&B vivante, bord déchiré + scotch
    photos = [Photo(read_frames(ps, pt, n), pbox, pw, pc, pa, fr(rel(pt0)), (sh["id"], j))
              for j, (ps, pt, pbox, pw, pc, pa, pt0) in enumerate(sh.get("photos", []))]
    strips = make_strips(sh)
    k0 = nbeat(a)
    if sh["kind"] in ("cut", "sil", "full"):
        raw = read_frames(sh["src"], sh["t"], n)
    if sh["kind"] in ("cut", "sil"):
        ms = masks("%s_%s_%.2f_%d" % (sh["id"], sh["src"], sh["t"], n), raw, sh["box"], k=27 if sh["kind"] == "sil" else 13)
    for i in range(n):
        f = a + i; u = i / max(n - 1, 1); kb = nbeat(f) - k0                 # frappes passées depuis le début du plan
        if sh["kind"] == "full":
            cx, cy, vh = sh["crop"]; z = sh["push"][0] + (sh["push"][1] - sh["push"][0]) * u
            s = H / vh * z; fx_, fy_ = sh["focus"]
            ccx = cx + (fx_ - cx) * (1 - 1 / z); ccy = cy + (fy_ - cy) * (1 - 1 / z)
            M = np.float32([[s, 0, W / 2 - ccx * s], [0, s, H / 2 - ccy * s]])
            img = grade(cv2.warpAffine(raw[i], M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE), 1.1)
        else:
            img = paper(sh["bg"])
        for st in strips:                                                   # une bande de plus à chaque frappe
            if st["k"] <= kb:
                dx, dy, da = jit((sh["id"], "s", st["k"]), nbeat(f), amp=6, ang=1.2)
                s_ = pop(f, BEATF[k0 + st["k"]] if st["k"] > 0 and k0 + st["k"] < len(BEATF) else a, n=4, amp=0.08) or 1.0
                paste(img, st["img"], st["cx"] + dx, st["cy"] + dy, s_, st["ang"] + da)
        for ph in photos:
            s_ = pop(f, ph.f0, n=5, amp=0.10)
            if s_ is not None:
                dx, dy, da = jit(ph.key, nbeat(f), amp=9, ang=1.8)
                paste(img, ph.rgba(i), ph.center[0] + dx, ph.center[1] + dy, s_, ph.angle + da)
        if sh["kind"] == "cut":
            x0, y0, x1, y1 = sh["box"]; sc = sh["scale"][0] + (sh["scale"][1] - sh["scale"][0]) * u
            m = ms[i]; rgba = cutout_rgba(raw[i], m, sh["box"]); hh = (y1 - y0) * sc
            st_ = np.dstack([np.ones_like(rgba[..., :3]) * np.array([0.96, 0.96, 0.95], np.float32), sticker(m)])
            sd = st_.copy(); sd[..., :3] = 0; sd[..., 3] = cv2.GaussianBlur(st_[..., 3], (0, 0), 5) * 0.5
            fcx = (sh["cx"] - x0) * sc; ccx = W / 2 + ((x1 - x0) / 2 * sc - fcx); ccy = sh.get("bottom", H) - hh / 2
            paste(img, sd, ccx + 10, ccy + 8, sc); paste(img, st_, ccx, ccy, sc); paste(img, rgba, ccx, ccy, sc)
        elif sh["kind"] == "sil":
            x0, y0, x1, y1 = sh["box"]; z = sh["push"][0] + (sh["push"][1] - sh["push"][0]) * u
            sc = sh["dest_w"] / (x1 - x0) * z; hh = (y1 - y0) * sc; m = ms[i]
            ccx = W / 2 + ((x1 - x0) / 2 - (sh["cx"] - x0)) * sc; ccy = H - hh / 2
            st_ = np.dstack([np.ones((m.shape[0], m.shape[1], 3), np.float32) * np.array([0.96, 0.96, 0.95], np.float32), sticker(m, 9)])
            sd = st_.copy(); sd[..., :3] = 0; sd[..., 3] = cv2.GaussianBlur(st_[..., 3], (0, 0), 6) * 0.55
            paste(img, sd, ccx + 14, ccy + 10, sc)
            if i < 3: paste(img, cutout_rgba(raw[i], m, sh["box"], white=True), ccx, ccy, sc)     # silhouette blanche : flash de 3 images
            else: paste(img, st_, ccx, ccy, sc); paste(img, cutout_rgba(raw[i], m, sh["box"]), ccx, ccy, sc)
        if sh["kind"] == "full":
            te = torn_edges(); img = img * (1 - te[..., 3:4]) + te[..., :3]
        if sh.get("txt2") and f >= fr(sh["txt2_t"]): draw_pieces(img, txt2, None, f, boil=sh["id"] + "b")
        else: draw_pieces(img, txt, None, f, boil=sh["id"])
        if sh["kind"] == "card":                                            # carton propre, juste scotché aux coins
            for j, (tx, ty, ta) in enumerate(((175, 300, -32), (905, 300, 30), (175, 1540, 28), (905, 1540, -30))):
                paste(img, CARD_TAPES[j], tx, ty, 1.0, ta)
        if big:
            if sh["kind"] == "card":
                z = sh["push"][0] + (sh["push"][1] - sh["push"][0]) * u
                for im, cx, cy, t in big:
                    s_ = pop(f, fr(t))
                    if s_ is not None: paste(img, im, W / 2 + (cx - W / 2) * z, H / 2 + (cy - H / 2) * z, s_ * z)
            else: draw_pieces(img, big, None, f)
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
    v = grab(HG + "/" + SRC["SOT"][0], V_IN, V_OUT - V_IN); env = np.ones(len(v), np.float32)
    k = int(0.03 * sr); env[:k] = np.linspace(0, 1, k); k = int(0.06 * sr); env[-k:] = np.linspace(1, 0, k)
    i0 = int(round(t_of_src(V_IN) * sr)); voix[i0:i0 + len(v)] = v * env[:, None] * 10 ** (4 / 20)
    m = music_raw(MUSIC_IN)[:N]
    t = np.arange(len(m)) / sr; brk = 59.75 - MUSIC_IN; vend = t_of_src(V_OUT); dr = CUTS[2]
    # sous la phrase : -17 dB, montée dans le break (-17 -> -9 dB), pleine sur le drop « One more time »
    gdb = np.interp(t, [0, 0.3, brk, vend, dr - 0.03, dr, END], [-26, -17, -16, -9, -6, 0, 0])
    k = int(0.45 * sr); fo = np.ones(len(m), np.float32); fo[-k:] = np.linspace(1, 0, k)
    mus[:len(m)] = m * (10 ** (gdb / 20) * fo)[:, None]
    sf.write(OUT + "R1-voix.wav", voix, sr, subtype="PCM_24"); sf.write(OUT + "R1-musique.wav", mus, sr, subtype="PCM_24")
    sf.write(D + "tmp_mix.wav", voix + mus, sr, subtype="FLOAT")
    r = subprocess.run([FF, "-hide_banner", "-i", D + "tmp_mix.wav", "-af", "loudnorm=I=-14:TP=-2.5:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    js = json.loads(r[r.rindex("{"):r.rindex("}") + 1])
    af = ("loudnorm=I=-14:TP=-2.5:LRA=11:measured_I=%s:measured_TP=%s:measured_LRA=%s:measured_thresh=%s:offset=%s:linear=true,"
          "aresample=48000" % (js["input_i"], js["input_tp"], js["input_lra"], js["input_thresh"], js["target_offset"]))
    subprocess.run([FF, "-v", "error", "-y", "-i", D + "tmp_mix.wav", "-af", af, "-c:a", "pcm_s24le", OUT + "R1-mix.wav"], check=True)
    os.remove(D + "tmp_mix.wav"); print("audio : mix avant normalisation", js["input_i"], "LUFS")

# ---------------- plan ----------------
def build_plan():
    video = []
    for sh in SHOTS:
        v = {"id": sh["id"], "clip": sh["clip"], "folder": "genR1", "path": OUT + sh["clip"], "s": 0, "e": sh["n"], "rec": sh["a"], "dur": sh["n"],
             "clip_fps": FPS, "speed_pct": 100, "track": 1, "note": sh["why"], "kind": sh["kind"], "temps": round(sh["n"] / FPS / T, 2)}
        if sh.get("src"):
            path, sfps, url, off, ctx = SRC[sh["src"]]
            v["source"] = {"fichier": path, "in_s": round(sh["t"], 3), "out_s": round(sh["t"] + sh["n"] / FPS, 3), "fps": sfps, "url": url, "contexte": ctx}
        if sh.get("photos"):
            v["photos_nb"] = [{"fichier": SRC[p[0]][0], "in_s": p[1], "out_s": round(p[1] + sh["n"] / FPS, 2), "cadre_source": p[2], "url": SRC[p[0]][2]} for p in sh["photos"]]
        video.append(v)
    texts = []
    for sh in SHOTS:
        for key in ("txt", "txt2"):
            for line in sh.get(key, []):
                texts.append({"plan": sh["id"], "texte": " ".join(w for w, _ in line)})
        for s_, t_, c_ in sh.get("big", []): texts.append({"plan": sh["id"], "texte": s_})
    plan = {"name": "R1 - Collage ransom-note - Manon Aubry", "fps": FPS, "w": W, "h": H, "duree_s": END,
            "note": "Plans ProRes 9:16 composés en Python (lot5/_claude/gen/R1/out) : fonds unis + grain papier, Aubry détourée (segment/Vision), "
                    "silhouettes en aplat blanc, photos N&B vivantes collées, textes ransom-note cuits. s/e en images du clip (30 i/s), rec en images timeline. "
                    "Coupes sur les kicks réels de One More Time (out/R1-frappes.json). Aucun ralenti. Générateur : lot5/_claude/gen/R1/genR1.py",
            "phrase": {"texte": "Bientôt, quand le vent aura tourné et que nous serons au pouvoir, nous assumerons de taxer les riches, de bloquer les prix des produits essentiels",
                       "url": SRC["SOT"][2], "source": SRC["SOT"][0], "in_s": 71.08, "out_s": 78.24,
                       "timeline_s": [round(t_of_src(71.08), 2), round(t_of_src(78.24), 2)],
                       "voix": "son direct synchro (plans A1-A3) ; la phrase continue dans la source (« de geler la dette… ») : coupure après « essentiels », sens intact"},
            "musique": {"fichier": "lot5/sons/R1-daftpunk-one-more-time_complet.wav", "titre": "Daft Punk - One More Time", "url": SON_URL,
                        "debut_complet_s": round(MUSIC_IN, 4), "fin_complet_s": round(MUSIC_IN + END, 3), "drop_timeline_s": CUTS[2],
                        "coupes_kicks_s": CUTS, "coupes_images": CUTF},
            "textes": texts,
            "video": video,
            "audio": [{"id": "mix", "clip": "R1-mix.wav", "folder": "genR1", "path": OUT + "R1-mix.wav", "rec": 0, "track": 1,
                       "note": "mix -14 LUFS : voix SOT %.2f-%.2f s (+4 dB) à %.2f s ; One More Time dès %.3f s du complet, -17 dB sous la voix, montée dans le break, plein au drop, fondu de fin 0,45 s"
                               % (V_IN, V_OUT, t_of_src(V_IN), MUSIC_IN)}],
            "stems": ["lot5/_claude/gen/R1/out/R1-voix.wav", "lot5/_claude/gen/R1/out/R1-musique.wav"],
            "logos_exclus": "SOT : pupitre (logo du Parlement, drapeau UE) sous la découpe ; Strasbourg : logo ELA hors des cadres photo et hors des détourages ; soirée 2024 : logo LFI, bandeau et pancarte hors cadre photo"}
    json.dump(plan, open(D + "plan-R1.json", "w"), indent=1, ensure_ascii=False)
    son = {"id": "R1", "titre": "One More Time", "artiste": "Daft Punk", "url": SON_URL,
           "chaine": "Daft Punk (officielle, certifiée, « Daft Punk - One More Time (Official Video) »)",
           "fichier": "lot5/sons/R1-daftpunk-one-more-time_complet.wav",
           "extrait_complet_s": {"debut": round(MUSIC_IN, 4), "fin": round(MUSIC_IN + END, 3)},
           "paroles_audibles": "sous la phrase : instrumental filtré puis break (59,75-63,55 s) ; au drop : « One more time, we're gonna celebrate, oh yeah, alright, don't stop the dancing » puis début de « One more time » (Whisper : « I'm gonna celebrate »)",
           "bpm": 123.0, "temps_s": round(T, 4),
           "drop": {"complet_s": round(MUSIC_IN + CUTS[2], 4), "timeline_s": CUTS[2], "nature": "retour du kick après le break filtré, sur « One more time »"},
           "frappes_timeline_s": [round(k, 4) for k in KICKS], "coupes_sur_frappes_s": CUTS,
           "mix": "lot5/_claude/gen/R1/out/R1-mix.wav"}
    json.dump(son, open(D + "son.json", "w"), indent=1, ensure_ascii=False)

# ---------------- aperçu 540x960 ----------------
def apercu():
    plan = json.load(open(D + "plan-R1.json")); ins = []; fl = []
    for i, v in enumerate(plan["video"]):
        ins += ["-i", OUT + v["clip"]]
        fl.append("[%d:v]trim=start_frame=%d:end_frame=%d,setpts=PTS-STARTPTS,scale=540:960,setsar=1[v%d]" % (i, v["s"], v["e"], i))
    k = len(plan["video"]); fl.append("".join("[v%d]" % i for i in range(k)) + "concat=n=%d:v=1:a=0[v]" % k)
    ins += ["-i", OUT + "R1-mix.wav"]; out = HG + "/preview/apercu-R1.mp4"
    subprocess.run([FF, "-v", "error", "-y"] + ins + ["-filter_complex", ";".join(fl), "-map", "[v]", "-map", "%d:a" % k,
                    "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "aac", "-b:a", "192k", "-shortest", out], check=True)
    print("aperçu", out)
# ---------------- mesure sur l'export : coupes vs kicks, LUFS / TP ----------------
def mesure():
    out = HG + "/preview/apercu-R1.mp4"
    r = subprocess.run([FF, "-v", "info", "-i", out, "-vf", "scale=135:240,select='gt(scene,0.25)',showinfo", "-an", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    cuts = [float(x) for x in re.findall(r"pts_time:([0-9.]+)", r)]
    p = subprocess.run([FF, "-v", "error", "-i", out, "-vn", "-ac", "2", "-ar", "48000", "-f", "f32le", "-"], capture_output=True)
    y = np.frombuffer(p.stdout, np.float32).reshape(-1, 2)
    h = [x[0] for x in detect_hits(y) if x[1] == "kick" and x[3] > 0.03]
    print("coupes image détectées (export) :", cuts)
    worst = 0
    for c in [fr_ / FPS for fr_ in CUTF]:
        det = min(cuts, key=lambda x: abs(x - c)) if cuts else None
        k = min(h, key=lambda t: abs(t - c)); e = (c - k) * 1000; worst = max(worst, abs(e))
        print("  coupe %.3f (détectée %s)  kick %.4f  écart %+.1f ms" % (c, "%.3f" % det if det is not None else "-", k, e))
    print("écart max coupes/kicks : %.1f ms" % worst)
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
