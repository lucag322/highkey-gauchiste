# R14 (lot 7) — Collage ransom-note « tract syndical collé sur un mur », Jean-Luc Mélenchon, son Eurythmics – Sweet Dreams (Are Made of This)
#   (audio officiel « 2018 Remastered », chaîne Eurythmics). Modèle : lot6/_claude/gen/R6/genR6.py (validé), même moteur (découpe Vision
#   par instance, morceaux de texte penchés serif/sans, frappes, carton final), poussé : mur d'affiches qui se recouvrent (une affiche
#   collée de plus à chaque temps, posée « au balai » de haut en bas, colle encore humide 6 images), tracts A4 jaunes à bandeau violet,
#   restes d'affiches arrachées sur les bords, photos de la manif intersyndicale en bichromie violet / jaune, scotch, trame d'imprimerie.
# Découpes : outil partagé _claude/outils/decoupe.py (lui seul), buste entier posé sur le bas du cadre (B3 : bord déchiré à mi-poitrine),
#   bonnettes des micros du pupitre rebouchées avec l'image (accepté par Luca), visages dans la zone sûre TikTok. Plans de la manif
#   non découpables proprement (voisins, écharpes, pied de micro devant le visage) : la manif sert de voix et d'affiches photo.
# Sous la voix : le plan synchro de la marche en grande photo collée (pas de découpe) et la foule ; découpes de Saint-Denis après le drop seulement.
# Palette R14 (brief) : violet électrique + jaune citron, encre prune, papier d'affiche blanc cassé (aucune couleur de R1-R6).
# Phrase (son direct, synchro) : « Nous parlons de 5 millions de nos concitoyens qui se sont mis au service des autres et qui chaque jour
#   portent ce pays sur leur dos » (manifestation intersyndicale de la fonction publique, Paris, 29/09/2026, chaîne JEAN-LUC MÉLENCHON,
#   fichier lot3/sources/C4-melenchon-intersyndicale.mp4 132,1-141,8 s). La phrase continue par « pour pouvoir le faire fonctionner »
#   (non gardé, sens inchangé). Autre phrase que C4, I1, W1, R2, R3, R4 (lus) ; plans : autres moments que C4 (116,5 s) et I1 (155, 160 s).
# Son : Sweet Dreams, extrait continu ; la phrase passe sur l'interlude instrumental du riff (39,3-49,4 s du morceau, sans paroles),
#   baissé puis qui monte ; drop = retour de « Sweet dreams are made of this » (49,4 s), puis coupes toutes les 2 temps sur les kicks réels.
# Textes après le drop (règle Luca 27/10) : 5 MILLIONS / DE NOS CONCITOYENS -> AU SERVICE / DES AUTRES -> CHAQUE JOUR ->
#   PORTENT CE PAYS / SUR LEUR DOS, puis 2 plans sans texte et le carton final JEAN-LUC MÉLENCHON + 2027.
# Usage : python genR14.py [shots] [audio] [plan] [apercu] [mesure] [only=ID,ID]   (sans argument = tout sauf mesure)
import sys
sys.dont_write_bytecode = True
import os, json, subprocess, math, re
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
HG = "/Users/luca.grousset/Movies/highkey-gauchiste"
D = HG + "/lot7/_claude/gen/R14/"; OUT = D + "out/"; CACHE = D + "cache/"; os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, D)
from hits import detect_hits
FF = "/opt/homebrew/bin/ffmpeg"; INST = D + "tools/inst"; FPS = 30; W, H = 1080, 1920
def fr(t): return int(round(t * FPS))
def hexc(h): h = h.lstrip("#"); return np.array([int(h[4:6], 16), int(h[2:4], 16), int(h[0:2], 16)], np.float32) / 255   # BGR
def rgb(h): h = h.lstrip("#"); return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
# palette R14 : violet électrique, violet clair (papier tract), jaune citron, encre prune, papier d'affiche
VIOLET, LILAC, YELLOW, INK, PAPER, WHITE = "#6A1FD0", "#CDB8F2", "#FFEA2E", "#22093F", "#F3EFE6", "#FFFFFF"

# ---------------- sources (lecture seule, lot 3) ----------------
SRC = {
    "IS": ("lot3/sources/C4-melenchon-intersyndicale.mp4", 30.0, "https://www.youtube.com/watch?v=N406os8VSkE", 0.0,
           "manifestation intersyndicale de la fonction publique, Paris, 29/09/2026 (chaîne JEAN-LUC MÉLENCHON)"),
    "SD3": ("lot3/sources/C4-melenchon-stdenis-03.mp4", 30.0, "https://www.youtube.com/watch?v=1dkY_JVFx9I", None,
            "meeting de Saint-Denis, 07/06/2026 (chaîne JEAN-LUC MÉLENCHON)"),
    "SD7": ("lot3/sources/C4-melenchon-stdenis-07.mp4", 30.0, "https://www.youtube.com/watch?v=1dkY_JVFx9I", None,
            "meeting de Saint-Denis, 07/06/2026, foule et drapeaux (chaîne JEAN-LUC MÉLENCHON)"),
    "SD2": ("lot3/sources/C4-melenchon-stdenis-02.mp4", 30.0, "https://www.youtube.com/watch?v=1dkY_JVFx9I", None,
            "meeting de Saint-Denis, 07/06/2026 (chaîne JEAN-LUC MÉLENCHON)"),
    "SD5": ("lot3/sources/C4-melenchon-stdenis-05.mp4", 30.0, "https://www.youtube.com/watch?v=1dkY_JVFx9I", None,
            "meeting de Saint-Denis, 07/06/2026 (chaîne JEAN-LUC MÉLENCHON)"),
    "SD6": ("lot3/sources/C4-melenchon-stdenis-06.mp4", 30.0, "https://www.youtube.com/watch?v=1dkY_JVFx9I", None,
            "meeting de Saint-Denis, 07/06/2026 (chaîne JEAN-LUC MÉLENCHON)"),
    "SD1": ("lot3/sources/C4-melenchon-stdenis-01.mp4", 30.0, "https://www.youtube.com/watch?v=1dkY_JVFx9I", None,
            "meeting de Saint-Denis, 07/06/2026, place vue d'en haut (chaîne JEAN-LUC MÉLENCHON)"),
}

# ---------------- musique : Eurythmics – Sweet Dreams (Are Made of This) ----------------
SON_FILE = HG + "/lot7/sons/R14-eurythmics-sweet-dreams_complet.wav"; SON_URL = "https://www.youtube.com/watch?v=mZxwGnOz7ZQ"
MDROP = 49.3514                      # retour de « Sweet dreams are made of this » après l'interlude du riff
DROP = 10.04; T = 0.4790             # ~125 BPM (kicks mesurés 39,34 -> 57,54)
MUSIC_IN0 = MDROP - DROP
END = 18.18                          # juste après « Who am I to disagree? » (fin 56,68 s du morceau), kick 57,54 ; règle 20 s max
NPRE = 3                             # coupes sous la voix (kicks réels de l'interlude)
CUT_T = [4.33, 6.25, 7.68] + [DROP] + [DROP + 2 * k * T for k in range(1, 7)]
HITS_JSON = OUT + "R14-frappes.json"
def hits_all(mi): return detect_hits(music_raw(mi))
def music_raw(mi, dur=END + 0.5, sr=48000):
    import soundfile as sf
    i0 = int(round(mi * sr)); x, r = sf.read(SON_FILE, start=i0, frames=int(dur * sr), dtype="float32"); assert r == sr; return x
def kicks_of(h): return [x[0] for x in h if x[1] == "kick" and x[3] > 0.12]
def snares_of(h): return [x[0] for x in h if x[1] == "caisse"]
def snap_list(h, targets):
    ks = kicks_of(h); out = []
    for i, t in enumerate(targets):
        if i > NPRE: t = out[-1] + 2 * T                                    # après le drop : 2 temps après la coupe précédente réelle
        c = min(ks, key=lambda k: abs(k - t)); assert abs(c - t) < 0.05, ("pas de frappe près de", t, c); out.append(c)
    return out
def frappes():
    if os.path.exists(HITS_JSON):
        js = json.load(open(HITS_JSON))
        if js["cle"] == [MUSIC_IN0, END, CUT_T]: return js["music_in"], js["frappes"]
    best, bad = None, 9
    for off in np.arange(-0.016, 0.0165, 0.001):
        h = hits_all(MUSIC_IN0 + off); cuts = snap_list(h, CUT_T)
        e = max(abs(c - round(c * FPS) / FPS) for c in cuts)
        if e < bad: best, bad, hb = off, e, h
    mi = MUSIC_IN0 + best
    json.dump({"cle": [MUSIC_IN0, END, CUT_T], "music_in": mi, "frappes": hb}, open(HITS_JSON, "w")); return mi, hb
MUSIC_IN, HITS = frappes()
FINE = 0.0                            # recalage fin éventuel mesuré sur l'export AAC
MUSIC_IN += FINE; HITS = [[h[0] - FINE] + list(h[1:]) for h in HITS]
KICKS = kicks_of(HITS)
CUTS = snap_list(HITS, CUT_T); CUTF = [fr(c) for c in CUTS]
DROPF = CUTF[NPRE]; TB = T

# ---------------- voix ----------------
V_SRC0 = 131.95                       # source IS à t = 0 (silence après « service public. » 131,76 ; « Nous » ~132,4)
V_IN, V_OUT = 131.95, 141.98          # … « dos » (fin 141,82) ; « pour pouvoir le faire fonctionner » (142,12) non gardé
def t_of_src(s): return s - V_SRC0
WORDS = [("NOUS", 132.40), ("PARLONS", 132.62), ("DE", 133.16), ("5", 133.38), ("MILLIONS", 133.70), ("DE", 134.62), ("NOS", 135.02),
         ("CONCITOYENS", 135.24), ("QUI", 136.08), ("SE", 136.30), ("SONT", 136.48), ("MIS", 136.72), ("AU", 136.86), ("SERVICE", 137.00),
         ("DES", 137.42), ("AUTRES", 137.60), ("ET", 138.30), ("QUI", 138.70), ("CHAQUE", 138.90), ("JOUR", 139.18), ("PORTENT", 139.48),
         ("CE", 140.02), ("PAYS", 140.22), ("SUR", 140.60), ("LEUR", 141.20), ("DOS", 141.40)]
def wt(i): return t_of_src(WORDS[i][1])
def ln(*idx): return [(WORDS[i][0], wt(i)) for i in idx]

# ---------------- polices ransom-note ----------------
S = "/System/Library/Fonts/Supplemental/"
FONTS = [(S + "Arial Black.ttf", 0), (S + "Georgia Bold.ttf", 0), (S + "Times New Roman Bold.ttf", 0), (S + "Impact.ttf", 0),
         (S + "Courier New Bold.ttf", 0), (S + "Rockwell.ttc", 2), (S + "AmericanTypewriter.ttc", 2), (S + "Didot.ttc", 2),
         (S + "Bodoni 72.ttc", 2), (S + "Futura.ttc", 2)]
FCOND = (S + "Futura.ttc", 4)
STYLES = [(rgb(PAPER), rgb(INK)), (rgb(INK), rgb(YELLOW)), (rgb(YELLOW), rgb(INK)), (rgb(VIOLET), (255, 255, 255)),
          ((255, 255, 255), rgb(VIOLET)), (rgb(LILAC), rgb(INK)), (rgb(YELLOW), rgb(VIOLET)), ((236, 233, 224), (20, 20, 20))]
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
    col = np.array([0.80, 0.88, 0.90], np.float32)[None, None, :] * (1 + 0.04 * rng.standard_normal((h, w, 1)).astype(np.float32))
    return np.dstack([col, m * 0.72]).astype(np.float32)
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
sys.path.insert(0, HG + "/_claude/outils")
from decoupe import masques, controle, planche                           # outil partagé obligatoire (lot 7)
def cutmasks(key, frames, box, pt, seed=0, tear=None):
    """Découpe (decoupe.masques, outil partagé) : lui seul, buste entier jusqu'au pupitre (règle Luca : jamais tête + épaules) ;
    les bonnettes des micros devant la poitrine (trous laissés par la segmentation) sont rebouchées avec l'image d'origine
    (un bout de micro est accepté). Le bas du buste (coupé à plat au pupitre) est posé sur le bas du cadre 9:16."""
    ms = masques(frames, box, pt, CACHE + "dec/" + key)
    heads, cxs, bots, out = [], [], [], []
    for m in ms:
        b = (m > 0.5).astype(np.uint8); hh_, ww_ = b.shape
        inv = (1 - b).copy(); ff = np.zeros((hh_ + 2, ww_ + 2), np.uint8)
        for sx in range(0, ww_, 20): cv2.floodFill(inv, ff, (sx, 0), 2)
        for sy in range(0, hh_, 20):
            if inv[sy, 0] == 1: cv2.floodFill(inv, ff, (0, sy), 2)
            if inv[sy, ww_ - 1] == 1: cv2.floodFill(inv, ff, (ww_ - 1, sy), 2)
        m = np.where(inv == 1, 1.0, m).astype(np.float32)                   # trous fermés (bonnettes) rebouchés
        out.append(m); b = m > 0.5
        ys = np.where(b.any(1))[0]; heads.append(ys[0]); bots.append(ys[-1])
        cxs.append(float(np.where(b.any(0))[0].mean()))
    head = int(np.median(heads)); y_t = int(np.median(bots))
    if tear:                                                                # bord bas en papier déchiré à mi-poitrine (tête assez haute, hors interface TikTok)
        y_t = min(y_t, head + tear); rng = np.random.default_rng(seed); ww_ = out[0].shape[1]
        def cren(pas): return np.interp(np.arange(ww_), np.arange(0, ww_ + pas, pas), rng.uniform(0, 1, len(range(0, ww_ + pas, pas))))
        line = (y_t - 28 + (0.75 * cren(28) + 0.25 * cren(7)) * 28).astype(int); yy = np.arange(out[0].shape[0])[:, None]
        out = [np.where(yy < line[None, :], m, 0).astype(np.float32) for m in out]
        for j, m in enumerate(out):                                         # une seule forme (bout de main ou de micro isolé par la déchirure retiré)
            n_, lab, st, _ = cv2.connectedComponentsWithStats((m > 0.5).astype(np.uint8), 8)
            if n_ > 2:
                k_ = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA])); out[j] = m * cv2.dilate((lab == k_).astype(np.uint8), np.ones((5, 5), np.uint8))
    ct = [controle(m) for m in out[::max(1, len(out) // 5)]]
    print("  découpe %s : tête %d, bas %d, contrôle %s" % (key, head, y_t, {k: max(c[k] for c in ct) for k in ("gauche", "droite", "haut", "morceaux", "bas_net")}), flush=True)
    planche(frames, out, box, CACHE + "planche_%s.jpg" % key)
    return out, y_t, head, float(np.median(cxs))
def grade(x, sat=1.10):
    x = 0.82 * x + 0.18 * (x * x * (3 - 2 * x))
    L = x @ np.array([0.0722, 0.7152, 0.2126], np.float32)
    return np.clip(L[..., None] + (x - L[..., None]) * sat, 0, 1)
def lum(x, gain=1.15):
    L = x @ np.array([0.0722, 0.7152, 0.2126], np.float32)
    L = L / max(float(np.percentile(L, 99)), 0.2); L = np.clip(L, 0, 1) ** 0.75
    L = np.clip((L - 0.5) * gain + 0.5 + 0.03, 0, 1); return 0.75 * L + 0.25 * (L * L * (3 - 2 * L))
DUO = {"violet": (INK, LILAC), "vif": (VIOLET, WHITE), "jaune": (INK, YELLOW), "jv": (VIOLET, YELLOW)}
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
STRIP_COLS = [YELLOW, WHITE, VIOLET, LILAC, INK, PAPER, YELLOW, LILAC]
def strip_rgba(w, h, rng, colhex, ht=False):
    col = hexc(colhex); dot = hexc(INK if colhex in (YELLOW, WHITE, LILAC, PAPER) else YELLOW)
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
        src_ = self.frames[i][y0:y1, x0:x1]
        c = cv2.resize(grade(src_) if self.duo == "couleur" else duotone(src_, self.duo), (self.width, self.h), interpolation=cv2.INTER_AREA)
        hh, ww = self.h + 2 * b, self.width + 2 * b
        out = np.zeros((hh + 2 * M, ww + 2 * M, 4), np.float32); out[..., 3] = self.shadow
        body = np.ones((hh, ww, 3), np.float32) * np.array([0.95, 0.95, 0.94], np.float32); body[b:b + self.h, b:b + self.width] = c
        a = self.mask[..., None]; reg = out[M:M + hh, M:M + ww]
        reg[..., :3] = body * a; reg[..., 3] = np.maximum(self.mask, reg[..., 3])
        for t, (tx, ty) in self.tapes: over(out, t, tx, ty)
        return out
def beat_grid():
    """Temps : kicks réels après le drop + grille d'un temps comptée à rebours depuis le drop dans le pont sans kick."""
    g = [k for k in KICKS if k >= CUTS[NPRE] - 0.05]; t = CUTS[NPRE] - T
    while t > 0: g.append(t); t -= T
    return sorted(g)
BEATS = beat_grid(); BEATF = [fr(b) for b in BEATS]
def nbeat(f): return sum(1 for b in BEATF if b <= f)
def jit(key, k, amp=8.0, ang=1.5):
    r = np.random.default_rng(skey(key) * 1000 + k); return r.uniform(-amp, amp), r.uniform(-amp, amp), r.uniform(-ang, ang)

# ---------------- affiches collées (nouveau R14) ----------------
_post = {}
def poster_rgba(kind, w, h, seed):
    """Affiche / tract collé : papier texturé, bord légèrement déchiré, ombre ; aucun vrai texte (lignes de faux texte en barres)."""
    k = (kind, w, h, seed)
    if k in _post: return _post[k]
    rng = np.random.default_rng(seed); M = 24
    fib = cv2.GaussianBlur(rng.standard_normal((h, w)).astype(np.float32), (0, 0), sigmaX=5, sigmaY=0.8)
    tex = (1 + 0.05 * fib + 0.025 * cv2.GaussianBlur(rng.standard_normal((h, w)).astype(np.float32), (0, 0), 1.0))[..., None]
    if kind == "tract":                                                     # tract syndical A4 jaune, bandeau violet, faux texte
        body = np.ones((h, w, 3), np.float32) * hexc(YELLOW)
        body[int(0.05 * h):int(0.20 * h), int(0.06 * w):int(0.94 * w)] = hexc(VIOLET)
        body[int(0.23 * h):int(0.27 * h), int(0.06 * w):int(0.70 * w)] = hexc(INK)
        y = 0.32
        while y < 0.86:
            L = rng.uniform(0.55, 0.88) if rng.random() > 0.18 else rng.uniform(0.25, 0.45)
            body[int(y * h):int(y * h) + max(3, int(0.011 * h)), int(0.06 * w):int((0.06 + L * 0.88) * w)] = hexc(INK) * 0.9 + hexc(YELLOW) * 0.1
            y += 0.034 if rng.random() > 0.15 else 0.06
        body[int(0.90 * h):int(0.95 * h), :] = hexc(VIOLET)
    elif kind == "trame":                                                   # affiche tramée violette (dégradé de points)
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32); cell = 16.0
        u, v = (xx + yy) / 1.4142, (xx - yy) / 1.4142
        scr = (np.cos(2 * np.pi * u / cell) + np.cos(2 * np.pi * v / cell)) / 4 + 0.5
        g = np.clip(yy / h * 0.9 + 0.05 + 0.15 * np.sin(xx / w * 3.0), 0, 1)
        ink = np.clip((g - scr) * 6, 0, 1)[..., None]
        body = hexc(LILAC) * (1 - ink) + hexc(VIOLET) * ink
    elif kind == "tract_fin":                                               # affiche finale : jaune, filets violets haut et bas
        body = np.ones((h, w, 3), np.float32) * hexc(YELLOW)
        body[int(0.04 * h):int(0.07 * h), int(0.05 * w):int(0.95 * w)] = hexc(VIOLET)
        body[int(0.93 * h):int(0.96 * h), int(0.05 * w):int(0.95 * w)] = hexc(VIOLET)
    elif kind == "bande":                                                   # affiche à grandes bandes violet / jaune
        body = np.ones((h, w, 3), np.float32) * hexc(PAPER)
        for j, y0 in enumerate(np.arange(0, h, h / 5)):
            if j % 2 == 0: body[int(y0):int(y0 + h / 10)] = hexc(VIOLET if j % 4 == 0 else YELLOW)
    else:                                                                   # "photo:<SRC>:<t>:<duo>" : photo de manif imprimée en bichromie
        _, src, t, duo = kind.split(":")
        fr0 = read_frames(src, float(t), 1)[0]
        x0, y0, x1, y1 = 0, 180, 1580, 1080                                   # sous le filigrane d'angle
        r = (x1 - x0) / (y1 - y0); ph = int(0.80 * h); pw = int(ph * r)
        crop = fr0[y0:y1, x0:x1]
        if pw < w:                                                          # photo trop étroite : recadrer en hauteur
            pw = w; ph2 = int(pw / r); crop = cv2.resize(crop, (pw, ph2)); off = (ph2 - ph) // 2; ph_img = crop[off:off + ph]
        else:
            crop = cv2.resize(crop, (pw, ph)); off = (pw - w) // 2; ph_img = crop[:, off:off + w]
        body = np.ones((h, w, 3), np.float32) * hexc(PAPER)
        body[:ph] = duotone(ph_img, duo)
        body[ph + int(0.03 * h):ph + int(0.12 * h), int(0.06 * w):int(0.94 * w)] = hexc(VIOLET if duo != "vif" else YELLOW)
    body = np.clip(body * tex, 0, 1)
    m = torn_mask(h, w, rng, rough=5, step=13, inset=3)
    out = np.zeros((h + 2 * M, w + 2 * M, 4), np.float32)
    sh = np.zeros((h + 2 * M, w + 2 * M), np.float32); sh[M + 10:M + 10 + h, M + 8:M + 8 + w] = m * 0.5
    out[..., 3] = cv2.GaussianBlur(sh, (0, 0), 6)
    reg = out[M:M + h, M:M + w]; reg[..., :3] = body * m[..., None]; reg[..., 3] = np.maximum(m, reg[..., 3])
    tp = rot_rgba(tape_rgba(int(w * 0.30), 42, rng), rng.uniform(-12, 12)); over(out, tp, int(w * 0.38), M - 18)   # scotch en haut
    _post[k] = out; return out
def draw_poster(img, pz, f):
    """Affiche posée « au balai » de haut en bas en 3 images, colle humide (plus sombre) qui sèche en 6 images."""
    kind, cx, cy, w, h, ang, f0, seed = pz
    if f < f0: return
    im = poster_rgba(kind, w, h, seed); u = min(1.0, (f - f0 + 1) / 3)
    if u < 1:
        im = im.copy(); im[int(im.shape[0] * u):] = 0
    wet = 0.84 + 0.16 * min(1.0, (f - f0) / 6)
    if wet < 1: im = im.copy(); im[..., :3] *= wet
    dx, dy, da = jit(("p", seed), nbeat(f), amp=3, ang=0.4)
    paste(img, im, cx + dx, cy + dy, 1.0, ang + da)

# ---------------- plans ----------------
SDBOX = (200, 0, 1920, 820)           # Saint-Denis gros plans : pupitre (y > 820) hors fenêtre ; filigrane et décor jamais gardés (découpe = lui seul)
SDPT = (0.45, 0.75)
KEYL = ("MILLIONS", "DOS", "PAYS", "5")
def P(kind, cx, cy, w, h, ang, beat): return (kind, cx, cy, w, h, ang, beat)
SHOTS = [
    dict(id="A1", kind="collage", bg=VIOLET, sheet=(LILAC, "bas", 0.90, -4, 1), strips=2,
         posters=[P("photo:IS:149.6:jv", 540, 1250, 900, 1150, -3, 0), P("tract", 200, 1560, 340, 470, -7, 2), P("trame", 900, 1540, 300, 430, 6, 4),
                  P("bande", 170, 760, 260, 380, 4, 6)],
         photos=[("IS", None, (640, 0, 1585, 1080), 860, (540, 1150), -2.0, 0.0, "couleur")],
         boards=[([ln(0, 1, 2), ln(3, 4)], None), ([[("DE", wt(6)), ("NOS", wt(6))], ln(7)], wt(6))], txt_h=118,
         why="son direct SYNCHRO : la marche intersyndicale (29/09/2026) en grande photo couleur collée au mur (bords déchirés, scotch), « Nous parlons de 5 millions de nos concitoyens »"),
    dict(id="A2", kind="collage", bg=YELLOW, sheet=(VIOLET, "haut", 0.10, 3, 2), strips=2,
         posters=[P("photo:IS:118.0:violet", 540, 1080, 860, 1100, -3, 0), P("tract", 830, 1450, 360, 500, 8, 1), P("photo:SD7:2.0:jv", 300, 1500, 480, 620, -6, 2),
                  P("trame", 820, 760, 300, 420, 6, 3)],
         boards=[([ln(8, 9, 10, 11), ln(12, 13), ln(14, 15)], None)], txt_h=118,
         why="voix off sur la foule : « qui se sont mis au service des autres » ; affiche de la manif collée en grand puis recouverte"),
    dict(id="A3", kind="collage", bg=PAPER, sheet=(YELLOW, "bas", 0.86, 5, 3), strips=2,
         posters=[P("trame", 230, 1500, 420, 600, -6, 0), P("photo:SD7:5.0:vif", 870, 1560, 420, 560, 6, 1)],
         photos=[("IS", None, (800, 0, 1500, 860), 740, (560, 1130), 2.5, 0.0, "couleur")],
         boards=[([ln(16, 17), ln(18, 19)], None)], txt_h=128,
         why="même plan synchro, plus serré, nouvelle photo collée : « et qui chaque jour »"),
    dict(id="A4", kind="collage", bg=VIOLET, sheet=(YELLOW, "haut", 0.10, -3, 4), strips=3,
         posters=[P("photo:IS:76.0:jaune", 240, 1560, 420, 560, -5, 0), P("tract", 870, 1580, 380, 520, 6, 1), P("photo:IS:174.0:violet", 820, 760, 360, 460, -4, 3)],
         photos=[("IS", None, (700, 0, 1585, 1000), 900, (540, 1170), -1.5, 0.0, "couleur")],
         boards=[([ln(20, 21, 22), ln(23, 24, 25)], None)], txt_h=140,
         why="plan synchro : « portent ce pays sur leur dos », les affiches de la manif se recouvrent autour de la photo jusqu'au drop"),
    dict(id="B1", kind="sil", src="SD2", t=7.0, bg=YELLOW, ghost=VIOLET, box=SDBOX, pt=SDPT, edge_y=1926, head_y=640, push=(1.0, 1.04), offx=130,
         posters=[P("photo:IS:80.0:violet", 260, 1250, 460, 620, -6, 0), P("tract", 850, 1350, 400, 560, 7, 1)],
         rboards=[([[("5", 0.0), ("MILLIONS", 0.0)], [("DE", TB), ("NOS", TB), ("CONCITOYENS", TB)]], 0.0)], txt_y=300, txt_h=150, letters=("5", "MILLIONS"), strips=2, flash=True,
         why="drop : flash blanc 3 images, silhouette blanche puis Mélenchon (Saint-Denis, main levée) sur affiche jaune, double tirage violet"),
    dict(id="B2", kind="collage", bg=VIOLET, strips=2,
         posters=[P("photo:SD7:3.2:jv", 540, 900, 820, 1000, 3, 0), P("photo:IS:120.0:jaune", 330, 1430, 560, 700, -6, 1), P("tract", 820, 1500, 380, 520, 8, 1)],
         rboards=[([[("AU", 0.0), ("SERVICE", 0.0)], [("DES", TB), ("AUTRES", TB)]], 0.0)], txt_y=300, txt_h=160,
         why="mur d'affiches : la foule et les drapeaux de Saint-Denis, la manif intersyndicale, collées l'une sur l'autre"),
    dict(id="B3", kind="cut", src="SD3", t=26.6, offx=170, bg=LILAC, sheet=(VIOLET, "bas", 0.80, -5, 5), ghost=VIOLET, box=SDBOX, pt=SDPT,
         edge_y=1560, head_y=640, tear=640, push=(1.0, 1.04), strips=2,
         posters=[P("tract", 220, 1000, 380, 540, -8, 0), P("photo:SD1:18.0:violet", 860, 980, 420, 560, 6, 1)],
         rboards=[([[("CHAQUE", 0.0), ("JOUR", 0.0)]], 0.0)], txt_y=300, txt_h=170,
         why="2026 — meeting de Saint-Denis, gros plan (sans le son) : Mélenchon détouré sur affiche lilas, feuille violette déchirée"),
    dict(id="B4", kind="cut", src="SD6", t=12.0, bg=YELLOW, sheet=(VIOLET, "haut", 0.11, 4, 6), ghost=VIOLET, box=SDBOX, pt=SDPT,
         edge_y=1926, head_y=640, push=(1.0, 1.04), strips=2,
         posters=[P("photo:IS:150.8:violet", 230, 1050, 400, 540, -5, 0), P("trame", 870, 1050, 360, 520, 6, 1)],
         rboards=[([[("PORTENT", 0.0), ("CE", 0.0), ("PAYS", 0.0)], [("SUR", TB), ("LEUR", TB), ("DOS", TB)]], 0.0)], txt_y=290, txt_h=140, letters=("DOS",), flash2=True,
         why="Saint-Denis, index levé (sans le son) : « portent ce pays sur leur dos »"),
    dict(id="B5", kind="collage", bg=PAPER, strips=1,
         posters=[P("photo:IS:176.5:jv", 540, 760, 760, 980, -3, 0), P("tract", 330, 1300, 480, 660, 5, 0.5), P("photo:SD7:7.0:violet", 780, 1350, 520, 680, -6, 1),
                  P("bande", 300, 600, 380, 520, 7, 1.5), P("photo:IS:76.8:jaune", 640, 1050, 600, 760, 3, 1.75)],
         why="les affiches se recouvrent au demi-temps : foule de la manif, tracts, drapeaux de Saint-Denis"),
    dict(id="B6", kind="sil", src="SD1", t=6.5, bg=VIOLET, ghost=YELLOW, box=SDBOX, pt=SDPT, edge_y=1926, head_y=640, offx=-160, push=(1.0, 1.035),
         posters=[P("tract", 230, 1100, 420, 580, -7, 0), P("photo:IS:236.0:jv", 860, 1180, 440, 600, 5, 1)], strips=2,
         why="Saint-Denis, poing serré (sans le son) : silhouette blanche 3 images puis en couleur sur le mur violet"),
    dict(id="FIN", kind="card", bg=VIOLET, push=(1.0, 1.035),
         posters=[P("tract_fin", 540, 960, 940, 1560, -1.5, 0)],
         big=[("JEAN-LUC", 0.0, rgb(VIOLET)), ("MÉLENCHON", 0.0, rgb(VIOLET)), ("2027", TB, rgb(INK))], big_y=560, big_sizes=[200, 200, 420],
         why="carton final : affiche jaune collée sur le mur violet, JEAN-LUC MÉLENCHON + 2027"),
]
BOUNDS_T = [0] + CUTF + [fr(END)]
assert len(BOUNDS_T) == len(SHOTS) + 1, (len(BOUNDS_T), len(SHOTS))
for i, sh in enumerate(SHOTS):
    sh["a"], sh["bb"] = BOUNDS_T[i], BOUNDS_T[i + 1]; sh["n"] = sh["bb"] - sh["a"]; sh["clip"] = "R14_%s.mov" % sh["id"]
    if sh.get("src") == "IS" and sh["t"] is None: sh["t"] = V_SRC0 + sh["a"] / FPS           # plans A synchro avec la voix
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
    photos = [Photo(read_frames(ps, pt if pt is not None else V_SRC0 + a / FPS, n), pbox, pw, pc, pa, fr(rel(pt0)) if pt0 > 0 or sh["id"].startswith("B") else a, (sh["id"], j), duo)
              for j, (ps, pt, pbox, pw, pc, pa, pt0, duo) in enumerate(sh.get("photos", []))]
    if sh["id"].startswith("A"):                                             # plans A : apparition au temps absolu du mot
        for ph, spec in zip(photos, sh.get("photos", [])): ph.f0 = max(a, fr(spec[6])) if spec[6] > 0 else a
    strips = make_strips(sh)
    posters = [(k_, cx_, cy_, w_, h_, an_, min(sh["bb"] - 3, max(a, fr(a / FPS + bt * T))), skey((sh["id"], j)))
               for j, (k_, cx_, cy_, w_, h_, an_, bt) in enumerate(sh.get("posters", []))]
    k0 = nbeat(a)
    if sh["kind"] in ("cut", "sil"):
        if sh.get("still"):                                                 # affiche figée (sous la voix : il ne parle pas à l'image)
            raw = read_frames(sh["src"], sh["t"], 1) * n
            m1, y_t, head, pcx = cutmasks("%s_%s_%.2f_1" % (sh["id"], sh["src"], sh["t"]), raw[:1], sh["box"], sh["pt"], skey(sh["id"]), sh.get("tear"))
            ms = m1 * n
        else:
            raw = read_frames(sh["src"], sh["t"], n)
            ms, y_t, head, pcx = cutmasks("%s_%s_%.2f_%d" % (sh["id"], sh["src"], sh["t"], n), raw, sh["box"], sh["pt"], skey(sh["id"]), sh.get("tear"))
    for i in range(n):
        f = a + i; u = i / max(n - 1, 1); kb = nbeat(f) - k0
        img = paper(sh["bg"])
        if sh.get("sheet"): apply_sheet(img, sh["sheet"])
        for pz in posters: draw_poster(img, pz, f)                          # mur : une affiche de plus par temps
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
            z = sh["push"][0] + (sh["push"][1] - sh["push"][0]) * u            # poussée lente avant, jamais de dézoom
            sc0 = (sh["edge_y"] - sh["head_y"]) / max(1, y_t - head); sc = sc0 * z
            ey = sh["edge_y"] + (sh["edge_y"] - H * 0.42) * (z - 1)               # le zoom part du centre de l'image
            ccx = W / 2 + sh.get("offx", 0) + ((x1 - x0) / 2 - pcx) * sc
            ccy = ey - y_t * sc + (y1 - y0) * sc / 2; r_ = 9
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
            for j, (tx, ty, ta) in enumerate(((110, 230, -32), (970, 230, 30), (110, 1700, 28), (970, 1700, -30))):
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
    v = grab(HG + "/" + SRC["IS"][0], V_IN, V_OUT - V_IN); env = np.ones(len(v), np.float32)
    k = int(0.03 * sr); env[:k] = np.linspace(0, 1, k); k = int(0.08 * sr); env[-k:] = np.linspace(1, 0, k)
    i0 = int(round(t_of_src(V_IN) * sr)); voix[i0:i0 + len(v)] = v * env[:, None] * 10 ** (VGAIN / 20)
    m = music_raw(MUSIC_IN)[:N]
    t = np.arange(len(m)) / sr; vend = t_of_src(V_OUT); dr = CUTS[NPRE]
    # sous la phrase : pont sans basse baissé, montée progressive, plein sur le drop « Oh Djadja »
    gdb = np.interp(t, [0, 0.25, 4.0, vend - 0.6, dr - 0.03, dr, END], [-17, -14, -13, -9, -6, 0, 0])
    k = int(0.40 * sr); fo = np.ones(len(m), np.float32); fo[-k:] = np.linspace(1, 0, k)
    mus[:len(m)] = m * (10 ** (gdb / 20) * fo)[:, None]
    sf.write(OUT + "R14-voix.wav", voix, sr, subtype="PCM_24"); sf.write(OUT + "R14-musique.wav", mus, sr, subtype="PCM_24")
    sf.write(D + "tmp_mix.wav", voix + mus, sr, subtype="FLOAT")
    r = subprocess.run([FF, "-hide_banner", "-i", D + "tmp_mix.wav", "-af", "loudnorm=I=-14:TP=-2.5:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    js = json.loads(r[r.rindex("{"):r.rindex("}") + 1])
    af = ("loudnorm=I=-14:TP=-2.5:LRA=11:measured_I=%s:measured_TP=%s:measured_LRA=%s:measured_thresh=%s:offset=%s:linear=true,"
          "aresample=48000" % (js["input_i"], js["input_tp"], js["input_lra"], js["input_thresh"], js["target_offset"]))
    subprocess.run([FF, "-v", "error", "-y", "-i", D + "tmp_mix.wav", "-af", af, "-c:a", "pcm_s24le", OUT + "R14-mix.wav"], check=True)
    os.remove(D + "tmp_mix.wav"); print("audio : mix avant normalisation", js["input_i"], "LUFS")
VGAIN = 4.0

# ---------------- plan ----------------
def build_plan():
    video = []
    for sh in SHOTS:
        v = {"id": sh["id"], "clip": sh["clip"], "folder": "genR14", "path": OUT + sh["clip"], "s": 0, "e": sh["n"], "rec": sh["a"], "dur": sh["n"],
             "clip_fps": FPS, "speed_pct": 100, "track": 1, "note": sh["why"], "kind": sh["kind"], "temps": round(sh["n"] / FPS / T, 2)}
        if sh.get("src"):
            path, sfps, url, off, ctx = SRC[sh["src"]]
            v["source"] = {"fichier": path, "in_s": round(sh["t"], 3), "out_s": round(sh["t"] + sh["n"] / FPS, 3), "fps": sfps, "url": url, "contexte": ctx}
            if off is not None: v["source"]["youtube_t"] = round(off + sh["t"], 1)
        if sh.get("posters"):
            v["affiches"] = [{"type": p_[0], "temps": p_[6]} for p_ in sh["posters"]]
        if sh.get("photos"):
            v["photos"] = [{"fichier": SRC[p[0]][0], "in_s": round(p[1] if p[1] is not None else V_SRC0 + sh["a"] / FPS, 3),
                            "out_s": round((p[1] if p[1] is not None else V_SRC0 + sh["a"] / FPS) + sh["n"] / FPS, 3), "synchro": p[1] is None, "cadre_source": p[2], "bichromie": p[7], "url": SRC[p[0]][2]} for p in sh["photos"]]
        video.append(v)
    texts = []
    for sh in SHOTS:
        for lines, _ in sh.get("boards", []):
            for line in lines: texts.append({"plan": sh["id"], "texte": " ".join(w for w, _ in line)})
        for line in sh.get("txt", []): texts.append({"plan": sh["id"], "texte": " ".join(w for w, _ in line)})
        for lines, _ in sh.get("rboards", []): texts.append({"plan": sh["id"], "texte": " ".join(w for line in lines for w, _ in line)})
        for s_, t_, c_ in sh.get("big", []): texts.append({"plan": sh["id"], "texte": s_})
    PHR = "Nous parlons de 5 millions de nos concitoyens qui se sont mis au service des autres et qui chaque jour portent ce pays sur leur dos"
    plan = {"name": "R14 - Collage ransom-note tract syndical - Jean-Luc Mélenchon", "fps": FPS, "w": W, "h": H, "duree_s": END,
            "note": "Plans ProRes 9:16 composés en Python (lot7/_claude/gen/R14/out), découpes decoupe.py : mur d'affiches qui se recouvrent (une par temps, posée de haut en bas, "
                    "colle humide), tracts jaunes à bandeau violet, Mélenchon détouré seul (decoupe.py), double tirage tramé, "
                    "silhouettes blanches 3 images, photos de manif en bichromie, textes ransom-note cuits. s/e en images du clip (30 i/s), rec en images "
                    "timeline. Coupes sur les kicks réels de Sweet Dreams (out/R14-frappes.json). Aucun ralenti. Générateur : lot7/_claude/gen/R14/genR14.py",
            "phrase": {"texte": PHR, "url": SRC["IS"][2], "source": SRC["IS"][0], "in_s": 132.40, "out_s": 141.82,
                       "timeline_s": [round(t_of_src(132.40), 2), round(t_of_src(141.82), 2)],
                       "voix": "son direct synchro : la marche en grande photo couleur collée (A1, A3, A4), foule (A2) ; suite « pour pouvoir le faire fonctionner » non gardée"},
            "musique": {"fichier": "lot7/sons/R14-eurythmics-sweet-dreams_complet.wav", "titre": "Eurythmics - Sweet Dreams (Are Made of This) (2018 Remastered)", "url": SON_URL,
                        "debut_complet_s": round(MUSIC_IN, 4), "fin_complet_s": round(MUSIC_IN + END, 3), "drop_timeline_s": CUTS[NPRE],
                        "coupes_frappes_s": CUTS, "coupes_images": CUTF},
            "textes": texts, "video": video,
            "audio": [{"id": "mix", "clip": "R14-mix.wav", "folder": "genR14", "path": OUT + "R14-mix.wav", "rec": 0, "track": 1,
                       "note": "mix -14 LUFS : voix IS %.2f-%.2f s (+%.0f dB) à %.2f s ; Sweet Dreams dès %.3f s du complet, baissé sous la voix (interlude du riff), montée, plein au drop, fondu de fin 0,4 s"
                               % (V_IN, V_OUT, VGAIN, t_of_src(V_IN), MUSIC_IN)}],
            "stems": ["lot7/_claude/gen/R14/out/R14-voix.wav", "lot7/_claude/gen/R14/out/R14-musique.wav"],
            "logos_exclus": "intersyndicale : filigrane MELENCHON2027.fr hors fenêtre (détourage x < 1590, photos y > 180) ; Saint-Denis : filigrane et pupitre exclus"}
    json.dump(plan, open(D + "plan-R14.json", "w"), indent=1, ensure_ascii=False)
    son = {"id": "R14", "titre": "Sweet Dreams (Are Made of This) (2018 Remastered)", "artiste": "Eurythmics", "url": SON_URL,
           "chaine": "Eurythmics (officielle, vérifiée ; le clip officiel qeMFqkcPYcg est sur la même chaîne)",
           "fichier": "lot7/sons/R14-eurythmics-sweet-dreams_complet.wav",
           "extrait_complet_s": {"debut": round(MUSIC_IN, 4), "fin": round(MUSIC_IN + END, 3)},
           "paroles_audibles": "sous la phrase : interlude instrumental du riff (aucune parole) ; au drop : « Sweet dreams are made of this, who am I to disagree? »",
           "bpm": round(60 / T, 1), "temps_s": T,
           "drop": {"complet_s": round(MUSIC_IN + CUTS[NPRE], 4), "timeline_s": CUTS[NPRE], "nature": "retour de « Sweet dreams are made of this » après l'interlude"},
           "frappes_timeline_s": [round(k, 4) for k in KICKS], "coupes_sur_frappes_s": CUTS,
           "mix": "lot7/_claude/gen/R14/out/R14-mix.wav"}
    json.dump(son, open(D + "son.json", "w"), indent=1, ensure_ascii=False)

# ---------------- aperçu 540x960 ----------------
def apercu():
    plan = json.load(open(D + "plan-R14.json")); ins = []; fl = []
    for i, v in enumerate(plan["video"]):
        ins += ["-i", OUT + v["clip"]]
        fl.append("[%d:v]trim=start_frame=%d:end_frame=%d,setpts=PTS-STARTPTS,scale=540:960,setsar=1[v%d]" % (i, v["s"], v["e"], i))
    k = len(plan["video"]); fl.append("".join("[v%d]" % i for i in range(k)) + "concat=n=%d:v=1:a=0[v]" % k)
    ins += ["-i", OUT + "R14-mix.wav"]; out = HG + "/preview/apercu-R14.mp4"
    subprocess.run([FF, "-v", "error", "-y"] + ins + ["-filter_complex", ";".join(fl), "-map", "[v]", "-map", "%d:a" % k,
                    "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "aac", "-b:a", "192k", "-shortest", out], check=True)
    print("aperçu", out)
# ---------------- mesure sur l'export : coupes vs frappes, LUFS / TP ----------------
def mesure():
    out = HG + "/preview/apercu-R14.mp4"
    r = subprocess.run([FF, "-v", "info", "-i", out, "-vf", "scale=135:240,select='gt(scene,0.2)',showinfo", "-an", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    cuts = [float(x) for x in re.findall(r"pts_time:([0-9.]+)", r)]
    p = subprocess.run([FF, "-v", "error", "-i", out, "-vn", "-ac", "2", "-ar", "48000", "-f", "f32le", "-"], capture_output=True)
    y = np.frombuffer(p.stdout, np.float32).reshape(-1, 2)
    hh = detect_hits(y)
    worst = 0
    for i, c in enumerate([fr_ / FPS for fr_ in CUTF]):
        det = min(cuts, key=lambda x: abs(x - c)) if cuts else None
        pool = [x[0] for x in hh if (x[1] == "kick" and x[3] > 0.03)]
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
