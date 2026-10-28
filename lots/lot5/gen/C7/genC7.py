# Lot 5 / C7 — Citation ciné, Éric Coquerel (député LFI). Copie de la structure de lot4/_claude/gen/C6/genC6.py (elle-même copie de C5 / C2).
# « C'est la constitution d'une noblesse d'argent. Le macronisme, c'est ça. C'est-à-dire quelques milliers de personnes dans ce pays
#   qui s'enrichissent comme jamais on s'est enrichi. »
#   (meeting municipales 2026 à Saint-Ouen, 02/03/2026, chaîne Eric Coquerel, youtu.be/q5zM4ghkEqs?t=521) — autre phrase et autres images que C2 et K2.
# Son : Kanye West — POWER (Kanye West VEVO). Montée sous la phrase (couplet « Do it better than anybody… every superhero need his theme music »
# filtré, volume qui monte), la phrase finit dans le trou avant le refrain, DROP sur « No one man should have all that power » (attaque 25,120 s),
# fin après « Stop tripping, I'm tripping off the power ».
# Sources : lot5/sources/C7-coquerel-stouen-*.mp4 (4K, téléchargées pour C7 : décor plein de logos NPA / LFI / REV effacés par delogo.py),
#           lot2/sources/C2-coquerel-hemicycle-01.mp4 et C2-coquerel-hemicycle-04.mp4 (lecture seule, plans NON utilisés par C2 / K2).
# Ralentis : PAS précalculés. Clip livré à vitesse normale (n = durée_tl × fps_source), speed_pct + retime dans plan-C7.json.
# Usage : python genC7.py [plans] [audio] [apercu] [only=ID,ID]
import sys, os, json, subprocess, shutil, math
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
HK = "/Users/luca.grousset/Movies/highkey-gauchiste"
L5 = HK + "/lot5"; L2 = HK + "/lot2"
sys.path.insert(0, HK + "/_claude/outils")
D = L5 + "/_claude/gen/C7/"; OUT = D + "out/"; os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, D)
import framing
framing.CACHE = D + "cache/faces"
from framing import plan_views
from fx import crop_view, vignette, grain, gblur, ease_out
from words import clean
from delogo import delogo
FF = "/opt/homebrew/bin/ffmpeg"; SEG = HK + "/_claude/outils/segment"
W, H, TFPS = 1080, 1920, 30
RED = (228, 0, 43); WHITE = (242, 238, 232)
FONT = "/System/Library/Fonts/Supplemental/Baskerville.ttc"; FIDX = 4      # Baskerville SemiBold (test 3 / C2 / C5 / C6)
TRACK = 0.20

# ---------------- sources ----------------
SO = "https://www.youtube.com/watch?v=q5zM4ghkEqs"
SRC = {  # id : (racine, fichier, fps, largeur, hauteur, url, temps url du début du fichier, delogo)
    "SM": (L5, "C7-coquerel-stouen-macronisme.mp4", 25, 3840, 2160, SO, 516, True),
    "SP": (L5, "C7-coquerel-stouen-peuple.mp4", 25, 3840, 2160, SO, 1364, True),
    "SL": (L5, "C7-coquerel-stouen-brasleves.mp4", 25, 3840, 2160, SO, 1232, True),
    "SD": (L5, "C7-coquerel-stouen-brasdroit.mp4", 25, 3840, 2160, SO, 324, True),
    "SV": (L5, "C7-coquerel-stouen-brasouverts.mp4", 25, 3840, 2160, SO, 1034, True),
    "H1": (L2, "C2-coquerel-hemicycle-01.mp4", 60, 1920, 1080, "https://www.youtube.com/watch?v=v6HH2QrtogU", None, False),
    "H4": (L2, "C2-coquerel-hemicycle-04.mp4", 60, 1920, 1080, "https://www.youtube.com/watch?v=v6HH2QrtogU", None, False),
}
def sfps(k): return SRC[k][2]
# Saint-Ouen 4K : lettres SAINT-OUEN sous 0,76 H, spectateur à droite au-delà de 0,90 W ; logos entre 0,15 et 0,45 H (effacés au-dessus de 0,47 H).
B_SO = (0, 0, 3456, 1640); YLOGO = 0.47 * 2160
B_H1 = (0, 40, 1920, 1080)                 # drapeau minuscule en haut à droite

# ---------------- temps ----------------
MUSIC = L5 + "/sons/C7-kanye-power_complet.wav"
V0 = 5.00                            # voix : timeline = fichier SM - V0 (« C'est » 5,36 -> 0,36 s)
VOUT = 13.92                         # fin de « enrichi » 13,86 (+60 ms) ; « Je n'aurai pas… » commence à 14,08
C_OFF = 15.834                       # musique : timeline = complet - C_OFF (choisi pour que toutes les attaques tombent à < 15 ms d'une image)
C_DROP = 25.120                      # attaque (score 20,9 ; basse qui entre après le trou 24,75-25,0) sur « No one man should have all that power »
DROP = C_DROP - C_OFF                # 9,286
# coupes = attaques RÉELLES mesurées (temps_forts.py sur le morceau complet), pas de grille
CUTS_V = [17.945, 20.075, 22.015, 23.430]                 # sous la phrase : « Le macronisme », « quelques », « qui », « jamais »
CUTS_C = [25.120, 26.705, 28.240, 29.600, 31.360, 32.720]  # après le drop
C_END = 34.490                       # attaque après « tripping off the power » (34,1), avant « The system broken »
def tc(c): return c - C_OFF
END = tc(C_END)
def f30(t): return int(round(t * TFPS))

# ---------------- texte (mots Whisper large-v3-turbo sur le fichier SM, mot à mot) ----------------
WORDS = [("C'est", 5.36), ("la", 5.46), ("constitution", 5.56), ("d'une", 6.10), ("noblesse", 6.50), ("d'argent.", 6.86),
         ("Le", 7.34), ("macronisme,", 7.64), ("c'est", 8.24), ("ça.", 8.52), ("C'est-à-dire", 8.78), ("quelques", 9.24), ("milliers", 9.80),
         ("de", 10.14), ("personnes", 10.24), ("dans", 10.56), ("ce", 10.74), ("pays", 10.90), ("qui", 11.16), ("s'enrichissent", 11.64),
         ("comme", 12.30), ("jamais", 12.52), ("on", 12.94), ("s'est", 13.26), ("enrichi.", 13.44)]
TEXTE = "C'est la constitution d'une noblesse d'argent. Le macronisme, c'est ça. C'est-à-dire quelques milliers de personnes dans ce pays qui s'enrichissent comme jamais on s'est enrichi."
T = [{"w": w, "start": s} for w, s in WORDS]
def up(t): return clean(t["w"], keep_quotes=False).replace("'", "’").upper()
YB, YI = 0.47, 0.62                                      # zone sûre TikTok : x 0,17-0,83, y 0,12-0,75 (retour Luca)
def card(lines, red, y, em, t1):
    Ls = [[[up(T[i]), T[i]["start"] - V0, i in red] for i in li] for li in lines]
    return {"lines": Ls, "t0": Ls[0][0][1], "t1": t1, "y": y, "em": em, "tr": TRACK if y == YB else 0.13}
def ts(i): return T[i]["start"] - V0
CV = [tc(c) for c in CUTS_V]; C = [tc(c) for c in CUTS_C]
CVr = [f30(x) / TFPS for x in CV]; DROPr = f30(DROP) / TFPS      # fins de cartons calées sur l'image de coupe
CARDS = [   # mots longs : approche réduite et un mot par ligne pour garder des lettres grandes (lisibles sur téléphone)
    dict(card([[0, 1], [2]], [], YB, 130, ts(3)), tr=0.10),              # C'EST LA / CONSTITUTION (noir)
    dict(card([[3], [4], [5]], [4, 5], YB, 130, CVr[0]), tr=0.10),       # D'UNE / NOBLESSE / D'ARGENT (noir, rouge Caslon)
    dict(card([[6], [7], [8, 9]], [7], YI, 124, ts(10)), tr=0.06),       # LE / MACRONISME / C'EST ÇA (Saint-Ouen, synchro)
    dict(card([[10]], [], YI, 124, CVr[1]), tr=0.06),                    # C'EST-À-DIRE (synchro)
    dict(card([[11], [12], [13, 14], [15, 16, 17]], [], YB, 120, CVr[2]), tr=0.10),   # QUELQUES / MILLIERS / DE PERSONNES / DANS CE PAYS (noir)
    dict(card([[18], [19], [20, 21]], [], YI, 116, ts(22)), tr=0.05),    # QUI / S'ENRICHISSENT / COMME JAMAIS (synchro)
    dict(card([[22, 23], [24]], [24], YI, 124, DROPr), tr=0.06),         # ON S'EST / ENRICHI (punch-in, rouge)
]
_fc = {}
def font(px):
    px = int(round(px))
    if px not in _fc: _fc[px] = ImageFont.truetype(FONT, px, index=FIDX)
    return _fc[px]
DFONT = os.path.expanduser("~/Library/Fonts/CaslonGraphique-Opti.otf"); DSC, DTR = 1.22, 0.03
_dc = {}
def dfont(px):
    px = int(round(px))
    if px not in _dc: _dc[px] = ImageFont.truetype(DFONT, px)
    return _dc[px]
def wfont(red, em): return (dfont(em * DSC), DTR * em * DSC) if red else (font(em), None)
def word_w(word, red, em, tr):
    f, t = wfont(red, em); t = tr * em if t is None else t
    return sum(f.getlength(ch) for ch in word) + t * max(len(word) - 1, 0)
def gap(em, tr): return font(em).getlength(" ") + 2 * tr * em
def line_w(li, em, tr): return sum(word_w(w[0], w[2], em, tr) for w in li) + gap(em, tr) * max(len(li) - 1, 0)
def card_em(c): return min(c["em"], min(0.62 * W / (line_w(li, 100, c["tr"]) / 100) for li in c["lines"]))
def draw_text(img, t, on_image):
    act = [c for c in CARDS if c["t0"] - 1e-3 <= t < c["t1"]]
    if not act: return img
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dr = ImageDraw.Draw(layer)
    sh = Image.new("L", (W, H), 0); ds = ImageDraw.Draw(sh); em = 100
    for c in act:
        em = card_em(c); lh = em * 1.32; tr = c["tr"]
        vis = [[w for w in li if w[1] <= t + 1e-3] for li in c["lines"]]
        y0 = c["y"] * H - len(c["lines"]) * lh / 2
        for li_i, li in enumerate(vis):
            if not li: continue
            x = W / 2 - line_w(li, em, tr) / 2; yb = y0 + li_i * lh + em * 0.95
            for word, tw, red in li:
                a = ease_out((t - tw) / 0.12)                 # apparition 4 images, sans rebond
                f, tt = wfont(red, em); tt = tr * em if tt is None else tt
                for ch in word:
                    if on_image:
                        ds.text((x, yb), ch, font=f, anchor="ls", fill=int(235 * a), stroke_width=max(3, int(em * 0.06)), stroke_fill=int(235 * a))
                    dr.text((x, yb), ch, font=f, anchor="ls", fill=(RED if red else WHITE) + (int(255 * a),))
                    x += f.getlength(ch) + tt
                x += gap(em, tr) - tt
    out = img
    if on_image:
        m = np.asarray(sh.filter(ImageFilter.GaussianBlur(em * 0.10)), np.float32)[..., None] / 255
        out = out * (1 - 0.85 * m)
    lay = np.asarray(layer, np.float32) / 255
    return out * (1 - lay[..., 3:4]) + lay[..., [2, 1, 0]] * lay[..., 3:4]

# ---------------- étalonnage « sépia lavé » (identique test 3 / C2 / C5 / C6) ----------------
TINT = np.array([0.93, 1.0, 1.05], np.float32)
VIG = None
def grade(img):
    global VIG
    y = img @ np.array([0.114, 0.587, 0.299], np.float32)
    x = y[..., None] * 0.84 + img * 0.16
    x = np.clip(x, 0, 1); x = x * x * (3 - 2 * x) * 0.55 + x * 0.45
    x = 0.055 + x * 0.83
    x = gblur(x * TINT, 0.8)
    if VIG is None: VIG = vignette(np.ones((H, W, 3), np.float32), strength=0.62, power=2.0)
    return grain(x * VIG, 0.028, 1.6)

# ---------------- plans ----------------
def S(i, a, b, src, t_in, sp, mode, hint, z0, z1, bounds=B_SO, vh=None, txt=False, note="", gain=1.0, top=0.17):
    return dict(id=i, a=a, b=b, src=src, t_in=t_in, sp=sp, mode=mode, hint=hint, z0=z0, z1=z1, bounds=bounds, vh=vh, txt=txt, note=note, gain=gain, top=top)
SYNC = None                                # t_in = None -> synchro labiale (temps timeline + V0)
SHOTS = [
    S("Q1", 0.0, CV[0], None, None, 100, "noir", None, 1, 1, txt=True, note="C'EST LA / CONSTITUTION puis D'UNE NOBLESSE / D'ARGENT sur noir"),
    S("Q2", CV[0], CV[1], "SM", SYNC, 100, "face", (1850, 450), 1.0, 1.06, vh=1250, txt=True, note="Saint-Ouen, plan poitrine, synchro labiale (« Le macronisme, c'est ça. C'est-à-dire »)"),
    S("Q3", CV[1], CV[2], None, None, 100, "noir", None, 1, 1, txt=True, note="QUELQUES MILLIERS / DE PERSONNES / DANS CE PAYS sur noir"),
    S("Q4", CV[2], CV[3], "SM", SYNC, 100, "face", (1850, 450), 1.05, 1.12, vh=1250, txt=True, note="Saint-Ouen, synchro (« qui s'enrichissent comme »)"),
    S("Q5", CV[3], DROP, "SM", SYNC, 100, "face", (1850, 450), 1.25, 1.36, vh=1250, txt=True, note="même plan resserré (punch-in sur la frappe), « jamais on s'est enrichi », coupe au drop"),
    S("B01", C[0], C[1], "SL", 5.70, 50, "face", (1850, 450), 1.0, 1.05, vh=850, note="drop : Saint-Ouen, gros plan visage au ralenti, regard vers la salle"),
    S("B02", C[1], C[2], "H4", 0.60, 50, "face", (960, 300), 1.0, 1.05, bounds=B_H1, vh=1040, note="Assemblée nationale, à la tribune, regard levé vers l'hémicycle"),
    S("B03", C[2], C[3], "SV", 12.40, 50, "face", (1850, 450), 1.0, 1.04, vh=1640, top=0.20, note="Saint-Ouen, plan large au pupitre, regard vers la salle"),
    S("B04", C[3], C[4], "H1", 1.70, 50, "face", (960, 300), 1.0, 1.05, bounds=B_H1, vh=950, note="Assemblée nationale, gros plan à la tribune, relève la tête"),
    S("B05", C[4], C[5], "SD", 3.00, 50, "face", (1850, 450), 1.0, 1.05, vh=900, note="Saint-Ouen, gros plan visage au ralenti"),
    S("B06", C[5], END, "SM", 15.00, 50, "face", (1850, 450), 1.0, 1.05, vh=1640, top=0.22, note="Saint-Ouen, mains levées devant lui (juste après la phrase), fondu au noir"),
]
FADE_ID, FADE_S = "B06", 0.6
REC_FIX = {"Q4": 186}                     # attaque 22,015 -> 6,181 s : image 186 (6,200) plus proche de l'attaque mesurée sur le mix musique (6,215) que 185
for i, sh in enumerate(SHOTS):
    sh["rec"] = REC_FIX.get(sh["id"], f30(sh["a"]))
for i, sh in enumerate(SHOTS):
    sh["dur"] = (SHOTS[i + 1]["rec"] if i + 1 < len(SHOTS) else f30(END)) - sh["rec"]
    fps = sfps(sh["src"]) if sh["src"] else TFPS; sh["fps"] = fps
    sh["n"] = int(math.ceil(sh["dur"] / TFPS * fps - 1e-6))
    sh["clip"] = "C7_%s.mov" % sh["id"]
    if sh["src"] and sh["t_in"] is None: sh["t_in"] = sh["rec"] / TFPS + V0

def spath(k): return SRC[k][0] + "/sources/" + SRC[k][1]
def read_frames(src, t, n):
    _, _, _, sw, shh, _, _, _ = SRC[src]
    p = subprocess.Popen([FF, "-v", "error", "-ss", "%.4f" % t, "-i", spath(src), "-frames:v", str(n),
                          "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE)
    sz = sw * shh * 3
    for _ in range(n):
        b = p.stdout.read(sz)
        if len(b) < sz: break
        yield np.frombuffer(b, np.uint8).reshape(shh, sw, 3)
    p.stdout.close(); p.wait()
def writer(path, fps):
    return subprocess.Popen([FF, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", "%dx%d" % (W, H), "-r", str(fps), "-i", "-",
                             "-c:v", "prores_ks", "-profile:v", "3", "-pix_fmt", "yuv422p10le", "-vendor", "apl0", path], stdin=subprocess.PIPE)
def views_for(sh):
    root, f, fps, sw, shh, _, _, _ = SRC[sh["src"]]
    framing.ROOT = root; framing.SW, framing.SH = sw, shh
    s = int(round(sh["t_in"] * fps)); n = sh["n"]; z0, z1 = sh["z0"], sh["z1"]; bd = sh["bounds"]
    used = max(int(round(n * sh["sp"] / 100)), 2)              # images réellement montrées (ralenti Resolve)
    zoom = lambda k: z0 + (z1 - z0) * min(k, used - 1) / max(used - 1, 1)
    vh = min(sh["vh"] or shh, bd[3] - bd[1], (bd[2] - bd[0]) * 16 / 9)
    if sh["mode"] == "face":
        # suivi visage maison : taille de vue = vh / zoom (jamais plus large que nécessaire pour la tête), jamais de dézoom,
        # cadre calé sur le haut de la tête (Saint-Ouen : tête près du bord haut de la source, la vue ne doit pas s'élargir pour ça)
        heads = framing.pick(framing.detect(f, s, n + 2, fps), sh["hint"], bd)
        if not heads: return s, (None, False)
        hbs = [framing.head_box(heads[min(k, len(heads) - 1)]) for k in range(n)]
        vmax = min(bd[3] - bd[1], (bd[2] - bd[0]) * 16 / 9)
        vs = [min(vmax, max(vh / zoom(k), (hb[3] - hb[1]) / 0.80, (hb[2] - hb[0]) * 16 / 9 / 0.88)) for k, hb in enumerate(hbs)]
        for k in range(n - 2, -1, -1): vs[k] = max(vs[k], vs[k + 1])
        out = []
        for hb, v in zip(hbs, vs):
            vw = v * 9 / 16
            x0 = min(max((hb[0] + hb[2]) / 2 - vw / 2, bd[0]), bd[2] - vw); y0 = min(max(hb[1] - sh["top"] * v, bd[1]), bd[3] - v)
            out.append((x0 + vw / 2, y0 + v / 2, v))
        return s, (out, True)
    return s, plan_views(f, s, n, fps, speed=1.0, hint=sh["hint"], bounds=bd, vh=vh, zoom=zoom, fixed=sh["hint"])
def render(sh):
    n, fps = sh["n"], sh["fps"]; w = writer(OUT + sh["clip"], fps); info = ""
    if sh["mode"] == "noir":
        for k in range(n):
            img = grain(np.zeros((H, W, 3), np.float32) + 0.012, 0.012, 1.6)
            img = draw_text(img, sh["rec"] / TFPS + k / fps, False)
            w.stdin.write((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8).tobytes())
        w.stdin.close(); w.wait(); return info
    s, (views, ok) = views_for(sh); bd = sh["bounds"]; dl = SRC[sh["src"]][7]
    info = ("visage" if ok else "SANS VISAGE") if sh["mode"] == "face" else "fixe"
    tmp = D + "cache/_seg_" + sh["id"]; shutil.rmtree(tmp, ignore_errors=True); os.makedirs(tmp + "/in"); os.makedirs(tmp + "/mk")
    k = 0; vmin = 9e9; yl = []
    for fr in read_frames(sh["src"], s / fps, n):
        cx, cy, v = views[min(k, len(views) - 1)]; vw = v * 9 / 16; vmin = min(vmin, v)
        assert bd[0] - 1 <= cx - vw / 2 and cx + vw / 2 <= bd[2] + 1 and bd[1] - 1 <= cy - v / 2 and cy + v / 2 <= bd[3] + 1, (sh["id"], k, cx, cy, v)
        img = crop_view(fr, cx, cy, vw, W, H)                    # uint8, recadré 1080x1920
        cv2.imwrite(tmp + "/in/f%04d.png" % k, img); yl.append((YLOGO - (cy - v / 2)) * H / v); k += 1
    if dl: subprocess.run([SEG, tmp + "/in", tmp + "/mk"], check=True, capture_output=True)
    lg = []
    for j in range(k):
        img = cv2.imread(tmp + "/in/f%04d.png" % j).astype(np.float32) / 255 * sh["gain"]
        if dl:
            pm = cv2.imread(tmp + "/mk/f%04d.png" % j, 0).astype(np.float32) / 255
            img, fr_ = delogo(img, pm, yl[j]); lg.append(fr_)
        img = grade(img)
        if sh["txt"]: img = draw_text(img, sh["rec"] / TFPS + j / fps, True)
        w.stdin.write((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8).tobytes())
    shutil.rmtree(tmp, ignore_errors=True)
    info += " vue min %d px (agrandi x%.2f)" % (vmin, 1920 / vmin)
    if lg: info += " logos effacés %.1f %%" % (100 * max(lg))
    if k < n: info += " court:%d/%d" % (k, n)
    w.stdin.close(); w.wait()
    return info

# ---------------- audio ----------------
SR = 48000
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
VEND = VOUT - V0
def build_audio():
    from scipy.signal import butter, sosfiltfilt
    n = int(round(END * SR)); mix = np.zeros((n, 2), np.float32)
    v = fade(load(spath("SM"), V0, VOUT - V0), 0.02, 0.06)
    mus = load(MUSIC, C_OFF, END + 0.05)[:n]
    lv, _ = lufs(v); lm, _ = lufs(mus[int(DROP * SR):])
    v *= db(-15 - lv); mus *= db(-14 - lm)                      # voix -15 LUFS ; refrain après drop -14 LUFS
    t = np.arange(len(mus)) / SR
    # MONTÉE sous la phrase : couplet filtré (passe-bas 1,2 kHz) qui s'ouvre de la 3e coupe au drop, volume -11 dB -> -5 dB, plein sur la frappe du drop
    lp = sosfiltfilt(butter(4, 1200, "low", fs=SR, output="sos"), mus, axis=0).astype(np.float32)
    op = np.clip((t - CV[2]) / (DROP - 0.05 - CV[2]), 0, 1)[:, None]
    body = lp * (1 - op) + mus * op
    gdb = -11 + 6 * np.clip(t / VEND, 0, 1)
    env = np.where(t < DROP - 0.03, db(gdb), 1.0)
    ramp = (t >= DROP - 0.03) & (t < DROP)
    env[ramp] = db(gdb[ramp]) + (1 - db(gdb[ramp])) * (t[ramp] - DROP + 0.03) / 0.03
    env = env * np.clip(t / 0.3, 0, 1)                           # entrée 0,3 s
    env = env * np.where(t > END - FADE_S, np.clip((END - t) / FADE_S, 0, 1) ** 1.5, 1)
    sel = t < DROP
    out = np.where(sel[:, None], body, mus) * env[:, None].astype(np.float32)
    mix[:len(out)] += out; mix[:len(v)] += v
    tmp = OUT + "_tmp_mix.wav"; sf_write(tmp, mix); g = 0.0; li2 = None
    for _ in range(4):
        li = lufs(mix)[0] if li2 is None else li2
        g += -14.0 - li
        subprocess.run([FF, "-v", "error", "-y", "-i", tmp, "-af", "volume=%.2fdB,alimiter=limit=0.80:attack=3:release=60:level=false,aresample=192000,alimiter=limit=0.82:attack=1:release=40:level=false,aresample=48000" % g,
                        "-c:a", "pcm_s24le", OUT + "C7-mix.wav"], check=True)
        li2, tp2 = lufs(load(OUT + "C7-mix.wav"))
        if abs(li2 + 14) < 0.3 and tp2 < -1.0: break
    os.remove(tmp)
    sf_write(OUT + "C7-voix.wav", v); sf_write(OUT + "C7-musique.wav", out)
    return "mix %.1f LUFS, true peak %.1f dBTP (voix %.1f, musique %.1f d'origine)" % (li2, tp2, lv, lm)

# ---------------- plan-C7.json ----------------
def write_plan():
    vid = []
    for sh in SHOTS:
        it = {"id": sh["id"], "clip": sh["clip"], "folder": "genC7", "path": OUT + sh["clip"], "s": 0, "e": sh["n"], "clip_fps": sh["fps"],
              "rec": sh["rec"], "dur": sh["dur"], "track": 1, "note": sh["note"]}
        if sh["src"]:
            sp = sh["sp"]; used = sh["n"] * sp / 100 / sh["fps"]; r = SRC[sh["src"]]
            it["source"] = {"fichier": os.path.relpath(spath(sh["src"]), HK), "url": r[5], "in_s": round(sh["t_in"], 3), "out_s": round(sh["t_in"] + used, 3)}
            if r[6] is not None: it["source"]["yt_in_s"] = round(r[6] + sh["t_in"], 2)
            it["effets"] = "recadrage 9:16 %s (bornes %s), zoom %.2f->%.2f, %ssépia lavé + vignette + grain%s" % (
                "suivi visage" if sh["mode"] == "face" else "fixe", list(sh["bounds"]), sh["z0"], sh["z1"],
                "logos NPA/LFI/REV du décor effacés (delogo.py, masque personne Vision), " if r[7] else "", ", texte cuit" if sh["txt"] else "")
            it["speed_pct"] = sp
            if sp != 100: it["retime"] = "optical_flow"
        else:
            it["speed_pct"] = 100
            it["effets"] = "noir + grain, texte cuit (Baskerville SemiBold approche 0,20 em ; mot rouge en CaslonGraphique-Opti)"
        if sh["id"] == FADE_ID: it["fade_out_s"] = FADE_S
        vid.append(it)
    plan = {"name": "C7 - Citation cine - Eric Coquerel", "fps": 30, "w": 1080, "h": 1920, "duree_s": round(END, 3),
            "note": "Aperçu lot 5. Plans ProRes 9:16 prêts (recadrés, logos du décor effacés, étalonnés, texte cuit). Ralentis à faire dans Resolve : speed_pct + Optical Flow ; e-s = images source à vitesse normale. Générateur : lot5/_claude/gen/C7/genC7.py",
            "citation": {"texte": TEXTE, "fichier": "lot5/sources/" + SRC["SM"][1], "in_s": V0, "out_s": VOUT, "source_url": SO,
                         "yt_in_s": round(516 + V0, 2), "yt_out_s": round(516 + VOUT, 2), "date": "2026-03-02, meeting municipales 2026 à Saint-Ouen (chaîne Eric Coquerel)"},
            "musique": {"fichier": "lot5/sons/C7-kanye-power_complet.wav", "url": "https://www.youtube.com/watch?v=L53gjP-TtGE", "debut_dans_complet_s": round(C_OFF, 3), "fin_dans_complet_s": round(C_END, 3),
                        "drop_timeline_s": round(DROP, 3), "coupes_timeline_s": [round(sh["rec"] / 30, 3) for sh in SHOTS[1:]]},
            "textes": [{"t0": round(c["t0"], 2), "t1": round(c["t1"], 2), "lignes": [" ".join(w[0] for w in li) for li in c["lines"]],
                        "rouge": [w[0] for li in c["lines"] for w in li if w[2]]} for c in CARDS],
            "video": vid,
            "audio": [{"id": "mix", "clip": "C7-mix.wav", "folder": "genC7", "path": OUT + "C7-mix.wav", "rec": 0, "track": 1,
                       "note": "mix -14 LUFS : voix SM %.2f-%.2f s (fondu 60 ms) + musique complet %.3f-%.2f s ; sous la voix couplet filtré passe-bas 1,2 kHz qui s'ouvre de %.2f s au drop et volume -11 -> -5 dB (montée), plein sur le drop %.2f s, fondu de fin %.1f s" % (V0, VOUT, C_OFF, C_END, CV[2], DROP, FADE_S)}],
            "stems": [OUT + "C7-voix.wav", OUT + "C7-musique.wav"]}
    json.dump(plan, open(D + "plan-C7.json", "w"), indent=1, ensure_ascii=False)

# ---------------- aperçu ffmpeg 540×960 ----------------
def preview():
    out = HK + "/preview/apercu-C7.mp4"; args = [FF, "-v", "error", "-y"]; fl = []
    for i, sh in enumerate(SHOTS):
        args += ["-i", OUT + sh["clip"]]
        fl.append("[%d:v]setpts=(PTS-STARTPTS)/%.4f,fps=30,trim=end_frame=%d,setpts=PTS-STARTPTS,scale=540:960,setsar=1%s[v%d]" % (
            i, sh["sp"] / 100, sh["dur"], ",fade=t=out:st=%.3f:d=%.2f" % (sh["dur"] / 30 - FADE_S, FADE_S) if sh["id"] == FADE_ID else "", i))
    args += ["-i", OUT + "C7-mix.wav"]
    fl.append("".join("[v%d]" % i for i in range(len(SHOTS))) + "concat=n=%d:v=1:a=0[v]" % len(SHOTS))
    args += ["-filter_complex", ";".join(fl), "-map", "[v]", "-map", "%d:a" % len(SHOTS), "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p",
             "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out]
    subprocess.run(args, check=True)
    return out

if __name__ == "__main__":
    only = None
    for a in sys.argv:
        if a.startswith("only="): only = a[5:].split(",")
    if "plans" in sys.argv:
        for sh in SHOTS:
            if only and sh["id"] not in only: continue
            print(sh["id"], "%.2f-%.2f" % (sh["a"], sh["b"]), sh["dur"], "img tl", sh["n"], "img src", render(sh), flush=True)
    if "audio" in sys.argv: print(build_audio())
    write_plan()
    if "apercu" in sys.argv: print(preview())
    print("total %.2f s ; %d plans ; drop %.2f" % (END, len(SHOTS), DROP))
