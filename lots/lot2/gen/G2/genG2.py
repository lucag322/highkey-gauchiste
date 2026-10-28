# Lot 2 / G2 — Glow, Manon Aubry (plénière de Strasbourg, état de l'Union 2026). Copie de la structure de _claude/gen/4/gen4.py (test-4-glow).
# Partie A : la phrase (voix + cartons mot à mot, TOUT en blanc, halo bleu pris dans le mur de l'hémicycle, contour sombre, Avenir Next Bold Italic).
# Partie B : boom de Sienna (The Marías) juste après « Leyen », rafale de plans coupés sur les temps (0,8275 s), N&B sur le 1er temps, fondu au noir.
# Ralentis : PAS précalculés. Clip livré à vitesse normale (n = durée_tl × fps_source), speed_pct + retime dans plan-G2.json ; aperçu = setpts.
# Usage : python genG2.py [plans] [audio] [apercu] [only=ID,ID]
import sys, os, json, subprocess, colorsys
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
HK = "/Users/luca.grousset/Movies/highkey-gauchiste"
L2 = HK + "/lot2"
sys.path.insert(0, HK + "/_claude/outils")
import framing
framing.ROOT = L2; framing.CACHE = L2 + "/_claude/cache/faces"          # sources du lot 2
from framing import plan_views
from fx import crop_view, vignette, grain, gblur, ease_out
from words import tokens, clean
FF = "/opt/homebrew/bin/ffmpeg"
D = L2 + "/_claude/gen/G2/"; OUT = D + "out/"; os.makedirs(OUT, exist_ok=True)
W, H, TFPS = 1080, 1920, 30
FONT = "/System/Library/Fonts/Avenir Next.ttc"; FIDX = 1                  # Avenir Next Bold Italic (test 4)

# ---------------- sources ----------------
SRC = {"SOT": "G2-aubry-sotEU-2026.mp4", "PLE": "G2-aubry-plenaire-2025-10.mp4"}
SFPS = {"SOT": 25, "PLE": 25}
B_SOT = (200, 0, 1720, 752)      # bas du cadre sur le bandeau uni du pupitre (haut 726) ; logo hémicycle à y≈756 exclu
B_PLE = (200, 0, 1720, 788)      # plénière 2025 : pupitre 764, logo à y≈795 exclu

# ---------------- halo : couleur prise dans la vidéo (mur bleu nuit de l'hémicycle, éclairci) ----------------
def wall_color():
    b = subprocess.run([FF, "-v", "error", "-ss", "24.5", "-i", L2 + "/sources/" + SRC["SOT"], "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                       capture_output=True, check=True).stdout
    fr = np.frombuffer(b, np.uint8).reshape(1080, 1920, 3)
    r, g, bl = fr[40:300, 150:600].reshape(-1, 3).mean(0) / 255
    h, s, v = colorsys.rgb_to_hsv(r, g, bl)
    rr, gg, bb = colorsys.hsv_to_rgb(h, 0.62, 1.0)          # même teinte, lumineuse
    return (r, g, bl), (rr, gg, bb)
WALL, GLOW = wall_color()
GLOW_BGR = np.array(GLOW[::-1], np.float32)
GLOW_HEX = "#%02X%02X%02X" % tuple(int(c * 255) for c in GLOW)

# ---------------- temps ----------------
MUSIC = L2 + "/sons/G2-the-marias-sienna_complet.wav"
V0, VOUT = 20.10, 28.03          # voix (fichier SOT) : « Pendant » attaque à 20,20 ; « Leyen » finit à 28,00
DROP = VOUT - V0                 # 7,93 : boom de Sienna (26,04 s du morceau complet) pile après « Leyen »
C_DROP = 26.04; C_OFF = C_DROP - DROP
P = 0.8275                       # 1 temps = 2 pulsations mesurées (kick 26,04 / caisse claire 26,87 / kick 27,69 ...)
CUTS_C = [C_DROP + k * P for k in range(9)]
def tc(c): return c - C_OFF
C = [tc(c) for c in CUTS_C]
END = C[-1]                      # 14,55 s (règle : 15 s max)
def f30(t): return int(round(t * TFPS))

# ---------------- texte (mot à mot du dérush, derush-AG.json G2) ----------------
DR = json.load(open(L2 + "/_claude/derush-AG.json"))["figures"]["G2"]["phrase"]
MOTS = [dict(m) for m in DR["mots"]]
MOTS[0]["start"] = 20.20; MOTS[11]["start"] = 24.00     # attaques mesurées à l'énergie (dérush en avance de 0,2 / 0,08 s)
T = tokens(MOTS)
def up(t): return clean(t["w"], keep_quotes=False).replace("'", "’").upper()
GROUPS = [2, 1, 1, 1, 1, 1, 3, 2, 2, 1, 1, (1, 3)]      # (a, b) = carton sur 2 lignes
# PENDANT CE | TEMPS-LÀ | LES | MILLIARDAIRES | EUX | CONTINUENT | DE SE GAVER | VOILÀ L'ÉTAT | DE VOTRE | UNION | EUROPÉENNE | MADAME / VON DER LEYEN
assert sum(sum(g) if isinstance(g, tuple) else g for g in GROUPS) == len(T), (len(T), [t["w"] for t in T])
CARDS, i = [], 0
for g in GROUPS:
    lines = []
    for z in (g if isinstance(g, tuple) else (g,)):
        lines.append([[up(t), t["start"] - V0] for t in T[i:i + z]]); i += z
    CARDS.append({"lines": lines, "words": [w for li in lines for w in li], "t0": lines[0][0][1]})
for k, c in enumerate(CARDS): c["t1"] = CARDS[k + 1]["t0"] if k + 1 < len(CARDS) else DROP
XL, YB, EM_MAX, WFRAC = 0.065, 0.655, 150, 0.86   # cartons calés à gauche comme le test 4, ligne de base à 65 % de la hauteur
_fc = {}
def font(px):
    px = int(round(px))
    if px not in _fc: _fc[px] = ImageFont.truetype(FONT, px, index=FIDX)
    return _fc[px]
def card_em(c):
    w100 = max(font(100).getlength(" ".join(w[0] for w in li)) for li in c["lines"]) / 100
    return min(EM_MAX, WFRAC * W / w100)
def draw_text(img, t):
    act = [c for c in CARDS if c["t0"] - 1e-3 <= t < c["t1"]]
    if not act: return img
    c = act[0]; em = card_em(c); f = font(em)
    m = Image.new("L", (W, H), 0); dm = ImageDraw.Draw(m)
    sp = f.getlength(" ")
    for li_i, li in enumerate(c["lines"]):
        x = XL * W; yb = YB * H + li_i * em * 1.12
        for word, tw in li:
            if tw <= t + 1e-3:
                a = ease_out((t - tw) / 0.10)                # entrée 3 images, forte décélération, sans rebond
                dm.text((x, yb + 14 * (1 - a)), word, font=f, anchor="ls", fill=int(255 * a))
            x += f.getlength(word) + sp
    mk = np.asarray(m, np.float32) / 255
    if mk.max() == 0: return img
    # halo coloré DERRIÈRE les lettres (2 flous, le large boosté) ; contour sombre serré ; lettres blanches nettes
    g = np.clip(gblur(mk, em * 0.20) * 1.9 + gblur(mk, em * 0.07) * 1.3, 0, 1)[..., None]
    out = img * (1 - 0.35 * g) + GLOW_BGR * g * 0.95
    st = cv2.dilate(mk, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
    st = gblur(st, 0.8)[..., None]
    out = out * (1 - 0.85 * st) + np.array([0.12, 0.04, 0.03], np.float32) * 0.85 * st   # contour bleu-noir
    a = mk[..., None]
    return out * (1 - a) + a

# ---------------- étalonnage glow (LUT douce type s4, neutre-froid) + SoftGlow ----------------
VIG = None
def grade(img, glow=0.5, nb=False):
    global VIG
    L = img @ np.array([0.0722, 0.7152, 0.2126], np.float32)
    x = img * img * (3 - 2 * img) * 0.2 + img * 0.8          # S douce
    x = L[..., None] + (x - L[..., None]) * (0.0 if nb else 0.92)
    x = 0.035 + x * 0.95
    x = x * np.array([1.03, 1.0, 0.985], np.float32)          # BGR : léger froid
    hl = np.clip(x - 0.55, 0, 1)
    x = x + gblur(hl, 16) * glow * 1.6 + gblur(hl, 5) * glow * 0.5   # SoftGlow (seuil 0,55)
    if nb: x = x * 0.62
    if VIG is None: VIG = vignette(np.ones((H, W, 3), np.float32), strength=0.35, power=2.2)
    return grain(x * VIG, 0.012, 1.4)

# ---------------- plans ----------------
def S(i, a, b, src, t_in, sp, fx, hint, z0, z1, bounds, txt=False, note=""):
    return dict(id=i, a=a, b=b, src=src, t_in=t_in, sp=sp, fx=fx, hint=hint, z0=z0, z1=z1, bounds=bounds, txt=txt, note=note)
SHOTS = [
    S("A", 0.0, DROP, "SOT", V0, 100, "phrase", (1000, 270), 1.00, 1.05, B_SOT, True, "Aubry au pupitre face à von der Leyen, synchro, poussée lente (un seul plan comme le test 4)"),
    S("B1", C[0], C[1], "SOT", 99.40, 100, "nb", (1000, 270), 1.03, 1.07, B_SOT, note="boom : N&B, voix ferme, bouche ouverte"),
    S("B2", C[1], C[3], "PLE", 124.75, 50, "ralenti", (1080, 320), 1.00, 1.06, B_PLE, note="plénière 2025 (veste blanche) : regard levé, elle attaque"),
    S("B3", C[3], C[4], "SOT", 102.25, 100, "zoom", (1000, 270), 1.03, 1.07, B_SOT, note="bouche ouverte, regard vers la présidente"),
    S("B4", C[4], C[5], "PLE", 194.60, 100, "zoom", (1080, 320), 1.03, 1.07, B_PLE, note="regard franc, conclusion"),
    S("B5", C[5], C[6], "SOT", 125.85, 100, "zoom", (1000, 270), 1.03, 1.07, B_SOT, note="face caméra, elle parle"),
    S("B6", C[6], C[8], "PLE", 127.90, 50, "fin", (1080, 320), 1.00, 1.08, B_PLE, note="doigt pointé, ralenti, fondu au noir"),
]
FADE_ID, FADE_S = "B6", 0.45
for sh in SHOTS:
    sh["rec"] = f30(sh["a"]); sh["dur"] = f30(sh["b"]) - sh["rec"]
    fps = SFPS[sh["src"]]; sh["fps"] = fps
    sh["n"] = int(round(sh["dur"] / TFPS * fps))
    sh["clip"] = "G2_%s.mov" % sh["id"]

def hair_extent(src, t, n, fps):
    """Largeur réelle de la tête (cheveux bouclés compris) : pixels qui ne sont pas le mur bleu nuit, rangée par rangée (basse déf 480 px)."""
    sc = 4; w, h = 1920 // sc, 1080 // sc
    b = subprocess.run([FF, "-v", "error", "-ss", "%.4f" % t, "-i", L2 + "/sources/" + SRC[src], "-frames:v", str(n), "-vf", "scale=%d:%d" % (w, h),
                        "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    fr = np.frombuffer(b, np.uint8).reshape(-1, h, w, 3).astype(np.int16)
    R, G, B_ = fr[..., 0], fr[..., 1], fr[..., 2]
    wall = (B_ - R > 22) & (B_ > 28) & (R < 60)
    return ~wall, sc
def hair_fit(sh, s, n, fps, views, vh_max):
    """Recentre en x sur la tête entière (cheveux) et élargit la vue si besoin ; hauteur jamais croissante (pas de dézoom)."""
    person, sc = hair_extent(sh["src"], s / fps, n, fps); bd = sh["bounds"]
    need, cxs = [], []
    for k in range(n):
        cx, cy, v = views[min(k, len(views) - 1)]; pm = person[min(k, len(person) - 1)]
        y0 = cy - v / 2; r0 = int(max(y0 + 0.04 * v, 0) / sc); r1 = int((y0 + 0.47 * v) / sc)   # cheveux + visage, au-dessus des micros
        cols = pm[r0:r1, int(bd[0] / sc):int(bd[2] / sc)].mean(0) > 0.04
        idx = np.nonzero(cols)[0]
        if len(idx): x0, x1 = (idx[0] * sc + bd[0], (idx[-1] + 1) * sc + bd[0])
        else: x0, x1 = cx - 100, cx + 100
        cxs.append((x0 + x1) / 2); need.append(max(v, (x1 - x0) * 1.12 * 16 / 9))
    cxs = np.convolve(np.pad(cxs, 4, mode="edge"), np.ones(9) / 9, mode="valid")
    heads = framing.pick(framing.detect(SRC[sh["src"]], s, n + 2, fps), sh["hint"], bd)     # priorité au visage si tout ne tient pas
    for k in range(n - 2, -1, -1): need[k] = max(need[k], need[k + 1])
    out, bad = [], 0
    for k in range(n):
        cx, cy, v = views[min(k, len(views) - 1)]
        v = min(need[k], vh_max); vw = v * 9 / 16
        cx = cxs[k]
        if heads:
            hx0, _, hx1, _ = framing.head_box(heads[min(k, len(heads) - 1)]); m = 0.06 * vw
            lo, hi = hx1 + m - vw / 2, hx0 - m + vw / 2
            if lo <= hi: cx = min(max(cx, lo), hi)
        cx = min(max(cx, bd[0] + vw / 2), bd[2] - vw / 2); cy = min(max(cy, bd[1] + v / 2), bd[3] - v / 2)
        out.append((cx, cy, v))
        pm = person[min(k, len(person) - 1)]; y0 = cy - v / 2
        r0 = int(max(y0 + 0.04 * v, 0) / sc); r1 = int((y0 + 0.47 * v) / sc)
        c0, c1 = int((cx - vw / 2) / sc), int((cx + vw / 2) / sc)
        edge = pm[r0:r1, max(c0, 0):max(c0, 0) + 2].mean() > 0.10 or pm[r0:r1, c1 - 2:c1].mean() > 0.10
        bad += bool(edge)
    return out, bad
def read_frames(src, t, n):
    p = subprocess.Popen([FF, "-v", "error", "-ss", "%.4f" % t, "-i", L2 + "/sources/" + SRC[src], "-frames:v", str(n),
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
def render(sh):
    n, fps = sh["n"], sh["fps"]; w = writer(OUT + sh["clip"], fps)
    s = int(round(sh["t_in"] * fps)); z0, z1 = sh["z0"], sh["z1"]; bd = sh["bounds"]
    zoom = lambda f: z0 + (z1 - z0) * (1 - (1 - f / max(n - 1, 1)) ** 2)    # poussée avant lente, jamais de dézoom
    vh = min(1080, bd[3] - bd[1], (bd[2] - bd[0]) * 16 / 9)
    views, ok = plan_views(SRC[sh["src"]], s, n, fps, speed=1.0, hint=sh["hint"], bounds=bd, vh=vh, zoom=zoom, top=0.15)
    views, nbad = hair_fit(sh, s, n, fps, views, vh)
    info = ("visage" if ok else "SANS VISAGE") + " cheveux hors cadre:%d img" % nbad
    k = 0; vmin = 9e9
    for fr in read_frames(sh["src"], s / fps, n):
        cx, cy, v = views[min(k, len(views) - 1)]; vw = v * 9 / 16; vmin = min(vmin, v)
        assert bd[0] - 1 <= cx - vw / 2 and cx + vw / 2 <= bd[2] + 1 and bd[1] - 1 <= cy - v / 2 and cy + v / 2 <= bd[3] + 1, (sh["id"], k, cx, cy, v)
        img = crop_view(fr.astype(np.float32) / 255, cx, cy, vw, W, H)
        img = grade(img, glow=0.5 if sh["txt"] else 0.7, nb=sh["fx"] == "nb")
        if sh["txt"]: img = draw_text(img, sh["a"] + k / fps)
        w.stdin.write((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8).tobytes()); k += 1
    info += " vue min %d px (agrandi x%.2f)" % (vmin, 1920 / vmin)
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
def build_audio():
    n = int(round(END * SR)); mix = np.zeros((n, 2), np.float32)
    v = fade(load(L2 + "/sources/" + SRC["SOT"], V0, VOUT - V0), 0.03, 0.05)
    mus = load(MUSIC, C_OFF, END + 0.05)[:n]
    lv, _ = lufs(v); lm, _ = lufs(mus[int(DROP * SR):])
    v *= db(-15 - lv); mus *= db(-14 - lm)                      # voix -15 LUFS ; musique après le boom -14 LUFS
    t = np.arange(len(mus)) / SR
    env = np.where(t < DROP - 0.03, db(-9), 1.0).astype(np.float32)   # intro de Sienna sous la voix (voix chantée en anglais : -9 dB)
    env *= np.clip(t / 0.25, 0, 1)
    env *= np.where(t > END - 0.6, np.clip((END - t) / 0.6, 0, 1) ** 1.5, 1)
    mix[:len(mus)] += mus * env[:, None]; mix[:len(v)] += v
    tmp = OUT + "_tmp_mix.wav"; sf_write(tmp, mix); g = 0.0; li2 = None
    for _ in range(3):
        li = lufs(mix)[0] if li2 is None else li2
        g += -14.0 - li
        subprocess.run([FF, "-v", "error", "-y", "-i", tmp, "-af", "volume=%.2fdB,alimiter=limit=0.80:attack=3:release=60:level=false,aresample=192000,alimiter=limit=0.82:attack=1:release=40:level=false,aresample=48000" % g,
                        "-c:a", "pcm_s24le", OUT + "G2-mix.wav"], check=True)
        li2, tp2 = lufs(load(OUT + "G2-mix.wav"))
        if abs(li2 + 14) < 0.3 and tp2 < -1.0: break
    os.remove(tmp)
    sf_write(OUT + "G2-voix.wav", v); sf_write(OUT + "G2-musique.wav", mus)
    return "mix %.1f LUFS, true peak %.1f dBTP (voix %.1f, musique %.1f d'origine)" % (li2, tp2, lv, lm)

# ---------------- plan-G2.json ----------------
def write_plan():
    vid = []
    for sh in SHOTS:
        sp = sh["sp"]; used = sh["n"] * sp / 100 / sh["fps"]
        it = {"id": sh["id"], "clip": sh["clip"], "folder": "genG2", "path": OUT + sh["clip"], "s": 0, "e": sh["n"], "clip_fps": sh["fps"],
              "rec": sh["rec"], "dur": sh["dur"], "track": 1, "note": sh["note"],
              "source": {"fichier": "lot2/sources/" + SRC[sh["src"]], "in_s": round(sh["t_in"], 3), "out_s": round(sh["t_in"] + used, 3)},
              "effets": "recadrage 9:16 suivi visage (bornes %s, pupitre et logo exclus), poussée %.2f->%.2f, glow doux%s%s" % (
                  list(sh["bounds"]), sh["z0"], sh["z1"], ", N&B" if sh["fx"] == "nb" else "", ", cartons cuits" if sh["txt"] else "")}
        if sp != 100: it["speed_pct"] = sp; it["retime"] = "optical_flow"
        if sh["id"] == FADE_ID: it["fade_out_s"] = FADE_S
        vid.append(it)
    plan = {"name": "G2 - Glow - Manon Aubry", "fps": 30, "w": 1080, "h": 1920, "duree_s": round(END, 3),
            "note": "Plans ProRes 9:16 prêts (recadrés au-dessus du pupitre, étalonnés, cartons cuits sur A1/A2). Ralentis à faire dans Resolve : speed_pct + Optical Flow ; e-s = images source à vitesse normale. Générateur : lot2/_claude/gen/G2/genG2.py",
            "phrase": {"texte": DR["texte"], "fichier": "lot2/sources/" + SRC["SOT"], "in_s": V0, "out_s": VOUT,
                       "url": "https://www.youtube.com/watch?v=nwc4Hd8pO8o"},
            "texte_style": {"police": "Avenir Next Bold Italic", "couleur": "#FFFFFF (tout le texte)", "halo": GLOW_HEX, "halo_source": "mur bleu nuit de l'hémicycle (moyenne RGB %s, éclairci)" % [round(c * 255) for c in WALL],
                            "contour": "bleu-noir 2 px", "position": "calé à gauche x=%.3f, ligne de base y=%.3f" % (XL, YB)},
            "musique": {"fichier": "lot2/sons/G2-the-marias-sienna_complet.wav", "debut_dans_complet_s": round(C_OFF, 3),
                        "drop_timeline_s": round(DROP, 3), "temps_s": P, "coupes_timeline_s": [round(c, 3) for c in C]},
            "textes": [{"t0": round(c["t0"], 2), "t1": round(c["t1"], 2), "texte": " / ".join(" ".join(w[0] for w in li) for li in c["lines"])} for c in CARDS],
            "video": vid,
            "audio": [{"id": "mix", "clip": "G2-mix.wav", "folder": "genG2", "path": OUT + "G2-mix.wav", "rec": 0, "track": 1,
                       "note": "mix -14 LUFS : voix SOT %.2f-%.2f s + Sienna complet %.2f-%.2f s, intro -9 dB sous la voix, boom à %.2f s, fondu de fin 0,6 s" % (V0, VOUT, C_OFF, C_OFF + END, DROP)}]}
    json.dump(plan, open(D + "plan-G2.json", "w"), indent=1, ensure_ascii=False)

# ---------------- aperçu ffmpeg 540×960 ----------------
def preview():
    out = L2 + "/exports/apercu-G2.mp4"; args = [FF, "-v", "error", "-y"]; fl = []
    for i, sh in enumerate(SHOTS):
        args += ["-i", OUT + sh["clip"]]
        fl.append("[%d:v]setpts=(PTS-STARTPTS)/%.4f,fps=30,trim=end_frame=%d,setpts=PTS-STARTPTS,scale=540:960,setsar=1%s[v%d]" % (
            i, sh["sp"] / 100, sh["dur"], ",fade=t=out:st=%.3f:d=%.2f" % (sh["dur"] / 30 - FADE_S, FADE_S) if sh["id"] == FADE_ID else "", i))
    args += ["-i", OUT + "G2-mix.wav"]
    fl.append("".join("[v%d]" % i for i in range(len(SHOTS))) + "concat=n=%d:v=1:a=0[v]" % len(SHOTS))
    args += ["-filter_complex", ";".join(fl), "-map", "[v]", "-map", "%d:a" % len(SHOTS), "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p",
             "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out]
    subprocess.run(args, check=True)
    return out

if __name__ == "__main__":
    only = None
    for a in sys.argv:
        if a.startswith("only="): only = a[5:].split(",")
    print("halo", GLOW_HEX, "mur", [round(c * 255) for c in WALL])
    print("cartons", [(" ".join(w[0] for w in c["words"]), round(c["t0"], 2), round(c["t1"], 2), int(card_em(c))) for c in CARDS])
    if "plans" in sys.argv:
        for sh in SHOTS:
            if only and sh["id"] not in only: continue
            print(sh["id"], "%.2f-%.2f" % (sh["a"], sh["b"]), sh["dur"], "img tl", sh["n"], "img src", render(sh), flush=True)
    if "audio" in sys.argv: print(build_audio())
    write_plan()
    if "apercu" in sys.argv: print(preview())
    print("total %.2f s ; %d plans ; drop %.2f ; coupes %s" % (END, len(SHOTS), DROP, [round(c, 2) for c in C]))
