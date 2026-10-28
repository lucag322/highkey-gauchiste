# C1 — Citation ciné, Clémence Guetté (lot 2), musique Hans Zimmer - Time. Modèle : _claude/gen/3/gen3.py (test 3) et gen/C2 (montée sous la citation, entrée à la fin).
# Aperçu hors Resolve : plans ProRes 9:16 recadrés (visage suivi), sépia lavé + vignette + grain, texte cuit sur les plans parlés.
# Ralentis PAS précalculés : clip à vitesse normale (e-s = durée_tl/30 × fps_source), speed_pct + retime dans plan-C1.json.
# Usage : python genC1.py [plans] [audio] [apercu] [only=ID,ID]
import sys, os, json, math, subprocess
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
ROOT = "/Users/luca.grousset/Movies/highkey-gauchiste"; LOT = ROOT + "/lot2"
sys.path.insert(0, ROOT + "/_claude/outils")
import framing
from framing import plan_views
from fx import crop_view, vignette, grain, gblur, ease_out
from words import clean
FF = "/opt/homebrew/bin/ffmpeg"
D = LOT + "/_claude/gen/C1/"; OUT = D + "out/"; os.makedirs(OUT, exist_ok=True)
framing.ROOT = LOT; framing.CACHE = D + "cache"           # detect() lit LOT/sources/<src>
SRC = {k: "C1-guette-%s.mp4" % k for k in ["bezons-citation", "bezons-01", "bezons-02", "amfis-01", "amfis-02", "amfis-03",
                                              "meaux-01", "meaux-02", "meaux-03", "meaux-04", "meaux-05", "meaux-06", "meaux-07", "meaux-08", "meaux-09", "meaux-10"]}
SRC["amfis-fin"] = "../_claude/gen/C1/dl/amfis-fin.mp4"    # yt-dlp HW03wZDi6Tk 1678-1694 s (chaîne La France insoumise)
SFPS = {k: (60 if k.startswith("amfis") else 25) for k in SRC}
W, H, TFPS = 1080, 1920, 30
RED = (228, 0, 43); WHITE = (242, 238, 232)
FONT = "/System/Library/Fonts/Supplemental/Baskerville.ttc"; FIDX = 4      # Baskerville SemiBold
TRACK = 0.20
LFI = (1610, 35, 1885, 180); A26 = (25, 25, 150, 155)                     # logos incrustés (px source)
WM = {k: [LFI] + ([A26] if k.startswith("amfis") else []) for k in SRC}

# ---------------- temps ----------------
# Musique : Hans Zimmer - Time (Inception), audio officiel WaterTower Music (YouTube c56t7upa8Bk). Sadeness puis Nightcall refusés par Luca
# Time = 63 BPM, une attaque nette par mesure (changement d'accord, 3,81 s) ;
# dans la montée, les noires aussi sont nettes ; après la grande entrée, seules les mesures (+ le 4e temps 159,46) sont des attaques franches.
# Attaques RÉELLES mesurées dans le morceau complet avec temps_forts.py (saut d'énergie multi-bandes, pas de grille) :
MUSIC = LOT + "/sons/C1-zimmer-time_complet.wav"
A = dict(b1=146.105, baisser=147.055, jamais=150.860, tout=151.800,      # montée (noires)
         entree=152.770,                                                  # GRANDE ENTRÉE cuivres + cordes + percussions (score 24, le plus fort)
         m2=156.580, t4=159.455, m3=160.400, a3=162.185, m4=164.220)     # mesures suivantes (+ 4e temps 159,46 et attaque 162,19)
C_OFF = 146.0917                     # timeline = morceau - C_OFF ; choisi pour que chaque attaque de coupe tombe à < 12 ms d'une image 30 i/s
END = 20.0                           # règle Luca : citation ciné 20 s max
def f30(t): return int(round(t * TFPS))
def fr(t): return f30(t) / TFPS      # temps de l'image de coupe la plus proche
def tl(k): return A[k] - C_OFF
c1, c2, c3 = fr(tl("baisser")), fr(tl("jamais")), fr(tl("tout"))
DROP = fr(tl("entree"))              # 6,667 : grande entrée de Time, 0,22 s après la fin de « changer. »
c_m2, c_t4, c_m3, c_a3, c_m4 = fr(tl("m2")), fr(tl("t4")), fr(tl("m3")), fr(tl("a3")), fr(tl("m4"))
V1 = 9.88 - tl("jamais")             # voix 1 : timeline = source - V1 ; « jamais » (9,88 s source) sur l'attaque 150,86 -> V1 = 5,112
V2 = 6.81 - tl("m4")                 # voix 2 : timeline = source - V2 ; « tout » (explosive mesurée à 6,81 s dans amfis-fin) sur la mesure 164,22

# ---------------- textes (mot à mot) ----------------
C = json.load(open(LOT + "/_claude/derush-C.json"))["videos"]["C1"]["citation"]
def toks_from(ws):
    out = []
    for w in ws:
        t = w["mot"] if "mot" in w else w["word"].strip(); s = w.get("t0", w.get("start"))
        if out and t.startswith("'"): out[-1]["w"] += t; continue
        out.append({"w": t, "start": s})
    return out
T1 = toks_from(C["mots"])
T1[12]["start"] = 9.52               # « nous » (3e) : attaque mesurée sur l'enveloppe à 9,52 (dérush 9,34 = trop tôt)
# whisper sur dl/amfis-fin.mp4, corrigé sur l'enveloppe : silence 5,05-6,12 -> « nous » 6,14 (et non 5,54), « tout » = explosive 6,81
T2 = [{"w": w, "start": s} for w, s in [("Dans", 4.38), ("un", 4.48), ("an,", 4.76), ("nous", 6.14), ("pouvons", 6.37), ("tout", 6.81), ("changer.", 6.89)]]
assert len(T1) == 19, [t["w"] for t in T1]
def up(t): return clean(t["w"], keep_quotes=False).replace("'", "’").upper()
def card(toks, off, lines, red, y, em_max, t1, at=None):
    """at = {indice: temps timeline} : mot-clé posé sur une attaque de la musique (même image que la coupe) au lieu du début du mot."""
    at = at or {}
    L = [[[up(toks[i]), at.get(i, toks[i]["start"] - off), i in red] for i in li] for li in lines]
    return {"lines": L, "t0": L[0][0][1], "t1": t1, "y": y, "em": em_max, "tr": TRACK if y == YB else 0.13}
YB, YI = 0.47, 0.70
# nous n'allons pas baisser la tête, | nous n'allons pas céder aux intimidations, | nous n'allons jamais renoncer à tout changer.
#  0    1      2   3       4  5          6    7     8   9     10  11                12   13     14     15      16 17   18
q = lambda i: T1[i]["start"] - V1
q2 = lambda i: T2[i]["start"] - V2
# Zone sûre TikTok (1080×1920) : lignes ≤ SAFE_W px centrées (x 0,17-0,83), texte entre y 0,12 et 0,75. Les lignes trop longues sont
# coupées en 2-4 lignes pour garder des lettres d'environ 70 px ; les cartons sur image (YI) sont posés par le bas (dernière ligne de base à BASE_I).
SAFE_W = 660; BASE_I = 1395
CARDS = [
    card(T1, V1, [[0], [1], [2]], [], YB, 130, c1),                        # noir : NOUS / N'ALLONS / PAS
    card(T1, V1, [[3], [4, 5]], [5], YI, 124, q(6)),                       # visage, TÊTE rouge
    card(T1, V1, [[6], [7], [8, 9]], [], YI, 124, q(10)),                  # NOUS / N'ALLONS / PAS CÉDER
    card(T1, V1, [[10], [11]], [], YI, 124, q(12)),
    card(T1, V1, [[12], [13]], [], YI, 124, c2),                           # NOUS / N'ALLONS (visage)
    card(T1, V1, [[14], [15], [16]], [14], YB, 130, c3, at={14: c2}),      # JAMAIS (rouge, sur l'attaque 150,86) / RENONCER / À, sur noir
    card(T1, V1, [[17], [18]], [], YI, 124, DROP, at={17: c3}),            # TOUT / CHANGER (visage, TOUT sur l'attaque 151,80)
    card(T2, V2, [[0], [1, 2]], [], YI, 124, q2(3)),                       # DANS / UN AN
    card(T2, V2, [[3], [4], [5], [6]], [5, 6], YI, 124, END, at={5: c_m4, 6: c_m4}),   # NOUS / POUVONS / TOUT / CHANGER rouge sur la mesure 164,22
]
_fc = {}
def font(px):
    px = int(round(px))
    if px not in _fc: _fc[px] = ImageFont.truetype(FONT, px, index=FIDX)
    return _fc[px]
DFONT = os.path.expanduser("~/Library/Fonts/CaslonGraphique-Opti.otf"); DSC, DTR = 1.22, 0.03   # mots impactants (rouges) : police dramatique
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
def line_w(li, em, tr):
    return sum(word_w(w[0], w[2], em, tr) for w in li) + gap(em, tr) * max(len(li) - 1, 0)
def card_em(c):
    fit = min(SAFE_W / (line_w(li, 100, c["tr"]) / 100) for li in c["lines"])
    return min(c["em"], fit)
def draw_text(img, t, on_image):
    """img BGR float ; cartons actifs à t (mots un par un, ligne recentrée comme la réf) ; mots rouges en Caslon Graphique."""
    act = [c for c in CARDS if c["t0"] - 1e-3 <= t < c["t1"]]
    if not act: return img
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dr = ImageDraw.Draw(layer)
    sh = Image.new("L", (W, H), 0); ds = ImageDraw.Draw(sh)
    for c in act:
        em = card_em(c); lh = em * 1.32; tr = c["tr"]
        vis = [[w for w in li if w[1] <= t + 1e-3] for li in c["lines"]]
        n_lines = len(c["lines"]); y0 = c["y"] * H - n_lines * lh / 2
        if c["y"] == YI: y0 = BASE_I - (n_lines - 1) * lh - em * 0.95          # posé par le bas, au-dessus de la légende TikTok
        for li_i, li in enumerate(vis):
            if not li: continue
            x = W / 2 - line_w(li, em, tr) / 2; yb = y0 + li_i * lh + em * 0.95       # ligne de base commune
            for wi, (word, tw, red) in enumerate(li):
                a = ease_out((t - tw) / 0.12)                     # apparition 4 images, sans rebond
                col = RED if red else WHITE
                f, tt = wfont(red, em); tt = tr * em if tt is None else tt
                for ch in word:
                    if on_image:
                        ds.text((x, yb), ch, font=f, anchor="ls", fill=int(235 * a), stroke_width=max(3, int(em * 0.06)), stroke_fill=int(235 * a))
                    dr.text((x, yb), ch, font=f, anchor="ls", fill=col + (int(255 * a),))
                    x += f.getlength(ch) + tt
                x += gap(em, tr) - tt
    out = img
    if on_image:                                                  # contour + ombre douce sombres
        m = np.asarray(sh.filter(ImageFilter.GaussianBlur(em * 0.10)), np.float32)[..., None] / 255
        out = out * (1 - 0.85 * m)
    lay = np.asarray(layer, np.float32) / 255
    rgb = lay[..., [2, 1, 0]]; al = lay[..., 3:4]
    return out * (1 - al) + rgb * al

# ---------------- étalonnage « sépia lavé » ----------------
TINT = np.array([0.93, 1.0, 1.05], np.float32)                  # B, G, R
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

# ---------------- liste des plans ----------------
def S(i, a, b, src, t_in, sp, mode, hint, z0, z1, txt=False, note=""):
    return dict(id=i, a=a, b=b, src=src, t_in=t_in, sp=sp, mode=mode, hint=hint, z0=z0, z1=z1, txt=txt, note=note)
# Chaque coupe = une attaque mesurée de Time ; chaque poussée finit sur la coupe suivante (donc sur une attaque).
# Plans du montage Nightcall gardés : Q1-Q4, B05 (-> B01), B06 (-> B02), B03, B07 (-> B04), V1, B08 ; Time n'a qu'une attaque franche
# par mesure après l'entrée, donc B02 meaux-04, B04 meaux-05 et B01 meaux-06 sortent.
# amfis-fin change de caméra à 4,70 s source (foule -> visage) : V1 commence après (attaque 162,19), B04 couvre « Dans un ».
SHOTS = [
    S("Q1", 0.0, c1, None, None, 100, "noir", None, 1, 1, True, "noir : NOUS N'ALLONS PAS (1 temps : attaques 146,11 -> 147,06)"),
    S("Q2", c1, c2, "bezons-citation", c1 + V1, 100, "face", (940, 300), 1.22, 1.30, True, "Bezons, synchro labiale, TÊTE rouge ; coupe sur « baisser »"),
    S("Q3", c2, c3, None, None, 100, "noir", None, 1, 1, True, "JAMAIS rouge sur noir, sur l'attaque 150,86 ; RENONCER À"),
    S("Q4", c3, DROP, "bezons-citation", c3 + V1, 100, "face", (940, 300), 1.30, 1.36, True, "Bezons, synchro, TOUT CHANGER ; coupe sur l'attaque 151,80"),
    S("B01", DROP, c_m2, "meaux-09", 1.0, 50, "fix", (1100, 540), 1.0, 1.08, note="GRANDE ENTRÉE de Time (152,77) : Meaux, foule immense, projecteur"),
    S("B02", c_m2, c_t4, "meaux-10", 1.5, 50, "face", (660, 300), 1.0, 1.06, note="mesure 156,58 : Meaux, Guetté, gestes"),
    S("B03", c_t4, c_m3, "amfis-02", 1.0, 50, "fix", (760, 540), 1.0, 1.03, note="4e temps 159,46 : AMFIS 2026, foule de dos, poing levé"),
    S("B04", c_m3, c_a3, "meaux-02", 1.0, 50, "fix", (900, 540), 1.0, 1.04, True, note="mesure 160,40 : Meaux, foule sombre (voix « Dans un » commence ici)"),
    S("V1", c_a3, c_m4, "amfis-fin", c_a3 + V2, 100, "face", (840, 300), 1.12, 1.18, True, "attaque 162,19 : AMFIS 2026, « an, nous pouvons » synchro"),
    S("B08", c_m4, END, "meaux-01", 1.0, 50, "fix", (950, 540), 1.0, 1.06, True, note="mesure 164,22 : TOUT CHANGER rouge, Meaux scène symétrique, fondu au noir"),
]
for sh in SHOTS:
    sh["rec"] = f30(sh["a"]); sh["dur"] = f30(sh["b"]) - sh["rec"]
    fps = SFPS.get(sh["src"], TFPS)
    sh["fps"] = fps; sh["n"] = int(round(sh["dur"] / TFPS * fps))        # images source à vitesse NORMALE (règle LISEZMOI)
    sh["clip"] = "C1_%s.mov" % sh["id"]

# ---------------- rendu d'un plan ----------------
# dl/amfis-fin.mp4 (YouTube HW03wZDi6Tk 1678-1694 s) a disparu : les mêmes images sont dans sources/C1-guette-amfis-03.mp4
# (1682,5-1690,5 s), soit amfis-fin = amfis-03 + 4,5 s (270 images à 60 i/s, alignement vérifié image par image sur hd/HD-C1.mp4).
# Ne sert qu'à l'image de V1 (amfis-fin 4,78-6,82 s) ; la voix 2 (dès 4,30 s) reste lue dans amfis-fin.
ALT = {"amfis-fin": ("C1-guette-amfis-03.mp4", 4.5)}
def src_file(src):
    if src in ALT and not os.path.exists(LOT + "/sources/" + SRC[src]): return ALT[src]
    return SRC[src], 0.0
def read_frames(src, t, n):
    f, off = src_file(src)
    p = subprocess.Popen([FF, "-v", "error", "-ss", "%.4f" % (t - off), "-i", LOT + "/sources/" + f, "-frames:v", str(n),
                          "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE)
    sz = 1920 * 1080 * 3
    for _ in range(n):
        b = p.stdout.read(sz)
        if len(b) < sz: break
        yield np.frombuffer(b, np.uint8).reshape(1080, 1920, 3)
    p.stdout.close(); p.wait()
def writer(path, fps):
    return subprocess.Popen([FF, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", "%dx%d" % (W, H), "-r", str(fps), "-i", "-",
                             "-c:v", "prores_ks", "-profile:v", "3", "-pix_fmt", "yuv422p10le", "-vendor", "apl0", path], stdin=subprocess.PIPE)
def unmark(fr, src, cx, vw):
    out = fr
    for (x0, y0, x1, y1) in WM.get(src, []):
        if cx + vw / 2 < x0 or cx - vw / 2 > x1: continue
        if out is fr: out = fr.copy()
        pad = 12; ya, yb, xa, xb = max(y0 - pad, 0), y1 + pad, max(x0 - pad, 0), min(x1 + pad, 1920)
        roi = out[ya:yb, xa:xb]; m = np.zeros(roi.shape[:2], np.uint8); m[pad:-pad, (x0 - xa):(x1 - xa)] = 255
        out[ya:yb, xa:xb] = cv2.inpaint(roi, m, 6, cv2.INPAINT_TELEA)
    return out
def render(sh):
    n, fps = sh["n"], sh["fps"]; w = writer(OUT + sh["clip"], fps); info = ""
    if sh["mode"] == "noir":
        for k in range(n):
            t = sh["a"] + k / fps
            img = grain(np.zeros((H, W, 3), np.float32) + 0.012, 0.012, 1.6)
            img = draw_text(img, t, False)
            w.stdin.write((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8).tobytes())
    else:
        s = int(round(sh["t_in"] * fps)); z0, z1 = sh["z0"], sh["z1"]
        sf, off = src_file(sh["src"]); sv = s - int(round(off * fps))          # image de départ dans le fichier réellement lu
        zoom = lambda f: z0 + (z1 - z0) * f / max(n - 1, 1)
        if sh["mode"] == "face":
            views, ok = plan_views(sf, sv, n, fps, speed=1.0, hint=sh["hint"], vh=1080, zoom=zoom)
            info = "visage" if ok else "SANS VISAGE"
        else:
            views, ok = plan_views(sf, sv, n, fps, speed=1.0, hint=sh["hint"], vh=1080, zoom=zoom, fixed=sh["hint"])
        k = 0
        for fr in read_frames(sh["src"], s / fps, n):
            cx, cy, vh = views[min(k, len(views) - 1)]; vw = vh * 9 / 16
            fr = unmark(fr, sh["src"], cx, vw)
            img = crop_view(fr.astype(np.float32) / 255, cx, cy, vw, W, H)
            img = grade(img)
            if sh["txt"]: img = draw_text(img, sh["a"] + k / fps / (sh["sp"] / 100), True)   # ralenti : image source k affichée à a + k/(fps × vitesse)
            w.stdin.write((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8).tobytes()); k += 1
        if k < n: info += " court:%d/%d" % (k, n)
    w.stdin.close(); w.wait()
    return info

# ---------------- audio ----------------
SR = 48000
def load(path, t=0.0, d=None):
    cmd = [FF, "-v", "error", "-ss", "%.4f" % t, "-i", path] + (["-t", "%.4f" % d] if d else []) + ["-f", "f32le", "-ac", "2", "-ar", str(SR), "-"]
    return np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, np.float32).reshape(-1, 2).copy()
def fade(x, fi, fo):
    n = len(x); a = np.ones(n, np.float32)
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
def env_duck(t, spans, g):
    e = np.ones_like(t)
    for a, b in spans:
        e = np.minimum(e, np.interp(t, [a - 0.25, a, b, b + 0.4], [1, db(g), db(g), 1]))
    return e
V1_IN, V1_OUT = 5.30, 11.56          # voix 1 (source) : juste avant « nous » -> coupe avant « Et ça commencera… »
V2_IN, V2_OUT = 4.30, 7.42           # voix 2 (source) : « Dans un an, nous pouvons tout changer. »
def build_audio():
    n = int(round(END * SR)); mix = np.zeros((n, 2), np.float32)
    def put(x, t):
        i = max(int(round(t * SR)), 0); j = min(n, i + len(x)); mix[i:j] += x[:j - i]
    v1 = fade(load(LOT + "/sources/" + SRC["bezons-citation"], V1_IN, V1_OUT - V1_IN), 0.04, 0.10)
    v2 = fade(load(LOT + "/sources/" + SRC["amfis-fin"], V2_IN, V2_OUT - V2_IN), 0.03, 0.12)
    lv, _ = lufs(np.concatenate([v1, v2])); v1 *= db(-15 - lv); v2 *= db(-15 - lv)
    m = load(MUSIC, C_OFF, END + 0.05)[:n]; t = np.arange(len(m)) / SR
    lm, _ = lufs(m[int(DROP * SR):]); m *= db(-14 - lm)           # après l'entrée : -14 LUFS
    # montée de Time sous la citation (déjà ~8 dB sous l'entrée) un peu baissée, plein pot pile sur l'attaque de la grande entrée
    e = np.where(t < tl("entree") - 0.004, db(-2.5), 1.0)
    e = e * np.clip(t / 0.01, 0, 1)                              # anti-clic (le morceau démarre 13 ms avant l'attaque 146,11)
    e = e * env_duck(t, [(V2_IN - V2 + 0.05, V2_OUT - V2)], -9.0)  # voix 2 bien lisible sur l'orchestre
    e = e * np.clip((END - t) / 1.0, 0, 1) ** 1.5
    m = m * e[:, None].astype(np.float32)
    put(m, 0.0); put(v1, V1_IN - V1); put(v2, V2_IN - V2)
    sf_write(OUT + "C1-musique.wav", m); vv = np.zeros_like(mix); vv[int(round((V1_IN - V1) * SR)):][:len(v1)] += v1[:n]
    i2 = int(round((V2_IN - V2) * SR)); vv[i2:i2 + len(v2)] += v2[:n - i2]; sf_write(OUT + "C1-voix.wav", vv)
    tmp = OUT + "_tmp_mix.wav"; sf_write(tmp, mix); g = 0.0; li, _ = lufs(mix)
    for _ in range(3):
        g += -14.0 - li
        subprocess.run([FF, "-v", "error", "-y", "-i", tmp, "-af", "volume=%.2fdB,alimiter=limit=0.80:attack=3:release=60:level=false,aresample=192000,alimiter=limit=0.82:attack=1:release=40:level=false,aresample=48000" % g,
                        "-c:a", "pcm_s24le", OUT + "C1-mix.wav"], check=True)
        li, tp = lufs(load(OUT + "C1-mix.wav"))
        if abs(li + 14) < 0.3 and tp < -1.0: break
    os.remove(tmp)
    return "mix %.1f LUFS, true peak %.1f dBTP ; voix %.1f, Time après l'entrée %.1f LUFS d'origine" % (li, tp, lv, lm)

# ---------------- plan-C1.json ----------------
def write_plan():
    vid = []
    for sh in SHOTS:
        it = {"id": sh["id"], "clip": sh["clip"], "folder": "C1", "path": OUT + sh["clip"], "s": 0, "e": sh["n"], "clip_fps": sh["fps"],
              "rec": sh["rec"], "dur": sh["dur"], "track": 1, "note": sh["note"]}
        if sh["src"]:
            sp = sh["sp"]; used = sh["n"] * sp / 100 / sh["fps"]
            f = SRC[sh["src"]]; f = "lot2/sources/" + f if not f.startswith("..") else "lot2/_claude/gen/C1/dl/amfis-fin.mp4"
            it["source"] = {"fichier": f, "in_s": round(sh["t_in"], 3), "out_s": round(sh["t_in"] + used, 3)}
            it["effets"] = "recadrage 9:16 %s, poussée %.2f->%.2f, sépia lavé + vignette + grain, logos effacés%s" % (
                "suivi visage" if sh["mode"] == "face" else "fixe", sh["z0"], sh["z1"], ", texte cuit" if sh["txt"] else "")
            if sp != 100: it["speed_pct"] = sp; it["retime"] = "optical_flow"
        else:
            it["effets"] = "noir + grain, texte cuit (Baskerville SemiBold espacée, mot-clé CaslonGraphique-Opti rouge)"
        if sh["id"] == "B08": it["fade_out_s"] = 0.8
        vid.append(it)
    plan = {"name": "C1 - Citation cine - Guette", "fps": 30, "w": 1080, "h": 1920, "duree_s": END,
            "note": "Aperçu lot 2. Plans ProRes 9:16 prêts (recadrés, étalonnés, texte cuit). Ralentis dans Resolve : speed_pct + Optical Flow ; e-s = images source à vitesse normale. Générateur : lot2/_claude/gen/C1/genC1.py",
            "musique": {"fichier": "lot2/sons/C1-zimmer-time_complet.wav", "titre": "Hans Zimmer - Time (Inception), WaterTower Music",
                        "debut_dans_complet_s": C_OFF, "fin_dans_complet_s": round(C_OFF + END, 3), "bpm": 63.0,
                        "grande_entree_complet_s": A["entree"], "drop_timeline_s": round(DROP, 3),
                        "attaques_complet_s": A, "coupes_timeline_s": sorted({round(s["a"], 4) for s in SHOTS if s["a"] > 0}),
                        "coupes": "chaque coupe sur une attaque mesurée (temps_forts.py) : noires de la montée sous la citation, puis une par mesure (+ 4e temps 159,46) après la grande entrée"},
            "citations": [{"source": "lot2/sources/C1-guette-bezons-citation.mp4 5,44-11,44 s (YouTube 9Cgr6La_XaE, 1021,9-1028,1 s), timeline = source - %.3f" % V1, "texte": C["texte"]},
                          {"source": "lot2/_claude/gen/C1/dl/amfis-fin.mp4 4,38-7,30 s (YouTube HW03wZDi6Tk ≈1682,4-1685,3 s), timeline = source + %.3f" % -V2, "texte": "Dans un an, nous pouvons tout changer."}],
            "textes": [{"t0": round(c["t0"], 2), "t1": round(c["t1"], 2), "lignes": [" ".join(w[0] for w in li) for li in c["lines"]],
                        "rouge": [w[0] for li in c["lines"] for w in li if w[2]]} for c in CARDS],
            "video": vid,
            "audio": [{"id": "mix", "clip": "C1-mix.wav", "folder": "C1", "path": OUT + "C1-mix.wav", "rec": 0, "track": 1,
                       "note": "mix final -14 LUFS : Time de %.3f s (morceau complet) posé en 0, montée -2,5 dB sous la voix 1, grande entrée à %.3f s, voix 2 à %.3f s, duck -9 dB sous la voix 2 ; stems C1-musique.wav / C1-voix.wav" % (C_OFF, DROP, V2_IN - V2)}]}
    json.dump(plan, open(D + "plan-C1.json", "w"), indent=1, ensure_ascii=False)

# ---------------- aperçu ffmpeg 540×960 ----------------
def preview():
    out = ROOT + "/preview/apercu-C1.mp4"; args = [FF, "-v", "error", "-y"]; fl = []
    for i, sh in enumerate(SHOTS):
        args += ["-i", OUT + sh["clip"]]; sp = sh["sp"] / 100
        fl.append("[%d:v]setpts=(PTS-STARTPTS)/%.4f,fps=30,trim=end_frame=%d,setpts=PTS-STARTPTS,scale=540:960,setsar=1%s[v%d]" % (
            i, sp, sh["dur"], ",fade=t=out:st=%.3f:d=0.8" % (sh["dur"] / 30 - 0.8) if sh["id"] == "B08" else "", i))
    args += ["-i", OUT + "C1-mix.wav"]
    fl.append("".join("[v%d]" % i for i in range(len(SHOTS))) + "concat=n=%d:v=1:a=0[v]" % len(SHOTS))
    args += ["-filter_complex", ";".join(fl), "-map", "[v]", "-map", "%d:a" % len(SHOTS), "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p",
             "-c:a", "aac", "-b:a", "192k", "-shortest", out]
    subprocess.run(args, check=True)
    return out

if __name__ == "__main__":
    only = None
    for a in sys.argv:
        if a.startswith("only="): only = a[5:].split(",")
    if "plans" in sys.argv:
        for sh in SHOTS:
            if only and sh["id"] not in only: continue
            print(sh["id"], sh["dur"], "img tl", sh["n"], "img src", render(sh), flush=True)
    if "audio" in sys.argv: print(build_audio())
    write_plan()
    if "apercu" in sys.argv: print(preview())
    print("total", sum(s["dur"] for s in SHOTS) / 30, "s ;", len(SHOTS), "plans ; plus court", min(s["dur"] for s in SHOTS) / 30, "s")
