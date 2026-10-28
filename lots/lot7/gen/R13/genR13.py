# R13 (lot 7) — Collage ransom-note « affiche de meeting découpée », Jean-Luc Mélenchon, son Black Eyed Peas – Pump It.
# Modèle : lot6/_claude/gen/R2/genR2.py (validé, même figure, chiffres) — mêmes fonctions (découpe Vision, morceaux de texte penchés
#   serif/sans, photos vivantes scotchées, bandes déchirées, frappes, carton final), poussé vers l'affiche de meeting :
#   papier d'affiche crème à trame orange, chiffres en lettres découpées très grandes, bandes d'affiche déchirées, plis de colle,
#   figure en bichromie bleu nuit -> crème (cravate passée en orange), écho orange / bleu nuit décalé, plein cadre bleu nuit -> orange -> crème.
# Palette R13 (brief) : orange #FF6B1A + bleu nuit #101B3D (+ crème d'affiche). Aucun rouge, aucun vert, aucun papier journal.
# Phrase (son direct, synchro) : « 8 millions de pauvres à l'aide alimentaire, 3 000 personnes à la rue, 11 millions de pauvres que
#   comptent les statistiques officielles, telle est la France dorénavant. » (Convention municipales LFI, 23/11/2025, chaîne
#   JEAN-LUC MÉLENCHON, youtu.be/Yc46p2zQZxY 802,4-814,0 s) -> autre phrase que C3 (longue marche) et les autres edits Mélenchon.
# Son : Pump It (piste officielle « Provided to YouTube by Universal Music Group », chaîne Black Eyed Peas) : sous la phrase, le break
#   riff sans basse (143,0-148,4 s) raccordé sur une mesure à l'intro riff (0-6,88 s) ; drop = entrée du beat de l'intro (kick 6,879 s).
# Usage : python genR13.py [shots] [audio] [plan] [apercu] [mesure] [only=ID,ID]   (sans argument = tout sauf mesure)
import sys
sys.dont_write_bytecode = True
import os, json, subprocess, re
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
HG = "/Users/luca.grousset/Movies/highkey-gauchiste"
D = HG + "/lot7/_claude/gen/R13/"; OUT = D + "out/"; CACHE = D + "cache/"; os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, D)
from hits import detect_hits
sys.path.insert(0, HG + "/_claude/outils")
from decoupe import masques as decoupe_masques, controle, planche   # outil partagé obligatoire (Luca 27/10) : rien que la personne
FF = "/opt/homebrew/bin/ffmpeg"; SEG = HG + "/_claude/outils/segment"; FPS = 30; W, H = 1080, 1920
def fr(t): return int(round(t * FPS))
def hexc(h): h = h.lstrip("#"); return np.array([int(h[4:6], 16), int(h[2:4], 16), int(h[0:2], 16)], np.float32) / 255   # BGR
def rgb(h): h = h.lstrip("#"); return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
ORANGE, ORANGE2, NAVY, NAVY2, INK, CREAM, CREAMD = "#FF6B1A", "#E2520E", "#101B3D", "#22356E", "#0A1024", "#F3EBDC", "#DCCFB8"

# ---------------- sources (lecture seule) ----------------
URL = "https://www.youtube.com/watch?v=Yc46p2zQZxY"
CTX = "Convention pour les municipales 2026, 23/11/2025 (chaîne JEAN-LUC MÉLENCHON)"
SRC = {
    "PV": ("lot7/sources/R13-melenchon-convention-pauvres.mp4", 60.0, URL, 790.0, CTX + ", extrait 790-840 s"),
    "OUV": ("lot7/sources/R13-melenchon-convention-ouverture.mp4", 60.0, URL, 0.0, CTX + ", ouverture 0-45 s"),
    "APL": ("lot7/sources/R13-melenchon-convention-applaudissements.mp4", 60.0, URL, 1250.0, CTX + ", applaudissements 1250-1275 s"),
}
CAM_CUT = 18.05                       # PV : plan de dos dans la salle (11,02-18,05) -> gros plan pupitre (18,05-42,73)

# ---------------- musique : Black Eyed Peas – Pump It ----------------
SON_FILE = HG + "/lot7/sons/R13-bep-pump-it_complet.wav"; SON_URL = "https://www.youtube.com/watch?v=_lCXWaTxpXI"
BAR = 1.56221; T = BAR / 4            # 153,6 BPM (kicks du beat 6,879 -> 150,603 s)
MDROP = 6.8791                        # entrée du beat sous le riff de l'intro (kick, le moment des edits TikTok)
I0 = MDROP - 4 * BAR                  # début de la 1re mesure de l'intro (0,630 s) ; 0-0,63 = levée du riff
B_END = 150.6025 - BAR - I0           # break sans basse : on le quitte une levée avant la mesure 149,04 s -> intro 0,0 s
def song_raw(t0, dur, sr=48000):
    import soundfile as sf
    i0 = int(round(t0 * sr)); x, r = sf.read(SON_FILE, start=i0, frames=int(round(dur * sr)), dtype="float32"); assert r == sr; return x
# coupes : (segment, temps dans le morceau) ; b = break 143-148,4 s, i = intro et suite (drop 6,879)
CUT_SONG = [("b", 146.1925), ("b", 148.0278), ("i", 2.4142), ("i", 3.7611), ("i", MDROP),
            ("i", 7.6146), ("i", 8.4413), ("i", 9.2799), ("i", 10.0024), ("i", 10.6167), ("i", 11.5655), ("i", 12.5592)]
DROP_NOM = 12.25
def tl_cuts(L1): return [(h - B_END + L1) if s == "b" else (h + L1) for s, h in CUT_SONG]
def best_L1():
    best, bad = 0.0, 9
    for off in np.arange(-0.016, 0.0165, 0.001):
        L1 = DROP_NOM - MDROP + off; e = max(abs(c - fr(c) / FPS) for c in tl_cuts(L1))
        if e < bad: best, bad = L1, e
    return best
L1 = best_L1()                        # durée du break dans la timeline (la levée de l'intro arrive à L1)
B_IN = B_END - L1
CUTS = tl_cuts(L1); CUTF = [fr(c) for c in CUTS]
DROP = CUTS[4]; DROPF = CUTF[4]
END = 19.85
BEATS = [DROP + k * T for k in range(-31, 21)]; BEATF = [fr(b) for b in BEATS]
def nbeat(f): return sum(1 for b in BEATF if b <= f)
def music_stem(dur, sr=48000):
    """Break (B_IN -> B_END) puis intro (0 -> …), raccord sur la mesure, fondu enchaîné 8 ms."""
    a = song_raw(B_IN, L1 + 0.008); b = song_raw(0.0, dur - L1 + 0.01)
    n = int(round(L1 * sr)); k = int(0.008 * sr)
    out = np.zeros((int(round(dur * sr)), 2), np.float32); out[:n] = a[:n]
    xf = np.linspace(0, 1, k, dtype=np.float32)[:, None]
    out[n:n + k] = a[n:n + k] * (1 - xf) + b[:k] * xf
    m = min(len(out) - n - k, len(b) - k); out[n + k:n + k + m] = b[k:k + m]
    return out

# ---------------- voix ----------------
V_SRC0 = 12.05                        # timeline t <-> source PV t + 12,05
V_IN, V_OUT = 12.28, 24.25            # « 8 » (12,36) … « dorénavant » (fin 23,98, souffle jusqu'à 24,2) ; « Dans les villes… » (24,95) non gardé
def t_of_src(s): return s - V_SRC0
WORDS = [("8", 12.36), ("MILLIONS", 13.04), ("DE", 13.38), ("PAUVRES", 13.62), ("À", 14.08), ("L'AIDE", 14.20), ("ALIMENTAIRE", 14.40),
         ("3 000", 15.88), ("PERSONNES", 16.38), ("À", 16.88), ("LA", 17.08), ("RUE", 17.18),
         ("11", 18.30), ("MILLIONS", 18.64), ("DE", 19.06), ("PAUVRES", 19.34), ("QUE", 19.88), ("COMPTENT", 20.22), ("LES", 20.58),
         ("STATISTIQUES", 20.70), ("OFFICIELLES", 21.38), ("TELLE", 22.28), ("EST", 22.76), ("LA", 22.78), ("FRANCE", 22.90), ("DORÉNAVANT", 23.28)]
def wt(i): return t_of_src(WORDS[i][1])
assert t_of_src(23.98) < DROP - 0.25, ("la phrase déborde sur le drop", t_of_src(23.98), DROP)

# ---------------- polices ransom-note (affiche : beaucoup de condensées) ----------------
S = "/System/Library/Fonts/Supplemental/"
FONTS = [(S + "Arial Black.ttf", 0), (S + "Georgia Bold.ttf", 0), (S + "Impact.ttf", 0), (S + "DIN Condensed Bold.ttf", 0),
         (S + "Rockwell.ttc", 2), (S + "Didot.ttc", 2), (S + "Bodoni 72.ttc", 2), (S + "Futura.ttc", 4), (S + "BigCaslon.ttf", 0),
         (S + "Copperplate.ttc", 1), (S + "Courier New Bold.ttf", 0), ("/System/Library/Fonts/Avenir Next Condensed.ttc", 8)]
FCOND = (S + "Futura.ttc", 4)
FIMP = (S + "Impact.ttf", 0)
TEX = "TEX"                           # morceau découpé dans l'affiche (papier crème à trame orange)
STYLES = [(rgb(CREAM), rgb(NAVY)), (rgb(NAVY), rgb(CREAM)), (rgb(ORANGE), rgb(NAVY)), (rgb(NAVY), rgb(ORANGE)),
          (rgb(CREAM), rgb(ORANGE2)), (rgb(ORANGE), rgb(CREAM)), (TEX, rgb(NAVY)), (rgb(INK), rgb(ORANGE))]
_fc = {}
def font(spec, size):
    k = (spec, size)
    if k not in _fc: _fc[k] = ImageFont.truetype(spec[0], size, index=spec[1])
    return _fc[k]

# ---------------- papier d'affiche ----------------
_post = {}
def poster_texture(w, h, seed, base=CREAM, dots=ORANGE, band=True):
    """Papier d'affiche collé : crème, fibres, plis de colle, trame orange en dégradé (gros points), aucune lettre."""
    k = (w, h, seed, base, dots, band)
    if k in _post: return _post[k].copy()
    rng = np.random.default_rng(seed)
    n = cv2.resize(rng.standard_normal((max(2, h // 40), max(2, w // 40))).astype(np.float32), (w, h), interpolation=cv2.INTER_CUBIC)
    n2 = cv2.GaussianBlur(rng.standard_normal((h, w)).astype(np.float32), (0, 0), 1.1)
    img = np.clip(hexc(base)[None, None, :] * (1 + 0.035 * n[..., None] + 0.03 * n2[..., None]), 0, 1).astype(np.float32)
    if band:                                                                 # trame : points qui grossissent en diagonale
        y, x = np.mgrid[0:h, 0:w].astype(np.float32); step = 22
        g = np.clip(((x / w) * 0.35 + (y / h) * 0.85 - 0.35 + rng.uniform(-0.1, 0.1)) * 1.4, 0, 1)
        cell_x = (x % step) - step / 2; cell_y = (y % step) - step / 2
        r = g * step * 0.42; dm = np.clip(r - np.sqrt(cell_x ** 2 + cell_y ** 2) + 0.5, 0, 1)[..., None] * 0.55
        img = img * (1 - dm) + hexc(dots)[None, None, :] * dm
    wr = np.zeros((h, w), np.float32)                                        # plis de colle (filets clairs/sombres)
    for _ in range(4):
        x0 = rng.uniform(-0.2, 1.2) * w; ang = rng.uniform(-0.5, 0.5)
        cv2.line(wr, (int(x0), 0), (int(x0 + np.tan(ang) * h), h), float(rng.choice([-1, 1])), 2, cv2.LINE_AA)
    img = np.clip(img + cv2.GaussianBlur(wr, (0, 0), 2.0)[..., None] * 0.05, 0, 1)
    _post[k] = img.astype(np.float32)
    return _post[k].copy()
TEX_PIL = None
def tex_pil():
    global TEX_PIL
    if TEX_PIL is None:
        t = poster_texture(900, 420, 7); TEX_PIL = Image.fromarray((t[..., ::-1] * 255).astype(np.uint8))
    return TEX_PIL

def chip(txt, h, rng, fspec=None, style=None, rot=None, styles=None):
    """Un morceau découpé : rectangle irrégulier (uni ou papier d'affiche) + texte, RGBA PIL, légèrement penché."""
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
NUM = ("8", "3 000", "11")            # chiffres : lettres découpées une par une, très grands
LETTERS = NUM + ("MILLIONS", "DORÉNAVANT")
def board(lines, y0, seed, h=112, maxw=XMAX - XMIN - 30, bg=None):
    """lines = [[(mot, t_apparition), …], …] -> liste de pièces placées (img, cx, cy, t). Pas de puce de la couleur du fond."""
    rng = np.random.default_rng(seed); pieces = []; y = y0
    clash = {ORANGE: (rgb(ORANGE),), NAVY: (rgb(NAVY), rgb(INK)), "POSTER": (TEX, rgb(CREAM)), "ON": (rgb(ORANGE), rgb(NAVY), rgb(INK))}.get(bg, ())
    styles = [st for st in STYLES if st[0] not in clash]
    for line in lines:
        hs = [h * (1.75 if w in NUM else 1.0) for w, _ in line]
        imgs = [shadowed(word_img(w, hh, rng, w in LETTERS, styles)) for (w, _), hh in zip(line, hs)]
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
    """Texte propre (carton final / gros mot plein cadre) : lignes centrées, largeur max, retour [(img, cx, cy, t)]."""
    pieces = []; y = y0
    for k, (txt, t, col) in enumerate(lines):
        size = (sizes or [300] * len(lines))[k]; f = font(spec, size)
        while f.getlength(txt) > maxw - 2 * contour - 44: size -= 4; f = font(spec, size)
        x0, y0b, x1, y1 = f.getbbox(txt)
        im = Image.new("RGBA", (x1 - x0 + 2 * contour + 24, y1 - y0b + 2 * contour + 24), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.text((12 + contour - x0, 12 + contour - y0b), txt, font=f, fill=tuple(col) + (255,), stroke_width=contour, stroke_fill=rgb(INK) + (255,))
        a = shadowed(im) if contour else np.dstack([np.asarray(im)[..., :3][..., ::-1], np.asarray(im)[..., 3]]).astype(np.float32) / 255
        pieces.append((a, W / 2, y + a.shape[0] / 2, t)); y += a.shape[0] + gap
    for im, cx, cy, t in pieces:
        assert XMIN - 2 <= cx - im.shape[1] / 2 and YMIN - 2 <= cy - im.shape[0] / 2 and cy + im.shape[0] / 2 <= YMAX + 2, ("hors zone", cy, im.shape)
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
_tex = {}
def paper(col):
    if col not in _tex:
        rng = np.random.default_rng(len(_tex) + 3)
        n = cv2.resize(rng.standard_normal((48, 27)).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC)
        n2 = cv2.GaussianBlur(rng.standard_normal((H, W)).astype(np.float32), (0, 0), 1.2)
        _tex[col] = np.clip(hexc(col)[None, None, :] * (1 + 0.04 * n[..., None] + 0.04 * n2[..., None]), 0, 1).astype(np.float32)
        m = np.zeros((H, W), np.float32)                                    # plis de colle de l'affiche
        cv2.line(m, (0, int(H * 0.62)), (W, int(H * 0.48)), 1.0, 2, cv2.LINE_AA); cv2.line(m, (int(W * 0.3), 0), (int(W * 0.42), H), 0.7, 2, cv2.LINE_AA)
        m = cv2.GaussianBlur(m, (0, 0), 1.5) * 0.10; _tex[col] = np.clip(_tex[col] + m[..., None], 0, 1)
    return _tex[col].copy()
def background(bg, key):
    return poster_texture(W, H, 100 + key) if bg == "POSTER" else paper(bg)
VIG = None
def finish(img, f):
    global VIG
    if VIG is None:
        y, x = np.mgrid[0:H, 0:W].astype(np.float32)
        r = np.sqrt(((x - W / 2) / (W / 2)) ** 2 + ((y - H / 2) / (H / 2)) ** 2) / np.sqrt(2)
        VIG = (1 - 0.24 * np.clip(r, 0, 1) ** 2.4)[..., None].astype(np.float32)
    g = np.random.default_rng(1000 + f).standard_normal((H // 2, W // 2)).astype(np.float32)
    g = cv2.resize(g, (W, H), interpolation=cv2.INTER_LINEAR)[..., None] * 0.026
    return np.clip(img * VIG + g, 0, 1)

# ---------------- lecture source ----------------
def read_frames(src, t, n_out, tmin=None, tmax=None):
    """n_out images à 30 i/s depuis t ; temps bornés à [tmin, tmax] (gel d'image avant/après une coupe caméra de la source)."""
    path, sfps = SRC[src][0], SRC[src][1]
    ts = [t + i / FPS for i in range(n_out)]
    if tmin is not None: ts = [max(x, tmin) for x in ts]
    if tmax is not None: ts = [min(x, tmax) for x in ts]
    t0 = min(ts); need = [int(round((x - t0) * sfps)) for x in ts]
    p = subprocess.run([FF, "-v", "error", "-ss", "%.4f" % t0, "-i", HG + "/" + path, "-frames:v", str(max(need) + 1),
                        "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True)
    a = np.frombuffer(p.stdout, np.uint8).reshape(-1, 1080, 1920, 3)
    return [a[min(i, len(a) - 1)].astype(np.float32) / 255 for i in need]
def masks(key, frames, box, k=13):
    x0, y0, x1, y1 = box; d = CACHE + "seg/" + key; di, dm = d + "/in", d + "/m"
    if not (os.path.isdir(dm) and len(os.listdir(dm)) >= len(frames)):
        os.makedirs(di, exist_ok=True)
        for i, fr_ in enumerate(frames): cv2.imwrite("%s/f%04d.png" % (di, i), (fr_[y0:y1, x0:x1] * 255).astype(np.uint8))
        subprocess.run([SEG, di, dm], check=True, capture_output=True)
    out = []
    for i in range(len(frames)):
        m = cv2.imread("%s/f%04d.png" % (dm, i), 0).astype(np.float32) / 255
        m = cv2.morphologyEx(m, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))   # tiges de micro retirées
        m = np.clip((cv2.GaussianBlur(m, (0, 0), 1.2) - 0.5) * 2.2 + 0.5, 0, 1)
        out.append(m)
    return out
def fill_fig(crop, m):
    """Micro et pied retirés par l'outil (trous / fentes dans le buste) : on bouche les trous fermés (bord bas compté comme fermé),
    on repeint l'image là où il n'y avait pas franchement la personne (inpainting) et on refait un alpha net -> silhouette pleine,
    sans micro ni pied visible, sans zone à moitié transparente (bras flou)."""
    t = (m > 0.5).astype(np.uint8); h, w = t.shape
    pad = np.zeros((h + 2, w + 2), np.uint8); pad[1:-1, 1:-1] = t; pad[-1, :] = 1
    ff = (1 - pad).copy(); mask = np.zeros((h + 4, w + 4), np.uint8)
    cv2.floodFill(ff, mask, (0, 0), 2)
    tf = (t | (ff[1:-1, 1:-1] == 1)).astype(np.uint8)
    inner = cv2.erode(tf, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (13, 13)))
    reg = ((inner > 0) & (m < 0.92)).astype(np.uint8)
    if reg.sum():
        reg = cv2.dilate(reg, np.ones((5, 5), np.uint8)) & tf
        u8 = (np.clip(crop, 0, 1) * 255).astype(np.uint8)
        crop = cv2.inpaint(u8, reg, 6, cv2.INPAINT_TELEA).astype(np.float32) / 255
    mf = np.clip((cv2.GaussianBlur(tf.astype(np.float32), (0, 0), 1.1) - 0.5) * 2.4 + 0.5, 0, 1)
    return crop, mf
LW = np.array([0.0722, 0.7152, 0.2126], np.float32)
def lum(x, p=99, gamma=0.85):
    L = x @ LW; L = L / max(float(np.percentile(L, p)), 0.2); return np.clip(L, 0, 1) ** gamma
def ramp(L, cols, k=None):
    k = np.linspace(0, 1, len(cols)).astype(np.float32) if k is None else np.array(k, np.float32)
    cs = np.stack([hexc(c) for c in cols]); return np.stack([np.interp(L, k, cs[:, c]) for c in range(3)], -1).astype(np.float32)
def fig_look(x):
    """Figure d'affiche : bichromie encre -> bleu nuit -> crème, contrastée ; la cravate rouge passe en orange."""
    hsv = cv2.cvtColor((np.clip(x, 0, 1) * 255).astype(np.uint8), cv2.COLOR_BGR2HSV).astype(np.float32)
    hh, ss, vv = hsv[..., 0], hsv[..., 1] / 255, hsv[..., 2] / 255
    m = (((hh < 9) | (hh > 168)) & (ss > 0.55) & (vv < 0.80) & (vv > 0.12)).astype(np.float32)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8)); m = cv2.GaussianBlur(m, (0, 0), 1.5)[..., None]
    L = lum(x); L = np.clip((L - 0.5) * 1.25 + 0.52, 0, 1)
    g = ramp(L, [INK, NAVY2, "#8E9AB8", CREAM], [0, 0.33, 0.66, 1.0])
    oo = np.clip(hexc(ORANGE)[None, None, :] * (0.6 + 0.7 * L[..., None]), 0, 1)
    return g * (1 - m) + oo * m
def photo_look(x):
    L = x @ LW; lo, hi = np.percentile(L, 1), np.percentile(L, 99.5); L = np.clip((L - lo) / max(hi - lo, 0.05), 0, 1) ** 0.75
    return ramp(L, [NAVY, "#7C88A8", CREAM], [0, 0.5, 1])
def duo(x): return ramp(lum(x, 99.5), [INK, NAVY2, ORANGE, CREAM], [0, 0.3, 0.68, 1.0])

# ---------------- collage poussé : déchirures, scotch, bandes d'affiche, couches qui sautent sur les frappes ----------------
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
    col = np.array([0.74, 0.86, 0.92], np.float32)[None, None, :] * (1 + 0.04 * rng.standard_normal((h, w, 1)).astype(np.float32))
    return np.dstack([col, m * 0.72]).astype(np.float32)
def halftone(h, w, col, dot, step=14, r=4):
    img = np.ones((h, w, 3), np.float32) * col[None, None, :]
    for y in range(0, h, step):
        for x in range((y // step % 2) * step // 2, w, step): cv2.circle(img, (x, y), r, tuple(float(v) for v in dot), -1, cv2.LINE_AA)
    return img
STRIP_KINDS = [(ORANGE, "plain"), ("POSTER", "tex"), (NAVY, "plain"), (ORANGE, "ht"), (CREAMD, "plain"), (NAVY2, "htnavy"), (CREAM, "plain"), (INK, "stripes")]
def strip_rgba(w, h, rng, colhex, kind):
    """Bande d'affiche déchirée : couleur pleine, trame, papier d'affiche ou rayures de meeting ; ombre portée."""
    if kind == "tex": body = poster_texture(w, h, int(rng.integers(1000)))
    elif kind == "ht": body = halftone(h, w, hexc(ORANGE), dot=tuple(hexc(NAVY)))
    elif kind == "htnavy": body = halftone(h, w, hexc(NAVY), dot=tuple(hexc(ORANGE)), step=16, r=5)
    elif kind == "stripes":
        body = np.ones((h, w, 3), np.float32) * hexc(NAVY)[None, None, :]
        for x in range(-h, w, 44): cv2.line(body, (x, h), (x + h, 0), tuple(float(v) for v in hexc(ORANGE)), 14, cv2.LINE_AA)
    else: body = np.ones((h, w, 3), np.float32) * hexc(colhex)[None, None, :]
    body = np.clip(body * (1 + 0.035 * cv2.GaussianBlur(rng.standard_normal((h, w)).astype(np.float32), (0, 0), 1.5))[..., None], 0, 1)
    m = torn_mask(h, w, rng, rough=10, step=12)
    out = np.zeros((h + 16, w + 16, 4), np.float32)
    out[10:10 + h, 8:8 + w, 3] = cv2.GaussianBlur(m, (0, 0), 3) * 0.45
    a = m[..., None]; out[:h, :w, :3] = body * a; out[:h, :w, 3] = np.maximum(m, out[:h, :w, 3])
    return out
def make_strips(sh):
    n = sh.get("strips", 0); rng = np.random.default_rng(skey(sh["id"]) + 5); out = []
    zones = [(150, 470), (930, 560), (540, 300), (120, 1250), (960, 1320), (230, 900), (880, 1050), (800, 220), (300, 1600), (540, 1720)]
    for k in range(n):
        w, h = int(rng.uniform(400, 720)), int(rng.uniform(90, 190))
        colhex, kind = STRIP_KINDS[(k + skey(sh["id"])) % len(STRIP_KINDS)]
        if colhex == sh.get("bg"): colhex, kind = STRIP_KINDS[(k + 3 + skey(sh["id"])) % len(STRIP_KINDS)]
        if colhex == sh.get("bg"): colhex, kind = CREAMD, "plain"
        cx, cy = zones[(k + skey(sh["id"])) % 3] if k < 3 else zones[(k * 3 + skey(sh["id"])) % len(zones)]
        out.append(dict(img=strip_rgba(w, h, rng, colhex, kind), cx=cx + rng.uniform(-60, 60), cy=cy + rng.uniform(-60, 60),
                        ang=rng.uniform(-28, 28), k=k))
    return out
class Photo:
    """Photo bichromie bleu nuit -> crème (vidéo vivante) : bord d'affiche déchiré, scotch, ombre ; elle saute sur chaque frappe."""
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
        c = cv2.resize(photo_look(self.frames[i][y0:y1, x0:x1]), (self.width, self.h), interpolation=cv2.INTER_AREA)
        hh, ww = self.h + 2 * b, self.width + 2 * b
        out = np.zeros((hh + 2 * M, ww + 2 * M, 4), np.float32); out[..., 3] = self.shadow
        body = np.ones((hh, ww, 3), np.float32) * hexc(CREAM); body[b:b + self.h, b:b + self.width] = c
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
    """Bords d'affiche déchirés (crème) en haut et en bas du plein cadre."""
    global TORN_EDGES
    if TORN_EDGES is None:
        rng = np.random.default_rng(11); out = np.zeros((H, W, 4), np.float32); tex = paper(CREAMD)
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
CLOSE = (250, 0, 1650, 1080)          # PV gros plan pupitre (logos « Convention municipales » haut gauche / LFI haut droite : fond détouré)
BACK = (440, 110, 1100, 1080)         # PV plan de dos : Mélenchon au pupitre + silhouettes, sans logo ni écran sous-titré
OUVF = (300, 0, 1560, 1080)           # OUV gros plan poing / bras levé
CROWD = (0, 400, 1300, 1080)          # OUV foule debout (41,3-45 s), sans l'écran haut droite
TEAM = (300, 160, 1700, 1080)         # OUV équipe qui applaudit sur scène (0-4 s), sous le logo
HALLB = (0, 640, 1920, 1080)          # PV salle vue de la scène (43-50 s), bas du cadre : foule, sans l'écran
WIDEB = (360, 740, 1560, 1080)        # OUV plan large (10,3-24,6 s) : bas du cadre (salle + militants sur scène), sans l'écran à texte
SILH = (0, 430, 1500, 1080)           # APL salle de dos en contre-jour (16,2-24,8 s) : silhouettes, sans l'écran
APLW = (0, 640, 1920, 1080)           # APL plan large (0-9,6 s) : bas du cadre, la salle
def B(lines, y, h=118, seed=None, t1=None, sync=True, bg=None): return dict(lines=lines, y=y, h=h, seed=seed, t1=t1, sync=sync, bg=bg)
W8 = lambda i0, i1: [(WORDS[i][0], wt(i)) for i in range(i0, i1)]
CARD1 = [[("8", 0.0), ("MILLIONS", 0.0)], [("DE", 0.0), ("PAUVRES", 0.0)], [("À", 0.0), ("L'AIDE", 0.0)], [("ALIMENTAIRE", 0.0)]]
CARD2 = [[("11", 0.0), ("MILLIONS", 0.0)], [("DE", 0.0), ("PAUVRES", 0.0)]]
CARD3 = [[("TELLE", 0.0), ("EST", 0.0)], [("LA", 0.0), ("FRANCE", 0.0)], [("DORÉNAVANT", 0.0)]]
SHOTS = [
    dict(id="A1", kind="collage", bg=NAVY, strips=6,
         photos=[dict(src="PV", t="sync", box=BACK, w=720, c=(540, 1300), a=-3, t0=0.0, tmax=CAM_CUT - 0.02)],
         txt=[B([W8(0, 2), W8(2, 4), W8(4, 6), W8(6, 7)], 250, bg=NAVY)],
         why="dans la salle, de dos (synchro) : Mélenchon au pupitre au loin, « 8 millions de pauvres à l'aide alimentaire », fond bleu nuit"),
    dict(id="A2", kind="collage", bg=ORANGE, strips=7,
         photos=[dict(src="PV", t="sync", box=BACK, w=640, c=(560, 1330), a=4, t0=0.0, tmax=CAM_CUT - 0.02),
                 dict(src="OUV", t=41.6, box=CROWD, w=520, c=(330, 1660), a=-6, t0=2 * T)],
         txt=[B([[(w, wt(8)) for w, _ in W8(9, 12)]], 300, h=150, bg=ORANGE)],
         why="même plan de dos synchro, fond orange : voix « 3 000 personnes à la rue », à l'écran seulement « À LA RUE » (chiffre douteux jamais affiché) + la foule de la convention (elle ne parle pas)"),
    dict(id="B1", kind="collage", bg="POSTER", strips=6,
         photos=[dict(src="OUV", t=0.3, box=TEAM, w=720, c=(540, 1120), a=-3, t0=0.0),
                 dict(src="PV", t=43.0, box=HALLB, w=560, c=(360, 1590), a=6, t0=2 * T),
                 dict(src="OUV", t=12.0, box=WIDEB, w=560, c=(760, 1730), a=-5, t0=4 * T)],
         txt=[B([W8(12, 14), W8(14, 16)], 255, bg="POSTER")],
         why="affiche crème à trame orange : l'équipe qui applaudit, la salle, les militants sur scène (il ne parle pas à l'image ; le gros plan de lecture des notes est écarté) : « 11 millions de pauvres »"),
    dict(id="B2", kind="cut", src="PV", t="sync", tmin=CAM_CUT + 0.02, bg=NAVY, box=CLOSE, pt=(0.436, 0.74), scale=(1.10, 1.13), cx=960, strips=5,
         txt=[B([W8(16, 18), W8(18, 20)], 265, h=112, bg=NAVY)],
         why="gros plan synchro, fond bleu nuit, écho orange : « que comptent les statistiques… »"),
    dict(id="B3", kind="collage", bg="POSTER", strips=6,
         photos=[dict(src="APL", t=17.0, box=SILH, w=720, c=(560, 1180), a=-3, t0=0.0),
                 dict(src="OUV", t=14.0, box=WIDEB, w=560, c=(370, 1620), a=6, t0=2 * T),
                 dict(src="PV", t=46.0, box=HALLB, w=520, c=(760, 1730), a=-5, t0=4 * T)],
         txt=[B([W8(20, 21), W8(21, 23), W8(23, 25), W8(25, 26)], 250, h=116, bg="POSTER")],
         why="collage d'affiche sur la fin de la phrase (il ne parle pas à l'image : la salle en contre-jour, les militants sur scène, la salle vue de la scène) : « …officielles, telle est la France dorénavant » ; le gros plan de la fin (tête baissée sur ses notes) est écarté"),
    dict(id="C1", kind="cut", src="OUV", t=25.45, bg=ORANGE, box=(300, 0, 1750, 1080), pt=(0.6, 0.79), scale=(1.08, 1.11), cx=980, white3=True, flash=True, strips=3,
         txt=[B(CARD1, 250, h=120, seed=1313, sync=False, bg="ON")],
         why="DROP (entrée du beat de Pump It) : flash 3 images, silhouette blanche puis Mélenchon bras levé vers la salle (ouverture, musique seule), fond orange"),
    dict(id="C2", kind="collage", bg=NAVY, strips=3,
         photos=[dict(src="APL", t=21.0, box=SILH, w=700, c=(400, 1060), a=-4, t0=0.0),
                 dict(src="OUV", t=18.0, box=WIDEB, w=620, c=(700, 1380), a=5, t0=T),
                 dict(src="PV", t=44.5, box=HALLB, w=660, c=(470, 1700), a=-3, t0=2 * T)],
         txt=[B([[(w, -1.0) for w, _ in l] for l in CARD1], 250, h=120, seed=1313, sync=False, bg="ON")],
         why="collage bleu nuit : la salle en contre-jour, les militants sur scène, la salle vue de la scène ; même carton qui reste"),
    dict(id="C3", kind="full", src="OUV", t=42.6, crop=(560, 760, 620), push=(1.0, 1.05), focus=(560, 760), flash=True,
         txt=[B(CARD2, 300, h=130, seed=2626, sync=False, bg="ON")],
         why="plein cadre bichromie : la foule debout, drapeaux, bords d'affiche déchirés ; carton « 11 millions de pauvres »"),
    dict(id="C4", kind="cut", src="PV", t=39.25, bg=NAVY, box=(150, 0, 1700, 1080), pt=(0.497, 0.79), scale=(1.04, 1.07), cx=920, strips=4,
         txt=[B([[(w, -1.0) for w, _ in l] for l in CARD2], 300, h=130, seed=2626, sync=False, bg="ON")],
         why="Mélenchon index pointé (même discours, 829 s, musique seule), écho orange ; même carton"),
    dict(id="C5", kind="collage", bg=ORANGE, strips=4,
         photos=[dict(src="OUV", t=3.2, box=TEAM, w=720, c=(540, 1000), a=3, t0=0.0),
                 dict(src="PV", t=48.0, box=HALLB, w=560, c=(380, 1400), a=-6, t0=T / 2),
                 dict(src="OUV", t=22.0, box=WIDEB, w=520, c=(740, 1700), a=5, t0=T)],
         txt=[B(CARD3, 255, h=120, seed=3939, sync=False, bg="ON")],
         why="collage orange : l'équipe qui applaudit, la salle, les militants sur scène ; carton « telle est la France dorénavant »"),
    dict(id="C6", kind="cut", src="PV", t=41.20, bg="POSTER", box=(150, 0, 1700, 1080), pt=(0.497, 0.79), scale=(1.06, 1.09), cx=920, white3=True, strips=4,
         txt=[B([[(w, -1.0) for w, _ in l] for l in CARD3], 255, h=120, seed=3939, sync=False, bg="ON")],
         why="Mélenchon main tendue vers la salle (même discours, 831 s, musique seule) : silhouette blanche 3 images puis découpe, affiche crème ; même carton"),
    dict(id="C7", kind="collage", bg=NAVY, strips=5,
         photos=[dict(src="APL", t=19.0, box=SILH, w=740, c=(540, 760), a=-3, t0=0.0),
                 dict(src="OUV", t=7.6, box=(200, 150, 1700, 1080), w=600, c=(360, 1240), a=5, t0=T / 2),
                 dict(src="PV", t=13.0, box=BACK, w=420, c=(800, 1500), a=-6, t0=T)],
         why="collage sans texte : la salle en contre-jour, Mélenchon arrive au pupitre, la salle de dos"),
    dict(id="FIN", kind="card", bg=ORANGE, push=(1.0, 1.035),
         big=[("JEAN-LUC", 0.0, rgb(NAVY)), ("MÉLENCHON", T, rgb(ORANGE2)), ("2027", 2 * T, rgb(NAVY))],
         big_y=650, big_sizes=[220, 220, 240],
         why="carton final propre (affiche crème sur fond orange, bleu nuit + orange) : son nom + 2027, pas de CTA"),
]
BOUNDS_T = [0] + CUTF + [fr(END)]
assert len(BOUNDS_T) == len(SHOTS) + 1, (len(BOUNDS_T), len(SHOTS))
for i, sh in enumerate(SHOTS):
    sh["a"], sh["bb"] = BOUNDS_T[i], BOUNDS_T[i + 1]; sh["n"] = sh["bb"] - sh["a"]; sh["clip"] = "R13_%s.mov" % sh["id"]
    if sh.get("t") == "sync": sh["t"] = V_SRC0 + sh["a"] / FPS; sh["sync"] = True
assert min(sh["n"] for sh in SHOTS) >= 13, [(s["id"], s["n"]) for s in SHOTS]
for sh in SHOTS:
    if sh.get("sync") and sh["kind"] in ("cut", "full"): assert sh["t"] + sh["n"] / FPS > CAM_CUT, ("gros plan avant la coupe caméra", sh["id"])

def write_mov(frames, path):
    p = subprocess.Popen([FF, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", "%dx%d" % (W, H), "-r", str(FPS), "-i", "-",
                          "-c:v", "prores_ks", "-profile:v", "3", "-pix_fmt", "yuv422p10le", "-vendor", "apl0", path], stdin=subprocess.PIPE)
    for f in frames: p.stdin.write((np.clip(f, 0, 1) * 255 + 0.5).astype(np.uint8).tobytes())
    p.stdin.close(); p.wait()
def draw_pieces(img, pieces, f_abs, boil=None):
    k = nbeat(f_abs)
    for j, (im, cx, cy, t, t1) in enumerate(pieces):
        if t1 is not None and f_abs >= fr(t1): continue
        s = pop(f_abs, fr(t))
        if s is None: continue
        dx, dy, da = jit((boil, j), k, amp=4, ang=1.0) if boil else (0, 0, 0)
        paste(img, im, cx + dx, cy + dy, s, da)
CARD_TAPES = [tape_rgba(170, 46, np.random.default_rng(40 + j)) for j in range(4)]
CARD = None
def card_panel():
    global CARD
    if CARD is None:
        rng = np.random.default_rng(5); w, h = 900, 1180
        m = torn_mask(h, w, rng, rough=9, step=12, inset=6)
        out = np.zeros((h + 20, w + 20, 4), np.float32); out[12:12 + h, 10:10 + w, 3] = cv2.GaussianBlur(m, (0, 0), 5) * 0.5
        body = paper(CREAM)[:h, :w]; out[:h, :w, :3] = body * m[..., None]; out[:h, :w, 3] = np.maximum(m, out[:h, :w, 3])
        CARD = out
    return CARD
def render(sh):
    n = sh["n"]; a = sh["a"]; frames = []
    rel = lambda t: sh["a"] / FPS + t
    sync = sh.get("sync", False)
    txt = []
    for bi, bd in enumerate(sh.get("txt", [])):
        p = board(bd["lines"], bd["y"], seed=bd["seed"] or skey(sh["id"]) * 7 + bi, h=bd["h"], bg=bd["bg"])
        t1 = rel(bd["t1"]) if bd["t1"] is not None else None
        txt += [(im, cx, cy, (max(t, a / FPS) if bd["sync"] else rel(t)), t1) for im, cx, cy, t in p]
    big = []
    if sh.get("big"):
        lines = [(s, (wt(int(t[1:])) if isinstance(t, str) else t), c) for s, t, c in sh["big"]]
        p = big_text(lines, sh["big_y"], sizes=sh["big_sizes"], spec=(FIMP if sh["kind"] == "card" else FCOND),
                     maxw=(XMAX - XMIN) * (0.92 if sh["kind"] == "card" else 1.0), contour=10 if sh["kind"] == "full" else 0,
                     gap=(-6 if sh["kind"] == "card" else -18))
        big = [(im, cx, cy, (max(t, a / FPS) if isinstance(sh["big"][j][1], str) else rel(t)), None) for j, (im, cx, cy, t) in enumerate(p)]
    photos = []
    for j, ph in enumerate(sh.get("photos", [])):
        tt = V_SRC0 + a / FPS if ph["t"] == "sync" else ph["t"]
        photos.append(Photo(read_frames(ph["src"], tt, n, tmax=ph.get("tmax")), ph["box"], ph["w"], ph["c"], ph["a"], fr(rel(ph["t0"])), (sh["id"], j)))
        ph["_t"] = round(tt, 3)
    strips = make_strips(sh)
    k0 = nbeat(a)
    if sh["kind"] in ("cut", "full"):
        raw = read_frames(sh["src"], sh["t"], n, tmin=sh.get("tmin"))
    if sh["kind"] == "cut":
        ms = decoupe_masques(raw, sh["box"], sh["pt"], CACHE + "perso/%s_%s_%.3f_%d_%s" % (sh["id"], sh["src"], sh["t"], n, "-".join(map(str, sh["box"]))))
        cs = [controle(m) for m in ms]
        sh["_controle"] = {k: max(c[k] for c in cs) for k in ("gauche", "droite", "haut", "morceaux", "bas_net")}
        print("   découpe %s : %s" % (sh["id"], sh["_controle"]))
        os.makedirs(D + "sheets", exist_ok=True)
        x0, y0, x1, y1 = sh["box"]; filled = [fill_fig(raw[i][y0:y1, x0:x1], ms[i]) for i in range(n)]
        full = []
        for i in range(n):
            fr_ = raw[i].copy(); fr_[y0:y1, x0:x1] = filled[i][0]; full.append(fr_)
        planche(full, [fm for _, fm in filled], sh["box"], D + "sheets/decoupe-%s.png" % sh["id"])
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
        for st in strips:                                                   # une bande d'affiche de plus à chaque frappe
            if st["k"] <= kb + 2:
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
            crop, m = fill_fig(raw[i][y0:y1, x0:x1], ms[i]); hh = (y1 - y0) * sc
            fcx = (sh["cx"] - x0) * sc; ccx = W / 2 + ((x1 - x0) / 2 * sc - fcx); ccy = H - hh / 2
            body = fig_look(crop)
            white = np.ones_like(body) * hexc(CREAM)
            st_ = np.dstack([np.ones_like(body) * np.array([0.97, 0.97, 0.96], np.float32), sticker(m, 8)])
            sd = st_.copy(); sd[..., :3] = 0; sd[..., 3] = cv2.GaussianBlur(st_[..., 3], (0, 0), 6) * 0.5
            ecol = hexc(NAVY) if sh["bg"] == ORANGE else hexc(ORANGE)
            echo = np.dstack([np.ones_like(body) * ecol, sticker(m, 4) * 0.96])
            ex, ey, _ = jit((sh["id"], "echo"), nbeat(f), amp=10, ang=0)
            paste(img, sd, ccx + 14, ccy + 10, sc)
            paste(img, echo, ccx - 34 + ex, ccy - 18 + ey, sc * 1.015)
            if sh.get("white3") and i < 3: paste(img, np.dstack([white, m]), ccx, ccy, sc)
            else: paste(img, st_, ccx, ccy, sc); paste(img, np.dstack([body, m]), ccx, ccy, sc)
        if sh["kind"] == "full":
            te = torn_edges(); img = img * (1 - te[..., 3:4]) + te[..., :3]
        if sh["kind"] == "card":
            z = sh["push"][0] + (sh["push"][1] - sh["push"][0]) * u
            paste(img, card_panel(), W / 2, H / 2 - 40, z, -1.5)
            for j, (tx, ty, ta) in enumerate(((190, 420, -32), (890, 420, 30), (190, 1450, 28), (890, 1450, -30))):
                paste(img, CARD_TAPES[j], W / 2 + (tx - W / 2) * z, H / 2 + (ty - H / 2) * z, 1.0, ta)
            for im, cx, cy, t, _ in big:
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
    v = grab(HG + "/" + SRC["PV"][0], V_IN, V_OUT - V_IN); env = np.ones(len(v), np.float32)
    k = int(0.03 * sr); env[:k] = np.linspace(0, 1, k); k = int(0.12 * sr); env[-k:] = np.linspace(1, 0, k)
    i0 = int(round(t_of_src(V_IN) * sr)); voix[i0:i0 + len(v)] = v * env[:, None] * 10 ** (4 / 20)
    m = music_stem(END)[:N]
    t = np.arange(len(m)) / sr; vend = t_of_src(23.98); dr = DROP
    # sous la phrase : break riff à -19 dB, montée sur l'intro (riff seul) -19 -> -8 dB, plein sur l'entrée du beat
    gdb = np.interp(t, [0, 0.3, L1, vend, dr - 0.03, dr, END], [-30, -19, -19, -8, -6, 0, 0])
    k = int(0.30 * sr); fo = np.ones(len(m), np.float32); fo[-k:] = np.linspace(1, 0, k)
    mus[:len(m)] = m * (10 ** (gdb / 20) * fo)[:, None]
    sf.write(OUT + "R13-voix.wav", voix, sr, subtype="PCM_24"); sf.write(OUT + "R13-musique.wav", mus, sr, subtype="PCM_24")
    sf.write(D + "tmp_mix.wav", voix + mus, sr, subtype="FLOAT")
    r = subprocess.run([FF, "-hide_banner", "-i", D + "tmp_mix.wav", "-af", "loudnorm=I=-14:TP=-2.5:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    js = json.loads(r[r.rindex("{"):r.rindex("}") + 1])
    af = ("loudnorm=I=-14:TP=-2.5:LRA=11:measured_I=%s:measured_TP=%s:measured_LRA=%s:measured_thresh=%s:offset=%s:linear=true,"
          "aresample=48000" % (js["input_i"], js["input_tp"], js["input_lra"], js["input_thresh"], js["target_offset"]))
    subprocess.run([FF, "-v", "error", "-y", "-i", D + "tmp_mix.wav", "-af", af, "-c:a", "pcm_s24le", OUT + "R13-mix.wav"], check=True)
    os.remove(D + "tmp_mix.wav"); print("audio : mix avant normalisation", js["input_i"], "LUFS")

# ---------------- plan ----------------
PHRASE = ("8 millions de pauvres à l'aide alimentaire, 3 000 personnes à la rue, 11 millions de pauvres que comptent "
          "les statistiques officielles, telle est la France dorénavant.")
def song_pos(tl):
    return ("break", round(B_IN + tl, 3)) if tl < L1 else ("intro+", round(tl - L1, 3))
def build_plan():
    video = []
    for sh in SHOTS:
        v = {"id": sh["id"], "clip": sh["clip"], "folder": "genR13", "path": OUT + sh["clip"], "s": 0, "e": sh["n"], "rec": sh["a"], "dur": sh["n"],
             "clip_fps": FPS, "speed_pct": 100, "track": 1, "note": sh["why"], "kind": sh["kind"], "temps": round(sh["n"] / FPS / T, 2)}
        if sh.get("src"):
            path, sfps, url, off, ctx = SRC[sh["src"]]
            v["source"] = {"fichier": path, "in_s": round(sh["t"], 3), "out_s": round(sh["t"] + sh["n"] / FPS, 3), "fps": sfps,
                           "url": url, "t_youtube_s": round(off + sh["t"], 2), "contexte": ctx, "synchro": bool(sh.get("sync"))}
            if sh.get("tmin"): v["source"]["gel_jusqua_s"] = sh["tmin"]
        if sh.get("photos"):
            v["photos"] = []
            for ph in sh["photos"]:
                tt = V_SRC0 + sh["a"] / FPS if ph["t"] == "sync" else ph["t"]
                v["photos"].append({"fichier": SRC[ph["src"]][0], "in_s": round(tt, 3), "out_s": round(tt + sh["n"] / FPS, 3), "cadre_source": ph["box"],
                                    "url": SRC[ph["src"]][2], "t_youtube_s": round(SRC[ph["src"]][3] + tt, 2), "synchro": ph["t"] == "sync"})
        video.append(v)
    texts = []
    for sh in SHOTS:
        for bd in sh.get("txt", []):
            for line in bd["lines"]: texts.append({"plan": sh["id"], "texte": " ".join(w for w, _ in line)})
        for s_, t_, c_ in sh.get("big", []): texts.append({"plan": sh["id"], "texte": s_})
    plan = {"name": "R13 - Collage ransom-note affiche de meeting - Jean-Luc Mélenchon (Black Eyed Peas - Pump It)", "fps": FPS, "w": W, "h": H,
            "duree_s": round(fr(END) / FPS, 3),
            "note": "Plans ProRes 9:16 composés en Python (lot7/_claude/gen/R13/out) : fonds orange / bleu nuit / affiche crème à trame orange, "
                    "Mélenchon détouré (segment/Vision) en bichromie bleu nuit -> crème (cravate orange) + écho décalé, photos bichromie scotchées, "
                    "bandes d'affiche déchirées, plein cadre bichromie bleu nuit -> orange -> crème, textes ransom-note cuits (chiffres en lettres découpées). "
                    "s/e en images du clip (30 i/s), rec en images timeline. Coupes sur les frappes réelles de Pump It (son.json). Aucun ralenti. "
                    "Générateur : lot7/_claude/gen/R13/genR13.py",
            "phrase": {"texte": PHRASE, "url": URL, "source": SRC["PV"][0], "in_s": 12.36, "out_s": 23.98,
                       "t_youtube_s": [802.36, 813.98], "timeline_s": [round(t_of_src(12.36), 2), round(t_of_src(23.98), 2)],
                       "avant": "« Je ne signalerai que le plus douloureux du résultat et le plus honteux pour ses auteurs. »",
                       "apres_non_garde": "« Dans les villes de toutes tailles, une gare sur deux a fermé… » (phrase suivante)",
                       "voix": "son direct synchro : A1-A2 plan de dos dans la salle (même moment), B1-B2 gros plan pupitre (même moment ; B1 figé "
                               "1 s sur la 1re image du gros plan pendant « la rue », la source étant encore sur le plan de dos), B3 les élus, la salle et l'équipe qui écoutent",
                       "doute": "Whisper (turbo et large-v3) entend « trois mille personnes à la rue » (très probablement 300 000) : le chiffre n'est jamais affiché, seulement « À LA RUE »"},
            "musique": {"fichier": "lot7/sons/R13-bep-pump-it_complet.wav", "titre": "Black Eyed Peas - Pump It", "url": SON_URL,
                        "montage": [{"timeline_s": [0.0, round(L1, 4)], "complet_s": [round(B_IN, 4), round(B_END, 4)], "partie": "break riff sans basse"},
                                    {"timeline_s": [round(L1, 4), END], "complet_s": [0.0, round(END - L1, 4)], "partie": "intro riff puis entrée du beat (drop)"}],
                        "drop_timeline_s": round(DROP, 4), "coupes_s": [round(c, 4) for c in CUTS], "coupes_images": CUTF},
            "textes": texts, "video": video,
            "audio": [{"id": "mix", "clip": "R13-mix.wav", "folder": "genR13", "path": OUT + "R13-mix.wav", "rec": 0, "track": 1,
                       "note": "mix -14 LUFS : voix PV %.2f-%.2f s (+4 dB) à %.2f s ; Pump It : break %.3f-%.3f s puis intro dès 0 s (raccord sur la mesure, fondu 8 ms), "
                               "-19 dB sous la voix, montée sur le riff de l'intro, plein au drop, fondu de fin 0,3 s" % (V_IN, V_OUT, t_of_src(V_IN), B_IN, B_END)}],
            "stems": ["lot7/_claude/gen/R13/out/R13-voix.wav", "lot7/_claude/gen/R13/out/R13-musique.wav"],
            "logos_exclus": "logos « Convention municipales » (haut gauche) et LFI (haut droite) : hors des cadres photo, fonds détourés ; écrans à texte de la scène hors cadre"}
    json.dump(plan, open(D + "plan-R13.json", "w"), indent=1, ensure_ascii=False)
    son = {"id": "R13", "titre": "Pump It (Radio Edit)", "artiste": "The Black Eyed Peas", "url": SON_URL,
           "chaine": "Black Eyed Peas (chaîne officielle vérifiée, « Provided to YouTube by Universal Music Group », ℗ 2005 Interscope)",
           "fichier": "lot7/sons/R13-bep-pump-it_complet.wav",
           "extrait_complet_s": {"debut": round(B_IN, 4), "fin": round(END - L1, 3),
                                 "montage": "break %.2f-%.2f s (timeline 0-%.2f) puis intro 0-%.2f s (timeline %.2f-%.2f), raccord sur la mesure"
                                            % (B_IN, B_END, L1, END - L1, L1, END)},
           "paroles_audibles": "sous la phrase (-19 dB) : break riff (« dun dun dun », ad-libs) puis l'intro riff seule ; au drop : le riff avec le beat, "
                               "le hook « Pump it » (Whisper « Pump it… up, up, high »)",
           "bpm": round(60 / T, 2), "temps_s": round(T, 5),
           "drop": {"complet_s": MDROP, "timeline_s": round(DROP, 4), "nature": "entrée du beat (kick) sous le riff de l'intro, moment des edits TikTok"},
           "frappes_timeline_s": [round(b, 4) for b in BEATS if 0 <= b <= END],
           "coupes_sur_frappes_s": [round(c, 4) for c in CUTS],
           "coupes_complet": [("break %.4f" % h) if s == "b" else ("%.4f" % h) for s, h in CUT_SONG],
           "mix": "lot7/_claude/gen/R13/out/R13-mix.wav"}
    json.dump(son, open(D + "son.json", "w"), indent=1, ensure_ascii=False)

# ---------------- aperçu 540x960 ----------------
def apercu():
    plan = json.load(open(D + "plan-R13.json")); ins = []; fl = []
    for i, v in enumerate(plan["video"]):
        ins += ["-i", OUT + v["clip"]]
        fl.append("[%d:v]trim=start_frame=%d:end_frame=%d,setpts=PTS-STARTPTS,scale=540:960,setsar=1[v%d]" % (i, v["s"], v["e"], i))
    k = len(plan["video"]); fl.append("".join("[v%d]" % i for i in range(k)) + "concat=n=%d:v=1:a=0[v]" % k)
    ins += ["-i", OUT + "R13-mix.wav"]; out = HG + "/preview/apercu-R13.mp4"
    subprocess.run([FF, "-v", "error", "-y"] + ins + ["-filter_complex", ";".join(fl), "-map", "[v]", "-map", "%d:a" % k,
                    "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "aac", "-b:a", "192k", "-shortest", out], check=True)
    print("aperçu", out)
# ---------------- mesure sur l'export ----------------
def stem_hits():
    """Frappes réelles détectées séparément dans les deux morceaux du montage musical (break, intro+suite), en temps timeline."""
    hb = [(x[0] + 0.0, x) for x in detect_hits(song_raw(B_IN, L1))]
    hi = [(x[0] + L1, x) for x in detect_hits(song_raw(0.0, END - L1))]
    return [t for t, _ in hb] + [t for t, _ in hi]
def mesure():
    import soundfile as sf
    out = HG + "/preview/apercu-R13.mp4"
    r = subprocess.run([FF, "-v", "info", "-i", out, "-vf", "scale=135:240,select='gt(scene,0.2)',showinfo", "-an", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    cuts = [float(x) for x in re.findall(r"pts_time:([0-9.]+)", r)]
    p = subprocess.run([FF, "-v", "error", "-i", out, "-vn", "-ac", "1", "-ar", "48000", "-f", "f32le", "-"], capture_output=True)
    ye = np.frombuffer(p.stdout, np.float32)
    ymx, _ = sf.read(OUT + "R13-mix.wav", dtype="float32"); ymx = ymx.mean(1)
    n = min(len(ye), len(ymx)); A = np.fft.rfft(ye[:n], 2 * n); Bf = np.fft.rfft(ymx[:n], 2 * n)
    xc = np.fft.irfft(A * np.conj(Bf)); lags = np.r_[0:2000, -2000:0]; lag = lags[np.argmax(np.r_[xc[:2000], xc[-2000:]])] / 48000
    h = stem_hits()
    print("décalage audio export / mix : %+.1f ms" % (lag * 1000))
    print("coupes image détectées (export) :", cuts)
    worst = 0
    for j, c in enumerate([fr_ / FPS for fr_ in CUTF]):
        det = min(cuts, key=lambda x: abs(x - c)) if cuts else None
        k = min(h, key=lambda t: abs(t - CUTS[j])) + lag
        e = ((det if det is not None and abs(det - c) < 0.1 else c) - k) * 1000; worst = max(worst, abs(e))
        print("  coupe %.3f (détectée %s)  frappe %.4f  écart %+.1f ms" % (c, "%.3f" % det if det is not None else "-", k, e))
    print("écart max coupes/frappes : %.1f ms" % worst)
    r = subprocess.run([FF, "-hide_banner", "-i", out, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    print(r[r.rindex("Summary"):])
if __name__ == "__main__":
    args = set(a for a in sys.argv[1:] if not a.startswith("only=")) or {"shots", "audio", "plan", "apercu"}
    only = [x for a in sys.argv[1:] if a.startswith("only=") for x in a.split("=", 1)[1].split(",")]
    print("L1 %.4f (break %.3f-%.3f) ; drop %.4f ; coupes (s) :" % (L1, B_IN, B_END, DROP), [round(c, 3) for c in CUTS], "images :", CUTF, "fin", fr(END))
    if "shots" in args or only:
        for sh in SHOTS:
            if not only or sh["id"] in only: render(sh)
    if "audio" in args: make_audio()
    if "plan" in args: build_plan()
    if "apercu" in args: apercu()
    if "mesure" in args: mesure()
