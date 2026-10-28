# R12 (lot 7) — Collage ransom-note « Marseille » (modèle lot6 R6, recette inspis/2026-10-26 abdulelsayed), Manuel Bompard,
# son 13'Organisé – Bande organisée (clip officiel, chaîne DORETDEPLATINE, label de JuL), drop sur le refrain. Version 2 (retours Luca 27/10).
# Idée du brief : collage Marseille (Vieux-Port, Notre-Dame-de-la-Garde, Panier, Vélodrome, foules), base bleu ciel + blanc, accent noir encre,
#   photos en COULEUR (Wikimedia Commons, licences dans photos-licences.json ; meeting 2025 et Vieux-Port 2017 officiels).
# Découpe : _claude/outils/decoupe.py (instance Vision x segmentation personne : ni pupitre ni micro ni voisin, une seule forme),
#   controle() vérifié plan par plan, buste coupé au pupitre posé sur le bas du cadre (jamais de silhouette qui flotte).
# Phrase (son direct, plans SYNCHRO, Bompard énergique) : « Assez de cette islamophobie, assez de ces discours qui stigmatisent une partie
#   de la population. » (meeting de lancement de la campagne municipale, Marseille, 06/12/2025, chaîne Manuel Bompard,
#   youtu.be/7FBfSi-UjCA 424,04-429,42 s) -> autre phrase que lot1 #2 (QAG Nuñez), A2 (candidats au pouvoir), P3 (crise politique).
# Son : Bande organisée, extrait continu ; sous la phrase, fin du couplet étouffée (passe-bas, baissée) puis le break sans kick
#   (206,03-208,13 s) ; drop = retour du kick à 208,13 s sur le refrain « En bande organisée » ; coupes sur les kicks réels (143 BPM).
# Textes après le drop : ASSEZ DE CETTE ISLAMOPHOBIE. / ASSEZ DE CES DISCOURS QUI STIGMATISENT. puis MANUEL BOMPARD en lettres découpées.
# Usage : python genR12.py [shots] [audio] [plan] [apercu] [mesure] [only=ID,ID]   (sans argument = tout sauf mesure)
import sys
sys.dont_write_bytecode = True
import os, json, subprocess, math, re
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
HG = "/Users/luca.grousset/Movies/highkey-gauchiste"
D = HG + "/lot7/_claude/gen/R12/"; OUT = D + "out/"; CACHE = D + "cache/"; os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, D); sys.path.insert(0, HG + "/_claude/outils")
from hits import detect_hits
from decoupe import masques, controle, planche, bas_dechire
FF = "/opt/homebrew/bin/ffmpeg"; FPS = 30; W, H = 1080, 1920
def fr(t): return int(round(t * FPS))
def hexc(h): h = h.lstrip("#"); return np.array([int(h[4:6], 16), int(h[2:4], 16), int(h[0:2], 16)], np.float32) / 255   # BGR
def rgb(h): h = h.lstrip("#"); return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
# palette R12 : bleu ciel + blanc (base), noir encre (accent fort), azur ; photos en couleur
AZUR, CIEL, WHITE, PAPER, INK, ARGENT = "#1E8FD2", "#8FD0F0", "#FFFFFF", "#FBFBF8", "#0B0B0D", "#C7D0D6"

# ---------------- sources ----------------
SRC = {
    "M": ("lot7/sources/R12-bompard-marseille-meeting.mp4", 25.0, "https://www.youtube.com/watch?v=7FBfSi-UjCA", 0.0,
          "meeting de lancement de la campagne municipale, Marseille, 06/12/2025 (chaîne Manuel Bompard)"),
    "Z": ("lot3/sources/Z1-marseille2017-debut.mp4", 25.0, "https://www.youtube.com/watch?v=yrjWwsV4zS4", 0.0,
          "meeting pour la paix, Vieux-Port de Marseille, 09/04/2017 (chaîne JEAN-LUC MÉLENCHON) : foule et port seulement"),
}
PHOTOS = {k: ("lot7/sources/R12-photo-%s.jpg" % k, None, "%s%s" % ("https://commons.wikimedia.org/wiki/File:", t), None, "photo Wikimedia Commons (%s)" % lic) for k, t, lic in (
    ("vieuxport-2", "Marseille_le_vieux_port.jpg", "CC BY-SA 4.0, Jiròni Picas"), ("port-ndg-pano", "Hafen_von_Marseille-Notre_Dame_de_la_Garde.jpg", "CC BY-SA 3.0, Tobi 87"),
    ("ndg-2024", "Notre-Dame_de_la_Garde_Marseille_2024.jpg", "CC BY-SA 4.0, kallerna"), ("panier-rue", "Street_in_Marseille_-_Panier.jpg", "CC BY-SA 3.0, Michiel1972"),
    ("panier", "Marseille_-_Le_Panier.JPG", "domaine public, Vincent"), ("velodrome-virage-nord", "Stade_Vélodrome_Virage_Nord_OM_Lille.jpg", "CC BY 2.0, Stephane Delbecque"),
    ("vieuxport-cc0", "Vieux-Port_Marseille.jpg", "CC0, DanielMichaelPerry"))}
SRC.update(PHOTOS)

# ---------------- musique : 13'Organisé – Bande organisée ----------------
SON_FILE = HG + "/lot7/sons/R12-bande-organisee_complet.wav"; SON_URL = "https://www.youtube.com/watch?v=-CVn3-3g_BI"
MDROP = 208.1330                     # retour du kick après le break, refrain « En bande organisée »
DROP = 6.05; T = 0.42007             # 143 BPM (kicks 208,133 -> 216,535 = 20 temps)
MUSIC_IN0 = MDROP - DROP
END = 19.62                          # fin dans le break après les « hasta luego » (avant « Égal » 221,78 s) ; règle lot 7 : 20 s max
PRE = [204.3687, 206.0281]           # kicks réels sous la voix (2e « assez » ; dernier kick avant le break = 206,03)
POST = [4, 8, 12, 16, 20, 24, 26]    # coupes après le drop, en temps
CUT_T = [b - MUSIC_IN0 for b in PRE] + [DROP] + [DROP + k * T for k in POST]
HITS_JSON = OUT + "R12-frappes.json"
def music_raw(mi, dur=END + 0.5, sr=48000):
    import soundfile as sf
    i0 = int(round(mi * sr)); x, r = sf.read(SON_FILE, start=i0, frames=int(dur * sr), dtype="float32"); assert r == sr; return x
def kicks_of(h): return [x[0] for x in h if x[1] == "kick" and x[3] > 0.12]
def snap_list(h, targets):
    ks = kicks_of(h); out = []; npre = len(PRE)
    for i, t in enumerate(targets):
        if i > npre: t = out[npre] + POST[i - npre - 1] * T                  # après le drop : compté depuis le drop réel
        c = min(ks, key=lambda k: abs(k - t)); assert abs(c - t) < 0.04, ("pas de frappe près de", t, c); out.append(c)
    return out
def frappes():
    if os.path.exists(HITS_JSON):
        js = json.load(open(HITS_JSON))
        if js["cle"] == [MUSIC_IN0, END, CUT_T]: return js["music_in"], js["frappes"]
    best, bad = None, 9
    for off in np.arange(-0.016, 0.0165, 0.001):
        h = detect_hits(music_raw(MUSIC_IN0 + off)); cuts = snap_list(h, CUT_T)
        e = max(abs(c - round(c * FPS) / FPS) for c in cuts)
        if e < bad: best, bad, hb = off, e, h
    mi = MUSIC_IN0 + best
    json.dump({"cle": [MUSIC_IN0, END, CUT_T], "music_in": mi, "frappes": hb}, open(HITS_JSON, "w")); return mi, hb
MUSIC_IN, HITS = frappes()
FINE = 0.0                            # recalage fin éventuel mesuré sur l'export AAC
MUSIC_IN += FINE; HITS = [[h[0] - FINE] + list(h[1:]) for h in HITS]
KICKS = kicks_of(HITS)
CUTS = snap_list(HITS, CUT_T); CUTF = [fr(c) for c in CUTS]
IDROP = len(PRE); DROPF = CUTF[IDROP]; TB = T

# ---------------- voix ----------------
V_SRC0 = 423.89                       # source M à t = 0 (« assez » 424,04 -> 0,15 s ; « population. » fin 429,42 -> 5,53 s, avant le drop)
V_IN, V_OUT = 423.95, 429.75          # « …loyaux à la République. » (fin 423,60) non gardé ; applaudissements après la phrase en fondu
def t_of_src(s): return s - V_SRC0
# débuts de mots : enveloppe d'énergie + whisper (tx/phr2.json)
WORDS = [("ASSEZ", 424.04), ("DE", 424.48), ("CETTE", 424.80), ("ISLAMOPHOBIE,", 425.00), ("ASSEZ", 426.16), ("DE", 426.46), ("CES", 426.90),
         ("DISCOURS", 427.06), ("QUI", 427.42), ("STIGMATISENT", 427.58), ("UNE", 428.18), ("PARTIE", 428.34), ("DE", 428.60), ("LA", 428.74),
         ("POPULATION.", 428.84)]
def wt(i): return t_of_src(WORDS[i][1])
def ln(*idx): return [(WORDS[i][0], wt(i)) for i in idx]

# ---------------- polices ransom-note ----------------
S = "/System/Library/Fonts/Supplemental/"
FONTS = [(S + "Arial Black.ttf", 0), (S + "Georgia Bold.ttf", 0), (S + "Times New Roman Bold.ttf", 0), (S + "Impact.ttf", 0),
         (S + "Courier New Bold.ttf", 0), (S + "Rockwell.ttc", 2), (S + "AmericanTypewriter.ttc", 2), (S + "Didot.ttc", 2),
         (S + "Bodoni 72.ttc", 2), (S + "Futura.ttc", 2)]
FCOND = (S + "Futura.ttc", 4)
STYLES = [(rgb(PAPER), rgb(INK)), (rgb(INK), rgb(WHITE)), (rgb(AZUR), rgb(WHITE)), (rgb(WHITE), rgb(AZUR)),
          (rgb(CIEL), rgb(INK)), (rgb(INK), rgb(CIEL)), (rgb(ARGENT), rgb(INK)), ((236, 233, 224), (20, 20, 20))]
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
FTALL = [(S + "Impact.ttf", 0), (S + "Futura.ttc", 4), (S + "Bodoni 72.ttc", 2), (S + "Didot.ttc", 2), (S + "Rockwell.ttc", 2), (S + "Times New Roman Bold.ttf", 0)]
def tall(im, k):
    """Lettre de magazine étirée en hauteur (pièce découpée plus haute que large)."""
    a = np.asarray(im); return Image.fromarray(cv2.resize(a, (a.shape[1], int(a.shape[0] * k)), interpolation=cv2.INTER_CUBIC))
def word_parts(word, t, h, rng, letters, seq, tape=None, stretch=1.0):
    """Pièces d'un mot : [(img, t)] ; lettres découpées une à une (seq = intervalle entre lettres, 0 = toutes ensemble)."""
    if not letters: return [(shadowed(chip(word, h, rng, tape=tape)), t)]
    if stretch > 1:
        return [(shadowed(tall(chip(c, h * rng.uniform(0.94, 1.06), rng, fspec=FTALL[rng.integers(len(FTALL))], rot=0, tape=False), stretch)
                          .rotate(rng.uniform(-6, 6), resample=Image.BICUBIC, expand=True)), t + k * seq) for k, c in enumerate(word)]
    return [(shadowed(chip(c, h * rng.uniform(0.92, 1.08), rng, rot=rng.uniform(-7, 7), tape=False)), t + k * seq) for k, c in enumerate(word)]
def board(lines, y0, seed, h=112, letters=(), seq=0.0, maxw=XMAX - XMIN - 30, tape=None, stretch=1.0):
    """lines = [[(mot, t), …], …] -> pièces placées [(img, cx, cy, t)] ; mots de `letters` en lettres découpées."""
    rng = np.random.default_rng(seed); pieces = []; y = y0
    for line in lines:
        words = [word_parts(w, t, h * (1.12 if w in letters else 1.0), rng, w in letters, seq, tape, stretch) for w, t in line]
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
        FOLDS = (1 + 0.03 * acc)[..., None].astype(np.float32)
    return FOLDS
_tex = {}
def paper(col):
    if col not in _tex:
        rng = np.random.default_rng(len(_tex) + 3)
        n = cv2.resize(rng.standard_normal((48, 27)).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC)
        n2 = cv2.GaussianBlur(rng.standard_normal((H, W)).astype(np.float32), (0, 0), 1.2)
        fib = cv2.GaussianBlur(rng.standard_normal((H, W)).astype(np.float32), (0, 0), sigmaX=6, sigmaY=0.8)   # fibres
        _tex[col] = np.clip(hexc(col)[None, None, :] * (1 + 0.012 * n[..., None] + 0.025 * n2[..., None] + 0.035 * fib[..., None]) * folds(), 0, 1).astype(np.float32)
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
        VIG = (1 - 0.12 * np.clip(r, 0, 1) ** 2.4)[..., None].astype(np.float32)
    g = np.random.default_rng(1000 + f).standard_normal((H // 2, W // 2)).astype(np.float32)
    g = cv2.resize(g, (W, H), interpolation=cv2.INTER_LINEAR)[..., None] * 0.024
    return np.clip(img * VIG + g, 0, 1)

# ---------------- lecture source, détourage ----------------
_still = {}
def read_frames(src, t, n_out):
    path, sfps = SRC[src][0], SRC[src][1]
    if sfps is None:                                                       # photo fixe
        if path not in _still: _still[path] = cv2.imread(HG + "/" + path).astype(np.float32) / 255
        return [_still[path]] * n_out
    need = [int(round(i * sfps / FPS)) for i in range(n_out)]
    p = subprocess.run([FF, "-v", "error", "-ss", "%.4f" % t, "-i", HG + "/" + path, "-frames:v", str(need[-1] + 1),
                        "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True)
    a = np.frombuffer(p.stdout, np.uint8).reshape(-1, 1080, 1920, 3)
    return [a[min(i, len(a) - 1)].astype(np.float32) / 255 for i in need]
CTRL = {}
def masks(key, frames, box, pt):
    """Découpe propre (decoupe.py) + contrôle : aucun membre coupé aux bords du box, un seul morceau ; planche à regarder."""
    d = CACHE + "decoupe/" + key; ms = masques(frames, box, pt, d)
    c = [controle(m) for m in ms]
    worst = {k: max(x[k] for x in c) for k in ("gauche", "droite", "haut", "morceaux", "bas_net")}
    yb = max(int(np.where((m > 0.5).any(1))[0][-1]) for m in ms if (m > 0.5).any())
    CTRL[key] = dict(worst, bas_px=yb); print("    découpe", key, CTRL[key], flush=True)
    planche(frames, ms, box, CACHE + "decoupe/planche_%s.jpg" % key)
    return ms, yb
def grade(x, sat=1.10):
    x = 0.82 * x + 0.18 * (x * x * (3 - 2 * x))
    L = x @ np.array([0.0722, 0.7152, 0.2126], np.float32)
    return np.clip(L[..., None] + (x - L[..., None]) * sat, 0, 1)
def lum(x, gain=1.15):
    L = x @ np.array([0.0722, 0.7152, 0.2126], np.float32)
    L = L / max(float(np.percentile(L, 99)), 0.2); L = np.clip(L, 0, 1) ** 0.75
    L = np.clip((L - 0.5) * gain + 0.5 + 0.03, 0, 1); return 0.75 * L + 0.25 * (L * L * (3 - 2 * L))
DUO = {"ciel": (INK, "#CDEEFC"), "azur": ("#0B3F66", WHITE)}       # bichromies (rares) ; sinon photos en couleur
def duotone(x, duo):
    if duo == "couleur": return grade(x, 1.18)
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
STRIP_COLS = [INK, WHITE, CIEL, INK, AZUR, PAPER, INK, WHITE]
def strip_rgba(w, h, rng, colhex, ht=False):
    col = hexc(colhex); dot = hexc(INK if colhex in (WHITE, CIEL, PAPER, ARGENT) else CIEL)
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
    def __init__(self, frames, box, width, center, angle, f0, key, duo, border=16, pol=False):
        self.frames, self.box, self.width, self.center, self.angle, self.f0, self.key, self.duo = frames, box, width, center, angle, f0, key, duo
        x0, y0, x1, y1 = box; self.h = int(round(width * (y1 - y0) / (x1 - x0)))
        if pol: border = 22
        self.b = border; self.bb = 4 * border if pol else border; self.pol = pol      # polaroid : bas plus large, bords nets
        rng = np.random.default_rng(skey(key)); M = 40
        self.M = M; hh, ww = self.h + border + self.bb, width + 2 * border
        self.mask = np.pad(np.ones((hh - 4, ww - 4), np.float32), 2) if pol else torn_mask(hh, ww, rng, rough=6, step=11, inset=3)
        self.shadow = np.zeros((hh + 2 * M, ww + 2 * M), np.float32); self.shadow[M + 9:M + 9 + hh, M + 7:M + 7 + ww] = self.mask * 0.5
        self.shadow = cv2.GaussianBlur(self.shadow, (0, 0), 4)
        self.tapes = []
        for (tx, ty) in ((M + int(rng.uniform(-10, 30)), M - 12), (M + ww - int(rng.uniform(90, 140)), M + hh - 26)):
            self.tapes.append((rot_rgba(tape_rgba(int(rng.uniform(110, 150)), 38, rng), rng.uniform(-40, -25)), (tx, ty)))
    def rgba(self, i):
        x0, y0, x1, y1 = self.box; b, M = self.b, self.M
        c = cv2.resize(duotone(self.frames[i][y0:y1, x0:x1], self.duo), (self.width, self.h), interpolation=cv2.INTER_AREA)
        hh, ww = self.h + b + self.bb, self.width + 2 * b
        out = np.zeros((hh + 2 * M, ww + 2 * M, 4), np.float32); out[..., 3] = self.shadow
        body = np.ones((hh, ww, 3), np.float32) * np.array([0.96, 0.97, 0.97], np.float32); body[b:b + self.h, b:b + self.width] = c
        a = self.mask[..., None]; reg = out[M:M + hh, M:M + ww]
        reg[..., :3] = body * a; reg[..., 3] = np.maximum(self.mask, reg[..., 3])
        for t, (tx, ty) in self.tapes: over(out, t, tx, ty)
        return out
def beat_grid():
    """Temps : kicks réels après le drop + grille d'un temps comptée à rebours depuis le drop dans le pont sans kick."""
    g = [k for k in KICKS if k >= CUTS[IDROP] - 0.05]; t = CUTS[IDROP] - T
    while t > 0: g.append(t); t -= T
    return sorted(g)
BEATS = beat_grid(); BEATF = [fr(b) for b in BEATS]
def nbeat(f): return sum(1 for b in BEATF if b <= f)
def jit(key, k, amp=8.0, ang=1.5):
    r = np.random.default_rng(skey(key) * 1000 + k); return r.uniform(-amp, amp), r.uniform(-amp, amp), r.uniform(-ang, ang)

# ---------------- plans ----------------
BOX = (360, 0, 1590, 650)             # pupitre : logo LFI (x > 1590), bandeau et pupitre exclus par decoupe.py ; bras jamais au bord (controle = 0)
TRIM = 26                             # lignes du bas de la découpe retirées (feuilles posées sur le pupitre)
ZB = (0, 80, 1920, 1080)              # Vieux-Port 2017 (aucun logo dans ces plans)
HB = (200, 370, 1700, 1080)           # salle 2025 depuis la scène : écran « La force de tout changer » (y < 360) et logo LFI hors cadre
PB = {"vieuxport-2": (0, 160, 1920, 1300), "port-ndg-pano": (0, 0, 1920, 667), "ndg-2024": (0, 0, 1920, 2200), "panier-rue": (0, 250, 1920, 2560),
      "panier": (0, 300, 1920, 2560), "velodrome-virage-nord": (0, 445, 1280, 640), "vieuxport-cc0": (0, 300, 1920, 1440)}
def ph(k, w, c, a, t0=0.0, t=0.0): return (k, t, PB.get(k, ZB if k == "Z" else HB), w, c, a, t0, "couleur")
def pt_(cx, y=0.62): return ((cx - BOX[0]) / (BOX[2] - BOX[0]), y)
KEYL = ("ASSEZ",)
SC = (1.66, 1.71)
LIFT = 250                            # bas déchiré de la découpe posé à 250 px du bas : le visage monte dans la zone sûre (< 75 % de la hauteur)
SHOTS = [
    dict(id="A1", kind="cut", src="M", t=None, bg=CIEL, sheet=(WHITE, "bas", 0.87, -4, 1), ghost=INK, box=BOX, pt=pt_(980), scale=SC, cx=980,
         boards=[([ln(0, 1, 2), ln(3)], None)], txt_h=165, strips=3,
         photos=[ph("vieuxport-2", 470, (250, 800), -7, 0.62)],
         why="SYNCHRO (régie d'origine) : « Assez de cette islamophobie, », index levé ; Vieux-Port et Notre-Dame-de-la-Garde en polaroid couleur"),
    dict(id="A2", kind="cut", src="M", t=None, bg=PAPER, sheet=(INK, "bas", 0.87, 4, 2), ghost=CIEL, box=BOX, pt=pt_(980), scale=SC, cx=980,
         boards=[([ln(4, 5, 6), ln(7, 8), ln(9)], None)], txt_h=150, strips=3,
         photos=[ph("panier-rue", 330, (860, 800), 6, wt(7))],
         why="SYNCHRO : « assez de ces discours qui stigmatisent », sur papier blanc + bande noire déchirée, ruelle du Panier"),
    dict(id="A3", kind="cut", src="M", t=None, bg=INK, sheet=(CIEL, "bas", 0.87, -3, 3), ghost=AZUR, box=BOX, pt=pt_(980), scale=SC, cx=980,
         boards=[([ln(10, 11), ln(12, 13), ln(14)], None)], txt_h=150, strips=3,
         photos=[ph("Z", 460, (250, 820), -6, wt(11), 1.0), ph("velodrome-virage-nord", 470, (840, 760), 5, wt(14))],
         why="SYNCHRO : « une partie de la population. » pendant le break ; fond noir, foule du Vieux-Port 2017 et virage du Vélodrome en couleur"),
    dict(id="B1", kind="sil", src="M", t=500.90, bg=CIEL, sheet=(WHITE, "bas", 0.87, -3, 8), ghost=INK, box=BOX, pt=pt_(950), dest_w=SC[0] * (BOX[2] - BOX[0]), cx=950, push=(1.0, 1.04),
         rboards=[([[("ASSEZ", 0.0), ("DE", 0.0), ("CETTE", 0.0)], [("ISLAMOPHOBIE.", 0.0)]], 0.0)], txt_y=290, txt_h=175, letters=("ASSEZ",), strips=3, flash=True,
         photos=[ph("ndg-2024", 330, (850, 820), 6, 0.0)],
         why="drop : silhouette blanche 3 images puis Bompard détouré en couleur, bras levé vers la salle (musique seule)"),
    dict(id="B2", kind="collage", bg=PAPER,
         photos=[ph("vieuxport-2", 720, (540, 640), -4), ph("M", 700, (560, 1110), 4, TB, 210.5), ph("velodrome-virage-nord", 680, (520, 1560), -3, 2 * TB)],
         strips=4, why="collage Marseille en couleur, une photo par temps : Vieux-Port et la Bonne Mère, la salle du meeting 2025, le virage du Vélodrome"),
    dict(id="B3", kind="cut", src="M", t=451.50, bg=PAPER, sheet=(CIEL, "bas", 0.87, 4, 5), ghost=INK, box=BOX, pt=pt_(980), scale=SC, cx=980,
         rboards=[([[("ASSEZ", 0.0), ("DE", 0.0), ("CES", 0.0)], [("DISCOURS", 0.0), ("QUI", 0.0)], [("STIGMATISENT.", 0.0)]], 0.0)], txt_y=270, txt_h=160,
         letters=("ASSEZ",), strips=3,
         photos=[ph("port-ndg-pano", 640, (540, 820), -3, 0.0)],
         why="Bompard qui pointe la salle (musique seule), panorama du port et de Notre-Dame-de-la-Garde derrière"),
    dict(id="B4", kind="collage", bg=INK,
         photos=[ph("panier-rue", 400, (300, 640), -5), ph("Z", 660, (620, 1060), 4, TB, 19.0), ph("ndg-2024", 420, (330, 1520), -4, 2 * TB),
                 ph("M", 600, (720, 1640), 6, 3 * TB, 367.0)],
         strips=3, why="collage sur fond noir qui se remplit à chaque temps : Panier, Vieux-Port 2017 et grande roue, la Bonne Mère, la salle 2025"),
    dict(id="B5", kind="cut", src="M", t=360.00, bg=CIEL, sheet=(INK, "bas", 0.87, 3, 6), ghost=INK, box=BOX, pt=pt_(990), scale=SC, cx=990,
         photos=[ph("vieuxport-cc0", 440, (260, 800), -6, 0.0), ph("M", 420, (830, 740), 5, TB, 212.5)],
         strips=3, why="Bompard index levé (musique seule), quai du Vieux-Port et salle en photos"),
    dict(id="B6", kind="collage", bg=PAPER,
         photos=[ph("Z", 720, (540, 700), -3, 0.0, 47.5), ph("panier", 380, (300, 1330), 5, TB), ph("port-ndg-pano", 700, (600, 1650), -4, 2 * TB)],
         strips=3, why="foule aux drapeaux devant le port (2017), le Panier, la ville vue de la Bonne Mère"),
    dict(id="B7", kind="collage", bg=CIEL,
         photos=[ph("M", 780, (540, 900), 3, 0.0, 370.0), ph("vieuxport-2", 520, (430, 1450), -5, TB / 2)],
         strips=2, why="respiration 2 temps : la salle du meeting en couleur"),
    dict(id="FIN", kind="card", bg=PAPER, sheet=(CIEL, "bas", 0.74, -3, 7), push=(1.0, 1.03),
         rboards=[([[("MANUEL", 0.0)], [("BOMPARD", 0.0)]], 0.0)], txt_y=430, txt_h=200, letters=("MANUEL", "BOMPARD"), seq=TB / 3, stretch=1.7,
         photos=[ph("vieuxport-2", 520, (540, 1430), -3, 2 * TB)],
         why="carton final : MANUEL BOMPARD en grandes lettres découpées (noir / blanc / ciel), polaroid du Vieux-Port, pas de CTA"),
]
BOUNDS_T = [0] + CUTF + [fr(END)]
assert len(BOUNDS_T) == len(SHOTS) + 1, (len(BOUNDS_T), len(SHOTS))
for i, sh in enumerate(SHOTS):
    sh["a"], sh["bb"] = BOUNDS_T[i], BOUNDS_T[i + 1]; sh["n"] = sh["bb"] - sh["a"]; sh["clip"] = "R12_%s.mov" % sh["id"]
    if sh.get("src") == "M" and sh["t"] is None: sh["t"] = V_SRC0 + sh["a"] / FPS              # plans A synchro avec la voix
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
            p = board(lines, sh["txt_y"], seed + j, h=sh.get("txt_h", 130), letters=sh.get("letters", ()), seq=sh.get("seq", 0.0), tape=False, stretch=sh.get("stretch", 1.0))   # pas de scotch sur les lettres
            boards.append(([(im, cx, cy, rel(t)) for im, cx, cy, t in p], fr(rel(t0))))
    elif sh.get("txt"):
        p = board(sh["txt"], sh["txt_y"], seed, h=sh.get("txt_h", 130), letters=sh.get("letters", ()), seq=sh.get("seq", 0.0))
        boards.append(([(im, cx, cy, rel(t)) for im, cx, cy, t in p], a))
    big = []
    if sh.get("big"):
        big = [(im, cx, cy, rel(t)) for im, cx, cy, t in big_text(sh["big"], sh["big_y"], (S + "Impact.ttf", 0), (XMAX - XMIN) * 0.92, sh["big_sizes"])]
    photos = [Photo(read_frames(ps, pt, n), pbox, pw, pc, pa, fr(rel(pt0)) if pt0 > 0 or sh["id"].startswith("B") else a, (sh["id"], j), duo)
              for j, (ps, pt, pbox, pw, pc, pa, pt0, duo) in enumerate(sh.get("photos", []))]
    for ph, spec in zip(photos, sh.get("photos", [])):
        if spec[0] == "Z" or spec[0] in PHOTOS: ph.__init__(ph.frames, ph.box, ph.width, ph.center, ph.angle, ph.f0, ph.key, ph.duo, pol=True)
    if sh["id"].startswith("A"):                                             # plans A : apparition au temps absolu du mot
        for ph, spec in zip(photos, sh.get("photos", [])): ph.f0 = max(a, fr(spec[6])) if spec[6] > 0 else a
    strips = make_strips(sh)
    k0 = nbeat(a)
    if sh["kind"] in ("cut", "sil"):
        raw = read_frames(sh["src"], sh["t"], n)
        ms, yb = masks("%s_%s_%.2f_%d" % (sh["id"], sh["src"], sh["t"], n), raw, sh["box"], sh["pt"])
        yb -= TRIM; ms = [np.where(np.arange(m.shape[0])[:, None] > yb, 0, m).astype(np.float32) for m in ms]
        ms = [bas_dechire(m, seed=skey(sh["id"])) for m in ms]             # buste jusqu'au pupitre, fini en bord de papier déchiré
    for i in range(n):
        f = a + i; u = i / max(n - 1, 1); kb = nbeat(f) - k0
        img = paper(sh["bg"])
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
                ccx = W / 2 + ((x1 - x0) / 2 - (sh["cx"] - x0)) * sc; ccy = H - LIFT - (yb - (y1 - y0) / 2) * sc; r_ = 7
            else:
                z = sh["push"][0] + (sh["push"][1] - sh["push"][0]) * u
                sc = sh["dest_w"] / (x1 - x0) * z; hh = (y1 - y0) * sc
                ccx = W / 2 + ((x1 - x0) / 2 - (sh["cx"] - x0)) * sc; ccy = H - LIFT - (yb - (y1 - y0) / 2) * sc; r_ = 9
            if sh.get("ghost"):                                             # double tirage tramé, décalé, qui saute sur les temps
                gdx, gdy, gda = jit((sh["id"], "g"), nbeat(f), amp=10, ang=1.0)
                g = ghost_rgba(raw[i], m, sh["box"], 1.0, sh["ghost"])
                paste(img, g, ccx + 46 + gdx, ccy + 40 + gdy, sc * 1.08, -2.5 + gda)
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
            for j, (tx, ty, ta) in enumerate(((175, 300, -32), (905, 300, 30), (175, 1540, 28), (905, 1540, -30))):
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
VGAIN = 16.5
def make_audio():
    import soundfile as sf, scipy.signal as ss
    sr = 48000; N = int(round(END * sr))
    def grab(path, t, dur):
        p = subprocess.run([FF, "-v", "error", "-ss", "%.3f" % t, "-t", "%.3f" % dur, "-i", path, "-ac", "2", "-ar", str(sr), "-f", "f32le", "-"], capture_output=True)
        return np.frombuffer(p.stdout, np.float32).reshape(-1, 2).copy()
    voix = np.zeros((N, 2), np.float32); mus = np.zeros((N, 2), np.float32)
    v = grab(HG + "/" + SRC["M"][0], V_IN, V_OUT - V_IN); env = np.ones(len(v), np.float32)
    k = int(0.04 * sr); env[:k] = np.linspace(0, 1, k); k = int(0.15 * sr); env[-k:] = np.linspace(1, 0, k)
    i0 = int(round(t_of_src(V_IN) * sr)); voix[i0:i0 + len(v)] = v * env[:, None] * 10 ** (VGAIN / 20)
    m = music_raw(MUSIC_IN)[:N]; t = np.arange(len(m)) / sr; vend = t_of_src(V_OUT); dr = CUTS[IDROP]
    ml = ss.sosfiltfilt(ss.butter(4, 520, "lp", fs=sr, output="sos"), m, axis=0).astype(np.float32)   # couplet étouffé sous la voix
    w = np.interp(t, [0, CUTS[IDROP - 1], dr - 0.03, dr], [0.0, 0.15, 0.55, 1.0])[:, None]            # le filtre s'ouvre dans le break
    x = ml * (1 - w) + m * w
    gdb = np.interp(t, [0, 0.3, CUTS[IDROP - 1], dr - 0.03, dr, END], [-17, -14, -15, -11, -5, -5])
    k = int(0.40 * sr); fo = np.ones(len(m), np.float32); fo[-k:] = np.linspace(1, 0, k)
    mus[:len(m)] = x * (10 ** (gdb / 20) * fo)[:, None]
    sf.write(OUT + "R12-voix.wav", voix, sr, subtype="FLOAT"); sf.write(OUT + "R12-musique.wav", mus, sr, subtype="FLOAT")
    sf.write(D + "tmp_mix.wav", voix + mus, sr, subtype="FLOAT")
    r = subprocess.run([FF, "-hide_banner", "-i", D + "tmp_mix.wav", "-af", "loudnorm=I=-14:TP=-2.5:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    js = json.loads(r[r.rindex("{"):r.rindex("}") + 1])
    af = ("loudnorm=I=-14:TP=-2.5:LRA=11:measured_I=%s:measured_TP=%s:measured_LRA=%s:measured_thresh=%s:offset=%s:linear=true,"
          "aresample=48000" % (js["input_i"], js["input_tp"], js["input_lra"], js["input_thresh"], js["target_offset"]))
    subprocess.run([FF, "-v", "error", "-y", "-i", D + "tmp_mix.wav", "-af", af, "-c:a", "pcm_s24le", OUT + "R12-mix.wav"], check=True)
    os.remove(D + "tmp_mix.wav"); print("audio : mix avant normalisation", js["input_i"], "LUFS")
    for nm, y_ in (("voix", voix[i0:i0 + len(v)]), ("musique sous la voix", mus[:int(dr * sr)]), ("musique après le drop", mus[int(dr * sr):])):
        sf.write(D + "tmp.wav", y_, sr, subtype="FLOAT")
        r = subprocess.run([FF, "-hide_banner", "-i", D + "tmp.wav", "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True).stderr
        print("  %-22s %s" % (nm, re.findall(r"I:\s+(-?[0-9.]+) LUFS", r)[-1])); os.remove(D + "tmp.wav")

# ---------------- plan ----------------
PHR = "Assez de cette islamophobie, assez de ces discours qui stigmatisent une partie de la population."
def build_plan():
    video = []
    for sh in SHOTS:
        v = {"id": sh["id"], "clip": sh["clip"], "folder": "genR12", "path": OUT + sh["clip"], "s": 0, "e": sh["n"], "rec": sh["a"], "dur": sh["n"],
             "clip_fps": FPS, "speed_pct": 100, "track": 1, "note": sh["why"], "kind": sh["kind"], "temps": round(sh["n"] / FPS / T, 2)}
        if sh.get("src"):
            path, sfps, url, off, ctx = SRC[sh["src"]]
            v["source"] = {"fichier": path, "in_s": round(sh["t"], 3), "out_s": round(sh["t"] + sh["n"] / FPS, 3), "fps": sfps, "url": url, "contexte": ctx,
                           "youtube_t": round(off + sh["t"], 1)}
        if sh.get("photos"):
            v["photos"] = [{"fichier": SRC[p[0]][0], "in_s": round(p[1], 2), "out_s": round(p[1] + sh["n"] / FPS, 2), "cadre_source": p[2], "bichromie": p[7],
                            "url": SRC[p[0]][2], "polaroid": p[0] == "Z"} for p in sh["photos"]]
        video.append(v)
    texts = []
    for sh in SHOTS:
        for lines, _ in sh.get("boards", []):
            for line in lines: texts.append({"plan": sh["id"], "texte": " ".join(w for w, _ in line)})
        for lines, _ in sh.get("rboards", []): texts.append({"plan": sh["id"], "texte": " ".join(w for line in lines for w, _ in line)})
        for s_, t_, c_ in sh.get("big", []): texts.append({"plan": sh["id"], "texte": s_})
    plan = {"name": "R12 - Collage ransom-note Marseille - Manuel Bompard", "fps": FPS, "w": W, "h": H, "duree_s": END,
            "note": "Plans ProRes 9:16 composés en Python (lot7/_claude/gen/R12/out) : fonds papier froissé ciel / azur / blanc + feuille déchirée, "
                    "Bompard détouré seul (_claude/outils/decoupe.py : ni pupitre ni micro, bas du buste posé sur le bas du cadre), double tirage tramé, "
                    "silhouette blanche 3 images au drop, photos de Marseille en couleur (polaroids scotchés), textes ransom-note cuits. s/e en images du clip (30 i/s), rec en images timeline. "
                    "Coupes sur les kicks réels de Bande organisée (out/R12-frappes.json). Aucun ralenti. Générateur : lot7/_claude/gen/R12/genR12.py",
            "phrase": {"texte": PHR, "url": SRC["M"][2] + "&t=424", "source": SRC["M"][0], "in_s": 424.04, "out_s": 429.42,
                       "timeline_s": [round(t_of_src(424.04), 2), round(t_of_src(429.42), 2)],
                       "voix": "son direct, plans A1-A3 synchro (même source, même moment, plan pupitre de la régie)",
                       "contexte": "dite juste après « …ne seraient pas vraiment loyaux à la République » (sondage IFOP sur les musulmans), non gardé"},
            "musique": {"fichier": "lot7/sons/R12-bande-organisee_complet.wav", "titre": "13'Organisé - Bande organisée", "url": SON_URL,
                        "debut_complet_s": round(MUSIC_IN, 4), "fin_complet_s": round(MUSIC_IN + END, 3), "drop_timeline_s": CUTS[IDROP],
                        "coupes_frappes_s": CUTS, "coupes_images": CUTF},
            "textes": texts, "video": video,
            "audio": [{"id": "mix", "clip": "R12-mix.wav", "folder": "genR12", "path": OUT + "R12-mix.wav", "rec": 0, "track": 1,
                       "note": "mix -14 LUFS : voix %.2f-%.2f s (+%.0f dB) à %.2f s ; Bande organisée dès %.3f s du complet, couplet passe-bas 520 Hz baissé sous la voix, "
                               "filtre qui s'ouvre dans le break, plein au drop (refrain), fondu de fin 0,4 s" % (V_IN, V_OUT, VGAIN, t_of_src(V_IN), MUSIC_IN)}],
            "stems": ["lot7/_claude/gen/R12/out/R12-voix.wav", "lot7/_claude/gen/R12/out/R12-musique.wav"],
            "logos_exclus": "meeting 2025 : logo LFI (haut droite), écran « La force de tout changer » et bandeau « élections municipales » supprimés par le "
                            "détourage ou hors des cadres photo ; Vieux-Port 2017 : aucun logo ; Vélodrome : bandeaux sponsors hors cadre",
            "photos_libres": "lot7/_claude/gen/R12/photos-licences.json (Wikimedia Commons ; CC BY / CC BY-SA : créditer les auteurs dans la légende)",
            "controle_decoupes": CTRL}
    json.dump(plan, open(D + "plan-R12.json", "w"), indent=1, ensure_ascii=False)
    son = {"id": "R12", "titre": "Bande organisée", "artiste": "13'Organisé (SCH, Kofs, JuL, Naps, Soso Maness, Elams, Solda, Houari)", "url": SON_URL,
           "chaine": "DORETDEPLATINE (officielle, certifiée, label de JuL, « Bande Organisée … // Clip Officiel »)",
           "fichier": "lot7/sons/R12-bande-organisee_complet.wav",
           "extrait_complet_s": {"debut": round(MUSIC_IN, 4), "fin": round(MUSIC_IN + END, 3)},
           "paroles_audibles": "sous la phrase : fin d'un couplet, étouffée (passe-bas) et baissée, puis le break sans kick ; au drop : le refrain « En bande organisée… » jusqu'aux « hasta luego »",
           "bpm": round(60 / T, 1), "temps_s": T,
           "drop": {"complet_s": round(MUSIC_IN + CUTS[IDROP], 4), "timeline_s": CUTS[IDROP], "nature": "retour du kick après le break, refrain « En bande organisée »"},
           "frappes_timeline_s": [round(k, 4) for k in KICKS], "coupes_sur_frappes_s": CUTS,
           "mix": "lot7/_claude/gen/R12/out/R12-mix.wav"}
    json.dump(son, open(D + "son.json", "w"), indent=1, ensure_ascii=False)

# ---------------- aperçu 540x960 ----------------
APERCU = HG + "/preview/apercu-R12.mp4"
def apercu():
    plan = json.load(open(D + "plan-R12.json")); ins = []; fl = []
    for i, v in enumerate(plan["video"]):
        ins += ["-i", OUT + v["clip"]]
        fl.append("[%d:v]trim=start_frame=%d:end_frame=%d,setpts=PTS-STARTPTS,scale=540:960,setsar=1[v%d]" % (i, v["s"], v["e"], i))
    k = len(plan["video"]); fl.append("".join("[v%d]" % i for i in range(k)) + "concat=n=%d:v=1:a=0[v]" % k)
    ins += ["-i", OUT + "R12-mix.wav"]
    subprocess.run([FF, "-v", "error", "-y"] + ins + ["-filter_complex", ";".join(fl), "-map", "[v]", "-map", "%d:a" % k,
                    "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "aac", "-b:a", "192k", "-shortest", APERCU], check=True)
    print("aperçu", APERCU)
# ---------------- mesure sur l'export : coupes vs frappes, LUFS / TP ----------------
def mesure():
    r = subprocess.run([FF, "-v", "info", "-i", APERCU, "-vf", "scale=135:240,select='gt(scene,0.2)',showinfo", "-an", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    cuts = [float(x) for x in re.findall(r"pts_time:([0-9.]+)", r)]
    p = subprocess.run([FF, "-v", "error", "-i", APERCU, "-vn", "-ac", "2", "-ar", "48000", "-f", "f32le", "-"], capture_output=True)
    y = np.frombuffer(p.stdout, np.float32).reshape(-1, 2)
    hh = detect_hits(y); worst = 0
    for i, c in enumerate([fr_ / FPS for fr_ in CUTF]):
        det = min(cuts, key=lambda x: abs(x - c)) if cuts else None
        pool = [x[0] for x in hh if (x[1] == "kick" and x[3] > 0.03)]
        k = min(pool, key=lambda t: abs(t - c)); e = (c - k) * 1000; worst = max(worst, abs(e))
        print("  coupe %.3f (détectée %s)  kick %.4f  écart %+.1f ms" % (c, "%.3f" % det if det is not None else "-", k, e))
    print("écart max coupes/frappes : %.1f ms" % worst)
    r = subprocess.run([FF, "-hide_banner", "-i", APERCU, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
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
