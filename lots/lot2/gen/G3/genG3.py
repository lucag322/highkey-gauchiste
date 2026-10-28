# G3 — Glow, Antoine Léaument (lot 2), son « TENDU » (Josman). Modèle : _claude/gen/4/gen4.py + exports/test-4-glow.mp4.
# Aperçu hors Resolve : plans ProRes 9:16 recadrés (visage suivi), étalonnage glow chaud, texte cuit (Avenir Next Bold Italic,
# TOUT en blanc, halo doré pris dans les ornements de l'hémicycle + contour sombre, jamais de rouge).
# Ralentis PAS précalculés : clip à vitesse normale (n = durée_tl/30 × fps_source), speed_pct + retime dans plan-G3.json.
# Usage : python genG3.py [plans] [audio] [apercu] [only=ID,ID]
import sys, os, json, subprocess
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
ROOT = "/Users/luca.grousset/Movies/highkey-gauchiste"; LOT = ROOT + "/lot2"
sys.path.insert(0, ROOT + "/_claude/outils")
import framing
from framing import plan_views
from fx import crop_view, vignette, grain, gblur
from words import clean
FF = "/opt/homebrew/bin/ffmpeg"
D = LOT + "/_claude/gen/G3/"; OUT = D + "out/"; os.makedirs(OUT, exist_ok=True)
framing.ROOT = LOT; framing.CACHE = D + "cache"
AN = "G3-leaument-an-securite-2026-06.mp4"; LCP = "G3-leaument-lcp-qag-2026-04.mp4"
W, H, TFPS, SFPS = 1080, 1920, 30, 25
FONT = ("/System/Library/Fonts/Avenir Next.ttc", 1)          # Avenir Next Bold Italic (test 4)
GLOW = (255, 184, 77)        # #FFB84D : or des ornements de l'hémicycle (mesuré 195,133,68 sur 221 s, éclairci)
WHITE = (255, 255, 255)
# bornes source sans logos : AN = logo LFI en haut à gauche (x<350) + emblème AN en haut à droite (x>1600)
B_AN = (360, 0, 1600, 1080)
B_LCP = (420, 0, 1400, 830)   # LCP : interprète LSF + chrono à droite, bandeaux en bas, voisine à gauche

# ---------------- temps ----------------
# Retour Luca (HD 15h05) : coupes et poussées hors rythme. La grille de sons-lot2.json (68,5 BPM) dérive et tombe à côté des frappes.
# On cale tout sur les kicks 808 RÉELS du morceau tel que posé (rythme/frappes.py -> rythme/frappes.json, temps timeline).
SON = [x for x in json.load(open(LOT + "/_claude/sons-lot2.json"))["sons"] if x["id"] == "G3"][0]
FR = json.load(open(D + "rythme/frappes.json")); MOFF = FR["MOFF"]       # temps extrait = timeline + MOFF (placement inchangé)
K = FR["kicks_808"]                                                      # 5,408 6,067 6,724 8,045 8,477 8,918 9,572 10,229 12,000 12,443 13,078 13,731
DROP = K[0]                                   # 1er kick 808 après la phrase (finit à 5,20 s) : entrée pleine du morceau + 1re coupe
END = 14.90                                   # règle Luca : glow 15 s max
V = 221.70                                    # voix : timeline = source - V (phrase 221,84-226,90 s -> 0,14-5,20 s)
def f30(t): return int(round(t * TFPS))

# ---------------- textes (mot à mot, phrase réelle) ----------------
G = json.load(open(LOT + "/_claude/derush-AG.json"))["figures"]["G3"]["phrase"]
T = []
for w in G["mots"]:
    if w["start"] < 221.8: continue
    if w["w"] == "?": T[-1]["w"] += " ?"; continue          # point d'interrogation gardé (sens de la question)
    T.append({"w": w["w"], "start": w["start"]})
assert len(T) == 18, [t["w"] for t in T]
def up(t): return clean(t["w"].replace(" ?", "")).upper() + (" ?" if t["w"].endswith("?") else "")
# Vous voulez | des policiers | qui courent | après les | manifestants ? | Nous voulons | des policiers | qui déjouent | les projets | terroristes.
GROUPS = [2, 2, 2, 2, 1, 2, 2, 2, 2, 1]
assert sum(GROUPS) == len(T)
CARDS, i = [], 0
for g in GROUPS:
    CARDS.append({"words": [(up(T[j]), T[j]["start"] - V) for j in range(i, i + g)]}); i += g
for k, c in enumerate(CARDS): c["t1"] = CARDS[k + 1]["words"][0][1] if k + 1 < len(CARDS) else DROP
YT = 0.60                                    # centre vertical du texte (test 4 : 60 % depuis le haut)
_fc = {}
def font(px):
    px = int(round(px))
    if px not in _fc: _fc[px] = ImageFont.truetype(FONT[0], px, index=FONT[1])
    return _fc[px]
def card_size(c):
    f = font(100); txt = " ".join(w[0] for w in c["words"])
    return min(110, 0.88 * W / (f.getlength(txt) / 100))       # test 4 : em_max 150 en Text+ = 110 px PIL, 88 % de largeur
def draw_text(img, t):
    act = [c for c in CARDS if c["words"][0][1] - 1e-3 <= t < c["t1"]]
    if not act: return img
    lay = Image.new("L", (W, H), 0); dl = ImageDraw.Draw(lay)
    for c in act:
        px = card_size(c); f = font(px); sp = f.getlength(" ")
        tot = sum(f.getlength(w[0]) for w in c["words"]) + sp * (len(c["words"]) - 1)
        x = W / 2 - tot / 2; y = YT * H
        for word, tw in c["words"]:
            if tw <= t + 1e-3: dl.text((x, y), word, font=f, anchor="lm", fill=255)   # apparition sèche au mot (comme le test 4)
            x += f.getlength(word) + sp
    a = np.asarray(lay, np.float32) / 255
    g1 = np.clip(gblur(a, 24 / 2.5) * 2.2, 0, 1); g2 = np.clip(gblur(a, 8 / 2.5) * 1.6, 0, 1)   # halo large + serré (cards.py)
    col = np.array(GLOW[::-1], np.float32) / 255
    out = img
    for g in (g1, g2): out = out * (1 - g[..., None]) + col * g[..., None]
    sh = gblur(a, 2.2)
    for _ in range(3): out = out * (1 - sh[..., None])                         # contour sombre serré ×3
    return out * (1 - a[..., None]) + np.array(WHITE, np.float32) / 255 * a[..., None]

# ---------------- étalonnage « glow » ----------------
VIG = None
def grade(img, nb=False):
    global VIG
    x = img
    if nb:
        y = x @ np.array([0.114, 0.587, 0.299], np.float32); x = np.repeat(y[..., None], 3, 2)
        x = np.clip((x - 0.03) * 1.15, 0, 1) ** 1.1 * 0.9
    else:
        x = np.clip((x - 0.02) * 1.08, 0, 1); x = x * x * (3 - 2 * x) * 0.35 + x * 0.65        # contraste doux
        lum = x @ np.array([0.114, 0.587, 0.299], np.float32)
        x = lum[..., None] + (x - lum[..., None]) * 1.05
    hi = np.clip((x - 0.55) / 0.45, 0, 1)                        # soft glow (SoftGlow seuil 0,6, gain 0,5-0,7)
    x = x + gblur(hi, 18) * (0.25 if nb else 0.45)
    if VIG is None: VIG = vignette(np.ones((H, W, 3), np.float32), strength=0.45, power=2.2)
    return grain(np.clip(x, 0, 1) * VIG, 0.012, 1.4)

# ---------------- liste des plans ----------------
# Chaque coupe = image la plus proche d'un kick 808 (écart <= 16,7 ms). Poussée : démarre sur la coupe (kick), décélère fort
# et s'arrête pile sur le kick de la coupe suivante, calculée en TEMPS TIMELINE (ralentis compris).
# Clips : vitesse normale = 30 i/s (image source 25 i/s la plus proche, comme Resolve) ; ralenti = images source 25 i/s
# étiquetées 30 i/s, Resolve à 41,667 % (= 50 % du temps réel) en Optical Flow : 1 image clip = 1 image timeline, aucun arrondi.
def S(i, a, b, src, t_in, sp, hint, bnd, vh, z0, z1, fx="", note=""):
    return dict(id=i, a=a, b=b, src=src, t_in=t_in, sp=sp, hint=hint, bnd=bnd, vh=vh, z0=z0, z1=z1, fx=fx, note=note)
SHOTS = [
    S("A", 0.0, K[0], AN, V, 100, (830, 260), B_AN, 760, 1.0, 1.10, "texte", "phrase entière, synchro, poussée lente jusqu'au 1er kick, texte cuit"),
    S("B0", K[0], K[2], AN, 20.40, 100, (830, 260), B_AN, 700, 1.0, 1.06, "nb", "N&B sur l'entrée du morceau : geste, regard de côté"),
    S("B1", K[2], K[3], AN, 193.30, 50, (840, 260), B_AN, 760, 1.0, 1.06, "", "bras tendu vers les bancs (ralenti)"),
    S("B2", K[3], K[5], AN, 116.45, 100, (870, 260), B_AN, 700, 1.0, 1.06, "", "index levé puis main à la tête"),
    S("B3", K[5], K[7], LCP, 107.00, 100, (930, 270), B_LCP, 760, 1.0, 1.06, "", "LCP QAG avril 2026 : debout, micro, regard droit"),
    S("B4", K[7], K[8], AN, 52.00, 50, (880, 250), B_AN, 760, 1.0, 1.07, "", "tourné vers la droite, assuré (ralenti, sur la nappe de 808)"),
    S("B5", K[8], K[10], AN, 268.00, 100, (850, 250), B_AN, 700, 1.0, 1.06, "", "redressé, voix forte"),
    S("B6", K[10], K[11], AN, 142.30, 100, (900, 250), B_AN, 700, 1.0, 1.05, "", "regard vers la droite"),
    S("B7", K[11], END, AN, 195.30, 50, (840, 260), B_AN, 760, 1.0, 1.08, "fin", "index levé -> poing (ralenti), fondu au noir 0,6 s"),
]
for sh in SHOTS:
    sh["rec"] = f30(sh["a"]); sh["dur"] = f30(sh["b"]) - sh["rec"]
    sh["clip"] = "G3k_%s.mov" % sh["id"]   # « k » = version calée sur les kicks : nouveaux noms, pas de clip périmé dans le Media Pool
    sh["speed_res"] = 100.0 if sh["sp"] == 100 else sh["sp"] * SFPS / TFPS    # vitesse à régler dans Resolve sur le clip 30 i/s
def ease_out(u): u = min(max(u, 0.0), 1.0); return 1 - (1 - u) ** 3
def zoom_at(sh, t):                                   # t = temps timeline
    if sh["fx"] == "texte": u = (t - sh["a"]) / (sh["b"] - sh["a"]); u = min(max(u, 0), 1)     # phrase : poussée régulière
    else: u = ease_out((t - sh["a"]) / (sh["b"] - sh["a"]))
    return sh["z0"] + (sh["z1"] - sh["z0"]) * u

# ---------------- rendu d'un plan ----------------
def read_frames(src, t, n):
    p = subprocess.Popen([FF, "-v", "error", "-ss", "%.4f" % t, "-i", LOT + "/sources/" + src, "-frames:v", str(n),
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
    if slow:   # image clip k = image source s0+k, affichée au temps timeline a + k / (25 × 0,5)
        tl_t = lambda k: sh["a"] + k / (SFPS * sh["sp"] / 100); src_i = lambda k: k; spd = 1.0; n_src = n
    else:      # image clip k (30 i/s) = image source la plus proche de t_in + k/30
        tl_t = lambda k: sh["a"] + k / TFPS; src_i = lambda k: int(round(k * SFPS / TFPS)); spd = SFPS / TFPS; n_src = src_i(n - 1) + 1
    vh0 = sh["vh"]
    views, ok = plan_views(sh["src"], s0, n, SFPS, speed=spd, hint=sh["hint"], bounds=sh["bnd"], vh=vh0, zoom=lambda k: zoom_at(sh, tl_t(k)), top=0.16)
    frames = list(read_frames(sh["src"], s0 / SFPS, n_src))
    w = writer(OUT + sh["clip"], TFPS)
    for k in range(n):
        fr = frames[min(src_i(k), len(frames) - 1)]
        cx, cy, vh = views[k]; vw = vh * 9 / 16
        img = crop_view(fr.astype(np.float32) / 255, cx, cy, vw, W, H)
        img = grade(img, sh["fx"] == "nb")
        t = tl_t(k)
        if sh["fx"] == "texte": img = draw_text(img, t)
        if sh["fx"] == "fin": img = img * min(max((END - t) / 0.6, 0.0), 1.0)          # fondu au noir cuit (0,6 s timeline)
        w.stdin.write((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8).tobytes())
    w.stdin.close(); w.wait()
    return ("visage" if ok else "SANS VISAGE") + ("" if len(frames) >= n_src else " court:%d/%d" % (len(frames), n_src))

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
def build_audio():
    from scipy.signal import butter, sosfilt
    n = int(END * SR); mix = np.zeros((n, 2), np.float32)
    v = fade(load(LOT + "/sources/" + AN, V + 0.10, 226.98 - V - 0.10), 0.03, 0.08)     # « Vous voulez … terroristes. » 221,80-226,98
    lv, _ = lufs(v); v *= db(-15 - lv)
    m = load(LOT + "/" + SON["fichier"], MOFF, END)
    lm, _ = lufs(m[int(DROP * SR):]); m *= db(-14 - lm)
    t = np.arange(len(m)) / SR
    lo = sosfilt(butter(4, 420, "low", fs=SR, output="sos"), m, axis=0).astype(np.float32)   # sous la voix : morceau étouffé (le rap ne gêne pas la phrase)
    a = np.interp(t, [0, DROP - 0.06, DROP], [1, 1, 0])[:, None].astype(np.float32)
    mus = lo * db(-7) * a + m * (1 - a)
    mus *= (np.clip((END - t) / 1.2, 0, 1) ** 1.5)[:, None].astype(np.float32)               # fondu de fin avec l'image
    mus = fade(mus, 0.25, 0)
    mix[:len(mus)] += mus; i0 = int(0.10 * SR); mix[i0:i0 + len(v)] += v[:n - i0]
    tmp = OUT + "_tmp_mix.wav"; sf_write(tmp, mix); g = 0.0; li, _ = lufs(mix)
    for _ in range(3):
        g += -14.0 - li
        subprocess.run([FF, "-v", "error", "-y", "-i", tmp, "-af", "volume=%.2fdB,alimiter=limit=0.80:attack=3:release=60:level=false,aresample=192000,alimiter=limit=0.82:attack=1:release=40:level=false,aresample=48000" % g,
                        "-c:a", "pcm_s24le", OUT + "G3k-mix.wav"], check=True)
        li, tp = lufs(load(OUT + "G3k-mix.wav"))
        if abs(li + 14) < 0.3 and tp < -1.0: break
    os.remove(tmp)
    return "mix %.1f LUFS, true peak %.1f dBTP" % (li, tp)

# ---------------- plan-G3.json ----------------
def write_plan():
    vid = []
    for sh in SHOTS:
        sp = sh["sp"]; used = sh["dur"] / TFPS * sp / 100
        it = {"id": sh["id"], "clip": sh["clip"], "folder": "G3", "path": OUT + sh["clip"], "s": 0, "e": sh["dur"], "clip_fps": TFPS,
              "rec": sh["rec"], "dur": sh["dur"], "track": 1, "note": sh["note"],
              "source": {"fichier": "lot2/sources/" + sh["src"], "in_s": round(sh["t_in"], 3), "out_s": round(sh["t_in"] + used, 3)},
              "effets": "recadrage 9:16 suivi visage (sans logo), glow chaud%s" % (
                  {"nb": ", N&B", "texte": ", texte cuit", "fin": ", fondu au noir 0,6 s cuit"}.get(sh["fx"], ""))}
        it["frappe_s"] = round(sh["a"], 3); it["poussee"] = "x%.2f -> x%.2f, du kick %.3f s au kick %.3f s (temps timeline)" % (sh["z0"], sh["z1"], sh["a"], sh["b"])
        if sp != 100:
            it["speed_pct"] = round(sh["speed_res"], 4); it["retime"] = "optical_flow"
            it["ralenti"] = "%d %% du temps réel : clip = images source 25 i/s étiquetées 30 i/s, Resolve à %.4f %%" % (sp, sh["speed_res"])
        vid.append(it)
    plan = {"name": "G3 - Glow - Leaument", "fps": 30, "w": 1080, "h": 1920, "duree_s": END,
            "note": "Lot 2, recalé sur les kicks 808 réels (rythme/frappes.json). Plans ProRes 9:16 30 i/s prêts (recadrés, poussées, étalonnés, texte cuit sur A, fondu cuit sur B7) : e = durée timeline, aucun arrondi 25->30. Ralentis : speed_pct (41,6667 sur clip étiqueté 30 i/s = 50 %% réel) + Optical Flow + Speed Warp. Générateur : lot2/_claude/gen/G3/genG3.py, halo %s" % ("#%02X%02X%02X" % GLOW),
            "musique": {"fichier": "lot2/" + SON["fichier"], "debut_extrait_s": round(MOFF, 3), "entree_pleine_timeline_s": DROP, "bpm_reel": 137.8,
                        "coupes": "sur les kicks 808 réels (rythme/frappes.json), écart <= 1/2 image ; poussées du kick de coupe au kick suivant",
                        "kicks_808_s": K,
                        "sous_la_voix": "morceau passe-bas 420 Hz -7 dB de 0 à %.2f s, plein ensuite" % DROP},
            "phrase": {"source": "lot2/sources/%s 221,84-226,90 s (YouTube 4CPac_uArQ0, Assemblée 16/06/2026)" % AN, "texte": G["texte"], "timeline_s": [0.14, 5.20]},
            "textes": [{"t0": round(c["words"][0][1], 2), "t1": round(c["t1"], 2), "ligne": " ".join(w[0] for w in c["words"])} for c in CARDS],
            "halo": "#%02X%02X%02X (or des ornements de l'hémicycle)" % GLOW,
            "video": vid,
            "audio": [{"id": "mix", "clip": "G3k-mix.wav", "folder": "G3", "path": OUT + "G3k-mix.wav", "rec": 0, "track": 1,
                       "note": "mix final -14 LUFS : voix 0,10-5,28 s, TENDU étouffé dessous puis plein au palier %.2f s, fondu de fin" % DROP}]}
    json.dump(plan, open(D + "plan-G3.json", "w"), indent=1, ensure_ascii=False)

# ---------------- aperçu ffmpeg 540×960 ----------------
def preview():
    out = ROOT + "/preview/apercu-G3.mp4"; args = [FF, "-v", "error", "-y"]; fl = []
    for i, sh in enumerate(SHOTS):
        args += ["-i", OUT + sh["clip"]]; sp = sh["speed_res"] / 100
        fl.append("[%d:v]setpts=(PTS-STARTPTS)/%.6f,fps=30,trim=end_frame=%d,setpts=PTS-STARTPTS,scale=540:960,setsar=1[v%d]" % (i, sp, sh["dur"], i))
    args += ["-i", OUT + "G3k-mix.wav"]
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
    write_plan()
    if "apercu" in sys.argv: print(preview())
    print("total", sum(s["dur"] for s in SHOTS) / 30, "s ;", len(SHOTS), "plans ; plus court", min(s["dur"] for s in SHOTS) / 30, "s")
    print([" ".join(w[0] for w in c["words"]) for c in CARDS])
