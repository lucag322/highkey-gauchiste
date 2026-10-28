# Lot 5 / K3 — Karaoké discours (recette editsofourtimes, modèles lot3 K1 et lot4 K2), Clémence Guetté, Kendrick Lamar – HUMBLE.
# Montée (couplet « If I quit this season… / My left stroke just went viral / … you and I know ») sous la voix, drop sur le refrain « Bitch, be humble, sit down ».
# Phrase réelle mot à mot : meeting de Bezons, 13/02/2026 (chaîne Clémence Guetté, 9Cgr6La_XaE, 241,86-254,78 s) : « Ce sont les riches qui dessinent
# la ville, ce sont les pauvres qui construisent la ville, ce sont les riches qui privatisent les réseaux et ce sont les pauvres qui subissent
# les pollutions de ces réseaux. Et il est temps que ça change. » (autre phrase et autres plans que C1 et G6).
# Structure : plan long d'ouverture synchro, puis 1 plan par fragment (Bezons, Meaux, public), retour synchro sur « Et il est temps que ça change »,
# rafale sur « Bitch, be humble », puis document d'époque plein écran (RMC Story 08/10/2026, UNE VICTOIRE DE LFI FERAIT FUIR LE PRÉSIDENT DU MEDEF).
# Sous-titres jaune #FFD700, Avenir Next Heavy Italic, bas-centre, mot à mot, sans guillemets (comme K2).
# Coupes sur les vraies frappes (timing.py -> timing.json). Pas de ralenti. Usage : python genK3.py [plans] [audio] [apercu] [only=ID,..]
import sys, os, json, subprocess
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
HK = "/Users/luca.grousset/Movies/highkey-gauchiste"
L5 = HK + "/lot5"
sys.path.insert(0, HK + "/_claude/outils")
import framing
D = L5 + "/_claude/gen/K3/"; OUT = D + "out/"; os.makedirs(OUT, exist_ok=True)
framing.ROOT = L5; framing.CACHE = D + "cache/faces/a/b"
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

SRC = {"BZ": "K3-guette-bezons-riches.mp4", "BZ1": "../../lot2/sources/C1-guette-bezons-01.mp4", "BZ2": "../../lot2/sources/C1-guette-bezons-02.mp4",
       "ME3": "../../lot2/sources/C1-guette-meaux-03.mp4", "ME4": "../../lot2/sources/C1-guette-meaux-04.mp4", "ME6": "../../lot2/sources/C1-guette-meaux-06.mp4",
       "ME7": "../../lot2/sources/C1-guette-meaux-07.mp4", "ME8": "../../lot2/sources/C1-guette-meaux-08.mp4", "AMF": "../../lot2/sources/C1-guette-amfis-01.mp4",
       "RMC": "../../lot4/sources/G6-guette-bfmtv-2026-10-08.mp4"}
BZN = ("https://www.youtube.com/watch?v=9Cgr6La_XaE", "Clémence Guetté (meeting de Bezons)", "2026-02-13")
MXN = ("https://www.youtube.com/watch?v=Cse3O99mlR0", "Clémence Guetté (meeting de Meaux)", "2026-03-10")
AMN = ("https://www.youtube.com/watch?v=HW03wZDi6Tk", "La France insoumise (AMFIS 2026)", "2026-08-20")
URL = {"BZ": BZN + (232.0, ), "BZ1": BZN + (None, ), "BZ2": BZN + (None, ), "ME3": MXN + (None, ), "ME4": MXN + (None, ), "ME6": MXN + (None, ),
       "ME7": MXN + (None, ), "ME8": MXN + (None, ), "AMF": AMN + (None, ),
       "RMC": ("https://www.youtube.com/watch?v=YTteQi-qY9w", "RMC Story, Apolline Matin (interview de Clémence Guetté)", "2026-10-08", 0.0)}
SFPS = {"BZ": 25, "BZ1": 25, "BZ2": 25, "ME3": 25, "ME4": 25, "ME6": 25, "ME7": 25, "ME8": 25, "AMF": 60, "RMC": 25}
# zones source sans logo LFI (haut droite, x > 1630), sans pupitre MEETING BEZONS / MEAUX, sans affiche de campagne (Meaux, haut gauche), sans logo AMFIS (haut gauche)
BOUNDS = {"BZ": (300, 0, 1620, 845), "BZ1": (0, 0, 1620, 800), "BZ2": (0, 0, 1620, 800),
          "ME4": (0, 0, 1620, 850), "ME7": (0, 0, 1620, 850), "ME3": (600, 0, 1620, 1080), "ME8": (560, 0, 1620, 1080),
          "ME6": (0, 150, 1620, 1080), "AMF": (160, 0, 1620, 1080)}

# ---------------- texte : mots du transcript (whisper large-v3-turbo, mot à mot) ----------------
TXW = json.load(open(D + "tx/bezons.json"))
RAW = [{"w": w["word"].strip(), "start": w["start"], "end": w["end"]} for s in TXW["segments"] for w in s["words"] if SEG[0] - 0.05 <= w["start"] <= SEG[1] - 0.1]
T = tokens(RAW)
SIZES = [4, 4, 4, 4, 4, 4, 5, 4, 3, 7]
assert sum(SIZES) == len(T), (len(T), [t["w"] for t in T])
FR = TM["frag"]; CUT_FROM = TM["cut_from"]
def tl(orig): return orig - SEG[0] + VT                       # temps de l'extrait -> timeline
def disp(w): return clean(w, keep_quotes=False).replace("'", "’")
FRAGS, i = [], 0
for k, z in enumerate(SIZES):
    ws = T[i:i + z]; i += z; shown = FR[k][0].split()
    assert [disp(t["w"]).lower() for t in ws] == [s.lower() for s in shown], (FR[k][0], [t["w"] for t in ws])
    FRAGS.append({"txt": FR[k][0], "words": [(s, tl(t["start"])) for s, t in zip(shown, ws)], "w0": tl(ws[0]["start"]), "end_voice": tl(ws[-1]["end"])})
CUTS = [hit(FRAGS[k]["w0"] - 0.06) for k in range(CUT_FROM, len(FRAGS))]
for k, f in enumerate(FRAGS): f["ds"] = CUTS[k - CUT_FROM] if k >= CUT_FROM else f["w0"]
VEND = FRAGS[-1]["end_voice"]
DROP_T = hit(TM["drop_c"] - M0)                                # « Bitch, be humble »
RCUTS = [DROP_T, hit(DROP_T + 0.4), hit(DROP_T + 0.8), hit(DROP_T + 1.6)]   # rafale Bitch | be | humble | document sur « sit down »
END = hit(TM["end_c"] - M0)                                    # frappe après le 2e « sit down »
for k, f in enumerate(FRAGS): f["de"] = FRAGS[k + 1]["ds"] if k + 1 < len(FRAGS) else DROP_T

FONT = ("/System/Library/Fonts/Avenir Next.ttc", 9)            # Avenir Next Heavy Italic (comme K2)
YEL = np.array([0, 215, 255], np.float32) / 255                # #FFD700 en BGR
EM_MAX, WFRAC, YB = 150, 0.60, 0.715          # zone sûre TikTok : bloc ≤ 60 % de large, ≤ 150 px, bas du bloc à 0,715
_F = {}
def font(px):
    px = int(round(px))
    if px not in _F: _F[px] = ImageFont.truetype(FONT[0], px, index=FONT[1])
    return _F[px]
_L = {}
def layer(ci, nv):
    """Fragment ci avec ses nv premiers mots ; mise en page du fragment complet (1 à 3 lignes équilibrées, pas de saut)."""
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
SYNC = lambda t: t - VT + SEG[0]                                 # timeline -> temps de l'extrait BZ (image synchro de la voix)
SHOTS = [
    S("O1", "BZ", 0.0, C[0], SYNC(0.0), hint=(930, 300), z1=1.10, txt=True, note="ouverture longue synchro : Guetté au pupitre de Bezons, Ce sont les riches qui dessinent la ville, ce sont les pauvres qui construisent la ville"),
    S("F2", "ME8", C[0], C[1], 0.5, auto=True, z1=1.03, txt=True, note="ce sont les riches : le public de Meaux (personne ne parle, Guetté hors champ)"),
    S("F3", "BZ", C[1], C[2], SYNC(C[1]), hint=(930, 300), txt=True, z0=1.32, note="qui privatisent les réseaux : synchro (même source, même moment), gros plan"),
    S("F4", "ME3", C[2], C[3], 1.0, auto=True, txt=True, note="et ce sont les pauvres : le public populaire du premier rang à Meaux (bouches fermées)"),
    S("F5", "AMF", C[3], C[4], 3.5, auto=True, z1=1.03, txt=True, note="qui subissent les pollutions : AMFIS 2026, la foule de dos"),
    S("F6", "BZ", C[4], C[5], SYNC(C[4]), hint=(930, 300), txt=True, z0=1.0, z1=1.04, note="de ces réseaux : synchro (même source, même moment), plan moyen avant le resserrement sur Et il est temps"),
    S("F7", "BZ", C[5], RCUTS[0], SYNC(C[5]), hint=(930, 300), txt=True, z0=1.18, note="Et il est temps que ça change : retour synchro, plus serré"),
    S("R1", "BZ1", RCUTS[0], RCUTS[1], 1.0, hint=(830, 250), z0=1.05, note="drop Bitch (musique seule) : Bezons, penchée sur le pupitre, regard dur"),
    S("R2", "ME7", RCUTS[1], RCUTS[2], 4.0, fixed=(750, 425), z1=1.03, note="rafale be (musique seule) : Meaux, tête levée vers la salle, rampe rouge"),
    S("R3", "ME4", RCUTS[2], RCUTS[3], 1.5, hint=(640, 290), note="humble (musique seule) : Meaux, Guetté seule dans le noir, rampe rouge"),
    S("DOC", "RMC", RCUTS[3], END, 549.0, note="sit down : document d'époque plein écran, RMC Story 08/10/2026, UNE VICTOIRE DE LFI FERAIT FUIR LE PRÉSIDENT DU MEDEF"),
]
FADE_S = 0.3
for sh in SHOTS:
    sh["rec"] = f30(sh["a"]); sh["dur"] = f30(sh["b"]) - sh["rec"]; sh["n"] = sh["dur"]; sh["clip"] = "K3_%s.mov" % sh["id"]

def read_frames(src, t, n, w=1920, h=1080):
    p = subprocess.Popen([FF, "-v", "error", "-ss", "%.4f" % t, "-i", os.path.normpath(L5 + "/sources/" + SRC[src]), "-vf", "fps=30", "-frames:v", str(n),
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

def detect_full(path, t, n, tag, step=3):
    """Visages (px source) sur n images à 30 i/s depuis t (une image sur step analysée), pleine résolution."""
    d = D + "cache/full/%s_%.2f_%d" % (tag, t, n)
    if not os.path.exists(d + "/faces.json"):
        os.makedirs(d, exist_ok=True)
        subprocess.run([FF, "-v", "error", "-y", "-ss", "%.4f" % t, "-i", path, "-vf", "fps=30,select='not(mod(n\\,%d))'" % step, "-fps_mode", "passthrough",
                        "-frames:v", str((n + step - 1) // step), "-start_number", "0", "-q:v", "2", d + "/f%04d.jpg"], check=True)
        subprocess.run([HK + "/_claude/outils/faces", d], check=True, capture_output=True)
    js = json.load(open(d + "/faces.json"))
    SW_, SH_ = 1280, 720
    return [[(b[0] * SW_, b[1] * SH_, b[2] * SW_, b[3] * SH_) for b in js.get("f%04d.jpg" % i, [])] for i in range((n + step - 1) // step)]

# titre RMC (image 1280x720, y 574-616) découpé sans les guillemets : UNE VICTOIRE DE LFI FERAIT | FUIR | LE PRÉSIDENT DU MEDEF
TITLE_Y = (574, 616); P1, P2, P3 = (166, 541), (557, 617), (634, 958)
def render(sh):
    n = sh["n"]; w = writer(OUT + sh["clip"]); info = ""
    if sh["src"] == "RMC":   # capture JT 9:16 plein écran : image recadrée sur Guetté (sans logos RMC) + titre du bandeau en 2 lignes
        fl = detect_full(os.path.normpath(L5 + "/sources/" + SRC["RMC"]), sh["t_in"], n, "RMC", step=3)
        def guette(fs):
            fs = [f for f in fs if f[2] > 40]
            return min(fs, key=lambda f: abs(f[0] + f[2] / 2 - 610)) if fs else None
        xs = [(lambda g: g[0] + g[2] / 2 if g else None)(guette(f_)) for f_ in fl]
        kn = [i for i, x in enumerate(xs) if x is not None]
        xs = [xs[i] if xs[i] is not None else xs[min(kn, key=lambda j: abs(j - i))] for i in range(len(xs))]
        fx_ = np.interp(np.arange(n), np.arange(len(xs)) * 3, xs)
        fx_ = np.convolve(np.pad(fx_, 7, mode="edge"), np.ones(15) / 15, mode="valid")
        k = 0
        for fr in read_frames("RMC", sh["t_in"], n, 1280, 720):
            src = fr.astype(np.float32) / 255
            z = 1.0 + 0.03 * k / max(n - 1, 1); vh = 566 / z; vw = vh * 9 / 16          # au-dessus du bandeau (y < 568)
            cx = float(np.clip(fx_[k], 230 + vw / 2, 1140 - vw / 2))                    # logos RMC (x < 225) et RMC STORY (x > 1150) exclus
            img = grade(crop_view(src[:566], cx, 566 - vh / 2 - 1, vw, W, H))
            sc = 1.7; y0_, y1_ = TITLE_Y
            l1 = src[y0_:y1_, P1[0]:P1[1]]
            gap = np.repeat(src[y0_:y1_, 632:635].mean(axis=1, keepdims=True), 5, axis=1)        # fond blanc du bandeau entre FUIR et LE (après le guillemet fermant, x 623-628)
            l2 = np.concatenate([src[y0_:y1_, P2[0]:P2[1]], gap, src[y0_:y1_, P3[0]:P3[1]]], axis=1)
            l1 = cv2.resize(l1, (int(l1.shape[1] * sc), int(l1.shape[0] * sc)), interpolation=cv2.INTER_CUBIC)
            l2 = cv2.resize(l2, (int(l2.shape[1] * sc), int(l2.shape[0] * sc)), interpolation=cv2.INTER_CUBIC)
            yb = int(0.735 * H); ya = yb - l2.shape[0]; yt = ya - 8 - l1.shape[0]
            for im_, yy in ((l1, yt), (l2, ya)):
                x0 = (W - im_.shape[1]) // 2; img[yy:yy + im_.shape[0], x0:x0 + im_.shape[1]] = im_
            fo = (n - k) / (FADE_S * 30)
            if fo < 1: img *= max(fo, 0)
            w.stdin.write((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8).tobytes()); k += 1
        w.stdin.close(); w.wait(); return "document, %d images" % k
    fps = SFPS[sh["src"]]; s = int(round(sh["t_in"] * fps)); speed = fps / 30; bd = BOUNDS[sh["src"]]
    vh = min(bd[3] - bd[1], (bd[2] - bd[0]) * 16 / 9)
    if sh["fixed"]:
        views = [(sh["fixed"][0], sh["fixed"][1], vh / (1 + (sh["z1"] - 1) * f / max(n - 1, 1))) for f in range(n)]; info = "centre fixe (cadré à la main, tête et cheveux entiers)"
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
MUSIC = L5 + "/sons/K3-kendrick-humble_complet.wav"
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
DUCK = -12.0                                                     # couplet rappé sous la voix : un peu plus bas que K2 (-10) pour garder la voix nette
VA, VB = SEG[0] - 0.05, SEG[1] + 0.10                            # bloc de voix (pauses d'origine) ; « Et c'est pour ça » commence à 22,98
def build_audio():
    n = int(round(END * SR)); voice = np.zeros((n, 2), np.float32)
    x = fade(load(L5 + "/sources/" + SRC["BZ"], VA, VB - VA), 0.015, 0.04)
    p = int(round(tl(VA) * SR)); voice[p:p + len(x)] += x[:n - p]
    mus = fade(load(MUSIC, M0, END + 0.05)[:n], 0.03, 0)
    lv, _ = lufs(voice[int(tl(SEG[0]) * SR):int(VEND * SR)]); lm, _ = lufs(mus)
    voice *= db(-14 - lv); mus *= db(-14 - lm)
    t = np.arange(n) / SR
    d0, d1 = tl(SEG[0]) - 0.12, VEND + 0.06
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
                        "-c:a", "pcm_s24le", OUT + "K3-mix.wav"], check=True)
        li2, tp2 = lufs(load(OUT + "K3-mix.wav"))
        if abs(li2 + 14) < 0.3 and tp2 < -2.2: break
    os.remove(tmp)
    sf_write(OUT + "K3-voix.wav", voice); sf_write(OUT + "K3-musique.wav", mus)
    return "mix %.1f LUFS, true peak %.1f dBTP (voix d'origine %.1f, musique d'origine %.1f LUFS, ducking %.0f dB)" % (li2, tp2, lv, lm, DUCK)

# ---------------- plan-K3.json + son.json ----------------
PHRASE = ("Ce sont les riches qui dessinent la ville, ce sont les pauvres qui construisent la ville, ce sont les riches qui privatisent les réseaux "
          "et ce sont les pauvres qui subissent les pollutions de ces réseaux. Et il est temps que ça change.")
def write_plan():
    vid = []
    for sh in SHOTS:
        u, ch, date, off = URL[sh["src"]]
        src_ = {"fichier": os.path.relpath(os.path.normpath(L5 + "/sources/" + SRC[sh["src"]]), HK), "in_s": round(sh["t_in"], 3), "out_s": round(sh["t_in"] + sh["n"] / 30, 3),
                "url": u, "chaine": ch, "date": date}
        if off is not None: src_["temps_url_s"] = round(off + sh["t_in"], 2)
        else: src_["temps_url_s"] = "extrait lot2 (voir lot2/_claude/derush-C.json)"
        it = {"id": sh["id"], "clip": sh["clip"], "folder": "genK3", "path": OUT + sh["clip"], "s": 0, "e": sh["n"], "clip_fps": 30, "speed_pct": 100,
              "rec": sh["rec"], "dur": sh["dur"], "track": 1, "note": sh["note"], "source": src_,
              "effets": "capture plein écran 9:16 : image recadrée sur Guetté (suivi horizontal du visage, sans logos RMC ni bandeau météo) + titre du bandeau en 2 lignes UNE VICTOIRE DE LFI FERAIT / FUIR LE PRÉSIDENT DU MEDEF (guillemets d'origine retirés par découpe), bloc dans la zone sûre TikTok (x 0,19-0,81, y ≤ 0,735), poussée 1,00->1,03, fondu au noir %.1f s" % FADE_S if sh["src"] == "RMC" else
                        "recadrage 9:16 (%s, bornes %s), poussée lente %.2f->%.2f, étalonnage couleur doux + vignette + grain%s" % (
                            "centre fixe sans visage coupé" if (sh["auto"] or sh["fixed"]) else "suivi du visage", list(BOUNDS[sh["src"]]), sh["z0"], sh["z0"] * sh["z1"], ", sous-titres cuits" if sh["txt"] else "")}
        if "views" in sh: it["vues_debut_fin"] = sh["views"]
        vid.append(it)
    plan = {"name": "K3 - Karaoké discours - Guetté", "fps": 30, "w": 1080, "h": 1920, "duree_s": round(f30(END) / 30, 3),
            "note": "Plans ProRes 1080x1920 30 i/s prêts (recadrés, étalonnés, sous-titres cuits). Aucun ralenti. Générateur : lot5/_claude/gen/K3/genK3.py ; calage : timing.py",
            "phrase": {"texte": PHRASE, "source_url": BZN[0], "in_s_url": round(232 + SEG[0], 2), "out_s_url": round(232 + SEG[1], 2), "chaine": "Clémence Guetté (chaîne officielle)", "date": "2026-02-13",
                       "blocs_voix_timeline": [{"url_in": round(232 + VA, 2), "url_out": round(232 + VB, 2), "timeline_in": round(tl(VA), 3)}]},
            "textes": {"police": "Avenir Next Heavy Italic", "couleur": "#FFD700", "taille": "jusqu'à 150 px (1 à 3 lignes), bloc ≤ 60 % de large", "position": "bas-centre, bas du bloc à 71,5 % (zone sûre TikTok)", "contour": "sombre net + ombre douce, pas de fond", "guillemets": "aucun",
                       "fragments": [{"t0": round(f["ds"], 3), "t1": round(f["de"], 3), "texte": f["txt"]} for f in FRAGS]},
            "video": vid,
            "audio": [{"id": "mix", "clip": "K3-mix.wav", "folder": "genK3", "path": OUT + "K3-mix.wav", "rec": 0, "track": 1,
                       "note": "mix -14 LUFS : musique seule %.2f s, voix %.2f-%.2f s avec musique %d dB dessous, remontée jusqu'au drop %.3f s (Bitch, be humble), fondu %.1f s" % (
                           tl(SEG[0]), tl(SEG[0]), VEND, DUCK, DROP_T, FADE_S)}]}
    json.dump(plan, open(D + "plan-K3.json", "w"), indent=1, ensure_ascii=False)
    son = {"titre": "HUMBLE.", "artiste": "Kendrick Lamar", "url": "https://www.youtube.com/watch?v=tvTRZJ-4EyI", "chaine": "Kendrick Lamar (chaîne officielle vérifiée, clip officiel)",
           "fichier": "lot5/sons/K3-kendrick-humble_complet.wav (audio du clip officiel, 3:04)",
           "extrait_debut_s": round(M0, 3), "extrait_fin_s": round(M0 + END, 3),
           "contenu": "fin du couplet 1 (If I quit this season… / My left stroke just went viral / Right stroke… / Sopranos… / It's levels to it, you and I know, 50,3-64,3 s) sous la voix à %d dB, "
                      "puis refrain Bitch, be humble, sit down (64,35-66,4 s) et Be humble, sit down (67,9-69,6 s) à pleine puissance, fin sur la frappe après le 2e sit down" % DUCK,
           "bpm": round(60 / TM["period"], 2), "drop": "Bitch, be humble : %.3f s dans le complet = %.3f s timeline (attaques voix mesurées : Bitch 64,35, be 64,73, hum 65,13, sit 65,93, down 66,33)" % (TM["drop_c"], DROP_T),
           "frappes_timeline_s": [round(h, 3) for h in HITS if -0.01 <= h <= END + 0.01],
           "coupes_timeline_s": [round(sh["a"], 3) for sh in SHOTS[1:]] + [round(END, 3)]}
    json.dump(son, open(D + "son.json", "w"), indent=1, ensure_ascii=False)

# ---------------- aperçu 540x960 ----------------
def preview():
    out = HK + "/preview/apercu-K3.mp4"; args = [FF, "-v", "error", "-y"]; fl = []
    for i, sh in enumerate(SHOTS):
        args += ["-i", OUT + sh["clip"]]
        fl.append("[%d:v]trim=end_frame=%d,setpts=PTS-STARTPTS,scale=540:960,setsar=1[v%d]" % (i, sh["dur"], i))
    args += ["-i", OUT + "K3-mix.wav"]
    fl.append("".join("[v%d]" % i for i in range(len(SHOTS))) + "concat=n=%d:v=1:a=0[v]" % len(SHOTS))
    args += ["-filter_complex", ";".join(fl), "-map", "[v]", "-map", "%d:a" % len(SHOTS), "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", "-r", "30",
             "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out]
    subprocess.run(args, check=True); return out

if __name__ == "__main__":
    only = None
    for a in sys.argv:
        if a.startswith("only="): only = a[5:].split(",")
    for f in FRAGS: print("%-30s %.3f-%.3f (mot %.3f)" % (f["txt"], f["ds"], f["de"], f["w0"]))
    print("rafale", ["%.3f" % r for r in RCUTS], "fin %.3f" % END)
    for sh in SHOTS: print("  %-4s %-4s %.3f-%.3f %3d img" % (sh["id"], sh["src"], sh["a"], sh["b"], sh["dur"]))
    if "plans" in sys.argv:
        for sh in SHOTS:
            if only and sh["id"] not in only: continue
            print(sh["id"], "%.3f-%.3f" % (sh["a"], sh["b"]), sh["dur"], "img", render(sh), flush=True)
    if "audio" in sys.argv: print(build_audio())
    write_plan()
    if "apercu" in sys.argv: print(preview())
    print("total %.3f s ; %d plans ; voix %.2f-%.2f" % (END, len(SHOTS), tl(SEG[0]), VEND))
