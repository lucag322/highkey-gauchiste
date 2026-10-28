# R3 (lot 6) — Collage ransom-note poussé (modèle lot5 R1, inspi @abdulelsayed), Jean-Luc Mélenchon,
# son Stardust – Music Sounds Better With You (clip officiel, chaîne Stardust).
# Visuel (choix Luca 27/10 : « aplats couleur comme R1/R6 ») : Mélenchon découpé sur aplats de couleurs vives du début à la fin
# (mandarine, turquoise, fuchsia, cobalt), fond qui change sur les frappes, contour autocollant, double tirage tramé derrière, bandes,
# scotch, tirages couleur ; plans de 2017 en couleur ; carton final : JEAN-LUC MÉLENCHON + 2027 (année de l'élection).
# Phrase (son direct, meeting pour la paix, Vieux-Port de Marseille, 9/4/2017, chaîne JEAN-LUC MÉLENCHON, youtu.be/yrjWwsV4zS4
#   ~2523,4-2532,4 s) : « Il faut que soit mis un terme à cette caste dorée de parasites incapables, inutiles. »
#   -> autre phrase que Z1 (« Les riches… au-dessus de nos moyens »), Z3 (« Ne comptez que sur vos propres forces »), A6, M1, W1, I1, C3, C4.
# Voix = images synchro de la captation d'origine (plan large scène -> foule -> plan large), dans l'ordre exact de la régie.
# Son : extrait continu ; sous la phrase, fin du refrain (« Love might bring us back together ») puis le break filtré sans kick plein
#   (174,4-180,2 s) = montée ; drop = retour du kick à 180,20 s juste après « Ooh baby », puis « I feel right, the music sounds better with you ».
# Coupes sur les kicks réels (break : kicks filtrés), après le drop toutes les 2 temps.
# Usage : python genR3.py [shots] [audio] [plan] [apercu] [mesure] [only=ID,ID]   (sans argument = tout sauf mesure)
import sys
sys.dont_write_bytecode = True
import os, json, subprocess, math, re
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
HG = "/Users/luca.grousset/Movies/highkey-gauchiste"
D = HG + "/lot6/_claude/gen/R3/"; OUT = D + "out/"; CACHE = D + "cache/"; os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, D)
from hits import detect_hits
FF = "/opt/homebrew/bin/ffmpeg"; SEG = HG + "/_claude/outils/segment"; FPS = 30; W, H = 1080, 1920
def fr(t): return int(round(t * FPS))
def hexc(h): h = h.lstrip("#"); return np.array([int(h[4:6], 16), int(h[2:4], 16), int(h[0:2], 16)], np.float32) / 255   # BGR
def rgb(h): h = h.lstrip("#"); return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
# palette R3 : album 2017 (kraft, page noire d'album, crème sépia, rouge passé) puis 2026 couleurs franches
KRAFT, KRAFT2, ALBUM, SEPCREAM, OLDRED = "#B8946A", "#A27B4F", "#231A14", "#E9DCC3", "#9E2B25"
TANG, TURQ, FUCH, COBALT, CREAM, INK = "#FF6A13", "#00A6A6", "#E5007D", "#2340FF", "#F4EBDD", "#141414"

# ---------------- sources (lecture seule) ----------------
SRC = {
    "CASTE": ("lot6/sources/R3-marseille2017-caste.mp4", 25.0, "https://www.youtube.com/watch?v=yrjWwsV4zS4", 2500.0,
              "meeting pour la paix, Vieux-Port de Marseille, 9/4/2017 (chaîne JEAN-LUC MÉLENCHON)"),
    "HUMA": ("lot1/sources/3-melenchon-huma-citation.mp4", 50.0, "https://www.youtube.com/watch?v=80bBtk2lTiI", 4710.0,
             "Fête de l'Humanité, 12/9/2026 (chaîne JEAN-LUC MÉLENCHON)"),
    "VAL": ("lot1/sources/1-melenchon-valence-amfis.mp4", 30.0, "https://www.youtube.com/watch?v=IYegq2-6-go", 1620.0,
            "meeting des AMFiS, Valence, 2026 (chaîne JEAN-LUC MÉLENCHON)"),
}

# ---------------- musique : Stardust – Music Sounds Better With You ----------------
SON_FILE = HG + "/lot6/sons/R3-stardust-music-sounds-better_complet.wav"; SON_URL = "https://www.youtube.com/watch?v=FQlAEiCb8m0"
T = 0.4842                                   # 123,9 BPM (kicks 180,197 -> 191,334)
MDROP = 180.197                              # retour du kick après le break filtré, juste après « Ooh baby »
DROP = 9.95
MUSIC_IN0 = MDROP - DROP
# coupes (temps du morceau) : 3 avant le drop (kick, puis kicks filtrés du break), drop, puis toutes les 2 temps
# (186,0 n'a pas de kick audible -> le plan B6 dure 4 temps), fin = kick 189,882
CUT_SONG = [171.964, 175.365, 177.301, 180.197, 181.163, 182.131, 183.096, 184.071, 185.032, 186.954, 187.944]
END_SONG = 189.882
HITS_JSON = OUT + "R3-frappes.json"
def music_raw(mi, dur=None, sr=48000):
    import soundfile as sf
    dur = dur or (END_SONG - MUSIC_IN0 + 0.6)
    i0 = int(round(mi * sr)); x, r = sf.read(SON_FILE, start=i0, frames=int(dur * sr), dtype="float32"); assert r == sr; return x
def kicks_of(h, lvl=0.05): return [x[0] for x in h if x[1] == "kick" and x[3] > lvl]
def snap_list(ks, targets):
    out = []
    for t in targets:
        c = min(ks, key=lambda k: abs(k - t)); assert abs(c - t) < 0.04, ("pas de kick près de", t, c); out.append(c)
    return out
def frappes():
    tg = [c - MUSIC_IN0 for c in CUT_SONG + [END_SONG]]
    if os.path.exists(HITS_JSON):
        js = json.load(open(HITS_JSON))
        if js["cle"] == [MUSIC_IN0, tg]: return js["music_in"], js["frappes"]
    best, bad = None, 9
    for off in np.arange(-0.016, 0.0165, 0.001):
        h = detect_hits(music_raw(MUSIC_IN0 + off))
        try: cuts = snap_list(kicks_of(h), [t - off for t in tg])
        except AssertionError: continue                                     # détection instable à ce décalage
        e = max(abs(c - round(c * FPS) / FPS) for c in cuts)
        if e < bad: best, bad, hb = off, e, h
    mi = MUSIC_IN0 + best
    json.dump({"cle": [MUSIC_IN0, tg], "music_in": mi, "frappes": hb}, open(HITS_JSON, "w")); return mi, hb
MUSIC_IN, HITS = frappes()
FINE = 0.0                                   # recalage fin mesuré sur l'export AAC si besoin
MUSIC_IN += FINE; HITS = [[h[0] - FINE] + list(h[1:]) for h in HITS]
KICKS = kicks_of(HITS)
ALLC = snap_list(KICKS, [c - MUSIC_IN for c in CUT_SONG + [END_SONG]])
CUTS = ALLC[:-1]
CUTF = [fr(c) for c in CUTS]; ENDF = fr(ALLC[-1]); END = ENDF / FPS
DROPF = CUTF[3]; TB = T

# ---------------- voix ----------------
V_SRC0 = 23.10                               # fichier CASTE à t = 0 (« Il » 23,40 -> 0,30 s)
V_IN, V_OUT = 23.34, 32.42                   # « Il » … « inutiles » (fin 32,35), applaudissements coupés en fondu
def t_of_src(s): return s - V_SRC0
WORDS = [("IL", 23.40), ("FAUT", 23.75), ("QUE", 24.10), ("SOIT", 24.35), ("MIS", 24.55), ("UN", 24.75), ("TERME", 25.10), ("À", 25.42),
         ("CETTE", 27.05), ("CASTE", 27.62), ("DORÉE", 28.05), ("DE", 29.25), ("PARASITES", 29.50), ("INCAPABLES", 30.22), ("INUTILES", 31.65)]
def wt(i): return t_of_src(WORDS[i][1])
SRC_CUTS = [24.76, 27.72, 33.80]             # coupes de la régie d'origine (plan large -> foule -> plan large -> foule)

# ---------------- polices ransom-note ----------------
S = "/System/Library/Fonts/Supplemental/"
FONTS = [(S + "Arial Black.ttf", 0), (S + "Georgia Bold.ttf", 0), (S + "Times New Roman Bold.ttf", 0), (S + "Impact.ttf", 0),
         (S + "Courier New Bold.ttf", 0), (S + "Rockwell.ttc", 2), (S + "AmericanTypewriter.ttc", 2), (S + "Didot.ttc", 2),
         (S + "Bodoni 72.ttc", 2), (S + "Futura.ttc", 2)]
FCOND = (S + "Futura.ttc", 4)
# morceaux de texte : 2017 = papiers jaunis, encre brune, rouge passé ; 2026 = couleurs franches
SEPIA_STYLES = [((236, 224, 200), (40, 26, 16)), ((40, 28, 20), (238, 226, 204)), ((158, 43, 37), (244, 234, 214)),
                ((210, 190, 155), (30, 20, 12)), ((246, 240, 228), (120, 40, 30)), ((185, 150, 106), (25, 18, 12))]
POP_STYLES = [(rgb(TANG), (255, 255, 255)), (rgb(TURQ), (20, 20, 20)), (rgb(FUCH), (255, 255, 255)), (rgb(COBALT), (255, 255, 255)),
              ((250, 248, 240), rgb(FUCH)), ((20, 20, 20), (255, 255, 255)), ((250, 248, 240), (20, 20, 20)), ((255, 225, 60), (20, 20, 20))]
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
    if not letters: return chip(word, h, rng, styles, fspec=((S + "Impact.ttf", 0) if len(word) >= 9 else None))[0]   # mots longs : police étroite, lisible en grand
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
    """lines = [[(mot, t_apparition), …], …] -> liste de pièces placées (img, cx, cy, t)."""
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
def paper(col, fibre=False):
    """Fond papier : grain + (option) fibres de kraft."""
    k = (col, fibre)
    if k not in _tex:
        rng = np.random.default_rng(len(_tex) + 3)
        n = cv2.resize(rng.standard_normal((48, 27)).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC)
        n2 = cv2.GaussianBlur(rng.standard_normal((H, W)).astype(np.float32), (0, 0), 1.2)
        tex = 1 + 0.03 * n[..., None] + 0.035 * n2[..., None]
        if fibre:
            fb = np.zeros((H, W), np.float32)
            for _ in range(2600):
                x, y = rng.uniform(0, W), rng.uniform(0, H); a = rng.uniform(0, np.pi); l = rng.uniform(6, 22)
                cv2.line(fb, (int(x), int(y)), (int(x + l * np.cos(a)), int(y + l * np.sin(a))), float(rng.choice([-1, 1])), 1, cv2.LINE_AA)
            tex = tex + 0.05 * cv2.GaussianBlur(fb, (0, 0), 0.6)[..., None]
        _tex[k] = np.clip(hexc(col)[None, None, :] * tex, 0, 1).astype(np.float32)
    return _tex[k].copy()
VIG = None
def finish(img, f, old=False):
    global VIG
    if VIG is None:
        y, x = np.mgrid[0:H, 0:W].astype(np.float32)
        r = np.sqrt(((x - W / 2) / (W / 2)) ** 2 + ((y - H / 2) / (H / 2)) ** 2) / np.sqrt(2)
        VIG = (1 - 0.28 * np.clip(r, 0, 1) ** 2.4)[..., None].astype(np.float32)
    rng = np.random.default_rng(1000 + f)
    g = rng.standard_normal((H // 2, W // 2)).astype(np.float32)
    g = cv2.resize(g, (W, H), interpolation=cv2.INTER_LINEAR)[..., None] * (0.035 if old else 0.022)
    img = img * VIG + g
    if old:                                                                  # 2017 : poussières + rayure de pellicule
        dust = np.zeros((H, W), np.float32)
        for _ in range(int(rng.integers(10, 22))):
            cv2.circle(dust, (int(rng.uniform(0, W)), int(rng.uniform(0, H))), int(rng.integers(1, 4)), float(rng.choice([-0.5, 0.6])), -1, cv2.LINE_AA)
        if rng.uniform() < 0.6:
            x = int(rng.uniform(80, W - 80)); cv2.line(dust, (x, 0), (x + int(rng.integers(-20, 20)), H), 0.25, 1, cv2.LINE_AA)
        img = img + cv2.GaussianBlur(dust, (0, 0), 0.8)[..., None] * 0.6
    return np.clip(img, 0, 1)

# ---------------- lecture source ----------------
def read_frames(src, t, n_out, t_max=None):
    path, sfps = SRC[src][0], SRC[src][1]
    need = [int(round(i * sfps / FPS)) for i in range(n_out)]
    if t_max is not None: need = [min(k, int((t_max - t) * sfps)) for k in need]   # ne pas montrer l'image suivante de la régie
    p = subprocess.run([FF, "-v", "error", "-ss", "%.4f" % t, "-i", HG + "/" + path, "-frames:v", str(need[-1] + 1),
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
        m = cv2.morphologyEx(m, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))
        n_, lab, st, _ = cv2.connectedComponentsWithStats((m > 0.5).astype(np.uint8))   # garder la plus grande personne (la figure)
        if n_ > 2:
            big = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA])); keep = cv2.dilate((lab == big).astype(np.uint8), np.ones((9, 9), np.uint8))
            m = m * keep
        m = np.clip((cv2.GaussianBlur(m, (0, 0), 1.2) - 0.5) * 2.2 + 0.5, 0, 1)
        out.append(m)
    return out
LUMA = np.array([0.0722, 0.7152, 0.2126], np.float32)
def grade(x, sat=1.08):
    x = 0.82 * x + 0.18 * (x * x * (3 - 2 * x))
    L = x @ LUMA
    return np.clip(L[..., None] + (x - L[..., None]) * sat, 0, 1)
SEP_DARK, SEP_MID, SEP_LIGHT = hexc("#2A1A0E"), hexc("#8A6440"), hexc("#F3E6CC")
def sepia(x):
    """Tirage 2017 : luminance -> virage sépia (noirs bruns, blancs crème), contraste doux, voile."""
    L = x @ LUMA; L = L / max(float(np.percentile(L, 99)), 0.25); L = np.clip(L, 0, 1)
    L = 0.08 + 0.86 * (0.7 * L + 0.3 * (L * L * (3 - 2 * L)))
    lo = np.clip(L * 2, 0, 1)[..., None]; hi = np.clip(L * 2 - 1, 0, 1)[..., None]
    return np.where(L[..., None] < 0.5, SEP_DARK * (1 - lo) + SEP_MID * lo, SEP_MID * (1 - hi) + SEP_LIGHT * hi).astype(np.float32)
def tone(x, kind):
    return sepia(x) if kind == "sepia" else grade(x, 1.22)
def cutout_rgba(img, m, box, kind="color", white=False):
    x0, y0, x1, y1 = box; c = tone(img[y0:y1, x0:x1], kind)
    if white: c = np.ones_like(c) * np.array([0.96, 0.97, 0.98], np.float32)
    return np.dstack([c, m]).astype(np.float32)

# ---------------- matières du collage : déchirures, scotch, coins d'album, bandes, trame ----------------
def skey(x): return sum((i + 1) * ord(c) for i, c in enumerate(str(x)))
def torn_mask(h, w, rng, rough=7, step=14, inset=8):
    pts = []
    for x in np.arange(inset, w - inset, step): pts.append((x, inset + rng.uniform(-rough, rough)))
    for y in np.arange(inset, h - inset, step): pts.append((w - inset + rng.uniform(-rough, rough), y))
    for x in np.arange(w - inset, inset, -step): pts.append((x, h - inset + rng.uniform(-rough, rough)))
    for y in np.arange(h - inset, inset, -step): pts.append((inset + rng.uniform(-rough, rough), y))
    m = np.zeros((h, w), np.float32); cv2.fillPoly(m, [np.array(pts, np.int32)], 1.0, lineType=cv2.LINE_AA)
    return m
def tape_rgba(w, h, rng, col=(0.74, 0.86, 0.91), alpha=0.78):
    m = np.ones((h, w), np.float32)
    for y in range(h):
        a = int(rng.integers(0, 7)); b = int(rng.integers(0, 7)); m[y, :a] = 0; m[y, w - b:] = 0
    c = np.array(col, np.float32)[None, None, :] * (1 + 0.04 * rng.standard_normal((h, w, 1)).astype(np.float32))
    return np.dstack([c, m * alpha]).astype(np.float32)
def halftone(h, w, col, dot=(0.12, 0.10, 0.10), step=14):
    img = np.ones((h, w, 3), np.float32) * col[None, None, :]
    for y in range(0, h, step):
        for x in range((y // step % 2) * step // 2, w, step): cv2.circle(img, (x, y), 4, dot, -1, cv2.LINE_AA)
    return img
def strip_rgba(w, h, rng, colhex, ht=False):
    col = hexc(colhex); body = halftone(h, w, col) if ht else np.ones((h, w, 3), np.float32) * col[None, None, :]
    body = np.clip(body * (1 + 0.035 * cv2.GaussianBlur(rng.standard_normal((h, w)).astype(np.float32), (0, 0), 1.5))[..., None], 0, 1)
    m = torn_mask(h, w, rng, rough=9, step=12)
    out = np.zeros((h + 16, w + 16, 4), np.float32)
    out[10:10 + h, 8:8 + w, 3] = cv2.GaussianBlur(m, (0, 0), 3) * 0.45
    a = m[..., None]; out[:h, :w, :3] = body * a; out[:h, :w, 3] = np.maximum(m, out[:h, :w, 3])
    return out
STRIPS_2017 = [SEPCREAM, OLDRED, "#6B4A2E", "#D8C29C", "#3A2A1E", "#C9A77A"]
STRIPS_2026 = [TANG, TURQ, FUCH, COBALT, CREAM, "#FFE13C", INK, "#FFFFFF"]
def make_strips(sh):
    n = sh.get("strips", 0); rng = np.random.default_rng(skey(sh["id"]) + 5); out = []
    cols = STRIPS_2017 if sh.get("old") else STRIPS_2026
    zones = [(150, 480), (930, 560), (120, 1250), (960, 1300), (540, 300), (540, 1700), (230, 900), (880, 1050)]
    for k in range(n):
        w, h = int(rng.uniform(380, 660)), int(rng.uniform(80, 170))
        colhex = cols[(k + skey(sh["id"])) % len(cols)]
        if colhex == sh.get("bg"): colhex = cols[(k + 3) % len(cols)]
        cx, cy = zones[(k * 3 + skey(sh["id"])) % len(zones)]
        out.append(dict(img=strip_rgba(w, h, rng, colhex, ht=(k % 3 == 1)), cx=cx + rng.uniform(-60, 60), cy=cy + rng.uniform(-60, 60),
                        ang=rng.uniform(-28, 28), k=k))
    return out
def corner_rgba(sz=46, col=(0.07, 0.06, 0.05)):
    """Coin photo d'album (triangle de papier noir)."""
    m = np.zeros((sz, sz), np.float32); cv2.fillPoly(m, [np.array([(0, 0), (sz, 0), (0, sz)], np.int32)], 1.0, lineType=cv2.LINE_AA)
    return np.dstack([np.ones((sz, sz, 3), np.float32) * np.array(col, np.float32), m * 0.96])
CORNER = corner_rgba()
class Photo:
    """Photo vivante : tirage sépia (2017) ou couleur (2026), bord déchiré, scotch ou coins d'album, ombre ; saute sur les frappes."""
    def __init__(self, frames, box, width, center, angle, f0, key, kind="sepia", border=16, corners=False):
        self.frames, self.box, self.width, self.center, self.angle, self.f0, self.key, self.kind = frames, box, width, center, angle, f0, key, kind
        x0, y0, x1, y1 = box; self.h = int(round(width * (y1 - y0) / (x1 - x0))); self.b = border
        rng = np.random.default_rng(skey(key)); M = 40
        self.M = M; hh, ww = self.h + 2 * border, width + 2 * border
        self.mask = torn_mask(hh, ww, rng, rough=5 if kind == "sepia" else 3, step=11, inset=3)
        self.shadow = np.zeros((hh + 2 * M, ww + 2 * M), np.float32); self.shadow[M + 9:M + 9 + hh, M + 7:M + 7 + ww] = self.mask * 0.5
        self.shadow = cv2.GaussianBlur(self.shadow, (0, 0), 4)
        self.paper = np.array([0.80, 0.88, 0.93], np.float32) if kind == "sepia" else np.array([0.97, 0.97, 0.97], np.float32)
        tcol = (0.62, 0.78, 0.86) if kind == "sepia" else (0.80, 0.92, 0.95)
        self.tape_imgs = []
        if not corners:
            for t, (tx, ty), ta in ((tape_rgba(int(rng.uniform(110, 150)), 38, rng, tcol), (M + int(rng.uniform(-10, 30)), M - 12), rng.uniform(-40, -25)),
                                    (tape_rgba(int(rng.uniform(110, 150)), 38, rng, tcol), (M + ww - int(rng.uniform(90, 140)), M + hh - 26), rng.uniform(-40, -25))):
                R = cv2.getRotationMatrix2D((t.shape[1] / 2, t.shape[0] / 2), ta, 1.0)
                c = np.abs(R[:, :2]) @ np.array([t.shape[1], t.shape[0]]); R[0, 2] += c[0] / 2 - t.shape[1] / 2; R[1, 2] += c[1] / 2 - t.shape[0] / 2
                self.tape_imgs.append((cv2.warpAffine(t, R, (int(c[0]), int(c[1]))), (tx, ty)))
        else:
            for k, (tx, ty) in ((0, (M - 6, M - 6)), (1, (M - 6, M + hh - 40)), (2, (M + ww - 40, M + hh - 40)), (3, (M + ww - 40, M - 6))):
                self.tape_imgs.append((np.ascontiguousarray(np.rot90(CORNER, k=k)), (tx, ty)))
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
BEATS = sorted(k for k in KICKS if k < END + 0.01); BEATF = [fr(b) for b in BEATS]   # kicks réels (y compris filtrés du break)
def nbeat(f): return sum(1 for b in BEATF if b <= f)
def jit(key, k, amp=8.0, ang=1.5):
    r = np.random.default_rng(skey(key) * 1000 + k); return r.uniform(-amp, amp), r.uniform(-amp, amp), r.uniform(-ang, ang)
_scr = {}
def screen(h, w, cell=13):
    if (h, w) not in _scr:
        y, x = np.mgrid[0:h, 0:w].astype(np.float32); u, v = (x + y) / 1.4142, (x - y) / 1.4142
        _scr[(h, w)] = (np.cos(2 * np.pi * u / cell) + np.cos(2 * np.pi * v / cell)) / 4 + 0.5
    return _scr[(h, w)]
def ghost_rgba(img, m, box, sc, colhex):
    """Double tirage en trame d'imprimerie (points à 45°) de la découpe, couleur unie (copie lot6 R6) : posé derrière la découpe."""
    x0, y0, x1, y1 = box; w, h = int((x1 - x0) * sc), int((y1 - y0) * sc)
    L = img[y0:y1, x0:x1] @ LUMA; L = np.clip(L / max(float(np.percentile(L, 99)), 0.2) * 1.3, 0, 1)
    L = cv2.resize(L, (w, h), interpolation=cv2.INTER_AREA); mm = cv2.resize(m, (w, h), interpolation=cv2.INTER_AREA)
    ink = np.clip(((1 - L) * 0.9 + 0.08 - screen(h, w)) * 6, 0, 1) * mm
    return np.dstack([np.ones((h, w, 3), np.float32) * hexc(colhex)[None, None, :], ink * 0.95]).astype(np.float32)
def sticker(m, r=7):
    return cv2.dilate(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1)))
TORN_EDGES = None
def torn_edges():
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
# cadres source (sans sous-titres incrustés y > 890, ni interprète LSF x > 1630, ni pancartes, ni pupitre à logo, ni filigrane Valence)
M_WIDE1 = (640, 120, 1420, 880)      # plan large scène (côté gauche), Mélenchon au centre
M_WIDE2 = (620, 100, 1400, 880)      # plan large scène (côté port)
M_WIDE2_CUT = (800, 300, 1230, 760)
M_WIDE1_CUT = (820, 280, 1180, 765)  # détourage dans le plan large côté gauche  # détourage dans le plan large côté port (au-dessus des têtes de la foule)
M_CROWD = (0, 0, 1620, 890)          # foule (synchro, 24,76-27,72)
M_CLOSE = (300, 0, 1600, 890)        # gros plan Vieux-Port
HUMA_BOX = (380, 40, 1460, 800)      # Fête de l'Huma : au-dessus du pupitre (logo hors champ)
VAL_BOX = (480, 20, 1500, 820)       # Valence : au-dessus du pupitre, filigrane hors champ (x > 1560)
VAL_CROWD_A = (0, 180, 1560, 1080); VAL_CROWD_B = (0, 280, 1500, 1080)
SP, PP = SEPIA_STYLES, POP_STYLES
# photo = (source, t (None = synchro avec la voix), cadre, largeur, (cx, cy), angle, apparition (s dans le plan), tirage, coins d'album)
SHOTS = [
    # ---- 2017 (en couleur) : son direct, images synchro de la régie, Mélenchon découpé sur aplats qui changent sur les frappes ----
    dict(id="A1", kind="cut", src="CASTE", bgs=[TANG, FUCH, TANG, COBALT], ghost=COBALT, box=M_WIDE1_CUT, scale=(2.42, 2.50), cx=990, tmax=SRC_CUTS[0] - 0.02,
         txt=[[("IL", wt(0)), ("FAUT", wt(1))], [("QUE", wt(2)), ("SOIT", wt(3))], [("MIS", wt(4)), ("UN", wt(5))]], txt_y=262, txt_h=168, styles=PP,
         strips=3, why="2017 — Vieux-Port, plan large synchro (« Il faut que soit mis un… ») : Mélenchon découpé en couleur, contour autocollant, double tramé cobalt, aplat qui change sur les frappes"),
    dict(id="A2", kind="collage", bgs=[TURQ, FUCH, COBALT, TANG],
         photos=[("CASTE", None, M_CROWD, 880, (540, 1130), 2, 0.0, "color", False),
                 ("CASTE", 24.70, M_WIDE1, 440, (770, 1560), 6, TB, "color", False, True),
                 ("CASTE", 35.8, (200, 0, 1620, 890), 470, (290, 1600), -7, TB * 3, "color", False),
                 ("CASTE", 47.6, (0, 0, 1620, 890), 460, (640, 1760), 4, TB * 5, "color", False)],
         tmax=SRC_CUTS[1] - 0.02,
         txt=[[("TERME", wt(6)), ("À", wt(7))], [("CETTE", wt(8))], [("CASTE", wt(9))], [("DORÉE", wt(10))]], txt_y=260, txt_h=160, styles=PP,
         strips=4, why="2017 — plan synchro de la foule (« …terme à… cette caste dorée ») : tirages couleur scotchés sur un aplat qui change à chaque frappe ; tirage synchro figé sur ses 0,45 dernières s (la régie repasse au plan large) + photo fixe du plan large + foule (autres moments, sans lui)"),
    dict(id="A3", kind="cut", src="CASTE", bgs=[COBALT, TURQ, COBALT, FUCH], ghost=TANG, box=M_WIDE2_CUT, scale=(2.38, 2.46), cx=1010,
         photos=[("CASTE", 34.6, (200, 0, 1620, 890), 600, (300, 1150), -6, 0.0, "color", False), ("CASTE", 47.5, (0, 0, 1620, 890), 560, (820, 1420), 5, TB * 2, "color", False)],
         txt=[[("CASTE", 0.0)], [("DORÉE", 0.0)], [("DE", wt(11)), ("PARASITES", wt(12))]], txt_y=250, txt_h=150, styles=PP, letters=("CASTE", "DORÉE"),
         strips=4, why="2017 — plan large synchro (« caste dorée de parasites ») : Mélenchon découpé en couleur, double tramé mandarine, tirages couleur de la foule (autres moments, sans lui)"),
    dict(id="A4", kind="cut", src="CASTE", bgs=[FUCH, TANG, FUCH, TURQ], ghost=TURQ, box=M_WIDE2_CUT, scale=(2.50, 2.62), cx=1010,
         photos=[("CASTE", 43.3, (0, 0, 1620, 890), 520, (250, 1180), -8, TB * 1, "color", False),
                 ("CASTE", 48.4, (0, 0, 1620, 890), 500, (850, 1250), 7, TB * 3, "color", False), ("CASTE", 57.9, (0, 0, 1620, 890), 480, (300, 1560), -3, TB * 4, "color", False)],
         txt=[[("INCAPABLES", wt(13))], [("INUTILES", wt(14))]], txt_y=290, txt_h=150, styles=PP, letters=("INUTILES",),
         strips=5, why="2017 — plan large synchro (« incapables, inutiles ») : Mélenchon découpé en couleur, double tramé turquoise, un tirage de la foule de plus sur les frappes du break"),
    # ---- 2026 : au drop, le collage revient en couleurs franches (musique seule) ----
    # textes (règle Luca 27/10) : un carton complet par plan, dans l'ordre de la phrase puis sa conclusion, jamais répété :
    # CETTE CASTE DORÉE / DE PARASITES / INCAPABLES. / INUTILES. / IL FAUT Y METTRE UN TERME. / (B6, B7 sans texte) / carton final
    dict(id="B1", kind="cut", src="HUMA", t=62.4, bg=TANG, box=HUMA_BOX, scale=(1.50, 1.54), cx=900, flash=True, ghost=FUCH,
         txt=[[("CETTE", 0.0)], [("CASTE", 0.1)], [("DORÉE", 0.2)]], txt_y=262, txt_h=155, styles=PP, letters=("CASTE", "DORÉE"),
         strips=4, why="2026 — Fête de l'Huma, bras tendu : flash blanc du drop, Mélenchon détouré en couleur sur mandarine, contour autocollant"),
    dict(id="B2", kind="collage", bg=TURQ,
         photos=[("VAL", 30.0, VAL_CROWD_A, 720, (520, 820), -4, 0.0, "color", False), ("HUMA", 75.0, (0, 0, 1920, 1080), 560, (340, 1300), 5, TB * 0.5, "color", False),
                 ("VAL", 102.0, VAL_CROWD_B, 600, (700, 1580), -3, TB, "color", False)],
         txt=[[("DE", 0.0)], [("PARASITES", 0.07)]], txt_y=270, txt_h=165, styles=PP,
         strips=3, why="2026 — collage couleur : foules de Valence (drapeaux) et de la Fête de l'Huma sur turquoise"),
    dict(id="B3", kind="full", src="HUMA", t=73.6, crop=(380, 540, 1080), push=(1.0, 1.05), focus=(380, 600), flash=True,
         big=[("INCAPABLES.", 0.0, (250, 250, 250))], big_y=820, big_sizes=[190],
         why="2026 — Fête de l'Huma, la foule plein cadre en couleur, bords déchirés ; gros mot blanc avec contour"),
    dict(id="B4", kind="sil", src="VAL", t=147.4, bg=FUCH, ghost=COBALT, box=VAL_BOX, dest_w=1290, cx=1000, push=(1.0, 1.035),
         txt=[[("INUTILES.", 0.0)]], txt_y=300, txt_h=180, styles=PP, letters=("INUTILES.",),
         strips=3, why="2026 — Valence, index levé : silhouette blanche 3 images puis Mélenchon en couleur sur fuchsia"),
    dict(id="B5", kind="cut", src="HUMA", t=85.3, bg=COBALT, ghost=TANG, box=(450, 80, 1400, 800), scale=(1.62, 1.66), cx=880,
         photos=[("VAL", 33.0, VAL_CROWD_A, 560, (290, 760), -6, 0.0, "color", False)],
         txt=[[("IL", 0.0), ("FAUT", 0.07), ("Y", 0.14)], [("METTRE", 0.21)], [("UN", 0.28), ("TERME.", 0.35)]], txt_y=250, txt_h=150, styles=PP,
         strips=3, why="2026 — Fête de l'Huma, Mélenchon détouré sur cobalt + tirage couleur de la foule de Valence ; conclusion : IL FAUT Y METTRE UN TERME."),
    dict(id="B6", kind="collage", bgs=[TANG, TURQ, FUCH, COBALT],
         photos=[("CASTE", 39.5, M_CLOSE, 760, (520, 760), -4, 0.0, "color", False), ("HUMA", 12.0, (520, 40, 1720, 800), 700, (560, 1080), 5, TB, "color", False),
                 ("VAL", 203.4, (380, 20, 1500, 815), 640, (470, 1430), -5, TB * 2, "color", False), ("VAL", 26.0, VAL_CROWD_A, 600, (600, 1720), 3, TB * 3, "color", False)],
         strips=3, why="collage couleur : gros plan du Vieux-Port 2017 recouvert, frappe après frappe, par les tirages de 2026 (Huma, Valence) sur un aplat qui change à chaque frappe — sans texte"),
    dict(id="B7", kind="sil", src="HUMA", t=165.0, bg=TURQ, ghost=FUCH, box=(520, 60, 1460, 800), dest_w=1240, cx=1000, push=(1.0, 1.035),
         strips=3, why="2026 — Fête de l'Huma : silhouette blanche puis Mélenchon en couleur sur turquoise"),
    dict(id="FIN", kind="card", bg=CREAM, push=(1.0, 1.035),
         big=[("JEAN-LUC", 0.0, rgb(INK)), ("MÉLENCHON", TB, rgb(FUCH)), ("2027", 2 * TB, rgb(TANG))],
         big_y=560, big_sizes=[300, 300, 420], big_font="impact",
         why="carton final propre (fond crème, noir + fuchsia + mandarine) : son nom et 2027 (année de l'élection), bien visible"),
]
BOUNDS_T = [0] + CUTF + [ENDF]
assert len(BOUNDS_T) == len(SHOTS) + 1, (len(BOUNDS_T), len(SHOTS))
for i, sh in enumerate(SHOTS):
    sh["a"], sh["bb"] = BOUNDS_T[i], BOUNDS_T[i + 1]; sh["n"] = sh["bb"] - sh["a"]; sh["clip"] = "R3_%s.mov" % sh["id"]
    if sh.get("src") == "CASTE" and sh.get("t") is None: sh["t"] = V_SRC0 + sh["a"] / FPS          # plans synchro avec la voix
assert min(sh["n"] for sh in SHOTS) >= 15, [(s["id"], s["n"]) for s in SHOTS]
for sh in SHOTS:                                                         # images synchro : jamais l'autre côté d'une coupe de la régie
    if sh["id"].startswith("A"):
        s0, s1 = V_SRC0 + sh["a"] / FPS, V_SRC0 + sh["bb"] / FPS
        for c in SRC_CUTS:                                               # coupe de la régie dans le plan : tirages synchro figés juste avant
            if s0 + 0.06 < c < s1 - 0.02: assert sh.get("tmax") and sh["tmax"] < c and s1 - c < 0.6, (sh["id"], s0, s1, c)

SCENES = {"CASTE": [19.88, 24.76, 27.72, 33.80, 39.40, 43.24, 46.88, 51.40, 57.84, 60.96],
          "HUMA": [4.58, 70.64, 79.92, 105.22, 110.62, 114.82, 118.5, 139.88, 144.36, 147.72, 193.36, 206.58],
          "VAL": [7.27, 18.57, 24.93, 39.9, 49.5, 55.8, 62.07, 71.9, 78.33, 93.13, 98.57, 106.8, 113.2, 155.57, 161.37, 174.8, 211.73]}
for sh in SHOTS:                                                         # coupes des captations (ffmpeg scene) : jamais dans la partie visible
    items = [(p[0], p[1], p[6], len(p) > 9 and p[9]) for p in sh.get("photos", []) if p[1] is not None]
    if sh.get("src") and not sh["id"].startswith("A"): items.append((sh["src"], sh["t"], 0.0, False))
    for src, t0, ap, frz in items:
        if frz: continue
        v0, v1 = t0 + ap, t0 + sh["n"] / FPS
        assert not any(v0 < c < v1 for c in SCENES[src]), ("coupe de la source dans", sh["id"], src, t0, v0, v1)
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
    sync = sh["id"].startswith("A")                                          # textes des plans A : temps absolus de la voix
    tpos = lambda p: [(im, cx, cy, (max(t, sh["a"] / FPS) if sync else rel(t))) for im, cx, cy, t in p]
    txt = tpos(board(sh["txt"], sh["txt_y"], seed=skey(sh["id"]) * 7, styles=sh["styles"], letters=sh.get("letters", ()),
                     h=sh.get("txt_h", 118))) if sh.get("txt") else []
    big = []
    if sh.get("big"):
        big = [(im, cx, cy, rel(t)) for im, cx, cy, t in
               big_text([(s, t, c) for s, t, c in sh["big"]], sh["big_y"], sizes=sh["big_sizes"], spec=((S + "Impact.ttf", 0) if sh.get("big_font") else FCOND),
                        maxw=(XMAX - XMIN) * (0.86 if sh["kind"] == "card" else 1.0), contour=10 if sh["kind"] == "full" else 0)]
    t_sync = V_SRC0 + a / FPS
    photos = []
    for j, p in enumerate(sh.get("photos", [])):
        ps, pt, pbox, pw, pc, pa, pt0, pk, pcorn = p[:9]; freeze = len(p) > 9 and p[9]       # freeze : photo fixe (une seule image)
        tt = t_sync if pt is None else pt
        tm = tt if freeze else (sh.get("tmax") if pt is None else None)
        photos.append(Photo(read_frames(ps, tt, n, tm), pbox, pw, pc, pa, fr(rel(pt0)), (sh["id"], j), pk, corners=pcorn))
    strips = make_strips(sh)
    k0 = nbeat(a); old = sh.get("old", False); kind_tone = "sepia" if old else "color"
    if sh["kind"] in ("cut", "sil", "full"):
        raw = read_frames(sh["src"], sh["t"], n, sh.get("tmax"))
    if sh["kind"] in ("cut", "sil"):
        ms = masks("%s_%s_%.2f_%d" % (sh["id"], sh["src"], sh["t"], n), raw, sh["box"], k=27 if sh["kind"] == "sil" else 13)
    for i in range(n):
        f = a + i; u = i / max(n - 1, 1); kb = nbeat(f) - k0
        if sh["kind"] == "full":
            cx, cy, vh = sh["crop"]; z = sh["push"][0] + (sh["push"][1] - sh["push"][0]) * u
            s = H / vh * z; fx_, fy_ = sh["focus"]
            ccx = cx + (fx_ - cx) * (1 - 1 / z); ccy = cy + (fy_ - cy) * (1 - 1 / z)
            M = np.float32([[s, 0, W / 2 - ccx * s], [0, s, H / 2 - ccy * s]])
            img = grade(cv2.warpAffine(raw[i], M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE), 1.2)
        else:
            img = paper(sh["bgs"][kb % len(sh["bgs"])] if sh.get("bgs") else sh["bg"], sh.get("fibre", False))   # aplat qui change sur les frappes
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
        if sh["kind"] == "cut":
            x0, y0, x1, y1 = sh["box"]; sc = sh["scale"][0] + (sh["scale"][1] - sh["scale"][0]) * u
            m = ms[i]; rgba = cutout_rgba(raw[i], m, sh["box"], kind_tone); hh = (y1 - y0) * sc
            stc = np.array([0.88, 0.93, 0.95], np.float32) if old else np.array([0.96, 0.96, 0.95], np.float32)
            st_ = np.dstack([np.ones_like(rgba[..., :3]) * stc, sticker(m, 5 if old else 7)])
            sd = st_.copy(); sd[..., :3] = 0; sd[..., 3] = cv2.GaussianBlur(st_[..., 3], (0, 0), 5) * 0.5
            fcx = (sh["cx"] - x0) * sc; ccx = W / 2 + ((x1 - x0) / 2 * sc - fcx); ccy = sh.get("bottom", H) - hh / 2
            if sh.get("ghost"):                                             # double tirage tramé, décalé, qui saute sur les temps
                gdx, gdy, gda = jit((sh["id"], "g"), nbeat(f), amp=10, ang=1.0)
                paste(img, ghost_rgba(raw[i], m, sh["box"], sc, sh["ghost"]), ccx + 46 + gdx, ccy - 34 + gdy, 1.10, -2.5 + gda)
            paste(img, sd, ccx + 10, ccy + 8, sc); paste(img, st_, ccx, ccy, sc); paste(img, rgba, ccx, ccy, sc)
        elif sh["kind"] == "sil":
            x0, y0, x1, y1 = sh["box"]; z = sh["push"][0] + (sh["push"][1] - sh["push"][0]) * u
            sc = sh["dest_w"] / (x1 - x0) * z; hh = (y1 - y0) * sc; m = ms[i]
            ccx = W / 2 + ((x1 - x0) / 2 - (sh["cx"] - x0)) * sc; ccy = H - hh / 2
            st_ = np.dstack([np.ones((m.shape[0], m.shape[1], 3), np.float32) * np.array([0.96, 0.96, 0.95], np.float32), sticker(m, 9)])
            sd = st_.copy(); sd[..., :3] = 0; sd[..., 3] = cv2.GaussianBlur(st_[..., 3], (0, 0), 6) * 0.55
            if sh.get("ghost"):
                gdx, gdy, gda = jit((sh["id"], "g"), nbeat(f), amp=10, ang=1.0)
                paste(img, ghost_rgba(raw[i], m, sh["box"], sc, sh["ghost"]), ccx + 46 + gdx, ccy - 34 + gdy, 1.10, -2.5 + gda)
            paste(img, sd, ccx + 14, ccy + 10, sc)
            if i < 3: paste(img, cutout_rgba(raw[i], m, sh["box"], white=True), ccx, ccy, sc)     # silhouette blanche : 3 images
            else: paste(img, st_, ccx, ccy, sc); paste(img, cutout_rgba(raw[i], m, sh["box"], kind_tone), ccx, ccy, sc)
        if sh["kind"] == "full":
            te = torn_edges(); img = img * (1 - te[..., 3:4]) + te[..., :3]
        draw_pieces(img, txt, f, boil=sh["id"])
        if sh["kind"] == "card":
            for j, (tx, ty, ta) in enumerate(((175, 360, -32), (905, 360, 30), (175, 1480, 28), (905, 1480, -30))):
                paste(img, CARD_TAPES[j], tx, ty, 1.0, ta)
        if big:
            if sh["kind"] == "card":
                z = sh["push"][0] + (sh["push"][1] - sh["push"][0]) * u
                for im, cx, cy, t in big:
                    s_ = pop(f, fr(t))
                    if s_ is not None: paste(img, im, W / 2 + (cx - W / 2) * z, H / 2 + (cy - H / 2) * z, s_ * z)
            else: draw_pieces(img, big, f)
        if sh.get("flash") and i < 3: img = img + (1 - img) * [1.0, 0.6, 0.25][i]   # aplat blanc : flash de transition (1 image pleine + 2 de fondu)
        frames.append(finish(img, f, old))
    write_mov(frames, OUT + sh["clip"])
    print("  %-4s %3d im  (%s)" % (sh["id"], n, sh["kind"]), flush=True)

# ---------------- audio ----------------
VGAIN = -1.0                                 # voix déjà forte dans la captation : -1 dB (≈ -14 LUFS sur la phrase, musique ≈ 12 dB dessous)
def make_audio():
    import soundfile as sf
    sr = 48000; N = int(round(END * sr))
    def grab(path, t, dur):
        p = subprocess.run([FF, "-v", "error", "-ss", "%.3f" % t, "-t", "%.3f" % dur, "-i", path, "-ac", "2", "-ar", str(sr), "-f", "f32le", "-"], capture_output=True)
        return np.frombuffer(p.stdout, np.float32).reshape(-1, 2).copy()
    voix = np.zeros((N, 2), np.float32); mus = np.zeros((N, 2), np.float32)
    v = grab(HG + "/" + SRC["CASTE"][0], V_IN, V_OUT - V_IN); env = np.ones(len(v), np.float32)
    k = int(0.03 * sr); env[:k] = np.linspace(0, 1, k); k = int(0.10 * sr); env[-k:] = np.linspace(1, 0, k)
    i0 = int(round(t_of_src(V_IN) * sr)); voix[i0:i0 + len(v)] = v * env[:, None] * 10 ** (VGAIN / 20)
    m = music_raw(MUSIC_IN)[:N]
    t = np.arange(len(m)) / sr; brk = 174.40 - MUSIC_IN; vend = t_of_src(32.35); dr = CUTS[3]
    # sous la phrase : -14 dB (fin du refrain), montée dans le break filtré (-13 -> -8 dB), plein au drop
    gdb = np.interp(t, [0, 0.3, brk, vend, dr - 0.03, dr, END], [-24, -14, -13, -8, -5, 0, 0])
    k = int(0.40 * sr); fo = np.ones(len(m), np.float32); fo[-k:] = np.linspace(1, 0, k)
    mus[:len(m)] = m * (10 ** (gdb / 20) * fo)[:, None]
    sf.write(OUT + "R3-voix.wav", voix, sr, subtype="PCM_24"); sf.write(OUT + "R3-musique.wav", mus, sr, subtype="PCM_24")
    sf.write(D + "tmp_mix.wav", voix + mus, sr, subtype="FLOAT")
    r = subprocess.run([FF, "-hide_banner", "-i", D + "tmp_mix.wav", "-af", "loudnorm=I=-14:TP=-2.5:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    js = json.loads(r[r.rindex("{"):r.rindex("}") + 1])
    af = ("loudnorm=I=-14:TP=-2.5:LRA=11:measured_I=%s:measured_TP=%s:measured_LRA=%s:measured_thresh=%s:offset=%s:linear=true,"
          "aresample=48000" % (js["input_i"], js["input_tp"], js["input_lra"], js["input_thresh"], js["target_offset"]))
    subprocess.run([FF, "-v", "error", "-y", "-i", D + "tmp_mix.wav", "-af", af, "-c:a", "pcm_s24le", OUT + "R3-mix.wav"], check=True)
    os.remove(D + "tmp_mix.wav"); print("audio : mix avant normalisation", js["input_i"], "LUFS")

# ---------------- plan ----------------
PHRASE = "Il faut que soit mis un terme à cette caste dorée de parasites incapables, inutiles."
def build_plan():
    video = []
    for sh in SHOTS:
        v = {"id": sh["id"], "clip": sh["clip"], "folder": "genR3", "path": OUT + sh["clip"], "s": 0, "e": sh["n"], "rec": sh["a"], "dur": sh["n"],
             "clip_fps": FPS, "speed_pct": 100, "track": 1, "note": sh["why"], "kind": sh["kind"], "temps": round(sh["n"] / FPS / T, 2)}
        if sh.get("src"):
            path, sfps, url, off, ctx = SRC[sh["src"]]
            v["source"] = {"fichier": path, "in_s": round(sh["t"], 3), "out_s": round(sh["t"] + sh["n"] / FPS, 3), "fps": sfps, "url": url,
                           "t_youtube_s": round(off + sh["t"], 2), "contexte": ctx}
        if sh.get("photos"):
            v["photos"] = [{"fichier": SRC[p[0]][0], "in_s": round(p[1] if p[1] is not None else V_SRC0 + sh["a"] / FPS, 3), "cadre_source": p[2],
                            "tirage": p[7], "url": SRC[p[0]][2], "synchro": p[1] is None} for p in sh["photos"]]
        video.append(v)
    texts = []
    for sh in SHOTS:
        for line in sh.get("txt", []): texts.append({"plan": sh["id"], "texte": " ".join(w for w, _ in line)})
        for s_, t_, c_ in sh.get("big", []): texts.append({"plan": sh["id"], "texte": s_})
    yt = SRC["CASTE"][3]
    plan = {"name": "R3 - Collage ransom-note - Jean-Luc Mélenchon (album 2017 -> 2026)", "fps": FPS, "w": W, "h": H, "duree_s": round(END, 3),
            "note": "Plans ProRes 9:16 composés en Python (lot6/_claude/gen/R3/out) : Mélenchon détouré (segment/Vision) sur aplats vifs (mandarine, "
                    "turquoise, fuchsia, cobalt) qui changent sur les frappes, contour autocollant, double tirage tramé, bandes, scotch, tirages couleur "
                    "(2017 avant le drop, 2026 après), silhouettes blanches 3 images, foule plein cadre, textes ransom-note cuits. s/e en images du clip (30 i/s), "
                    "rec en images timeline. Coupes sur les kicks réels de Music Sounds Better With You (out/R3-frappes.json). Aucun ralenti. Générateur : genR3.py",
            "phrase": {"texte": PHRASE, "url": SRC["CASTE"][2], "source": SRC["CASTE"][0], "in_s": 23.40, "out_s": 32.35,
                       "t_youtube_s": [round(yt + 23.40, 2), round(yt + 32.35, 2)],
                       "timeline_s": [round(t_of_src(23.40), 2), round(t_of_src(32.35), 2)],
                       "voix": "son direct, images synchro de la régie d'origine (plan large, foule, plan large) ; pause naturelle de 1,4 s après « à » gardée ; "
                               "applaudissements coupés en fondu après « inutiles »"},
            "musique": {"fichier": "lot6/sons/R3-stardust-music-sounds-better_complet.wav", "titre": "Stardust - Music Sounds Better With You", "url": SON_URL,
                        "debut_complet_s": round(MUSIC_IN, 4), "fin_complet_s": round(MUSIC_IN + END, 3), "drop_timeline_s": round(CUTS[3], 4),
                        "coupes_kicks_s": [round(c, 4) for c in CUTS], "coupes_images": CUTF},
            "textes": texts, "video": video,
            "audio": [{"id": "mix", "clip": "R3-mix.wav", "folder": "genR3", "path": OUT + "R3-mix.wav", "rec": 0, "track": 1,
                       "note": "mix -14 LUFS : voix %.2f-%.2f s (+%g dB) à %.2f s ; Stardust dès %.3f s du complet, -14 dB sous la voix, montée dans le break, "
                               "plein au drop, fondu de fin 0,4 s" % (V_IN, V_OUT, VGAIN, t_of_src(V_IN), MUSIC_IN)}],
            "stems": ["lot6/_claude/gen/R3/out/R3-voix.wav", "lot6/_claude/gen/R3/out/R3-musique.wav"],
            "logos_exclus": "Marseille : sous-titres incrustés, interprète LSF et pancartes hors cadres ; Huma et Valence : pupitres (logos) sous la découpe, "
                            "filigrane MELENCHON 2027 de Valence hors cadre"}
    json.dump(plan, open(D + "plan-R3.json", "w"), indent=1, ensure_ascii=False)
    son = {"id": "R3", "titre": "Music Sounds Better With You", "artiste": "Stardust", "url": SON_URL,
           "chaine": "Stardust (officielle, « Stardust - Music Sounds Better With You (Official Music Video) »)",
           "fichier": "lot6/sons/R3-stardust-music-sounds-better_complet.wav",
           "extrait_complet_s": {"debut": round(MUSIC_IN, 4), "fin": round(MUSIC_IN + END, 3)},
           "paroles_audibles": "sous la phrase : fin du refrain (« Love might bring us back together ») puis break filtré ; juste avant le drop « Ooh baby » ; "
                               "après : « I feel right, the music sounds better with you »",
           "bpm": round(60 / T, 1), "temps_s": T,
           "drop": {"complet_s": round(MUSIC_IN + CUTS[3], 4), "timeline_s": round(CUTS[3], 4), "nature": "retour du kick après le break filtré, juste après « Ooh baby »"},
           "frappes_timeline_s": [round(k, 4) for k in KICKS if k <= END], "coupes_sur_frappes_s": [round(c, 4) for c in CUTS],
           "mix": "lot6/_claude/gen/R3/out/R3-mix.wav"}
    json.dump(son, open(D + "son.json", "w"), indent=1, ensure_ascii=False)

# ---------------- aperçu 540x960 ----------------
def apercu():
    plan = json.load(open(D + "plan-R3.json")); ins = []; fl = []
    for i, v in enumerate(plan["video"]):
        ins += ["-i", OUT + v["clip"]]
        fl.append("[%d:v]trim=start_frame=%d:end_frame=%d,setpts=PTS-STARTPTS,scale=540:960,setsar=1[v%d]" % (i, v["s"], v["e"], i))
    k = len(plan["video"]); fl.append("".join("[v%d]" % i for i in range(k)) + "concat=n=%d:v=1:a=0[v]" % k)
    ins += ["-i", OUT + "R3-mix.wav"]; out = HG + "/preview/apercu-R3.mp4"
    subprocess.run([FF, "-v", "error", "-y"] + ins + ["-filter_complex", ";".join(fl), "-map", "[v]", "-map", "%d:a" % k,
                    "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "aac", "-b:a", "192k", "-shortest", out], check=True)
    print("aperçu", out)
# ---------------- mesure sur l'export : coupes vs kicks, LUFS / TP ----------------
def lowband_onset(y, c, sr=48000):
    """Attaque du kick dans la bande < 120 Hz autour de c : 1re fenêtre de 2,5 ms qui monte de 8 dB au-dessus des 20 ms précédentes."""
    import scipy.signal as ss
    m = ss.sosfiltfilt(ss.butter(4, 120, "lp", fs=sr, output="sos"), y.mean(1)); hop = 120
    a, b = int((c - 0.08) * sr), int((c + 0.08) * sr)
    e = 20 * np.log10(np.sqrt(np.convolve(m[a:b] ** 2, np.ones(hop) / hop, "same")) + 1e-9)
    for i in range(int(0.02 * sr), len(e), hop // 2):
        if e[i] > e[i - int(0.02 * sr):i].mean() + 8: return (a + i - hop // 2) / sr
    return c + 1
def mesure():
    out = HG + "/preview/apercu-R3.mp4"
    r = subprocess.run([FF, "-v", "info", "-i", out, "-vf", "scale=135:240,select='gt(scene,0.25)',showinfo", "-an", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    cuts = [float(x) for x in re.findall(r"pts_time:([0-9.]+)", r)]
    p = subprocess.run([FF, "-v", "error", "-i", out, "-vn", "-ac", "2", "-ar", "48000", "-f", "f32le", "-"], capture_output=True)
    y = np.frombuffer(p.stdout, np.float32).reshape(-1, 2)
    i0 = int((CUTS[3] - 0.3) * 48000)                                    # 2 fenêtres : avant le drop (kicks bas sous la voix) / après
    h = [x[0] for x in detect_hits(y[:i0]) if x[1] == "kick" and x[3] > 0.005] + \
        [x[0] + i0 / 48000 for x in detect_hits(y[i0:]) if x[1] == "kick" and x[3] > 0.005] + \
        [x[0] for x in detect_hits(y) if x[1] == "kick" and x[3] > 0.005]               # + fenêtre entière (la détection dépend de la fenêtre)
    print("coupes image détectées (export) :", cuts)
    worst = 0
    for c in [fr_ / FPS for fr_ in CUTF]:
        det = min(cuts, key=lambda x: abs(x - c)) if cuts else None
        k = min(h, key=lambda t: abs(t - c)); how = "détecteur"
        if abs(c - k) > 0.02: k, how = lowband_onset(y, c), "attaque < 120 Hz (détecteur pris par la voix)"
        e = (c - k) * 1000; worst = max(worst, abs(e))
        print("  coupe %.3f (détectée %s)  kick %.4f  écart %+.1f ms  [%s]" % (c, "%.3f" % det if det is not None else "-", k, e, how))
    print("écart max coupes/kicks : %.1f ms" % worst)
    r = subprocess.run([FF, "-hide_banner", "-i", out, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    print(r[r.rindex("Summary"):])
if __name__ == "__main__":
    args = set(a for a in sys.argv[1:] if not a.startswith("only=")) or {"shots", "audio", "plan", "apercu"}
    only = [x for a in sys.argv[1:] if a.startswith("only=") for x in a.split("=", 1)[1].split(",")]
    print("musique dès %.4f s ; coupes (s) :" % MUSIC_IN, [round(c, 4) for c in CUTS], "images :", CUTF, "fin", END)
    if "shots" in args or only:
        for sh in SHOTS:
            if not only or sh["id"] in only: render(sh)
    if "audio" in args: make_audio()
    if "plan" in args: build_plan()
    if "apercu" in args: apercu()
    if "mesure" in args: mesure()
