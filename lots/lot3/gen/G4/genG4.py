# G4 — Glow COULEUR, Danièle Obono (lot 3), son « Dark Beach » (Pastel Ghost). Modèle : lot2/_claude/gen/G3/genG3.py (mais
# aucune image N&B : règle lot 3). Aperçu hors Resolve : plans ProRes 9:16 recadrés (visage suivi), étalonnage glow couleur
# (bloom teinté violet), texte cuit (Avenir Next Bold Italic, TOUT en blanc, halo violet pris dans la colonne lumineuse du
# plateau LCI + contour sombre, jamais de rouge).
# Phrase : LCI 24/09/2026 (YouTube wn6qL6YseFY, chaîne officielle de D. Obono) 1540,08-1544,74 s.
# Ralentis PAS précalculés : clip à vitesse normale, speed_pct + retime optical flow dans plan-G4.json.
# Son : extrait 68,94-83,84 s du morceau ; drop (74,19 s) sur le 1er plan après la phrase (règle lot 3 : pas l'intro).
# Usage : python genG4.py [plans] [audio] [apercu] [only=ID,ID]
import sys, os, json, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont
HK = "/Users/luca.grousset/Movies/highkey-gauchiste"; L3 = HK + "/lot3"
sys.path.insert(0, HK + "/_claude/outils")
import framing
from framing import plan_views
from fx import crop_view, vignette, grain, gblur
from words import tokens, clean
FF = "/opt/homebrew/bin/ffmpeg"
D = L3 + "/_claude/gen/G4/"; OUT = D + "out/"; os.makedirs(OUT, exist_ok=True)
framing.ROOT = L3; framing.CACHE = D + "cache"
W, H, TFPS, SFPS = 1080, 1920, 30, 30          # toutes les sources sont en 1920×1080 30 i/s
# ---------------- sources (lot3/sources) ----------------
LA = "G4-obono-lci-2026-09-24-a.mp4"           # wn6qL6YseFY 1400-1560 s (LCI 24/09/2026)
LB = "G4-obono-lci-2026-09-24-b.mp4"           # wn6qL6YseFY 870-1030 s
BF = "G4-obono-bfmtv-2026-09-04.mp4"           # XDCpNQsFZWc 1500-1680 s (BFMTV 04/09/2026)
LA0, LB0, BF0 = 1400.0, 870.0, 1500.0          # début de l'extrait dans la vidéo YouTube
YT = {LA: ("wn6qL6YseFY", LA0), LB: ("wn6qL6YseFY", LB0), BF: ("XDCpNQsFZWc", BF0)}
B_LCI = (0, 0, 1560, 760)        # LCI : logo + heure en haut à droite (x>1580), bandeau nom (y≈770) et bandeaux en bas exclus
B_BFM = (300, 0, 1920, 815)      # BFMTV : logo en haut à gauche (x<280), bandeau rouge (y≈830) exclu
B_EXT = (0, 0, 1560, 860)        # A1/A2 : source prolongée par reflet (voir plus bas)
B_CU = (0, 0, 1560, 815)         # LCI gros plans SANS bandeau nom : seul le bandeau du bas (y≈820) et le logo sont exclus
# ---------------- halo : couleur prise dans la vidéo ----------------
GLOW = (159, 128, 255)           # #9F80FF : colonne violette du plateau LCI (mesurée #957BFC à 145 s), saturation 0,5, éclaircie
WHITE = (255, 255, 255)
GTINT = np.array([255, 205, 235][::-1], np.float32) / 255     # bloom légèrement rosé-violet (BGR)

# ---------------- temps ----------------
FR = json.load(open(D + "rythme/frappes.json")); MOFF = FR["MOFF"]   # temps morceau = timeline + MOFF
K = FR["kicks_timeline"]                       # kicks réels (attaques 30-120 Hz), 130 BPM, timeline
DROP = 5.250                                   # LE drop de Dark Beach (74,188 s du morceau, le passage le plus revu sur YouTube 73,6-75,8 s) = kick
assert min(abs(k - DROP) for k in K) < 0.002
END = 14.90                                    # glow 15 s max
V = LA0 + 139.88                               # timeline = temps YouTube - V  (phrase 1540,08 -> 0,20 s)
VOICE = (1540.06, 1544.86)                     # voix posée (YouTube), « Ce que … pauvres. » mots 1540,08-1544,74
def f30(t): return int(round(t * TFPS))
KA = [k for k in K if k >= DROP - 1e-3]        # kicks à partir du palier

# ---------------- textes (mot à mot, phrase réelle) ----------------
# Le transcript d'origine (tx/wn6qL6YseFY.json) n'est plus dans le dossier : temps d'apparition des mots (timeline) relevés
# image par image sur l'ancien rendu G4_A1/A2 (même image d'apparition pour chaque mot) ; fin du dernier mot 1544,74 s.
WORDS = [("Ce", 0.2), ("que", 0.3), ("les", 0.4), ("gens", 0.533), ("ne", 0.62), ("supportent", 0.767), ("pas,", 1.2), ("c'est", 1.52),
         ("de", 1.8), ("voir", 1.9), ("autant", 2.12), ("de", 2.567), ("richesses", 2.733), ("dans", 3.18), ("un", 3.544), ("pays", 3.744),
         ("où", 3.92), ("il", 4.077), ("y", 4.211), ("a", 4.211), ("10", 4.26), ("millions", 4.411), ("de", 4.58), ("pauvres.", 4.711)]
T = [{"w": w, "start": V + t} for w, t in WORDS]; T[-1]["end"] = 1544.74
assert " ".join(t["w"] for t in T) == "Ce que les gens ne supportent pas, c'est de voir autant de richesses dans un pays où il y a 10 millions de pauvres.", " ".join(t["w"] for t in T)
def up(t): return clean(t["w"]).upper()
# Ce que les gens | ne supportent pas | c'est de voir | autant de richesses | dans un pays | où il y a | 10 millions | de pauvres
GROUPS = [4, 3, 3, 3, 3, 4, 2, 2]
assert sum(GROUPS) == len(T)
CARDS, i = [], 0
for g in GROUPS:
    CARDS.append({"words": [(up(T[j]), T[j]["start"] - V) for j in range(i, i + g)]}); i += g
for k, c in enumerate(CARDS): c["t1"] = CARDS[k + 1]["words"][0][1] if k + 1 < len(CARDS) else DROP
TEXT_Y = 0.60                                  # centre vertical du bloc (test 4 : 60 % depuis le haut)
WFRAC, EM_MAX, EM_MIN, LH = 0.60, 110, 100, 1.15  # zone sûre TikTok : bloc ≤ 60 % de large (x 0,20-0,80) ; 1 à 3 lignes, lettres ≥ 70 px
FONT = ("/System/Library/Fonts/Avenir Next.ttc", 1)          # Avenir Next Bold Italic (test 4)
_fc = {}
def font(px):
    px = int(round(px))
    if px not in _fc: _fc[px] = ImageFont.truetype(FONT[0], px, index=FONT[1])
    return _fc[px]
def card_layout(c):
    """Moins de lignes possible (équilibrées) avec un corps ≥ EM_MIN dans WFRAC de la largeur ; sinon le plus gros corps."""
    import itertools
    if "lay" in c: return c["lay"]
    ws = [w[0] for w in c["words"]]; f = font(100); sp = f.getlength(" ") / 100
    wl = lambda l: sum(f.getlength(w) / 100 for w in l) + sp * (len(l) - 1)
    best = None
    for n in range(1, min(3, len(ws)) + 1):
        for cut in itertools.combinations(range(1, len(ws)), n - 1):
            b = (0,) + cut + (len(ws),); ls = [list(range(b[k], b[k + 1])) for k in range(n)]
            mw = max(wl([ws[i] for i in l]) for l in ls); em = min(EM_MAX, WFRAC * W / mw)
            if best is None or (round(em, 1), -mw) > (round(best[0], 1), -best[2]): best = (em, ls, mw)   # égalité : lignes les plus équilibrées
        if best[0] >= EM_MIN: break
    c["lay"] = best[:2]; return c["lay"]
def draw_text(img, t):
    act = [c for c in CARDS if c["words"][0][1] - 1e-3 <= t < c["t1"]]
    if not act: return img
    lay = Image.new("L", (W, H), 0); dl = ImageDraw.Draw(lay)
    for c in act:
        px, ls = card_layout(c); f = font(px); sp = f.getlength(" "); lh = px * LH
        for li, l in enumerate(ls):
            tot = sum(f.getlength(c["words"][i][0]) for i in l) + sp * (len(l) - 1)
            x = W / 2 - tot / 2; y = TEXT_Y * H + (li - (len(ls) - 1) / 2) * lh
            for i in l:
                word, tw = c["words"][i]
                if tw <= t + 1e-3: dl.text((x, y), word, font=f, anchor="lm", fill=255)   # apparition sèche au mot
                x += f.getlength(word) + sp
    a = np.asarray(lay, np.float32) / 255
    g1 = np.clip(gblur(a, 24 / 2.5) * 2.2, 0, 1); g2 = np.clip(gblur(a, 8 / 2.5) * 1.6, 0, 1)
    col = np.array(GLOW[::-1], np.float32) / 255
    out = img
    for g in (g1, g2): out = out * (1 - g[..., None]) + col * g[..., None]
    sh = gblur(a, 2.2)
    for _ in range(3): out = out * (1 - sh[..., None])
    return out * (1 - a[..., None]) + np.array(WHITE, np.float32) / 255 * a[..., None]

# ---------------- étalonnage « glow » couleur (jamais de N&B) ----------------
VIG = None
def grade(img):
    global VIG
    x = np.clip((img - 0.02) * 1.06, 0, 1); x = x * x * (3 - 2 * x) * 0.30 + x * 0.70      # contraste doux
    lum = x @ np.array([0.114, 0.587, 0.299], np.float32)
    x = lum[..., None] + (x - lum[..., None]) * 1.08                                      # couleurs un peu plus riches
    hi = np.clip((x - 0.55) / 0.45, 0, 1)
    x = x + gblur(hi, 18) * 0.50 * GTINT                                                  # bloom teinté (SoftGlow)
    if VIG is None: VIG = vignette(np.ones((H, W, 3), np.float32), strength=0.40, power=2.2)
    return grain(np.clip(x, 0, 1) * VIG, 0.012, 1.4)

# ---------------- liste des plans ----------------
# A1 : phrase sur le gros plan d'Obono (même caméra) pris 5,10 s plus loin, où elle dit « C'est ça que les gens ne supportent
#      pas » : mêmes mots que « Ce que les gens ne supportent pas » -> lèvres raccord ; la régie LCI montre la présentatrice
#      pendant 1540,33-1542,33. A2 : retour en synchro exacte dès que le gros plan revient, coupe sur un kick.
# B : rafale sur les kicks réels, 2 temps (0,92 s) par plan, poussée lente avant qui s'arrête sur le kick suivant.
def S(i, a, b, src, t_in, sp, hint, bnd, vh, z0, z1, fx="", note=""):
    return dict(id=i, a=a, b=b, src=src, t_in=t_in, sp=sp, hint=hint, bnd=bnd, vh=vh, z0=z0, z1=z1, fx=fx, note=note)
A_CUT = K[6]                                   # 2,949 s : kick, gros plan LCI de retour depuis 1542,333
A1_OFF = 5.10
SHOTS = [
    S("A1", 0.0, A_CUT, LA, V - LA0 + A1_OFF, 100, (700, 380), B_CU, 815, 1.00, 1.00, "texte",
      "phrase : gros plan LCI pris +5,10 s (« C'est ça que les gens ne supportent pas », lèvres raccord), cadre fixe (visage trop grand pour pousser)"),
    S("A2", A_CUT, DROP, LA, V - LA0 + A_CUT, 100, (700, 380), B_CU, 815, 1.00, 1.00, "texte",
      "suite de la phrase en synchro exacte, flash doux sur la coupe (même caméra que A1)"),
    S("B1", KA[0], KA[2], BF, 43.20, 100, (900, 330), B_BFM, 815, 1.00, 1.03, "flash", "drop : flash, BFMTV veste jaune, main levée"),
    S("B2", KA[2], KA[4], LA, 53.00, 100, (600, 330), B_CU, 815, 1.00, 1.02, "", "gros plan LCI, regard intense (sans bandeau nom)"),
    S("B3", KA[4], KA[6], LA, 76.00, 50, (600, 330), B_CU, 815, 1.00, 1.02, "", "gros plan LCI (ralenti) ; plan moyen écarté : nom de l'émission sur le décor"),
    S("B4", KA[6], KA[8], LB, 68.50, 100, (540, 330), B_CU, 815, 1.00, 1.02, "", "gros plan LCI, elle répond"),
    S("B5", KA[8], KA[10], BF, 154.50, 100, (900, 330), B_BFM, 815, 1.00, 1.03, "", "BFMTV gros plan, regard de côté"),
    S("B6", KA[10], KA[12], LA, 49.00, 100, (600, 330), B_CU, 815, 1.00, 1.02, "", "gros plan LCI, elle parle"),
    S("B7", KA[12], KA[14], BF, 155.60, 50, (900, 330), B_BFM, 815, 1.00, 1.03, "", "BFMTV gros plan (ralenti)"),
    S("B8", KA[14], KA[16], BF, 158.70, 100, (900, 330), B_BFM, 815, 1.00, 1.03, "", "BFMTV gros plan"),
    S("B9", KA[16], KA[18], LA, 70.00, 100, (600, 330), B_CU, 815, 1.00, 1.02, "", "gros plan LCI, main levée"),
    S("B10", KA[18], END, BF, 41.40, 50, (900, 330), B_BFM, 815, 1.00, 1.04, "fin", "BFMTV gros plan (ralenti), fondu au noir 0,6 s"),
]
for sh in SHOTS:
    sh["rec"] = f30(sh["a"]); sh["dur"] = f30(sh["b"]) - sh["rec"]
    sh["clip"] = "G4_%s.mov" % sh["id"]
    if sh["id"] in ("A1", "A2"):
        # gros plan LCI : le visage (boîte Vision) fait 76 % de la largeur d'un cadre 9:16 de 815 px de haut -> tête au ras des bords.
        # On prolonge la source de 45 px sous la limite du bandeau (lignes 815-859 = reflet flouté des lignes 770-814, veste
        # imprimée, sous le vignettage) pour un cadre de 860 px : marge ≈ 5 % de chaque côté. Aucun texte du bandeau à l'image.
        sh["bnd"] = B_EXT; sh["vh"] = 860; sh["ext"] = True
    sh["speed_res"] = 100.0 if sh["sp"] == 100 else sh["sp"] * SFPS / TFPS
def ease_out(u): u = min(max(u, 0.0), 1.0); return 1 - (1 - u) ** 3
def zoom_at(sh, t):
    u = (t - sh["a"]) / (sh["b"] - sh["a"])
    u = min(max(u, 0), 1) if sh["fx"] == "texte" else ease_out(u)
    return sh["z0"] + (sh["z1"] - sh["z0"]) * u

# ---------------- rendu d'un plan ----------------
def read_frames(src, t, n):
    p = subprocess.Popen([FF, "-v", "error", "-ss", "%.4f" % t, "-i", L3 + "/sources/" + src, "-frames:v", str(n),
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
    n = sh["dur"]; s0 = int(round(sh["t_in"] * SFPS)); slow = sh["sp"] != 100
    # clip livré à vitesse normale (image k = source s0+k) ; ralenti : Resolve lit ce clip à sp % -> image k au temps a + k/(30·sp)
    tl_t = (lambda k: sh["a"] + k / (SFPS * sh["sp"] / 100)) if slow else (lambda k: sh["a"] + k / TFPS)
    views, ok = plan_views(sh["src"], s0, n, SFPS, speed=1.0, hint=sh["hint"], bounds=sh["bnd"], vh=sh["vh"],
                           zoom=lambda k: zoom_at(sh, tl_t(k)), top=0.16,
                           shake=(lambda k: (sh["dx"], 0.0)) if sh.get("dx") else None)
    frames = list(read_frames(sh["src"], s0 / SFPS, n))
    w = writer(OUT + sh["clip"], TFPS)
    for k in range(n):
        fr = frames[min(k, len(frames) - 1)]
        if sh.get("ext"):
            fr = fr.copy(); refl = fr[814:769:-1].astype(np.float32) / 255
            fr[815:860] = (gblur(refl, 2.0) * 255 + 0.5).astype(np.uint8)
        cx, cy, vh = views[k]; vw = vh * 9 / 16
        img = grade(crop_view(fr.astype(np.float32) / 255, cx, cy, vw, W, H))
        t = tl_t(k)
        if sh["fx"] == "texte": img = draw_text(img, t)
        if sh["id"] == "A2":                                                        # flash doux sur la coupe A1 -> A2 (même caméra)
            fl = max(0.0, 0.35 * (1 - (t - sh["a"]) / 0.10)); img = img + (1 - img) * fl
        if sh["fx"] == "flash":                                                    # flash sur le palier (4 images timeline)
            fl = max(0.0, 0.75 * (1 - (t - sh["a"]) / 0.13))
            img = img + (1 - img) * fl * np.array([1.0, 0.92, 0.97], np.float32)
        if sh["fx"] == "fin": img = img * min(max((END - t) / 0.6, 0.0), 1.0)
        w.stdin.write((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8).tobytes())
    w.stdin.close(); w.wait()
    return ("visage" if ok else "SANS VISAGE") + ("" if len(frames) >= n else " court:%d/%d" % (len(frames), n))

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
SON = L3 + "/sons/G4-pastel-ghost-dark-beach_complet.wav"
def build_audio():
    from scipy.signal import butter, sosfilt
    n = int(END * SR); mix = np.zeros((n, 2), np.float32)
    v = fade(load(L3 + "/sources/" + LA, VOICE[0] - LA0, VOICE[1] - VOICE[0]), 0.02, 0.08)
    lv, _ = lufs(v); v *= db(-15 - lv)
    m = load(SON, MOFF, END)
    lm, _ = lufs(m[int(DROP * SR):]); m *= db(-14 - lm)
    t = np.arange(len(m)) / SR
    lo = sosfilt(butter(4, 420, "low", fs=SR, output="sos"), m, axis=0).astype(np.float32)   # ducking : morceau étouffé sous la voix
    a = np.interp(t, [0, DROP - 0.06, DROP], [1, 1, 0])[:, None].astype(np.float32)
    mus = lo * db(-7) * a + m * (1 - a)                                                       # puis la musique reprend en plein au palier
    mus *= (np.clip((END - t) / 1.2, 0, 1) ** 1.5)[:, None].astype(np.float32)
    mus = fade(mus, 0.25, 0)
    mix[:len(mus)] += mus; i0 = int(round((VOICE[0] - V) * SR)); mix[i0:i0 + len(v)] += v[:n - i0]
    tmp = OUT + "_tmp_mix.wav"; sf_write(tmp, mix); g = 0.0; li, _ = lufs(mix)
    for _ in range(3):
        g += -14.0 - li
        subprocess.run([FF, "-v", "error", "-y", "-i", tmp, "-af", "volume=%.2fdB,alimiter=limit=0.80:attack=3:release=60:level=false,aresample=192000,alimiter=limit=0.82:attack=1:release=40:level=false,aresample=48000" % g,
                        "-c:a", "pcm_s24le", OUT + "G4-mix.wav"], check=True)
        li, tp = lufs(load(OUT + "G4-mix.wav"))
        if abs(li + 14) < 0.3 and tp < -1.0: break
    os.remove(tmp)
    return "mix %.1f LUFS, true peak %.1f dBTP" % (li, tp)

# ---------------- son.json + plan-G4.json ----------------
def write_son():
    son = {"titre": "Dark Beach", "artiste": "Pastel Ghost", "url": "https://youtu.be/guDJvZp5Bqk", "chaine": "PASTEL GHOST (officielle)",
           "fichier": "lot3/sons/G4-pastel-ghost-dark-beach_complet.wav",
           "extrait_morceau_s": [round(MOFF, 3), round(MOFF + END, 3)], "bpm": 129.9,
           "drop": {"morceau_s": round(MOFF + DROP, 3), "timeline_s": DROP, "note": "le drop connu (edits TikTok) : pic « les plus revus » YouTube 73,6-75,8 s ; creux d'une mesure 72,38-74,19 puis crash + retour plein"},
           "sous_la_phrase": "montée 68,94-74,19 s du morceau, étouffée (passe-bas 420 Hz, -7 dB) sous la voix",
           "frappes": "kicks réels (attaque 30-120 Hz) sur chaque temps, rythme/frappes.json",
           "kicks_timeline_s": [k for k in K if k <= END]}
    json.dump(son, open(D + "son.json", "w"), indent=1, ensure_ascii=False)
def write_plan():
    vid = []
    for sh in SHOTS:
        sp = sh["sp"]; used = sh["dur"] / TFPS * sp / 100; yid, y0 = YT[sh["src"]]
        it = {"id": sh["id"], "clip": sh["clip"], "folder": "G4", "path": OUT + sh["clip"], "s": 0, "e": sh["dur"], "clip_fps": TFPS,
              "rec": sh["rec"], "dur": sh["dur"], "track": 1, "note": sh["note"],
              "source": {"fichier": "lot3/sources/" + sh["src"], "in_s": round(sh["t_in"], 3), "out_s": round(sh["t_in"] + used, 3),
                         "youtube": "%s %.2f-%.2f s" % (yid, y0 + sh["t_in"], y0 + sh["t_in"] + used)},
              "effets": "recadrage 9:16 suivi visage (sans logo ni bandeau), glow couleur violet%s" % (
                  {"flash": ", flash 0,13 s cuit", "texte": ", texte cuit", "fin": ", fondu au noir 0,6 s cuit"}.get(sh["fx"], ""))}
        it["frappe_s"] = round(sh["a"], 3); it["poussee"] = "x%.2f -> x%.2f, du kick %.3f s au kick %.3f s (temps timeline)" % (sh["z0"], sh["z1"], sh["a"], sh["b"])
        if sp != 100:
            it["speed_pct"] = round(sh["speed_res"], 4); it["retime"] = "optical_flow"
            it["ralenti"] = "%d %% : clip 30 i/s à vitesse normale, Resolve à %g %% (Optical Flow, Speed Warp better)" % (sp, sh["speed_res"])
        vid.append(it)
    plan = {"name": "G4 - Glow - Obono", "fps": 30, "w": 1080, "h": 1920, "duree_s": END,
            "note": "Lot 3, glow COULEUR (aucune image N&B). Coupes sur les kicks réels (rythme/frappes.json). Plans ProRes 9:16 30 i/s prêts (recadrés, poussées, étalonnés, texte cuit sur A1/A2, flash cuit sur B1, fondu cuit sur B10). Ralentis : speed_pct + Optical Flow. Générateur : lot3/_claude/gen/G4/genG4.py, halo #%02X%02X%02X" % GLOW,
            "musique": {"fichier": "lot3/sons/G4-pastel-ghost-dark-beach_complet.wav", "debut_extrait_s": round(MOFF, 3), "entree_pleine_timeline_s": DROP, "bpm_reel": 129.9,
                        "kicks_timeline_s": [k for k in K if k <= END],
                        "sous_la_voix": "ducking : morceau passe-bas 420 Hz -7 dB de 0 à %.2f s, plein ensuite" % DROP},
            "phrase": {"source": "https://youtu.be/wn6qL6YseFY 1540,08-1544,74 s (LCI 24/09/2026, chaîne de Danièle Obono)",
                       "texte": " ".join(t["w"] for t in T), "timeline_s": [round(T[0]["start"] - V, 3), round(T[-1]["end"] - V, 3)]},
            "textes": [{"t0": round(c["words"][0][1], 2), "t1": round(c["t1"], 2), "ligne": " ".join(w[0] for w in c["words"])} for c in CARDS],
            "halo": "#%02X%02X%02X (colonne violette du plateau LCI)" % GLOW,
            "video": vid,
            "audio": [{"id": "mix", "clip": "G4-mix.wav", "folder": "G4", "path": OUT + "G4-mix.wav", "rec": 0, "track": 1,
                       "note": "mix final -14 LUFS : voix %.2f-%.2f s, Dark Beach étouffé dessous puis plein au palier %.2f s, fondu de fin" % (VOICE[0] - V, VOICE[1] - V, DROP)}]}
    json.dump(plan, open(D + "plan-G4.json", "w"), indent=1, ensure_ascii=False)

# ---------------- aperçu ffmpeg 540×960 ----------------
def preview():
    out = HK + "/preview/apercu-G4.mp4"; args = [FF, "-v", "error", "-y"]; fl = []
    for i, sh in enumerate(SHOTS):
        args += ["-i", OUT + sh["clip"]]; sp = sh["speed_res"] / 100
        fl.append("[%d:v]setpts=(PTS-STARTPTS)/%.6f,fps=30,trim=end_frame=%d,setpts=PTS-STARTPTS,scale=540:960,setsar=1[v%d]" % (i, sp, sh["dur"], i))
    args += ["-i", OUT + "G4-mix.wav"]
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
            print(sh["id"], "%.3f-%.3f" % (sh["a"], sh["b"]), "rec", sh["rec"], "dur", sh["dur"], render(sh), flush=True)
    if "audio" in sys.argv: print(build_audio())
    write_son(); write_plan()
    if "apercu" in sys.argv: print(preview())
    print("total", sum(s["dur"] for s in SHOTS) / 30, "s ;", len(SHOTS), "plans ; plus court", min(s["dur"] for s in SHOTS) / 30, "s")
    print([" ".join(w[0] for w in c["words"]) for c in CARDS])
