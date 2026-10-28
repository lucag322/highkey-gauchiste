# Style 3 — Citation ciné (réf @coln333), plein écran 9:16, hors Resolve.
# Plans ProRes recadrés (visage suivi) + étalonnés sépia lavé + vignette + grain, texte cuit sur les plans parlés.
# Ralentis : PAS précalculés. Clip livré à vitesse normale (e-s = durée_tl/30 × fps_source), "speed_pct" + "retime" dans plan3.json.
# Usage : python gen3.py [plans] [audio] [apercu] [only=ID,ID]
import sys, os, json, math, subprocess
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
ROOT = "/Users/luca.grousset/Movies/highkey-gauchiste"
sys.path.insert(0, ROOT + "/_claude/outils")
from framing import plan_views
from fx import crop_view, vignette, grain, gblur, ease_out
from words import tokens, clean
FF = "/opt/homebrew/bin/ffmpeg"
D = ROOT + "/_claude/gen/3/"; OUT = D + "out/"; os.makedirs(OUT, exist_ok=True)
SRC = {1: "1-melenchon-valence-amfis.mp4", 3: "3-melenchon-huma-citation.mp4", 5: "5-melenchon-saintdenis-smic.mp4"}
SFPS = {1: 30, 3: 50, 5: 30}
W, H, TFPS = 1080, 1920, 30
RED = (228, 0, 43); WHITE = (242, 238, 232)
FONT = "/System/Library/Fonts/Supplemental/Baskerville.ttc"; FIDX = 4      # Baskerville SemiBold
TRACK = 0.20                                                              # approche très large (réf)
WM = {1: (1570, 50, 1880, 185), 5: (1570, 50, 1880, 185)}               # filigrane MELENCHON2027.fr (px source)

# ---------------- temps ----------------
MUSIC = ROOT + "/sons/3-coln333_sans-voix.wav"
DROP = 10.40                         # fin de la citation (95,24 s source) = drop de la musique
BEATS = [0.0, 0.627, 1.277, 1.904, 2.531, 3.181, 3.831, 4.481, 5.132, 5.782, 6.432, 7.082, 7.709, 8.359, 8.986, 9.636,
         10.263, 10.913, 11.54, 12.167, 12.794, 13.444, 14.095, 14.745, 15.395, 16.045, 16.695, 17.345, 17.995, 18.622,
         19.273, 19.923, 20.55, 21.2, 21.85, 22.5]            # librosa sur le fichier sans voix (92,3 BPM), 0 = drop
def tb(k): return DROP + BEATS[k]
END = 33.6
V1 = 84.85                           # voix 1 : timeline = source - V1 (citation 85,02-95,24)
V2 = 119.355 - tb(26)                # voix 2 : « Ce n'est pas vrai que nous avons perdu d'avance. » 119,36-121,98
def f30(t): return int(round(t * TFPS))

# ---------------- textes (mot à mot du dérush) ----------------
DR = json.load(open(ROOT + "/_claude/derush.json"))["styles"]["3"]
T1 = tokens(DR["citation"]["words"]); T2 = tokens(DR["citations_alternatives"][0]["words"])
assert len(T1) == 18 and len(T2) == 9, (len(T1), len(T2))
def up(t): return clean(t["w"], keep_quotes=False).replace("'", "’").upper()
def card(toks, off, lines, red, y, em_max, t1, first_q=False, last_q=False):
    L = []
    for li in lines:
        L.append([[up(toks[i]), toks[i]["start"] - off, i in red] for i in li])
    # règle Luca : jamais de guillemets à l'écran (first_q / last_q ignorés)
    return {"lines": L, "t0": L[0][0][1], "t1": t1, "y": y, "em": em_max, "tr": TRACK if y == YB else 0.13}
YB, YI = 0.47, 0.70                  # noir : centre ; image : bas du tiers central (au-dessus de l'UI TikTok)
CARDS = [
    card(T1, V1, [[0], [1]], [], YB, 130, T1[2]["start"] - V1, first_q=True),
    card(T1, V1, [[2, 3], [4]], [], YB, 130, T1[5]["start"] - V1),
    card(T1, V1, [[5], [6]], [6], YB, 130, T1[7]["start"] - V1),
    card(T1, V1, [[7, 8, 9], [10]], [], YI, 124, T1[11]["start"] - V1),
    card(T1, V1, [[11]], [11], YB, 150, T1[12]["start"] - V1),
    card(T1, V1, [[12], [13]], [], YI, 124, T1[14]["start"] - V1),
    card(T1, V1, [[14]], [], YI, 124, T1[15]["start"] - V1),
    card(T1, V1, [[15, 16], [17]], [], YI, 124, DROP, last_q=True),
    card(T2, V2, [[0, 1], [2, 3]], [2, 3], YI, 124, T2[4]["start"] - V2),
    card(T2, V2, [[4, 5], [6]], [], YI, 124, T2[7]["start"] - V2),
    card(T2, V2, [[7], [8]], [], YI, 124, 122.45 - V2),
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
    fit = min(0.90 * W / (line_w(li, 100, c["tr"]) / 100) for li in c["lines"])
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
# (id, rec_debut_s, rec_fin_s, source, t_in source, vitesse %, mode, indice (cx,cy) px source, zoom0, zoom1, texte, note)
def S(i, a, b, src, t_in, sp, mode, hint, z0, z1, txt=False, note=""):
    return dict(id=i, a=a, b=b, src=src, t_in=t_in, sp=sp, mode=mode, hint=hint, z0=z0, z1=z1, txt=txt, note=note)
SHOTS = [
    S("Q1", 0.0, T1[7]["start"] - V1, None, None, 100, "noir", None, 1, 1, True, "citation sur noir"),
    S("Q2", T1[7]["start"] - V1, T1[11]["start"] - V1, 3, T1[7]["start"], 100, "face", (900, 400), 1.12, 1.18, True, "Mélenchon, synchro labiale"),
    S("Q3", T1[11]["start"] - V1, T1[12]["start"] - V1, None, None, 100, "noir", None, 1, 1, True, "MAÎTRISABLE rouge sur noir"),
    S("Q4", T1[12]["start"] - V1, DROP, 3, T1[12]["start"], 100, "face", (900, 400), 1.18, 1.26, True, "Mélenchon serré, synchro"),
    S("B01", tb(0), tb(2), 1, 56.5, 50, "fix", (1140, 540), 1.0, 1.06, note="Valence, de dos sur la passerelle vers la scène"),
    S("B02", tb(2), tb(3), 1, 67.0, 100, "fix", (900, 540), 1.0, 1.08, note="Valence, drone foule immense"),
    S("B03", tb(3), tb(5), 3, 75.0, 100, "fix", (960, 540), 1.0, 1.06, note="Huma, foule au soleil, tente LFI"),
    S("B04", tb(5), tb(6), 1, 73.0, 50, "fix", (960, 540), 1.0, 1.05, note="Valence, mer de drapeaux"),
    S("B05", tb(6), tb(8), 1, 116.0, 50, "face", (950, 400), 1.15, 1.24, note="Valence, Mélenchon serré"),
    S("B06", tb(8), tb(9), 1, 96.0, 50, "fix", (960, 540), 1.0, 1.05, note="Valence, poings levés, scène au loin"),
    S("B07", tb(9), tb(11), 5, 3.3, 50, "face", (1200, 350), 1.0, 1.08, note="Saint-Denis, Mélenchon serré poing fermé"),
    S("B08", tb(11), tb(12), 3, 218.0, 50, "fix", (960, 540), 1.0, 1.05, note="Huma, foule bras levés"),
    S("B09", tb(12), tb(14), 1, 150.0, 50, "face", (950, 400), 1.12, 1.22, note="Valence, Mélenchon index levé (« la victoire est possible »)"),
    S("B10", tb(14), tb(15), 5, 101.0, 100, "fix", (1100, 540), 1.0, 1.08, note="Saint-Denis, place noire de monde"),
    S("B11", tb(15), tb(17), 1, 44.5, 50, "fix", (1000, 540), 1.0, 1.05, note="Valence, de dos sur le chemin du lac vers la scène"),
    S("B12", tb(17), tb(18), 3, 112.0, 50, "fix", (960, 540), 1.0, 1.05, note="Huma, chapiteau, foule"),
    S("B13", tb(18), tb(20), 1, 158.0, 100, "fix", (790, 540), 1.0, 1.06, note="Valence, de dos au pupitre face à la foule"),
    S("B14", tb(20), tb(21), 3, 286.0, 50, "fix", (960, 540), 1.0, 1.05, note="Huma, foule immense au soleil"),
    S("B15", tb(21), tb(23), 3, 100.0, 50, "face", (900, 400), 1.1, 1.2, note="Huma, Mélenchon au pupitre"),
    S("B16", tb(23), tb(24), 5, 107.0, 50, "fix", (960, 540), 1.0, 1.05, note="Saint-Denis, drapeaux"),
    S("B17", tb(24), tb(26), 1, 13.0, 100, "fix", (960, 540), 1.0, 1.05, note="Valence, drone scène sur le lac"),
    S("V1", tb(26), tb(31), 3, tb(26) + V2, 100, "face", (900, 400), 1.10, 1.22, True, "Huma, « Ce n'est pas vrai que nous avons perdu d'avance. » synchro, poussée lente"),
    S("B18", tb(31), tb(33), 5, 236.0, 50, "fix", (960, 540), 1.0, 1.06, note="Saint-Denis, foule vue d'en haut"),
    S("B19", tb(33), END, 5, 126.0, 50, "fix", (1000, 540), 1.0, 1.05, note="Saint-Denis, de dos face à la foule, fondu au noir"),
]
for sh in SHOTS:
    sh["rec"] = f30(sh["a"]); sh["dur"] = f30(sh["b"]) - sh["rec"]
    fps = SFPS.get(sh["src"], TFPS)
    sh["fps"] = fps; sh["n"] = int(round(sh["dur"] / TFPS * fps))        # images source à vitesse NORMALE (règle LISEZMOI)
    sh["clip"] = "3_%s.mov" % sh["id"]

# ---------------- rendu d'un plan ----------------
def read_frames(src, t, n):
    p = subprocess.Popen([FF, "-v", "error", "-ss", "%.4f" % t, "-i", ROOT + "/sources/" + SRC[src], "-frames:v", str(n),
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
    if src not in WM: return fr
    x0, y0, x1, y1 = WM[src]
    if cx + vw / 2 < x0: return fr
    fr = fr.copy(); pad = 12
    roi = fr[y0 - pad:y1 + pad, x0 - pad:min(x1 + pad, 1920)]
    m = np.zeros(roi.shape[:2], np.uint8); m[pad:-pad, pad:] = 255
    fr[y0 - pad:y1 + pad, x0 - pad:min(x1 + pad, 1920)] = cv2.inpaint(roi, m, 6, cv2.INPAINT_TELEA)
    return fr
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
        zoom = lambda f: z0 + (z1 - z0) * f / max(n - 1, 1)
        if sh["mode"] == "face":
            views, ok = plan_views(SRC[sh["src"]], s, n, fps, speed=1.0, hint=sh["hint"], vh=1080, zoom=zoom)
            info = "visage" if ok else "SANS VISAGE"
        else:
            views, ok = plan_views(SRC[sh["src"]], s, n, fps, speed=1.0, hint=sh["hint"], vh=1080, zoom=zoom, fixed=sh["hint"])
        k = 0
        for fr in read_frames(sh["src"], s / fps, n):
            cx, cy, vh = views[min(k, len(views) - 1)]; vw = vh * 9 / 16
            fr = unmark(fr, sh["src"], cx, vw)
            img = crop_view(fr.astype(np.float32) / 255, cx, cy, vw, W, H)
            img = grade(img)
            if sh["txt"]: img = draw_text(img, sh["a"] + k / fps, True)
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
def kweight_lufs(x):
    # LUFS approx (ITU BS.1770 : filtres K + porte -70 / -10) via ffmpeg ebur128 serait plus lent ; ici ffmpeg loudnorm en mesure
    p = OUT + "_tmp_meas.wav"; sf_write(p, x)
    r = subprocess.run([FF, "-v", "info", "-i", p, "-af", "loudnorm=print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
    js = json.loads(r[r.rindex("{"):r.rindex("}") + 1]); os.remove(p)
    return float(js["input_i"]), float(js["input_tp"])
def sf_write(p, x):
    import soundfile as sf; sf.write(p, x, SR, subtype="PCM_24")
def db(g): return 10 ** (g / 20)
def build_audio():
    src3 = ROOT + "/sources/" + SRC[3]; n = int(END * SR); mix = np.zeros((n, 2), np.float32)
    def put(x, t):
        i = int(round(t * SR)); j = min(n, i + len(x)); mix[i:j] += x[:j - i]
    v1 = fade(load(src3, V1, 95.42 - V1), 0.02, 0.15)
    v2 = fade(load(src3, 119.25, 122.25 - 119.25), 0.03, 0.2)
    mus = load(MUSIC)
    # niveaux : voix -> -15 LUFS, musique -> -14 LUFS (corps), nappe pré-drop -> -30 LUFS
    lv, _ = kweight_lufs(np.concatenate([v1, v2])); lm, _ = kweight_lufs(mus)
    v1 *= db(-15 - lv); v2 *= db(-15 - lv); mus *= db(-14 - lm)
    # nappe : musique passe-bas (12-22,6 s) sous la citation, comme la réf (voix sur nappe ~-22 dB puis montée au drop)
    nap = mus[int(12.0 * SR):int((12.0 + DROP + 0.1) * SR)].copy()
    b, a = [None] * 2
    from scipy.signal import butter, sosfilt
    sos = butter(4, 450, "low", fs=SR, output="sos"); nap = sosfilt(sos, nap, axis=0).astype(np.float32)
    nap = fade(nap * db(-13), 1.5, 0.12)
    put(v1, 0.0); put(nap, 0.0)
    m = mus[: n - int(DROP * SR)].copy()
    t = DROP + np.arange(len(m)) / SR
    env = np.ones(len(m), np.float32)
    d0, d1 = 119.25 - V2 - 0.15, 122.2 - V2           # duck sous la voix 2
    duck = db(-9)
    env = np.where(t < d0, 1, np.where(t < d0 + 0.2, 1 + (duck - 1) * (t - d0) / 0.2, np.where(t < d1, duck, np.where(t < d1 + 0.35, duck + (1 - duck) * (t - d1) / 0.35, 1))))
    fo0 = END - 1.1; env = env * np.clip((END - t) / 1.1, 0, 1) ** 1.5 * (t >= fo0) + env * (t < fo0)
    put(m * env[:, None].astype(np.float32), DROP); put(v2, 119.25 - V2)
    # gain vers -14 LUFS puis limiteur (crête < -1 dBFS), deux passes
    tmp = OUT + "_tmp_mix.wav"; sf_write(tmp, mix); g = 0.0
    for _ in range(3):
        li, _tp = kweight_lufs(mix * db(g)) if g == 0.0 else (li2, None)
        g += -14.0 - li
        subprocess.run([FF, "-v", "error", "-y", "-i", tmp, "-af", "volume=%.2fdB,alimiter=limit=0.80:attack=3:release=60:level=false,aresample=192000,alimiter=limit=0.82:attack=1:release=40:level=false,aresample=48000" % g,
                        "-c:a", "pcm_s24le", OUT + "3-mix.wav"], check=True)
        li2, tp2 = kweight_lufs(load(OUT + "3-mix.wav"))
        if abs(li2 + 14) < 0.3 and tp2 < -1.0: break
    os.remove(tmp); mix = load(OUT + "3-mix.wav")
    sf_write(OUT + "3-voix.wav", np.pad(v1, ((0, 0), (0, 0)))); sf_write(OUT + "3-musique.wav", mus)
    li2, tp2 = kweight_lufs(mix)
    return "mix %.1f LUFS, true peak %.1f dBTP (voix %.1f, musique %.1f d'origine)" % (li2, tp2, lv, lm)

# ---------------- plan3.json ----------------
def write_plan():
    vid = []
    for sh in SHOTS:
        it = {"id": sh["id"], "clip": sh["clip"], "folder": "gen3", "path": OUT + sh["clip"], "s": 0, "e": sh["n"], "clip_fps": sh["fps"],
              "rec": sh["rec"], "dur": sh["dur"], "track": 1, "note": sh["note"]}
        if sh["src"]:
            sp = sh["sp"]; used = sh["n"] * sp / 100 / sh["fps"]
            it["source"] = {"fichier": "sources/" + SRC[sh["src"]], "in_s": round(sh["t_in"], 3), "out_s": round(sh["t_in"] + used, 3)}
            it["effets"] = "recadrage 9:16 %s, zoom %.2f->%.2f, sépia lavé + vignette + grain%s" % (
                "suivi visage" if sh["mode"] == "face" else "fixe", sh["z0"], sh["z1"], ", texte cuit" if sh["txt"] else "")
            if sp != 100: it["speed_pct"] = sp; it["retime"] = "optical_flow"
        else:
            it["effets"] = "noir + grain, texte cuit (Baskerville SemiBold, approche 0,20 em)"
        if sh["id"] == "B19": it["fade_out_s"] = 0.7
        vid.append(it)
    plan = {"name": "3 - Citation cine", "fps": 30, "w": 1080, "h": 1920, "duree_s": END,
            "note": "Plans ProRes 9:16 prêts (recadrés, étalonnés, texte cuit). Ralentis à faire dans Resolve : speed_pct + Optical Flow / Speed Warp ; e-s = images source à vitesse normale. Générateur : _claude/gen/3/gen3.py",
            "musique": {"fichier": "sons/3-coln333_sans-voix.wav", "drop_timeline_s": DROP, "bpm": 92.3, "beats_timeline_s": [round(tb(k), 3) for k in range(len(BEATS))]},
            "textes": [{"t0": round(c["t0"], 2), "t1": round(c["t1"], 2), "lignes": [" ".join(w[0] for w in li) for li in c["lines"]],
                        "rouge": [w[0] for li in c["lines"] for w in li if w[2]]} for c in CARDS],
            "video": vid,
            "audio": [{"id": "mix", "clip": "3-mix.wav", "folder": "gen3", "path": OUT + "3-mix.wav", "rec": 0, "track": 1,
                       "note": "mix final -14 LUFS (voix 84,85-95,42 s et 119,25-122,25 s de la source 3, nappe, musique au drop, duck -9 dB sous la voix 2)"}]}
    json.dump(plan, open(ROOT + "/_claude/plan3.json", "w"), indent=1, ensure_ascii=False)

# ---------------- aperçu ffmpeg 540×960 ----------------
def preview():
    out = ROOT + "/exports/apercu-3-citation-cine.mp4"; args = [FF, "-v", "error", "-y"]; fl = []
    for i, sh in enumerate(SHOTS):
        args += ["-i", OUT + sh["clip"]]
        sp = sh["sp"] / 100
        fl.append("[%d:v]setpts=(PTS-STARTPTS)/%.4f,fps=30,trim=end_frame=%d,setpts=PTS-STARTPTS,scale=540:960,setsar=1%s[v%d]" % (
            i, sp, sh["dur"], ",fade=t=out:st=%.3f:d=0.7" % (sh["dur"] / 30 - 0.7) if sh["id"] == "B19" else "", i))
    args += ["-i", OUT + "3-mix.wav"]
    fl.append("".join("[v%d]" % i for i in range(len(SHOTS))) + "concat=n=%d:v=1:a=0[v]" % len(SHOTS))
    args += ["-filter_complex", ";".join(fl), "-map", "[v]", "-map", "%d:a" % len(SHOTS), "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p",
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
    print("total", sum(s["dur"] for s in SHOTS) / 30, "s ;", len(SHOTS), "plans")
