# R9 (lot 7, refait le 27/10 : Luca n'a aimé ni Petit génie, ni le fanzine pastel) — Collage ransom-note énergique dans la lignée
# de lot6 R2 et R6 (validés), Jean-Luc Mélenchon, son Tiakola – Meuda (clip officiel, chaîne TIAKOLA certifiée).
# Visuel : aplats vert émeraude / noir / papier blanc qui changent sur les frappes, Mélenchon découpé en N&B contrasté (outil commun
#   _claude/outils/decoupe.py), buste entier jusqu'au pupitre posé sur le bas du cadre et assez grand pour que le visage reste
#   entre ~45 et 70 % de la hauteur (hors interface TikTok), contour autocollant blanc, double tirage tramé, grosses lettres
#   découpées, photos N&B / émeraude scotchées, bandes et trame qui s'empilent sur les frappes, flash blanc 3 images au drop,
#   carton final JEAN-LUC MÉLENCHON + 2027.
# Phrase (sur la jeunesse, son direct, Fête de l'Humanité 12/09/2026, chaîne JEAN-LUC MÉLENCHON, youtu.be/80bBtk2lTiI ~4739,2-4746,9 s
#   = lot1/sources/3-melenchon-huma-citation.mp4 29,20-36,94 s) :
#   « Alors c'est une crise de la civilisation humaine que votre génération, jeunes gens, va non seulement devoir affronter, mais régler. »
#   -> autre phrase que tous les edits Mélenchon des lots 1 à 6. Valence (AMFiS 2026) n'a pas de phrase courte sur la jeunesse
#   (« Notre peuple et vous jeunes gens… » dure 25 s) : Valence donne les images de la foule et des jeunes (extrait neuf
#   lot7/sources/R9-melenchon-valence-jeunes.mp4 = youtu.be/IYegq2-6-go 2940-3010 s).
# Son : extrait continu ; sous la phrase, la partie guitare sans basse avant le 1er refrain (= montée) ; drop = entrée de la basse
#   808 sur le 1er refrain (32,74 s du morceau). Paroles : aucune écrite ici (consigne Luca) ; refrain désigné par ses temps.
# Usage : python genR9.py [shots] [audio] [plan] [apercu] [mesure] [only=ID,ID]   (sans argument = tout sauf mesure)
import sys
sys.dont_write_bytecode = True
import os, json, subprocess, math, re
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
HG = "/Users/luca.grousset/Movies/highkey-gauchiste"
D = HG + "/lot7/_claude/gen/R9/"; OUT = D + "out/"; CACHE = D + "cache/"; os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, D)
from hits import detect_hits
sys.path.insert(0, HG + "/_claude/outils")
from decoupe import masques as dc_masques, controle as dc_controle, planche as dc_planche   # outil commun des découpes
FF = "/opt/homebrew/bin/ffmpeg"; FPS = 30; W, H = 1080, 1920
def fr(t): return int(round(t * FPS))
def hexc(h): h = h.lstrip("#"); return np.array([int(h[4:6], 16), int(h[2:4], 16), int(h[0:2], 16)], np.float32) / 255   # BGR
def rgb(h): h = h.lstrip("#"); return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
# palette R9 (brief refait) : vert émeraude, noir, blanc
EMER, EMER_D, EMER_L = "#00A86B", "#006B47", "#3FD39A"
BLACK, WHITE = "#101010", "#F4F2EC"

# ---------------- sources (lecture seule) ----------------
SRC = {
    "HUMA": ("lot1/sources/3-melenchon-huma-citation.mp4", 50.0, "https://www.youtube.com/watch?v=80bBtk2lTiI", 4710.0,
             "Fête de l'Humanité, 12/9/2026 (chaîne JEAN-LUC MÉLENCHON)"),
    "VALJ": ("lot7/sources/R9-melenchon-valence-jeunes.mp4", 30.0, "https://www.youtube.com/watch?v=IYegq2-6-go", 2940.0,
             "meeting des AMFiS, Valence, 23/8/2026 (chaîne JEAN-LUC MÉLENCHON), extrait 2940-3010 s"),
}

# ---------------- musique : Tiakola – Meuda ----------------
SON_FILE = HG + "/lot7/sons/R9-tiakola-meuda_complet.wav"; SON_URL = "https://www.youtube.com/watch?v=Qq7Q6CLCfvs"
T = 0.4225                                   # ≈ 142 BPM (808 32,740 -> 36,120 = 8 temps)
MDROP = 32.740                               # entrée de la basse 808 sur le 1er refrain (refrain 32,7-56 s, repris 86-110 s et 141-150 s)
MUSIC_IN0 = 23.879                           # pincement de guitare (partie sans basse) : t = 0 de la timeline
# coupes (temps du morceau) : 2 avant le drop (guitare 26,86, kick 29,35), drop, puis sur les 808 / claps les plus forts ; fin = 808 42,88
CUT_SONG = [26.855, 29.346, 32.740, 35.275, 36.120, 36.964, 38.233, 39.473, 40.346]
END_SONG = 42.880
HITS_JSON = OUT + "R9-frappes.json"
def music_raw(mi, dur=None, sr=48000):
    import soundfile as sf
    dur = dur or (END_SONG - MUSIC_IN0 + 0.6)
    i0 = int(round(mi * sr)); x, r = sf.read(SON_FILE, start=i0, frames=int(dur * sr), dtype="float32"); assert r == sr; return x
def hits_of(h, lvl=0.025): return [x[0] for x in h if x[3] > lvl]
def snap_list(ks, targets):
    out = []
    for t in targets:
        c = min(ks, key=lambda k: abs(k - t)); assert abs(c - t) < 0.04, ("pas de frappe près de", t, c); out.append(c)
    return out
def frappes():
    tg = [c - MUSIC_IN0 for c in CUT_SONG + [END_SONG]]
    if os.path.exists(HITS_JSON):
        js = json.load(open(HITS_JSON))
        if js["cle"] == [MUSIC_IN0, tg]: return js["music_in"], js["frappes"]
    best, bad = None, 9
    for off in np.arange(-0.016, 0.0165, 0.001):
        h = detect_hits(music_raw(MUSIC_IN0 + off))
        try: cuts = snap_list(hits_of(h), [t - off for t in tg])
        except AssertionError: continue
        e = max(abs(c - round(c * FPS) / FPS) for c in cuts)
        if e < bad: best, bad, hb = off, e, h
    mi = MUSIC_IN0 + best
    json.dump({"cle": [MUSIC_IN0, tg], "music_in": mi, "frappes": hb}, open(HITS_JSON, "w")); return mi, hb
MUSIC_IN, HITS = frappes()
ALLC = snap_list(hits_of(HITS), [c - MUSIC_IN for c in CUT_SONG + [END_SONG]])
CUTS = ALLC[:-1]
CUTF = [fr(c) for c in CUTS]; ENDF = fr(ALLC[-1]); END = ENDF / FPS
DROPF = CUTF[2]; TB = T
def _beats():
    """Frappes visibles (aplats, bandes, photos) : pincements forts avant le drop, 808 et claps forts après, au moins 0,3 s d'écart."""
    pre = [x[0] for x in HITS if x[3] > 0.09 and x[2] > 0.45 and x[0] < CUTS[2] - 0.1]
    post = [x[0] for x in HITS if x[0] >= CUTS[2] - 0.02 and ((x[1] == "kick" and x[3] > 0.35) or (x[1] == "caisse" and x[2] > 0.6))]
    out = []
    for t in sorted(pre + post + CUTS):
        if not out or t - out[-1] > 0.3: out.append(round(t, 4))
    return [b for b in out if b < END + 0.01]
BEATS = _beats(); BEATF = [fr(b) for b in BEATS]
def nbeat(f): return sum(1 for b in BEATF if b <= f)

# ---------------- voix ----------------
V_SRC0 = 28.60                               # fichier HUMA à t = 0 (« Alors » 29,20 -> 0,60 s)
V_IN, V_OUT = 29.12, 37.02                   # « Alors » … « régler » (fin 36,94), coupé avant « et que nous tous » (37,10)
def t_of_src(s): return s - V_SRC0
WORDS = [("ALORS", 29.20), ("C'EST", 29.76), ("UNE", 30.38), ("CRISE", 30.56), ("DE", 30.94), ("LA", 31.10), ("CIVILISATION", 31.20),
         ("HUMAINE", 31.84), ("QUE", 32.34), ("VOTRE", 32.92), ("GÉNÉRATION,", 33.34), ("JEUNES", 34.12), ("GENS,", 34.32),
         ("VA", 34.90), ("NON", 35.06), ("SEULEMENT", 35.22), ("DEVOIR", 35.50), ("AFFRONTER,", 35.86), ("MAIS", 36.44), ("RÉGLER.", 36.58)]
def wt(i): return t_of_src(WORDS[i][1])

# ---------------- polices ransom-note ----------------
S = "/System/Library/Fonts/Supplemental/"
FONTS = [(S + "Arial Black.ttf", 0), (S + "Georgia Bold.ttf", 0), (S + "Times New Roman Bold.ttf", 0), (S + "Impact.ttf", 0),
         (S + "Courier New Bold.ttf", 0), (S + "Rockwell.ttc", 2), (S + "AmericanTypewriter.ttc", 2), (S + "Didot.ttc", 2),
         (S + "Bodoni 72.ttc", 2), (S + "Futura.ttc", 2)]
FCOND = (S + "Futura.ttc", 4)
POP_STYLES = [(rgb(EMER), (255, 255, 255)), (rgb(BLACK), (255, 255, 255)), (rgb(WHITE), rgb(BLACK)), (rgb(WHITE), rgb(EMER_D)),
              (rgb(EMER_D), (255, 255, 255)), (rgb(BLACK), rgb(EMER_L)), ((255, 255, 255), rgb(EMER))]
_fc = {}
def font(spec, size):
    k = (spec, size)
    if k not in _fc: _fc[k] = ImageFont.truetype(spec[0], size, index=spec[1])
    return _fc[k]
def chip(txt, h, rng, styles, fspec=None, style=None, rot=None, avoid=None):
    """Un morceau découpé : rectangle irrégulier + texte, RGBA PIL, légèrement penché."""
    fspec = fspec or FONTS[rng.integers(len(FONTS))]
    if style is None:
        style = styles[rng.integers(len(styles))]
        while avoid is not None and style == avoid: style = styles[rng.integers(len(styles))]
    bg, fg = style
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
    return im.rotate(a, resample=Image.BICUBIC, expand=True), style
def word_img(word, h, rng, styles, letters=False):
    if not letters: return chip(word, h, rng, styles, fspec=((S + "Impact.ttf", 0) if len(word) >= 9 else None))[0]
    parts = []; last = None
    for c in word:                                                           # lettre par lettre, jamais 2 papiers identiques côte à côte
        p, last = chip(c, h * rng.uniform(0.92, 1.08), rng, styles, rot=rng.uniform(-7, 7), avoid=last); parts.append(p)
    wsum = sum(p.width for p in parts) - 12 * (len(parts) - 1); hh = max(p.height for p in parts) + 10
    im = Image.new("RGBA", (wsum, hh), (0, 0, 0, 0)); x = 0
    for p in parts:
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
    return out
XMIN, XMAX, YMIN, YMAX = 0.19 * W, 0.81 * W, 0.13 * H, 0.74 * H          # zone sûre TikTok (0,17-0,83 / 0,12-0,75) + marge
def board(lines, y0, seed, styles, h=112, letters=(), maxw=XMAX - XMIN - 30):
    """lines = [[(mot, t), …], …] -> pièces (img, cx, cy, t)."""
    rng = np.random.default_rng(seed); pieces = []; y = y0
    for line in lines:
        imgs = [shadowed(word_img(w, h * (1.12 if w in letters else 1.0), rng, styles, w in letters)) for w, _ in line]
        gap = 8; tot = sum(i.shape[1] for i in imgs) + gap * (len(imgs) - 1)
        sc = min(1.0, maxw / tot); lh = max(i.shape[0] for i in imgs) * sc
        x = W / 2 - tot * sc / 2 + rng.uniform(-14, 14); x = min(max(x, XMIN + 4), XMAX - 4 - tot * sc)
        for (w, t), im in zip(line, imgs):
            if sc < 1: im = cv2.resize(im, (int(im.shape[1] * sc), int(im.shape[0] * sc)), interpolation=cv2.INTER_AREA)
            pieces.append((im, x + im.shape[1] / 2, y + lh / 2, t)); x += im.shape[1] + gap * sc
        y += lh - 6
    for im, cx, cy, t in pieces:
        assert XMIN - 2 <= cx - im.shape[1] / 2 and cx + im.shape[1] / 2 <= XMAX + 2, ("texte hors zone x", cx, im.shape)
        assert YMIN - 2 <= cy - im.shape[0] / 2 and cy + im.shape[0] / 2 <= YMAX + 2, ("texte hors zone y", cy, im.shape)
    return pieces
def big_text(lines, y0, spec=FCOND, maxw=XMAX - XMIN, sizes=None, contour=0):
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
    """Aplat de papier : grain + nuages légers."""
    if col not in _tex:
        rng = np.random.default_rng(len(_tex) + 3)
        n = cv2.resize(rng.standard_normal((48, 27)).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC)
        n2 = cv2.GaussianBlur(rng.standard_normal((H, W)).astype(np.float32), (0, 0), 1.2)
        base = hexc(col)[None, None, :] * (1 + 0.03 * n[..., None] + 0.035 * n2[..., None])
        if col == BLACK: base = base + 0.02 * (n[..., None] + 1)
        _tex[col] = np.clip(base, 0, 1).astype(np.float32)
    return _tex[col].copy()
VIG = None
def finish(img, f):
    global VIG
    if VIG is None:
        y, x = np.mgrid[0:H, 0:W].astype(np.float32)
        r = np.sqrt(((x - W / 2) / (W / 2)) ** 2 + ((y - H / 2) / (H / 2)) ** 2) / np.sqrt(2)
        VIG = (1 - 0.26 * np.clip(r, 0, 1) ** 2.4)[..., None].astype(np.float32)
    rng = np.random.default_rng(1000 + f)
    g = rng.standard_normal((H // 2, W // 2)).astype(np.float32)
    g = cv2.resize(g, (W, H), interpolation=cv2.INTER_LINEAR)[..., None] * 0.025
    return np.clip(img * VIG + g, 0, 1)

# ---------------- lecture source ----------------
def read_frames(src, t, n_out):
    path, sfps = SRC[src][0], SRC[src][1]
    need = [int(round(i * sfps / FPS)) for i in range(n_out)]
    p = subprocess.run([FF, "-v", "error", "-ss", "%.4f" % t, "-i", HG + "/" + path, "-frames:v", str(need[-1] + 1),
                        "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True)
    a = np.frombuffer(p.stdout, np.uint8).reshape(-1, 1080, 1920, 3)
    return [a[min(i, len(a) - 1)].astype(np.float32) / 255 for i in need]
LUMA = np.array([0.0722, 0.7152, 0.2126], np.float32)
def mono(x):
    """N&B contrasté (tirage de journal) : noirs denses, blancs propres."""
    L = x @ LUMA; lo, hi = np.percentile(L, 1.5), np.percentile(L, 99.3)
    L = np.clip((L - lo) / max(hi - lo, 0.1), 0, 1); L = 0.80 * L + 0.20 * (L * L * (3 - 2 * L))
    return np.repeat(L[..., None], 3, 2).astype(np.float32)
def emer(x):
    """Duotone émeraude : noir -> émeraude -> blanc."""
    L = mono(x)[..., 0]; lo = np.clip(L * 2, 0, 1)[..., None]; hi = np.clip(L * 2 - 1, 0, 1)[..., None]
    k, e, w = hexc("#07120D"), hexc(EMER), hexc(WHITE)
    return np.where(L[..., None] < 0.5, k * (1 - lo) + e * lo, e * (1 - hi) + w * hi).astype(np.float32)
def tone(x, kind): return emer(x) if kind == "emer" else mono(x)
def cutout_rgba(img, m, box, kind="mono", white=False):
    x0, y0, x1, y1 = box; c = tone(img[y0:y1, x0:x1], kind)
    if white: c = np.ones_like(c) * np.array([0.96, 0.97, 0.98], np.float32)
    return np.dstack([c, m]).astype(np.float32)

# ---------------- matières du collage : déchirures, scotch, bandes, trame ----------------
def skey(x): return sum((i + 1) * ord(c) for i, c in enumerate(str(x)))
def torn_mask(h, w, rng, rough=7, step=14, inset=8):
    pts = []
    for x in np.arange(inset, w - inset, step): pts.append((x, inset + rng.uniform(-rough, rough)))
    for y in np.arange(inset, h - inset, step): pts.append((w - inset + rng.uniform(-rough, rough), y))
    for x in np.arange(w - inset, inset, -step): pts.append((x, h - inset + rng.uniform(-rough, rough)))
    for y in np.arange(h - inset, inset, -step): pts.append((inset + rng.uniform(-rough, rough), y))
    m = np.zeros((h, w), np.float32); cv2.fillPoly(m, [np.array(pts, np.int32)], 1.0, lineType=cv2.LINE_AA)
    return m
def tape_rgba(w, h, rng, col=(0.86, 0.90, 0.88), alpha=0.72):
    m = np.ones((h, w), np.float32)
    for y in range(h):
        a = int(rng.integers(0, 7)); b = int(rng.integers(0, 7)); m[y, :a] = 0; m[y, w - b:] = 0
    c = np.array(col, np.float32)[None, None, :] * (1 + 0.04 * rng.standard_normal((h, w, 1)).astype(np.float32))
    return np.dstack([c, m * alpha]).astype(np.float32)
def halftone(h, w, col, dot, step=14):
    img = np.ones((h, w, 3), np.float32) * col[None, None, :]
    for y in range(0, h, step):
        for x in range((y // step % 2) * step // 2, w, step): cv2.circle(img, (x, y), 4, tuple(float(v) for v in dot), -1, cv2.LINE_AA)
    return img
def strip_rgba(w, h, rng, colhex, ht=False):
    col = hexc(colhex); dot = hexc(BLACK) if colhex != BLACK else hexc(EMER)
    body = halftone(h, w, col, dot) if ht else np.ones((h, w, 3), np.float32) * col[None, None, :]
    body = np.clip(body * (1 + 0.035 * cv2.GaussianBlur(rng.standard_normal((h, w)).astype(np.float32), (0, 0), 1.5))[..., None], 0, 1)
    m = torn_mask(h, w, rng, rough=9, step=12)
    out = np.zeros((h + 16, w + 16, 4), np.float32)
    out[10:10 + h, 8:8 + w, 3] = cv2.GaussianBlur(m, (0, 0), 3) * 0.45
    a = m[..., None]; out[:h, :w, :3] = body * a; out[:h, :w, 3] = np.maximum(m, out[:h, :w, 3])
    return out
STRIP_COLS = [EMER, BLACK, WHITE, EMER_D, EMER_L, WHITE]
def make_strips(sh):
    n = sh.get("strips", 0); rng = np.random.default_rng(skey(sh["id"]) + 5); out = []
    zones = sh.get("strip_zones") or [(150, 480), (930, 560), (120, 1250), (960, 1300), (540, 300), (540, 1780), (230, 900), (880, 1050)]
    bgs = sh.get("bgs") or [sh.get("bg")]
    for k in range(n):
        w, h = int(rng.uniform(380, 660)), int(rng.uniform(80, 170))
        colhex = STRIP_COLS[(k + skey(sh["id"])) % len(STRIP_COLS)]
        if colhex in bgs: colhex = STRIP_COLS[(k + 3) % len(STRIP_COLS)]
        if colhex in bgs: colhex = STRIP_COLS[(k + 4) % len(STRIP_COLS)]
        cx, cy = zones[(k * 3 + skey(sh["id"])) % len(zones)]
        out.append(dict(img=strip_rgba(w, h, rng, colhex, ht=(k % 3 == 1)), cx=cx + rng.uniform(-60, 60), cy=cy + rng.uniform(-60, 60),
                        ang=rng.uniform(-28, 28), k=k))
    return out
class Photo:
    """Photo vivante : tirage N&B ou émeraude, bord déchiré, scotch, ombre ; saute sur les frappes."""
    def __init__(self, frames, box, width, center, angle, f0, key, kind="mono", border=16):
        self.frames, self.box, self.width, self.center, self.angle, self.f0, self.key, self.kind = frames, box, width, center, angle, f0, key, kind
        x0, y0, x1, y1 = box; self.h = int(round(width * (y1 - y0) / (x1 - x0))); self.b = border
        rng = np.random.default_rng(skey(key)); M = 40
        self.M = M; hh, ww = self.h + 2 * border, width + 2 * border
        self.mask = torn_mask(hh, ww, rng, rough=4, step=11, inset=3)
        self.shadow = np.zeros((hh + 2 * M, ww + 2 * M), np.float32); self.shadow[M + 9:M + 9 + hh, M + 7:M + 7 + ww] = self.mask * 0.5
        self.shadow = cv2.GaussianBlur(self.shadow, (0, 0), 4)
        self.paper = np.array([0.94, 0.95, 0.96], np.float32)
        self.tape_imgs = []
        for t, (tx, ty), ta in ((tape_rgba(int(rng.uniform(110, 150)), 38, rng), (M + int(rng.uniform(-10, 30)), M - 12), rng.uniform(-40, -25)),
                                (tape_rgba(int(rng.uniform(110, 150)), 38, rng), (M + ww - int(rng.uniform(90, 140)), M + hh - 26), rng.uniform(-40, -25))):
            R = cv2.getRotationMatrix2D((t.shape[1] / 2, t.shape[0] / 2), ta, 1.0)
            c = np.abs(R[:, :2]) @ np.array([t.shape[1], t.shape[0]]); R[0, 2] += c[0] / 2 - t.shape[1] / 2; R[1, 2] += c[1] / 2 - t.shape[0] / 2
            self.tape_imgs.append((cv2.warpAffine(t, R, (int(c[0]), int(c[1]))), (tx, ty)))
    def rgba(self, i):
        x0, y0, x1, y1 = self.box; b, M = self.b, self.M
        c = cv2.resize(tone(self.frames[i][y0:y1, x0:x1], self.kind), (self.width, self.h), interpolation=cv2.INTER_AREA)
        hh, ww = self.h + 2 * b, self.width + 2 * b
        out = np.zeros((hh + 2 * M, ww + 2 * M, 4), np.float32); out[..., 3] = self.shadow
        body = np.ones((hh, ww, 3), np.float32) * self.paper; body[b:b + self.h, b:b + self.width] = c
        a = self.mask[..., None]; reg = out[M:M + hh, M:M + ww]
        reg[..., :3] = body * a; reg[..., 3] = np.maximum(self.mask, reg[..., 3])
        for t, (tx, ty) in self.tape_imgs:
            th, tw = t.shape[:2]; ty2, tx2 = max(0, ty), max(0, tx)
            sub = out[ty2:ty2 + th, tx2:tx2 + tw]; tt = t[:sub.shape[0], :sub.shape[1]]
            ta = tt[..., 3:4]; sub[..., :3] = sub[..., :3] * (1 - ta) + tt[..., :3] * ta; sub[..., 3] = np.maximum(sub[..., 3], tt[..., 3])
        return out
def jit(key, k, amp=8.0, ang=1.5):
    r = np.random.default_rng(skey(key) * 1000 + k); return r.uniform(-amp, amp), r.uniform(-amp, amp), r.uniform(-ang, ang)
_scr = {}
def screen(h, w, cell=13):
    if (h, w) not in _scr:
        y, x = np.mgrid[0:h, 0:w].astype(np.float32); u, v = (x + y) / 1.4142, (x - y) / 1.4142
        _scr[(h, w)] = (np.cos(2 * np.pi * u / cell) + np.cos(2 * np.pi * v / cell)) / 4 + 0.5
    return _scr[(h, w)]
def ghost_rgba(img, m, box, sc, colhex):
    """Double tirage en trame d'imprimerie (points à 45°) de la découpe, couleur unie : posé derrière la découpe."""
    x0, y0, x1, y1 = box; w, h = int((x1 - x0) * sc), int((y1 - y0) * sc)
    L = img[y0:y1, x0:x1] @ LUMA; L = np.clip(L / max(float(np.percentile(L, 99)), 0.2) * 1.3, 0, 1)
    L = cv2.resize(L, (w, h), interpolation=cv2.INTER_AREA); mm = cv2.resize(m, (w, h), interpolation=cv2.INTER_AREA)
    ink = np.clip(((1 - L) * 0.9 + 0.08 - screen(h, w)) * 6, 0, 1) * mm
    return np.dstack([np.ones((h, w, 3), np.float32) * hexc(colhex)[None, None, :], ink * 0.95]).astype(np.float32)
def head_x(m):
    """x (dans le cadre) du centre de la tête : pixels du masque dans les 7 % du haut (crâne, pas le bras levé) de la silhouette."""
    ys, xs = np.nonzero(m > 0.5)
    if len(ys) == 0: return m.shape[1] / 2
    top = ys.min(); sel = ys < top + 0.07 * (ys.max() - top)
    return float(xs[sel].mean())
def sticker(m, r=7):
    return cv2.dilate(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1)))
TORN_EDGES = None
def torn_edges():
    global TORN_EDGES
    if TORN_EDGES is None:
        rng = np.random.default_rng(11); out = np.zeros((H, W, 4), np.float32); col = hexc(WHITE)
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
# Découpes (Luca 27/10) : rien que lui (decoupe.py), buste entier jusqu'au haut du pupitre (y ≈ 815, bouts de micros tolérés),
# posé sur le bas du cadre ; échelle choisie pour que le menton reste au-dessus de ~70 % de la hauteur et le haut de la tête
# sous les textes. Valence : filigrane MELENCHON 2027.fr (x > 1560, y < 170) toujours hors cadre.
HUMA_SYNC = (420, 60, 1620, 815)      # Huma 29-37 s : synchro avec la voix
HUMA_ARMS = (330, 60, 1750, 815)      # Huma 45,5-47,4 s : bras ouverts
HUMA_HAND = (440, 40, 1520, 815)      # Huma 49,6-51,5 s : main ouverte
HUMA_REACH = (260, 40, 1520, 815)     # Huma 65,2-66,1 s : bras tendu
CROWD_W = (0, 200, 1560, 1080)        # Valence 5,6-15,7 s : foule au bord du lac, drapeaux
BACKS = (0, 170, 1500, 1080)          # Valence 19,9-23,7 s : jeunes de dos qui applaudissent
CROWD_F = (0, 300, 1560, 1080)        # Valence 23,7-29,1 s : foule, drapeaux, chapeaux
BACKS2 = (0, 200, 1500, 1080)         # Valence 59,9-66,3 s : la salle de dos, la scène au loin
PP = POP_STYLES
TOPZ = [(150, 300), (930, 360), (110, 820), (980, 760), (540, 230), (200, 600), (900, 980), (130, 1150)]   # bandes : autour des textes / sur les côtés
# photo = (source, t, cadre, largeur, (cx, cy), angle, apparition (s dans le plan), tirage)
SHOTS = [
    # ---- avant le drop : voix de l'Huma, foule de Valence (personne ne parle à l'image) puis images synchro ----
    dict(id="A1", kind="collage", bgs=[EMER, BLACK, WHITE, EMER],
         photos=[("VALJ", 20.10, BACKS, 860, (540, 1130), 3, 0.0, "mono"),
                 ("VALJ", 7.00, CROWD_W, 560, (330, 1560), -6, TB, "emer"),
                 ("VALJ", 60.30, BACKS2, 540, (760, 1650), 5, TB * 3, "mono")],
         txt=[[("ALORS", wt(0)), ("C'EST", wt(1))], [("UNE", wt(2)), ("CRISE", wt(3))], [("DE", wt(4)), ("LA", wt(5))], [("CIVILISATION", wt(6))]],
         txt_y=258, txt_h=132, styles=PP, letters=("CRISE",), strips=3,
         why="ouverture sur les jeunes de Valence de dos qui applaudissent (personne ne parle à l'image) + foule émeraude + salle de dos, tirages scotchés, un de plus sur les frappes"),
    dict(id="A2", kind="cut", src="HUMA", sync=True, bgs=[BLACK, EMER, WHITE, BLACK], ghost=EMER, box=HUMA_SYNC, scale=(1.40, 1.44),
         txt=[[("HUMAINE", wt(7))], [("QUE", wt(8)), ("VOTRE", wt(9))], [("GÉNÉRATION,", wt(10))]],
         txt_y=258, txt_h=128, styles=PP, strips=3, strip_zones=TOPZ,
         why="Huma, plan synchro (« humaine que votre génération ») : Mélenchon découpé N&B jusqu'au pupitre, contour autocollant, double tramé émeraude"),
    dict(id="A3", kind="cut", src="HUMA", sync=True, bgs=[EMER, WHITE, BLACK, EMER], ghost=BLACK, box=HUMA_SYNC, scale=(1.44, 1.48),
         txt=[[("JEUNES", wt(11)), ("GENS,", wt(12))], [("VA", wt(13)), ("NON", wt(14)), ("SEULEMENT", wt(15))], [("DEVOIR", wt(16)), ("AFFRONTER,", wt(17))],
              [("MAIS", wt(18)), ("RÉGLER.", wt(19))]],
         txt_y=258, txt_h=118, styles=PP, strips=4, strip_zones=TOPZ,
         why="Huma, plan synchro (« jeunes gens, va non seulement devoir affronter, mais régler ») : découpe N&B sur aplat qui change sur les frappes, double tramé noir"),
    # ---- après le drop : musique seule, un carton complet par plan, dans l'ordre de la phrase, jamais répété ----
    dict(id="B1", kind="cut", src="HUMA", t=49.60, bgs=[EMER, BLACK, EMER, WHITE], box=HUMA_HAND, scale=(1.45, 1.49), flash=True, ghost=WHITE,
         txt=[[("UNE", 0.0), ("CRISE", 0.0)], [("DE LA CIVILISATION", TB * 2)], [("HUMAINE", TB * 4)]], txt_y=258, txt_h=140, styles=PP,
         letters=("CRISE", "HUMAINE"), strips=4, strip_zones=TOPZ,
         why="drop : flash blanc 3 images, Fête de l'Huma main ouverte découpé N&B sur émeraude puis noir, gros mots découpés qui tombent sur les frappes"),
    dict(id="B2", kind="collage", bg=BLACK,
         photos=[("VALJ", 24.00, CROWD_F, 860, (540, 1110), -3, 0.0, "mono"), ("VALJ", 11.50, CROWD_W, 620, (600, 1560), 5, TB, "emer")],
         txt=[[("VOTRE", 0.0)], [("GÉNÉRATION", 0.07)]], txt_y=300, txt_h=180, styles=PP, letters=("VOTRE",), strips=3,
         why="foule de Valence (drapeaux) en tirage N&B + tirage émeraude, sur noir"),
    dict(id="B3", kind="collage", bg=EMER,
         photos=[("VALJ", 63.40, BACKS2, 880, (540, 1120), 2, 0.0, "mono"), ("VALJ", 26.00, CROWD_F, 540, (330, 1600), -6, TB, "mono")],
         txt=[[("JEUNES", 0.0)], [("GENS", 0.07)]], txt_y=290, txt_h=210, styles=PP, letters=("JEUNES", "GENS"), strips=3,
         why="la salle de Valence de dos face à la scène + foule, sur émeraude"),
    dict(id="B4", kind="cut", src="HUMA", t=45.50, bgs=[WHITE, EMER, WHITE], box=HUMA_ARMS, scale=(1.40, 1.44), ghost=EMER, pt=(0.42, 0.75),
         txt=[[("VA NON SEULEMENT", 0.0)], [("DEVOIR", 0.1)], [("AFFRONTER", 0.2)]], txt_y=258, txt_h=140, styles=PP,
         strips=4, strip_zones=TOPZ,
         why="Fête de l'Huma bras ouverts (autre moment), découpé N&B sur papier blanc, double tramé émeraude"),
    dict(id="B5", kind="full", src="VALJ", t=13.20, crop=(720, 580, 1000), push=(1.0, 1.05), focus=(720, 600),
         txt=[[("MAIS", 0.0)], [("RÉGLER.", 0.07)]], txt_y=560, txt_h=240, styles=PP, letters=("RÉGLER.",), txt_maxw=0.80,   # 0,80 : le pop (+12 %) et le tremblé restent dans x 0,17-0,83 (retour HD)
         why="la foule de Valence plein cadre en N&B, bords déchirés ; MAIS RÉGLER. en grosses lettres découpées"),
    dict(id="B6", kind="sil", src="HUMA", t=65.20, bg=EMER, ghost=BLACK, box=HUMA_REACH, scale=(1.72, 1.77),
         strips=4, strip_zones=TOPZ,
         why="Fête de l'Huma, bras tendu : silhouette blanche 3 images puis Mélenchon N&B sur émeraude, sans texte"),
    dict(id="FIN", kind="card", bg=WHITE, push=(1.0, 1.035),
         big=[("JEAN-LUC", 0.0, rgb(BLACK)), ("MÉLENCHON", TB * 2, rgb(EMER_D)), ("2027", TB * 4, rgb(BLACK))],
         big_y=560, big_sizes=[300, 300, 430], big_font="impact",
         why="carton final propre (papier blanc déchiré scotché sur émeraude, noir + émeraude) : son nom et 2027 (année de l'élection)"),
]
BOUNDS_T = [0] + CUTF + [ENDF]
assert len(BOUNDS_T) == len(SHOTS) + 1, (len(BOUNDS_T), len(SHOTS))
for i, sh in enumerate(SHOTS):
    sh["a"], sh["bb"] = BOUNDS_T[i], BOUNDS_T[i + 1]; sh["n"] = sh["bb"] - sh["a"]; sh["clip"] = "R9_%s.mov" % sh["id"]
    if sh.get("sync"): sh["t"] = V_SRC0 + sh["a"] / FPS                     # plans synchro avec la voix
assert min(sh["n"] for sh in SHOTS) >= 15, [(s["id"], s["n"]) for s in SHOTS]
SCENES = {"HUMA": [4.58, 70.64, 79.92, 105.22], "VALJ": [5.6, 15.7, 19.9, 23.73, 29.1, 59.9, 66.3]}
for sh in SHOTS:                                                         # coupes des captations (ffmpeg scene) : jamais dans la partie visible
    items = [(p[0], p[1], p[6]) for p in sh.get("photos", [])]
    if sh.get("src"): items.append((sh["src"], sh["t"], 0.0))
    for src, t0, ap in items:
        v0, v1 = t0 + ap, t0 + sh["n"] / FPS
        assert not any(v0 - 0.05 < c < v1 + 0.05 for c in SCENES[src]), ("coupe de la source dans", sh["id"], src, t0, v0, v1)
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
CARD_PAPER = None
def card_paper():
    """Feuille blanche déchirée scotchée sur aplat émeraude (carton final)."""
    global CARD_PAPER
    if CARD_PAPER is None:
        rng = np.random.default_rng(5); img = paper(EMER)
        m = torn_mask(1500, 900, rng, rough=10, step=16, inset=10); body = paper(WHITE)[:1500, :900]
        sh = cv2.GaussianBlur(m, (0, 0), 8) * 0.5
        x0, y0 = 90, 210
        img[y0 + 12:y0 + 1512, x0 + 10:x0 + 910] *= (1 - sh[..., None])
        img[y0:y0 + 1500, x0:x0 + 900] = img[y0:y0 + 1500, x0:x0 + 900] * (1 - m[..., None]) + body * m[..., None]
        CARD_PAPER = img
    return CARD_PAPER.copy()
CTL = {}
def render(sh):
    n = sh["n"]; a = sh["a"]; frames = []
    rel = lambda t: sh["a"] / FPS + t
    sync = sh["id"].startswith("A")                                          # textes des plans A : temps absolus de la voix
    tpos = lambda p: [(im, cx, cy, (max(t, sh["a"] / FPS) if sync else rel(t))) for im, cx, cy, t in p]
    txt = tpos(board(sh["txt"], sh["txt_y"], seed=skey(sh["id"]) * 7, styles=sh["styles"], letters=sh.get("letters", ()),
                     h=sh.get("txt_h", 118), maxw=(XMAX - XMIN - 30) * sh.get("txt_maxw", 1.0))) if sh.get("txt") else []
    big = []
    if sh.get("big"):
        big = [(im, cx, cy, rel(t)) for im, cx, cy, t in
               big_text([(s, t, c) for s, t, c in sh["big"]], sh["big_y"], sizes=sh["big_sizes"], spec=((S + "Impact.ttf", 0) if sh.get("big_font") else FCOND),
                        maxw=(XMAX - XMIN) * 0.86)]
    photos = []
    for j, p in enumerate(sh.get("photos", [])):
        ps, pt, pbox, pw, pc, pa, pt0, pk = p[:8]
        photos.append(Photo(read_frames(ps, pt, n), pbox, pw, pc, pa, fr(rel(pt0)), (sh["id"], j), pk))
    strips = make_strips(sh)
    k0 = nbeat(a)
    if sh["kind"] in ("cut", "sil", "full"):
        raw = read_frames(sh["src"], sh["t"], n)
    if sh["kind"] in ("cut", "sil"):
        key = "%s_%s_%.2f_%d_%s" % (sh["id"], sh["src"], sh["t"], n, "-".join(map(str, sh["box"])))
        ms = dc_masques(raw, sh["box"], sh.get("pt", (0.5, 0.75)), CACHE + "dc/" + key)
        ctl = [dc_controle(m) for m in ms]
        CTL[sh["id"]] = dict(gauche=max(c["gauche"] for c in ctl), droite=max(c["droite"] for c in ctl), haut=max(c["haut"] for c in ctl),
                             morceaux=sorted(set(c["morceaux"] for c in ctl)), bas_net_min=min(c["bas_net"] for c in ctl))
        print("    controle %s : %s (bas posé sur le bas du cadre)" % (sh["id"], CTL[sh["id"]]), flush=True)
        dc_planche(raw, ms, sh["box"], CACHE + "planche_%s.jpg" % sh["id"])
        hx = np.array([head_x(m) for m in ms], np.float32) + sh["box"][0]     # la tête suit (lissée), centrée hors des boutons
        hx = np.convolve(np.pad(hx, 10, mode="edge"), np.ones(21) / 21, "valid")
    for i in range(n):
        f = a + i; u = i / max(n - 1, 1); kb = nbeat(f) - k0
        if sh["kind"] == "full":
            cx, cy, vh = sh["crop"]; z = sh["push"][0] + (sh["push"][1] - sh["push"][0]) * u
            s = H / vh * z; fx_, fy_ = sh["focus"]
            ccx = cx + (fx_ - cx) * (1 - 1 / z); ccy = cy + (fy_ - cy) * (1 - 1 / z)
            M = np.float32([[s, 0, W / 2 - ccx * s], [0, s, H / 2 - ccy * s]])
            img = mono(cv2.warpAffine(raw[i], M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE))
        elif sh["kind"] == "card":
            img = card_paper()
        else:
            img = paper(sh["bgs"][kb % len(sh["bgs"])] if sh.get("bgs") else sh["bg"])   # aplat qui change sur les frappes
        for st in strips:                                                   # une bande de plus à chaque frappe
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
            x0, y0, x1, y1 = sh["box"]; sc = sh["scale"][0] + (sh["scale"][1] - sh["scale"][0]) * u
            m = ms[i]; hh = (y1 - y0) * sc
            ccx = W / 2 + ((x1 - x0) / 2 - (hx[i] - x0)) * sc; ccy = H - hh / 2          # buste posé sur le bas du cadre
            st_ = np.dstack([np.ones((m.shape[0], m.shape[1], 3), np.float32) * np.array([0.97, 0.97, 0.96], np.float32), sticker(m, 8)])
            sd = st_.copy(); sd[..., :3] = 0; sd[..., 3] = cv2.GaussianBlur(st_[..., 3], (0, 0), 6) * 0.55
            if sh.get("ghost"):                                             # double tirage tramé, décalé, qui saute sur les temps
                gdx, gdy, gda = jit((sh["id"], "g"), nbeat(f), amp=10, ang=1.0)
                paste(img, ghost_rgba(raw[i], m, sh["box"], sc, sh["ghost"]), ccx + 46 + gdx, ccy - 30 + gdy, 1.08, -2.5 + gda)
            paste(img, sd, ccx + 12, ccy + 10, sc)
            if sh["kind"] == "sil" and i < 3: paste(img, cutout_rgba(raw[i], m, sh["box"], white=True), ccx, ccy, sc)   # silhouette blanche : 3 images
            else: paste(img, st_, ccx, ccy, sc); paste(img, cutout_rgba(raw[i], m, sh["box"]), ccx, ccy, sc)
        if sh["kind"] == "full":
            te = torn_edges(); img = img * (1 - te[..., 3:4]) + te[..., :3]
        draw_pieces(img, txt, f, boil=sh["id"])
        if sh["kind"] == "card":
            for j, (tx, ty, ta) in enumerate(((150, 230, -32), (930, 230, 30), (150, 1690, 28), (930, 1690, -30))):
                paste(img, CARD_TAPES[j], tx, ty, 1.0, ta)
            z = sh["push"][0] + (sh["push"][1] - sh["push"][0]) * u
            for im, cx, cy, t in big:
                s_ = pop(f, fr(t))
                if s_ is not None: paste(img, im, W / 2 + (cx - W / 2) * z, H / 2 + (cy - H / 2) * z, s_ * z)
        if sh.get("flash") and i < 3: img = img + (1 - img) * [1.0, 0.6, 0.25][i]   # aplat blanc : flash de transition (1 image pleine + 2 de fondu)
        frames.append(finish(img, f))
    write_mov(frames, OUT + sh["clip"])
    print("  %-4s %3d im  (%s)" % (sh["id"], n, sh["kind"]), flush=True)

# ---------------- audio ----------------
VGAIN = 7.0                                   # voix de la captation faible (-23,5 LUFS) : +7 dB, musique ≈ 10 dB dessous
def make_audio():
    import soundfile as sf
    sr = 48000; N = int(round(END * sr))
    def grab(path, t, dur):
        p = subprocess.run([FF, "-v", "error", "-ss", "%.3f" % t, "-t", "%.3f" % dur, "-i", path, "-ac", "2", "-ar", str(sr), "-f", "f32le", "-"], capture_output=True)
        return np.frombuffer(p.stdout, np.float32).reshape(-1, 2).copy()
    voix = np.zeros((N, 2), np.float32); mus = np.zeros((N, 2), np.float32)
    v = grab(HG + "/" + SRC["HUMA"][0], V_IN, V_OUT - V_IN); env = np.ones(len(v), np.float32)
    k = int(0.03 * sr); env[:k] = np.linspace(0, 1, k); k = int(0.08 * sr); env[-k:] = np.linspace(1, 0, k)
    i0 = int(round(t_of_src(V_IN) * sr)); voix[i0:i0 + len(v)] = v * env[:, None] * 10 ** (VGAIN / 20)
    m = music_raw(MUSIC_IN)[:N]
    t = np.arange(len(m)) / sr; vend = t_of_src(36.94); dr = CUTS[2]
    # sous la phrase : partie guitare sans basse à -16 dB, montée -> -9 dB à la fin de la phrase, drop à -4 dB (voix et refrain au même niveau perçu)
    gdb = np.interp(t, [0, 0.25, 4.0, vend, dr - 0.03, dr, END], [-26, -16, -15, -9, -7, -4, -4])
    k = int(0.30 * sr); fo = np.ones(len(m), np.float32); fo[-k:] = np.linspace(1, 0, k)
    mus[:len(m)] = m * (10 ** (gdb / 20) * fo)[:, None]
    sf.write(OUT + "R9-voix.wav", voix, sr, subtype="PCM_24"); sf.write(OUT + "R9-musique.wav", mus, sr, subtype="PCM_24")
    sf.write(D + "tmp_mix.wav", voix + mus, sr, subtype="FLOAT")
    r = subprocess.run([FF, "-hide_banner", "-i", D + "tmp_mix.wav", "-af", "loudnorm=I=-14:TP=-2.5:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    js = json.loads(r[r.rindex("{"):r.rindex("}") + 1])
    af = ("loudnorm=I=-14:TP=-2.5:LRA=11:measured_I=%s:measured_TP=%s:measured_LRA=%s:measured_thresh=%s:offset=%s:linear=true,"
          "aresample=48000" % (js["input_i"], js["input_tp"], js["input_lra"], js["input_thresh"], js["target_offset"]))
    subprocess.run([FF, "-v", "error", "-y", "-i", D + "tmp_mix.wav", "-af", af, "-c:a", "pcm_s24le", OUT + "R9-mix.wav"], check=True)
    os.remove(D + "tmp_mix.wav"); print("audio : mix avant normalisation", js["input_i"], "LUFS")

# ---------------- plan ----------------
PHRASE = "Alors c'est une crise de la civilisation humaine que votre génération, jeunes gens, va non seulement devoir affronter, mais régler."
PAROLES = ("aucune parole écrite (consigne Luca) : sous la phrase, fin du 1er couplet (partie guitare sans basse, baissée) ; "
           "au drop, le 1er refrain (32,74-42,88 s du morceau, entrée de la basse 808)")
def build_plan():
    video = []
    for sh in SHOTS:
        v = {"id": sh["id"], "clip": sh["clip"], "folder": "genR9", "path": OUT + sh["clip"], "s": 0, "e": sh["n"], "rec": sh["a"], "dur": sh["n"],
             "clip_fps": FPS, "speed_pct": 100, "track": 1, "note": sh["why"], "kind": sh["kind"], "temps": round(sh["n"] / FPS / T, 2)}
        if sh.get("src"):
            path, sfps, url, off, ctx = SRC[sh["src"]]
            v["source"] = {"fichier": path, "in_s": round(sh["t"], 3), "out_s": round(sh["t"] + sh["n"] / FPS, 3), "fps": sfps, "url": url,
                           "t_youtube_s": round(off + sh["t"], 2), "contexte": ctx, "synchro_voix": bool(sh.get("sync"))}
        if sh["id"] in CTL: v["decoupe"] = dict(outil="_claude/outils/decoupe.py", cadre=sh["box"], **CTL[sh["id"]])
        if sh.get("photos"):
            v["photos"] = [{"fichier": SRC[p[0]][0], "in_s": round(p[1], 3), "cadre_source": p[2], "tirage": p[7], "url": SRC[p[0]][2],
                            "t_youtube_s": round(SRC[p[0]][3] + p[1], 2)} for p in sh["photos"]]
        video.append(v)
    texts = []
    for sh in SHOTS:
        for line in sh.get("txt", []): texts.append({"plan": sh["id"], "texte": " ".join(w for w, _ in line)})
        for s_, t_, c_ in sh.get("big", []): texts.append({"plan": sh["id"], "texte": s_})
    yt = SRC["HUMA"][3]
    plan = {"name": "R9 - Collage ransom-note émeraude - Jean-Luc Mélenchon (jeunesse)", "fps": FPS, "w": W, "h": H, "duree_s": round(END, 3),
            "note": "Plans ProRes 9:16 composés en Python (lot7/_claude/gen/R9/out) : Mélenchon détouré (_claude/outils/decoupe.py) en N&B, buste "
                    "jusqu'au pupitre posé sur le bas du cadre (visage dans la zone sûre TikTok), contour autocollant, double tirage tramé, aplats "
                    "émeraude / noir / blanc qui changent sur les frappes, bandes, scotch, tirages N&B et émeraude, silhouette blanche 3 images, foule "
                    "plein cadre, textes ransom-note cuits. s/e en images du clip (30 i/s), rec en images timeline. Coupes sur les frappes réelles de "
                    "Meuda (out/R9-frappes.json). Aucun ralenti. Générateur : genR9.py",
            "phrase": {"texte": PHRASE, "url": SRC["HUMA"][2], "source": SRC["HUMA"][0], "in_s": 29.20, "out_s": 36.94,
                       "t_youtube_s": [round(yt + 29.20, 2), round(yt + 36.94, 2)],
                       "timeline_s": [round(t_of_src(29.20), 2), round(t_of_src(36.94), 2)],
                       "voix": "son direct de la Fête de l'Huma, images synchro (plan continu 4,58-70,64 s) ou foule de Valence où personne ne parle ; "
                               "coupée après « régler » avant « et que nous tous… » (sens gardé)"},
            "musique": {"fichier": "lot7/sons/R9-tiakola-meuda_complet.wav", "titre": "Tiakola - Meuda", "url": SON_URL,
                        "debut_complet_s": round(MUSIC_IN, 4), "fin_complet_s": round(MUSIC_IN + END, 3), "drop_timeline_s": round(CUTS[2], 4),
                        "coupes_frappes_s": [round(c, 4) for c in CUTS], "coupes_images": CUTF},
            "textes": texts, "video": video,
            "audio": [{"id": "mix", "clip": "R9-mix.wav", "folder": "genR9", "path": OUT + "R9-mix.wav", "rec": 0, "track": 1,
                       "note": "mix -14 LUFS : voix %.2f-%.2f s (%+g dB) à %.2f s ; Meuda dès %.3f s du complet, -16 dB sous la voix, montée, "
                               "-4 dB au drop, fondu de fin 0,3 s" % (V_IN, V_OUT, VGAIN, t_of_src(V_IN), MUSIC_IN)}],
            "stems": ["lot7/_claude/gen/R9/out/R9-voix.wav", "lot7/_claude/gen/R9/out/R9-musique.wav"],
            "logos_exclus": "Huma : pupitre FÊTE DE L'HUMA sous la découpe (cadres y < 815) ; Valence : filigrane MELENCHON 2027.fr (haut droite) hors de tous les cadres"}
    json.dump(plan, open(D + "plan-R9.json", "w"), indent=1, ensure_ascii=False)
    son = {"id": "R9", "titre": "Meuda", "artiste": "Tiakola", "url": SON_URL,
           "chaine": "TIAKOLA (chaîne officielle certifiée, « Tiakola - Meuda (Clip officiel) »)",
           "fichier": "lot7/sons/R9-tiakola-meuda_complet.wav",
           "extrait_complet_s": {"debut": round(MUSIC_IN, 4), "fin": round(MUSIC_IN + END, 3)},
           "paroles_audibles": PAROLES, "bpm": round(60 / T, 1), "temps_s": T,
           "structure_s": {"partie_sans_basse": [0, 32.7], "refrain_1": [32.74, 56.5], "refrain_2": [86.1, 110.6], "refrain_3_partiel": [141.6, 151.5]},
           "drop": {"complet_s": round(MUSIC_IN + CUTS[2], 4), "timeline_s": round(CUTS[2], 4),
                    "nature": "entrée de la basse 808 sur le 1er refrain (le refrain revient à 86 s et 141 s du morceau)"},
           "frappes_timeline_s": BEATS, "coupes_sur_frappes_s": [round(c, 4) for c in CUTS],
           "mix": "lot7/_claude/gen/R9/out/R9-mix.wav"}
    json.dump(son, open(D + "son.json", "w"), indent=1, ensure_ascii=False)

# ---------------- aperçu 540x960 ----------------
def apercu():
    plan = json.load(open(D + "plan-R9.json")); ins = []; fl = []
    for i, v in enumerate(plan["video"]):
        ins += ["-i", OUT + v["clip"]]
        fl.append("[%d:v]trim=start_frame=%d:end_frame=%d,setpts=PTS-STARTPTS,scale=540:960,setsar=1[v%d]" % (i, v["s"], v["e"], i))
    k = len(plan["video"]); fl.append("".join("[v%d]" % i for i in range(k)) + "concat=n=%d:v=1:a=0[v]" % k)
    ins += ["-i", OUT + "R9-mix.wav"]; out = HG + "/preview/apercu-R9.mp4"
    subprocess.run([FF, "-v", "error", "-y"] + ins + ["-filter_complex", ";".join(fl), "-map", "[v]", "-map", "%d:a" % k,
                    "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "aac", "-b:a", "192k", "-shortest", out], check=True)
    print("aperçu", out)
# ---------------- mesure sur l'export : coupes vs frappes, LUFS / TP ----------------
def mesure():
    out = HG + "/preview/apercu-R9.mp4"
    r = subprocess.run([FF, "-v", "info", "-i", out, "-vf", "scale=135:240,select='gt(scene,0.25)',showinfo", "-an", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    cuts = [float(x) for x in re.findall(r"pts_time:([0-9.]+)", r)]
    p = subprocess.run([FF, "-v", "error", "-i", out, "-vn", "-ac", "2", "-ar", "48000", "-f", "f32le", "-"], capture_output=True)
    y = np.frombuffer(p.stdout, np.float32).reshape(-1, 2)
    import soundfile as sf                                                # recalage de l'export (délai AAC) sur le mix posé
    mx, _ = sf.read(OUT + "R9-mix.wav", dtype="float32"); a0, a1 = int((CUTS[2] + 0.5) * 48000), int((CUTS[2] + 6.5) * 48000)
    best = max(range(-960, 961, 8), key=lambda d: float(np.dot(y[a0 + d:a1 + d].mean(1), mx[a0:a1].mean(1))))
    best = max(range(best - 8, best + 9), key=lambda d: float(np.dot(y[a0 + d:a1 + d].mean(1), mx[a0:a1].mean(1))))
    print("décalage audio export / mix posé : %+.2f ms" % (best / 48.0))
    i0 = int((CUTS[2] - 0.3) * 48000)
    h_all = [x[0] for x in detect_hits(y[:i0]) if x[3] > 0.004] + [x[0] + i0 / 48000 for x in detect_hits(y[i0:]) if x[3] > 0.005]
    STEM_HITS = [x[0] for x in detect_hits(sf.read(OUT + "R9-musique.wav", dtype="float32")[0][:int((CUTS[2] - 0.3) * 48000)]) if x[3] > 0.002]
    print("coupes image détectées (export) :", cuts)
    worst = 0
    for c in [fr_ / FPS for fr_ in CUTF]:
        det = min(cuts, key=lambda x: abs(x - c)) if cuts else None
        k = min(h_all, key=lambda t: abs(t - c)); how = "détecteur sur l'export"
        if abs(c - k) > 0.02 and c < CUTS[2] - 0.05:                      # avant le drop la voix masque les pincements de guitare :
            k = min(STEM_HITS, key=lambda t: abs(t - c)) + best / 48000.0; how = "frappe de la piste musique, export recalé"
        e = (c - k) * 1000; worst = max(worst, abs(e))
        print("  coupe %.3f (détectée %s)  frappe %.4f  écart %+.1f ms  [%s]" % (c, "%.3f" % det if det is not None else "-", k, e, how))
    print("écart max coupes/frappes : %.1f ms" % worst)
    r = subprocess.run([FF, "-hide_banner", "-i", out, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    print(r[r.rindex("Summary"):])
if __name__ == "__main__":
    args = set(a for a in sys.argv[1:] if not a.startswith("only=")) or {"shots", "audio", "plan", "apercu"}
    only = [x for a in sys.argv[1:] if a.startswith("only=") for x in a.split("=", 1)[1].split(",")]
    print("musique dès %.4f s ; coupes (s) :" % MUSIC_IN, [round(c, 4) for c in CUTS], "images :", CUTF, "fin", END)
    print("frappes visibles :", BEATS)
    if "shots" in args or only:
        for sh in SHOTS:
            if not only or sh["id"] in only: render(sh)
    if "audio" in args: make_audio()
    if "plan" in args: build_plan()
    if "apercu" in args: apercu()
    if "mesure" in args: mesure()
