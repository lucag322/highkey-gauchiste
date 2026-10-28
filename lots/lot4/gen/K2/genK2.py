# Lot 4 / K2 — Karaoké discours (recette editsofourtimes, modèle lot3 K1 corrigé), Éric Coquerel, Clara Luciani – La grenade.
# Montée (couplet « Et je te montrerai / Comme je mords, comme j'aboie ») sous la voix, drop sur le refrain « Prends garde, sous mon sein la grenade ».
# Phrase réelle mot à mot : discours PLF 2026 à l'Assemblée, 24/10/2025 (chaîne Eric Coquerel), « L'essence du texte n'a pas changé.
# Il demandait toujours trop à ceux qui ont peu et toujours trop peu à ceux qui ont beaucoup. »
# Structure : plan long d'ouverture synchro, puis 1 plan par fragment (banc des ministres, gestes, public populaire, retour synchro),
# rafale d'1 temps sur « Prends garde », puis document d'époque plein écran (BFMTV 24/10/2025, LA BATAILLE DU BUDGET EST LANCÉE).
# Sous-titres jaune #FFD700, Avenir Next Heavy Italic gros et gras, bas-centre, mot à mot, sans guillemets (comme K1 corrigé).
# Coupes sur les vraies frappes (timing.py -> timing.json). Pas de ralenti. Usage : python genK2.py [plans] [audio] [apercu] [only=ID,..]
import sys, os, json, subprocess
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
HK = "/Users/luca.grousset/Movies/highkey-gauchiste"
L4 = HK + "/lot4"
sys.path.insert(0, HK + "/_claude/outils")
import framing
D = L4 + "/_claude/gen/K2/"; OUT = D + "out/"; os.makedirs(OUT, exist_ok=True)
framing.ROOT = L4; framing.CACHE = D + "cache/faces/a/b"
from framing import plan_views, detect, head_box
from fx import crop_view, gblur, over, vignette, grain
from words import tokens, clean
FF = "/opt/homebrew/bin/ffmpeg"
W, H, TFPS = 1080, 1920, 30
TM = json.load(open(D + "timing.json"))
M0 = TM["M0"]; VT = TM["voice_tl"]; SEG = TM["seg"]
HITS = [h - M0 for h in TM["hits_complet"]]
def hit(t): return min(HITS, key=lambda h: abs(h - t))
def f30(t): return int(round(t * TFPS))

SRC = {"TX": "K2-coquerel-hemicycle-plf-texte.mp4", "BANC": "K2-coquerel-hemicycle-plf-banc.mp4", "G1": "K2-coquerel-hemicycle-plf-geste1.mp4",
       "G2": "K2-coquerel-hemicycle-plf-geste2.mp4", "SD2": "../../lot2/sources/C2-coquerel-stdenis-02.mp4", "SD3": "../../lot2/sources/C2-coquerel-stdenis-03.mp4",
       "BFM": "K2-coquerel-bfmtv-bataille-budget.mp4", "SALLE": "K2-coquerel-stdenis-salle.mp4", "FIN": "K2-coquerel-stdenis-fin.mp4",
       "PU1": "K2-coquerel-stdenis-pupitre1.mp4", "PU2": "K2-coquerel-stdenis-pupitre2.mp4", "PU3": "K2-coquerel-stdenis-pupitre3.mp4"}
AN = ("https://www.youtube.com/watch?v=v6HH2QrtogU", "Eric Coquerel (discours PLF 2026, Assemblée nationale)", "2025-10-24")
SDN = ("https://www.youtube.com/watch?v=JqMnuzxTXGI", "Eric Coquerel (meeting Saint-Denis/Pierrefitte)", "2026-03-10")
URL = {"TX": AN + (470.0,), "BANC": AN + (50.0,), "G1": AN + (128.0,), "G2": AN + (224.0,), "SD2": SDN + (62.3,), "SD3": SDN + (143.5,), "SALLE": SDN + (0.0,), "FIN": SDN + (201.5,), "PU1": SDN + (114.8,), "PU2": SDN + (162.0,), "PU3": SDN + (193.0,),
       "BFM": ("https://www.youtube.com/watch?v=e4pPUY6q7QU", "BFMTV (interview d'Éric Coquerel)", "2025-10-24", 1440.0)}
SFPS = {"TX": 60, "BANC": 60, "G1": 60, "G2": 60, "SD2": 30, "SD3": 30, "BFM": 25, "SALLE": 30, "FIN": 30, "PU1": 30, "PU2": 30, "PU3": 30}
# zones source sans logo / drapeau d'antenne / L'ESPOIR / logo LFI
BOUNDS = {"TX": (0, 32, 1920, 1080), "BANC": (0, 32, 1920, 1080), "G1": (0, 32, 1920, 1080), "G2": (0, 32, 1920, 1080),
          "SD2": (0, 140, 1920, 1080), "SD3": (0, 140, 1920, 1080),
          "SALLE": (270, 0, 1670, 1080), "FIN": (270, 0, 1670, 1080),
          "PU1": (300, 0, 1690, 830), "PU2": (300, 0, 1690, 830), "PU3": (300, 0, 1690, 830)}   # pupitre : sans le panneau MEETING SAINT-DENIS (y > 835)          # salle : exclut L'ESPOIR (haut gauche) et le logo LFI (haut droite)

# ---------------- texte : mots du transcript (whisper large-v3-turbo, mot à mot) ----------------
TXW = json.load(open(D + "tx/hemi.json"))
RAW = [{"w": w["word"].strip(), "start": w["start"], "end": w["end"]} for s in TXW["segments"] for w in s["words"] if SEG[0] - 0.05 <= w["start"] <= SEG[1]]
T = tokens(RAW)
SIZES = [3, 3, 2, 2, 5, 4, 5]
assert sum(SIZES) == len(T), (len(T), [t["w"] for t in T])
FR = TM["frag"]; CUT_FROM = TM["cut_from"]
def tl(orig): return orig - SEG[0] + VT                       # temps de l'extrait -> timeline
def disp(w): return clean(w, keep_quotes=False).replace("'", "’")
FRAGS, i = [], 0
for k, z in enumerate(SIZES):
    ws = T[i:i + z]; i += z
    FRAGS.append({"txt": FR[k][0], "words": [(disp(t["w"]), tl(t["start"])) for t in ws], "w0": tl(ws[0]["start"]), "end_voice": tl(ws[-1]["end"])})
    assert " ".join(disp(t["w"]) for t in ws) == FR[k][0], (FR[k][0], [t["w"] for t in ws])
CUTS = [hit(FRAGS[k]["w0"] - 0.06) for k in range(CUT_FROM, len(FRAGS))]
for k, f in enumerate(FRAGS): f["ds"] = CUTS[k - CUT_FROM] if k >= CUT_FROM else f["w0"]
VEND = FRAGS[-1]["end_voice"]
DROP_T = hit(TM["drop_c"] - M0)                                # « Prends garde »
RCUTS = [DROP_T, hit(DROP_T + 0.46), hit(DROP_T + 0.92), hit(DROP_T + 1.38)]   # rafale Prends | garde | (sous) | document
END = hit(TM["end_c"] - M0)                                    # frappe après « grenade »
for k, f in enumerate(FRAGS): f["de"] = FRAGS[k + 1]["ds"] if k + 1 < len(FRAGS) else DROP_T

FONT = ("/System/Library/Fonts/Avenir Next.ttc", 9)            # Avenir Next Heavy Italic (K1 corrigé : plus gros, plus gras)
YEL = np.array([0, 215, 255], np.float32) / 255                # #FFD700 en BGR
EM_MAX, WFRAC, YB = 150, 0.60, 0.715          # zone sûre TikTok : bloc ≤ 66 % de large (x 0,17-0,83), bas du bloc ≤ 0,75
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
    sh1 = np.clip(gblur(o, 12) * 1.5, 0, 1) * 0.55
    sh2 = np.clip(gblur(o, 1.0), 0, 1) * 0.92
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
def S(i, src, a, b, t_in, hint=None, auto=False, note="", z1=1.06, txt=False, z0=1.0, fixed=None):
    return dict(id=i, src=src, a=a, b=b, t_in=t_in, hint=hint, auto=auto, note=note, z1=z1, txt=txt, z0=z0, fixed=fixed)
C = CUTS
SYNC = lambda t: t - VT + SEG[0]                                 # timeline -> temps de l'extrait TX (image synchro de la voix)
SHOTS = [
    S("O1", "TX", 0.0, C[0], SYNC(0.0), hint=(900, 380), z1=1.12, txt=True, note="ouverture longue synchro : Coquerel à la tribune, L'essence du texte n'a pas changé"),
    S("F2", "BANC", C[0], C[1], 5.3, hint=(300, 330), txt=True, note="Il demandait : banc des ministres (Lecornu) pendant le discours"),
    S("F3", "PU1", C[1], C[2], 2.9, hint=(960, 280), txt=True, note="toujours trop : Coquerel au meeting de Saint-Denis, bras levé", z0=1.05),
    S("F4", "SALLE", C[2], C[3], 8.0, fixed=(973, 540), txt=True, note="à ceux qui ont peu : la salle populaire du meeting de Saint-Denis, Coquerel au pupitre au fond"),
    S("F5", "PU2", C[3], C[4], 4.9, hint=(960, 280), txt=True, note="et toujours trop peu : Coquerel au meeting de Saint-Denis, mains levées", z0=1.05),
    S("F6", "TX", C[4], RCUTS[0], SYNC(C[4]), hint=(900, 380), txt=True, note="à ceux qui ont beaucoup : retour synchro, regard vers l'hémicycle", z0=1.15),
    S("R1", "FIN", RCUTS[0], RCUTS[1], 1.0, fixed=(1350, 540), z1=1.04, note="drop Prends : salle de Saint-Denis debout, drapeaux"),
    S("R2", "TX", RCUTS[1], RCUTS[2], 44.3, auto=True, note="rafale garde : plan large de l'hémicycle"),
    S("R3", "PU3", RCUTS[2], RCUTS[3], 3.3, hint=(960, 280), note="rafale garde : Coquerel au meeting de Saint-Denis, bras levé", z0=1.1),
    S("DOC", "BFM", RCUTS[3], END, 14.9, note="la grenade : document d'époque plein écran, BFMTV 24/10/2025, LA BATAILLE DU BUDGET EST LANCÉE"),
]
FADE_S = 0.4
for sh in SHOTS:
    sh["rec"] = f30(sh["a"]); sh["dur"] = f30(sh["b"]) - sh["rec"]; sh["n"] = sh["dur"]; sh["clip"] = "K2_%s.mov" % sh["id"]

def read_frames(src, t, n, w=1920, h=1080):
    p = subprocess.Popen([FF, "-v", "error", "-ss", "%.4f" % t, "-i", os.path.normpath(L4 + "/sources/" + SRC[src]), "-vf", "fps=30", "-frames:v", str(n),
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

def cut_faces(faces, views, thr=0.05):
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
    fps = SFPS[sh["src"]]
    faces = detect(SRC[sh["src"]], s, int(n * speed) + 2, fps); faces = [faces[min(int(f * speed), len(faces) - 1)] for f in range(n)]
    best = None
    for vs in (1.0, 0.92, 0.85, 0.78, 0.7):
        v0 = vmax * vs; vw0 = v0 * 9 / 16
        for cy in sorted({bd[1] + v0 / 2, (bd[1] + bd[3]) / 2, bd[3] - v0 / 2}):
            for cx in np.arange(bd[0] + vw0 / 2, bd[2] - vw0 / 2 + 1, 12):
                views = [(cx, cy, v0 / (1 + (sh["z1"] - 1) * f / max(n - 1, 1))) for f in range(n)]
                bad = cut_faces(faces, views)
                score = bad * 1000 + abs(cx - (bd[0] + bd[2]) / 2) / 400 + (1 - vs) * 3
                if best is None or score < best[0]: best = (score, views, bad, vs)
    return best[1], best[2], best[3]

def render(sh):
    n = sh["n"]; w = writer(OUT + sh["clip"]); info = ""
    if sh["src"] == "BFM":   # capture JT 9:16 plein écran : image recadrée sur Coquerel (sans logo BFMTV) + titre et bandeau nom découpés
        from crowd import detect_full
        fl = detect_full(os.path.normpath(L4 + "/sources/" + SRC["BFM"]), sh["t_in"], n, "BFM", step=3)
        xs = [max(fl_, key=lambda f: f[2])[0] + max(fl_, key=lambda f: f[2])[2] / 2 if fl_ else None for fl_ in fl]
        kn = [i for i, x in enumerate(xs) if x is not None]
        xs = [xs[i] if xs[i] is not None else xs[min(kn, key=lambda j: abs(j - i))] for i in range(len(xs))]
        fx_ = np.interp(np.arange(n), np.arange(len(xs)) * 3, xs)
        fx_ = np.convolve(np.pad(fx_, 7, mode="edge"), np.ones(15) / 15, mode="valid")
        k = 0
        for fr in read_frames("BFM", sh["t_in"], n, 1280, 720):
            src = fr.astype(np.float32) / 255
            z = 1.0 + 0.03 * k / max(n - 1, 1); vh = 518 / z; vw = vh * 9 / 16       # au-dessus du bandeau nom (y < 520)
            cx = float(np.clip(fx_[k], 190 + vw / 2, 1280 - vw / 2))                   # suit le visage, logo BFMTV (x < 185) exclu
            img = grade(crop_view(src[:518], cx, 518 - vh / 2 - 1, vw, W, H))
            # bandeaux dans la zone sûre TikTok : x 0,17-0,83 (≤ 713 px de large), bas ≤ 0,75 de la hauteur
            st_ = 1.45; t1 = cv2.resize(src[562:620, 50:504], (int(454 * st_), int(58 * st_)), interpolation=cv2.INTER_CUBIC)   # LA BATAILLE DU BUDGET
            t2 = cv2.resize(src[562:620, 503:736], (int(233 * st_), int(58 * st_)), interpolation=cv2.INTER_CUBIC)              # EST LANCÉE
            sc = 660 / 555
            r1 = cv2.resize(src[521:556, 57:533], (int(476 * sc), int(35 * sc)), interpolation=cv2.INTER_CUBIC)   # Éric Coquerel Député LFI de Seine-Saint-Denis,
            r2 = cv2.resize(src[521:556, 531:1086], (int(555 * sc), int(35 * sc)), interpolation=cv2.INTER_CUBIC) # président de la commission des finances à l'Assemblée
            x0 = (W - 660) // 2; yb = int(0.735 * H)
            y4 = yb - t2.shape[0]; y3 = y4 - t1.shape[0]; y2 = y3 - 10 - r2.shape[0]; y1 = y2 - r1.shape[0]
            for im_, yy in ((r1, y1), (r2, y2), (t1, y3), (t2, y4)): img[yy:yy + im_.shape[0], x0:x0 + im_.shape[1]] = im_
            fo = (n - k) / (FADE_S * 30)
            if fo < 1: img *= max(fo, 0)
            w.stdin.write((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8).tobytes()); k += 1
        w.stdin.close(); w.wait(); return "document, %d images" % k
    fps = SFPS[sh["src"]]; s = int(round(sh["t_in"] * fps)); speed = fps / 30; bd = BOUNDS[sh["src"]]
    vh = min(bd[3] - bd[1], (bd[2] - bd[0]) * 16 / 9)
    if sh["fixed"]:
        views = [(sh["fixed"][0], sh["fixed"][1], vh / (1 + (sh["z1"] - 1) * f / max(n - 1, 1))) for f in range(n)]; info = "centre fixe (visages de dos ou < 6 %)"
    elif sh["auto"]:
        views, bad, vs = auto_view(sh, s, n, speed); info = "auto, vue %.0f%%, visages coupés estimés %d" % (vs * 100, bad)
    else:
        zoom = lambda f: sh["z0"] * (1.0 + (sh["z1"] - 1.0) * f / max(n - 1, 1))
        views, ok = plan_views(SRC[sh["src"]], s, n, fps, speed=speed, hint=sh["hint"], bounds=bd, vh=vh, zoom=zoom, top=0.16)
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
    return info + " ; vue %d->%d px (x%.2f)" % (views[0][2], views[-1][2], 1080 / views[-1][2]) + ("" if k == n else " COURT %d/%d" % (k, n))

# ---------------- audio ----------------
SR = 48000
MUSIC = L4 + "/sons/K2-la-grenade_complet.wav"
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
DUCK = -10.0
VA, VB = SEG[0] - 0.05, SEG[1] + 0.12                            # bloc de voix (pauses d'origine)
def build_audio():
    n = int(round(END * SR)); voice = np.zeros((n, 2), np.float32)
    x = fade(load(L4 + "/sources/" + SRC["TX"], VA, VB - VA), 0.015, 0.04)
    p = int(round(tl(VA) * SR)); voice[p:p + len(x)] += x[:n - p]
    mus = load(MUSIC, M0, END + 0.05)[:n]
    lv, _ = lufs(voice[int(tl(SEG[0]) * SR):int(VEND * SR)]); lm, _ = lufs(mus)
    voice *= db(-14 - lv); mus *= db(-14 - lm)
    t = np.arange(n) / SR
    d0, d1 = tl(SEG[0]) - 0.12, VEND + 0.08
    env = np.ones(n, np.float32)
    env = np.where((t >= d0) & (t < d0 + 0.15), 1 - (1 - db(DUCK)) * (t - d0) / 0.15, env)
    env = np.where((t >= d0 + 0.15) & (t < d1), db(DUCK), env)
    env = np.where((t >= d1) & (t < DROP_T), db(DUCK) + (1 - db(DUCK)) * (t - d1) / max(DROP_T - d1, 0.01), env)
    env *= np.where(t > END - FADE_S, np.clip((END - t) / FADE_S, 0, 1), 1)
    mix = mus * env[:, None].astype(np.float32) + voice
    tmp = OUT + "_tmp_mix.wav"; sf_write(tmp, mix); g = 0.0; li2 = None
    for _ in range(5):
        li = lufs(mix)[0] if li2 is None else li2
        g += -14.0 - li
        subprocess.run([FF, "-v", "error", "-y", "-i", tmp, "-af", "volume=%.2fdB,alimiter=limit=0.70:attack=3:release=60:level=false,aresample=192000,alimiter=limit=0.71:attack=1:release=40:level=false,aresample=48000" % g,
                        "-c:a", "pcm_s24le", OUT + "K2-mix.wav"], check=True)
        li2, tp2 = lufs(load(OUT + "K2-mix.wav"))
        if abs(li2 + 14) < 0.3 and tp2 < -2.2: break
    os.remove(tmp)
    sf_write(OUT + "K2-voix.wav", voice); sf_write(OUT + "K2-musique.wav", mus)
    return "mix %.1f LUFS, true peak %.1f dBTP (voix d'origine %.1f, musique d'origine %.1f LUFS, ducking %.0f dB)" % (li2, tp2, lv, lm, DUCK)

# ---------------- plan-K2.json + son.json ----------------
PHRASE = "L'essence du texte n'a pas changé. Il demandait toujours trop à ceux qui ont peu et toujours trop peu à ceux qui ont beaucoup."
def write_plan():
    vid = []
    for sh in SHOTS:
        u, ch, date, off = URL[sh["src"]]
        it = {"id": sh["id"], "clip": sh["clip"], "folder": "genK2", "path": OUT + sh["clip"], "s": 0, "e": sh["n"], "clip_fps": 30, "speed_pct": 100,
              "rec": sh["rec"], "dur": sh["dur"], "track": 1, "note": sh["note"],
              "source": {"fichier": os.path.relpath(os.path.normpath(L4 + "/sources/" + SRC[sh["src"]]), HK), "in_s": round(sh["t_in"], 3), "out_s": round(sh["t_in"] + sh["n"] / 30, 3),
                         "url": u, "temps_url_s": round(off + sh["t_in"], 2), "chaine": ch, "date": date},
              "effets": "capture plein écran 9:16 : image recadrée sur Coquerel (suivi horizontal du visage, sans logo BFMTV ni bandeau défilant) + bandeau nom en 2 lignes + titre LA BATAILLE DU BUDGET / EST LANCÉE en 2 lignes, bloc dans la zone sûre TikTok (x 0,17-0,83, y ≤ 0,735), poussée 1,00->1,03, fondu au noir %.1f s" % FADE_S if sh["src"] == "BFM" else
                        "recadrage 9:16 (%s, bornes %s), poussée lente %.2f->%.2f, étalonnage couleur doux + vignette + grain%s" % (
                            "centre fixe sans visage coupé" if (sh["auto"] or sh["fixed"]) else "suivi du visage", list(BOUNDS[sh["src"]]), sh["z0"], sh["z0"] * sh["z1"], ", sous-titres cuits" if sh["txt"] else "")}
        if "views" in sh: it["vues_debut_fin"] = sh["views"]
        vid.append(it)
    plan = {"name": "K2 - Karaoké discours - Coquerel", "fps": 30, "w": 1080, "h": 1920, "duree_s": round(f30(END) / 30, 3),
            "note": "Plans ProRes 1080x1920 30 i/s prêts (recadrés, étalonnés, sous-titres cuits). Aucun ralenti. Générateur : lot4/_claude/gen/K2/genK2.py ; calage : timing.py",
            "phrase": {"texte": PHRASE, "source_url": AN[0], "in_s_url": round(470 + SEG[0], 2), "out_s_url": round(470 + SEG[1], 2), "chaine": "Eric Coquerel (chaîne officielle)", "date": "2025-10-24",
                       "blocs_voix_timeline": [{"url_in": round(470 + VA, 2), "url_out": round(470 + VB, 2), "timeline_in": round(tl(VA), 3)}]},
            "textes": {"police": "Avenir Next Heavy Italic", "couleur": "#FFD700", "taille": "jusqu'à 150 px (1 à 3 lignes), bloc ≤ 60 % de large", "position": "bas-centre, bas du bloc à 71,5 % (zone sûre TikTok)", "contour": "sombre net + ombre douce, pas de fond", "guillemets": "aucun",
                       "fragments": [{"t0": round(f["ds"], 3), "t1": round(f["de"], 3), "texte": f["txt"]} for f in FRAGS]},
            "video": vid,
            "audio": [{"id": "mix", "clip": "K2-mix.wav", "folder": "genK2", "path": OUT + "K2-mix.wav", "rec": 0, "track": 1,
                       "note": "mix -14 LUFS : musique seule %.2f s, voix %.2f-%.2f s avec musique %d dB dessous, remontée jusqu'au drop %.3f s (Prends garde), fondu %.1f s" % (
                           tl(SEG[0]), tl(SEG[0]), VEND, DUCK, DROP_T, FADE_S)}]}
    json.dump(plan, open(D + "plan-K2.json", "w"), indent=1, ensure_ascii=False)
    son = {"titre": "La grenade", "artiste": "Clara Luciani", "url": "https://youtu.be/85m-Qgo9_nE", "chaine": "Clara Luciani (clip officiel)",
           "fichier": "lot4/sons/K2-la-grenade_complet.wav (audio du clip officiel, 3:15)",
           "extrait_debut_s": round(M0, 3), "extrait_fin_s": round(M0 + END, 3),
           "contenu": "couplet Et je te montrerai / Comme je mords, comme j'aboie (33,9-39,9 s, sous la voix, -10 dB) puis refrain Prends garde, sous mon sein la grenade (41,9-47,0 s) à pleine puissance, fin sur la frappe après grenade",
           "bpm": round(60 / TM["period"], 2), "drop": "Prends garde : %.3f s dans le complet = %.3f s timeline (Whisper : Prends 41,88, garde 42,82, grenade 46,06-47,00)" % (TM["drop_c"], DROP_T),
           "frappes_timeline_s": [round(h, 3) for h in HITS if -0.01 <= h <= END + 0.01],
           "coupes_timeline_s": [round(sh["a"], 3) for sh in SHOTS[1:]] + [round(END, 3)]}
    json.dump(son, open(D + "son.json", "w"), indent=1, ensure_ascii=False)

# ---------------- aperçu 540x960 ----------------
def preview():
    out = HK + "/preview/apercu-K2.mp4"; args = [FF, "-v", "error", "-y"]; fl = []
    for i, sh in enumerate(SHOTS):
        args += ["-i", OUT + sh["clip"]]
        fl.append("[%d:v]trim=end_frame=%d,setpts=PTS-STARTPTS,scale=540:960,setsar=1[v%d]" % (i, sh["dur"], i))
    args += ["-i", OUT + "K2-mix.wav"]
    fl.append("".join("[v%d]" % i for i in range(len(SHOTS))) + "concat=n=%d:v=1:a=0[v]" % len(SHOTS))
    args += ["-filter_complex", ";".join(fl), "-map", "[v]", "-map", "%d:a" % len(SHOTS), "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", "-r", "30",
             "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out]
    subprocess.run(args, check=True); return out

if __name__ == "__main__":
    only = None
    for a in sys.argv:
        if a.startswith("only="): only = a[5:].split(",")
    for f in FRAGS: print("%-26s %.3f-%.3f (mot %.3f)" % (f["txt"], f["ds"], f["de"], f["w0"]))
    print("rafale", ["%.3f" % r for r in RCUTS], "fin %.3f" % END)
    if "plans" in sys.argv:
        for sh in SHOTS:
            if only and sh["id"] not in only: continue
            print(sh["id"], "%.3f-%.3f" % (sh["a"], sh["b"]), sh["dur"], "img", render(sh), flush=True)
    if "audio" in sys.argv: print(build_audio())
    write_plan()
    if "apercu" in sys.argv: print(preview())
    print("total %.3f s ; %d plans ; voix %.2f-%.2f" % (END, len(SHOTS), tl(SEG[0]), VEND))
