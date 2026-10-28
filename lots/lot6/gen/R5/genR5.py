# R5 (lot 6) — Collage ransom-note POP, Antoine Léaument, son Justice – D.A.N.C.E. (audio officiel, chaîne Justice).
# Modèle : lot5/_claude/gen/R1/genR1.py (découpe Vision, morceaux de texte penchés serif/sans, frappes, carton final), poussé plus loin :
#   - aplats pop qui changent à CHAQUE frappe, avec une 2e feuille déchirée (bord blanc fibreux + ombre) tramée Ben-Day ;
#   - silhouette « mal repérée » (aplat de couleur décalé derrière la découpe, façon sérigraphie pop) + contour autocollant ;
#   - plan « echo » : 3 silhouettes en aplats décalés (multiples pop) + la découpe couleur ;
#   - photos en bichromie (trame magazine) bord déchiré + scotch ; bandes de papier qui s'empilent sur les frappes ;
#   - lettres de magazine (mots-clés lettre par lettre), aplat blanc plein cadre seulement en flash de 3 images (drop, plan plein cadre).
# Phrase (son direct, plan synchro) : « Mais la peur, vous vous en nourrissez. Pire, vous la suscitez et vous l'exploitez pour des
#   motifs politiciens pour une raison simple. Quand la peur règne, on peut gouverner par la force. » (tribune de l'Assemblée,
#   16/06/2026, chaîne La France insoumise à l'Assemblée nationale, youtu.be/4CPac_uArQ0, 24,76-32,96 s)
#   -> autre phrase que G3 (221,8-226,9 s, policiers) et P1 (interview grève Ubisoft).
# Son : D.A.N.C.E., montée basse/kick (25,5-34,3 s du morceau) filtrée sous la phrase, drop = entrée du beat plein sur
#   « Do the D.A.N.C.E. » (34,28 s), puis coupes toutes les 2 temps sur les kicks réels.
# Usage : python genR5.py [shots] [audio] [plan] [apercu] [mesure] [only=ID,ID]   (sans argument = tout sauf mesure)
import sys
sys.dont_write_bytecode = True
import os, json, subprocess, math, re
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
HG = "/Users/luca.grousset/Movies/highkey-gauchiste"
D = HG + "/lot6/_claude/gen/R5/"; OUT = D + "out/"; CACHE = D + "cache/"; os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, D)
from hits import detect_hits
FF = "/opt/homebrew/bin/ffmpeg"; SEG = HG + "/_claude/outils/segment"; FPS = 30; W, H = 1080, 1920
def fr(t): return int(round(t * FPS))
def hexc(h): h = h.lstrip("#"); return np.array([int(h[4:6], 16), int(h[2:4], 16), int(h[0:2], 16)], np.float32) / 255   # BGR
def rgb(h): h = h.lstrip("#"); return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
# palette pop R5 (aucune couleur de R1 : ni violet, ni bleu marine, ni rouge, ni crème)
ROSE, TURQ, ORANGE, BLEU, CITRON, LILAS, NOIR, BLANC = "#FF3E9A", "#00BFC9", "#FF6A13", "#2F4BFF", "#FFE53B", "#B98CFF", "#141414", "#FFF8EE"
CYCLE = [ROSE, TURQ, ORANGE, BLEU, CITRON, LILAS]

# ---------------- sources (lecture seule) ----------------
SRC = {
    "AN": ("lot2/sources/G3-leaument-an-securite-2026-06.mp4", 25.0, "https://www.youtube.com/watch?v=4CPac_uArQ0",
           "tribune de l'Assemblée, loi antiterroriste, 16/06/2026 (chaîne La France insoumise à l'Assemblée nationale)"),
    "CH": ("lot3/sources/P1-leaument-lcp-chenu-2026-01b.mp4", 24000 / 1001, "https://youtu.be/5VJWCXdOKyg",
           "LCP, hémicycle 22/01/2026, debout, réplique au RN (extrait P1, autres images)"),
    "BU": ("lot3/sources/P1-leaument-bureau-2026-06.mp4", 24000 / 1001, "https://youtu.be/mvSD-5YHhlk",
           "chaîne officielle, « La campagne de la victoire ! » 13/06/2026, face caméra au bureau (extrait P1, autres images)"),
    "GR": ("lot3/sources/P1-leaument-interview-greve-2026-02.mp4", 60.0, "https://youtu.be/EA4uU-DL4uM",
           "Point'n Think, interview pendant la grève Ubisoft 10/02/2026, écharpe tricolore (extrait P1, autres images)"),
    "QAG": ("lot2/sources/G3-leaument-lcp-qag-2026-04.mp4", 25.0, "https://www.youtube.com/watch?v=CwaWePGUP8w",
            "LCP, questions au gouvernement 28/04/2026, plan large de l'hémicycle (sans incrustations)"),
}

# ---------------- musique : Justice – D.A.N.C.E. ----------------
SON_FILE = HG + "/lot6/sons/R5-justice-dance_complet.wav"; SON_URL = "https://www.youtube.com/watch?v=tCnBrrnOefs"
MDROP = 34.284                        # entrée du beat plein sur « Do the D.A.N.C.E. » (kick le plus fort du début du morceau)
DROP = 8.75; T = 60 / 112.35          # 112,35 BPM (librosa)
MUSIC_IN0 = MDROP - DROP
END = 18.90
# coupes : kicks réels de la montée (toutes les 2 temps), drop, puis toutes les 2 temps (4 temps dans le break « Do the dance » sans kick)
CUT_SONG = [27.940, 30.073, 32.216, MDROP, 35.352, 36.459, 37.480, 38.541, 39.643, 40.666, 42.829]
CUT_T = [c - MUSIC_IN0 for c in CUT_SONG]
HITS_JSON = OUT + "R5-frappes.json"
def music_raw(mi, dur=END + 0.5, sr=48000):
    import soundfile as sf
    i0 = int(round(mi * sr)); x, r = sf.read(SON_FILE, start=i0, frames=int(dur * sr), dtype="float32"); assert r == sr; return x
def kicks_of(h): return [x[0] for x in h if x[1] == "kick" and x[3] > 0.12]
def snap_list(ks, targets, tol=0.045):
    out = []
    for t in targets:
        c = min(ks, key=lambda k: abs(k - t)); assert abs(c - t) < tol, ("pas de kick près de", t, c); out.append(c)
    return out
def frappes():
    if os.path.exists(HITS_JSON):
        js = json.load(open(HITS_JSON))
        if js["cle"] == [MUSIC_IN0, END, CUT_T]: return js["music_in"], js["frappes"]
    best, bad = None, 9
    for off in np.arange(-0.016, 0.0165, 0.001):
        h = detect_hits(music_raw(MUSIC_IN0 + off))
        try: cuts = snap_list(kicks_of(h), [c - off for c in CUT_T])
        except AssertionError: continue                                    # détection instable à ce décalage : on passe
        e = max(abs(c - round(c * FPS) / FPS) for c in cuts)
        if e < bad: best, bad, hb = off, e, h
    mi = MUSIC_IN0 + best
    json.dump({"cle": [MUSIC_IN0, END, CUT_T], "music_in": mi, "frappes": hb}, open(HITS_JSON, "w")); return mi, hb
MUSIC_IN, HITS = frappes()
FINE = 0.0                            # recalage fin mesuré sur l'export AAC (écart max coupes/kicks < 20 ms)
MUSIC_IN += FINE; HITS = [[h[0] - FINE] + list(h[1:]) for h in HITS]
KICKS = kicks_of(HITS)
CUTS = snap_list(KICKS, [c - (MUSIC_IN - MUSIC_IN0) for c in CUT_T]); CUTF = [fr(c) for c in CUTS]
DROPT = CUTS[3]; TB = T

# ---------------- voix ----------------
V_SRC0 = 24.40                        # source AN à t = 0 (« mais » 24,76 -> 0,36 s)
V_IN, V_OUT = 24.66, 33.10            # « mais » … « force » (fin 32,96) ; « L'instrumentalisation » (33,22) non gardé
def t_of_src(s): return s - V_SRC0
WORDS = [("MAIS", 24.76), ("LA", 24.96), ("PEUR", 25.12), ("VOUS", 25.58), ("VOUS", 25.64), ("EN", 25.80), ("NOURRISSEZ", 25.94),
         ("PIRE", 26.48), ("VOUS", 26.86), ("LA", 26.94), ("SUSCITEZ", 27.08), ("ET", 27.58), ("VOUS", 28.00), ("L'EXPLOITEZ", 28.10),
         ("POUR", 28.54), ("DES", 28.74), ("MOTIFS", 28.84), ("POLITICIENS", 29.16), ("POUR", 29.68), ("UNE", 29.84), ("RAISON", 29.96),
         ("SIMPLE", 30.18), ("QUAND", 30.90), ("LA", 31.06), ("PEUR", 31.18), ("RÈGNE", 31.36), ("ON", 31.76), ("PEUT", 31.82),
         ("GOUVERNER", 31.94), ("PAR", 32.30), ("LA", 32.46), ("FORCE", 32.58)]
def wt(i): return t_of_src(WORDS[i][1])
def W_(i): return (WORDS[i][0], wt(i))

# ---------------- beats : frappes réelles (avant le drop : kicks de la montée toutes les 2 temps ; après : chaque temps) ----------------
def beat_grid():
    pre = [k for k in KICKS if 0.1 < k < DROPT - 0.2]
    main = []
    for j in range(1, 12):                                                 # kicks principaux de la montée (2 temps)
        g = DROPT - 2 * j * T
        if g < 0.1: break
        c = min(pre, key=lambda k: abs(k - g - 0.06))
        if abs(c - g - 0.06) < 0.08: main.append(c)
    post = []
    for j in range(0, 40):
        g = DROPT + j * T
        if g > END: break
        c = min(KICKS, key=lambda k: abs(k - g))
        post.append(c if abs(c - g) < 0.045 else g)                        # break sans kick : grille d'un temps
    return sorted(b for b in set(main + post) if b > 0.4)
BEATS = beat_grid(); BEATF = [fr(b) for b in BEATS]
def nbeat(f): return sum(1 for b in BEATF if b <= f)

# ---------------- polices ransom-note (accents vérifiés : cache/test/fonts.png) ----------------
S = "/System/Library/Fonts/Supplemental/"
FONTS = [(S + "Arial Black.ttf", 0), (S + "Georgia Bold.ttf", 0), (S + "Times New Roman Bold.ttf", 0), (S + "Impact.ttf", 0),
         (S + "Rockwell.ttc", 2), (S + "AmericanTypewriter.ttc", 2), (S + "Didot.ttc", 2),
         (S + "Bodoni 72.ttc", 2), (S + "Futura.ttc", 2)]
FCOND = (S + "Futura.ttc", 4)         # Futura Condensed ExtraBold
STYLES = [(rgb(BLANC), rgb(NOIR)), (rgb(NOIR), rgb(BLANC)), (rgb(ROSE), (255, 255, 255)), (rgb(CITRON), rgb(NOIR)),
          (rgb(TURQ), rgb(NOIR)), (rgb(BLEU), (255, 255, 255)), (rgb(ORANGE), rgb(NOIR)), ((255, 255, 255), rgb(ROSE)),
          ((232, 226, 210), rgb(NOIR)), (rgb(NOIR), rgb(CITRON))]
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
    j = lambda: rng.integers(-5, 6)
    d.polygon([(6 + j(), 6 + j()), (6 + w_ + j(), 6 + j()), (6 + w_ + j(), 6 + h_ + j()), (6 + j(), 6 + h_ + j())], fill=bg + (255,))
    d.text((6 + px - x0, 6 + py - min(y0, cap[1])), txt, font=f, fill=fg + (255,), anchor="ls")
    a = rot if rot is not None else rng.uniform(-5, 5)
    return im.rotate(a, resample=Image.BICUBIC, expand=True)
def word_img(word, h, rng, letters=False):
    if not letters: return chip(word, h, rng)
    parts = [chip(c, h * rng.uniform(0.92, 1.08), rng, rot=rng.uniform(-8, 8)) for c in word]
    wsum = sum(p.width for p in parts) - 12 * (len(parts) - 1); hh = max(p.height for p in parts) + 12
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
    return out                                                              # BGR + alpha, float
XMIN, XMAX, YMIN, YMAX = 0.19 * W, 0.81 * W, 0.13 * H, 0.74 * H          # zone sûre TikTok (0,17-0,83 / 0,12-0,75) + marge
def board(lines, y0, seed, h=112, letters=(), maxw=XMAX - XMIN - 30):
    """lines = [[(mot, t_apparition), …], …] -> liste de pièces placées (img, cx, cy, t)."""
    rng = np.random.default_rng(seed); pieces = []; y = y0
    for line in lines:
        imgs = [shadowed(word_img(w, h * (1.14 if w in letters else 1.0), rng, w in letters)) for w, _ in line]
        gap = 8; tot = sum(i.shape[1] for i in imgs) + gap * (len(imgs) - 1)
        sc = min(1.0, maxw / tot); lh = max(i.shape[0] for i in imgs) * sc
        x = W / 2 - tot * sc / 2 + rng.uniform(-16, 16); x = min(max(x, XMIN + 4), XMAX - 4 - tot * sc)
        for (w, t), im in zip(line, imgs):
            if sc < 1: im = cv2.resize(im, (int(im.shape[1] * sc), int(im.shape[0] * sc)), interpolation=cv2.INTER_AREA)
            pieces.append((im, x + im.shape[1] / 2, y + lh / 2, t)); x += im.shape[1] + gap * sc
        y += lh - 6
    for im, cx, cy, t in pieces:                                            # zone sûre (texte)
        assert XMIN - 2 <= cx - im.shape[1] / 2 and cx + im.shape[1] / 2 <= XMAX + 2, ("texte hors zone x", cx, im.shape)
        assert YMIN - 2 <= cy - im.shape[0] / 2 and cy + im.shape[0] / 2 <= YMAX + 2, ("texte hors zone y", cy, im.shape)
    return pieces
def big_text(lines, y0, spec=FCOND, maxw=XMAX - XMIN, sizes=None, contour=0):
    """Texte propre (carton final / gros mots du plan plein cadre) : lignes centrées, largeur max, retour [(img, cx, cy, t)]."""
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
def skey(x): return sum((i + 1) * ord(c) for i, c in enumerate(str(x)))
DOTS = None
def dots():
    """Trame Ben-Day plein cadre (points ronds en quinconce)."""
    global DOTS
    if DOTS is None:
        m = np.zeros((H, W), np.float32); st = 22; rng = np.random.default_rng(5)   # points un peu irréguliers : une rangée parfaite est lue « ...... »
        for y in range(0, H + st, st):
            for x in range((y // st % 2) * st // 2, W + st, st):
                cv2.circle(m, (x + int(rng.integers(-3, 4)), y + int(rng.integers(-3, 4))), int(rng.integers(5, 8)), 1.0, -1, cv2.LINE_AA)
        DOTS = m
    return DOTS
_noise = {}
def paper_noise(seed):
    if seed not in _noise:
        rng = np.random.default_rng(seed)
        n = cv2.resize(rng.standard_normal((48, 27)).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC)
        n2 = cv2.GaussianBlur(rng.standard_normal((H, W)).astype(np.float32), (0, 0), 1.2)
        _noise[seed] = (1 + 0.025 * n + 0.03 * n2)[..., None]
    return _noise[seed]
def torn_line_mask(rng, ya, yb, rough=10, step=9):
    """Masque de la feuille déchirée sous une ligne irrégulière allant de (0, ya) à (W, yb) + bande blanche de fibres + ombre."""
    xs = np.arange(-10, W + 20, step); ys = ya + (yb - ya) * (xs / W) + np.cumsum(rng.uniform(-rough, rough, len(xs))) * 0.35
    ys += rng.uniform(-rough, rough, len(xs))
    pts = [(int(x), int(y)) for x, y in zip(xs, ys)] + [(W + 20, H + 20), (-10, H + 20)]
    m = np.zeros((H, W), np.float32); cv2.fillPoly(m, [np.array(pts, np.int32)], 1.0, lineType=cv2.LINE_AA)
    pts2 = [(int(x), int(y - rng.uniform(5, 13))) for x, y in zip(xs, ys)] + [(W + 20, H + 20), (-10, H + 20)]
    fib = np.zeros((H, W), np.float32); cv2.fillPoly(fib, [np.array(pts2, np.int32)], 1.0, lineType=cv2.LINE_AA)
    sh = cv2.GaussianBlur(np.roll(fib, -10, axis=0), (0, 0), 7) * 0.45
    return m, fib, sh
_bg = {}
def background(k, sid):
    """Aplat pop de la frappe k : couleur pleine + 2e feuille déchirée tramée Ben-Day (bord blanc fibreux, ombre)."""
    key = (k, sid)
    if key in _bg: return _bg[key].copy()
    if len(_bg) > 3: _bg.clear()
    rng = np.random.default_rng(1000 + k * 7 + skey(sid) % 97)
    c1 = CYCLE[k % len(CYCLE)]; c2 = CYCLE[(k + 3) % len(CYCLE)]
    img = np.ones((H, W, 3), np.float32) * hexc(c1)[None, None, :] * paper_noise(k % 5)
    mode = k % 3
    ya, yb = (rng.uniform(1150, 1500), rng.uniform(950, 1350)) if mode != 2 else (rng.uniform(850, 1000), rng.uniform(1500, 1650))
    m, fib, sh = torn_line_mask(rng, ya, yb)
    if mode == 1: m, fib, sh = m[::-1], fib[::-1], np.roll(sh[::-1], 20, axis=0)   # feuille du haut
    sheet = hexc(c2)[None, None, :] * (1 - 0.15 * dots()[..., None]) * paper_noise((k + 2) % 5)
    img = img * (1 - sh[..., None])
    img = img * (1 - fib[..., None]) + hexc(BLANC)[None, None, :] * fib[..., None]
    img = img * (1 - m[..., None]) + sheet * m[..., None]
    _bg[key] = np.clip(img, 0, 1).astype(np.float32)
    return _bg[key].copy()
VIG = None
def finish(img, f):
    global VIG
    if VIG is None:
        y, x = np.mgrid[0:H, 0:W].astype(np.float32)
        r = np.sqrt(((x - W / 2) / (W / 2)) ** 2 + ((y - H / 2) / (H / 2)) ** 2) / np.sqrt(2)
        VIG = (1 - 0.22 * np.clip(r, 0, 1) ** 2.4)[..., None].astype(np.float32)
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
PALM = (940, 120, 1110, 420)          # palme dorée derrière la tribune (coordonnées source AN) : Vision la colle à la tête
FACES = HG + "/_claude/outils/faces"
def masks(key, frames, box, k=13, palm=False):
    """Détourage personne (binaire segment, Vision) sur la zone box ; on garde la plus grande tache (la figure) ; cache cache/seg/<key>."""
    x0, y0, x1, y1 = box; d = CACHE + "seg/" + key; di, dm = d + "/in", d + "/m"
    if not (os.path.isdir(dm) and len(os.listdir(dm)) >= len(frames)):
        os.makedirs(di, exist_ok=True)
        for i, fr_ in enumerate(frames): cv2.imwrite("%s/f%04d.png" % (di, i), (fr_[y0:y1, x0:x1] * 255).astype(np.uint8))
        subprocess.run([SEG, di, dm], check=True, capture_output=True)
    fj = {}
    if palm:
        if not os.path.exists(di + "/faces.json"): subprocess.run([FACES, di], check=True, capture_output=True)
        fj = json.load(open(di + "/faces.json"))
    out = []
    for i in range(len(frames)):
        m = cv2.imread("%s/f%04d.png" % (dm, i), 0).astype(np.float32) / 255
        if palm:                                                            # palme : teinte dorée (H 8-25, S > 90) hors du visage (Vision faces + marge)
            px0, py0, px1, py1 = PALM; rx0, ry0, rx1, ry1 = px0 - x0, py0 - y0, px1 - x0, py1 - y0
            hsv = cv2.cvtColor((frames[i][py0:py1, px0:px1] * 255).astype(np.uint8), cv2.COLOR_BGR2HSV)
            gold = ((hsv[..., 0] >= 8) & (hsv[..., 0] <= 25) & (hsv[..., 1] > 75) & (hsv[..., 2] > 40)).astype(np.uint8)
            gold = cv2.morphologyEx(gold, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
            prot = np.zeros_like(gold)
            for fx, fy, fw, fh in fj.get("f%04d.png" % i, []):
                fx, fy, fw, fh = fx * (x1 - x0), fy * (y1 - y0), fw * (x1 - x0), fh * (y1 - y0)
                ax0, ay0 = int(fx - 0.15 * fw) - rx0, int(fy - 0.75 * fh) - ry0; ax1, ay1 = int(fx + 1.02 * fw) - rx0, int(fy + 1.2 * fh) - ry0
                prot[max(0, ay0):max(0, ay1), max(0, ax0):max(0, ax1)] = 1
            m[ry0:ry1, rx0:rx1][(gold > 0) & (prot == 0)] = 0
        m = cv2.morphologyEx(m, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))   # micros (tiges fines) retirés
        n, lab, st, _ = cv2.connectedComponentsWithStats((m > 0.5).astype(np.uint8))
        if n > 2:
            big = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
            keep = cv2.dilate((lab == big).astype(np.uint8), np.ones((9, 9), np.uint8)).astype(np.float32)
            m = m * keep
        b = (m > 0.5).astype(np.uint8); ff = b.copy(); fm = np.zeros((b.shape[0] + 2, b.shape[1] + 2), np.uint8)
        cv2.floodFill(ff, fm, (0, 0), 1); holes = (ff == 0)                    # trous fermés (cheveux, reflets) rebouchés
        m[holes] = 1.0
        m = np.clip((cv2.GaussianBlur(m, (0, 0), 1.2) - 0.5) * 2.2 + 0.5, 0, 1)
        out.append(m)
    return out
def grade(x, sat=1.15):
    x = 0.80 * x + 0.20 * (x * x * (3 - 2 * x))
    L = x @ np.array([0.0722, 0.7152, 0.2126], np.float32)
    return np.clip(L[..., None] + (x - L[..., None]) * sat, 0, 1)
def lum(x):
    L = x @ np.array([0.0722, 0.7152, 0.2126], np.float32)
    L = L / max(float(np.percentile(L, 99)), 0.2); L = np.clip(L, 0, 1) ** 0.8
    return np.clip((L - 0.5) * 1.25 + 0.5 + 0.03, 0, 1)
def duo(x, dark, light):
    """Bichromie magazine : ombres d'une couleur, lumières d'une autre, trame légère."""
    L = lum(x)[..., None]; return hexc(dark)[None, None, :] * (1 - L) + hexc(light)[None, None, :] * L
def cutout_rgba(img, m, box, solid=None):
    x0, y0, x1, y1 = box; c = grade(img[y0:y1, x0:x1])
    if solid is not None: c = np.ones_like(c) * hexc(solid)[None, None, :]
    return np.dstack([c, m]).astype(np.float32)
def sticker(m, r=7):
    """Contour blanc d'autocollant autour d'une découpe (masque dilaté)."""
    return cv2.dilate(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1)))

# ---------------- papiers : déchirures, scotch, bandes ----------------
def torn_mask(h, w, rng, rough=7, step=14, inset=8):
    pts = []
    for x in np.arange(inset, w - inset, step): pts.append((x, inset + rng.uniform(-rough, rough)))
    for y in np.arange(inset, h - inset, step): pts.append((w - inset + rng.uniform(-rough, rough), y))
    for x in np.arange(w - inset, inset, -step): pts.append((x, h - inset + rng.uniform(-rough, rough)))
    for y in np.arange(h - inset, inset, -step): pts.append((inset + rng.uniform(-rough, rough), y))
    m = np.zeros((h, w), np.float32); cv2.fillPoly(m, [np.array(pts, np.int32)], 1.0, lineType=cv2.LINE_AA)
    return m
def tape_rgba(w, h, rng):
    """Morceau de scotch translucide, bouts dentelés."""
    m = np.ones((h, w), np.float32)
    for y in range(h):
        a = int(rng.integers(0, 7)); b = int(rng.integers(0, 7)); m[y, :a] = 0; m[y, w - b:] = 0
    col = np.array([0.80, 0.90, 0.94], np.float32)[None, None, :] * (1 + 0.04 * rng.standard_normal((h, w, 1)).astype(np.float32))
    return np.dstack([col, m * 0.72]).astype(np.float32)
STRIP_COLS = [CITRON, BLANC, TURQ, ROSE, ORANGE, BLEU, LILAS]   # pas de bande noire : son bord déchiré est lu comme « ...... »
def strip_rgba(w, h, rng, colhex, ht=False):
    col = hexc(colhex); body = np.ones((h, w, 3), np.float32) * col[None, None, :]
    if ht:
        dm = np.zeros((h, w), np.float32)
        for y in range(0, h, 14):
            for x in range((y // 14 % 2) * 7, w, 14): cv2.circle(dm, (x, y), 4, 1.0, -1, cv2.LINE_AA)
        body = body * (1 - 0.35 * dm[..., None])
    body = np.clip(body * (1 + 0.035 * cv2.GaussianBlur(rng.standard_normal((h, w)).astype(np.float32), (0, 0), 1.5))[..., None], 0, 1)
    m = torn_mask(h, w, rng, rough=9, step=12)
    out = np.zeros((h + 16, w + 16, 4), np.float32)
    out[10:10 + h, 8:8 + w, 3] = cv2.GaussianBlur(m, (0, 0), 3) * 0.45
    a = m[..., None]; out[:h, :w, :3] = body * a; out[:h, :w, 3] = np.maximum(m, out[:h, :w, 3])
    return out
def make_strips(sh):   # trame jamais sur papier sombre (lue comme « ...... » par la détection de texte)
    n = sh.get("strips", 0); rng = np.random.default_rng(skey(sh["id"]) + 5); out = []
    zones = [(150, 480), (930, 560), (120, 1250), (960, 1300), (540, 300), (540, 1700), (230, 900), (880, 1050)]
    for k in range(n):
        w, h = int(rng.uniform(380, 640)), int(rng.uniform(80, 160))
        colhex = STRIP_COLS[(k + skey(sh["id"])) % len(STRIP_COLS)]
        cx, cy = zones[(k * 3 + skey(sh["id"])) % len(zones)]
        out.append(dict(img=strip_rgba(w, h, rng, colhex, ht=(k % 2 == 1 and colhex not in (NOIR, BLEU))), cx=cx + rng.uniform(-60, 60), cy=cy + rng.uniform(-60, 60),
                        ang=rng.uniform(-30, 30), k=k))
    return out
class Photo:
    """Photo bichromie (vidéo vivante) : bord papier déchiré, scotch aux coins, ombre ; elle saute un peu sur chaque frappe."""
    def __init__(self, frames, box, width, center, angle, f0, key, colors, border=14):
        self.frames, self.box, self.width, self.center, self.angle, self.f0, self.key, self.colors = frames, box, width, center, angle, f0, key, colors
        x0, y0, x1, y1 = box; self.h = int(round(width * (y1 - y0) / (x1 - x0))); self.b = border
        rng = np.random.default_rng(skey(key)); M = 40
        self.M = M; hh, ww = self.h + 2 * border, width + 2 * border
        self.mask = torn_mask(hh, ww, rng, rough=5, step=11, inset=3)
        self.shadow = np.zeros((hh + 2 * M, ww + 2 * M), np.float32); self.shadow[M + 9:M + 9 + hh, M + 7:M + 7 + ww] = self.mask * 0.5
        self.shadow = cv2.GaussianBlur(self.shadow, (0, 0), 4)
        self.tape_imgs = []
        for t, (tx, ty), ta in [(tape_rgba(int(rng.uniform(110, 150)), 38, rng), (M + int(rng.uniform(-10, 30)), M - 12), rng.uniform(-40, -25)),
                                (tape_rgba(int(rng.uniform(110, 150)), 38, rng), (M + ww - int(rng.uniform(90, 140)), M + hh - 26), rng.uniform(-40, -25))]:
            R = cv2.getRotationMatrix2D((t.shape[1] / 2, t.shape[0] / 2), ta, 1.0)
            c = np.abs(R[:, :2]) @ np.array([t.shape[1], t.shape[0]]); R[0, 2] += c[0] / 2 - t.shape[1] / 2; R[1, 2] += c[1] / 2 - t.shape[0] / 2
            self.tape_imgs.append((cv2.warpAffine(t, R, (int(c[0]), int(c[1]))), (tx, ty)))
        dm = np.zeros((self.h, width), np.float32)
        for y in range(0, self.h, 9):
            for x in range((y // 9 % 2) * 4, width, 9): cv2.circle(dm, (x, y), 2, 1.0, -1, cv2.LINE_AA)
        self.screen = (1 - 0.12 * dm)[..., None]                           # trame d'imprimerie
    def rgba(self, i):
        x0, y0, x1, y1 = self.box; b, M = self.b, self.M
        c = cv2.resize(duo(self.frames[i][y0:y1, x0:x1], *self.colors), (self.width, self.h), interpolation=cv2.INTER_AREA) * self.screen
        hh, ww = self.h + 2 * b, self.width + 2 * b
        out = np.zeros((hh + 2 * M, ww + 2 * M, 4), np.float32); out[..., 3] = self.shadow
        body = np.ones((hh, ww, 3), np.float32) * hexc(BLANC); body[b:b + self.h, b:b + self.width] = c
        a = self.mask[..., None]; reg = out[M:M + hh, M:M + ww]
        reg[..., :3] = body * a; reg[..., 3] = np.maximum(self.mask, reg[..., 3])
        for t, (tx, ty) in self.tape_imgs:
            th, tw = t.shape[:2]; ty2, tx2 = max(0, ty), max(0, tx)
            sub = out[ty2:ty2 + th, tx2:tx2 + tw]; tt = t[:sub.shape[0], :sub.shape[1]]
            ta = tt[..., 3:4]; sub[..., :3] = sub[..., :3] * (1 - ta) + tt[..., :3] * ta; sub[..., 3] = np.maximum(sub[..., 3], tt[..., 3])
        return out
def jit(key, k, amp=8.0, ang=1.5):
    r = np.random.default_rng(skey(key) * 1000 + k); return r.uniform(-amp, amp), r.uniform(-amp, amp), r.uniform(-ang, ang)
TORN_EDGES = None
def torn_edges():
    """Bords de papier déchiré blanc (bord fibreux) en haut et en bas du plan plein cadre, collé comme une coupure."""
    global TORN_EDGES
    if TORN_EDGES is None:
        rng = np.random.default_rng(11); out = np.zeros((H, W, 4), np.float32); col = hexc(ROSE) * (1 - 0.22 * dots()[..., None])
        for top in (True, False):
            ys = [rng.uniform(110, 170) if top else H - rng.uniform(130, 200) for _ in range(0, W + 12, 12)]
            pts = ([(0, 0)] if top else [(0, H)]) + [(x, y) for x, y in zip(range(0, W + 12, 12), ys)] + ([(W, 0)] if top else [(W, H)])
            m = np.zeros((H, W), np.float32); cv2.fillPoly(m, [np.array(pts, np.int32)], 1.0, lineType=cv2.LINE_AA)
            pts2 = ([(0, 0)] if top else [(0, H)]) + [(x, y + (rng.uniform(5, 12) if top else -rng.uniform(5, 12))) for x, y in zip(range(0, W + 12, 12), ys)] + ([(W, 0)] if top else [(W, H)])
            fib = np.zeros((H, W), np.float32); cv2.fillPoly(fib, [np.array(pts2, np.int32)], 1.0, lineType=cv2.LINE_AA)
            sh_ = cv2.GaussianBlur(np.roll(fib, 10 if top else -10, axis=0), (0, 0), 6) * 0.5
            a = np.maximum(fib, sh_)
            rgbv = (col * m[..., None] + hexc(BLANC) * (fib - m)[..., None])
            out[..., :3] = out[..., :3] * (1 - a[..., None]) + rgbv
            out[..., 3] = np.maximum(out[..., 3], a)
        TORN_EDGES = out
    return TORN_EDGES

# ---------------- plans ----------------
L = lambda *ids: [W_(i) for i in ids]
A1_TXT = [L(0, 1), L(2), L(3, 4, 5), L(6), L(7)]                              # MAIS LA / PEUR / VOUS VOUS EN / NOURRISSEZ / PIRE
A2_TXT = [L(8, 9), L(10), L(11, 12), L(13), L(14, 15)]                         # VOUS LA / SUSCITEZ / ET VOUS / L'EXPLOITEZ / POUR DES
A3_TXT = [L(16), L(17), L(18, 19), L(20, 21)]                                  # MOTIFS / POLITICIENS / POUR UNE / RAISON SIMPLE
A4_TXT = [L(22, 23), L(24, 25), L(26, 27), L(28), L(29, 30, 31)]               # QUAND LA / PEUR RÈGNE / ON PEUT / GOUVERNER / PAR LA FORCE
KEY = ("PEUR", "PIRE", "RÈGNE", "FORCE")
AN_BOX = (420, 60, 1500, 890)          # tribune : coupée au-dessus de la lampe du pupitre (logo LFI et logo AN hors détourage)
AN_WIDE = (360, 170, 1700, 1000)       # plan large de l'hémicycle (logo LFI hors cadre)
QAG_WIDE = (160, 140, 1440, 860)       # hémicycle LCP sans logo, chrono, interprète ni bandeau
GR_CROWD = (1420, 250, 1900, 900)      # foule de la grève derrière lui (logo Point'n Think hors cadre)
SHOTS = [
    dict(id="A1", kind="cut", src="AN", t=V_SRC0, box=AN_BOX, scale=(1.24, 1.28), cx=930, txt=A1_TXT, txt_y=250, txt_h=122,
         strips=3, echo=True, why="2026 — tribune de l'Assemblée : « Mais la peur, vous vous en nourrissez. Pire… » en son direct, Léaument détouré sur aplats pop qui changent à chaque frappe"),
    dict(id="A2", kind="cut", src="AN", t=None, box=AN_BOX, scale=(1.30, 1.34), cx=930, txt=A2_TXT, txt_y=250, txt_h=118,
         photos=[("AN", 4.0, AN_WIDE, 470, (225, 1120), -6, 0.0, (NOIR, CITRON)), ("GR", 2.0, GR_CROWD, 400, (870, 1250), 5, 1.07, (BLEU, BLANC))],
         strips=3, echo=True, why="même plan synchro : « …vous la suscitez et vous l'exploitez », photos bichromie de l'hémicycle (plan large) et de la grève"),
    dict(id="A3", kind="cut", src="AN", t=None, box=AN_BOX, scale=(1.26, 1.30), cx=930, txt=A3_TXT, txt_y=260, txt_h=130,
         photos=[("QAG", 46.25, QAG_WIDE, 480, (850, 1100), 5, 0.0, (NOIR, ROSE)), ("AN", 7.0, AN_WIDE, 440, (210, 1330), -4, 1.07, (BLEU, CITRON))],
         strips=5, echo=True, why="même plan synchro : « pour des motifs politiciens pour une raison simple », le collage se remplit"),
    dict(id="A4", kind="cut", src="AN", t=None, box=AN_BOX, scale=(1.32, 1.38), cx=930, txt=A4_TXT, txt_y=250, txt_h=122, letters=("RÈGNE",),
         photos=[("GR", 3.5, GR_CROWD, 420, (210, 1180), -5, 0.0, (NOIR, TURQ))],
         strips=6, echo=True, why="même plan synchro : « Quand la peur règne, on peut gouverner par la force. », montée jusqu'au drop"),
    dict(id="B1", kind="sil", src="CH", t=10.85, box=(450, 0, 1650, 1080), dest_w=1260, cx=1030, push=(1.0, 1.04),
         txt=[[("LA", 0.0), ("PEUR", 0.0)]], txt_y=300, txt_h=200, letters=("PEUR",), strips=3, flash=True,
         why="2026 — hémicycle (LCP), il pointe du doigt : flash blanc 3 images au drop, silhouette blanche puis découpe couleur, contour autocollant + aplat décalé"),
    dict(id="B2", kind="cut", src="GR", t=14.85, box=(470, 0, 1650, 1080), scale=(1.0, 1.04), cx=945,
         txt=[[("VOUS", 0.0), ("VOUS", 0.0), ("EN", 0.0)], [("NOURRISSEZ", 0.0)]], txt_y=280, txt_h=165, strips=3, echo=True,
         why="2026 — grève Ubisoft, écharpe tricolore : découpe sur aplats pop"),
    dict(id="B3", kind="echo", src="BU", t=0.30, box=(0, 0, 1920, 1080), dest_w=1700, cx=800, push=(1.0, 1.035),
         txt=[[("PIRE", 0.0)]], txt_y=290, txt_h=230, letters=("PIRE",), strips=2,
         why="2026 — au bureau, bras ouverts : 3 silhouettes en aplats décalés (multiples pop) + la découpe couleur"),
    dict(id="B4", kind="collage",
         photos=[("AN", 252.4, (560, 80, 1400, 900), 560, (330, 700), -5, 0.0, (NOIR, ROSE)), ("CH", 5.05, (420, 0, 1500, 1080), 500, (790, 900), 6, 0.267, (BLEU, CITRON)),
                 ("QAG", 48.0, QAG_WIDE, 600, (420, 1260), -3, 0.534, (NOIR, TURQ)), ("GR", 16.4, (470, 0, 1650, 1080), 480, (800, 1520), 4, 0.80, (NOIR, ORANGE))],
         txt=[[("VOUS", 0.0), ("LA", 0.0)], [("SUSCITEZ", 0.0)]], txt_y=260, txt_h=170, strips=3,
         why="collage magazine : photos bichromie (tribune, hémicycle LCP, plan large, grève) qui se posent à chaque demi-temps"),
    dict(id="B5", kind="full", src="AN", t=258.4, crop=(880, 540, 1080), push=(1.0, 1.05), focus=(860, 330),
         big=[("QUAND LA PEUR", 0.0, (255, 255, 255)), ("RÈGNE", 0.0, rgb(CITRON))], big_y=930, big_sizes=[120, 210], flash=True,
         why="2026 — tribune, autre moment, plein cadre couleur entre deux bords déchirés tramés ; gros texte avec contour"),
    dict(id="B6", kind="cut", src="AN", t=160.0, box=AN_BOX, scale=(1.30, 1.35), cx=960,
         txt=[[("ON", 0.0), ("PEUT", 0.0)], [("GOUVERNER", 0.0)]], txt_y=270, txt_h=170, strips=3, echo=True,
         photos=[("BU", 8.0, (200, 0, 1500, 1080), 420, (230, 1150), -6, 0.0, (NOIR, CITRON))],
         why="2026 — tribune (« je le fais donc à cette tribune », sans le son), découpe + aplat décalé, photo du bureau en bichromie"),
    dict(id="B7", kind="sil", src="BU", t=9.95, box=(0, 0, 1920, 1080), dest_w=1820, cx=950, push=(1.0, 1.05),
         txt=[[("PAR", 0.0), ("LA", 0.0)], [("FORCE", 0.0)]], txt_y=280, txt_h=190, strips=4, letters=("FORCE",),
         why="2026 — au bureau, face caméra : silhouette blanche 3 images puis découpe couleur ; PAR LA FORCE en un seul carton pendant le break « Do the dance »"),
    dict(id="FIN", kind="card", push=(1.0, 1.035),
         big=[("ANTOINE", 0.0, (255, 255, 255)), ("LÉAUMENT", 0.0, rgb(ROSE))],
         big_y=640, big_sizes=[280, 280], big_font="impact",
         why="carton final propre (fond noir, Impact blanc / rose) : son nom seul (aucun groupe de mots répété)"),
]
BOUNDS_T = [0] + CUTF + [fr(END)]
assert len(BOUNDS_T) == len(SHOTS) + 1, (len(BOUNDS_T), len(SHOTS))
for i, sh in enumerate(SHOTS):
    sh["a"], sh["bb"] = BOUNDS_T[i], BOUNDS_T[i + 1]; sh["n"] = sh["bb"] - sh["a"]; sh["clip"] = "R5_%s.mov" % sh["id"]
    if sh.get("src") == "AN" and sh["t"] is None: sh["t"] = V_SRC0 + sh["a"] / FPS           # plans A synchro avec la voix
assert min(sh["n"] for sh in SHOTS) >= 16, [(s["id"], s["n"]) for s in SHOTS]

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
        dx, dy, da = jit((boil, j), k, amp=4, ang=1.0) if boil else (0, 0, 0)        # les découpes « bougent » sur chaque frappe
        paste(img, im, cx + dx, cy + dy, s, da)
CARD_TAPES = [tape_rgba(170, 46, np.random.default_rng(40 + j)) for j in range(4)]
def other_cols(k, n=3):
    """Couleurs des aplats décalés : jamais celle du fond de la frappe."""
    c = [x for x in CYCLE if x != CYCLE[k % len(CYCLE)] and x != CYCLE[(k + 3) % len(CYCLE)]]
    return [c[(k + j) % len(c)] for j in range(n)]
def place_cut(img, raw_i, m, sh, sc, kbeat, mode):
    """Découpe en bas du cadre, centrée sur cx : aplat décalé (repérage pop), ombre, contour autocollant, découpe couleur."""
    x0, y0, x1, y1 = sh["box"]; hh = (y1 - y0) * sc
    ccx = W / 2 + ((x1 - x0) / 2 - (sh["cx"] - x0)) * sc; ccy = sh.get("bottom", H) - hh / 2
    oc = other_cols(kbeat)
    if mode == "echo":                                                   # 3 multiples en aplats
        for (dx, dy, s2), col in zip(((-230, -60, 0.9), (230, -60, 0.9), (0, -150, 0.8)), oc):
            paste(img, cutout_rgba(raw_i, m, sh["box"], solid=col), ccx + dx, ccy + dy + hh * (1 - s2) / 2, sc * s2)
    st_ = np.dstack([np.ones((m.shape[0], m.shape[1], 3), np.float32) * hexc(BLANC), sticker(m, 8)])
    if sh.get("echo") or mode == "echo":                                 # aplat décalé façon sérigraphie mal repérée
        paste(img, np.dstack([np.ones_like(st_[..., :3]) * hexc(oc[0] if mode != "echo" else NOIR), st_[..., 3]]), ccx + 26, ccy + 18, sc)
    sd = st_.copy(); sd[..., :3] = 0; sd[..., 3] = cv2.GaussianBlur(st_[..., 3], (0, 0), 6) * 0.45
    paste(img, sd, ccx + 12, ccy + 9, sc); paste(img, st_, ccx, ccy, sc)
    return ccx, ccy
def render(sh):
    n = sh["n"]; a = sh["a"]; frames = []
    rel = lambda t: sh["a"] / FPS + t
    def abs_pieces(p, timeline_abs):
        return [(im, cx, cy, (t if timeline_abs else rel(t))) for im, cx, cy, t in p]
    sync = sh["id"].startswith("A")
    txt = abs_pieces(board(sh["txt"], sh["txt_y"], seed=skey(sh["id"]) * 7, letters=sh.get("letters", KEY), h=sh.get("txt_h", 120)), sync) if sh.get("txt") else []
    big = []
    if sh.get("big"):
        big = abs_pieces(big_text([(s, t, c) for s, t, c in sh["big"]], sh["big_y"], sizes=sh["big_sizes"],
                                  spec=((S + "Impact.ttf", 0) if sh.get("big_font") else FCOND),
                                  maxw=(XMAX - XMIN) * (0.90 if sh["kind"] == "card" else 1.0), contour=10 if sh["kind"] == "full" else 0), False)
    photos = [Photo(read_frames(ps, pt, n), pbox, pw, pc, pa, fr(rel(pt0)), (sh["id"], j), cols)
              for j, (ps, pt, pbox, pw, pc, pa, pt0, cols) in enumerate(sh.get("photos", []))]
    strips = make_strips(sh)
    k0 = nbeat(a)
    if sh["kind"] in ("cut", "sil", "full", "echo"):
        raw = read_frames(sh["src"], sh["t"], n)
    if sh["kind"] in ("cut", "sil", "echo"):
        ms = masks("%s_%s_%.2f_%d" % (sh["id"], sh["src"], sh["t"], n), raw, sh["box"], k=13 if sh["src"] == "AN" else 9,
                   palm=(sh["src"] == "AN"))
    for i in range(n):
        f = a + i; u = i / max(n - 1, 1); kb = nbeat(f) - k0; kg = nbeat(f)
        if sh["kind"] == "full":
            cx, cy, vh = sh["crop"]; z = sh["push"][0] + (sh["push"][1] - sh["push"][0]) * u
            s = H / vh * z; fx_, fy_ = sh["focus"]
            ccx = cx + (fx_ - cx) * (1 - 1 / z); ccy = cy + (fy_ - cy) * (1 - 1 / z)
            M = np.float32([[s, 0, W / 2 - ccx * s], [0, s, H / 2 - ccy * s]])
            img = grade(cv2.warpAffine(raw[i], M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE), 1.15)
        elif sh["kind"] == "card":
            img = np.ones((H, W, 3), np.float32) * hexc(NOIR) * paper_noise(9)
        else:
            img = background(kg, sh["id"])                                  # aplat pop : change à chaque frappe
        for st in strips:                                                   # une bande de plus à chaque frappe
            if st["k"] <= kb:
                dx, dy, da = jit((sh["id"], "s", st["k"]), kg, amp=6, ang=1.2)
                s_ = pop(f, BEATF[k0 + st["k"] - 1] if 0 < st["k"] and k0 + st["k"] - 1 < len(BEATF) else a, n=4, amp=0.08) or 1.0
                paste(img, st["img"], st["cx"] + dx, st["cy"] + dy, s_, st["ang"] + da)
        for ph in photos:
            s_ = pop(f, ph.f0, n=5, amp=0.10)
            if s_ is not None:
                dx, dy, da = jit(ph.key, kg, amp=9, ang=1.8)
                paste(img, ph.rgba(i), ph.center[0] + dx, ph.center[1] + dy, s_, ph.angle + da)
        if sh["kind"] == "cut":
            sc = sh["scale"][0] + (sh["scale"][1] - sh["scale"][0]) * u
            ccx, ccy = place_cut(img, raw[i], ms[i], sh, sc, kg, "cut")
            paste(img, cutout_rgba(raw[i], ms[i], sh["box"]), ccx, ccy, sc)
        elif sh["kind"] in ("sil", "echo"):
            x0, y0, x1, y1 = sh["box"]; z = sh["push"][0] + (sh["push"][1] - sh["push"][0]) * u
            sc = sh["dest_w"] / (x1 - x0) * z
            ccx, ccy = place_cut(img, raw[i], ms[i], sh, sc, kg, sh["kind"])
            if sh["kind"] == "sil" and i < 3: paste(img, cutout_rgba(raw[i], ms[i], sh["box"], solid=BLANC), ccx, ccy, sc)   # silhouette blanche 3 images
            else: paste(img, cutout_rgba(raw[i], ms[i], sh["box"]), ccx, ccy, sc)
        if sh["kind"] == "full":
            te = torn_edges(); img = img * (1 - te[..., 3:4]) + te[..., :3]
        if txt: draw_pieces(img, txt, f, boil=sh["id"])
        if sh["kind"] == "card":
            for j, (tx, ty, ta) in enumerate(((175, 330, -32), (905, 330, 30), (175, 1500, 28), (905, 1500, -30))):
                paste(img, CARD_TAPES[j], tx, ty, 1.0, ta)
        if big:
            if sh["kind"] == "card":
                z = sh["push"][0] + (sh["push"][1] - sh["push"][0]) * u
                for im, cx, cy, t in big:
                    s_ = pop(f, fr(t))
                    if s_ is not None: paste(img, im, W / 2 + (cx - W / 2) * z, H / 2 + (cy - H / 2) * z, s_ * z)
            else: draw_pieces(img, big, f)
        if sh.get("flash") and i < 3: img = img + (1 - img) * [1.0, 0.6, 0.25][i]    # aplat blanc plein cadre : flash de transition 3 images
        frames.append(finish(img, f))
    write_mov(frames, OUT + sh["clip"])
    if sh["kind"] in ("cut", "sil", "echo"):                                # contrôle : haut de la tête vs bas du texte (1re image)
        m = ms[0]; ys = np.where(m.max(1) > 0.5)[0]; x0, y0, x1, y1 = sh["box"]
        sc = sh["scale"][0] if sh["kind"] == "cut" else sh["dest_w"] / (x1 - x0)
        top = H - (y1 - y0) * sc + ys[0] * sc
        tb = max(cy + im.shape[0] / 2 for im, cx, cy, t in txt) if txt else 0
        print("  %-4s %3d im  (%s)  tête y=%d  bas texte y=%d" % (sh["id"], n, sh["kind"], top, tb))
    else:
        print("  %-4s %3d im  (%s)" % (sh["id"], n, sh["kind"]))

# ---------------- audio ----------------
def sweep_lowpass(x, sr, fc_of_t):
    """Passe-bas qui s'ouvre (montée) : masque spectral STFT dont la coupure suit fc_of_t(t)."""
    import scipy.signal as ss
    out = np.zeros_like(x)
    for ch in range(x.shape[1]):
        f, t, Z = ss.stft(x[:, ch], fs=sr, nperseg=2048, noverlap=1536)
        fc = fc_of_t(t)[None, :]
        g = 1 / np.sqrt(1 + (f[:, None] / fc) ** 8)                          # pente ~ 48 dB/oct
        _, y = ss.istft(Z * g, fs=sr, nperseg=2048, noverlap=1536)
        out[:, ch] = y[:len(x)]
    return out
def make_audio():
    import soundfile as sf
    sr = 48000; N = int(round(END * sr))
    def grab(path, t, dur):
        p = subprocess.run([FF, "-v", "error", "-ss", "%.3f" % t, "-t", "%.3f" % dur, "-i", path, "-ac", "2", "-ar", str(sr), "-f", "f32le", "-"], capture_output=True)
        return np.frombuffer(p.stdout, np.float32).reshape(-1, 2).copy()
    voix = np.zeros((N, 2), np.float32); mus = np.zeros((N, 2), np.float32)
    v = grab(HG + "/" + SRC["AN"][0], V_IN, V_OUT - V_IN); env = np.ones(len(v), np.float32)
    k = int(0.03 * sr); env[:k] = np.linspace(0, 1, k); k = int(0.08 * sr); env[-k:] = np.linspace(1, 0, k)
    i0 = int(round(t_of_src(V_IN) * sr)); voix[i0:i0 + len(v)] = v * env[:, None] * 10 ** (5 / 20)
    m = music_raw(MUSIC_IN)[:N]
    dr = DROPT; vend = t_of_src(V_OUT)
    fc = lambda t: np.interp(t, [0, vend - 1.0, dr - 0.02, dr], [420, 1400, 9000, 20000])            # le filtre s'ouvre vers le drop
    m = sweep_lowpass(m.astype(np.float64), sr, fc).astype(np.float32)
    t = np.arange(len(m)) / sr
    gdb = np.interp(t, [0, 0.3, vend - 1.0, vend, dr - 0.02, dr, END], [-24, -13, -11, -8, -5, 0, 0])
    kf = int(0.45 * sr); fo = np.ones(len(m), np.float32); fo[-kf:] = np.linspace(1, 0, kf)
    mus[:len(m)] = m * (10 ** (gdb / 20) * fo)[:, None]
    sf.write(OUT + "R5-voix.wav", voix, sr, subtype="PCM_24"); sf.write(OUT + "R5-musique.wav", mus, sr, subtype="PCM_24")
    sf.write(D + "tmp_mix.wav", voix + mus, sr, subtype="FLOAT")
    r = subprocess.run([FF, "-hide_banner", "-i", D + "tmp_mix.wav", "-af", "loudnorm=I=-14:TP=-2.5:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    js = json.loads(r[r.rindex("{"):r.rindex("}") + 1])
    af = ("loudnorm=I=-14:TP=-2.5:LRA=11:measured_I=%s:measured_TP=%s:measured_LRA=%s:measured_thresh=%s:offset=%s:linear=true,"
          "aresample=48000" % (js["input_i"], js["input_tp"], js["input_lra"], js["input_thresh"], js["target_offset"]))
    subprocess.run([FF, "-v", "error", "-y", "-i", D + "tmp_mix.wav", "-af", af, "-c:a", "pcm_s24le", OUT + "R5-mix.wav"], check=True)
    os.remove(D + "tmp_mix.wav"); print("audio : mix avant normalisation", js["input_i"], "LUFS")

# ---------------- plan ----------------
PHRASE = ("Mais la peur, vous vous en nourrissez. Pire, vous la suscitez et vous l'exploitez pour des motifs politiciens pour une raison simple. "
          "Quand la peur règne, on peut gouverner par la force.")
def build_plan():
    video = []
    for sh in SHOTS:
        v = {"id": sh["id"], "clip": sh["clip"], "folder": "genR5", "path": OUT + sh["clip"], "s": 0, "e": sh["n"], "rec": sh["a"], "dur": sh["n"],
             "clip_fps": FPS, "speed_pct": 100, "track": 1, "note": sh["why"], "kind": sh["kind"], "temps": round(sh["n"] / FPS / T, 2)}
        if sh.get("src"):
            path, sfps, url, ctx = SRC[sh["src"]]
            v["source"] = {"fichier": path, "in_s": round(sh["t"], 3), "out_s": round(sh["t"] + sh["n"] / FPS, 3), "fps": round(sfps, 3), "url": url, "contexte": ctx}
        if sh.get("photos"):
            v["photos_bichromie"] = [{"fichier": SRC[p[0]][0], "in_s": p[1], "out_s": round(p[1] + sh["n"] / FPS, 2), "cadre_source": p[2], "url": SRC[p[0]][2]} for p in sh["photos"]]
        video.append(v)
    texts = []
    for sh in SHOTS:
        for line in sh.get("txt", []): texts.append({"plan": sh["id"], "texte": " ".join(w for w, _ in line)})
        for s_, t_, c_ in sh.get("big", []): texts.append({"plan": sh["id"], "texte": s_})
    plan = {"name": "R5 - Collage ransom-note pop - Antoine Léaument", "fps": FPS, "w": W, "h": H, "duree_s": END,
            "note": "Plans ProRes 9:16 composés en Python (lot6/_claude/gen/R5/out) : aplats pop qui changent à chaque frappe + feuille déchirée tramée Ben-Day, "
                    "Léaument détouré (segment/Vision, plus grande tache), aplat décalé façon sérigraphie, multiples pop (B3), photos bichromie collées, "
                    "textes ransom-note cuits. s/e en images du clip (30 i/s), rec en images timeline. Coupes sur les kicks réels de D.A.N.C.E. "
                    "(out/R5-frappes.json). Aucun ralenti. Générateur : lot6/_claude/gen/R5/genR5.py",
            "phrase": {"texte": PHRASE, "url": SRC["AN"][2] + "&t=24", "source": SRC["AN"][0], "in_s": 24.76, "out_s": 32.96,
                       "timeline_s": [round(t_of_src(24.76), 2), round(t_of_src(32.96), 2)],
                       "voix": "son direct synchro (plans A1-A4, même source, même moment) ; phrase complète, rien de coupé"},
            "musique": {"fichier": "lot6/sons/R5-justice-dance_complet.wav", "titre": "Justice - D.A.N.C.E.", "url": SON_URL,
                        "debut_complet_s": round(MUSIC_IN, 4), "fin_complet_s": round(MUSIC_IN + END, 3), "drop_timeline_s": DROPT,
                        "coupes_kicks_s": CUTS, "coupes_images": CUTF},
            "textes": texts, "video": video,
            "audio": [{"id": "mix", "clip": "R5-mix.wav", "folder": "genR5", "path": OUT + "R5-mix.wav", "rec": 0, "track": 1,
                       "note": "mix -14 LUFS : voix AN %.2f-%.2f s (+5 dB) à %.2f s ; D.A.N.C.E. dès %.3f s du complet, passe-bas 420 Hz -> ouvert et -13 -> -5 dB sous la voix, plein au drop, fondu de fin 0,45 s"
                               % (V_IN, V_OUT, t_of_src(V_IN), MUSIC_IN)}],
            "stems": ["lot6/_claude/gen/R5/out/R5-voix.wav", "lot6/_claude/gen/R5/out/R5-musique.wav"],
            "logos_exclus": "AN : logo LFI (haut gauche) et logo de l'Assemblée (haut droite) hors détourage et hors cadre (plein cadre recadré) ; LCP : logo, chrono, interprète et bandeau hors cadre photo ; grève : logo Point'n Think hors cadre"}
    json.dump(plan, open(D + "plan-R5.json", "w"), indent=1, ensure_ascii=False)
    son = {"id": "R5", "titre": "D.A.N.C.E.", "artiste": "Justice", "url": SON_URL,
           "chaine": "Justice (officielle, certifiée, « Justice - D.A.N.C.E. - † (Official Audio) »)",
           "fichier": "lot6/sons/R5-justice-dance_complet.wav",
           "extrait_complet_s": {"debut": round(MUSIC_IN, 4), "fin": round(MUSIC_IN + END, 3)},
           "paroles_audibles": "sous la phrase (filtré) : fin du 2e refrain des enfants (« You are such a P.Y.T. … just easy as A.B.C. ») ; au drop : « Do the D.A.N.C.E. » avec le beat plein, puis « Do the dance » (break sans kick)",
           "bpm": 112.35, "temps_s": round(T, 4),
           "drop": {"complet_s": round(MUSIC_IN + DROPT, 4), "timeline_s": DROPT, "nature": "entrée du beat plein (kick + basse) sur le refrain « Do the D.A.N.C.E. »"},
           "frappes_timeline_s": [round(k, 4) for k in BEATS], "coupes_sur_frappes_s": CUTS,
           "mix": "lot6/_claude/gen/R5/out/R5-mix.wav"}
    json.dump(son, open(D + "son.json", "w"), indent=1, ensure_ascii=False)

# ---------------- aperçu 540x960 ----------------
def apercu():
    plan = json.load(open(D + "plan-R5.json")); ins = []; fl = []
    for i, v in enumerate(plan["video"]):
        ins += ["-i", OUT + v["clip"]]
        fl.append("[%d:v]trim=start_frame=%d:end_frame=%d,setpts=PTS-STARTPTS,scale=540:960,setsar=1[v%d]" % (i, v["s"], v["e"], i))
    k = len(plan["video"]); fl.append("".join("[v%d]" % i for i in range(k)) + "concat=n=%d:v=1:a=0[v]" % k)
    ins += ["-i", OUT + "R5-mix.wav"]; out = HG + "/preview/apercu-R5.mp4"
    subprocess.run([FF, "-v", "error", "-y"] + ins + ["-filter_complex", ";".join(fl), "-map", "[v]", "-map", "%d:a" % k,
                    "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "aac", "-b:a", "192k", "-shortest", out], check=True)
    print("aperçu", out)
# ---------------- mesure sur l'export : coupes vs kicks, LUFS / TP ----------------
def mesure():
    out = HG + "/preview/apercu-R5.mp4"
    p = subprocess.run([FF, "-v", "error", "-i", out, "-vn", "-ac", "2", "-ar", "48000", "-f", "f32le", "-"], capture_output=True)
    y = np.frombuffer(p.stdout, np.float32).reshape(-1, 2)
    h = [x[0] for x in detect_hits(y) if x[1] == "kick" and x[3] > 0.03]
    worst = 0
    for c in [fr_ / FPS for fr_ in CUTF]:
        k = min(h, key=lambda t: abs(t - c)); e = (c - k) * 1000; worst = max(worst, abs(e))
        print("  coupe %.3f  kick %.4f  écart %+.1f ms" % (c, k, e))
    print("écart max coupes/kicks : %.1f ms" % worst)
    r = subprocess.run([FF, "-hide_banner", "-i", out, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    print(r[r.rindex("Summary"):])
if __name__ == "__main__":
    args = set(a for a in sys.argv[1:] if not a.startswith("only=")) or {"shots", "audio", "plan", "apercu"}
    only = [x for a in sys.argv[1:] if a.startswith("only=") for x in a.split("=", 1)[1].split(",")]
    print("musique dès %.4f s ; coupes (s) :" % MUSIC_IN, [round(c, 4) for c in CUTS], "images :", CUTF)
    print("beats :", [round(b, 3) for b in BEATS])
    if "shots" in args or only:
        for sh in SHOTS:
            if not only or sh["id"] in only: render(sh)
    if "audio" in args: make_audio()
    if "plan" in args: build_plan()
    if "apercu" in args: apercu()
    if "mesure" in args: mesure()
