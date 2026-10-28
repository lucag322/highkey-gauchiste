# A9 (lot 4) — Aura N&B, Louis Boyard (député LFI du Val-de-Marne), son « METAMORPHOSIS » (INTERWORLD, lien du brief, chaîne Chill Nation).
# Modèle : lot3/_claude/gen/A8/genA8.py (frappes réelles, N&B adouci, texte mot à mot recentré) + A6. Aperçu HORS Resolve (ffmpeg/numpy).
# Phrase : « La jeune génération a commencé à écrire son histoire. » (meeting Nouveau Paris populaire, 31/01/2026, chaîne Louis Boyard,
#          youtube cNkMqVnlUl0 @ 142,68-146,25 s = lot3/sources/K1-boyard-meeting-npp-a.mp4 2,68-6,25 s). Autre phrase que G1 (santé mentale) et K1 (QAG 06/10).
# Son : extrait continu du morceau, fin du break calme (voix de Boyard par-dessus), drop (1er kick + 808) à 54,89 s du complet.
# Règles : 9:16 plein écran, aucun visage coupé, aucun logo (LFI haut droite, pupitre NOUVEAU PARIS POPULAIRE, sous-titres incrustés QAG hors fenêtre),
# coupes sur les kicks réels (87,5 BPM demi-temps : 1 temps = 0,686 s), plans >= 1 temps, poussée lente avant seulement (le recadrage suit la taille
# du visage : jamais de dézoom même quand la caméra source recule), <= 15 s, ralentis = speed_pct (Resolve Optical Flow).
# Usage : python genA9.py [shots] [cards] [audio] [plan] [apercu] [only=ID,ID]   (sans argument = tout)
import sys, os, json, subprocess, math, functools
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
ROOT = "/Users/luca.grousset/Movies/highkey-gauchiste"; LOT = ROOT + "/lot4"
sys.path.insert(0, ROOT + "/_claude/outils")
import framing
from framing import plan_views
from fx import gblur, motion_blur, vignette, to8, ease_out
D = LOT + "/_claude/gen/A9/"; OUT = D + "out/"; os.makedirs(OUT, exist_ok=True)
framing.ROOT = LOT; framing.CACHE = D + "cache"          # lot4/sources/A9-* = liens vers les sources des lots 2-3 (rien de copié ni modifié)
framing.head_box = lambda f: (f[0] - 0.12 * f[2], f[1] - 0.5 * f[3], f[0] + 1.12 * f[2], f[1] + 1.2 * f[3])
framing.view_for = functools.partial(framing.view_for, margin=0.04)
FF = "/opt/homebrew/bin/ffmpeg"; FPS = 30; W, H = 1080, 1920
RED = (0xE4, 0x00, 0x2B); WHITE = (255, 255, 255)
F_BLACK = "/System/Library/Fonts/Supplemental/Arial Black.ttf"
F_AURA = ("/System/Library/Fonts/Helvetica.ttc", 2)
MA, MB = "A9-boyard-meeting-npp-a.mp4", "A9-boyard-meeting-npp-b.mp4"
QAG = "A9-boyard-lfi-qag.mp4"
REAL = {MA: "lot3/sources/K1-boyard-meeting-npp-a.mp4", MB: "lot3/sources/K1-boyard-meeting-npp-b.mp4", QAG: "lot3/sources/K1-boyard-lfi-qag-2026-10.mp4"}
SFPS = 25                                                         # toutes les sources : 25 i/s
# zones utilisables (px source 1920x1080) :
#  meetings : logo LFI haut droite (x > 1690), pupitre « NOUVEAU PARIS POPULAIRE » (y > 790 en plan serré)
#  QAG LFI  : logo LFI haut gauche, timer AN haut droite, sous-titres incrustés (y > 790)
B_M = (0, 0, 1690, 790); B_Q = (270, 0, 1555, 790); B_FULL = (0, 0, 1690, 1080)
# ---------------- musique ----------------
SON_FILE = LOT + "/sons/A9-interworld-metamorphosis_complet.wav"
SON_URL = "https://youtu.be/NS9z2QHcZdY"
MDROP = 54.915                                   # drop : attaque du 1er kick + 808 après le break (complet), mesurée
def fr(t): return int(round(t * FPS))
DROPF = 152; DROP = DROPF / FPS                  # 5,067 s
END = 14.97                                      # règle : aura N&B 15 s max
BEAT = 0.686                                     # kicks pleins mesurés 54,92 -> 63,84 (13 intervalles)
# ---------------- phrase (Whisper + attaques mesurées dans la source MA) ----------------
T_LONG = 2.55                                    # 1re image du plan parlé (caméra déjà serrée sur Boyard)
PF = 36                                          # hook « aura. » 1,2 s
V_IN, V_OUT = 2.60, 6.32                         # « La » attaque 2,68 … « histoire. » fin 6,25
def t_of_src(s): return PF / FPS + (s - T_LONG)
assert abs(t_of_src(6.25) - DROP) < 0.2 and t_of_src(6.25) < DROP
MUSIC_IN0 = MDROP - DROP
# ---------------- frappes réelles ----------------
def music_raw(mi, sr=48000):
    import soundfile as sf_
    x, r = sf_.read(SON_FILE, dtype="float32"); assert r == sr
    i0 = int(round(mi * sr)); return x[i0:i0 + int((END + 0.5) * sr)]
def detect_hits(y, sr=48000):
    """Kick (< 150 Hz, instant pris sur son clic 150-1500 Hz) et caisse (> 1,5 kHz) : attaque à 30 % de l'enveloppe (copie de genA8)."""
    import scipy.signal as ss, librosa
    m = y.mean(1); out = []
    def envel(typ, fc):
        return np.convolve(np.abs(ss.hilbert(ss.sosfiltfilt(ss.butter(4, fc, typ, fs=sr, output="sos"), m))), np.ones(96) / 96, "same")
    def attack(env, c):
        thr = 0.3 * env[c]; i = c
        while i > c - int(0.06 * sr) and i > 0 and env[i - 1] > thr: i -= 1
        return i
    clic = envel("bp", [150, 1500])
    for band, (typ, fc) in (("kick", ("lp", 150)), ("caisse", ("hp", 1500))):
        env = envel(typ, fc)
        hop = 128; e = env[::hop]; d = np.maximum(0, np.diff(e, prepend=e[0])); d /= d.max()
        for p in librosa.util.peak_pick(d, pre_max=20, post_max=20, pre_avg=40, post_avg=40, delta=0.12, wait=30):
            c0 = p * hop; lo, hi = max(0, c0 - int(0.01 * sr)), min(len(env), c0 + int(0.05 * sr))
            i = attack(env, lo + int(np.argmax(env[lo:hi])))
            lvl = float(env[min(len(env) - 1, i + int(0.03 * sr))])
            if band == "kick":
                lo, hi = max(0, i - int(0.06 * sr)), i + int(0.01 * sr); c = lo + int(np.argmax(clic[lo:hi]))
                if clic[c] > 2 * np.median(clic[max(0, lo - int(0.1 * sr)):lo]): i = attack(clic, c)
            out.append((round(i / sr, 4), band, round(float(d[p]), 2), round(lvl, 3)))
    return sorted(out)
# montage après le drop : (id, effet d'entrée, nb de temps) ; coupes sur les kicks pleins (temps 0 = drop)
EDIT = [("bras", "drop", 2), ("poing", "whip", 1), ("face", "whip", 1), ("foule", "cut", 1), ("qag", "whip", 1), ("leve", "whip", 1),
        ("aura", "cut", 1), ("doigt", "drop", 1), ("bras_b", "whip", 1), ("main", "whip", 1), ("lever", "cut", 2)]
CUT_K = [0]
for _, _, nb in EDIT: CUT_K.append(CUT_K[-1] + nb)                # temps des coupes (dernier = carton de fin)
HITS_JSON = OUT + "A9-frappes.json"
KLVL = 0.7                                       # kicks pleins (niveau d'enveloppe > 0,7)
def kick_attacks(y, grid, sr=48000):
    """Attaque réelle du kick près de chaque temps attendu : le 808 tenu masque les kicks pour peak_pick, donc on cherche
    la plus forte montée de l'enveloppe < 150 Hz (5 ms, fenêtre ±45 ms) puis l'instant où elle franchit la moitié entre le creux d'avant et le sommet."""
    import scipy.signal as ss
    m = y.mean(1)
    env = np.convolve(np.abs(ss.hilbert(ss.sosfiltfilt(ss.butter(4, 150, "lp", fs=sr, output="sos"), m))), np.ones(48) / 48, "same")
    out = []; q = int(0.005 * sr)
    for g in grid:
        a = max(q, int((g - 0.045) * sr)); b = min(len(env) - int(0.04 * sr), int((g + 0.045) * sr))
        seg = env[a:b]; dd = seg[q:] - seg[:-q]; i = a + int(np.argmax(dd)) + q // 2
        pk = i + int(np.argmax(env[i:i + int(0.03 * sr)])); lo_ = i - int(0.03 * sr) + int(np.argmin(env[i - int(0.03 * sr):i + 1]))
        thr = env[lo_] + 0.5 * (env[pk] - env[lo_]); j = pk
        while j > lo_ and env[j - 1] > thr: j -= 1
        out.append((round(j / sr, 4), round(float(env[pk]), 3), round(float(20 * np.log10(env[pk] / max(env[lo_], 1e-6))), 1)))
    return out
def frappes():
    """Décalage sous-image de l'extrait pour que les kicks coupés tombent au plus près des images ; frappes mesurées sur la musique posée."""
    if os.path.exists(HITS_JSON):
        js = json.load(open(HITS_JSON))
        if js.get("cle") == [MUSIC_IN0, END, CUT_K, "v3"]: return js["music_in"], js["kicks"], js["frappes"]
    y0 = music_raw(MUSIC_IN0); k0 = kick_attacks(y0, [DROP])[0][0]
    ks = [t for t, _, _ in kick_attacks(y0, [k0 + k * BEAT for k in CUT_K])]
    best = min(np.arange(-0.016, 0.0165, 0.001), key=lambda off: max(abs((t - off) - round((t - off) * FPS) / FPS) for t in ks))
    mi = MUSIC_IN0 + best; y = music_raw(mi)
    kk = kick_attacks(y, [t - best for t in ks]); h = detect_hits(y)
    json.dump({"cle": [MUSIC_IN0, END, CUT_K, "v3"], "music_in": mi, "kicks": kk, "frappes": h}, open(HITS_JSON, "w")); return mi, kk, h
MUSIC_IN, KK, HITS = frappes()
KICKS = [k[0] for k in KK]
assert all(k[1] > KLVL and k[2] > 3 for k in KK), KK
CUTS = KICKS
CUTF = [fr(c) for c in CUTS]
assert CUTF[0] == DROPF, (CUTF[0], DROPF)
PLAN_N = {sid: CUTF[i + 1] - CUTF[i] for i, (sid, _, _) in enumerate(EDIT)}
assert min(PLAN_N.values()) >= 15, ("plan < 1 temps", PLAN_N)
# ---------------- plans ----------------
# vh = hauteur de vue de départ (px source) ; track : la vue se resserre quand le visage rapetisse (caméra source qui recule) -> jamais de dézoom
SHOTS = {
    "long":   dict(src=MA, t=T_LONG, face=(870, 300), b=B_M, vh=790, zoom=(1.0, 1.03), top=0.10, track=True,
                   why="meeting Nouveau Paris populaire : « La jeune génération a commencé à écrire son histoire. » (son synchrone)"),
    "bras":   dict(src=MA, t=49.60, face=(990, 290), b=B_M, vh=790, zoom=(1.0, 1.05), top=0.12, track=True, dx=-0.18, why="bras tendu vers le ciel, index levé"),
    "poing":  dict(src=MB, t=24.25, face=(860, 330), b=B_M, vh=790, zoom=(1.0, 1.05), top=0.12, track=True, why="tête baissée, poing serré (hors cadre à gauche)"),
    "face":   dict(src=MB, t=9.60, face=(1120, 390), b=B_M, vh=790, zoom=(1.0, 1.05), top=0.12, track=True, why="de face, crie vers la salle"),
    "foule":  dict(src=MA, t=57.00, fixed=(1060, 560), b=B_FULL, vh=1040, zoom=(1.0, 1.05), why="salle rouge debout, drapeaux"),
    "qag":    dict(src=QAG, t=82.25, face=(930, 340), b=B_Q, vh=760, zoom=(1.0, 1.05), top=0.12, track=True,
                   why="QAG 06/10/2026, crie en pointant le ministre (« Vous pouvez le faire et vous le ferez », image seule)"),
    "leve":   dict(src=MA, t=22.40, face=(860, 290), b=B_M, vh=790, zoom=(1.0, 1.05), top=0.12, track=True, dx=0.18, why="bras levé, main ouverte"),
    "doigt":  dict(src=MA, t=26.40, face=(1100, 300), b=B_M, vh=790, zoom=(1.0, 1.05), top=0.12, track=True, dx=-0.18, why="index levé"),
    "bras_b": dict(src=MB, t=26.20, face=(1040, 330), b=B_M, vh=790, zoom=(1.0, 1.05), top=0.12, track=True, dx=-0.18, why="bras tendu vers la salle"),
    "main":   dict(src=MA, t=40.30, face=(1070, 300), b=B_M, vh=790, zoom=(1.0, 1.05), top=0.12, track=True, dx=-0.18, why="main levée, regard vers la salle"),
    "lever":  dict(src=MA, t=55.20, face=(990, 300), b=B_M, vh=790, zoom=(1.0, 1.04), top=0.12, track=True, dx=-0.18, speed=60, why="profil, regard vers la salle, poing levé hors cadre (ralenti de fin)"),
}
# ---------------- look N&B (genA8) ----------------
RNG = np.random.default_rng(11)
def grade(bgr, white=0.87):
    g = (0.114 * bgr[..., 0] + 0.587 * bgr[..., 1] + 0.299 * bgr[..., 2])
    g = np.clip((g - 0.02) / 0.96, 0, 1)
    g = g ** 0.82
    g = 0.78 * g + 0.22 * (g * g * (3 - 2 * g))
    g = g / (1 + 0.18 * g) * 1.18
    small = cv2.resize(g, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    hi = np.clip(small - 0.70, 0, None) * 1.5
    glow = cv2.resize(cv2.GaussianBlur(hi, (0, 0), 9), (W, H)) * 0.25
    soft = cv2.resize(cv2.GaussianBlur(small, (0, 0), 4), (W, H))
    g = 1 - (1 - g) * (1 - 0.10 * soft) + glow
    g = vignette(g[..., None], 0.30, 2.4)[..., 0]
    g = 0.035 + np.clip(g, 0, 1) * (white - 0.035)
    g = g + RNG.normal(0, 0.016, g.shape).astype(np.float32)
    return np.repeat(np.clip(g, 0, 1)[..., None], 3, 2)
# ---------------- lecture source ----------------
def read_frames(src, t, n_out, speed=1.0):
    need = [int(round(i * speed * SFPS / FPS)) for i in range(n_out)]; n_src = need[-1] + 1
    p = subprocess.run([FF, "-v", "error", "-ss", "%.4f" % t, "-i", LOT + "/sources/" + src, "-frames:v", str(n_src),
                        "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True)
    a = np.frombuffer(p.stdout, np.uint8).reshape(-1, 1080, 1920, 3)
    return [a[min(i, len(a) - 1)].astype(np.float32) / 255 for i in need], int(round(t * SFPS))
def crop_916(img, cx, cy, vh):
    vw = vh * 9 / 16; s = W / vw
    M = np.float32([[s, 0, W / 2 - cx * s], [0, s, H / 2 - cy * s]])
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
def face_heights(src, s0, n, hint, b, speed):
    """hauteur du visage suivi (px source) par image du plan, lissée (fenêtre 15) ; None si pas de visage."""
    n_src = int(n * speed * SFPS / FPS) + 2
    heads = framing.pick(framing.detect(src, s0, n_src, SFPS), hint, b)
    if not heads: return None
    hs = np.array([f[3] for f in heads], np.float32)
    k = 15; pad = np.pad(hs, (k // 2, k // 2), mode="edge"); hs = np.convolve(pad, np.ones(k) / k, "valid")
    return [float(hs[min(int(f * speed * SFPS / FPS), len(hs) - 1)]) for f in range(n)]
# ---------------- texte (Arial Black, contour noir + ombre douce, mot-clé rouge, jamais de guillemets) ----------------
def font(size): return ImageFont.truetype(F_BLACK, max(8, int(size)))
def fit_size(txt, maxw, start=260):
    s = start
    while font(s).getlength(txt) > maxw: s -= 4
    return s
# mots réels (Whisper turbo + attaques mesurées 200-3000 Hz, source MA) : La 2,68 / jeune 2,95 / génération 3,25 / a 4,42 / commencé 4,62 /
# à 5,00 / écrire 5,10 / son 5,45 / histoire 5,70-6,25
CARDS = [
    [(124, 1170, [("LA", 2.68, WHITE), ("JEUNE", 2.95, WHITE)]),
     (None, None, [("GÉNÉRATION", 3.25, WHITE)])],
    [(124, 1170, [("A", 4.42, WHITE), ("COMMENCÉ", 4.62, WHITE)]),
     (None, None, [("À", 5.00, WHITE), ("ÉCRIRE", 5.10, WHITE)])],
    [(124, 1170, [("SON", 5.45, WHITE)]),
     (None, None, [("HISTOIRE", 5.70, RED)])],
]
# zone sûre TikTok (Luca, 26/10) : bloc texte x 0,17-0,83 (<= 66 % de 1080, entrée à 112 % comprise -> 630 px), y 0,12-0,75 (bas du bloc <= 1440 px)
TXT_W = 630
def layout(card):
    out = []; y_prev = None; s_prev = None
    for size, yc, words in card:
        txt = " ".join(w for w, _, _ in words)
        if size is None: size = min(fit_size(txt, TXT_W, start=s_prev), s_prev); yc = y_prev + s_prev * 0.5 + 34 + size * 0.5
        else: size = fit_size(txt, TXT_W, start=size)
        f = font(size); total = f.getlength(txt); x = (W - total) / 2
        for w, t, col in words:
            out.append(dict(w=w, t=t, col=col, size=size, x=x, yc=yc)); x += f.getlength(w + " ")
        y_prev, s_prev = yc, size
    return out
def full_sizes(card): return [(it["size"], it["yc"]) for it in layout(card)]
def draw_words(items, scale_last=1.0, alpha_last=1.0):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay); ds = ImageDraw.Draw(sh)
    for k, it in enumerate(items):
        last = k == len(items) - 1; sc = scale_last if last else 1.0
        f = font(it["size"] * sc); sw = max(4, int(it["size"] * 0.045))
        wfull = font(it["size"]).getlength(it["w"]); wnow = f.getlength(it["w"])
        x = it["x"] + (wfull - wnow) / 2
        x0, y0, x1, y1 = d.textbbox((0, 0), it["w"], font=f); y = it["yc"] - (y1 - y0) / 2 - y0
        a = int(255 * (alpha_last if last else 1.0))
        ds.text((x, y + it["size"] * 0.05), it["w"], font=f, fill=(0, 0, 0, int(a * 0.78)), stroke_width=sw * 3, stroke_fill=(0, 0, 0, int(a * 0.78)))
        d.text((x, y), it["w"], font=f, fill=it["col"] + (a,), stroke_width=sw, stroke_fill=(0, 0, 0, a))
    sh = sh.filter(ImageFilter.GaussianBlur(18))
    return np.asarray(Image.alpha_composite(sh, lay)).astype(np.float32) / 255
def long_text(t_src):
    ci = max([i for i, c in enumerate(CARDS) if t_src >= c[0][2][0][1]], default=0)
    card = CARDS[ci]; fixed = full_sizes(card); k = 0; vis = []
    for size, yc, words in card:
        ws = []
        for w in words:
            if t_src >= w[1]: ws.append((w, fixed[k]))
            k += 1
        if ws: vis.append(ws)
    if not vis: return None
    items = []
    for ws in vis:                                               # ligne recentrée sur ses mots visibles, taille fixe
        size, yc = ws[0][1]; f = font(size); txt = " ".join(w[0] for w, _ in ws); x = (W - f.getlength(txt)) / 2
        for (w, t, col), _ in ws:
            items.append(dict(w=w, t=t, col=col, size=size, x=x, yc=yc)); x += f.getlength(w + " ")
    last = max(items, key=lambda it: it["t"]); items.remove(last); items.append(last)
    kf = (t_src - last["t"]) * FPS; e = ease_out(min(kf / 3.0, 1.0))      # entrée 3 images, sans rebond
    return draw_words(items, scale_last=1.12 - 0.12 * e, alpha_last=min(1.0, 0.35 + e))
def over_rgba(img_bgr, rgba):
    a = rgba[..., 3:4]; rgb = rgba[..., 2::-1]
    return img_bgr * (1 - a) + rgb * a
# ---------------- rendu ----------------
def write_mov(frames, path, fps=FPS):
    p = subprocess.Popen([FF, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", "%dx%d" % (W, H), "-r", str(fps), "-i", "-",
                          "-c:v", "prores_ks", "-profile:v", "3", "-pix_fmt", "yuv422p10le", "-vendor", "apl0", path], stdin=subprocess.PIPE)
    for f in frames: p.stdin.write(to8(f).tobytes())
    p.stdin.close(); p.wait()
def slots():
    out = [("long", "cut", PF, DROPF)]
    for i, (sid, eff, nb) in enumerate(EDIT): out.append((sid, eff, CUTF[i], CUTF[i + 1]))
    return out
def clip_name(sid, eff): return "A9_%s.mov" % sid if eff == "cut" else "A9_%s_%s.mov" % (sid, eff)
def render_slot(sid, eff, a, b, preview_speed=True):
    """Clip livré à vitesse normale (n images timeline = n × 25/30 images source) ; le ralenti (speed_pct) est fait dans Resolve / setpts dans l'aperçu."""
    sh = SHOTS[sid]; n = b - a
    raw, s0 = read_frames(sh["src"], sh["t"], n)
    m = math.ceil(n * sh.get("speed", 100) / 100)               # poussée lente avant terminée sur la frappe de sortie (ralenti compris)
    z0, z1 = sh["zoom"]; push = lambda f: z0 + (z1 - z0) * min(f / max(m - 1, 1), 1.0)
    zoom = push
    if sh.get("track"):
        hs = face_heights(sh["src"], s0, n, sh["face"], sh["b"], 1.0)
        if hs:
            h0 = hs[0]; zoom = lambda f: push(f) * max(1.0, h0 / hs[f])
    if "fixed" in sh:
        views, _ = plan_views(sh["src"], s0, n, SFPS, speed=SFPS / FPS, bounds=sh["b"], vh=sh["vh"], zoom=zoom, fixed=sh["fixed"])
    else:
        dx = sh.get("dx", 0)                                     # tête décalée vers le bord opposé au geste (main / poing levé) : plus de geste dans le cadre
        views, ok = plan_views(sh["src"], s0, n, SFPS, speed=SFPS / FPS, hint=sh["face"], bounds=sh["b"], vh=sh["vh"], zoom=zoom, top=sh["top"],
                               shake=(lambda f: (dx, 0)) if dx else None)
        if not ok: print("  ! pas de visage :", sid)
    frames = []
    for i, (img, (cx, cy, vh)) in enumerate(zip(raw, views)):
        g = grade(crop_916(img, cx, cy, vh), sh.get("white", 0.87))
        if sid == "long":
            tl = long_text(sh["t"] + i / FPS)
            if tl is not None: g = over_rgba(g, tl)
        if eff == "whip" and i < 3: g = motion_blur(g, 0, [220, 90, 25][i], steps=16)
        if eff == "drop" and i < 8:
            k = (1 - i / 8) ** 2; g = np.clip(g + k * 0.55 + gblur(g, 25) * k * 0.6, 0, 1)
        frames.append(g)
    write_mov(frames, OUT + clip_name(sid, eff))
    vx = views[0]; vz = views[-1]
    print("  %-7s %3d im  vue %d,%d h%d -> h%d  (x %d-%d, y %d-%d)" % (sid, n, vx[0], vx[1], vx[2], vz[2], vx[0] - vx[2] * 9 / 32, vx[0] + vx[2] * 9 / 32,
                                                                vx[1] - vx[2] / 2, vx[1] + vx[2] / 2))
def aura_card(n, fade_in=3, fade_out=0):
    im = Image.new("L", (W, H), 0); d = ImageDraw.Draw(im); f = ImageFont.truetype(F_AURA[0], 120, index=F_AURA[1])
    tw = d.textlength("aura.", font=f); d.text(((W - tw) / 2, H / 2 - 80), "aura.", font=f, fill=255)
    a = np.asarray(im).astype(np.float32) / 255
    base = np.clip(a * 0.92 + gblur(a, 22) * 0.9 + gblur(a, 6) * 0.5, 0, 0.95); out = []
    for i in range(n):
        k = 1.0
        if fade_in and i < fade_in: k = ease_out((i + 1) / fade_in)
        if fade_out and i >= n - fade_out: k = (n - i) / fade_out
        out.append(np.repeat((0.008 + base * k)[..., None], 3, 2))
    return out
def make_cards():
    write_mov(aura_card(PF), OUT + "A9_aura_intro.mov")
    write_mov(aura_card(PLAN_N["aura"]), OUT + "A9_aura.mov")
    write_mov(aura_card(fr(END) - CUTF[-1], fade_in=3, fade_out=12), OUT + "A9_aura_fin.mov")
# ---------------- plan ----------------
URLS = {MA: ("https://www.youtube.com/watch?v=cNkMqVnlUl0", 140.0, "Louis Boyard (meeting Nouveau Paris populaire)", "2026-01-31"),
        MB: ("https://www.youtube.com/watch?v=cNkMqVnlUl0", 252.0, "Louis Boyard (meeting Nouveau Paris populaire)", "2026-01-31"),
        QAG: ("https://www.youtube.com/watch?v=QbYEjxSoyww", 0.0, "La France insoumise à l'Assemblée nationale", "2026-10-06")}
def build_plan():
    video = []
    def add(id_, clip, n, rec, kind, extra=None):
        v = {"id": id_, "clip": clip, "folder": "genA9", "s": 0, "e": n, "rec": rec, "dur": n, "clip_fps": FPS, "track": 1, "kind": kind}
        if extra: v.update(extra)
        video.append(v)
    add("hook", "A9_aura_intro.mov", PF, 0, "card")
    for sid, eff, a, b in slots():
        if sid == "aura": add("aura_%d" % a, "A9_aura.mov", b - a, a, "card"); continue
        sh = SHOTS[sid]; u = URLS[sh["src"]]
        extra = {"source": "%s @ %.2f s (= lot4/sources/%s)" % (REAL[sh["src"]], sh["t"], sh["src"]), "source_fps": SFPS,
                 "url": u[0], "temps_url_s": round(u[1] + sh["t"], 2), "chaine": u[2], "date": u[3], "effet": eff, "pourquoi": sh["why"]}
        if sid != "long": extra["temps"] = round((b - a) / FPS / BEAT, 2)
        if sid == "long": extra["texte"] = "LA JEUNE / GÉNÉRATION · A COMMENCÉ / À ÉCRIRE · SON / HISTOIRE (rouge), mot à mot, Arial Black"
        extra["speed_pct"] = sh.get("speed", 100)
        if sh.get("speed"): extra["retime"] = "optical_flow"
        add("%s_%d" % (sid, a), clip_name(sid, eff), b - a, a, "shot", extra)
    add("fin", "A9_aura_fin.mov", fr(END) - CUTF[-1], CUTF[-1], "card")
    plan = {"name": "A9 - Aura N&B - Louis Boyard", "fps": FPS, "w": W, "h": H, "duree_s": END,
            "note": "Plans 9:16 recadrés + étalonnés N&B (lot4/_claude/gen/A9/out), vitesse normale. s/e en images du clip (30 i/s), rec en images timeline. "
                    "speed_pct < 100 : ralenti Resolve Optical Flow + Speed Warp (aperçu = setpts simple ; e - s = durée timeline à vitesse normale). "
                    "Coupes sur les kicks réels de METAMORPHOSIS mesurés dans la musique posée (out/A9-frappes.json), drop = 1er kick + 808 après le break "
                    "(54,89 s du complet = %.3f s timeline, image %d), 1 temps = 0,686 s (kicks pleins, 87,5 BPM demi-temps)." % (CUTS[0], DROPF),
            "phrase": {"texte": "La jeune génération a commencé à écrire son histoire.",
                       "source": "%s 2,68-6,25 s (YouTube cNkMqVnlUl0 @ 142,68-146,25 s, chaîne Louis Boyard, meeting Nouveau Paris populaire du 31/01/2026)" % REAL[MA],
                       "timeline_s": [round(t_of_src(2.68), 2), round(t_of_src(6.25), 2)]},
            "video": video,
            "audio": [{"id": "mix", "clip": "A9-mix.wav", "folder": "genA9", "rec": 0, "track": 1,
                       "note": "mix -14 LUFS : musique de 0 à la fin (complet lu en continu dès %.3f s), voix synchrone %.2f-%.2f s, musique -4 dB sous la voix (break déjà calme)" % (MUSIC_IN, t_of_src(V_IN), t_of_src(V_OUT))}],
            "stems": ["lot4/_claude/gen/A9/out/A9-voix.wav", "lot4/_claude/gen/A9/out/A9-musique.wav"],
            "musique": {"fichier": "lot4/sons/A9-interworld-metamorphosis_complet.wav", "titre": "INTERWORLD - METAMORPHOSIS (%s)" % SON_URL,
                        "debut_complet_s": round(MUSIC_IN, 4), "fin_complet_s": round(MUSIC_IN + END, 3), "gain_db": MGAIN,
                        "kicks_timeline_s": KICKS, "coupes_kicks_s": CUTS, "coupes_images": CUTF},
            "logos_exclus": "meetings : logo LFI haut droite et pupitre NOUVEAU PARIS POPULAIRE hors fenêtre ; QAG : logo LFI, timer AN et sous-titres incrustés hors fenêtre"}
    json.dump(plan, open(D + "plan-A9.json", "w"), indent=1, ensure_ascii=False)
    return plan
# ---------------- audio ----------------
MGAIN = 0.0
def lufs(path):
    r = subprocess.run([FF, "-hide_banner", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    import re
    return float(re.findall(r"I:\s+(-?[0-9.]+) LUFS", r)[-1])
def make_audio():
    import soundfile as sf
    sr = 48000; N = int(round(END * sr))
    def grab(path, t, dur):
        p = subprocess.run([FF, "-v", "error", "-ss", "%.3f" % t, "-t", "%.3f" % dur, "-i", path, "-ac", "2", "-ar", str(sr), "-f", "f32le", "-"], capture_output=True)
        return np.frombuffer(p.stdout, np.float32).reshape(-1, 2).copy()
    def place(buf, x, t, gain_db=0, fin=0.0, fout=0.0):
        g = 10 ** (gain_db / 20); n = len(x); env = np.ones(n, np.float32)
        if fin: m = int(fin * sr); env[:m] = np.linspace(0, 1, m)
        if fout: m = int(fout * sr); env[-m:] *= np.linspace(1, 0, m)
        a = int(round(t * sr)); b = min(N, a + n); buf[a:b] += x[:b - a] * env[:b - a, None] * g
    vx = grab(LOT + "/sources/" + MA, V_IN, V_OUT - V_IN)
    m = music_raw(MUSIC_IN, sr)[:N]
    # niveaux : voix calée 1 dB sous le drop (drop mesuré sur 4 s après le 1er kick)
    sf.write(D + "tmp_v.wav", vx, sr, subtype="FLOAT"); i0 = int(DROP * sr); sf.write(D + "tmp_d.wav", m[i0:i0 + 4 * sr], sr, subtype="FLOAT")
    vg = (lufs(D + "tmp_d.wav") + MGAIN - 1.0) - lufs(D + "tmp_v.wav"); os.remove(D + "tmp_v.wav"); os.remove(D + "tmp_d.wav")
    voix = np.zeros((N, 2), np.float32); mus = np.zeros((N, 2), np.float32)
    place(voix, vx, t_of_src(V_IN), vg, fin=0.04, fout=0.06)
    duck = np.ones(len(m), np.float32); g = 10 ** (-4 / 20)
    a0, a1, b0, b1 = [int(t * sr) for t in (t_of_src(V_IN) - 0.12, t_of_src(V_IN) + 0.02, t_of_src(V_OUT) - 0.06, DROP - 0.01)]
    duck[a0:a1] = np.linspace(1, g, a1 - a0); duck[a1:b0] = g; duck[b0:b1] = np.linspace(g, 1, b1 - b0)
    place(mus, m * duck[:, None], 0.0, MGAIN, fin=0.02, fout=0.6)
    sf.write(OUT + "A9-voix.wav", voix, sr, subtype="PCM_24"); sf.write(OUT + "A9-musique.wav", mus, sr, subtype="PCM_24")
    sf.write(D + "tmp_mix.wav", voix + mus, sr, subtype="FLOAT")
    r = subprocess.run([FF, "-hide_banner", "-i", D + "tmp_mix.wav", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    js = json.loads(r[r.rindex("{"):r.rindex("}") + 1])
    af = ("loudnorm=I=-14:TP=-1.5:LRA=11:measured_I=%s:measured_TP=%s:measured_LRA=%s:measured_thresh=%s:offset=%s:linear=true,"
          "alimiter=limit=0.85:level=false:attack=1:release=60,aresample=48000" % (js["input_i"], js["input_tp"], js["input_lra"], js["input_thresh"], js["target_offset"]))
    subprocess.run([FF, "-v", "error", "-y", "-i", D + "tmp_mix.wav", "-af", af, "-c:a", "pcm_s24le", OUT + "A9-mix.wav"], check=True)
    os.remove(D + "tmp_mix.wav"); print("audio : gain voix %+.1f dB, mix avant normalisation %s LUFS" % (vg, js["input_i"]))
# ---------------- aperçu 540x960 ----------------
def apercu():
    plan = json.load(open(D + "plan-A9.json")); ins = []; fl = []
    for i, v in enumerate(plan["video"]):
        n = v["e"] - v["s"]; sp = v.get("speed_pct", 100) / 100
        ins += ["-i", OUT + v["clip"]]
        if sp < 1:
            fl.append("[%d:v]trim=start_frame=%d:end_frame=%d,setpts=(PTS-STARTPTS)/%.4f,fps=30,trim=end_frame=%d,setpts=PTS-STARTPTS,scale=540:960,setsar=1[v%d]"
                      % (i, v["s"], v["s"] + math.ceil(n * sp) + 1, sp, n, i))
        else:
            fl.append("[%d:v]trim=start_frame=%d:end_frame=%d,setpts=PTS-STARTPTS,scale=540:960,setsar=1[v%d]" % (i, v["s"], v["e"], i))
    k = len(plan["video"])
    fl.append("".join("[v%d]" % i for i in range(k)) + "concat=n=%d:v=1:a=0[v]" % k)
    ins += ["-i", OUT + "A9-mix.wav"]
    out = ROOT + "/preview/apercu-A9.mp4"
    subprocess.run([FF, "-v", "error", "-y"] + ins + ["-filter_complex", ";".join(fl), "-map", "[v]", "-map", "%d:a" % k,
                    "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "aac", "-b:a", "192k", "-shortest", out], check=True)
    print("aperçu", out)
if __name__ == "__main__":
    args = set(a for a in sys.argv[1:] if not a.startswith("only=")) or {"shots", "cards", "audio", "plan", "apercu"}
    only = [x for a in sys.argv[1:] if a.startswith("only=") for x in a.split("=", 1)[1].split(",")]
    print("musique dès %.4f s du complet ; coupes (s) :" % MUSIC_IN, CUTS, "images :", CUTF)
    if "shots" in args or only:
        for sid, eff, a, b in slots():
            if sid != "aura" and (not only or sid in only): render_slot(sid, eff, a, b)
    if "cards" in args: make_cards()
    if "plan" in args: build_plan()
    if "audio" in args: make_audio()
    if "apercu" in args: apercu()
