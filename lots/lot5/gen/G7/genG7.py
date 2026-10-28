# G7 — Glow COULEUR, Sophia Chikirou (lot 5), son « Get Lucky » (Daft Punk ft. Pharrell Williams, Nile Rodgers).
# Modèle : lot4/_claude/gen/G5/genG5.py (même structure, mêmes outils). Aperçu hors Resolve.
# Plans ProRes 9:16 recadrés (visage suivi), étalonnage glow couleur (bloom rosé-violet), texte cuit (Avenir Next Bold Italic,
# TOUT en blanc, halo #FF80EE pris dans le velours prune de sa veste + contour sombre, jamais de rouge). Aucune image N&B.
# Phrase (v2, retour de Luca : « gagner en 2027 » pas pertinent) : réunion publique à Paris (14/10/2026, chaîne SOPHIA CHIKIROU,
# YouTube MZ7maKdeQTE) 1155,88-1160,48 s : « Nous voulons mettre fin au pillage organisé de notre pays. »
# (A3 avait pris « Nous appelons au débordement populaire. » à 1330 s : autre phrase.)
# Règle de Luca (retour K3) : sous sa voix, seulement le plan synchro (même source, même moment) ou un plan où elle ne parle pas
# (salle) ; après le drop, plans variés : gros plans, plans moyens, plans larges de la scène depuis la salle, salle.
# Sources : lot5/sources/G7-chikirou-paris-budget.mp4 (1145-1250 s, téléchargé pour la phrase) + lot2/sources/A3-chikirou-paris-b
# (aucun plan utilisé par A3), via les liens de sources/ ; aucun plan d'A3 repris.
# Ralentis PAS précalculés : clip à vitesse normale, speed_pct + retime optical flow dans plan-G7.json.
# Son : extrait 135,33-150,23 s du morceau : le break sans basse ni kick (« We're up all night to get lucky ») étouffé sous la
# phrase, le filtre s'ouvre sur 1,6 s, drop sur le retour du kick (140,33 s), pic « les plus revus » YouTube 139,4-146,9 s.
# Usage : python genG7.py [plans] [audio] [apercu] [only=ID,ID]
import sys, os, json, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont
HK = "/Users/luca.grousset/Movies/highkey-gauchiste"; L2 = HK + "/lot2"; L5 = HK + "/lot5"
sys.path.insert(0, HK + "/_claude/outils")
import framing
from framing import plan_views
from fx import crop_view, vignette, grain, gblur
from words import tokens, clean
FF = "/opt/homebrew/bin/ffmpeg"
D = L5 + "/_claude/gen/G7/"; OUT = D + "out/"; os.makedirs(OUT, exist_ok=True)
framing.ROOT = D[:-1]; framing.CACHE = D + "cache"     # D/sources/ = liens vers lot2/sources et lot5/sources
W, H, TFPS = 1080, 1920, 30
# ---------------- sources (lot2/sources, déjà téléchargées ; -b jamais utilisé par A3, -a seulement à d'autres moments) ----------------
SA = "G7-chikirou-paris-budget.mp4"   # MZ7maKdeQTE 1145-1250 s, 29,97 i/s (salle 0-3,2 ; large scène 3,2-7,2 ; plan moyen 7,2-33,4 ;
                                      # large 33,4-37,7 ; salle 37,7-42,4 ; large 42,4-47 ; plan moyen 47-73,2 et 76,1-86,3 ; salle 86,3-92,2)
SB = "A3-chikirou-paris-b.mp4"        # MZ7maKdeQTE 690-770 s, 29,97 i/s (gros plan 0-37,97 et 45,45-73,47 ; salle 37,97-45,45 ; large 73,47-80)
SFPS = {SA: 30000 / 1001, SB: 30000 / 1001}
YT = {SA: ("MZ7maKdeQTE", 1145.0), SB: ("MZ7maKdeQTE", 690.0)}
REAL = {SA: "lot5/sources/" + SA, SB: "lot2/sources/" + SB}
B_PM = (380, 0, 1580, 880)            # plan moyen : logo MELENCHON2027.fr (x≥1590, y≤170), pupitre PARIS (y≥890), têtes du public (x<380, x>1760) exclus
B_SA = (0, 0, 1580, 1080)             # salle : logo en haut à droite exclu
# ---------------- halo : couleur prise dans la vidéo ----------------
GLOW = (255, 128, 238)                # #FF80EE : velours prune de sa veste (mesuré #310B2A-#2D0D2D, teinte 300-311°), saturation 0,5, éclairci
WHITE = (255, 255, 255)
GTINT = np.array([255, 200, 240][::-1], np.float32) / 255     # bloom rosé-violet doux (BGR)

# ---------------- temps ----------------
FR = json.load(open(D + "rythme/frappes.json")); MOFF = FR["MOFF"]   # temps morceau = timeline + MOFF
K = FR["kicks_timeline"]; SN = FR["snares_timeline"]
DROP = 5.000                                   # retour du kick après le break (140,332 s du morceau)
assert min(abs(k - DROP) for k in K) < 0.002 and abs(MOFF + DROP - 140.332) < 0.002
END = 14.90                                    # glow 15 s max
V = YT[SA][1] + 10.63                          # timeline = temps YouTube - V  (« nous » 1155,88 -> 0,25 s)
VOICE = (1155.87, 1160.62)                     # voix posée (YouTube) : après « dire » (fin 1155,86), « pays » finit à 1160,58 (mesuré), « Et » à 1160,84
def f30(t): return int(round(t * TFPS))
def kick(t): k = min(K, key=lambda x: abs(x - t)); assert abs(k - t) < 0.06, (t, k); return k
def clap(t): k = min(SN, key=lambda x: abs(x - t)); assert abs(k - t) < 0.06, (t, k); return k   # frappes du break (pas de kick)

# ---------------- textes (mot à mot, phrase réelle) ----------------
TX = json.load(open(D + "tx/budget.json"))   # transcription mot à mot du fichier SA (temps fichier ; = lot2/_claude/tx/MZ7maKdeQTE.json - 1145 s)
raw = [{"w": w["word"].strip(), "start": w["start"] + YT[SA][1], "end": w["end"] + YT[SA][1]} for s in TX["segments"] for w in s["words"]
       if 10.8 <= w["start"] <= 15.3]
T = tokens(raw)
assert " ".join(t["w"] for t in T) == "nous voulons mettre fin au pillage organisé de notre pays.", " ".join(t["w"] for t in T)
def up(t): return clean(t["w"]).upper()
GROUPS = [2, 2, 2, 1, 3]                       # NOUS VOULONS | METTRE FIN | AU PILLAGE | ORGANISÉ | DE NOTRE PAYS
assert sum(GROUPS) == len(T)
CARDS, i = [], 0
for g in GROUPS:
    CARDS.append({"words": [(up(T[j]), T[j]["start"] - V) for j in range(i, i + g)]}); i += g
for k, c in enumerate(CARDS): c["t1"] = CARDS[k + 1]["words"][0][1] if k + 1 < len(CARDS) else DROP
TEXT_Y = 0.60
FONT = ("/System/Library/Fonts/Avenir Next.ttc", 1)          # Avenir Next Bold Italic (test 4)
_fc = {}
def font(px):
    px = int(round(px))
    if px not in _fc: _fc[px] = ImageFont.truetype(FONT[0], px, index=FONT[1])
    return _fc[px]
def card_size(c):
    f = font(100); txt = " ".join(w[0] for w in c["words"])
    return min(118, 0.60 * W / (f.getlength(txt) / 100))         # bloc ≤ 60 % de la largeur : zone sûre TikTok (x 0,17-0,83)
def draw_text(img, t):
    act = [c for c in CARDS if c["words"][0][1] - 1e-3 <= t < c["t1"]]
    if not act: return img
    lay = Image.new("L", (W, H), 0); dl = ImageDraw.Draw(lay)
    for c in act:
        px = card_size(c); f = font(px); sp = f.getlength(" ")
        tot = sum(f.getlength(w[0]) for w in c["words"]) + sp * (len(c["words"]) - 1)
        x = W / 2 - tot / 2; y = TEXT_Y * H
        for word, tw in c["words"]:
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
def grade(img, expo=1.35):
    global VIG
    x = np.clip(img * expo, 0, 1) ** 0.80                                                       # scène sombre : on remonte (expo + gamma)
    x = x * x * (3 - 2 * x) * 0.25 + x * 0.75                                                     # contraste doux
    lum = x @ np.array([0.114, 0.587, 0.299], np.float32)
    x = lum[..., None] + (x - lum[..., None]) * 1.15                                              # couleurs un peu plus riches
    hi = np.clip((x - 0.45) / 0.55, 0, 1)
    x = x + gblur(hi, 20) * 0.50 * GTINT + gblur(hi, 60) * 0.18 * GTINT                           # bloom teinté rosé-violet (SoftGlow)
    x = x + (1 - x) * np.array([0.10, 0.04, 0.10], np.float32) * 0.45                             # noirs levés rosé-violet
    if VIG is None: VIG = vignette(np.ones((H, W, 3), np.float32), strength=0.30, power=2.2)
    return grain(np.clip(x, 0, 1) * VIG, 0.012, 1.4)

# ---------------- liste des plans ----------------
# Avant le drop (voix) : A1, A2, A4 = synchro exacte (plan moyen au pupitre, punch-in avant à chaque clap) ; A3 = la salle (elle ne
# parle pas à l'image). Après le drop (musique seule) : rafale sur les kicks réels, 2 temps par plan, angles variés.
def S(i, a, b, src, t_in, sp, hint, bnd, vh, z0, z1, fx="", note="", expo=1.35, fixed=None, kind="gros plan"):
    return dict(id=i, a=a, b=b, src=src, t_in=t_in, sp=sp, hint=hint, bnd=bnd, vh=vh, z0=z0, z1=z1, fx=fx, note=note, expo=expo, fixed=fixed, kind=kind)
C1, C2, C3 = clap(1.39), clap(2.664), clap(3.956)
KB = [kick(t) for t in (5.000, 6.035, 7.061, 8.107, 9.128, 10.165, 11.196, 12.238, 13.267, 14.308)]
SYNC = lambda a: a + V - YT[SA][1]             # temps fichier SA synchrone
HB = (980, 330); HM = (950, 300)
WIDE = (930, 560); CROWD = (800, 600)
SHOTS = [
    S("A1", 0.0, C1, SA, SYNC(0.0), 100, HM, B_PM, 880, 1.00, 1.03, "texte", "synchro exacte, plan moyen au pupitre", kind="synchro"),
    S("A2", C1, C2, SA, SYNC(C1), 100, HM, B_PM, 700, 1.00, 1.03, "texte", "synchro exacte, punch-in avant sur le clap", kind="synchro"),
    S("A3", C2, C3, SB, 41.00, 50, CROWD, B_SA, 1000, 1.00, 1.04, "texte", "la salle comble (ralenti) : elle ne parle pas à l'image", 1.15, CROWD, kind="salle"),
    S("A4", C3, DROP, SA, SYNC(C3), 100, HM, B_PM, 560, 1.00, 1.03, "texte", "synchro exacte, plus serré", kind="synchro"),
    S("B1", KB[0], KB[1], SB, 3.00, 100, HB, B_PM, 760, 1.00, 1.03, "flash", "drop : flash, gros plan, applaudit la salle"),
    S("B2", KB[1], KB[2], SA, 4.20, 50, WIDE, B_SA, 1080, 1.00, 1.05, "", "plan large de la scène depuis la salle, public de dos (ralenti)", 1.15, WIDE, kind="large"),
    S("B3", KB[2], KB[3], SA, 29.40, 100, HM, B_PM, 880, 1.00, 1.03, "", "plan moyen, buste, face à la salle", kind="plan moyen"),
    S("B4", KB[3], KB[4], SB, 52.00, 100, HB, B_PM, 700, 1.00, 1.03, "", "gros plan, mains levées"),
    S("B5", KB[4], KB[5], SB, 43.50, 50, (700, 600), B_SA, 1000, 1.00, 1.04, "", "la salle comble, autre moment que A3 (ralenti)", 1.15, (700, 600), kind="salle"),
    S("B6", KB[5], KB[6], SB, 65.00, 100, HB, B_PM, 700, 1.00, 1.03, "", "gros plan, sourire, mains ouvertes"),
    S("B7", KB[6], KB[7], SA, 80.40, 100, HM, B_PM, 880, 1.00, 1.03, "", "plan moyen, désigne la salle", kind="plan moyen"),
    S("B8", KB[7], KB[8], SB, 75.50, 50, WIDE, B_SA, 1080, 1.00, 1.05, "", "plan large de la scène éclairée, public de dos (ralenti)", 1.15, WIDE, kind="large"),
    S("B9", KB[8], KB[9], SB, 13.00, 100, HB, B_PM, 680, 1.00, 1.03, "", "gros plan, visage face caméra"),
    S("B10", KB[9], END, SB, 70.80, 50, HB, B_PM, 680, 1.00, 1.04, "fin", "gros plan, mains jointes (ralenti), fondu au noir 0,6 s"),
]
for sh in SHOTS:
    sh["rec"] = f30(sh["a"]); sh["dur"] = f30(sh["b"]) - sh["rec"]
    sh["clip"] = "G7_%s.mov" % sh["id"]
    sh["speed_res"] = float(sh["sp"])
def ease_out(u): u = min(max(u, 0.0), 1.0); return 1 - (1 - u) ** 3
def zoom_at(sh, t):
    u = (t - sh["a"]) / (sh["b"] - sh["a"])
    u = min(max(u, 0), 1) if sh["fx"] == "texte" else ease_out(u)
    return sh["z0"] + (sh["z1"] - sh["z0"]) * u

# ---------------- rendu d'un plan ----------------
def read_frames(src, t, n):
    p = subprocess.Popen([FF, "-v", "error", "-ss", "%.4f" % t, "-i", D + "sources/" + src, "-frames:v", str(n),
                          "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE)
    sz = 1920 * 1080 * 3; out = []
    for _ in range(n):
        b = p.stdout.read(sz)
        if len(b) < sz: break
        out.append(np.frombuffer(b, np.uint8).reshape(1080, 1920, 3))
    p.stdout.close(); p.wait()
    return out
def writer(path, fps):
    return subprocess.Popen([FF, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", "%dx%d" % (W, H), "-r", str(fps), "-i", "-",
                             "-c:v", "prores_ks", "-profile:v", "3", "-pix_fmt", "yuv422p10le", "-vendor", "apl0", path], stdin=subprocess.PIPE)
def render(sh):
    n = sh["dur"]; sf = SFPS[sh["src"]]; s0 = int(round(sh["t_in"] * sf)); slow = sh["sp"] != 100
    ratio = sf / TFPS                                                      # image clip k -> image source int(k·ratio)
    tl_t = (lambda k: sh["a"] + k / (TFPS * sh["sp"] / 100)) if slow else (lambda k: sh["a"] + k / TFPS)
    views, ok = plan_views(sh["src"], s0, n, sf, speed=ratio, hint=sh["hint"], bounds=sh["bnd"], vh=sh["vh"],
                           zoom=lambda k: zoom_at(sh, tl_t(k)), top=0.16, fixed=sh["fixed"])
    frames = read_frames(sh["src"], s0 / sf, int(n * ratio) + 2)
    w = writer(OUT + sh["clip"], TFPS)
    for k in range(n):
        fr = frames[min(int(k * ratio + 1e-6), len(frames) - 1)]
        cx, cy, vh = views[k]; vw = vh * 9 / 16
        img = grade(crop_view(fr.astype(np.float32) / 255, cx, cy, vw, W, H), sh["expo"])
        t = tl_t(k)
        if sh["fx"] == "texte": img = draw_text(img, t)
        if sh["fx"] == "texte" and sh["id"] != "A1":                                                # flash doux sur les coupes de la phrase
            fl = max(0.0, 0.30 * (1 - (t - sh["a"]) / 0.10)); img = img + (1 - img) * fl
        if sh["fx"] == "flash":                                                    # flash sur le drop (4 images timeline)
            fl = max(0.0, 0.75 * (1 - (t - sh["a"]) / 0.13))
            img = img + (1 - img) * fl * np.array([0.98, 0.92, 1.0], np.float32)
        if sh["fx"] == "fin": img = img * min(max((END - t) / 0.6, 0.0), 1.0)
        w.stdin.write((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8).tobytes())
    w.stdin.close(); w.wait()
    return ("visage" if ok else ("fixe (salle)" if sh["fixed"] else "SANS VISAGE")) + ("" if len(frames) >= int(n * ratio) else " court:%d/%d" % (len(frames), n))

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
SON = L5 + "/sons/G7-daftpunk-get-lucky_complet.wav"
RISE = 1.6                                      # montée : le filtre s'ouvre sur les 1,6 s avant le drop
def build_audio():
    from scipy.signal import butter, sosfilt
    n = int(END * SR); mix = np.zeros((n, 2), np.float32)
    v = fade(load(D + "sources/" + SA, VOICE[0] - YT[SA][1], VOICE[1] - VOICE[0]), 0.01, 0.04)
    lv, _ = lufs(v); v *= db(-15 - lv)
    m = load(SON, MOFF, END)
    lm, _ = lufs(m[int(DROP * SR):]); m *= db(-14 - lm)
    t = np.arange(len(m)) / SR
    lo = sosfilt(butter(4, 420, "low", fs=SR, output="sos"), m, axis=0).astype(np.float32)    # break étouffé sous la voix
    md = sosfilt(butter(4, 2200, "low", fs=SR, output="sos"), m, axis=0).astype(np.float32)   # puis le filtre s'ouvre (montée)
    u = np.clip((t - (DROP - RISE)) / RISE, 0, 1)[:, None].astype(np.float32)
    pre = (lo * (1 - u) + md * u) * db(-6 + 3 * u)
    a = np.interp(t, [0, DROP - 0.03, DROP], [1, 1, 0])[:, None].astype(np.float32)
    mus = pre * a + m * (1 - a)                                                                # plein sur le drop
    mus *= (np.clip((END - t) / 1.2, 0, 1) ** 1.5)[:, None].astype(np.float32)
    mus = fade(mus, 0.25, 0)
    mix[:len(mus)] += mus; i0 = int(round((VOICE[0] - V) * SR)); mix[i0:i0 + len(v)] += v[:n - i0]
    tmp = OUT + "_tmp_mix.wav"; sf_write(tmp, mix); g = 0.0; li, _ = lufs(mix)
    for _ in range(4):
        g += -14.0 - li
        subprocess.run([FF, "-v", "error", "-y", "-i", tmp, "-af", "volume=%.2fdB,alimiter=limit=0.74:attack=3:release=60:level=false,aresample=192000,alimiter=limit=0.76:attack=1:release=40:level=false,aresample=48000" % g,
                        "-c:a", "pcm_s24le", OUT + "G7-mix.wav"], check=True)
        li, tp = lufs(load(OUT + "G7-mix.wav"))
        if abs(li + 14) < 0.3 and tp < -2.0: break
    os.remove(tmp)
    return "mix %.1f LUFS, true peak %.1f dBTP" % (li, tp)

# ---------------- son.json + plan-G7.json ----------------
LYR = "break : « We're up all night to get lucky » (136,7-140,6 s, étouffé sous la phrase puis révélé par la montée) ; après le drop : « We're up all night to get lucky » en boucle sur le kick (140,3-150,2 s, vérifié à la transcription)"
def write_son():
    son = {"titre": "Get Lucky", "artiste": "Daft Punk ft. Pharrell Williams, Nile Rodgers", "url": "https://www.youtube.com/watch?v=5NV6Rdv1a3I",
           "chaine": "Daft Punk (officielle, vérifiée, 7,2 M abonnés) — « Official Audio »",
           "fichier": "lot5/sons/G7-daftpunk-get-lucky_complet.wav",
           "extrait_morceau_s": [round(MOFF, 3), round(MOFF + END, 3)], "bpm": 116.0,
           "drop": {"morceau_s": round(MOFF + DROP, 3), "timeline_s": DROP,
                    "note": "retour du kick et de la basse après le break (124,4-140,3 s sans kick), pic « les plus revus » YouTube 139,4-146,9 s (max 141,9-144,4 s)"},
           "sous_la_phrase": "break 135,33-140,33 s étouffé (passe-bas 420 Hz, -6 dB) puis le filtre s'ouvre (2,2 kHz, -3 dB) sur les 1,6 s avant le drop",
           "paroles_audibles": LYR,
           "frappes": "kicks réels (attaque 30-120 Hz) après le drop ; claps réels du break (1,5-5 kHz) avant ; rythme/frappes.json",
           "coupes_timeline_s": [round(s["a"], 3) for s in SHOTS[1:]],
           "kicks_timeline_s": [k for k in K if k <= END]}
    json.dump(son, open(D + "son.json", "w"), indent=1, ensure_ascii=False)
def write_plan():
    vid = []
    for sh in SHOTS:
        sp = sh["sp"]; used = sh["dur"] / TFPS * sp / 100; yid, y0 = YT[sh["src"]]
        it = {"id": sh["id"], "plan": sh["kind"], "clip": sh["clip"], "folder": "G7", "path": OUT + sh["clip"], "s": 0, "e": sh["dur"], "clip_fps": TFPS,
              "rec": sh["rec"], "dur": sh["dur"], "track": 1, "note": sh["note"],
              "source": {"fichier": REAL[sh["src"]], "fps": round(SFPS[sh["src"]], 3), "in_s": round(sh["t_in"], 3), "out_s": round(sh["t_in"] + used, 3),
                         "youtube": "%s %.2f-%.2f s" % (yid, y0 + sh["t_in"], y0 + sh["t_in"] + used)},
              "effets": "recadrage 9:16 %s (sans logo ni pupitre), glow couleur rosé-violet%s" % ("fixe" if sh["fixed"] else "suivi visage",
                  {"flash": ", flash 0,13 s cuit", "texte": ", texte cuit", "fin": ", fondu au noir 0,6 s cuit"}.get(sh["fx"], ""))}
        it["frappe_s"] = round(sh["a"], 3); it["poussee"] = "x%.2f -> x%.2f, de la frappe %.3f s à la frappe %.3f s (temps timeline)" % (sh["z0"], sh["z1"], sh["a"], sh["b"])
        if sp != 100:
            it["speed_pct"] = round(sh["speed_res"], 4); it["retime"] = "optical_flow"
            it["ralenti"] = "%d %% : clip 30 i/s à vitesse normale, Resolve à %g %% (Optical Flow, Speed Warp better)" % (sp, sh["speed_res"])
        vid.append(it)
    plan = {"name": "G7 - Glow - Chikirou", "fps": 30, "w": 1080, "h": 1920, "duree_s": END,
            "note": "Lot 5, glow COULEUR (aucune image N&B). Coupes sur les frappes réelles (claps du break avant le drop, kicks après ; rythme/frappes.json). Plans ProRes 9:16 30 i/s prêts (recadrés, poussées, étalonnés, texte cuit sur A1-A3, flash cuit sur B1, fondu cuit sur B10). Ralentis : speed_pct + Optical Flow. Générateur : lot5/_claude/gen/G7/genG7.py, halo #%02X%02X%02X" % GLOW,
            "musique": {"fichier": "lot5/sons/G7-daftpunk-get-lucky_complet.wav", "debut_extrait_s": round(MOFF, 3), "entree_pleine_timeline_s": DROP, "bpm_reel": 116.0,
                        "kicks_timeline_s": [k for k in K if k <= END],
                        "sous_la_voix": "break étouffé (passe-bas 420 Hz -6 dB) de 0 à %.2f s, filtre qui s'ouvre sur %.1f s, plein au drop %.2f s" % (DROP - RISE, RISE, DROP)},
            "phrase": {"source": "https://www.youtube.com/watch?v=MZ7maKdeQTE 1155,88-1160,48 s (réunion publique à Paris, 14/10/2026, chaîne SOPHIA CHIKIROU)",
                       "texte": "Nous voulons mettre fin au pillage organisé de notre pays.",
                       "regle_voix": "sous la voix : plan synchro (A1, A2, A4) ou la salle (A3), jamais un autre plan où elle parle",
                       "timeline_s": [round(T[0]["start"] - V, 3), round(T[-1]["end"] - V, 3)]},
            "textes": [{"t0": round(c["words"][0][1], 2), "t1": round(c["t1"], 2), "ligne": " ".join(w[0] for w in c["words"])} for c in CARDS],
            "halo": "#%02X%02X%02X (velours prune de sa veste)" % GLOW,
            "video": vid,
            "audio": [{"id": "mix", "clip": "G7-mix.wav", "folder": "G7", "path": OUT + "G7-mix.wav", "rec": 0, "track": 1,
                       "note": "mix final -14 LUFS : voix %.2f-%.2f s, break de Get Lucky étouffé dessous puis montée et plein au drop %.2f s, fondu de fin" % (VOICE[0] - V, VOICE[1] - V, DROP)}]}
    json.dump(plan, open(D + "plan-G7.json", "w"), indent=1, ensure_ascii=False)

# ---------------- aperçu ffmpeg 540×960 ----------------
def preview():
    out = HK + "/preview/apercu-G7.mp4"; args = [FF, "-v", "error", "-y"]; fl = []
    for i, sh in enumerate(SHOTS):
        args += ["-i", OUT + sh["clip"]]; sp = sh["speed_res"] / 100
        fl.append("[%d:v]setpts=(PTS-STARTPTS)/%.6f,fps=30,trim=end_frame=%d,setpts=PTS-STARTPTS,scale=540:960,setsar=1[v%d]" % (i, sp, sh["dur"], i))
    args += ["-i", OUT + "G7-mix.wav"]
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
