# G5 — Glow COULEUR, Bally Bagayoko (lot 4), son « Ta fête » (Stromae). Modèle : lot3/_claude/gen/G4/genG4.py.
# Aperçu hors Resolve : plans ProRes 9:16 recadrés (visage suivi), étalonnage glow couleur (bloom teinté ambre), texte cuit
# (Avenir Next Bold Italic, TOUT en blanc, halo ambre #FFB97F pris dans la façade de l'hôtel de ville au soleil + contour sombre,
# jamais de rouge). Aucune image N&B.
# Phrase : Le Média, entretien place de l'hôtel de ville de Saint-Denis (18/03/2026, YouTube GvFhlaCWWGI) 925,40-930,12 s :
# « Nous sommes une ville antifasciste, antiraciste, anti-impérialiste. »
# Ralentis PAS précalculés : clip à vitesse normale, speed_pct + retime optical flow dans plan-G5.json.
# Son : extrait 20,96-35,86 s du morceau ; montée (beat sans voix, étouffé puis filtre qui s'ouvre) sous la phrase, drop sur
# l'entrée du refrain (26,26 s, pic « les plus revus » YouTube 26-28 s).
# Usage : python genG5.py [plans] [audio] [apercu] [only=ID,ID]
import sys, os, json, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont
HK = "/Users/luca.grousset/Movies/highkey-gauchiste"; L2 = HK + "/lot2"; L4 = HK + "/lot4"
sys.path.insert(0, HK + "/_claude/outils")
import framing
from framing import plan_views
from fx import crop_view, vignette, grain, gblur
from words import tokens, clean
sys.path.insert(0, "/Users/luca.grousset/Movies/highkey-gauchiste/lot4/_claude/gen/G5")
from micflou import hide_mic          # logo « Le Média » de la bonnette du micro flouté (pas de logo à l'image)
FF = "/opt/homebrew/bin/ffmpeg"
D = L4 + "/_claude/gen/G5/"; OUT = D + "out/"; os.makedirs(OUT, exist_ok=True)
framing.ROOT = L2; framing.CACHE = D + "cache"
W, H, TFPS = 1080, 1920, 30
# ---------------- sources (lot2/sources, déjà téléchargées, plans jamais utilisés par A5 ni C5) ----------------
LA = "A5b-bagayoko-lemedia-a.mp4"     # GvFhlaCWWGI 250-285 s (Le Média, 18/03/2026), 25 i/s
LB = "A5b-bagayoko-lemedia-b.mp4"     # GvFhlaCWWGI 925-950 s, 25 i/s (plan moyen 1,36-18,96 s)
MA = "A5b-bagayoko-meeting-a.mp4"     # 1dkY_JVFx9I (meeting de Saint-Denis 07/06/2026, chaîne JLM), 30 i/s
SFPS = {LA: 25, LB: 25, MA: 30}
YT = {LA: ("GvFhlaCWWGI", 250.0), LB: ("GvFhlaCWWGI", 925.0), MA: ("1dkY_JVFx9I", 0.0)}
B_LM = (0, 0, 1920, 1080)             # Le Média : pas de logo incrusté
B_MA = (0, 0, 1480, 1080)             # meeting : logo de la campagne en haut à droite (x>1500) exclu
# ---------------- halo : couleur prise dans la vidéo ----------------
GLOW = (255, 185, 127)                # #FFB97F : façade de l'hôtel de ville au soleil (moyenne #977A64-#A1876E, teinte 26-30°), saturation 0,5
WHITE = (255, 255, 255)
GTINT = np.array([255, 214, 170][::-1], np.float32) / 255     # bloom ambre doux (BGR)

# ---------------- temps ----------------
FR = json.load(open(D + "rythme/frappes.json")); MOFF = FR["MOFF"]   # temps morceau = timeline + MOFF
K = FR["kicks_timeline"]
DROP = 5.300                                   # entrée du refrain de Ta fête (26,263 s du morceau) = kick
assert min(abs(k - DROP) for k in K) < 0.002 and abs(MOFF + DROP - 26.263) < 0.002
END = 14.90                                    # glow 15 s max
V = YT[LB][1] + 0.15                           # timeline = temps YouTube - V  (« Nous » 925,40 -> 0,25 s)
VOICE = (925.37, 930.25)                       # voix posée (YouTube) : après « Saint-Denis » (fin 925,26), avant « et » ; mots 925,40-930,12
def f30(t): return int(round(t * TFPS))
def kick(t): k = min(K, key=lambda x: abs(x - t)); assert abs(k - t) < 0.06, (t, k); return k

# ---------------- textes (mot à mot, phrase réelle) ----------------
TX = json.load(open(L2 + "/_claude/tx/GvFhlaCWWGI.json"))
raw = [{"w": w["word"].strip(), "start": w["start"], "end": w["end"]} for s in TX["segments"] for w in s["words"]
       if 925.3 <= w["start"] <= 930.0]
T = tokens(raw)
assert " ".join(t["w"] for t in T) == "nous sommes une ville antifasciste, antiraciste, antiimpérialiste", " ".join(t["w"] for t in T)
SPELL = {"ANTIIMPÉRIALISTE": "ANTI-IMPÉRIALISTE"}   # orthographe (Whisper colle les deux i)
def up(t): u = clean(t["w"]).upper(); return SPELL.get(u, u)
GROUPS = [2, 2, 1, 1, 1]                       # Nous sommes | une ville | antifasciste | antiraciste | anti-impérialiste (zone sûre TikTok)
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
def grade(img, expo=1.0):
    global VIG
    x = np.clip((img * expo - 0.02) * 1.06, 0, 1); x = x * x * (3 - 2 * x) * 0.30 + x * 0.70      # contraste doux
    lum = x @ np.array([0.114, 0.587, 0.299], np.float32)
    x = lum[..., None] + (x - lum[..., None]) * 1.10                                              # couleurs un peu plus riches
    hi = np.clip((x - 0.55) / 0.45, 0, 1)
    x = x + gblur(hi, 18) * 0.45 * GTINT                                                          # bloom teinté ambre (SoftGlow)
    if VIG is None: VIG = vignette(np.ones((H, W, 3), np.float32), strength=0.40, power=2.2)
    return grain(np.clip(x, 0, 1) * VIG, 0.012, 1.4)

# ---------------- liste des plans ----------------
# A1 : début de la phrase (« Nous sommes une ville », dite pendant le plan large de la régie) sur un autre plan moyen du même
#      entretien (Le Média, autre moment, micro devant la bouche). A2/A3 : synchro exacte dès le plan moyen (1,36 s du fichier),
#      A3 = punch-in avant sur un kick. B : rafale sur les kicks réels du refrain, 2 temps par plan, poussée lente avant.
def S(i, a, b, src, t_in, sp, hint, bnd, vh, z0, z1, fx="", note="", expo=1.0):
    return dict(id=i, a=a, b=b, src=src, t_in=t_in, sp=sp, hint=hint, bnd=bnd, vh=vh, z0=z0, z1=z1, fx=fx, note=note, expo=expo)
C1, C2 = kick(1.496), kick(3.372)
KB = [kick(t) for t in (5.300, 6.243, 7.181, 8.116, 9.052, 9.991, 10.930, 11.867, 12.804, 13.687)]
SYNC = lambda a: a + V - YT[LB][1]             # temps fichier LB synchrone
SHOTS = [
    S("A1", 0.0, C1, LA, 20.00, 100, (960, 330), B_LM, 940, 1.00, 1.02, "texte",
      "début de la phrase (dit pendant le plan large de la régie) sur un autre plan moyen du même entretien, micro devant la bouche"),
    S("A2", C1, C2, LB, SYNC(C1), 100, (840, 330), B_LM, 940, 1.00, 1.02, "texte", "phrase en synchro exacte, plan moyen assis"),
    S("A3", C2, DROP, LB, SYNC(C2), 100, (840, 330), B_LM, 720, 1.00, 1.03, "texte", "punch-in avant sur le kick, synchro exacte"),
    S("B1", KB[0], KB[1], LA, 1.30, 100, (900, 330), B_LM, 760, 1.00, 1.03, "flash", "drop : flash, grand sourire au micro"),
    S("B2", KB[1], KB[2], MA, 9.00, 100, (900, 300), B_MA, 700, 1.00, 1.03, "", "meeting de Saint-Denis, au pupitre, regard relevé", 0.94),
    S("B3", KB[2], KB[3], LB, 9.00, 100, (840, 330), B_LM, 780, 1.00, 1.03, "", "Le Média, index levé"),
    S("B4", KB[3], KB[4], MA, 18.00, 50, (900, 300), B_MA, 680, 1.00, 1.03, "", "meeting, regard relevé vers la foule (ralenti)", 0.94),
    S("B5", KB[4], KB[5], LA, 16.00, 100, (960, 330), B_LM, 760, 1.00, 1.03, "", "Le Média, rire, main ouverte"),
    S("B6", KB[5], KB[6], LB, 12.00, 100, (840, 330), B_LM, 780, 1.00, 1.03, "", "Le Média, main levée"),
    S("B7", KB[6], KB[7], MA, 0.20, 50, (900, 300), B_MA, 660, 1.00, 1.03, "", "meeting, face caméra (ralenti)", 0.94),
    S("B8", KB[7], KB[8], LA, 21.30, 100, (960, 330), B_LM, 760, 1.00, 1.03, "", "Le Média, mains ouvertes"),
    S("B9", KB[8], KB[9], LB, 15.00, 100, (840, 330), B_LM, 780, 1.00, 1.03, "", "Le Média, geste de la main"),
    S("B10", KB[9], END, LA, 2.90, 100, (900, 330), B_LM, 740, 1.00, 1.04, "fin", "Le Média, sourire, fondu au noir 0,6 s"),
]
for sh in SHOTS:
    sh["rec"] = f30(sh["a"]); sh["dur"] = f30(sh["b"]) - sh["rec"]
    sh["clip"] = "G5_%s.mov" % sh["id"]
    sh["speed_res"] = float(sh["sp"])
    assert sh["sp"] == 100 or SFPS[sh["src"]] == 30          # ralentis seulement sur sources 30 i/s (pas d'images dupliquées)
def ease_out(u): u = min(max(u, 0.0), 1.0); return 1 - (1 - u) ** 3
def zoom_at(sh, t):
    u = (t - sh["a"]) / (sh["b"] - sh["a"])
    u = min(max(u, 0), 1) if sh["fx"] == "texte" else ease_out(u)
    return sh["z0"] + (sh["z1"] - sh["z0"]) * u

# ---------------- rendu d'un plan ----------------
def read_frames(src, t, n):
    p = subprocess.Popen([FF, "-v", "error", "-ss", "%.4f" % t, "-i", L2 + "/sources/" + src, "-frames:v", str(n),
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
                           zoom=lambda k: zoom_at(sh, tl_t(k)), top=0.16)
    frames = read_frames(sh["src"], s0 / sf, int(n * ratio) + 2)
    w = writer(OUT + sh["clip"], TFPS)
    for k in range(n):
        fr = frames[min(int(k * ratio + 1e-6), len(frames) - 1)]
        if sh["src"] in (LA, LB): fr, _ = hide_mic(fr)
        cx, cy, vh = views[k]; vw = vh * 9 / 16
        img = grade(crop_view(fr.astype(np.float32) / 255, cx, cy, vw, W, H), sh["expo"])
        t = tl_t(k)
        if sh["fx"] == "texte": img = draw_text(img, t)
        if sh["id"] in ("A2", "A3"):                                                # flash doux sur les coupes de la phrase
            fl = max(0.0, 0.30 * (1 - (t - sh["a"]) / 0.10)); img = img + (1 - img) * fl
        if sh["fx"] == "flash":                                                    # flash sur le drop (4 images timeline)
            fl = max(0.0, 0.75 * (1 - (t - sh["a"]) / 0.13))
            img = img + (1 - img) * fl * np.array([0.92, 0.96, 1.0], np.float32)
        if sh["fx"] == "fin": img = img * min(max((END - t) / 0.6, 0.0), 1.0)
        w.stdin.write((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8).tobytes())
    w.stdin.close(); w.wait()
    return ("visage" if ok else "SANS VISAGE") + ("" if len(frames) >= int(n * ratio) else " court:%d/%d" % (len(frames), n))

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
SON = L4 + "/sons/G5-stromae-ta-fete_complet.wav"
RISE = 1.6                                      # montée : le filtre s'ouvre sur les 1,6 s avant le drop
def build_audio():
    from scipy.signal import butter, sosfilt
    n = int(END * SR); mix = np.zeros((n, 2), np.float32)
    v = fade(load(L2 + "/sources/" + LB, VOICE[0] - YT[LB][1], VOICE[1] - VOICE[0]), 0.02, 0.15)
    lv, _ = lufs(v); v *= db(-15 - lv)
    m = load(SON, MOFF, END)
    lm, _ = lufs(m[int(DROP * SR):]); m *= db(-14 - lm)
    t = np.arange(len(m)) / SR
    lo = sosfilt(butter(4, 420, "low", fs=SR, output="sos"), m, axis=0).astype(np.float32)    # beat étouffé sous la voix
    md = sosfilt(butter(4, 2200, "low", fs=SR, output="sos"), m, axis=0).astype(np.float32)   # puis le filtre s'ouvre (montée)
    u = np.clip((t - (DROP - RISE)) / RISE, 0, 1)[:, None].astype(np.float32)
    pre = (lo * (1 - u) + md * u) * db(-7 + 3 * u)
    a = np.interp(t, [0, DROP - 0.03, DROP], [1, 1, 0])[:, None].astype(np.float32)
    mus = pre * a + m * (1 - a)                                                                # plein sur le drop
    mus *= (np.clip((END - t) / 1.2, 0, 1) ** 1.5)[:, None].astype(np.float32)
    mus = fade(mus, 0.25, 0)
    mix[:len(mus)] += mus; i0 = int(round((VOICE[0] - V) * SR)); mix[i0:i0 + len(v)] += v[:n - i0]
    tmp = OUT + "_tmp_mix.wav"; sf_write(tmp, mix); g = 0.0; li, _ = lufs(mix)
    for _ in range(4):
        g += -14.0 - li
        subprocess.run([FF, "-v", "error", "-y", "-i", tmp, "-af", "volume=%.2fdB,alimiter=limit=0.80:attack=3:release=60:level=false,aresample=192000,alimiter=limit=0.82:attack=1:release=40:level=false,aresample=48000" % g,
                        "-c:a", "pcm_s24le", OUT + "G5-mix.wav"], check=True)
        li, tp = lufs(load(OUT + "G5-mix.wav"))
        if abs(li + 14) < 0.3 and tp < -1.0: break
    os.remove(tmp)
    return "mix %.1f LUFS, true peak %.1f dBTP" % (li, tp)

# ---------------- son.json + plan-G5.json ----------------
def write_son():
    son = {"titre": "Ta fête", "artiste": "Stromae", "url": "https://youtu.be/ublchJYzhao", "chaine": "Stromae (officielle, vérifiée)",
           "fichier": "lot4/sons/G5-stromae-ta-fete_complet.wav",
           "extrait_morceau_s": [round(MOFF, 3), round(MOFF + END, 3)], "bpm": 128.0,
           "drop": {"morceau_s": round(MOFF + DROP, 3), "timeline_s": DROP,
                    "note": "entrée du refrain (voix + charleston), pic « les plus revus » YouTube 26,1-28,1 s ; avant : 8 mesures de beat sans voix"},
           "sous_la_phrase": "beat 20,96-26,26 s du morceau étouffé (passe-bas 420 Hz, -7 dB) puis le filtre s'ouvre (2,2 kHz, -4 dB) sur les 1,6 s avant le drop",
           "paroles_audibles": "refrain : « … ta mère veut te la faire aussi / Ta fête / Le juge voudrait te faire ta fête … » (≈ 26,3-35,9 s)",
           "frappes": "kicks réels (attaque 30-120 Hz), rythme/frappes.json",
           "kicks_timeline_s": [k for k in K if k <= END]}
    json.dump(son, open(D + "son.json", "w"), indent=1, ensure_ascii=False)
def write_plan():
    vid = []
    for sh in SHOTS:
        sp = sh["sp"]; used = sh["dur"] / TFPS * sp / 100; yid, y0 = YT[sh["src"]]
        it = {"id": sh["id"], "clip": sh["clip"], "folder": "G5", "path": OUT + sh["clip"], "s": 0, "e": sh["dur"], "clip_fps": TFPS,
              "rec": sh["rec"], "dur": sh["dur"], "track": 1, "note": sh["note"],
              "source": {"fichier": "lot2/sources/" + sh["src"], "fps": SFPS[sh["src"]], "in_s": round(sh["t_in"], 3), "out_s": round(sh["t_in"] + used, 3),
                         "youtube": "%s %.2f-%.2f s" % (yid, y0 + sh["t_in"], y0 + sh["t_in"] + used) if sh["src"] != MA else "%s (extrait lot2 A5b-meeting-a, voir derush-AG.json)" % yid},
              "effets": "recadrage 9:16 suivi visage (sans logo%s), glow couleur ambre%s" % (", logo du micro Le Média flouté" if sh["src"] in (LA, LB) else "",
                  {"flash": ", flash 0,13 s cuit", "texte": ", texte cuit", "fin": ", fondu au noir 0,6 s cuit"}.get(sh["fx"], ""))}
        it["frappe_s"] = round(sh["a"], 3); it["poussee"] = "x%.2f -> x%.2f, du kick %.3f s au kick %.3f s (temps timeline)" % (sh["z0"], sh["z1"], sh["a"], sh["b"])
        if sp != 100:
            it["speed_pct"] = round(sh["speed_res"], 4); it["retime"] = "optical_flow"
            it["ralenti"] = "%d %% : clip 30 i/s à vitesse normale, Resolve à %g %% (Optical Flow, Speed Warp better)" % (sp, sh["speed_res"])
        vid.append(it)
    plan = {"name": "G5 - Glow - Bagayoko", "fps": 30, "w": 1080, "h": 1920, "duree_s": END,
            "note": "Lot 4, glow COULEUR (aucune image N&B). Coupes sur les kicks réels (rythme/frappes.json). Plans ProRes 9:16 30 i/s prêts (recadrés, poussées, étalonnés, texte cuit sur A1-A3, flash cuit sur B1, fondu cuit sur B10). Ralentis : speed_pct + Optical Flow (sources 30 i/s seulement). Générateur : lot4/_claude/gen/G5/genG5.py, halo #%02X%02X%02X" % GLOW,
            "musique": {"fichier": "lot4/sons/G5-stromae-ta-fete_complet.wav", "debut_extrait_s": round(MOFF, 3), "entree_pleine_timeline_s": DROP, "bpm_reel": 128.0,
                        "kicks_timeline_s": [k for k in K if k <= END],
                        "sous_la_voix": "beat étouffé (passe-bas 420 Hz -7 dB) de 0 à %.2f s, filtre qui s'ouvre sur %.1f s, plein au drop %.2f s" % (DROP - RISE, RISE, DROP)},
            "phrase": {"source": "https://youtu.be/GvFhlaCWWGI 925,40-930,12 s (Le Média, entretien à Saint-Denis, 18/03/2026)",
                       "texte": "Nous sommes une ville antifasciste, antiraciste, anti-impérialiste.",
                       "timeline_s": [round(T[0]["start"] - V, 3), round(T[-1]["end"] - V, 3)]},
            "textes": [{"t0": round(c["words"][0][1], 2), "t1": round(c["t1"], 2), "ligne": " ".join(w[0] for w in c["words"])} for c in CARDS],
            "halo": "#%02X%02X%02X (façade de l'hôtel de ville de Saint-Denis au soleil)" % GLOW,
            "video": vid,
            "audio": [{"id": "mix", "clip": "G5-mix.wav", "folder": "G5", "path": OUT + "G5-mix.wav", "rec": 0, "track": 1,
                       "note": "mix final -14 LUFS : voix %.2f-%.2f s, Ta fête étouffé dessous puis montée et plein au drop %.2f s, fondu de fin" % (VOICE[0] - V, VOICE[1] - V, DROP)}]}
    json.dump(plan, open(D + "plan-G5.json", "w"), indent=1, ensure_ascii=False)

# ---------------- aperçu ffmpeg 540×960 ----------------
def preview():
    out = HK + "/preview/apercu-G5.mp4"; args = [FF, "-v", "error", "-y"]; fl = []
    for i, sh in enumerate(SHOTS):
        args += ["-i", OUT + sh["clip"]]; sp = sh["speed_res"] / 100
        fl.append("[%d:v]setpts=(PTS-STARTPTS)/%.6f,fps=30,trim=end_frame=%d,setpts=PTS-STARTPTS,scale=540:960,setsar=1[v%d]" % (i, sp, sh["dur"], i))
    args += ["-i", OUT + "G5-mix.wav"]
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
