# A8 (lot 3) — Aura N&B, Sébastien Delogu (député LFI des Bouches-du-Rhône), son « Alors on danse » (Stromae, chaîne officielle).
# Modèle : lot2/_claude/gen/A2 (frappes réelles) + A5 (N&B adouci, texte mot à mot recentré). Aperçu HORS Resolve (ffmpeg/numpy).
# Phrase : « Du mauvais côté du règlement, mais du bon côté de l'histoire » (QAG Gaza, 28/05/2025, chaîne LFI à l'Assemblée).
# Son : extrait continu du morceau 58,87 -> 73,8 s du complet : « Alors on sort pour oublier tous les problèmes » sous la phrase (baissé),
# « Alors on… » dans le break, drop (1er kick plein) sur « danse » à 63,54 s du complet = 4,667 s timeline.
# Règles : 9:16 plein écran, aucun visage coupé, aucun logo (LFI / timer AN / sous-titres incrustés hors fenêtre), coupes sur les kicks
# réels (118 BPM), plans >= 1 temps, poussée lente avant seulement, <= 15 s, ralentis = speed_pct (Resolve Optical Flow).
# Usage : python genA8.py [shots] [cards] [audio] [plan] [apercu] [only=ID,ID]   (sans argument = tout)
import sys, os, json, subprocess, math, functools
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
ROOT = "/Users/luca.grousset/Movies/highkey-gauchiste"; LOT = ROOT + "/lot3"
sys.path.insert(0, ROOT + "/_claude/outils")
import framing
from framing import plan_views
from fx import gblur, motion_blur, vignette, to8, ease_out
D = LOT + "/_claude/gen/A8/"; OUT = D + "out/"; os.makedirs(OUT, exist_ok=True)
framing.ROOT = LOT; framing.CACHE = D + "cache"
framing.head_box = lambda f: (f[0] - 0.12 * f[2], f[1] - 0.5 * f[3], f[0] + 1.12 * f[2], f[1] + 1.2 * f[3])
framing.view_for = functools.partial(framing.view_for, margin=0.04)
FF = "/opt/homebrew/bin/ffmpeg"; FPS = 30; W, H = 1080, 1920
RED = (0xE4, 0x00, 0x2B); WHITE = (255, 255, 255)
F_BLACK = "/System/Library/Fonts/Supplemental/Arial Black.ttf"
F_AURA = ("/System/Library/Fonts/Helvetica.ttc", 2)
QAG, FLAG = "A8-delogu-qag-gaza-2025.mp4", "A8-delogu-drapeau-lfian.mp4"
QNA, QNB = "A8-delogu-quartiers-nord-a.mp4", "A8-delogu-quartiers-nord-b.mp4"
LA, LB = "A8-delogu-lancement-a.mp4", "A8-delogu-lancement-b.mp4"
SFPS = 25                                                         # toutes les sources : 25 i/s
# zones utilisables (px source 1920x1080) :
#  QAG  : logo LFI haut gauche (x < 260), timer AN haut droite (x > 1560), sous-titres incrustés (y > 805) ; y0 = 80 pour sortir
#         le visage coupé par le haut de l'image source (député debout derrière, barbe x 800-1030, y 0-75).
#  FLAG : logo LFI-NUPES haut gauche, timer AN haut droite, sous-titres incrustés y > 830.
#  LA/LB: logo LFI haut droite (x > 1590, y < 175).
B_QAG = (270, 80, 1550, 805); B_FLAG = (270, 0, 1550, 825); B_LFI = (0, 0, 1580, 1080); B_FULL = (0, 0, 1920, 1080)
# ---------------- musique ----------------
SON_FILE = LOT + "/sons/A8-stromae-alors-on-danse_complet.wav"
SON_URL = "https://youtu.be/VHoT4N43jK8"
MDROP = 63.536                                   # 1er kick plein après le break (« danse »), complet
MGAIN = 5.0                                      # extrait à -19,2 LUFS -> mix normalisé ensuite à -14
def fr(t): return int(round(t * FPS))
DROPF = 140; DROP = DROPF / FPS                  # 4,667 s
END = 14.97                                      # règle : aura N&B 15 s max
BEAT = 0.5085                                    # 118 BPM mesuré (kicks 63,536 -> 77,773)
# ---------------- phrase (Whisper, mots dans la source QAG) ----------------
T_LONG = 132.92                                  # 1re image de Delogu (avant : plan de la présidente)
PF = DROPF - 98                                  # 1re image du plan parlé (132,92 s) ; il dure jusqu'à la caisse du break (« Alors… », image PRE)
# puis le drapeau (2024) monte sur « Alors on… » jusqu'au drop : à la fin du plan parlé Delogu se retourne et la voisine derrière lui
# sortirait par le bord gauche du cadre (visage coupé), d'où le plan parlé arrêté sur « l'histoire ».
V_IN, V_OUT = 132.66, 135.26                     # « Du » 132,72 … « l'histoire » fin 135,20 ; « monsieur le ministre » (135,36) laissé au break
def t_of_src(s): return PF / FPS + (s - T_LONG)
MUSIC_IN0 = MDROP - DROP
# ---------------- frappes réelles ----------------
def music_raw(mi, sr=48000):
    import soundfile as sf_
    x, r = sf_.read(SON_FILE, dtype="float32"); assert r == sr
    i0 = int(round(mi * sr)); return x[i0:i0 + int((END + 0.5) * sr)]
def detect_hits(y, sr=48000):
    """Kick (< 150 Hz, instant pris sur son clic 150-1500 Hz) et caisse (> 1,5 kHz) : attaque à 30 % de l'enveloppe (copie de genA2)."""
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
        for p in librosa.util.peak_pick(d, pre_max=20, post_max=20, pre_avg=40, post_avg=40, delta=0.15, wait=40):
            c0 = p * hop; lo, hi = max(0, c0 - int(0.01 * sr)), min(len(env), c0 + int(0.05 * sr))
            i = attack(env, lo + int(np.argmax(env[lo:hi])))
            lvl = float(env[min(len(env) - 1, i + int(0.03 * sr))])
            if band == "kick":
                lo, hi = max(0, i - int(0.06 * sr)), i + int(0.01 * sr); c = lo + int(np.argmax(clic[lo:hi]))
                if clic[c] > 2 * np.median(clic[max(0, lo - int(0.1 * sr)):lo]): i = attack(clic, c)
            out.append((round(i / sr, 4), band, round(float(d[p]), 2), round(lvl, 3)))
    return sorted(out)
# montage après le drop : (id, effet d'entrée, nb de temps) ; coupes sur les kicks pleins (temps 0 = drop)
EDIT = [("cri", "drop", 2), ("intense", "whip", 2), ("foule_ps", "whip", 1), ("main", "whip", 2), ("foule_lanc", "cut", 1),
        ("bras", "whip", 2), ("aura", "cut", 1), ("salut", "drop", 2), ("geste", "whip", 2), ("sourire", "cut", 2)]
PRE_SNARE = 62.746                               # frappe la plus forte du break (attaque 62,746 s, sommet 62,80), sur « Alors » (complet) : coupe plan parlé -> drapeau
CUT_K = [0]
for _, _, nb in EDIT: CUT_K.append(CUT_K[-1] + nb)                # temps des coupes (dernier = carton de fin)
HITS_JSON = OUT + "A8-frappes.json"
def frappes():
    """Décalage sous-image de l'extrait choisi pour que les kicks coupés tombent au plus près des images ; frappes mesurées sur la musique posée."""
    if os.path.exists(HITS_JSON):
        js = json.load(open(HITS_JSON))
        if js["cle"] == [MUSIC_IN0, END, CUT_K]: return js["music_in"], js["frappes"]
    h0 = detect_hits(music_raw(MUSIC_IN0))
    kicks = [h[0] for h in h0 if h[1] == "kick" and h[3] > 0.1]
    def cut_kicks(off):
        return [min(kicks, key=lambda t: abs(t - (DROP + k * BEAT))) - off for k in CUT_K]
    best = min(np.arange(-0.016, 0.0165, 0.001), key=lambda off: max(abs(t - round(t * FPS) / FPS) for t in cut_kicks(off)))
    mi = MUSIC_IN0 + best
    h = detect_hits(music_raw(mi))
    json.dump({"cle": [MUSIC_IN0, END, CUT_K], "music_in": mi, "frappes": h}, open(HITS_JSON, "w")); return mi, h
MUSIC_IN, HITS = frappes()
KICKS = [h[0] for h in HITS if h[1] == "kick" and h[3] > 0.1]
def snap(t):
    c = min(KICKS, key=lambda x: abs(x - t)); assert abs(c - t) < 0.04, ("pas de kick près de", t); return c
CUTS = [snap(DROP + k * BEAT) for k in CUT_K]
CUTF = [fr(c) for c in CUTS]
assert CUTF[0] == DROPF, (CUTF[0], DROPF)
PRE_T = min((h[0] for h in HITS if h[1] == "caisse"), key=lambda x: abs(x - (PRE_SNARE - MUSIC_IN))); PREF = fr(PRE_T)
assert abs(PRE_T - (PRE_SNARE - MUSIC_IN)) < 0.03 and DROPF - PREF >= 15, (PRE_T, PREF)
PLAN_N = {sid: CUTF[i + 1] - CUTF[i] for i, (sid, _, _) in enumerate(EDIT)}
assert min(PLAN_N.values()) >= 15, ("plan < 1 temps", PLAN_N)
# ---------------- plans ----------------
SHOTS = {
    "long":      dict(src=QAG, t=T_LONG, face=(720, 400), b=B_QAG, vh=725, zoom=(1.0, 1.03), top=0.12, dx=-70,
                      why="QAG Gaza 28/05/2025 : « Du mauvais côté du règlement, mais du bon côté de l'histoire » (son synchrone)"),
    "drapeau":   dict(src=FLAG, t=146.70, fixed=(1112, 434), b=B_FLAG, vh=471, zoom=(1.0, 1.04), speed=60,
                      why="brandit le drapeau palestinien dans l'hémicycle (28/05/2024), texte MAIS DU BON CÔTÉ / DE L'HISTOIRE tenu jusqu'au drop"),
    "intense":   dict(src=QNA, t=56.30, face=(1290, 400), b=B_FULL, vh=1080, zoom=(1.0, 1.05), top=0.10, why="meeting Quartiers Nord, gros plan, voix forte"),
    "foule_ps":  dict(src=QNB, t=447.30, fixed=(830, 540), b=B_FULL, vh=900, zoom=(1.0, 1.05), why="foule debout, drapeau palestinien et drapeaux LFI"),
    "main":      dict(src=QNB, t=22.45, face=(780, 380), b=B_FULL, vh=1080, zoom=(1.0, 1.05), top=0.10, why="gros plan, main levée"),
    "foule_lanc": dict(src=LA, t=26.00, fixed=(640, 560), b=B_LFI, vh=760, zoom=(1.0, 1.05), why="meeting de lancement, salle noire, drapeaux palestiniens"),
    "bras":      dict(src=QNB, t=80.45, face=(900, 330), b=B_FULL, vh=1080, zoom=(1.0, 1.05), top=0.10, why="gros plan, bras tendu vers la salle"),
    "salut":     dict(src=LB, t=8.00, face=(958, 265), b=B_LFI, vh=760, zoom=(1.0, 1.05), top=0.12, dx=60, why="lancement de campagne, salue la salle, drapeaux au premier plan"),
    "cri":       dict(src=QNA, t=100.85, face=(1000, 330), b=B_FULL, vh=1080, zoom=(1.0, 1.05), top=0.10, why="gros plan, harangue"),
    "geste":     dict(src=QNB, t=367.20, face=(960, 330), b=B_FULL, vh=1080, zoom=(1.0, 1.05), top=0.10, why="gros plan, main ouverte vers la salle"),
    "sourire":   dict(src=QNA, t=17.60, face=(1190, 260), b=B_FULL, vh=1080, zoom=(1.0, 1.04), top=0.12, speed=60, why="gros plan, grand sourire (ralenti de fin)"),
}
# ---------------- look N&B (genA5, adouci après retour Luca) ----------------
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
def read_frames(src, t, n_out):
    need = [int(round(i * SFPS / FPS)) for i in range(n_out)]; n_src = need[-1] + 1
    p = subprocess.run([FF, "-v", "error", "-ss", "%.4f" % t, "-i", LOT + "/sources/" + src, "-frames:v", str(n_src),
                        "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True)
    a = np.frombuffer(p.stdout, np.uint8).reshape(-1, 1080, 1920, 3)
    return [a[min(i, len(a) - 1)].astype(np.float32) / 255 for i in need], int(round(t * SFPS))
def crop_916(img, cx, cy, vh):
    vw = vh * 9 / 16; s = W / vw
    M = np.float32([[s, 0, W / 2 - cx * s], [0, s, H / 2 - cy * s]])
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
# ---------------- texte (Arial Black, contour noir + ombre douce, mot-clé rouge, jamais de guillemets) ----------------
def font(size): return ImageFont.truetype(F_BLACK, max(8, int(size)))
def fit_size(txt, maxw, start=260):
    s = start
    while font(s).getlength(txt) + 2 * max(4, int(s * 0.045)) > maxw: s -= 2     # contour compris
    return s
# zone sûre TikTok (retour Luca : textes sous l'interface) : bloc <= 66 % de large centré (x 184-896), y 230-1440.
# Lignes coupées en 3 (DU MAUVAIS / CÔTÉ DU / RÈGLEMENT, MAIS DU BON / CÔTÉ DE / L'HISTOIRE), hauteur de lettre >= ~65 px,
# bloc sous le menton (haut ~1050) et bas <= 1400.
TXT_W = 700; X_MIN, X_MAX = int(W * 0.17) + 6, int(W * 0.83) - 6; Y0 = 1085
S_A = fit_size("DU MAUVAIS", TXT_W, 110); S_B = fit_size("MAIS DU BON", TXT_W, 110)
# mots réels (Whisper, source QAG) : Du 132,72 / mauvais 132,92 / côté 133,18 / du 133,48 / règlement 133,68 /
# mais 134,06 / du 134,20 / bon 134,34 / côté 134,50 / de 134,78 / l'histoire 134,88-135,20
CARDS = [
    [(S_A, Y0, [("DU", 132.72, WHITE), ("MAUVAIS", 132.92, WHITE)]), (S_A, None, [("CÔTÉ", 133.18, WHITE), ("DU", 133.48, WHITE)]),
     (200, None, [("RÈGLEMENT", 133.68, WHITE)])],
    [(S_B, Y0, [("MAIS", 134.06, WHITE), ("DU", 134.20, WHITE), ("BON", 134.34, WHITE)]), (S_B, None, [("CÔTÉ", 134.50, WHITE), ("DE", 134.78, WHITE)]),
     (200, None, [("L'HISTOIRE", 134.88, RED)])],
]
def layout(card):
    out = []; y_prev = None; s_prev = None
    for size, yc, words in card:
        txt = " ".join(w for w, _, _ in words)
        size = fit_size(txt, TXT_W, start=size)
        if yc is None: yc = y_prev + s_prev * 0.5 + 34 + size * 0.5
        f = font(size); total = f.getlength(txt); x = (W - total) / 2
        for w, t, col in words:
            out.append(dict(w=w, t=t, col=col, size=size, x=x, yc=yc)); x += f.getlength(w + " ")
        y_prev, s_prev = yc, size
    return out
def full_sizes(card):
    """tailles/positions fixées sur la carte ENTIÈRE (la taille ne change pas quand un mot arrive) ; x recentré sur les mots visibles."""
    return [(it["size"], it["yc"]) for it in layout(card)]
def draw_words(items, scale_last=1.0, alpha_last=1.0):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay); ds = ImageDraw.Draw(sh)
    for k, it in enumerate(items):
        last = k == len(items) - 1; sc = scale_last if last else 1.0
        sw = max(4, int(it["size"] * 0.045)); wfull = font(it["size"]).getlength(it["w"])
        sc = min(sc, max(1.0, (X_MAX - X_MIN - 2 * sw) / wfull))                        # mot géant : agrandissement d'entrée plafonné
        f = font(it["size"] * sc); wnow = f.getlength(it["w"])
        x = min(max(it["x"] + (wfull - wnow) / 2, X_MIN + sw), X_MAX - sw - wnow)       # entrée agrandie gardée dans la zone sûre
        x0, y0, x1, y1 = d.textbbox((0, 0), it["w"], font=f); y = it["yc"] - (y1 - y0) / 2 - y0
        a = int(255 * (alpha_last if last else 1.0))
        ds.text((x, y + it["size"] * 0.05), it["w"], font=f, fill=(0, 0, 0, int(a * 0.78)), stroke_width=sw * 3, stroke_fill=(0, 0, 0, int(a * 0.78)))
        d.text((x, y), it["w"], font=f, fill=it["col"] + (a,), stroke_width=sw, stroke_fill=(0, 0, 0, a))
    sh = sh.filter(ImageFilter.GaussianBlur(18))
    return np.asarray(Image.alpha_composite(sh, lay)).astype(np.float32) / 255
def long_text(t_src):
    ci = 1 if t_src >= CARDS[1][0][2][0][1] else 0
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
    out = [("long", "cut", PF, PREF), ("drapeau", "cut", PREF, DROPF)]
    for i, (sid, eff, nb) in enumerate(EDIT): out.append((sid, eff, CUTF[i], CUTF[i + 1]))
    return out
def clip_name(sid, eff): return "A8_%s.mov" % sid if eff == "cut" else "A8_%s_%s.mov" % (sid, eff)
TXT_HOLD = [None]
def render_slot(sid, eff, a, b):
    sh = SHOTS[sid]; n = b - a
    raw, s0 = read_frames(sh["src"], sh["t"], n)
    m = math.ceil(n * sh.get("speed", 100) / 100)               # poussée lente avant terminée sur la frappe de sortie (ralenti compris)
    z0, z1 = sh["zoom"]; zoom = lambda f: z0 + (z1 - z0) * min(f / max(m - 1, 1), 1.0)
    if "fixed" in sh:
        views, _ = plan_views(sh["src"], s0, n, SFPS, speed=SFPS / FPS, bounds=sh["b"], vh=sh["vh"], zoom=zoom, fixed=sh["fixed"])
    else:
        dx = sh.get("dx", 0)
        views, ok = plan_views(sh["src"], s0, n, SFPS, speed=SFPS / FPS, hint=sh["face"], bounds=sh["b"], vh=sh["vh"], zoom=zoom, top=sh["top"],
                               shake=(lambda f: (dx / 600.0, 0)) if dx else None)
        if not ok: print("  ! pas de visage :", sid)
    frames = []
    for i, (img, (cx, cy, vh)) in enumerate(zip(raw, views)):
        g = grade(crop_916(img, cx, cy, vh), sh.get("white", 0.87))
        if sid == "long":
            tl = long_text(sh["t"] + i / FPS)
            if tl is not None: g = over_rgba(g, tl)
        if sid == "drapeau":                                    # fin de la phrase (« …DE L'HISTOIRE ») tenue sur le drapeau jusqu'au drop
            if i == 0: TXT_HOLD[0] = long_text(V_OUT + 0.2)
            g = over_rgba(g, TXT_HOLD[0])
        if eff == "whip" and i < 3: g = motion_blur(g, 0, [220, 90, 25][i], steps=16)
        if eff == "drop" and i < 8:
            k = (1 - i / 8) ** 2; g = np.clip(g + k * 0.55 + gblur(g, 25) * k * 0.6, 0, 1)
        frames.append(g)
    write_mov(frames, OUT + clip_name(sid, eff))
    vx = views[0]; vz = views[-1]
    print("  %-10s %3d im  vue %d,%d h%d -> h%d  (x %d-%d, y %d-%d)" % (sid, n, vx[0], vx[1], vx[2], vz[2], vx[0] - vx[2] * 9 / 32, vx[0] + vx[2] * 9 / 32,
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
    write_mov(aura_card(PF), OUT + "A8_aura_intro.mov")
    write_mov(aura_card(PLAN_N["aura"]), OUT + "A8_aura.mov")
    write_mov(aura_card(fr(END) - CUTF[-1], fade_in=3, fade_out=12), OUT + "A8_aura_fin.mov")
# ---------------- plan ----------------
def build_plan():
    video = []
    def add(id_, clip, n, rec, kind, extra=None):
        v = {"id": id_, "clip": clip, "folder": "genA8", "s": 0, "e": n, "rec": rec, "dur": n, "clip_fps": FPS, "track": 1, "kind": kind}
        if extra: v.update(extra)
        video.append(v)
    add("hook", "A8_aura_intro.mov", PF, 0, "card")
    for sid, eff, a, b in slots():
        if sid == "aura": add("aura_%d" % a, "A8_aura.mov", b - a, a, "card"); continue
        sh = SHOTS[sid]
        extra = {"source": "lot3/sources/%s @ %.2f s" % (sh["src"], sh["t"]), "source_fps": SFPS, "effet": eff, "pourquoi": sh["why"]}
        if sid != "long": extra["temps"] = round((b - a) / FPS / BEAT, 2)
        if sid == "long": extra["texte"] = "DU MAUVAIS CÔTÉ / DU RÈGLEMENT · MAIS DU BON CÔTÉ / DE L'HISTOIRE (rouge), mot à mot, Arial Black"
        extra["speed_pct"] = sh.get("speed", 100)
        if sh.get("speed"): extra["retime"] = "optical_flow"
        add("%s_%d" % (sid, a), clip_name(sid, eff), b - a, a, "shot", extra)
    add("fin", "A8_aura_fin.mov", fr(END) - CUTF[-1], CUTF[-1], "card")
    plan = {"name": "A8 - Aura N&B - Sébastien Delogu", "fps": FPS, "w": W, "h": H, "duree_s": END,
            "note": "Plans 9:16 recadrés + étalonnés N&B (lot3/_claude/gen/A8/out), vitesse normale. s/e en images du clip (30 i/s), rec en images timeline. "
                    "speed_pct < 100 : ralenti Resolve Optical Flow + Speed Warp (aperçu = setpts simple ; e - s = durée timeline à vitesse normale). "
                    "Coupes sur les kicks réels de Alors on danse mesurés dans la musique posée (out/A8-frappes.json), drop = 1er kick plein sur « danse » "
                    "(63,536 s du complet = %.3f s timeline, image %d), 1 temps = 0,5085 s (118 BPM)." % (CUTS[0], DROPF),
            "phrase": {"texte": "Du mauvais côté du règlement, mais du bon côté de l'histoire",
                       "source": "lot3/sources/%s 132,72-135,20 s (YouTube gEZLJe_uJUs, chaîne La France insoumise à l'Assemblée nationale, QAG Gaza du 28/05/2025, réponse au ministre ; « monsieur le ministre » non gardé)" % QAG,
                       "timeline_s": [round(t_of_src(132.72), 2), round(t_of_src(135.20), 2)]},
            "video": video,
            "audio": [{"id": "mix", "clip": "A8-mix.wav", "folder": "genA8", "rec": 0, "track": 1,
                       "note": "mix -14 LUFS : musique de 0 à la fin (complet lu en continu dès %.3f s), voix synchrone %.2f-%.2f s, musique -9 dB sous la voix" % (MUSIC_IN, t_of_src(V_IN), t_of_src(V_OUT))}],
            "stems": ["lot3/_claude/gen/A8/out/A8-voix.wav", "lot3/_claude/gen/A8/out/A8-musique.wav"],
            "musique": {"fichier": "lot3/sons/A8-stromae-alors-on-danse_complet.wav", "titre": "Stromae - Alors on danse (%s)" % SON_URL,
                        "debut_complet_s": round(MUSIC_IN, 4), "fin_complet_s": round(MUSIC_IN + END, 3), "gain_db": MGAIN,
                        "kicks_timeline_s": KICKS, "coupes_kicks_s": CUTS, "coupes_images": CUTF, "coupe_break_caisse_s": PRE_T, "coupe_break_image": PREF},
            "logos_exclus": "QAG : logo LFI, timer AN et sous-titres incrustés hors fenêtre ; drapeau : idem ; lancement : logo LFI haut droite hors fenêtre",
            "sources_url": {QAG: "youtube gEZLJe_uJUs (La France insoumise à l'Assemblée nationale, 28/05/2025)",
                            FLAG: "youtube iHBkHUaUUTc (La France insoumise à l'Assemblée nationale, 28/05/2024)",
                            QNA: "youtube oKStIbwdqHc (chaîne Sébastien Delogu, meeting Quartiers Nord 08/02/2026), offset 4680 s",
                            QNB: "youtube oKStIbwdqHc, offset 5240 s",
                            LA: "youtube jJa6EONNokI (chaîne Sébastien Delogu, lancement de campagne 08/12/2025), offset 1050 s",
                            LB: "youtube jJa6EONNokI, offset 1255 s"}}
    json.dump(plan, open(D + "plan-A8.json", "w"), indent=1, ensure_ascii=False)
    return plan
# ---------------- audio ----------------
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
    voix = np.zeros((N, 2), np.float32); mus = np.zeros((N, 2), np.float32)
    place(voix, grab(LOT + "/sources/" + QAG, V_IN, V_OUT - V_IN), t_of_src(V_IN), +3, fin=0.04, fout=0.06)
    m = music_raw(MUSIC_IN, sr)[:N]
    duck = np.ones(len(m), np.float32); g = 10 ** (-9 / 20)
    a0, a1, b0, b1 = [int(t * sr) for t in (t_of_src(V_IN) - 0.12, t_of_src(V_IN) + 0.02, t_of_src(V_OUT) - 0.06, t_of_src(V_OUT) + 0.02)]
    duck[a0:a1] = np.linspace(1, g, a1 - a0); duck[a1:b0] = g; duck[b0:b1] = np.linspace(g, 1, b1 - b0)
    place(mus, m * duck[:, None], 0.0, MGAIN, fin=0.02, fout=0.6)
    sf.write(OUT + "A8-voix.wav", voix, sr, subtype="PCM_24"); sf.write(OUT + "A8-musique.wav", mus, sr, subtype="PCM_24")
    sf.write(D + "tmp_mix.wav", voix + mus, sr, subtype="FLOAT")
    r = subprocess.run([FF, "-hide_banner", "-i", D + "tmp_mix.wav", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    js = json.loads(r[r.rindex("{"):r.rindex("}") + 1])
    af = ("loudnorm=I=-14:TP=-1.5:LRA=11:measured_I=%s:measured_TP=%s:measured_LRA=%s:measured_thresh=%s:offset=%s:linear=true,"
          "alimiter=limit=0.85:level=false:attack=1:release=60,aresample=48000" % (js["input_i"], js["input_tp"], js["input_lra"], js["input_thresh"], js["target_offset"]))
    subprocess.run([FF, "-v", "error", "-y", "-i", D + "tmp_mix.wav", "-af", af, "-c:a", "pcm_s24le", OUT + "A8-mix.wav"], check=True)
    os.remove(D + "tmp_mix.wav"); print("audio : mix avant normalisation", js["input_i"], "LUFS")
# ---------------- aperçu 540x960 ----------------
def apercu():
    plan = json.load(open(D + "plan-A8.json")); ins = []; fl = []
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
    ins += ["-i", OUT + "A8-mix.wav"]
    out = ROOT + "/preview/apercu-A8.mp4"
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
