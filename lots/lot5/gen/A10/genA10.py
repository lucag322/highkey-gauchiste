# A10 (lot 5) — Aura N&B, Mathilde Panot (présidente du groupe LFI à l'Assemblée), son « FE!N » (Travis Scott ft. Playboi Carti, chaîne officielle Travis Scott).
# Modèle : lot4/_claude/gen/A9/genA9.py (frappes réelles, N&B adouci, texte mot à mot recentré) + lot3 A6/A8. Aperçu HORS Resolve (ffmpeg/numpy).
# Phrase : « Ils ne viendront pas à bout de nous. » (meeting de Rochefort, 22/10/2026, chaîne Mathilde Panot, youtube 4l2dx1n-UFo @ 1577,0-1578,6 s
#          = lot2/sources/A1-panot-rochefort-a.mp4 31,99-33,53 s). Autre phrase et autres plans que A1 (« Désormais, plus rien ne passera. »).
# Son : extrait continu du morceau, fin de la montée avant le hook (voix de Panot par-dessus, musique baissée), drop = 1re frappe 808 du hook « FE!N » (29,81 s du complet).
# Règles : 9:16 plein écran, aucun visage coupé, aucun logo (filigrane MELENCHON2027.fr haut droite, pupitre ROCHEFORT, bandeau nom, logo LCP hors fenêtre),
# coupes sur les 808 réels (147,7 BPM, motif 3-3-2 : coupes à 0,81 ou 1,22 s), plans >= 2 temps, poussée lente avant seulement, <= 15 s,
# ralentis = speed_pct (Resolve Optical Flow).
# Usage : python genA10.py [shots] [cards] [audio] [plan] [apercu] [only=ID,ID]   (sans argument = tout)
import sys, os, json, subprocess, math, functools
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
ROOT = "/Users/luca.grousset/Movies/highkey-gauchiste"; LOT = ROOT + "/lot5"
sys.path.insert(0, ROOT + "/_claude/outils")
import framing
from framing import plan_views
from fx import gblur, motion_blur, vignette, to8, ease_out
D = LOT + "/_claude/gen/A10/"; OUT = D + "out/"; os.makedirs(OUT, exist_ok=True)
framing.ROOT = LOT; framing.CACHE = D + "cache"          # lot5/sources/A10-* = liens vers les sources du lot 2 (rien de copié ni modifié)
framing.head_box = lambda f: (f[0] - 0.12 * f[2], f[1] - 0.5 * f[3], f[0] + 1.12 * f[2], f[1] + 1.2 * f[3])
framing.view_for = functools.partial(framing.view_for, margin=0.04)
FF = "/opt/homebrew/bin/ffmpeg"; FPS = 30; W, H = 1080, 1920
RED = (0xE4, 0x00, 0x2B); WHITE = (255, 255, 255)
F_BLACK = "/System/Library/Fonts/Supplemental/Arial Black.ttf"
F_AURA = ("/System/Library/Fonts/Helvetica.ttc", 2)
RA, RB, RC = "A10-panot-rochefort-a.mp4", "A10-panot-rochefort-b.mp4", "A10-panot-rochefort-c.mp4"
QAG = "A10-panot-lcp-qag-2025-12.mp4"
REAL = {RA: "lot2/sources/A1-panot-rochefort-a.mp4", RB: "lot2/sources/A1-panot-rochefort-b.mp4", RC: "lot2/sources/A1-panot-rochefort-c.mp4",
        QAG: "lot2/sources/A1-panot-lcp-qag-2025-12.mp4"}
SFPS_OF = {RA: 30, RB: 30, RC: 30, QAG: 25}
# zones utilisables (px source 1920x1080) :
#  Rochefort : filigrane MELENCHON2027.fr haut droite (x > 1560), pupitre ROCHEFORT (y > 800 en plan tribune), bandeau nom bas gauche (b 59-68 s)
#  QAG LCP   : logo LCP haut gauche (x < 300)
B_R = (0, 0, 1560, 800); B_Q = (300, 0, 1920, 1080); B_FULL = (0, 0, 1560, 1080)
# ---------------- musique ----------------
SON_FILE = LOT + "/sons/A10-travisscott-fein_complet.wav"
SON_URL = "https://www.youtube.com/watch?v=B9synWjqBn8"
MDROP = 29.815                                   # drop : 1re frappe 808 du hook « FE!N » (complet), mesurée (+12 dB d'un coup)
def fr(t): return int(round(t * FPS))
DROPF = 94; DROP = DROPF / FPS                   # 3,133 s
END = 14.97                                      # règle : aura N&B 15 s max
BEAT = 0.40625                                   # 147,7 BPM (autocorrélation du hook 29,3-42,8 s)
# ---------------- phrase (Whisper + attaques mesurées 200-3000 Hz dans la source RA) ----------------
T_LONG = 31.734                                  # 1re image après la coupe source foule -> Panot (31,700 s)
PF = 36                                          # hook « aura. » 1,2 s
V_IN, V_OUT = 31.90, 33.62                       # « Ils » attaque 31,99 … « nous. » fin 33,53 (« Oui, » 31,2-31,7 laissé dehors, sur le plan foule)
def t_of_src(s): return PF / FPS + (s - T_LONG)
assert t_of_src(33.53) < DROP and DROP - t_of_src(33.53) < 0.3
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
# montage après le drop : (id, effet d'entrée, nb de temps) ; coupes sur les 808 forts du hook (motif 3-3-2 par mesure : temps 0, 3, 5, 6 | 8, 11, 13, 14 …)
EDIT = [("doigt", "drop", 3), ("pointe", "whip", 2), ("salle", "cut", 3), ("rire", "whip", 3), ("index", "whip", 2), ("salut", "whip", 3),
        ("hemi", "whip", 3), ("aura", "cut", 2), ("fin", "cut", 6)]
CUT_K = [0]
for _, _, nb in EDIT: CUT_K.append(CUT_K[-1] + nb)                # temps des coupes (dernier = carton de fin)
HITS_JSON = OUT + "A10-frappes.json"
KLVL = 0.7                                       # 808 forts (niveau d'enveloppe > 0,7 ; les 808 faibles du motif sont à 0,05-0,6)
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
assert min(PLAN_N.values()) >= 24, ("plan < 2 temps (0,81 s)", PLAN_N)
# ---------------- plans ----------------
# vh = hauteur de vue de départ (px source) ; track : la vue se resserre quand le visage rapetisse (caméra source qui recule) -> jamais de dézoom
SHOTS = {
    "long":   dict(src=RA, t=T_LONG, face=(1000, 230), b=B_R, vh=780, zoom=(1.0, 1.04), top=0.12, track=True,
                   why="meeting de Rochefort : « Ils ne viendront pas à bout de nous. » (son synchrone)"),
    "doigt":  dict(src=RA, t=0.00, face=(1000, 200), b=B_R, vh=780, zoom=(1.0, 1.05), top=0.12, track=True, dx=-0.16, speed=60,
                   why="index levé vers le ciel (Rochefort, début de l'extrait a), ralenti sur le drop"),
    "pointe": dict(src=QAG, t=34.00, face=(720, 220), b=B_Q, vh=760, zoom=(1.0, 1.05), top=0.12, track=True, dx=0.16,
                   why="hémicycle, QAG 04/12/2025 : pointe le banc du gouvernement (image seule)"),
    "salle":  dict(src=RA, t=29.20, fixed=(640, 560), b=B_FULL, vh=1040, zoom=(1.0, 1.05), why="salle comble vue du fond, drapeaux (Rochefort)"),
    "rire":   dict(src=RB, t=15.45, face=(880, 190), b=B_R, vh=780, zoom=(1.0, 1.05), top=0.12, track=True, why="éclat de rire, mains qui dessinent (Rochefort)"),
    "index":  dict(src=RB, t=103.85, face=(900, 190), b=B_R, vh=780, zoom=(1.0, 1.05), top=0.12, track=True, dx=-0.16, why="index levé, voix forte (Rochefort)"),
    "salut":  dict(src=RB, t=44.20, face=(860, 200), b=B_R, vh=780, zoom=(1.0, 1.05), top=0.12, track=True, dx=0.16, why="main levée vers la salle (Rochefort)"),
    "hemi":   dict(src=QAG, t=5.80, face=(850, 170), b=B_Q, vh=1080, zoom=(1.0, 1.05), top=0.12, track=True, dx=-0.16,
                   why="hémicycle, QAG 04/12/2025 : index levé (image seule)"),
    "fin":    dict(src=RB, t=85.60, face=(850, 170), b=B_R, vh=780, zoom=(1.0, 1.05), top=0.12, track=True, dx=-0.16, speed=40,
                   why="contre-plongée, index levé (Rochefort), ralenti de fin"),
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
    SFPS = SFPS_OF[src]
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
    SFPS = SFPS_OF[src]; n_src = int(n * speed * SFPS / FPS) + 2
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
# mots réels (Whisper turbo + attaques mesurées 200-3000 Hz, source RA) : Ils 31,99 / ne 32,10 / viendront 32,24 / pas 32,81 / à 32,93 /
# bout 33,09 / de 33,23 / nous 33,32-33,53
CARDS = [
    [(124, 1170, [("ILS", 31.99, WHITE), ("NE", 32.10, WHITE)]),
     (None, None, [("VIENDRONT", 32.24, WHITE)])],
    [(124, 1170, [("PAS", 32.81, WHITE), ("À", 32.93, WHITE), ("BOUT", 33.09, WHITE)]),
     (None, None, [("DE", 33.23, WHITE), ("NOUS", 33.32, RED)])],
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
def clip_name(sid, eff): return "A10_%s.mov" % sid if eff == "cut" else "A10_%s_%s.mov" % (sid, eff)
def render_slot(sid, eff, a, b, preview_speed=True):
    """Clip livré à vitesse normale (n images timeline = n × 25/30 images source) ; le ralenti (speed_pct) est fait dans Resolve / setpts dans l'aperçu."""
    sh = SHOTS[sid]; n = b - a; SFPS = SFPS_OF[sh["src"]]
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
    write_mov(aura_card(PF), OUT + "A10_aura_intro.mov")
    write_mov(aura_card(PLAN_N["aura"]), OUT + "A10_aura.mov")
    write_mov(aura_card(fr(END) - CUTF[-1], fade_in=3, fade_out=12), OUT + "A10_aura_fin.mov")
# ---------------- plan ----------------
URLS = {RA: ("https://www.youtube.com/watch?v=4l2dx1n-UFo", 1545.0, "Mathilde Panot (meeting de Rochefort)", "2026-10-22"),
        RB: ("https://www.youtube.com/watch?v=4l2dx1n-UFo", 20.0, "Mathilde Panot (meeting de Rochefort)", "2026-10-22"),
        RC: ("https://www.youtube.com/watch?v=4l2dx1n-UFo", 1980.0, "Mathilde Panot (meeting de Rochefort)", "2026-10-22"),
        QAG: ("https://www.youtube.com/watch?v=mqeo_ILV2_w", 0.0, "LCP - Assemblée nationale (QAG)", "2025-12-04")}
def build_plan():
    video = []
    def add(id_, clip, n, rec, kind, extra=None):
        v = {"id": id_, "clip": clip, "folder": "genA10", "s": 0, "e": n, "rec": rec, "dur": n, "clip_fps": FPS, "track": 1, "kind": kind}
        if extra: v.update(extra)
        video.append(v)
    add("hook", "A10_aura_intro.mov", PF, 0, "card")
    for sid, eff, a, b in slots():
        if sid == "aura": add("aura_%d" % a, "A10_aura.mov", b - a, a, "card"); continue
        sh = SHOTS[sid]; u = URLS[sh["src"]]
        extra = {"source": "%s @ %.2f s (= lot5/sources/%s)" % (REAL[sh["src"]], sh["t"], sh["src"]), "source_fps": SFPS_OF[sh["src"]],
                 "url": u[0], "temps_url_s": round(u[1] + sh["t"], 2), "chaine": u[2], "date": u[3], "effet": eff, "pourquoi": sh["why"]}
        if sid != "long": extra["temps"] = round((b - a) / FPS / BEAT, 2)
        if sid == "long": extra["texte"] = "ILS NE / VIENDRONT · PAS À BOUT / DE NOUS (NOUS rouge), mot à mot, Arial Black"
        extra["speed_pct"] = sh.get("speed", 100)
        if sh.get("speed"): extra["retime"] = "optical_flow"
        add("%s_%d" % (sid, a), clip_name(sid, eff), b - a, a, "shot", extra)
    add("fin", "A10_aura_fin.mov", fr(END) - CUTF[-1], CUTF[-1], "card")
    plan = {"name": "A10 - Aura N&B - Mathilde Panot", "fps": FPS, "w": W, "h": H, "duree_s": END,
            "note": "Plans 9:16 recadrés + étalonnés N&B (lot5/_claude/gen/A10/out), vitesse normale. s/e en images du clip (30 i/s), rec en images timeline. "
                    "speed_pct < 100 : ralenti Resolve Optical Flow + Speed Warp (aperçu = setpts simple ; e - s = durée timeline à vitesse normale). "
                    "Coupes sur les 808 réels de FE!N mesurés dans la musique posée (out/A10-frappes.json), drop = 1re frappe 808 du hook "
                    "(29,81 s du complet = %.3f s timeline, image %d), 1 temps = 0,406 s (147,7 BPM), plans de 2, 3 ou 6 temps (0,81 / 1,22 / 2,44 s)." % (CUTS[0], DROPF),
            "phrase": {"texte": "Ils ne viendront pas à bout de nous.",
                       "source": "%s 31,99-33,53 s (YouTube 4l2dx1n-UFo @ 1577,0-1578,6 s, chaîne Mathilde Panot, meeting de Rochefort du 22/10/2026)" % REAL[RA],
                       "timeline_s": [round(t_of_src(31.99), 2), round(t_of_src(33.53), 2)]},
            "video": video,
            "audio": [{"id": "mix", "clip": "A10-mix.wav", "folder": "genA10", "rec": 0, "track": 1,
                       "note": "mix -14 LUFS : musique de 0 à la fin (complet lu en continu dès %.3f s), voix synchrone %.2f-%.2f s, musique -8 dB sous la voix (montée avant le hook)" % (MUSIC_IN, t_of_src(V_IN), t_of_src(V_OUT))}],
            "stems": ["lot5/_claude/gen/A10/out/A10-voix.wav", "lot5/_claude/gen/A10/out/A10-musique.wav"],
            "musique": {"fichier": "lot5/sons/A10-travisscott-fein_complet.wav", "titre": "Travis Scott - FE!N ft. Playboi Carti (%s)" % SON_URL,
                        "debut_complet_s": round(MUSIC_IN, 4), "fin_complet_s": round(MUSIC_IN + END, 3), "gain_db": MGAIN,
                        "kicks_timeline_s": KICKS, "coupes_kicks_s": CUTS, "coupes_images": CUTF},
            "logos_exclus": "Rochefort : filigrane MELENCHON2027.fr (haut droite), pupitre ROCHEFORT et bandeau nom hors fenêtre ; QAG : logo LCP hors fenêtre"}
    json.dump(plan, open(D + "plan-A10.json", "w"), indent=1, ensure_ascii=False)
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
    vx = grab(LOT + "/sources/" + RA, V_IN, V_OUT - V_IN)
    m = music_raw(MUSIC_IN, sr)[:N]
    # niveaux : voix calée 0,5 dB au-dessus du drop (la montée de FE!N est chargée) (drop mesuré sur 4 s après le 1er kick)
    sf.write(D + "tmp_v.wav", vx, sr, subtype="FLOAT"); i0 = int(DROP * sr); sf.write(D + "tmp_d.wav", m[i0:i0 + 4 * sr], sr, subtype="FLOAT")
    vg = (lufs(D + "tmp_d.wav") + MGAIN + 0.5) - lufs(D + "tmp_v.wav"); os.remove(D + "tmp_v.wav"); os.remove(D + "tmp_d.wav")
    voix = np.zeros((N, 2), np.float32); mus = np.zeros((N, 2), np.float32)
    place(voix, vx, t_of_src(V_IN), vg, fin=0.04, fout=0.06)
    duck = np.ones(len(m), np.float32); g = 10 ** (-8 / 20)
    a0, a1, b0, b1 = [int(t * sr) for t in (t_of_src(V_IN) - 0.12, t_of_src(V_IN) + 0.02, t_of_src(V_OUT) - 0.06, DROP - 0.01)]
    duck[a0:a1] = np.linspace(1, g, a1 - a0); duck[a1:b0] = g; duck[b0:b1] = np.linspace(g, 1, b1 - b0)
    place(mus, m * duck[:, None], 0.0, MGAIN, fin=0.02, fout=0.6)
    sf.write(OUT + "A10-voix.wav", voix, sr, subtype="PCM_24"); sf.write(OUT + "A10-musique.wav", mus, sr, subtype="PCM_24")
    sf.write(D + "tmp_mix.wav", voix + mus, sr, subtype="FLOAT")
    r = subprocess.run([FF, "-hide_banner", "-i", D + "tmp_mix.wav", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    js = json.loads(r[r.rindex("{"):r.rindex("}") + 1])
    af = ("loudnorm=I=-14:TP=-1.5:LRA=11:measured_I=%s:measured_TP=%s:measured_LRA=%s:measured_thresh=%s:offset=%s:linear=true,"
          "alimiter=limit=0.85:level=false:attack=1:release=60,aresample=48000" % (js["input_i"], js["input_tp"], js["input_lra"], js["input_thresh"], js["target_offset"]))
    subprocess.run([FF, "-v", "error", "-y", "-i", D + "tmp_mix.wav", "-af", af, "-c:a", "pcm_s24le", OUT + "A10-mix.wav"], check=True)
    os.remove(D + "tmp_mix.wav"); print("audio : gain voix %+.1f dB, mix avant normalisation %s LUFS" % (vg, js["input_i"]))
# ---------------- aperçu 540x960 ----------------
def apercu():
    plan = json.load(open(D + "plan-A10.json")); ins = []; fl = []
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
    ins += ["-i", OUT + "A10-mix.wav"]
    out = ROOT + "/preview/apercu-A10.mp4"
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
