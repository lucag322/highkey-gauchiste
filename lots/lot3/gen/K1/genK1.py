# Lot 3 / K1 — Karaoké discours (recette editsofourtimes), Louis Boyard, Michael Jackson – Smooth Criminal : refrain « Annie, are you OK » sous la voix,
# drop sur « You've been hit by, you've been struck by a smooth criminal » juste après la phrase (choix de Luca).
# Phrase réelle mot à mot : QAG du 6/10/2026 (LCP), « La jeunesse vient de prendre conscience d'elle-même. ... que les jeunes ont raison depuis le début. »
# Structure de la recette : plan long d'ouverture synchro (asseoir le sujet), puis 1 plan par fragment du discours (B-roll lycéens, meeting),
# rafale de coupes d'1 temps sur « pour reculer / maintenant » et en fin, puis document d'époque (bandeau URGENT BFMTV) sur noir.
# Fin rallongée de 2,5 s (demande de Luca) : après la rafale, 2 plans de 2 temps (drapeaux du meeting, foule lycéenne) puis le document jusqu’à la frappe 179,495 s.
# Sous-titres jaune #FFD700, italique sans-serif léger (Avenir Next Medium Italic), bas-centre, texte nu sans guillemets, mot à mot.
# Coupes sur les vraies frappes du morceau (timing.py -> timing.json). Pas de ralenti. Usage : python genK1.py [plans] [audio] [apercu] [only=ID,..]
import sys, os, json, subprocess
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
HK = "/Users/luca.grousset/Movies/highkey-gauchiste"
L3 = HK + "/lot3"
sys.path.insert(0, HK + "/_claude/outils")
import framing
framing.ROOT = L3; framing.CACHE = L3 + "/_claude/gen/K1/cache/faces"
from framing import plan_views, detect, head_box
from fx import crop_view, gblur, over, vignette, grain
from words import tokens, clean
FF = "/opt/homebrew/bin/ffmpeg"
D = L3 + "/_claude/gen/K1/"; OUT = D + "out/"; os.makedirs(OUT, exist_ok=True)
W, H, TFPS = 1080, 1920, 30
TM = json.load(open(D + "timing.json"))
M0, SH = TM["M0"], TM["shifts"]
HITS = [h - M0 for h in TM["hits_complet"]]
def hit(t): return min(HITS, key=lambda h: abs(h - t))
def f30(t): return int(round(t * TFPS))

SRC = {"LCP": "K1-boyard-lcp-qag-2026-10.mp4", "LFI": "K1-boyard-lfi-qag-2026-10.mp4", "FI": "K1-lyceens-franceinfo-2026-10.mp4",
       "LP": "K1-lyceens-leprogres-2026-10.mp4", "MA": "K1-boyard-meeting-npp-a.mp4", "MB": "K1-boyard-meeting-npp-b.mp4",
       "BFM": "K1-boyard-bfmtv-urgent-2026-10.mp4"}
URL = {"LCP": ("https://www.youtube.com/watch?v=clLUMRlLyPc", 90.0, "LCP - Assemblée nationale", "2026-10-06"),
       "LFI": ("https://www.youtube.com/watch?v=QbYEjxSoyww", 0.0, "La France insoumise à l'Assemblée nationale", "2026-10-06"),
       "FI": ("https://www.youtube.com/watch?v=Fs3db3YZsUs", 35.0, "franceinfo", "2026-10-12"),
       "LP": ("https://www.youtube.com/watch?v=VU8-H-Iy5mY", 15.0, "Le Progrès (images Cebra Info)", "2026-10-06"),
       "MA": ("https://www.youtube.com/watch?v=cNkMqVnlUl0", 140.0, "Louis Boyard (meeting Nouveau Paris populaire)", "2026-01-31"),
       "MB": ("https://www.youtube.com/watch?v=cNkMqVnlUl0", 252.0, "Louis Boyard (meeting Nouveau Paris populaire)", "2026-01-31"),
       "BFM": ("https://www.youtube.com/watch?v=lZ-hCPSoNv4", 0.0, "Louis Boyard (capture BFMTV en direct)", "2026-10-02")}
# zones source sans logo / bandeau / interprète / sous-titres incrustés
BOUNDS = {"LCP": (280, 0, 1450, 845), "LFI": (270, 0, 1555, 800), "FI": (0, 0, 1920, 855), "LP": (240, 0, 1640, 1080),
          "MA": (0, 0, 1690, 1080), "MB": (0, 0, 1690, 1080)}
SFPS = 25

# ---------------- texte : mots du transcript LCP (whisper, mot à mot) ----------------
TX = json.load(open(L3 + "/../lot2/_claude/tx/clLUMRlLyPc.json"))
RAW = [{"w": w["word"].strip(), "start": w["start"], "end": w["end"]} for s in TX["segments"] for w in s["words"] if 94.2 <= w["start"] <= 107.7]
T = tokens(RAW)
SIZES = [2, 4, 1, 3, 2, 3, 2, 2, 1, 4, 3, 5, 5, 3]
assert sum(SIZES) == len(T), (len(T), [t["w"] for t in T])
FR = TM["frag"]; CUT_FROM = TM["cut_from"]
def seg_of(t0):
    return max(i for i, (a, b) in enumerate(TM["segs"]) if a - 0.05 <= t0)
def tl(orig): return orig - 94.28 + SH[seg_of(orig)]          # temps vidéo LCP d'origine -> timeline
def disp(w): return clean(w, keep_quotes=False).replace("'", "’").replace("Education", "Éducation")
FRAGS, i = [], 0
for k, z in enumerate(SIZES):
    ws = T[i:i + z]; i += z
    FRAGS.append({"txt": FR[k][0], "words": [(disp(t["w"]), tl(t["start"])) for t in ws], "w0": tl(ws[0]["start"]), "end_voice": tl(ws[-1]["end"])})
    assert " ".join(disp(t["w"]) for t in ws) == FR[k][0], (FR[k][0], [t["w"] for t in ws])
CUTS = [hit(FRAGS[k]["w0"] - 0.06) for k in range(CUT_FROM, len(FRAGS))]
for k, f in enumerate(FRAGS): f["ds"] = CUTS[k - CUT_FROM] if k >= CUT_FROM else f["w0"]
VEND = FRAGS[-1]["end_voice"]
DROP_T = hit(TM["drop_c"] - M0)                             # « You've been hit by » : le hook tombe juste après « début »
R0 = DROP_T; RCUTS = [R0, hit(173.390 - M0), hit(173.895 - M0), hit(174.405 - M0)]   # rafale : you've been | hit by | you've been | document
NCUTS = [RCUTS[3], hit(175.424 - M0), hit(176.438 - M0)]   # fin rallongée (demande de Luca, +2,5 s) : 2 plans de plus sur les frappes, puis document
END = hit(179.495 - M0)                                     # fin sur la frappe forte 179,495 s (temps 3, 2 mesures après le retour du groove 176,44 ; aucun mot chanté après « criminal » 176,68)
for k, f in enumerate(FRAGS): f["de"] = FRAGS[k + 1]["ds"] if k + 1 < len(FRAGS) else R0

FONT = ("/System/Library/Fonts/Avenir Next.ttc", 9)          # Avenir Next Heavy Italic (retour Luca : plus gros, plus gras)
YEL = np.array([0, 215, 255], np.float32) / 255              # #FFD700 en BGR
EM_MAX, WFRAC, YB = 150, 0.58, 0.715          # zone sûre TikTok : bloc ≤ 66 % de large (x 0,17-0,83), bas du bloc ≤ 0,75 (correctif lot4 K2 ; 58 % : débord de l’italique)
_F = {}
def font(px):
    px = int(round(px))
    if px not in _F: _F[px] = ImageFont.truetype(FONT[0], px, index=FONT[1])
    return _F[px]
_L = {}
def layer(ci, nv):
    """Fragment ci avec ses nv premiers mots ; mise en page du fragment complet (1 ou 2 lignes équilibrées, pas de saut)."""
    key = (ci, nv)
    if key in _L: return _L[key]
    words = [w[0] for w in FRAGS[ci]["words"]]
    f100 = font(100); sp = f100.getlength(" ") / 100
    wl = lambda ws: sum(f100.getlength(w) / 100 for w in ws) + sp * (len(ws) - 1)
    lines = [words]
    if len(words) > 1 and WFRAC * W / wl(words) < 125:
        k = min(range(1, len(words)), key=lambda k: max(wl(words[:k]), wl(words[k:])))
        lines = [words[:k], words[k:]]
        if len(words) > 2 and WFRAC * W / max(wl(l) for l in lines) < 110:
            import itertools
            lines = min(([words[:a], words[a:b], words[b:]] for a, b in itertools.combinations(range(1, len(words)), 2)), key=lambda ls: max(wl(l) for l in ls))
    em = min(EM_MAX, min(WFRAC * W / wl(l) for l in lines)); f = font(em)
    cap = f.getbbox("H"); lh = em * 1.10
    desc = f.getbbox("pgq")[3] - cap[3]
    st = max(3, int(round(em * 0.075)))
    m = Image.new("L", (W, H), 0); ms = Image.new("L", (W, H), 0); dr = ImageDraw.Draw(m); ds = ImageDraw.Draw(ms)
    idx = 0
    for li, l in enumerate(lines):
        y_top = YB * H - cap[3] - max(desc, 0) - st - (len(lines) - 1 - li) * lh
        x = W / 2 - em * wl(l) / 2
        for w in l:
            if idx < nv:
                ds.text((x, y_top), w, font=f, fill=255, stroke_width=st, stroke_fill=255)
                dr.text((x, y_top), w, font=f, fill=255)
            x += f.getlength(w) + f.getlength(" "); idx += 1
    a = np.asarray(m, np.float32) / 255; o = np.asarray(ms, np.float32) / 255
    sh1 = np.clip(gblur(o, 12) * 1.5, 0, 1) * 0.55            # ombre douce
    sh2 = np.clip(gblur(o, 1.0), 0, 1) * 0.92                  # contour sombre net
    _L[key] = (a, sh1, sh2); return _L[key]
def draw_text(img, t):
    for ci, c in enumerate(FRAGS):
        if c["ds"] <= t < c["de"]:
            nv = max(1, sum(1 for w in c["words"] if w[1] <= t + 0.02))
            a, s1, s2 = layer(ci, nv); z = np.zeros(3, np.float32)
            img = over(img, z, s1); img = over(img, z, s2)
            return over(img, YEL, a)
    return img

# ---------------- étalonnage commun (couleur, contraste doux, chaud léger, vignette, grain) ----------------
_VIG = vignette(np.ones((H, W, 3), np.float32), 0.32)
def grade(img):
    s = img * img * (3 - 2 * img); img = 0.78 * img + 0.22 * s
    y = img @ np.array([0.114, 0.587, 0.299], np.float32)
    img = y[..., None] + 0.95 * (img - y[..., None])
    img = img * np.array([0.97, 1.0, 1.03], np.float32)
    return grain(img * _VIG, 0.018)

# ---------------- plans ----------------
def S(i, src, a, b, t_in, hint=None, auto=False, note="", z1=1.06, txt=False, z0=1.0):
    return dict(id=i, src=src, a=a, b=b, t_in=t_in, hint=hint, auto=auto, note=note, z1=z1, txt=txt, z0=z0)
C = CUTS
O = SH[0]
LFI_OFF = -0.178                                  # LFI = LCP d'origine - 0,178 s (corrélation audio)
t_lfi = 102.04 + (C[4] - FRAGS[9]["w0"]) - 90.0 + 90.0 + LFI_OFF   # temps LFI au début du plan F10 (synchro)
SHOTS = [
    S("O1", "LCP", 0.0, C[0], 4.28 - O, hint=(900, 300), z1=1.12, txt=True, note="ouverture longue synchro : Boyard à l'Assemblée, La jeunesse ... trop loin"),
    S("F6", "FI", C[0], C[1], 6.55, auto=True, txt=True, note="Elle s'est déjà : sit-in de lycéens"),
    S("F7", "LP", C[1], C[2], 9.9, auto=True, txt=True, note="trop sacrifiée : CRS et lacrymogènes (Lyon, 6/10)"),
    S("F8", "LP", C[2], C[3], 39.0, auto=True, txt=True, note="pour reculer : cortège lycéen avec banderoles"),
    S("F9", "MA", C[3], C[4], 0.05, hint=(1130, 260), txt=True, note="maintenant : poing levé au meeting", z0=1.35),
    S("F10", "LFI", C[4], C[5], t_lfi, hint=(915, 300), txt=True, note="Alors monsieur le ministre : synchro, Assemblée (version LFI)"),
    S("F11", "FI", C[5], C[6], 1.5, auto=True, txt=True, note="de l'Éducation nationale : lycée bloqué (poubelles)"),
    S("F12", "MB", C[6], C[7], 35.0, hint=(1000, 300), txt=True, note="acceptez que vous avez perdu : bras tendu, accusateur", z0=1.35),
    S("F13", "FI", C[7], C[8], 50.6, auto=True, txt=True, note="que les jeunes ont raison : lycéens bras levés"),
    S("F14", "FI", C[8], RCUTS[0], 53.3, auto=True, txt=True, note="depuis le début : cortège lycéen avec pancartes"),
    S("R1", "LCP", RCUTS[0], RCUTS[1], 36.0, auto=True, note="drop You've been : groupe LFI debout qui applaudit"),
    S("R2", "MB", RCUTS[1], RCUTS[2], 39.7, hint=(800, 290), note="rafale hit by : bras levé au meeting", z0=1.35),
    S("R3", "MA", RCUTS[2], RCUTS[3], 12.0, auto=True, note="rafale you've been : salle du meeting"),
    S("N1", "MB", NCUTS[0], NCUTS[1], 6.0, auto=True, note="hit by : la salle du meeting agite les drapeaux"),
    S("N2", "LP", NCUTS[1], NCUTS[2], 26.0, auto=True, note="a smooth criminal : foule lycéenne et fumigènes (Lyon, 6/10)"),
    S("DOC", "BFM", NCUTS[2], END, 4.3, note="retour du groove : document d'époque plein écran, bandeau URGENT BFMTV"),
]
FADE_S = 0.4
for sh in SHOTS:
    sh["rec"] = f30(sh["a"]); sh["dur"] = f30(sh["b"]) - sh["rec"]; sh["n"] = sh["dur"]; sh["clip"] = "K1_%s.mov" % sh["id"]

def read_frames(src, t, n, w=1920, h=1080):
    p = subprocess.Popen([FF, "-v", "error", "-ss", "%.4f" % t, "-i", L3 + "/sources/" + SRC[src], "-vf", "fps=30", "-frames:v", str(n),
                          "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE)
    sz = w * h * 3
    for _ in range(n):
        b = p.stdout.read(sz)
        if len(b) < sz: break
        yield np.frombuffer(b, np.uint8).reshape(h, w, 3)
    p.stdout.close(); p.wait()
def writer(path):
    return subprocess.Popen([FF, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", "%dx%d" % (W, H), "-r", "30", "-i", "-",
                             "-c:v", "prores_ks", "-profile:v", "3", "-pix_fmt", "yuv422p10le", "-vendor", "apl0", path], stdin=subprocess.PIPE)

def cut_faces(faces, views, thr=0.035):
    """Nombre de visages (h >= thr x hauteur de vue) dont la tête touche un bord de la vue."""
    bad = 0
    for fl, (cx, cy, v) in zip(faces, views):
        vw = v * 9 / 16; x0, y0, x1, y1 = cx - vw / 2, cy - v / 2, cx + vw / 2, cy + v / 2
        for f in fl:
            if f[3] / v < thr: continue
            hx0, hy0, hx1, hy1 = head_box(f)
            inside = hx0 >= x0 and hx1 <= x1 and hy0 >= y0 and hy1 <= y1
            outside = hx1 <= x0 or hx0 >= x1 or hy1 <= y0 or hy0 >= y1
            if not inside and not outside: bad += 1
    return bad
def auto_view(sh, s, n, speed):
    """Plan de foule : centre fixe + poussée lente, choisi pour qu'aucun visage ne soit coupé par le cadre."""
    bd = BOUNDS[sh["src"]]; vmax = min(bd[3] - bd[1], (bd[2] - bd[0]) * 16 / 9)
    faces = detect(SRC[sh["src"]], s, int(n * speed) + 2, SFPS); faces = [faces[min(int(f * speed), len(faces) - 1)] for f in range(n)]
    best = None
    for vs in (1.0, 0.92, 0.85, 0.78, 0.7):
        v0 = vmax * vs; vw0 = v0 * 9 / 16
        for cy in sorted({bd[1] + v0 / 2, (bd[1] + bd[3]) / 2, bd[3] - v0 / 2}):
            for cx in np.arange(bd[0] + vw0 / 2, bd[2] - vw0 / 2 + 1, 12):
                views = []
                for f in range(n):
                    v = v0 / (1 + (sh["z1"] - 1) * f / max(n - 1, 1)); views.append((cx, cy, v))
                bad = cut_faces(faces, views)
                score = bad * 1000 + abs(cx - (bd[0] + bd[2]) / 2) / 400 + (1 - vs) * 3
                if best is None or score < best[0]: best = (score, views, bad, vs)
    return best[1], best[2], best[3]

def render(sh):
    n = sh["n"]; w = writer(OUT + sh["clip"]); info = ""
    if sh["src"] == "BFM":                                   # capture JT 9:16 plein écran : image recadrée sur Boyard + bandeau URGENT en 2 lignes
        k = 0
        for fr in read_frames("BFM", sh["t_in"], n, 1280, 720):
            src = fr.astype(np.float32) / 255
            z = 1.0 + 0.02 * k / max(n - 1, 1); vh = 548 / z; vw = vh * 9 / 16   # au-dessus du bandeau (y < 552), sans logo ni micros siglés
            img = crop_view(src[:552], 770, 548 - vh / 2 - 2, vw, W, H)
            img = grade(img)
            # bandeau réduit et centré dans la zone sûre TikTok : 650 px de large (x 0,20-0,80), bas à 1390 px (0,724)
            BW = 650; BH = int(round(76 * BW / 844)); B1 = int(round(344 * BW / 844)); bx = (W - BW) // 2
            r1 = cv2.resize(src[552:628, 0:344], (B1, BH), interpolation=cv2.INTER_AREA)            # URGENT | LYCÉES :
            r2 = cv2.resize(src[552:628, 346:1190], (BW, BH), interpolation=cv2.INTER_AREA)         # LOUIS BOYARD RÉAGIT EN DIRECT SUR BFMTV
            y1 = 1390 - 2 * BH; img[y1:y1 + BH, bx:bx + B1] = r1; img[y1 + BH:y1 + 2 * BH, bx:bx + BW] = r2
            fo = (n - k) / (FADE_S * 30)
            if fo < 1: img *= max(fo, 0)
            w.stdin.write((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8).tobytes()); k += 1
        w.stdin.close(); w.wait(); return "document, %d images" % k
    s = int(round(sh["t_in"] * SFPS)); speed = SFPS / 30; bd = BOUNDS[sh["src"]]
    vh = min(bd[3] - bd[1], (bd[2] - bd[0]) * 16 / 9)
    if sh["auto"]:
        views, bad, vs = auto_view(sh, s, n, speed); info = "auto, vue %.0f%%, visages coupés estimés %d" % (vs * 100, bad)
    else:
        zoom = lambda f: sh["z0"] * (1.0 + (sh["z1"] - 1.0) * f / max(n - 1, 1))
        views, ok = plan_views(SRC[sh["src"]], s, n, SFPS, speed=speed, hint=sh["hint"], bounds=bd, vh=vh, zoom=zoom, top=0.16)
        info = "visage" if ok else "SANS VISAGE"
    k = 0
    for fr in read_frames(sh["src"], sh["t_in"], n):
        cx, cy, v = views[min(k, len(views) - 1)]; vw = v * 9 / 16
        assert bd[0] - 1 <= cx - vw / 2 and cx + vw / 2 <= bd[2] + 1 and bd[1] - 1 <= cy - v / 2 and cy + v / 2 <= bd[3] + 1, (sh["id"], k, cx, cy, v)
        img = grade(crop_view(fr.astype(np.float32) / 255, cx, cy, vw, W, H))
        if sh["txt"]: img = draw_text(img, sh["a"] + k / 30)
        w.stdin.write((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8).tobytes()); k += 1
    w.stdin.close(); w.wait()
    sh["views"] = [(round(a, 1), round(b, 1), round(c, 1)) for a, b, c in (views[0], views[-1])]
    return info + " ; vue %d->%d px (x%.2f)" % (views[0][2], views[-1][2], 1920 / views[-1][2]) + ("" if k == n else " COURT %d/%d" % (k, n))

# ---------------- audio ----------------
SR = 48000
MUSIC = L3 + "/sons/K1-smooth-criminal_complet.wav"
def load(path, t=0.0, d=None):
    cmd = [FF, "-v", "error", "-ss", "%.4f" % t, "-i", path] + (["-t", "%.4f" % d] if d else []) + ["-vn", "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"]
    return np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, np.float32).reshape(-1, 2).copy()
def fade(x, fi, fo):
    a = np.ones(len(x), np.float32)
    if fi: k = int(fi * SR); a[:k] *= np.linspace(0, 1, k)
    if fo: k = int(fo * SR); a[-k:] *= np.linspace(1, 0, k)
    return x * a[:, None]
def sf_write(p, x):
    import soundfile as sf; sf.write(p, x, SR, subtype="PCM_24")
def lufs(x):
    p = OUT + "_tmp_meas.wav"; sf_write(p, x)
    r = subprocess.run([FF, "-v", "info", "-i", p, "-af", "loudnorm=print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
    js = json.loads(r[r.rindex("{"):r.rindex("}") + 1]); os.remove(p)
    return float(js["input_i"]), float(js["input_tp"])
def db(g): return 10 ** (g / 20)
# blocs de voix contigus (même décalage) : phrases A+B, C, D, E, F
VBLOCKS = []
for i, (a, b) in enumerate(TM["segs"]):
    if VBLOCKS and abs(SH[i] - VBLOCKS[-1][2]) < 1e-6: VBLOCKS[-1][1] = b
    else: VBLOCKS.append([a, b, SH[i]])
DUCK = -10.0
def build_audio():
    n = int(round(END * SR)); voice = np.zeros((n, 2), np.float32)
    for a, b, shf in VBLOCKS:
        x = fade(load(L3 + "/sources/" + SRC["LCP"], a - 0.04 - 90.0, b - a + 0.16), 0.015, 0.03)
        p = int(round((a - 0.04 - 94.28 + shf) * SR)); voice[p:p + len(x)] += x[:n - p]
    mus = load(MUSIC, M0, END + 0.05)[:n]
    lv, _ = lufs(voice[int(O * SR):int(VEND * SR)]); lm, _ = lufs(mus)
    voice *= db(-14 - lv); mus *= db(-14 - lm)
    t = np.arange(n) / SR
    d0, d1 = O - 0.12, VEND + 0.12
    env = np.ones(n, np.float32)
    env = np.where(t < d0, 1.0, env)
    env = np.where((t >= d0) & (t < d0 + 0.15), 1 - (1 - db(DUCK)) * (t - d0) / 0.15, env)
    env = np.where((t >= d0 + 0.15) & (t < d1), db(DUCK), env)
    env = np.where((t >= d1) & (t < d1 + 0.25), db(DUCK) + (1 - db(DUCK)) * (t - d1) / 0.25, env)
    env *= np.where(t > END - FADE_S, np.clip((END - t) / FADE_S, 0, 1), 1)
    mix = mus * env[:, None].astype(np.float32) + voice
    tmp = OUT + "_tmp_mix.wav"; sf_write(tmp, mix); g = 0.0; li2 = None
    for _ in range(4):
        li = lufs(mix)[0] if li2 is None else li2
        g += -14.0 - li
        subprocess.run([FF, "-v", "error", "-y", "-i", tmp, "-af", "volume=%.2fdB,alimiter=limit=0.70:attack=3:release=60:level=false,aresample=192000,alimiter=limit=0.71:attack=1:release=40:level=false,aresample=48000" % g,
                        "-c:a", "pcm_s24le", OUT + "K1-mix.wav"], check=True)
        li2, tp2 = lufs(load(OUT + "K1-mix.wav"))
        if abs(li2 + 14) < 0.3 and tp2 < -2.2: break
    os.remove(tmp)
    sf_write(OUT + "K1-voix.wav", voice); sf_write(OUT + "K1-musique.wav", mus)
    return "mix %.1f LUFS, true peak %.1f dBTP (voix d'origine %.1f, musique d'origine %.1f LUFS, ducking %.0f dB)" % (li2, tp2, lv, lm, DUCK)

# ---------------- plan-K1.json + son.json ----------------
def write_plan():
    vid = []
    for sh in SHOTS:
        u, off, ch, date = URL[sh["src"]]
        it = {"id": sh["id"], "clip": sh["clip"], "folder": "genK1", "path": OUT + sh["clip"], "s": 0, "e": sh["n"], "clip_fps": 30, "speed_pct": 100,
              "rec": sh["rec"], "dur": sh["dur"], "track": 1, "note": sh["note"],
              "source": {"fichier": "lot3/sources/" + SRC[sh["src"]], "in_s": round(sh["t_in"], 3), "out_s": round(sh["t_in"] + sh["n"] / 30, 3),
                         "url": u, "temps_url_s": round(off + sh["t_in"], 2), "chaine": ch, "date": date},
              "effets": "capture plein écran 9:16 : image recadrée sur Boyard (sans logo de coin ni micros siglés) + bandeau URGENT découpé en 2 lignes (sans bandeau défilant), poussée 1,00->1,02, fondu au noir %.1f s" % FADE_S if sh["src"] == "BFM" else
                        "recadrage 9:16 (%s, bornes %s), poussée lente 1->%.2f, étalonnage couleur doux + vignette + grain%s" % (
                            "centre fixe sans visage coupé" if sh["auto"] else "suivi du visage", list(BOUNDS[sh["src"]]), sh["z1"], ", sous-titres cuits" if sh["txt"] else "")}
        if "views" in sh: it["vues_debut_fin"] = sh["views"]
        vid.append(it)
    plan = {"name": "K1 - Karaoké discours - Boyard", "fps": 30, "w": 1080, "h": 1920, "duree_s": round(f30(END) / 30, 3),
            "note": "Plans ProRes 1080x1920 30 i/s prêts (recadrés, étalonnés, sous-titres cuits). Aucun ralenti. Générateur : lot3/_claude/gen/K1/genK1.py ; calage : timing.py",
            "phrase": {"texte": "La jeunesse vient de prendre conscience d'elle-même. Vous avez été trop loin. Elle s'est déjà trop sacrifiée pour reculer maintenant. Alors, monsieur le ministre de l'Éducation nationale, acceptez que vous avez perdu, que les jeunes ont raison depuis le début.",
                       "source_url": URL["LCP"][0], "in_s_url": 94.28, "out_s_url": 107.66, "chaine": "LCP - Assemblée nationale", "date": "2026-10-06",
                       "blocs_voix_timeline": [{"url_in": round(a - 0.04, 2), "url_out": round(b + 0.12, 2), "timeline_in": round(a - 0.04 - 94.28 + s, 3)} for a, b, s in VBLOCKS]},
            "textes": {"police": "Avenir Next Heavy Italic", "couleur": "#FFD700", "taille": "jusqu'à 150 px (1 à 3 lignes, bloc ≤ 58 % de large)", "position": "bas-centre, bas du bloc à 71,5 % (zone sûre TikTok)", "contour": "sombre net + ombre douce, pas de fond", "guillemets": "aucun",
                       "fragments": [{"t0": round(f["ds"], 3), "t1": round(f["de"], 3), "texte": f["txt"]} for f in FRAGS]},
            "video": vid,
            "audio": [{"id": "mix", "clip": "K1-mix.wav", "folder": "genK1", "path": OUT + "K1-mix.wav", "rec": 0, "track": 1,
                       "note": "mix -14 LUFS : musique seule %.2f s, voix (blocs %s) avec musique %d dB dessous, musique pleine après « début » (rafale + document), fondu %.1f s" % (
                           O, ", ".join("%.2f-%.2f" % (a, b) for a, b, s in VBLOCKS), DUCK, FADE_S)}]}
    json.dump(plan, open(D + "plan-K1.json", "w"), indent=1, ensure_ascii=False)
    son = {"titre": "Smooth Criminal", "artiste": "Michael Jackson", "url": "https://youtu.be/h_D3VFfhvs4", "chaine": "Michael Jackson (officielle)",
           "fichier": "lot3/sons/K1-smooth-criminal_complet.wav (audio du clip officiel, 9:26)",
           "extrait_debut_s": round(M0, 3), "extrait_fin_s": round(M0 + END, 3), "contenu": "fin du pont + refrain Annie, are you OK (160,3-170 s, sous la voix, -10 dB) puis hook You've been hit by, you've been struck by a smooth criminal (172,37-176,68 s) à pleine puissance, retour du groove (176,44 s), fin sur la frappe forte 179,495 s (instrumental, aucun mot chanté), fondu 0,4 s",
           "bpm": round(60 / TM["period"], 2), "drop": "You've been hit by : %.3f s dans le complet = %.3f s timeline (Whisper : you've 172,48, hit 173,28, smooth criminal 175,78-176,30)" % (TM["drop_c"], DROP_T),
           "frappes_timeline_s": [round(h, 3) for h in HITS if h <= END + 0.01],
           "coupes_timeline_s": [round(sh["a"], 3) for sh in SHOTS[1:]] + [round(END, 3)]}
    json.dump(son, open(D + "son.json", "w"), indent=1, ensure_ascii=False)

# ---------------- aperçu 540x960 ----------------
def preview():
    out = HK + "/preview/apercu-K1.mp4"; args = [FF, "-v", "error", "-y"]; fl = []
    for i, sh in enumerate(SHOTS):
        args += ["-i", OUT + sh["clip"]]
        fl.append("[%d:v]trim=end_frame=%d,setpts=PTS-STARTPTS,scale=540:960,setsar=1[v%d]" % (i, sh["dur"], i))
    args += ["-i", OUT + "K1-mix.wav"]
    fl.append("".join("[v%d]" % i for i in range(len(SHOTS))) + "concat=n=%d:v=1:a=0[v]" % len(SHOTS))
    args += ["-filter_complex", ";".join(fl), "-map", "[v]", "-map", "%d:a" % len(SHOTS), "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", "-r", "30",
             "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out]
    subprocess.run(args, check=True); return out

if __name__ == "__main__":
    only = None
    for a in sys.argv:
        if a.startswith("only="): only = a[5:].split(",")
    for f in FRAGS: print("%-30s %.3f-%.3f (mot %.3f)" % (f["txt"], f["ds"], f["de"], f["w0"]))
    if "plans" in sys.argv:
        for sh in SHOTS:
            if only and sh["id"] not in only: continue
            print(sh["id"], "%.3f-%.3f" % (sh["a"], sh["b"]), sh["dur"], "img", render(sh), flush=True)
    if "audio" in sys.argv: print(build_audio())
    write_plan()
    if "apercu" in sys.argv: print(preview())
    print("total %.3f s ; %d plans ; voix %.2f-%.2f" % (END, len(SHOTS), O, VEND))
