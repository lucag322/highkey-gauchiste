# R8 (lot 7) — Collage ransom-note « coupures de journal colorées », Jean-Luc Mélenchon, campagne 2022, son The White Stripes – Seven Nation Army.
# Modèle : lot6/_claude/gen/R2/genR2.py (copié puis adapté). Palette : marine, or, crème (pas de sépia, pas de rouge/noir de R2).
# Plus que R2 : pages de journal en deux encres (crème encre marine / marine encre crème), photos de foule en bichromie marine-crème
#   ou marine-or qui s'empilent sur les frappes (jusqu'à 4 par plan), plein cadre en trichromie marine-or-crème, écho or décalé
#   derrière chaque découpe (mauvais repérage), flash blanc 3 images seulement au drop et à l'entrée des pleins cadres.
# Phrase (son direct, synchro) : « Un autre monde est nécessaire, et parce qu'il est nécessaire, alors nous allons le rendre possible. »
#   (marche pour la 6e République, Paris, 20/3/2022, chaîne JEAN-LUC MÉLENCHON, youtu.be/Zlwij7ZXLts 3226,78-3233,66 s)
#   -> autre phrase que Z2 (« jamais lâché prise »), A6, M1, R2, R3, R4, W1, C3, C4, Z1, Z3, A5 ; plans nouveaux (extraits lot7/sources/R8-*).
# Son : Seven Nation Army (clip officiel, chaîne The White Stripes) : la phrase passe sur la fin du couplet 1 et la montée
#   « and the message coming from my eyes says leave it alone », drop = entrée du riff saturé (55,70 s), coupes sur les vraies frappes.
# Découpes (règle Luca 27/10, retour R12) : seulement la personne (pas de pupitre, micro, voisin), corps jusqu'au bord bas du cadre,
#   bords de la zone découpée hors champ (jamais un membre coupé en l'air) ; contrôle en pleine résolution : python genR8.py decoupes
# Usage : python genR8.py [shots] [audio] [plan] [apercu] [mesure] [decoupes] [only=ID,ID]   (sans argument = shots audio plan apercu)
import sys
sys.dont_write_bytecode = True
import os, json, subprocess, math, re
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
HG = "/Users/luca.grousset/Movies/highkey-gauchiste"
D = HG + "/lot7/_claude/gen/R8/"; OUT = D + "out/"; CACHE = D + "cache/"; os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, D)
from hits import detect_hits
FF = "/opt/homebrew/bin/ffmpeg"; SEG = HG + "/_claude/outils/segment"; FPS = 30; W, H = 1080, 1920
def fr(t): return int(round(t * FPS))
def hexc(h): h = h.lstrip("#"); return np.array([int(h[4:6], 16), int(h[2:4], 16), int(h[0:2], 16)], np.float32) / 255   # BGR
def rgb(h): h = h.lstrip("#"); return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
NAVY, NAVYD, GOLD, CREAM, CREAMD, WHITE = "#1D2B52", "#0F1730", "#E3A82B", "#F4EFE2", "#E3DDCC", "#FBF9F3"
GOLDL = "#F2C95C"

# ---------------- sources (lecture seule) ----------------
YT = "https://www.youtube.com/watch?v="
MARCHE = "marche pour la 6e République, place de la République, Paris, 20/3/2022 (chaîne JEAN-LUC MÉLENCHON)"
SRC = {
    "MO": ("lot7/sources/R8-marche2022-monde.mp4", 30.0, YT + "Zlwij7ZXLts", 3214.0, MARCHE + ", extrait 3214-3240 s (la phrase)"),
    "DA": ("lot7/sources/R8-marche2022-drapeaux-a.mp4", 30.0, YT + "Zlwij7ZXLts", 28.0, MARCHE + ", foule et drapeaux avant le discours"),
    "DB": ("lot7/sources/R8-marche2022-drapeaux-b.mp4", 30.0, YT + "Zlwij7ZXLts", 6165.0, MARCHE + ", fin du discours, foule et Mélenchon de dos"),
    "DC": ("lot7/sources/R8-marche2022-drapeaux-c.mp4", 30.0, YT + "Zlwij7ZXLts", 6310.0, MARCHE + ", fin : poing levé, mer de drapeaux, la place"),
    "M3": ("lot4/sources/Z2-marche2022-3266.mp4", 30.0, YT + "Zlwij7ZXLts", 3266.0, MARCHE + ", plan serré au pupitre"),
    "M5": ("lot4/sources/Z2-marche2022-5179.mp4", 30.0, YT + "Zlwij7ZXLts", 5179.0, MARCHE + ", de face au pupitre, bras levé"),
    "GE": ("lot7/sources/R8-marche2022-geste.mp4", 30.0, YT + "Zlwij7ZXLts", 6012.0, MARCHE + ", au pupitre, bras tendu vers la foule"),
    "FA": ("lot4/sources/Z2-premiertour2022-foule-a.mp4", 30.0, YT + "izCL2pR8UCE", 0.0, "soir du 1er tour, Paris, 10/4/2022 (chaîne JEAN-LUC MÉLENCHON)"),
    "FB": ("lot4/sources/Z2-premiertour2022-foule-b.mp4", 30.0, YT + "izCL2pR8UCE", 502.0, "soir du 1er tour, Paris, 10/4/2022 (chaîne JEAN-LUC MÉLENCHON)"),
    "TO": ("lot4/sources/Z2-toulouse2022-5692.mp4", 30.0, YT + "znUyK4s2pNs", 5692.0, "meeting place du Capitole, Toulouse, 3/4/2022 (chaîne JEAN-LUC MÉLENCHON)"),
}
CAM_CUT_F = 490                       # MO : coupe caméra plan de face -> plan serré bras levés (image 490 = 16,333 s, scène détectée)

# ---------------- musique : The White Stripes – Seven Nation Army ----------------
SON_FILE = HG + "/lot7/sons/R8-whitestripes-seven-nation-army_complet.wav"; SON_URL = YT + "0J2QdDbelmY"
T = 0.4900                            # ≈ 122,4 BPM (batterie jouée, pas de grille fixe : les coupes sont prises sur les frappes mesurées)
MDROP = 55.7037                       # entrée du riff saturé après « …says leave it alone » (grosse caisse + crash), mesurée
# coupes (temps du morceau) : grosses caisses mesurées (hits.py), 2 temps par plan après le drop (4 sur le plan C5)
CUT_M = [49.1890, 51.7172, 53.7009, MDROP, 56.6694, 57.6349, 58.6399, 59.6070, 61.5635, 62.5404, 63.5222, 64.5021, 65.4571]
M_END = 67.4474                       # grosse caisse : fin sur une frappe du riff
MUSIC_IN0 = 47.7242                   # départ sur une grosse caisse du couplet
def music_raw(mi, dur, sr=48000):
    import soundfile as sf
    i0 = int(round(mi * sr)); x, r = sf.read(SON_FILE, start=i0, frames=int(dur * sr), dtype="float32"); assert r == sr; return x
def best_in():
    """Décalage fin (±16 ms) du départ musique pour que chaque coupe tombe au plus près d'un bord d'image."""
    best, bad = 0.0, 9
    for off in np.arange(-0.016, 0.0165, 0.001):
        e = max(abs((m - MUSIC_IN0 - off) - fr(m - MUSIC_IN0 - off) / FPS) for m in CUT_M + [M_END])
        if e < bad: best, bad = off, e
    return MUSIC_IN0 + best
def kick_onset(c, win=0.08):
    """Attaque de la grosse caisse près de c (temps du morceau) : enveloppe < 120 Hz, pic dans ±win, attaque à 30 % du pic."""
    import scipy.signal as ss
    sr = 48000; x = music_raw(c - 0.3, 0.6).mean(1)
    e = np.convolve(np.abs(ss.hilbert(ss.sosfiltfilt(ss.butter(4, 120, "lp", fs=sr, output="sos"), x))), np.ones(96) / 96, "same")
    lo, hi = int((0.3 - win) * sr), int((0.3 + win) * sr); pk = lo + int(np.argmax(e[lo:hi])); i = pk
    while i > lo - int(0.04 * sr) and e[i - 1] > 0.3 * e[pk]: i -= 1
    return round(c - 0.3 + i / sr, 4)
CUT_M = [kick_onset(c) for c in CUT_M]; MDROP = CUT_M[3]; M_END = kick_onset(M_END)
FINE = 0.0                            # recalage mesuré sur l'export AAC (voir mesure)
MUSIC_IN = best_in() + FINE
CUTS = [m - MUSIC_IN for m in CUT_M]; CUTF = [fr(c) for c in CUTS]
DROPF = CUTF[3]; DROP = CUTS[3]
END = M_END - MUSIC_IN
HITS_M = [47.7242, 48.2032, 48.6939, 49.1890, 49.7944, 50.2094, 50.7151, 51.2088, 51.7172, 52.2565, 52.7714, 53.3394, 53.7009, 54.2716,
          54.8135, 55.1461, MDROP, 56.1894, 56.6694, 57.1533, 57.6349, 58.1089, 58.6399, 59.1396, 59.6070, 60.0382, 60.6608, 61.0915, 61.5635,
          62.0512, 62.5404, 63.0279, 63.5222, 64.0059, 64.5021, 64.9024, 65.4571, 65.9647, 66.4523, 66.9056, 67.4474]
BEATS = [b - MUSIC_IN for b in HITS_M]; BEATF = [fr(b) for b in BEATS]   # frappes (un temps) : les découpes « bougent » dessus
def nbeat(f): return sum(1 for b in BEATF if b <= f)

# ---------------- voix ----------------
V_SRC0 = (CAM_CUT_F - CUTF[1]) / FPS  # source MO à t = 0 : la coupe A1b/A2a tombe exactement sur la coupe caméra d'origine
V_IN, V_END, V_OUT = 12.74, 19.70, 20.30   # « Un » (12,78) … « possible » (fin 19,66) ; clameur de la foule gardée en fondu jusqu'au drop
def t_of_src(s): return s - V_SRC0
WORDS = [("UN", 12.78), ("AUTRE", 13.04), ("MONDE", 13.34), ("EST", 13.82), ("NÉCESSAIRE", 14.04), ("ET", 15.20), ("PARCE", 15.54),
         ("QU'IL", 15.98), ("EST", 16.24), ("NÉCESSAIRE", 16.36), ("ALORS", 17.50), ("NOUS", 17.82), ("ALLONS", 18.12), ("LE", 18.42),
         ("RENDRE", 18.60), ("POSSIBLE", 18.82)]
def wt(i): return t_of_src(WORDS[i][1])
assert t_of_src(V_END) < DROP - 0.25, ("la phrase déborde sur le drop", t_of_src(V_END), DROP)
assert t_of_src(V_IN) > 0.1, ("voix avant le début", t_of_src(V_IN))

# ---------------- polices ransom-note ----------------
S = "/System/Library/Fonts/Supplemental/"
FONTS = [(S + "Arial Black.ttf", 0), (S + "Georgia Bold.ttf", 0), (S + "Times New Roman Bold.ttf", 0), (S + "Impact.ttf", 0),
         (S + "Courier New Bold.ttf", 0), (S + "Rockwell.ttc", 2), (S + "AmericanTypewriter.ttc", 2), (S + "Didot.ttc", 2),
         (S + "Bodoni 72.ttc", 2), (S + "Futura.ttc", 2), (S + "BigCaslon.ttf", 0), (S + "Baskerville.ttc", 1)]
FIMP = (S + "Impact.ttf", 0)
TEX, TEXN = "TEX", "TEXN"             # puces en papier journal crème (encre marine) / marine (encre crème)
STYLES = [(rgb(CREAM), rgb(NAVY)), (rgb(NAVY), rgb(CREAM)), (rgb(GOLD), rgb(NAVYD)), (rgb(NAVY), rgb(GOLDL)),
          (TEX, rgb(NAVYD)), (rgb(WHITE), rgb(NAVY)), (TEXN, rgb(GOLDL)), (rgb(NAVYD), rgb(CREAM)), (rgb(GOLDL), rgb(NAVY))]
_fc = {}
def font(spec, size):
    k = (spec, size)
    if k not in _fc: _fc[k] = ImageFont.truetype(spec[0], size, index=spec[1])
    return _fc[k]

# ---------------- papier journal (deux encres) ----------------
_news = {}
def news_texture(w, h, seed, base=CREAM, ink=NAVYD, ink_a=0.50):
    """Page de journal : colonnes de faux texte (barres, aucune lettre lisible -> rien pour l'OCR TikTok), intertitres, filets."""
    k = (w, h, seed, base, ink)
    if k in _news: return _news[k].copy()
    rng = np.random.default_rng(seed); inkm = np.zeros((h, w), np.float32)
    m = 26; ncol = max(1, int(round(w / 240))); g = 16; cw = (w - 2 * m - (ncol - 1) * g) / ncol
    for c in range(ncol):
        x0 = m + c * (cw + g); y = m + rng.uniform(0, 40); first = True
        if c > 0: cv2.line(inkm, (int(x0 - g / 2), m), (int(x0 - g / 2), h - m), 0.45, 1)
        while y < h - m - 8:
            if rng.random() < 0.05 or first:                              # intertitre : barres épaisses
                first = False; hh = int(rng.uniform(13, 20)); nl = int(rng.integers(1, 3))
                for _ in range(nl):
                    x = x0
                    while True:
                        ww = int(rng.uniform(26, 80))
                        if x + ww > x0 + cw: break
                        cv2.rectangle(inkm, (int(x), int(y)), (int(x + ww), int(y + hh)), 0.85, -1); x += ww + rng.uniform(7, 11)
                    y += hh + 8
                y += 8; continue
            x = x0 + (14 if rng.random() < 0.1 else 0); lim = x0 + cw * (rng.uniform(0.3, 0.9) if rng.random() < 0.08 else 1.0)
            while True:
                ww = int(rng.uniform(7, 46))
                if x + ww > lim: break
                cv2.rectangle(inkm, (int(x), int(y)), (int(x + ww), int(y + 4)), 0.62, -1); x += ww + rng.uniform(4, 7)
            y += 10 + (7 if rng.random() < 0.07 else 0)
    inkm = cv2.GaussianBlur(inkm, (0, 0), 0.7)
    n = cv2.resize(rng.standard_normal((max(2, h // 40), max(2, w // 40))).astype(np.float32), (w, h), interpolation=cv2.INTER_CUBIC)
    n2 = cv2.GaussianBlur(rng.standard_normal((h, w)).astype(np.float32), (0, 0), 1.1)
    b = hexc(base)[None, None, :] * (1 + 0.03 * n[..., None] + 0.035 * n2[..., None])
    a = (inkm * ink_a)[..., None]
    out = np.clip(b * (1 - a) + hexc(ink)[None, None, :] * a, 0, 1).astype(np.float32); _news[k] = out
    return out.copy()
def news_navy(w, h, seed): return news_texture(w, h, seed, base=NAVY, ink=CREAM, ink_a=0.30)
_texp = {}
def tex_pil(kind):
    if kind not in _texp:
        t = news_texture(900, 420, 7) if kind == TEX else news_navy(900, 420, 8)
        _texp[kind] = Image.fromarray((np.clip(t[..., ::-1], 0, 1) * 255).astype(np.uint8))
    return _texp[kind]

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
    if bg in (TEX, TEXN):
        t = tex_pil(bg); ox, oy = int(rng.integers(0, max(1, t.width - im.width))), int(rng.integers(0, max(1, t.height - im.height)))
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
    clash = {NAVY: (rgb(NAVY), rgb(NAVYD), TEXN), GOLD: (rgb(GOLD), rgb(GOLDL)), "NEWS": (TEX, rgb(CREAM), rgb(WHITE)),
             "NEWSN": (TEXN, rgb(NAVY), rgb(NAVYD)), "MIX": (TEXN, TEX, rgb(NAVY), rgb(CREAM))}.get(bg, ())
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
def big_text(lines, y0, spec=FIMP, maxw=XMAX - XMIN, sizes=None, gap=-6):
    """Texte propre (carton final) : lignes centrées, largeur max, retour [(img, cx, cy, t)]."""
    pieces = []; y = y0
    for k, (txt, t, col) in enumerate(lines):
        size = (sizes or [300] * len(lines))[k]; f = font(spec, size)
        while f.getlength(txt) > maxw - 44: size -= 4; f = font(spec, size)
        x0, y0b, x1, y1 = f.getbbox(txt)
        im = Image.new("RGBA", (x1 - x0 + 24, y1 - y0b + 24), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.text((12 - x0, 12 - y0b), txt, font=f, fill=tuple(col) + (255,))
        a = np.dstack([np.asarray(im)[..., :3][..., ::-1], np.asarray(im)[..., 3]]).astype(np.float32) / 255
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
        if col in (NAVY, GOLD):                                             # pli de papier : un filet clair en diagonale
            m = np.zeros((H, W), np.float32); cv2.line(m, (0, int(H * 0.62)), (W, int(H * 0.48)), 1.0, 2, cv2.LINE_AA)
            m = cv2.GaussianBlur(m, (0, 0), 1.5) * 0.10; _tex[col] = np.clip(_tex[col] + m[..., None], 0, 1)
    return _tex[col].copy()
def background(bg, key):
    if bg == "NEWS": return news_texture(W, H, 100 + key)
    if bg == "NEWSN": return news_navy(W, H, 200 + key)
    return paper(bg)
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
def read_frames_f(src, f0, n_out):
    """Lecture à l'image près (plans synchro) : décode et garde les images f0 … f0+n-1."""
    p = subprocess.run([FF, "-v", "error", "-i", HG + "/" + SRC[src][0], "-vf", "select=between(n\\,%d\\,%d)" % (f0, f0 + n_out - 1), "-fps_mode", "passthrough",
                        "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True)
    a = np.frombuffer(p.stdout, np.uint8).reshape(-1, 1080, 1920, 3); assert len(a) == n_out, (src, f0, n_out, len(a))
    return [x.astype(np.float32) / 255 for x in a]
sys.path.insert(0, HG + "/_claude/outils")
from decoupe import masques, controle, bas_dechire, planche
def masks(key, frames, box, pt):
    """Découpe propre d'UNE personne (outil partagé decoupe.py : instance Vision x segmentation personne, sans pupitre ni micro,
    une seule forme, lissée) ; pt = point sur la poitrine normalisé dans le box. Cache : cache/dec/<key>."""
    return masques(frames, box, pt, CACHE + "dec/" + key)
def bottom_row(ms):
    """Dernière ligne de la découpe (max sur le plan) : ce bord est posé sur le bas du cadre 9:16."""
    return max(int(np.where((m > 0.5).any(1))[0][-1]) for m in ms if (m > 0.5).any())
LW = np.array([0.0722, 0.7152, 0.2126], np.float32)
def lum(x, pct=99, gamma=0.85):
    L = x @ LW; L = L / max(float(np.percentile(L, pct)), 0.2); return np.clip(L, 0, 1) ** gamma
def ramp(L, cols, knots=None):
    knots = knots or list(np.linspace(0, 1, len(cols))); C = np.stack([hexc(c) for c in cols])
    return np.stack([np.interp(L, knots, C[:, c]) for c in range(3)], -1).astype(np.float32)
def person(x):
    """Découpe de la figure : N&B contrasté, ombres marine (encre), hautes lumières crème."""
    L = lum(x, 99, 0.8); L = np.clip((L - 0.5) * 1.22 + 0.52, 0, 1); L = 0.75 * L + 0.25 * (L * L * (3 - 2 * L))
    return ramp(L, ["#0B1226", "#3A4564", "#C8C7C2", WHITE], [0, 0.3, 0.75, 1])
TONES = {"bleu": ([NAVYD, NAVY, "#9AA2B6", CREAM], [0, 0.35, 0.72, 1]),     # bichromie marine -> crème
         "or": ([NAVYD, "#7A6236", GOLD, CREAM], [0, 0.3, 0.68, 1]),         # marine -> or -> crème
         "tri": ([NAVYD, NAVY, GOLD, CREAM], [0, 0.38, 0.72, 1])}            # plein cadre
def tone(x, kind):
    L = lum(x, 99.5, 0.9); L = np.clip((L - 0.5) * 1.15 + 0.5, 0, 1); cols, kn = TONES[kind]; return ramp(L, cols, kn)

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
    """Morceau de scotch translucide (légèrement froid, pas jaune), bouts dentelés."""
    m = np.ones((h, w), np.float32)
    for y in range(h):
        a = int(rng.integers(0, 7)); b = int(rng.integers(0, 7)); m[y, :a] = 0; m[y, w - b:] = 0
    col = np.array([0.86, 0.88, 0.88], np.float32)[None, None, :] * (1 + 0.04 * rng.standard_normal((h, w, 1)).astype(np.float32))
    return np.dstack([col, m * 0.62]).astype(np.float32)
def halftone(h, w, col, dot, step=14, r=4):
    img = np.ones((h, w, 3), np.float32) * col[None, None, :]
    for y in range(0, h, step):
        for x in range((y // step % 2) * step // 2, w, step): cv2.circle(img, (x, y), r, tuple(float(v) for v in dot), -1, cv2.LINE_AA)
    return img
STRIP_KINDS = [(GOLD, "plain"), ("NEWS", "tex"), (NAVY, "plain"), (GOLD, "ht"), (CREAM, "plain"), ("NEWSN", "texn"), (WHITE, "plain"), (NAVY, "htgold")]
def strip_rgba(w, h, rng, colhex, kind):
    """Bande de papier déchiré : couleur pleine, trame d'imprimerie ou papier journal ; ombre portée."""
    if kind == "tex": body = news_texture(w, h, int(rng.integers(1000)))
    elif kind == "texn": body = news_navy(w, h, int(rng.integers(1000)))
    elif kind == "ht": body = halftone(h, w, hexc(GOLD), tuple(hexc(NAVY)))
    elif kind == "htgold": body = halftone(h, w, hexc(NAVY), tuple(hexc(GOLD)), step=16, r=5)
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
        if colhex == sh.get("bg"): colhex, kind = CREAMD, "plain"
        cx, cy = zones[(k + skey(sh["id"])) % 3] if k < 3 else zones[(k * 3 + skey(sh["id"])) % len(zones)]   # les 3 premières en haut (visibles)
        out.append(dict(img=strip_rgba(w, h, rng, colhex, kind), cx=cx + rng.uniform(-60, 60), cy=cy + rng.uniform(-60, 60),
                        ang=rng.uniform(-28, 28), k=k))
    return out
class Photo:
    """Coupure de journal (vidéo vivante, bichromie) : bord papier déchiré, scotch aux coins, ombre ; elle saute un peu sur chaque frappe."""
    def __init__(self, frames, box, width, center, angle, f0, key, kind="bleu", border=16):
        self.frames, self.box, self.width, self.center, self.angle, self.f0, self.key, self.kind = frames, box, width, center, angle, f0, key, kind
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
        c = cv2.resize(tone(self.frames[i][y0:y1, x0:x1], self.kind), (self.width, self.h), interpolation=cv2.INTER_AREA)
        hh, ww = self.h + 2 * b, self.width + 2 * b
        out = np.zeros((hh + 2 * M, ww + 2 * M, 4), np.float32); out[..., 3] = self.shadow
        body = np.ones((hh, ww, 3), np.float32) * hexc(WHITE); body[b:b + self.h, b:b + self.width] = c
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
WM_PATCH = None
def torn_edges():
    """Bords de papier crème déchiré en haut et en bas (plan plein cadre collé comme une coupure)."""
    global TORN_EDGES
    if TORN_EDGES is None:
        rng = np.random.default_rng(11); out = np.zeros((H, W, 4), np.float32); tex = paper(CREAM)   # papier uni (pas de faux texte : OCR TikTok)
        for y0, y1 in ((0, 150), (H - 170, H)):
            pts = [(0, y0)] if y0 == 0 else [(0, y1)]
            ys = (lambda: rng.uniform(95, 150)) if y0 == 0 else (lambda: H - rng.uniform(110, 170))
            pts += [(x, ys()) for x in range(0, W + 12, 12)]; pts += [(W, y0)] if y0 == 0 else [(W, y1)]
            m = np.zeros((H, W), np.float32); cv2.fillPoly(m, [np.array(pts, np.int32)], 1.0, lineType=cv2.LINE_AA)
            sh_ = cv2.GaussianBlur(np.roll(m, 8 if y0 == 0 else -8, axis=0), (0, 0), 5) * 0.5
            out[..., 3] = np.maximum(out[..., 3], np.maximum(m, sh_)); out[..., :3] += m[..., None] * tex
        TORN_EDGES = out
    return TORN_EDGES

WM_PATCH = strip_rgba(360, 270, np.random.default_rng(91), "NEWS", "tex")
# ---------------- plans ----------------
KEY = ("MONDE", "POSSIBLE")           # mots en lettres découpées une par une
FRONT = (300, 0, 1700, 605)           # MO de face au pupitre : coupé au ras du pupitre (affiche et rangée assise hors zone)
CLOSE = (500, 0, 1920, 1080)           # MO plan serré bras levés : pupitre (affiche) hors zone à gauche
FIST = (300, 0, 1700, 1080)           # DC poing levé : voisins (visages) hors de la zone
GESTE = (300, 0, 1920, 1000)           # GE au pupitre bras tendu : affiche du pupitre hors zone
TV = (200, 0, 1920, 1080)             # FB soir du 1er tour : voisin de gauche hors zone
WM = (0, 180, 1600, 1080)             # cadre photo sous / à gauche du filigrane « L'UNION POPULAIRE » (haut droite)
A1A_TXT = [[("UN", wt(0)), ("AUTRE", wt(1)), ("MONDE", wt(2))]]
A1B_TXT = [[("EST", wt(3)), ("NÉCESSAIRE", wt(4))], [("ET", wt(5)), ("PARCE", wt(6)), ("QU'IL", wt(7))]]
A2A_TXT = [[("EST", wt(8)), ("NÉCESSAIRE", wt(9))], [("ALORS", wt(10)), ("NOUS", wt(11)), ("ALLONS", wt(12))]]
A2B_TXT = [[("LE", wt(13)), ("RENDRE", wt(14))], [("POSSIBLE", wt(15))]]
# après le drop (règle Luca 27/10) : un carton complet, dans l'ordre de la phrase, jamais répété :
# « UN AUTRE MONDE EST NÉCESSAIRE » (C1 + C2, même carton qui reste) / « NOUS ALLONS LE RENDRE POSSIBLE » (C4 + C5), puis plus de texte
DROP1 = [[("UN", 0.0), ("AUTRE", 0.0), ("MONDE", 0.0)], [("EST", 0.0), ("NÉCESSAIRE", 0.0)]]
DROP2 = [[("NOUS", 0.0), ("ALLONS", 0.0)], [("LE", 0.0), ("RENDRE", 0.0)], [("POSSIBLE", 0.0)]]
SHOTS = [
    dict(id="A1a", kind="cut", src="MO", t=None, bg=NAVY, box=FRONT, pt=(0.454, 0.6), scale=(1.86, 1.89), lift=270, cx=935, txt=A1A_TXT, txt_y=270, txt_h=165, sync=True,
         strips=6, why="2022 — marche pour la 6e République, de face au pupitre : « Un autre monde… » en son direct, découpé N&B encre marine, écho or décalé, fond marine"),
    dict(id="A1b", kind="cut", src="MO", t=None, bg="NEWS", box=FRONT, pt=(0.454, 0.6), scale=(1.89, 1.93), lift=270, cx=935, txt=A1B_TXT, txt_y=260, txt_h=140, sync=True,
         strips=7, why="même plan synchro : « …est nécessaire, et parce qu'il… », fond page de journal crème encre marine"),
    dict(id="A2a", kind="full", src="MO", t=None, tone="or", crop=(1400, 540, 1080), push=(1.0, 1.02), focus=(1400, 300), notop=True, wm=True, txt=A2A_TXT, txt_y=1000, txt_h=165, sync=True,
         why="coupe caméra d'origine (même moment) : plan serré bras levés en plein cadre bichromie marine-or, bords de journal déchirés, « …est nécessaire, alors nous allons… » sous le visage"),
    dict(id="A2b", kind="full", src="MO", t=None, tone="bleu", crop=(1400, 540, 1080), push=(1.02, 1.04), focus=(1400, 300), notop=True, wm=True, txt=A2B_TXT, txt_y=1000, txt_h=175, sync=True,
         why="même plan synchro, bichromie marine-crème : « …le rendre possible. » puis la clameur"),
    dict(id="C1", kind="cut", src="GE", t=5.55, bg=NAVY, box=GESTE, pt=(0.5, 0.5), scale=(1.05, 1.08), cx=1300, white3=True, flash=True,
         txt=DROP1, txt_y=255, txt_h=150, txt_seed=4242, txt_bg="MIX", strips=3,
         why="DROP (entrée du riff saturé) : flash 3 images, silhouette blanche puis Mélenchon qui lève la main vers la foule (fin du discours), fond marine"),
    dict(id="C2", kind="collage", bg="NEWS",
         photos=[("DA", 9.5, WM, 640, (370, 1000), -4, 0.0, "bleu"), ("DC", 10.0, WM, 600, (740, 1250), 5, T / 2, "or"),
                 ("DB", 9.0, WM, 600, (420, 1560), -5, T, "bleu")],
         txt=DROP1, txt_y=255, txt_h=150, txt_seed=4242, txt_bg="MIX", strips=3,
         why="coupures de journal : foules de la marche qui s'empilent, une par demi-temps (crème, marine-or, marine)"),
    dict(id="C3", kind="full", src="DC", t=19.0, crop=(760, 540, 1080), push=(1.0, 1.05), focus=(760, 600), flash=True,
         why="plein cadre trichromie marine-or-crème : la place de la République noire de monde, bords de journal déchirés, sans texte"),
    dict(id="C4", kind="cut", src="M3", t=14.0, bg=GOLD, box=(600, 0, 1920, 1000), pt=(0.477, 0.6), scale=(1.28, 1.31), cx=1190,
         txt=DROP2, txt_y=250, txt_h=150, txt_seed=5151, txt_bg="MIX", strips=4,
         why="Mélenchon au pupitre, plan serré d'une autre caméra (musique seule), découpé, écho marine, fond or"),
    dict(id="C5", kind="collage", bg="NEWSN",
         photos=[("DB", 28.5, WM, 640, (360, 900), -5, 0.0, "or"), ("TO", 3.5, (0, 150, 1600, 1080), 580, (760, 1130), 6, T, "bleu"),
                 ("FB", 46.0, (0, 0, 1920, 1080), 600, (380, 1380), -4, 2 * T, "or"), ("DA", 14.5, WM, 560, (760, 1600), 4, 3 * T, "bleu")],
         txt=DROP2, txt_y=250, txt_h=150, txt_seed=5151, txt_bg="MIX", strips=3,
         why="les foules s'empilent sur 4 frappes : la marche, Toulouse (Capitole), le soir du 1er tour, la marche ; page de journal marine"),
    dict(id="C6", kind="full", src="DB", t=20.6, crop=(930, 540, 1080), push=(1.0, 1.05), focus=(930, 420), flash=True,
         why="plein cadre trichromie : Mélenchon de dos au pupitre face à la foule et aux drapeaux, sans texte"),
    dict(id="C7", kind="cut", src="FB", t=10.6, bg="NEWS", box=TV, scale=(1.10, 1.13), cx=700, lift=150, pt=(0.47, 0.74), strips=4,
         photos=[("FA", 12.5, (0, 0, 1920, 1080), 640, (540, 520), 4, 0.0, "bleu")],
         why="soir du 1er tour : Mélenchon poing serré (musique seule), découpé, la foule de la soirée collée au-dessus"),
    dict(id="C8", kind="collage", bg=NAVY,
         photos=[("DC", 26.5, WM, 660, (420, 760), -4, 0.0, "or"), ("DA", 18.5, WM, 600, (700, 1140), 5, T / 2, "bleu"),
                 ("TO", 13.0, (0, 150, 1600, 1080), 600, (400, 1500), -6, T, "or")],
         strips=3, why="collage sans texte : la place vue d'en haut, la foule de la marche, Toulouse"),
    dict(id="C9", kind="full", src="DC", t=10.4, crop=(800, 540, 1080), push=(1.0, 1.06), focus=(800, 540), flash=False,
         why="plein cadre trichromie : mer de drapeaux tricolores (fin de la marche), sans texte"),
    dict(id="FIN", kind="card", bg="NEWSN", push=(1.0, 1.035),
         big=[("JEAN-LUC", 0.0, rgb(NAVY)), ("MÉLENCHON", T, rgb(NAVY)), ("2027", 2 * T, rgb(NAVY))],
         big_y=650, big_sizes=[220, 220, 230],
         why="carton final propre (feuille crème sur page de journal marine, marine + bande or) : son nom + 2027 (règle Luca pour toutes les vidéos de Mélenchon)"),
]
BOUNDS_T = [0] + CUTF + [fr(END)]
assert len(BOUNDS_T) == len(SHOTS) + 1, (len(BOUNDS_T), len(SHOTS))
for i, sh in enumerate(SHOTS):
    sh["a"], sh["bb"] = BOUNDS_T[i], BOUNDS_T[i + 1]; sh["n"] = sh["bb"] - sh["a"]; sh["clip"] = "R8_%s.mov" % sh["id"]
    if sh.get("src") == "MO" and sh["t"] is None: sh["f0"] = int(round(V_SRC0 * FPS)) + sh["a"]; sh["t"] = sh["f0"] / FPS   # synchro voix
assert min(sh["n"] for sh in SHOTS) >= 14, [(s["id"], s["n"]) for s in SHOTS]
for sh in SHOTS[:2]: assert sh["f0"] + sh["n"] <= CAM_CUT_F, ("plan de face après la coupe caméra", sh["id"])
for sh in SHOTS[2:4]: assert sh["f0"] >= CAM_CUT_F and sh["f0"] + sh["n"] <= 622, ("plan serré avant la coupe caméra", sh["id"])

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
    """Feuille de papier crème déchirée, collée sur la page de journal marine (carton final)."""
    global CARD
    if CARD is None:
        rng = np.random.default_rng(5); w, h = 900, 1180
        m = torn_mask(h, w, rng, rough=9, step=12, inset=6)
        out = np.zeros((h + 20, w + 20, 4), np.float32); out[12:12 + h, 10:10 + w, 3] = cv2.GaussianBlur(m, (0, 0), 5) * 0.5
        body = paper(CREAM)[:h, :w]; out[:h, :w, :3] = body * m[..., None]; out[:h, :w, 3] = np.maximum(m, out[:h, :w, 3])
        CARD = out
    return CARD
def card_band(w, h, seed):
    """Bande or déchirée derrière « MÉLENCHON » sur le carton final."""
    rng = np.random.default_rng(seed); m = torn_mask(h, w, rng, rough=8, step=12, inset=4)
    out = np.zeros((h, w, 4), np.float32); out[..., :3] = hexc(GOLD); out[..., 3] = m; return out
def cut_geom(sh, u):
    """Échelle et centre du box dans le cadre : le bas de la découpe (ligne yb) tombe sur le bas du cadre 9:16 (+4 px),
    ou « lift » px plus haut avec un bord bas en papier déchiré (bas_dechire) pour que le visage monte dans la zone sûre TikTok."""
    x0, y0, x1, y1 = sh["box"]; sc = sh["scale"][0] + (sh["scale"][1] - sh["scale"][0]) * u
    hh = (y1 - y0) * sc; fcx = (sh["cx"] - x0) * sc; ccx = W / 2 + ((x1 - x0) / 2 * sc - fcx)
    ccy = H + 4 - sh.get("lift", 0) - hh / 2 + ((y1 - y0) - 1 - sh.get("yb", y1 - y0 - 1)) * sc
    return sc, ccx, ccy
def render(sh):
    n = sh["n"]; a = sh["a"]; frames = []
    rel = lambda t: sh["a"] / FPS + t
    def abs_pieces(p, timeline_abs):
        return [(im, cx, cy, (max(t, a / FPS) if timeline_abs else rel(t))) for im, cx, cy, t in p]
    sync = sh.get("sync", False)
    txt = abs_pieces(board(sh["txt"], sh["txt_y"], seed=sh.get("txt_seed", skey(sh["id"]) * 7), letters=KEY, h=sh.get("txt_h", 118), bg=sh.get("txt_bg", sh.get("bg"))), sync) if sh.get("txt") else []
    big = abs_pieces(big_text([(s, t, c) for s, t, c in sh["big"]], sh["big_y"], sizes=sh["big_sizes"], maxw=(XMAX - XMIN) * 0.92), False) if sh.get("big") else []
    # photos : (src, t, box, largeur, (cx, cy), angle, apparition en s dans le plan, bichromie)
    photos = [Photo(read_frames(ps, pt, n), pbox, pw, pc, pa, fr(rel(pt0)), (sh["id"], j), pk)
              for j, (ps, pt, pbox, pw, pc, pa, pt0, pk) in enumerate(sh.get("photos", []))]
    strips = make_strips(sh)
    k0 = nbeat(a)
    if sh["kind"] in ("cut", "full"):
        raw = read_frames_f(sh["src"], sh["f0"], n) if sh.get("f0") is not None else read_frames(sh["src"], sh["t"], n)
    if sh["kind"] == "cut":
        ms = masks("%s_%s_%.3f_%d_%s" % (sh["id"], sh["src"], sh["t"], n, "-".join(map(str, sh["box"]))), raw, sh["box"], sh["pt"]); sh["yb"] = bottom_row(ms)
        if sh.get("lift"): ms = [bas_dechire(m, seed=skey(sh["id"])) for m in ms]
    for i in range(n):
        f = a + i; u = i / max(n - 1, 1); kb = nbeat(f) - k0
        if sh["kind"] == "full":
            cx, cy, vh = sh["crop"]; z = sh["push"][0] + (sh["push"][1] - sh["push"][0]) * u
            s = H / vh * z; fx_, fy_ = sh["focus"]
            ccx = cx + (fx_ - cx) * (1 - 1 / z); ccy = cy + (fy_ - cy) * (1 - 1 / z)
            M = np.float32([[s, 0, W / 2 - ccx * s], [0, s, H / 2 - ccy * s]])
            img = tone(cv2.warpAffine(raw[i], M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE), sh.get("tone", "tri"))
        else:
            img = background(sh["bg"], skey(sh["id"]) % 50)
        for st in strips:                                                   # une bande de plus à chaque frappe
            if st["k"] <= kb + 2:                                          # 3 bandes dès le début du plan, puis une par frappe
                dx, dy, da = jit((sh["id"], "s", st["k"]), nbeat(f), amp=6, ang=1.2)
                kk = k0 + st["k"] - 3
                s_ = pop(f, BEATF[kk] if st["k"] > 2 and 0 <= kk < len(BEATF) else a, n=4, amp=0.08) or 1.0
                paste(img, st["img"], st["cx"] + dx, st["cy"] + dy, s_, st["ang"] + da)
        for ph in photos:
            s_ = pop(f, ph.f0, n=5, amp=0.10)
            if s_ is not None:
                dx, dy, da = jit(ph.key, nbeat(f), amp=9, ang=1.8)
                paste(img, ph.rgba(i), ph.center[0] + dx, ph.center[1] + dy, s_, ph.angle + da)
        if sh["kind"] == "cut":
            x0, y0, x1, y1 = sh["box"]; sc, ccx, ccy = cut_geom(sh, u); m = ms[i]
            body = person(raw[i][y0:y1, x0:x1])
            white = np.ones_like(body) * hexc(WHITE)
            st_ = np.dstack([white, sticker(m, 8)])
            sd = st_.copy(); sd[..., :3] = 0; sd[..., 3] = cv2.GaussianBlur(st_[..., 3], (0, 0), 6) * 0.5
            ecol = hexc(NAVY) if sh["bg"] == GOLD else hexc(GOLD)
            echo = np.dstack([np.ones_like(body) * ecol, sticker(m, 4) * 0.96])
            ex, ey, _ = jit((sh["id"], "echo"), nbeat(f), amp=10, ang=0)    # écho décalé qui saute sur les frappes (mauvais repérage)
            paste(img, sd, ccx + 14, ccy + 10, sc)
            paste(img, echo, ccx - 34 + ex, ccy - 18 + ey, sc * 1.015)
            if sh.get("white3") and i < 3: paste(img, np.dstack([white, m]), ccx, ccy, sc)    # silhouette blanche : 3 images
            else: paste(img, st_, ccx, ccy, sc); paste(img, np.dstack([body, m]), ccx, ccy, sc)
        if sh["kind"] == "full":
            te = torn_edges()
            if sh.get("notop"): te = te.copy(); te[:H // 2] = 0                    # tête près du haut : pas de bord déchiré dessus
            img = img * (1 - te[..., 3:4]) + te[..., :3]
            if sh.get("wm"): paste(img, WM_PATCH, 1010, 205, 1.0, -8)          # coupure de journal collée sur le filigrane (coin haut droit)
        if sh["kind"] == "card":
            z = sh["push"][0] + (sh["push"][1] - sh["push"][0]) * u
            paste(img, card_panel(), W / 2, H / 2 - 40, z, -1.5)
            for j, (tx, ty, ta) in enumerate(((190, 420, -32), (890, 420, 30), (190, 1450, 28), (890, 1450, -30))):
                paste(img, CARD_TAPES[j], W / 2 + (tx - W / 2) * z, H / 2 + (ty - H / 2) * z, 1.0, ta)
            for j, (im, cx, cy, t) in enumerate(big):
                s_ = pop(f, fr(t))
                if s_ is None: continue
                if j == 1:                                                  # bande or sous « MÉLENCHON »
                    bd = card_band(int(im.shape[1] * 1.04), int(im.shape[0] * 0.86), 77)
                    paste(img, bd, W / 2 + (cx - W / 2) * z, H / 2 + (cy + 2 - H / 2) * z, s_ * z, 1.2)
                paste(img, im, W / 2 + (cx - W / 2) * z, H / 2 + (cy - H / 2) * z, s_ * z)
        else:
            draw_pieces(img, txt, f, boil=sh["id"])
        if sh.get("flash") and i < 3: img = img + (1 - img) * [1.0, 0.6, 0.25][i]
        frames.append(finish(img, f))
    write_mov(frames, OUT + sh["clip"])
    print("  %-4s %3d im  (%s)" % (sh["id"], n, sh["kind"]))
def decoupes():
    """Contrôle des découpes en pleine résolution : 1re, milieu et dernière image de chaque plan découpé, sur gris,
    avec le cadre 9:16 (bords de la zone découpée en rouge s'ils tombent dans le champ)."""
    os.makedirs(CACHE + "decoupes", exist_ok=True)
    for sh in SHOTS:
        if sh["kind"] != "cut": continue
        n = sh["n"]; raw = read_frames_f(sh["src"], sh["f0"], n) if sh.get("f0") is not None else read_frames(sh["src"], sh["t"], n)
        ms = masks("%s_%s_%.3f_%d_%s" % (sh["id"], sh["src"], sh["t"], n, "-".join(map(str, sh["box"]))), raw, sh["box"], sh["pt"]); sh["yb"] = bottom_row(ms)
        if sh.get("lift"): ms = [bas_dechire(m, seed=skey(sh["id"])) for m in ms]
        cs = [controle(m) for m in ms]; agg = {k: max(c[k] for c in cs) for k in cs[0]}
        sc, ccx, ccy = cut_geom(sh, 0.0); bw_, bh_ = (sh["box"][2] - sh["box"][0]) * sc, (sh["box"][3] - sh["box"][1]) * sc
        edges = {"gauche": ccx - bw_ / 2 <= 0, "droite": ccx + bw_ / 2 >= W, "haut": ccy - bh_ / 2 <= 0}
        bad = [k for k in edges if agg[k] > 0 and not edges[k]]
        print("  %-4s controle (max sur le plan) %s  bas posé ligne %d/%d  bords touchés hors champ : %s  -> %s" % (sh["id"], agg, sh["yb"],
              sh["box"][3] - sh["box"][1], [k for k in edges if agg[k] > 0 and edges[k]], "OK" if not bad and agg["morceaux"] == 1 else "A ECARTER %s" % bad))
        planche(raw, ms, sh["box"], CACHE + "decoupes/%s-planche.jpg" % sh["id"])
        x0, y0, x1, y1 = sh["box"]; tiles = []
        for i in (0, n // 2, n - 1):
            img = np.ones((H, W, 3), np.float32) * 0.5; sc, ccx, ccy = cut_geom(sh, i / max(n - 1, 1))
            paste(img, np.dstack([raw[i][y0:y1, x0:x1], ms[i]]), ccx, ccy, sc)
            bx0, bx1 = ccx - (x1 - x0) * sc / 2, ccx + (x1 - x0) * sc / 2; by0 = ccy - (y1 - y0) * sc / 2
            for xx in (bx0, bx1):
                if 0 < xx < W: cv2.line(img, (int(xx), 0), (int(xx), H), (0, 0, 1), 3)
            if by0 > 0: cv2.line(img, (0, int(by0)), (W, int(by0)), (0, 0, 1), 3)
            tiles.append(img)
        cv2.imwrite(CACHE + "decoupes/%s.jpg" % sh["id"], (np.hstack(tiles) * 255).astype(np.uint8))


# ---------------- audio ----------------
def make_audio():
    import soundfile as sf
    sr = 48000; N = int(round(END * sr))
    def grab(path, t, dur):
        p = subprocess.run([FF, "-v", "error", "-ss", "%.3f" % t, "-t", "%.3f" % dur, "-i", path, "-ac", "2", "-ar", str(sr), "-f", "f32le", "-"], capture_output=True)
        return np.frombuffer(p.stdout, np.float32).reshape(-1, 2).copy()
    voix = np.zeros((N, 2), np.float32); mus = np.zeros((N, 2), np.float32)
    v = grab(HG + "/" + SRC["MO"][0], V_IN, V_OUT - V_IN); tv = np.arange(len(v)) / sr + V_IN
    env = np.interp(tv, [V_IN, V_IN + 0.03, V_END, V_OUT], [0, 1, 1, 0]).astype(np.float32)   # clameur après « possible » en fondu
    i0 = int(round(t_of_src(V_IN) * sr)); voix[i0:i0 + len(v)] = v * env[:, None] * 10 ** (3 / 20)
    m = music_raw(MUSIC_IN, END + 0.1)[:N]
    t = np.arange(len(m)) / sr; up = 48.90 - MUSIC_IN; vend = t_of_src(V_END); dr = DROP
    # sous la phrase : -19 dB (fin du couplet), montée sur « and the message… » (-19 -> -8 dB), plein sur le riff
    gdb = np.interp(t, [0, 0.25, up, vend, dr - 0.03, dr, END], [-26, -19, -19, -8, -6, 0, 0])
    k = int(0.30 * sr); fo = np.ones(len(m), np.float32); fo[-k:] = np.linspace(1, 0, k)
    mus[:len(m)] = m * (10 ** (gdb / 20) * fo)[:, None]
    sf.write(OUT + "R8-voix.wav", voix, sr, subtype="PCM_24"); sf.write(OUT + "R8-musique.wav", mus, sr, subtype="PCM_24")
    sf.write(D + "tmp_mix.wav", voix + mus, sr, subtype="FLOAT")
    r = subprocess.run([FF, "-hide_banner", "-i", D + "tmp_mix.wav", "-af", "loudnorm=I=-14:TP=-2.5:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    js = json.loads(r[r.rindex("{"):r.rindex("}") + 1])
    af = ("loudnorm=I=-14:TP=-2.5:LRA=11:measured_I=%s:measured_TP=%s:measured_LRA=%s:measured_thresh=%s:offset=%s:linear=true,"
          "aresample=48000" % (js["input_i"], js["input_tp"], js["input_lra"], js["input_thresh"], js["target_offset"]))
    subprocess.run([FF, "-v", "error", "-y", "-i", D + "tmp_mix.wav", "-af", af, "-c:a", "pcm_s24le", OUT + "R8-mix.wav"], check=True)
    os.remove(D + "tmp_mix.wav"); print("audio : mix avant normalisation", js["input_i"], "LUFS")

# ---------------- plan ----------------
PHRASE = "Un autre monde est nécessaire, et parce qu'il est nécessaire, alors nous allons le rendre possible."
def build_plan():
    video = []
    for sh in SHOTS:
        v = {"id": sh["id"], "clip": sh["clip"], "folder": "genR8", "path": OUT + sh["clip"], "s": 0, "e": sh["n"], "rec": sh["a"], "dur": sh["n"],
             "clip_fps": FPS, "speed_pct": 100, "track": 1, "note": sh["why"], "kind": sh["kind"], "temps": round(sh["n"] / FPS / T, 2)}
        if sh.get("src"):
            path, sfps, url, off, ctx = SRC[sh["src"]]
            v["source"] = {"fichier": path, "in_s": round(sh["t"], 3), "out_s": round(sh["t"] + sh["n"] / FPS, 3), "fps": sfps,
                           "url": url, "t_youtube_s": round(off + sh["t"], 2), "contexte": ctx, "synchro_voix": bool(sh.get("sync"))}
        if sh.get("photos"):
            v["coupures"] = [{"fichier": SRC[p[0]][0], "in_s": p[1], "out_s": round(p[1] + sh["n"] / FPS, 3), "cadre_source": p[2],
                              "url": SRC[p[0]][2], "t_youtube_s": round(SRC[p[0]][3] + p[1], 2), "bichromie": p[7]} for p in sh["photos"]]
        video.append(v)
    texts = []
    for sh in SHOTS:
        for line in sh.get("txt", []): texts.append({"plan": sh["id"], "texte": " ".join(w for w, _ in line)})
        for s_, t_, c_ in sh.get("big", []): texts.append({"plan": sh["id"], "texte": s_})
    plan = {"name": "R8 - Collage ransom-note - Jean-Luc Mélenchon (The White Stripes - Seven Nation Army)", "fps": FPS, "w": W, "h": H, "duree_s": round(fr(END) / FPS, 3),
            "note": "Plans ProRes 9:16 composés en Python (lot7/_claude/gen/R8/out) : fonds marine / or / pages de journal crème ou marine, "
                    "Mélenchon détouré (segment/Vision) en N&B encre marine + écho or décalé, coupures de foule vivantes en bichromie (scotch, bords déchirés), "
                    "pleins cadres en trichromie marine-or-crème, textes ransom-note cuits. s/e en images du clip (30 i/s), rec en images timeline. "
                    "Coupes sur les grosses caisses réelles de Seven Nation Army (son.json). Aucun ralenti. Générateur : lot7/_claude/gen/R8/genR8.py",
            "phrase": {"texte": PHRASE, "url": SRC["MO"][2], "source": SRC["MO"][0], "in_s": 12.78, "out_s": 19.66,
                       "t_youtube_s": [round(3214.0 + 12.78, 2), round(3214.0 + 19.66, 2)], "timeline_s": [round(t_of_src(12.78), 2), round(t_of_src(19.66), 2)],
                       "avant": "« …loin d'être inerte et résigné, nous sommes venus dire de toutes nos forces : »",
                       "voix": "son direct synchro (A1a-A1b de face au pupitre, A2a-A2b plan serré bras levés après la coupe caméra d'origine) ; "
                               "phrase entière, clameur de la place en fondu jusqu'au drop"},
            "musique": {"fichier": "lot7/sons/R8-whitestripes-seven-nation-army_complet.wav", "titre": "The White Stripes - Seven Nation Army", "url": SON_URL,
                        "debut_complet_s": round(MUSIC_IN, 4), "fin_complet_s": round(MUSIC_IN + fr(END) / FPS, 3), "drop_timeline_s": round(DROP, 4),
                        "coupes_s": [round(c, 4) for c in CUTS], "coupes_images": CUTF},
            "textes": texts, "video": video,
            "audio": [{"id": "mix", "clip": "R8-mix.wav", "folder": "genR8", "path": OUT + "R8-mix.wav", "rec": 0, "track": 1,
                       "note": "mix -14 LUFS : voix MO %.2f-%.2f s (+3 dB, fondu de la clameur %.2f-%.2f) à %.2f s ; Seven Nation Army dès %.3f s du complet, -19 dB sous la voix, montée sur « and the message… », plein au drop, fondu de fin 0,3 s"
                               % (V_IN, V_OUT, V_END, V_OUT, t_of_src(V_IN), MUSIC_IN)}],
            "stems": ["lot7/_claude/gen/R8/out/R8-voix.wav", "lot7/_claude/gen/R8/out/R8-musique.wav"],
            "logos_exclus": "filigrane « L'UNION POPULAIRE » (haut droite, x > 1600) hors des cadres photo et des détourages ; affiches des pupitres sous les découpes ; décor « L'UNION POPULAIRE » du soir du 1er tour retiré par le détourage"}
    json.dump(plan, open(D + "plan-R8.json", "w"), indent=1, ensure_ascii=False)
    son = {"id": "R8", "titre": "Seven Nation Army", "artiste": "The White Stripes", "url": SON_URL,
           "chaine": "The White Stripes (officielle, certifiée, « The White Stripes - Seven Nation Army (Official Music Video) »)",
           "fichier": "lot7/sons/R8-whitestripes-seven-nation-army_complet.wav",
           "extrait_complet_s": {"debut": round(MUSIC_IN, 4), "fin": round(MUSIC_IN + fr(END) / FPS, 3)},
           "paroles_audibles": "sous la phrase (baissé) : fin du couplet 1 puis « And the message coming from my eyes… » ; au drop : le riff saturé instrumental jusqu'à la fin",
           "bpm": round(60 / T, 1), "temps_s": T,
           "drop": {"complet_s": MDROP, "timeline_s": round(DROP, 4), "nature": "entrée du riff saturé (grosse caisse + crash) après « leave it alone »"},
           "frappes_timeline_s": [round(b, 4) for b in BEATS if 0 <= b <= END],
           "coupes_sur_frappes_s": [round(c, 4) for c in CUTS],
           "coupes_nature": ["grosse caisse"] * 3 + ["drop : grosse caisse + riff"] + ["grosse caisse (riff)"] * 9,
           "mix": "lot7/_claude/gen/R8/out/R8-mix.wav"}
    json.dump(son, open(D + "son.json", "w"), indent=1, ensure_ascii=False)

# ---------------- aperçu 540x960 ----------------
def apercu():
    plan = json.load(open(D + "plan-R8.json")); ins = []; fl = []
    for i, v in enumerate(plan["video"]):
        ins += ["-i", OUT + v["clip"]]
        fl.append("[%d:v]trim=start_frame=%d:end_frame=%d,setpts=PTS-STARTPTS,scale=540:960,setsar=1[v%d]" % (i, v["s"], v["e"], i))
    k = len(plan["video"]); fl.append("".join("[v%d]" % i for i in range(k)) + "concat=n=%d:v=1:a=0[v]" % k)
    ins += ["-i", OUT + "R8-mix.wav"]; out = HG + "/preview/apercu-R8.mp4"
    subprocess.run([FF, "-v", "error", "-y"] + ins + ["-filter_complex", ";".join(fl), "-map", "[v]", "-map", "%d:a" % k,
                    "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "aac", "-b:a", "192k", "-shortest", out], check=True)
    print("aperçu", out)
# ---------------- mesure sur l'export : coupes vs frappes, LUFS / TP ----------------
def mesure():
    """Coupes détectées sur l'export ; décalage audio de l'export (AAC) par corrélation avec le mix ;
    frappes réelles (grosse caisse) mesurées dans le morceau au même calage que le stem musique."""
    import soundfile as sf
    out = HG + "/preview/apercu-R8.mp4"
    r = subprocess.run([FF, "-v", "info", "-i", out, "-vf", "scale=135:240,select='gt(scene,0.2)',showinfo", "-an", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    cuts = [float(x) for x in re.findall(r"pts_time:([0-9.]+)", r)]
    p = subprocess.run([FF, "-v", "error", "-i", out, "-vn", "-ac", "1", "-ar", "48000", "-f", "f32le", "-"], capture_output=True)
    ye = np.frombuffer(p.stdout, np.float32)
    ymx, _ = sf.read(OUT + "R8-mix.wav", dtype="float32"); ymx = ymx.mean(1)
    n = min(len(ye), len(ymx)); A = np.fft.rfft(ye[:n], 2 * n); B = np.fft.rfft(ymx[:n], 2 * n)
    xc = np.fft.irfft(A * np.conj(B)); lags = np.r_[0:2000, -2000:0]; lag = lags[np.argmax(np.r_[xc[:2000], xc[-2000:]])] / 48000
    h = [x[0] for x in detect_hits(music_raw(MUSIC_IN, END + 0.2)) if x[1] == "kick" and x[2] > 0.15]
    print("décalage audio export / mix : %+.1f ms" % (lag * 1000))
    print("coupes image détectées (export) :", cuts)
    worst = 0
    for j, c in enumerate([fr_ / FPS for fr_ in CUTF]):
        det = min(cuts, key=lambda x: abs(x - c)) if cuts else None
        k = kick_onset(CUT_M[j]) - MUSIC_IN + lag                           # attaque de la grosse caisse mesurée (enveloppe < 120 Hz)
        e = ((det if det is not None and abs(det - c) < 0.1 else c) - k) * 1000; worst = max(worst, abs(e))
        print("  coupe %.3f (détectée %s)  grosse caisse %.4f  écart %+.1f ms" % (c, "%.3f" % det if det is not None else "-", k, e))
    print("écart max coupes/frappes : %.1f ms" % worst)
    r = subprocess.run([FF, "-hide_banner", "-i", out, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    print(r[r.rindex("Summary"):])
if __name__ == "__main__":
    args = set(a for a in sys.argv[1:] if not a.startswith("only=")) or {"shots", "audio", "plan", "apercu"}
    only = [x for a in sys.argv[1:] if a.startswith("only=") for x in a.split("=", 1)[1].split(",")]
    print("musique dès %.4f s ; V_SRC0 %.3f ; coupes (s) :" % (MUSIC_IN, V_SRC0), [round(c, 3) for c in CUTS], "images :", CUTF, "fin", fr(END))
    if "decoupes" in args: decoupes()
    if "shots" in args or only:
        for sh in SHOTS:
            if not only or sh["id"] in only: render(sh)
    if "audio" in args: make_audio()
    if "plan" in args: build_plan()
    if "apercu" in args: apercu()
    if "mesure" in args: mesure()
