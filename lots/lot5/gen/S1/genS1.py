# Lot 5 — S1 Arc solidarité (NOUVEAU, inspi hazemziadi17) : Lula 2022 -> carton BRAVO, LULA! -> Mélenchon « Guess who's next?! ».
# Son : Queen - We Are The Champions (Queen Official). Build « …and I need to go on and on… » sous la phrase de Lula, drop = « We are the champions ».
# Phrase réelle : Lula, discours de la victoire, São Paulo 30/10/2022 (TV Câmara) : « Tentaram me enterrar vivo e eu estou aqui. »
# Recette (fiche inspi) : arc 1 victoire Lula (foule, drapeau), charnière carton plein écran rouge #E4002B texte blanc 1 temps, arc 2 Mélenchon
# multi-contextes (Clermont 2026, convention 2025, marche et soir du 1er tour 2022) en coupes sèches plus rapides, sous-titre courant
# « Guess who's next?! » blanc, date posée sans animation sur le dernier plan ; couleur pleine (palette vive, pas de filtre lourd).
# Modèle de code : lot4/_claude/gen/M1/genM1.py. Aperçu HORS Resolve (ffmpeg/numpy).
# Usage : python genS1.py [shots] [plan] [audio] [apercu] [check] [mesure] [probe] [only=ID,ID]   (sans argument = tout sauf probe)
import sys, os, json, subprocess, math, shutil
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
ROOT = "/Users/luca.grousset/Movies/highkey-gauchiste"; LOT = ROOT + "/lot5"
sys.path.insert(0, ROOT + "/_claude/outils")
import framing
from fx import vignette, to8
from framing import plan_views
D = LOT + "/_claude/gen/S1/"; OUT = D + "out/"; os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, D)
from hits import detect_hits
framing.ROOT = D + "src"; framing.CACHE = D + "cache/faces"           # src/sources = liens vers lot2/lot3/lot4/lot5 (lecture seule)
FF = "/opt/homebrew/bin/ffmpeg"; FACES = ROOT + "/_claude/outils/faces"; FPS = 30; W, H = 1080, 1920
SRCDIR = D + "src/sources/"
CAM, FOA, FOB, NJA = "S1-lula-camara-enterrar.mp4", "S1-lula-folha-paulista-a.mp4", "S1-lula-folha-paulista-b.mp4", "S1-lula-ninja-paulista-a.mp4"
CL1, CL3, CL5 = "C3-melenchon-clermont-01.mp4", "C3-melenchon-clermont-03.mp4", "C3-melenchon-clermont-05.mp4"
CO1, CO2, CO3, CO7 = ("C3-melenchon-convention-0%d.mp4" % i for i in (1, 2, 3, 7))
M4018, M4895, FB, ENT = "Z2-marche2022-4018.mp4", "Z2-marche2022-4895.mp4", "Z2-premiertour2022-foule-b.mp4", "A6-melenchon-clermont-entree.mp4"
JLM = "chaîne JEAN-LUC MÉLENCHON"
SRC_INFO = {  # fichier -> (dossier réel, url YouTube, décalage du fichier dans la vidéo YouTube (s), contexte)
    CAM: ("lot5/sources", "https://www.youtube.com/watch?v=Tutjrt27Z6E", 86, "Lula élu, 1er discours, São Paulo, 30/10/2022 (TV Câmara dos Deputados)"),
    FOA: ("lot5/sources", "https://www.youtube.com/watch?v=5J2ar2UK8OM", 3, "Avenida Paulista, nuit de la victoire de Lula, 30/10/2022 (Folha de S.Paulo)"),
    FOB: ("lot5/sources", "https://www.youtube.com/watch?v=5J2ar2UK8OM", 210, "Avenida Paulista, nuit de la victoire de Lula, 30/10/2022 (Folha de S.Paulo)"),
    NJA: ("lot5/sources", "https://www.youtube.com/watch?v=LxNH-ZMXUYY", 0, "Avenida Paulista, nuit de la victoire de Lula, 30/10/2022 (Mídia NINJA)"),
    CL1: ("lot2/sources", "https://www.youtube.com/watch?v=sBvVfHxcJp4", 553.5, "meeting de Clermont-Ferrand, 11/10/2026 (%s)" % JLM),
    CL3: ("lot2/sources", "https://www.youtube.com/watch?v=sBvVfHxcJp4", 2218.5, "meeting de Clermont-Ferrand, 11/10/2026 (%s)" % JLM),
    CL5: ("lot2/sources", "https://www.youtube.com/watch?v=sBvVfHxcJp4", 4303.5, "meeting de Clermont-Ferrand, 11/10/2026 (%s)" % JLM),
    ENT: ("lot3/sources", "https://www.youtube.com/watch?v=sBvVfHxcJp4", 1470, "meeting de Clermont-Ferrand, 11/10/2026 (%s)" % JLM),
    CO1: ("lot2/sources", "https://www.youtube.com/watch?v=Yc46p2zQZxY", 24.5, "convention LFI, 23/11/2025 (%s)" % JLM),
    CO2: ("lot2/sources", "https://www.youtube.com/watch?v=Yc46p2zQZxY", 117.5, "convention LFI, 23/11/2025 (%s)" % JLM),
    CO3: ("lot2/sources", "https://www.youtube.com/watch?v=Yc46p2zQZxY", 489.5, "convention LFI, 23/11/2025 (%s)" % JLM),
    CO7: ("lot2/sources", "https://www.youtube.com/watch?v=Yc46p2zQZxY", 1696.5, "convention LFI, 23/11/2025 (%s)" % JLM),
    M4018: ("lot4/sources", "https://www.youtube.com/watch?v=Zlwij7ZXLts", 4018, "marche pour la 6e République, Paris, 20/3/2022 (%s)" % JLM),
    M4895: ("lot4/sources", "https://www.youtube.com/watch?v=Zlwij7ZXLts", 4895, "marche pour la 6e République, Paris, 20/3/2022 (%s)" % JLM),
    FB: ("lot4/sources", "https://www.youtube.com/watch?v=izCL2pR8UCE", 502, "soir du 1er tour, Paris, 10/4/2022 (%s)" % JLM),
}
_FPS = {}
def sfps(src):
    if src not in _FPS:
        r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate", "-of", "csv=p=0", SRCDIR + src],
                           capture_output=True, text=True).stdout.strip().split("/")
        _FPS[src] = float(r[0]) / float(r[1])
    return _FPS[src]
# ---------------- musique : Queen - We Are The Champions (Queen Official) ----------------
MFILE = LOT + "/sons/S1-queen-champions_complet.wav"; MURL = "https://www.youtube.com/watch?v=04854XqcfCY"
# extrait continu : « …and I need to go on, and on, and on, and on » (build, baissé sous Lula), drop « We are the champions, my friends /
# And we'll keep on fighting till the end », fin sur la frappe après « end ».
S0_BASE = 31.031                     # caisse du complet (début de l'extrait)
CUT_SONG = [31.944, 33.794, 34.740, 35.654, 36.640, 38.526, 39.504, 40.452, 42.314, 43.303, 44.221, 45.197, 46.134, 48.027]
#            foule  fumigènes Lula carton DROP ...
END_SONG = 49.272 + 0.40             # frappe qui clôt « till the end » + petite queue (fondu)
END = round(END_SONG - S0_BASE, 3)
BEAT = 60 / 63.0
def fr(t): return int(round(t * FPS))
def music_raw(s0, sr=48000, dur=END + 0.5):
    import soundfile as sf_
    x, r = sf_.read(MFILE, dtype="float32"); assert r == sr
    i0 = int(round(s0 * sr)); return x[i0:i0 + int(dur * sr)]
def choose_s0():
    js = OUT + "S1-frappes.json"
    if os.path.exists(js):
        d = json.load(open(js))
        if d.get("base") == S0_BASE and d.get("cuts") == CUT_SONG: return d["s0"], d["frappes"]
    hits = detect_hits(music_raw(S0_BASE, dur=END + 0.6))
    hits = [(round(h[0] + S0_BASE, 4), h[1], h[2]) for h in hits]
    real = []
    for c in CUT_SONG:
        h = min(hits, key=lambda h: abs(h[0] - c)); assert abs(h[0] - c) < 0.05, ("pas de frappe près de", c, h); real.append(h[0] if abs(h[0] - c) < 0.03 else c)   # c imposé = frappe détectée sur le mix exporté
    best = None
    for k in range(-16, 17):
        s0 = S0_BASE + k / 1000.0
        err = max(abs((r - s0) - fr(r - s0) / FPS) for r in real)
        if best is None or err < best[0]: best = (err, s0)
    s0 = round(best[1], 4)
    tl = [(round(h[0] - s0, 4), h[1], h[2]) for h in hits if 0 <= h[0] - s0 <= END]
    json.dump({"base": S0_BASE, "cuts": CUT_SONG, "s0": s0, "err_max_s": round(best[0], 4), "frappes": tl, "coupes_complet": real}, open(js, "w"), indent=0)
    return s0, tl
S0, HITS = choose_s0()
_d = json.load(open(OUT + "S1-frappes.json"))
CUTS = [round(r - S0, 4) for r in _d["coupes_complet"]]
CUTF = [fr(c) for c in CUTS]
CARD_I, DROP_I = 3, 4
DROP = CUTS[DROP_I]
assert min(np.diff([0] + CUTF + [fr(END)])) >= int(BEAT * FPS) - 2, "plan < 1 temps"
# ---------------- phrase (Lula, fichier lot5/sources/S1-lula-camara-enterrar.mp4 = YouTube Tutjrt27Z6E dès 86 s) ----------------
# mots (Whisper sur l'extrait + enveloppe) : porque 7,15-7,45 / tentaram 7,49-8,09 / me enterrar vivo 8,09-9,05 / e eu estou aqui 9,70-10,45 / ovation ensuite
P_IN, P_OUT = 7.49, 10.45            # « Tentaram … aqui »
V_IN, V_OUT = 7.49, 12.30            # voix + début de l'ovation (fondu)
P_T0 = 0.28                          # « Tentaram » à 0,28 s de la timeline
def f2t(f): return f - P_IN + P_T0
# ---------------- plans ----------------
B_CAM = (0, 0, 1600, 850)            # sans le logo Câmara (haut droite), le bandeau et l'interprète (bas)
B_CL = (0, 0, 1560, 790)             # Clermont : sans le filigrane MELENCHON2027 (haut droite) ni le pupitre « Clermont-Ferrand »
B_CO = (0, 0, 1640, 1080)            # convention : sans le logo (haut droite)
SHOTS = {
    # --- arc 1 : Lula, victoire du 30/10/2022 ---
    "drapeau": dict(src=FOA, t=4.30, fixed=(620, 480), b=(0, 0, 1920, 1080), vh=960, zoom=(1.0, 1.05), why="Avenida Paulista 30/10/2022 : drapeau du Brésil au-dessus de la foule (Tentaram… commence)"),
    "foule":   dict(src=NJA, t=22.35, fixed=(900, 520), b=(0, 0, 1700, 1080), vh=1000, zoom=(1.0, 1.05), why="Avenida Paulista : la foule, bras levés sous les lumières (voix de Lula par-dessus : plan de foule, règle synchro)"),
    "fumis":   dict(src=FOB, t=12.2, fixed=(760, 540), b=(0, 0, 1920, 1080), vh=1080, zoom=(1.0, 1.05), why="Avenida Paulista : fumigènes rouges, bras levés (ovation)"),
    "lula":    dict(src=FOA, t=8.0, fixed=(870, 390), b=(0, 0, 1920, 770), vh=760, zoom=(1.0, 1.04), why="Lula (à gauche) sur le camion de l'Avenida Paulista, mains levées avec Haddad et Alckmin (il ne parle pas)"),
    "carton":  dict(card=True, why="charnière : carton plein écran rouge #E4002B, BRAVO, LULA! en blanc (recette hazemziadi17)"),
    # --- arc 2 : Mélenchon, « Guess who's next?! » ---
    "doigt":   dict(src=CL3, t=1.3, face=(1000, 200), b=B_CL, vh=790, zoom=(1.0, 1.04), why="DROP « We are the champions » : Clermont 2026, index levé puis bras tendu vers la salle"),
    "salle":   dict(src=ENT, t=8.4, fixed=(800, 560), b=(0, 0, 1480, 1080), vh=1080, zoom=(1.0, 1.04), why="Clermont 2026 : la salle agite les drapeaux"),
    "poing":   dict(src=CO1, t=5.0, fixed=(1010, 540), b=B_CO, vh=1080, zoom=(1.0, 1.04), why="convention 2025 : poing levé"),
    "drap7":   dict(src=CO7, t=2.0, fixed=(900, 560), b=B_CO, vh=1000, zoom=(1.0, 1.04), why="convention 2025 : foule et drapeaux"),
    "marche":  dict(src=M4018, t=5.2, face=(960, 400), b=(0, 0, 1600, 1080), vh=900, zoom=(1.0, 1.05), why="marche pour la 6e République 2022 : à la tribune, drapeaux devant"),
    "flags":   dict(src=M4895, t=5.5, fixed=(900, 560), b=(0, 0, 1920, 1080), vh=1000, zoom=(1.0, 1.04), why="marche 2022 : marée de drapeaux"),
    "parle":   dict(src=CO2, t=5.0, face=(1000, 330), b=B_CO, vh=820, zoom=(1.0, 1.05), why="convention 2025 : gros plan"),
    "liesse":  dict(src=ENT, t=40.5, fixed=(800, 560), b=(0, 0, 1480, 1080), vh=1080, zoom=(1.0, 1.04), why="Clermont 2026 : la salle en liesse, drapeaux"),
    "sourire": dict(src=CO3, t=6.0, face=(1000, 330), b=B_CO, vh=820, zoom=(1.0, 1.05), why="convention 2025 : il sourit"),
    "arene":   dict(src=CL1, t=5.6, fixed=(960, 540), b=(0, 0, 1560, 1080), vh=1080, zoom=(1.0, 1.04), why="Clermont 2026 : l'arène pleine"),
    "fin":     dict(src=ENT, t=57.0, face=(960, 300), b=B_CL, vh=760, zoom=(1.0, 1.05), why="Clermont-Ferrand 11/10/2026 : il sourit à la tribune (date posée)"),
}
EDIT = ["drapeau", "foule", "fumis", "lula", "carton", "doigt", "salle", "poing", "marche", "flags", "parle", "liesse", "sourire", "arene", "fin"]
assert len(EDIT) == len(CUTS) + 1, (len(EDIT), len(CUTS))
def slots():
    b = [0] + CUTF + [fr(END)]
    return [(sid, b[i], b[i + 1]) for i, sid in enumerate(EDIT)]
# ---------------- textes ----------------
FONT = "/System/Library/Fonts/Supplemental/Arial Black.ttf"; FONT_U = "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"
RED = (0xE4, 0x00, 0x2B)
TR_FR = ["Ils ont essayé", "de m'enterrer vivant,", "et je suis là."]  # traduction mot à mot de « Tentaram me enterrar vivo e eu estou aqui »
NEXT = "Guess who's next?!"
DATE = "11 octobre"
def _font(sz, path=FONT): return ImageFont.truetype(path, sz)
def text_layer(lines, em, yc, maxw=0.62 * W, align="center", x0=None, extra=None):
    """Calque RGBA : lignes blanches, contour sombre + ombre douce, bloc centré (ou aligné à gauche en x0)."""
    while True:
        f = _font(em); ws = [f.getbbox(l)[2] - f.getbbox(l)[0] for l in lines]
        if max(ws) <= maxw: break
        em -= 2
    lh = int(em * 1.12); h = lh * len(lines); y0 = int(yc * H - h / 2)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay); ds = ImageDraw.Draw(sh)
    pos = []
    for i, (l, w) in enumerate(zip(lines, ws)):
        x = (W - w) / 2 if align == "center" else x0
        y = y0 + i * lh
        pos.append((x, y, w))
        ds.text((x + 4, y + 6), l, font=f, fill=(0, 0, 0, 170))
        d.text((x, y), l, font=f, fill=(255, 255, 255, 255), stroke_width=max(3, em // 14), stroke_fill=(10, 10, 10, 255))
    if extra: extra(d, pos, f, em)
    sh = sh.filter(__import__("PIL.ImageFilter", fromlist=["GaussianBlur"]).GaussianBlur(6))
    return Image.alpha_composite(sh, lay)
def heart(d, pos, f, em):
    x, y, w = pos[-1]; fh = _font(em, FONT_U)
    d.text((x + w + em * 0.3, y + em * 0.05), "♥", font=fh, fill=RED + (255,), stroke_width=max(2, em // 18), stroke_fill=(10, 10, 10, 255))
_LAY = {}
def layer(key):
    if key not in _LAY:
        if key == "tr": _LAY[key] = text_layer(TR_FR, 60, 0.665)
        elif key == "next": _LAY[key] = text_layer([NEXT], 62, 0.665)
        elif key == "date": _LAY[key] = text_layer([DATE], 44, 0.725, maxw=0.45 * W, align="left", x0=int(0.19 * W), extra=heart)
        _LAY[key] = np.asarray(_LAY[key]).astype(np.float32) / 255
    return _LAY[key]
def put(frame_bgr, key):
    l = layer(key); a = l[..., 3:4]; rgb = l[..., :3][..., ::-1]
    return frame_bgr * (1 - a) + rgb * a
def card_frames(n):
    img = Image.new("RGB", (W, H), RED); d = ImageDraw.Draw(img)
    lines = ["BRAVO,", "LULA!"]; em = 190
    while True:
        f = _font(em); ws = [f.getbbox(l)[2] - f.getbbox(l)[0] for l in lines]
        if max(ws) <= 0.54 * W: break
        em -= 4
    lh = int(em * 1.08); y0 = int(0.43 * H - lh * len(lines) / 2)
    for i, (l, w) in enumerate(zip(lines, ws)): d.text(((W - w) / 2 - f.getbbox(l)[0], y0 + i * lh), l, font=f, fill=(255, 255, 255))
    base = np.asarray(img)[..., ::-1].astype(np.float32) / 255
    base = base + RNG.normal(0, 0.008, base.shape[:2]).astype(np.float32)[..., None]
    out = []
    for i in range(n):
        x = base.copy()
        if i < 2: x = x + (1 - x) * (0.55 if i == 0 else 0.25)       # flash d'entrée (recette : flash cut avant/après)
        out.append(np.clip(x, 0, 1))
    return out
# ---------------- look : couleur pleine (vive), contraste en S, léger bloom ----------------
RNG = np.random.default_rng(5)
def grade(bgr):
    x = np.clip(bgr, 0, 1)
    l = 0.114 * x[..., 0] + 0.587 * x[..., 1] + 0.299 * x[..., 2]
    s = l * l * (3 - 2 * l)
    x = x + (s - l)[..., None] * 0.25
    l2 = (0.114 * x[..., 0] + 0.587 * x[..., 1] + 0.299 * x[..., 2])[..., None]
    x = l2 + (x - l2) * 1.18                                          # saturation +18 % (couleur pleine)
    small = cv2.resize(x, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    hi = np.clip(small - 0.70, 0, None)
    x = x + cv2.resize(cv2.GaussianBlur(hi, (0, 0), 10), (W, H)) * 0.35
    x = vignette(x, 0.20, 2.4)
    x = x + RNG.normal(0, 0.008, x.shape[:2]).astype(np.float32)[..., None]
    return np.clip(x, 0, 1)
def read_frames(src, t, n_out):
    fps_s = sfps(src)
    need = [int(round(i * fps_s / FPS)) for i in range(n_out)]; n_src = need[-1] + 1
    p = subprocess.run([FF, "-v", "error", "-ss", "%.4f" % t, "-i", SRCDIR + src, "-frames:v", str(n_src),
                        "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True)
    a = np.frombuffer(p.stdout, np.uint8).reshape(-1, 1080, 1920, 3)
    return [a[min(i, len(a) - 1)].astype(np.float32) / 255 for i in need], int(round(t * fps_s)), fps_s
def crop_916(img, cx, cy, vh):
    vw = vh * 9 / 16; s = W / vw
    M = np.float32([[s, 0, W / 2 - cx * s], [0, s, H / 2 - cy * s]])
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
def write_mov(frames, path, fps=FPS):
    p = subprocess.Popen([FF, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", "%dx%d" % (W, H), "-r", str(fps), "-i", "-",
                          "-c:v", "prores_ks", "-profile:v", "3", "-pix_fmt", "yuv422p10le", "-vendor", "apl0", path], stdin=subprocess.PIPE)
    for f in frames: p.stdin.write(to8(f).tobytes())
    p.stdin.close(); p.wait()
def views_for(sid, n):
    sh = SHOTS[sid]; fps_s = sfps(sh["src"]); s0 = int(round(sh["t"] * fps_s))
    z0, z1 = sh["zoom"]; zoom = lambda f: z0 + (z1 - z0) * min(f / max(n - 1, 1), 1.0)
    if "fixed" in sh:
        v, _ = plan_views(sh["src"], s0, n, fps_s, speed=fps_s / FPS, bounds=sh["b"], vh=sh["vh"], zoom=zoom, fixed=sh["fixed"]); return v
    v, ok = plan_views(sh["src"], s0, n, fps_s, speed=fps_s / FPS, hint=sh["face"], bounds=sh["b"], vh=sh["vh"], zoom=zoom, top=0.14)
    if not ok: print("  ! pas de visage :", sid)
    return v
def text_key(sid, a):
    i = EDIT.index(sid)
    if sid == "fin": return ["next", "date"]
    if i > DROP_I - 1 and sid != "carton": return ["next"]
    return []
def render_slot(sid, a, b):
    sh = SHOTS[sid]; n = b - a
    if sh.get("card"):
        write_mov(card_frames(n), OUT + "S1_%s.mov" % sid); print("  %-8s %3d im  carton" % (sid, n)); return
    raw, s0, fps_s = read_frames(sh["src"], sh["t"], n)
    views = views_for(sid, n)
    keys = text_key(sid, a); frames = []
    for k, (img, (cx, cy, vh)) in enumerate(zip(raw, views)):
        x = grade(crop_916(img, cx, cy, vh))
        if sid == "doigt" and k < 2: x = x + (1 - x) * (0.45 if k == 0 else 0.2)   # flash de sortie du carton (drop)
        tl = (a + k) / FPS
        if f2t(P_IN) - 0.05 <= tl <= f2t(P_OUT) + 0.35: x = put(x, "tr")
        for key in keys: x = put(x, key)
        frames.append(np.clip(x, 0, 1))
    write_mov(frames, OUT + "S1_%s.mov" % sid)
    vx, vz = views[0], views[-1]
    print("  %-8s %3d im  vue %d,%d h%d -> h%d  (x %d-%d, y %d-%d)" % (sid, n, vx[0], vx[1], vx[2], vz[2], vx[0] - vx[2] * 9 / 32, vx[0] + vx[2] * 9 / 32, vx[1] - vx[2] / 2, vx[1] + vx[2] / 2))
def probe():
    """Planche : 1re, milieu, dernière image de chaque plan (sans texte) pour choisir cadrages et vérifier logos."""
    tiles = []
    for sid, a, b in slots():
        sh = SHOTS[sid]; n = b - a
        if sh.get("card"): tiles.append([card_frames(3)[2]] * 3); continue
        raw, _, _ = read_frames(sh["src"], sh["t"], n); v = views_for(sid, n)
        tiles.append([grade(crop_916(raw[i], *v[i])) for i in (0, n // 2, n - 1)])
    cols = len(tiles); tw, th = 180, 320
    sheet = np.zeros((th * 3, tw * cols, 3), np.uint8)
    for c, tl in enumerate(tiles):
        for r, im in enumerate(tl): sheet[r * th:(r + 1) * th, c * tw:(c + 1) * tw] = cv2.resize(to8(im), (tw, th), interpolation=cv2.INTER_AREA)
    cv2.imwrite(D + "cache/probe.jpg", sheet); print("probe", D + "cache/probe.jpg")
# ---------------- plan ----------------
def build_plan():
    video = []
    for sid, a, b in slots():
        sh = SHOTS[sid]; n = b - a
        v = {"id": "%s_%d" % (sid, a), "clip": "S1_%s.mov" % sid, "folder": "genS1", "s": 0, "e": n, "rec": a, "track": 1, "kind": "shot",
             "clip_fps": FPS, "dur": n, "speed_pct": 100, "effet": "coupe franche", "temps": round(n / FPS / BEAT, 1), "pourquoi": sh["why"]}
        if sh.get("card"): v.update(kind="carton", source="généré (genS1.py card_frames)", contexte="carton BRAVO, LULA! rouge #E4002B")
        else:
            folder, url, off, ctx = SRC_INFO[sh["src"]]
            v.update(source="%s/%s @ %.3f s (%s @ %.2f s)" % (folder, sh["src"], sh["t"], url, off + sh["t"]), contexte=ctx)
        tk = text_key(sid, a)
        if tk: v["texte"] = [{"next": NEXT, "date": DATE + " ♥ (date du meeting de Clermont-Ferrand)"}[k] for k in tk]
        if sid in ("drapeau", "foule", "fumis"): v["texte"] = [" / ".join(TR_FR) + " (traduction de la phrase de Lula, pendant qu'elle est dite)"]
        video.append(v)
    plan = {"name": "S1 - Arc solidarité Lula 2022 -> Mélenchon (Queen - We Are The Champions)", "fps": FPS, "w": W, "h": H, "duree_s": END,
            "note": "Plans 9:16 recadrés + étalonnés couleur pleine, textes cuits (lot5/_claude/gen/S1/out). s/e en images du clip (30 i/s), rec en images timeline. "
                    "Coupes sur les frappes réelles de la musique posée (out/S1-frappes.json), carton BRAVO, LULA! 1 temps juste avant le drop, drop = « We are the champions ». "
                    "Aucun ralenti. Recette hazemziadi17 (arc victoire étrangère -> figure française, sous-titre courant Guess who's next?!, date sur le dernier plan).",
            "phrase": {"texte": "Tentaram me enterrar vivo e eu estou aqui.", "traduction": "Ils ont essayé de m'enterrer vivant, et je suis là.",
                       "source": "https://www.youtube.com/watch?v=Tutjrt27Z6E (chaîne Câmara dos Deputados, 1er discours de Lula élu, São Paulo 30/10/2022), %.2f-%.2f s — fichier lot5/sources/%s %.2f-%.2f s" % (86 + P_IN, 86 + P_OUT, CAM, P_IN, P_OUT),
                       "timeline_s": [round(f2t(P_IN), 3), round(f2t(P_OUT), 3)]},
            "video": video,
            "audio": [{"id": "mix", "clip": "S1-mix.wav", "folder": "genS1", "rec": 0, "track": 1, "note": "mix -14 LUFS, TP <= -1 dBTP"}],
            "stems": ["lot5/_claude/gen/S1/out/S1-voix.wav", "lot5/_claude/gen/S1/out/S1-musique.wav"],
            "musique": {"fichier": "lot5/sons/S1-queen-champions_complet.wav", "titre": "Queen - We Are The Champions", "url": MURL,
                        "debut_complet_s": S0, "fin_complet_s": round(S0 + END, 3), "coupes_timeline_s": CUTS, "drop_timeline_s": DROP},
            "logos_exclus": "logo TV Câmara, bandeau et interprète hors fenêtre ; filigranes MELENCHON2027 et pupitre Clermont-Ferrand hors fenêtre ; logo convention hors fenêtre"}
    json.dump(plan, open(D + "plan-S1.json", "w"), indent=1, ensure_ascii=False)
    son = {"id": "S1", "titre": "We Are The Champions", "artiste": "Queen", "url": MURL, "version": "Queen - We Are The Champions (Official Video Remastered), chaîne Queen Official (certifiée), 185 s",
           "fichier": "lot5/sons/S1-queen-champions_complet.wav",
           "extrait_utilise": {"debut_complet_s": S0, "fin_complet_s": round(S0 + END, 3), "duree_s": END,
                               "contenu": "« …And I need to go on, and on, and on, and on » (build, baissé -9 dB sous Lula puis remontée) ; drop « We are the champions, my friends / And we'll keep on fighting till the end » (1er refrain)"},
           "bpm": 63, "drop": {"complet_s": _d["coupes_complet"][DROP_I], "timeline_s": DROP, "note": "« We are the champions » (1er refrain, kick)"},
           "coupes_timeline_s": CUTS, "frappes_timeline_s": HITS,
           "methode": "hits.py (copie de lot4/_claude/gen/M1/hits.py) sur la musique posée ; mesure sur l'export dans mesure()"}
    json.dump(son, open(D + "son.json", "w"), indent=1, ensure_ascii=False)
    return plan
# ---------------- audio ----------------
def loud(path):
    r = subprocess.run([FF, "-hide_banner", "-i", path, "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True).stderr
    return float([l for l in r.splitlines() if l.strip().startswith("I:")][-1].split()[1])
def make_audio():
    import soundfile as sf
    sr = 48000; N = int(round(END * sr))
    p = subprocess.run([FF, "-v", "error", "-ss", "%.3f" % V_IN, "-t", "%.3f" % (V_OUT - V_IN), "-i", SRCDIR + CAM,
                        "-ac", "2", "-ar", str(sr), "-f", "f32le", "-"], capture_output=True)
    v = np.frombuffer(p.stdout, np.float32).reshape(-1, 2).copy()
    fi, fo = int(0.02 * sr), int(0.9 * sr); v[:fi] *= np.linspace(0, 1, fi)[:, None]; v[-fo:] *= np.linspace(1, 0, fo)[:, None]
    m = music_raw(S0, sr, END + 0.1)[:N].copy()
    pv = int((P_OUT - V_IN) * sr)
    sf.write(D + "tmp_v.wav", v[:pv], sr, subtype="FLOAT"); sf.write(D + "tmp_m.wav", m, sr, subtype="FLOAT")
    lv, lm = loud(D + "tmp_v.wav"), loud(D + "tmp_m.wav"); os.remove(D + "tmp_v.wav"); os.remove(D + "tmp_m.wav")
    gv = 10 ** ((lm - lv + 1.0) / 20)                                 # voix 1 dB au-dessus de la musique pleine, musique -10 dB dessous
    voix = np.zeros((N, 2), np.float32); a = int(round(f2t(V_IN) * sr)); L = min(len(v), N - a); voix[a:a + L] = v[:L] * gv
    t = np.arange(N) / sr; g = np.ones(N, np.float32); lo = 10 ** (-10 / 20)
    def ramp(t0, t1, g0, g1):
        s = (t >= t0) & (t < t1); g[s] = g0 + (g1 - g0) * (t[s] - t0) / (t1 - t0)
    tv0, tv1 = f2t(P_IN), f2t(P_OUT)
    g[t < tv1] = lo; ramp(0, 0.06, 0, lo)                              # build baissé sous la phrase
    ramp(tv1 + 0.05, CUTS[CARD_I], lo, 0.9)                           # montée « and on, and on » jusqu'au carton
    g[(t >= CUTS[CARD_I]) & (t < DROP)] = 0.95
    s = t > END - 0.30; g[s] *= np.clip((END - t[s]) / 0.30, 0, 1)
    mus = m * g[:, None]
    sf.write(OUT + "S1-voix.wav", voix, sr, subtype="PCM_24"); sf.write(OUT + "S1-musique.wav", mus, sr, subtype="PCM_24")
    sf.write(D + "tmp_mix.wav", voix + mus, sr, subtype="FLOAT")
    r_ = subprocess.run([FF, "-hide_banner", "-i", D + "tmp_mix.wav", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                        capture_output=True, text=True).stderr
    js = json.loads(r_[r_.rindex("{"):r_.rindex("}") + 1])
    af = ("loudnorm=I=-13.6:TP=-2:LRA=11:measured_I=%s:measured_TP=%s:measured_LRA=%s:measured_thresh=%s:offset=%s:linear=true,"
          "alimiter=limit=0.83:level=false:attack=1:release=60,aresample=48000"
          % (js["input_i"], js["input_tp"], js["input_lra"], js["input_thresh"], js["target_offset"]))
    subprocess.run([FF, "-v", "error", "-y", "-i", D + "tmp_mix.wav", "-af", af, "-c:a", "pcm_s24le", OUT + "S1-mix.wav"], check=True)
    os.remove(D + "tmp_mix.wav"); print("audio : voix %.1f / musique %.1f LUFS, gain voix %+.1f dB ; mix avant normalisation %s LUFS" % (lv, lm, 20 * math.log10(gv), js["input_i"]))
# ---------------- aperçu 540x960 ----------------
APERCU = ROOT + "/preview/apercu-S1.mp4"
def apercu():
    plan = json.load(open(D + "plan-S1.json")); ins = []; fl = []
    for i, v in enumerate(plan["video"]):
        ins += ["-i", OUT + v["clip"]]
        fl.append("[%d:v]trim=start_frame=%d:end_frame=%d,setpts=PTS-STARTPTS,scale=540:960,setsar=1[v%d]" % (i, v["s"], v["e"], i))
    k = len(plan["video"])
    fl.append("".join("[v%d]" % i for i in range(k)) + "concat=n=%d:v=1:a=0[v]" % k)
    ins += ["-i", OUT + "S1-mix.wav"]
    subprocess.run([FF, "-v", "error", "-y"] + ins + ["-filter_complex", ";".join(fl), "-map", "[v]", "-map", "%d:a" % k,
                    "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "aac", "-b:a", "192k", "-shortest", APERCU], check=True)
    print("aperçu", APERCU)
# ---------------- contrôle visages : tout visage > 5 % de la hauteur doit être entier, dans chaque plan ----------------
def check_faces():
    plan = json.load(open(D + "plan-S1.json")); bad = []
    for v in plan["video"]:
        if v["kind"] == "carton": continue
        n = v["e"] - v["s"]
        d = D + "cache/chk_" + v["clip"]; shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
        subprocess.run([FF, "-v", "error", "-i", OUT + v["clip"], "-vf", "select='lt(n\\,%d)',scale=540:960" % n, "-fps_mode", "passthrough",
                        "-q:v", "3", d + "/f%04d.jpg"], check=True)
        subprocess.run([FACES, d], check=True, capture_output=True)
        js = json.load(open(d + "/faces.json")); nb = 0
        for k, fl in js.items():
            for x, y, w, h in fl:
                if h < 0.05: continue
                top, bot, l, r = y - 0.3 * h, y + h * 1.05, x - 0.08 * w, x + w * 1.08
                if top < 0 or bot > 1 or l < 0 or r > 1: nb += 1; bad.append("%s %s (%.2f %.2f %.2f %.2f h%.2f)" % (v["clip"], k, top, bot, l, r, h))
        print("  visages", v["clip"], "images", len(js), "coupés", nb)
        shutil.rmtree(d, ignore_errors=True)
    print("TOTAL visages coupés :", len(bad)); print("\n".join(bad[:40]))
# ---------------- mesure sur l'export : coupes (changement d'image) vs frappes (audio de l'export) ----------------
def mesure():
    p = subprocess.run([FF, "-v", "error", "-i", APERCU, "-vf", "scale=54:96", "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True)
    fr_ = np.frombuffer(p.stdout, np.uint8).reshape(-1, 96, 54).astype(np.float32)
    diff = np.abs(np.diff(fr_, axis=0)).mean((1, 2))
    cuts_exp = [(i + 1) / FPS for i in range(len(diff)) if diff[i] > 12 and diff[i] > 2.5 * np.median(diff[max(0, i - 5):i + 6])]
    p = subprocess.run([FF, "-v", "error", "-i", APERCU, "-ac", "2", "-ar", "48000", "-f", "f32le", "-"], capture_output=True)
    y = np.frombuffer(p.stdout, np.float32).reshape(-1, 2)
    hits = detect_hits(y.copy(), 48000, delta=0.08)
    import soundfile as sf
    hits_m = detect_hits(sf.read(OUT + "S1-musique.wav", dtype="float32")[0], 48000, delta=0.08)                               # frappes détectées sur l'audio de l'export (même méthode que la pose)
    print("images", len(fr_), "durée %.3f s" % (len(fr_) / FPS), "| coupes détectées :", ["%.3f" % c for c in cuts_exp])
    errs = []
    for c in CUTS:
        ce = min(cuts_exp, key=lambda x: abs(x - c)) if cuts_exp else float("nan")
        near = [h for h in hits if abs(h[0] - c) < 0.04]; src_ = "export"
        if not near: near = [h for h in hits_m if abs(h[0] - c) < 0.04]; src_ = "stem musique (frappe masquée par la voix)"
        h = min(near, key=lambda h: abs(h[0] - c))[0] if near else float("nan")
        e = (ce - h) * 1000; errs.append(abs(e))
        print("  coupe prévue %.3f | image de coupe export %.3f | frappe %.4f (%s) | écart %+.1f ms" % (c, ce, h, src_, e))
    print("ÉCART MAX coupes/frappes : %.1f ms (%d coupes mesurées sur %d)" % (max(e for e in errs if e == e), sum(e == e for e in errs), len(errs)))
    r = subprocess.run([FF, "-hide_banner", "-i", APERCU, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    print("\n".join(l for l in r.splitlines()[-12:] if "I:" in l or "Peak:" in l or "LRA:" in l))
if __name__ == "__main__":
    args = set(a for a in sys.argv[1:] if not a.startswith("only=")) or {"shots", "plan", "audio", "apercu", "check", "mesure"}
    only = [x for a in sys.argv[1:] if a.startswith("only=") for x in a.split("=", 1)[1].split(",")]
    print("S0 = %.4f s du complet, fin %.3f s, coupes timeline :" % (S0, END), CUTS, "drop", DROP)
    print("phrase timeline %.3f-%.3f" % (f2t(P_IN), f2t(P_OUT)))
    if "probe" in args: probe()
    if "shots" in args or only:
        for sid, a, b in slots():
            if not only or sid in only: render_slot(sid, a, b)
    if "plan" in args: build_plan()
    if "audio" in args: make_audio()
    if "apercu" in args: apercu()
    if "check" in args: check_faces()
    if "mesure" in args: mesure()
