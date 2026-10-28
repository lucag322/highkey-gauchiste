# G6 — Glow COULEUR, Clémence Guetté (lot 4), son « Experience » (Ludovico Einaudi). Modèle : lot3/_claude/gen/G4/genG4.py.
# Aperçu hors Resolve : plans ProRes 9:16 30 i/s recadrés (visage suivi), étalonnage glow couleur (bloom rosé), texte cuit
# (Avenir Next Bold Italic, TOUT en blanc, halo saumon-rose pris dans le fond « lever de soleil » du plateau Télé Matin + contour
# sombre, jamais de rouge). Aucune image N&B.
# Phrase : franceinfo / Télé Matin « Les 4 vérités » 22/10/2026 (YouTube hl8dSp1e_o8, chaîne franceinfo) 401,94-406,37 s :
# « Honnêtement, ce gouvernement n'inspire que dégoût à la population française. Je pense qu'il devrait s'en rendre compte. »
# Ralentis PAS précalculés : clip à vitesse normale, speed_pct + retime optical flow dans plan-G6.json.
# Son : extrait 116,49-131,39 s du morceau ; montée cordes/piano sous la phrase, drop = arrivée du passage le plus connu (pic YouTube
# « les plus revus » 120-123 s, attaque de basse 121,49 s, la plus forte du passage) à 5,00 s.
# Sources 25 i/s (franceinfo 1080p, BFMTV 720p remis en 1920×1080, Meaux 1080p) -> plans 30 i/s (images répétées, fps=30).
# Usage : python genG6.py [plans] [audio] [apercu] [only=ID,ID]
import sys, os, json, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont
HK = "/Users/luca.grousset/Movies/highkey-gauchiste"; L4 = HK + "/lot4"
sys.path.insert(0, HK + "/_claude/outils")
import framing
from framing import plan_views
from fx import crop_view, vignette, grain, gblur
from words import tokens, clean
FF = "/opt/homebrew/bin/ffmpeg"
D = L4 + "/_claude/gen/G6/"; OUT = D + "out/"; os.makedirs(OUT, exist_ok=True)
framing.ROOT = L4; framing.CACHE = D + "cache"
W, H, TFPS, SFPS = 1080, 1920, 30, 25          # toutes les sources sont à 25 i/s
# ---------------- sources (lot4/sources) ----------------
FI = "G6-guette-franceinfo-2026-10-22.mp4"     # hl8dSp1e_o8 entière (franceinfo, Télé Matin « Les 4 vérités », 22/10/2026)
BF = "G6-guette-bfmtv-2026-10-08.mp4"          # YTteQi-qY9w entière (BFMTV/RMC « Apolline Matin », 08/10/2026, chaîne de C. Guetté), 720p
MX = "G6-guette-meaux-05.mp4"                  # copie de lot2/sources/C1-guette-meaux-05.mp4 (meeting de Meaux, Cse3O99mlR0), plan non utilisé par C1
YT = {FI: ("hl8dSp1e_o8", 0.0), BF: ("YTteQi-qY9w", 0.0), MX: ("Cse3O99mlR0 (extrait lot2 C1-guette-meaux-05)", None)}
# zones source (px 1920×1080) sans logo ni bandeau
B_FI = (0, 0, 1300, 855)         # gros plan franceinfo : « LES 4 VÉRITÉS » (x≥1310), interprète LSF (x≥1480), logo france.tv, bandeau nom (y≥860) exclus
B_FIW = (0, 0, 820, 880)         # plan large franceinfo : petit « LES 4 VÉRITÉS » (x≥830), dos du présentateur, interprète, logo tm (y≥920) exclus
B_BFB = (360, 0, 1700, 840)      # BFMTV fond bordeaux : logo RMC (x≤340), RMC STORY (x≥1720), bandeau AM (y≥850) exclus
B_BFS = (360, 0, 1330, 840)      # BFMTV fond ciel rose : logo RMC, bandes noires/jaunes du décor (x≥1340), bandeau AM exclus
B_MX = (0, 0, 1620, 830)         # Meaux : logo LFI (x≥1640), pupitre « MEAUX » (y≥840) exclus
SRC_SCALE = {BF: "scale=1920:1080:flags=lanczos,"}
# ---------------- halo : couleur prise dans la vidéo ----------------
GLOW = (255, 140, 142)           # #FF8C8E : fond « lever de soleil » du plateau Télé Matin (mesuré #AF9697), saturation 0,45, éclairci
WHITE = (255, 255, 255)
GTINT = np.array([255, 205, 210][::-1], np.float32) / 255     # bloom rosé chaud (BGR)

# ---------------- temps ----------------
FR = json.load(open(D + "rythme/frappes.json")); MOFF = FR["MOFF"]   # temps morceau = timeline + MOFF
K = FR["frappes_timeline"]                     # frappes réelles (attaques basse/piano sur chaque temps), 92,4 BPM, timeline
DROP = 5.000                                   # passage le plus connu d'Experience : temps fort 121,49 s du morceau (pic YouTube 120-123 s)
assert min(abs(k - DROP) for k in K) < 0.002
END = 14.90                                    # glow 15 s max
V = 401.69                                     # timeline = temps YouTube (franceinfo) - V  (« Honnêtement » 401,94 -> 0,25 s)
VOICE = (401.94, 406.37)                       # voix posée (YouTube) : présentateur jusqu'à 401,92 (f0 ≈ 120 Hz), Guetté dès 401,95 (f0 ≈ 250 Hz) ; « La fin » suit à 406,40
def f30(t): return int(round(t * TFPS))
iD = min(range(len(K)), key=lambda i: abs(K[i] - DROP))
def KB(n): return K[iD + n]                    # frappe n temps après le drop

# ---------------- textes (mot à mot, phrase réelle) ----------------
TX = json.load(open(D + "tx/hl8dSp1e_o8.json"))
raw = [{"w": w["word"].strip(), "start": w["start"], "end": w["end"]} for s in TX["segments"] for w in s["words"]
       if 402.0 <= w["start"] <= 406.2 and w["word"].strip() != "?"]
T = tokens(raw)
assert " ".join(t["w"] for t in T) == "Honnêtement, ce gouvernement n'inspire que dégoût à la population française. Je pense qu'il devrait s'en rendre compte.", " ".join(t["w"] for t in T)
T[0]["start"] = VOICE[0]                       # attaque réelle de « Honnêtement » (Whisper : 402,02)
def up(t): return clean(t["w"]).upper()
# Honnêtement | ce gouvernement | n'inspire que dégoût | à la population française | Je pense qu'il devrait | s'en rendre compte
GROUPS = [1, 2, 3, 4, 4, 3]
assert sum(GROUPS) == len(T), len(T)
CARDS, i = [], 0
for g in GROUPS:
    CARDS.append({"words": [(up(T[j]), T[j]["start"] - V) for j in range(i, i + g)]}); i += g
for k, c in enumerate(CARDS): c["t1"] = CARDS[k + 1]["words"][0][1] if k + 1 < len(CARDS) else DROP
TEXT_Y = 0.60                                  # centre vertical du texte (test 4 : 60 % depuis le haut)
FONT = ("/System/Library/Fonts/Avenir Next.ttc", 1)          # Avenir Next Bold Italic (test 4)
_fc = {}
def font(px):
    px = int(round(px))
    if px not in _fc: _fc[px] = ImageFont.truetype(FONT[0], px, index=FONT[1])
    return _fc[px]
# Zone sûre TikTok (retour Luca) : bloc ≤ 66 % de large, centré (x 0,17-0,83), y 0,12-0,75. On vise 60 % (marge pour l'italique
# et le halo) ; si une ligne devrait descendre sous 84 px, la carte passe sur 2 lignes équilibrées.
MAXW, PXMAX, PXMIN1 = 0.60 * W, 110, 84
def _fit(words):
    f = font(100); return min(PXMAX, MAXW / (f.getlength(" ".join(words)) / 100))
def card_layout(c):
    """[(mot, temps, x, y, px)] : 1 ou 2 lignes centrées autour de TEXT_Y."""
    if "lay" in c: return c["lay"]
    ws = [w[0] for w in c["words"]]
    lines = [ws]
    if len(ws) > 1 and _fit(ws) < PXMIN1:
        k = min(range(1, len(ws)), key=lambda k: max(font(100).getlength(" ".join(ws[:k])), font(100).getlength(" ".join(ws[k:]))))
        lines = [ws[:k], ws[k:]]
    px = min(_fit(l) for l in lines); f = font(px); sp = f.getlength(" "); lh = px * 1.12
    out, j = [], 0
    for li, l in enumerate(lines):
        tot = sum(f.getlength(w) for w in l) + sp * (len(l) - 1)
        x = W / 2 - tot / 2; y = TEXT_Y * H + (li - (len(lines) - 1) / 2) * lh
        for w in l:
            out.append((w, c["words"][j][1], x, y, px)); x += f.getlength(w) + sp; j += 1
    c["lay"] = out
    return out
def draw_text(img, t):
    act = [c for c in CARDS if c["words"][0][1] - 1e-3 <= t < c["t1"] - 1e-3]   # une seule carte à la fois
    if not act: return img
    lay = Image.new("L", (W, H), 0); dl = ImageDraw.Draw(lay)
    for c in act:
        for word, tw, x, y, px in card_layout(c):
            if tw <= t + 1e-3: dl.text((x, y), word, font=font(px), anchor="lm", fill=255)   # apparition sèche au mot
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
    x = lum[..., None] + (x - lum[..., None]) * 1.10                                      # couleurs un peu plus riches
    hi = np.clip((x - 0.55) / 0.45, 0, 1)
    x = x + gblur(hi, 18) * 0.50 * GTINT                                                  # bloom teinté (SoftGlow)
    if VIG is None: VIG = vignette(np.ones((H, W, 3), np.float32), strength=0.40, power=2.2)
    return grain(np.clip(x, 0, 1) * VIG, 0.012, 1.4)

# ---------------- liste des plans ----------------
# A0 : plan large franceinfo (même émission) où elle parle, lèvres illisibles : la régie montre le présentateur pendant
#      « Honnêtement, ce » (401,95-402,70). A1 : gros plan en synchro exacte dès 402,80, coupe sur une frappe.
# B : rafale sur les frappes réelles après le drop, 2 temps (1,3 s) par plan, 1 temps sur la 3e mesure, poussée lente avant.
def S(i, a, b, src, t_in, sp, hint, bnd, vh, z0, z1, fx="", note=""):
    return dict(id=i, a=a, b=b, src=src, t_in=t_in, sp=sp, hint=hint, bnd=bnd, vh=vh, z0=z0, z1=z1, fx=fx, note=note)
A_CUT = K[iD - 6]                              # 1,116 s : frappe, gros plan franceinfo depuis 402,70
assert A_CUT + V >= 402.72
SHOTS = [
    S("A0", 0.0, A_CUT, FI, 361.05, 100, (500, 320), B_FIW, 880, 1.00, 1.02, "texte",
      "début de la phrase sur le plan large franceinfo (elle parle, lèvres illisibles) ; la régie est sur le présentateur à ce moment"),
    S("A1", A_CUT, DROP, FI, A_CUT + V, 100, (860, 380), B_FI, 855, 1.00, 1.03, "texte",
      "phrase en synchro exacte sur le gros plan franceinfo, flash doux sur la coupe"),
    S("B1", KB(0), KB(2), FI, 347.40, 100, (860, 380), B_FI, 855, 1.00, 1.03, "flash", "drop (passage le plus connu, 121,49 s du morceau) : flash, gros plan franceinfo, elle parle"),
    S("B2", KB(2), KB(4), BF, 505.60, 100, (980, 360), B_BFS, 840, 1.00, 1.03, "", "BFMTV, fond ciel rose (lever de soleil)"),
    S("B3", KB(4), KB(6), FI, 364.40, 50, (860, 380), B_FI, 855, 1.00, 1.03, "", "gros plan franceinfo (ralenti)"),
    S("B4", KB(6), KB(8), BF, 345.80, 100, (960, 260), B_BFB, 840, 1.00, 1.03, "", "BFMTV, fond bordeaux"),
    S("B5", KB(8), KB(9), MX, 1.00, 100, (940, 200), B_MX, 830, 1.00, 1.02, "", "meeting de Meaux, fond noir (1 temps)"),
    S("B6", KB(9), KB(10), FI, 373.00, 100, (860, 380), B_FI, 855, 1.00, 1.02, "", "gros plan franceinfo (1 temps)"),
    S("B7", KB(10), KB(12), BF, 509.50, 100, (980, 360), B_BFS, 840, 1.00, 1.03, "", "BFMTV, fond ciel rose, elle parle"),
    S("B8", KB(12), KB(14), FI, 351.50, 50, (860, 380), B_FI, 855, 1.00, 1.03, "", "gros plan franceinfo (ralenti)"),
    S("B9", KB(14), END, BF, 349.50, 50, (960, 260), B_BFB, 840, 1.00, 1.03, "fin", "BFMTV fond bordeaux (ralenti), fondu au noir 0,6 s"),
]
for sh in SHOTS:
    sh["rec"] = f30(sh["a"]); sh["dur"] = f30(sh["b"]) - sh["rec"]
    sh["clip"] = "G6_%s.mov" % sh["id"]
    sh["speed_res"] = float(sh["sp"])           # clips livrés à 30 i/s (sources 25 i/s converties) : Resolve à sp %
def ease_out(u): u = min(max(u, 0.0), 1.0); return 1 - (1 - u) ** 3
def zoom_at(sh, t):
    u = (t - sh["a"]) / (sh["b"] - sh["a"])
    u = min(max(u, 0), 1) if sh["fx"] == "texte" else ease_out(u)
    return sh["z0"] + (sh["z1"] - sh["z0"]) * u

# ---------------- rendu d'un plan ----------------
def read_frames(src, t, n):
    p = subprocess.Popen([FF, "-v", "error", "-ss", "%.4f" % t, "-i", L4 + "/sources/" + src, "-vf", SRC_SCALE.get(src, "") + "fps=30",
                          "-frames:v", str(n), "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE)
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
    n = sh["dur"]; slow = sh["sp"] != 100
    # clip livré à vitesse normale (image k = source t_in + k/30) ; ralenti : Resolve lit ce clip à sp % -> image k au temps a + k/(30·sp)
    a0 = sh["rec"] / TFPS                      # temps réel de la 1re image du plan (coupe calée à l'image)
    tl_t = (lambda k: a0 + k / (TFPS * sh["sp"] / 100)) if slow else (lambda k: a0 + k / TFPS)
    views, ok = plan_views(sh["src"], int(round(sh["t_in"] * SFPS)), n, SFPS, speed=SFPS / TFPS, hint=sh["hint"], bounds=sh["bnd"], vh=sh["vh"],
                           zoom=lambda k: zoom_at(sh, tl_t(k)), top=0.16)
    frames = list(read_frames(sh["src"], sh["t_in"], n))
    w = writer(OUT + sh["clip"], TFPS)
    for k in range(n):
        fr = frames[min(k, len(frames) - 1)]
        cx, cy, vh = views[k]; vw = vh * 9 / 16
        img = grade(crop_view(fr.astype(np.float32) / 255, cx, cy, vw, W, H))
        t = tl_t(k)
        if sh["fx"] == "texte": img = draw_text(img, t)
        if sh["id"] == "A1":                                                        # flash doux sur la coupe A0 -> A1
            fl = max(0.0, 0.35 * (1 - (t - sh["a"]) / 0.10)); img = img + (1 - img) * fl
        if sh["fx"] == "flash":                                                    # flash sur le drop (4 images timeline)
            fl = max(0.0, 0.75 * (1 - (t - sh["a"]) / 0.13))
            img = img + (1 - img) * fl * np.array([0.97, 0.93, 1.0], np.float32)
        if sh["fx"] == "fin": img = img * min(max((END - t) / 0.6, 0.0), 1.0)
        w.stdin.write((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8).tobytes())
    w.stdin.close(); w.wait()
    vhs = [v[2] for v in views]
    return ("visage" if ok else "SANS VISAGE") + " vue %.0f->%.0f px" % (vhs[0], vhs[-1]) + ("" if len(frames) >= n else " court:%d/%d" % (len(frames), n))

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
SON = L4 + "/sons/G6-einaudi-experience_complet.wav"
VEND = VOICE[1] - V
def build_audio():
    from scipy.signal import butter, sosfilt
    n = int(END * SR); mix = np.zeros((n, 2), np.float32)
    v = fade(load(L4 + "/sources/" + FI, VOICE[0], VOICE[1] - VOICE[0]), 0.02, 0.03)
    lv, _ = lufs(v); v *= db(-15 - lv)
    m = load(SON, MOFF, END)
    lm, _ = lufs(m[int(DROP * SR):]); m *= db(-14 - lm)
    t = np.arange(len(m)) / SR
    # sous la voix : piano baissé (-8 dB) et adouci (passe-bas 2,5 kHz), puis montée jusqu'au drop
    lo = sosfilt(butter(2, 2500, "low", fs=SR, output="sos"), m, axis=0).astype(np.float32)
    a = np.interp(t, [0, VEND, DROP - 0.03, DROP], [1, 1, 0.35, 0])[:, None].astype(np.float32)
    g = np.interp(t, [0, VEND, DROP], [db(-8), db(-8), 1.0])[:, None].astype(np.float32)
    mus = lo * g * a + m * g * (1 - a)
    mus *= (np.clip((END - t) / 1.2, 0, 1) ** 1.5)[:, None].astype(np.float32)
    mus = fade(mus, 0.25, 0)
    mix[:len(mus)] += mus; i0 = int(round((VOICE[0] - V) * SR)); mix[i0:i0 + len(v)] += v[:n - i0]
    tmp = OUT + "_tmp_mix.wav"; sf_write(tmp, mix); gg = 0.0; li, _ = lufs(mix)
    for _ in range(4):
        gg += -14.0 - li
        subprocess.run([FF, "-v", "error", "-y", "-i", tmp, "-af", "volume=%.2fdB,alimiter=limit=0.80:attack=3:release=60:level=false,aresample=192000,alimiter=limit=0.82:attack=1:release=40:level=false,aresample=48000" % gg,
                        "-c:a", "pcm_s24le", OUT + "G6-mix.wav"], check=True)
        li, tp = lufs(load(OUT + "G6-mix.wav"))
        if abs(li + 14) < 0.3 and tp < -1.0: break
    os.remove(tmp)
    return "mix %.1f LUFS, true peak %.1f dBTP" % (li, tp)

# ---------------- son.json + plan-G6.json ----------------
def write_son():
    son = {"titre": "Experience", "artiste": "Ludovico Einaudi", "url": "https://youtu.be/1e9B31FLT-s", "chaine": "Ludovico Einaudi (officielle, Official Visualizer)",
           "fichier": "lot4/sons/G6-einaudi-experience_complet.wav",
           "extrait_morceau_s": [round(MOFF, 3), round(MOFF + END, 3)], "bpm": 92.4,
           "drop": {"morceau_s": round(MOFF + DROP, 3), "timeline_s": DROP,
                    "note": "le passage le plus connu : pic « les plus revus » YouTube 120,1-123,2 s ; drop sur le temps fort 121,49 s (attaque de basse la plus forte du passage, mesurée)"},
           "sous_la_phrase": "montée cordes/piano 116,49-121,49 s (crescendo 118,9-121,5 s), -8 dB et passe-bas doux 2,5 kHz sous la voix, remonte à plein de 4,68 à 5,00 s",
           "frappes": "pas de batterie : frappe = attaque réelle la plus précoce (basse 30-200 Hz ou piano 200-4000 Hz) de chaque temps, rythme/grille.py -> frappes.json",
           "frappes_timeline_s": [k for k in K if k <= END]}
    json.dump(son, open(D + "son.json", "w"), indent=1, ensure_ascii=False)
def write_plan():
    vid = []
    for sh in SHOTS:
        sp = sh["sp"]; used = sh["dur"] / TFPS * sp / 100; yid, y0 = YT[sh["src"]]
        it = {"id": sh["id"], "clip": sh["clip"], "folder": "G6", "path": OUT + sh["clip"], "s": 0, "e": sh["dur"], "clip_fps": TFPS,
              "rec": sh["rec"], "dur": sh["dur"], "track": 1, "note": sh["note"],
              "source": {"fichier": "lot4/sources/" + sh["src"], "fps": SFPS, "in_s": round(sh["t_in"], 3), "out_s": round(sh["t_in"] + used, 3),
                         "youtube": ("%s %.2f-%.2f s" % (yid, y0 + sh["t_in"], y0 + sh["t_in"] + used)) if y0 is not None else yid},
              "effets": "recadrage 9:16 suivi visage (sans logo ni bandeau), glow couleur rose%s" % (
                  {"flash": ", flash 0,13 s cuit", "texte": ", texte cuit", "fin": ", fondu au noir 0,6 s cuit"}.get(sh["fx"], ""))}
        it["frappe_s"] = round(sh["a"], 3); it["poussee"] = "x%.2f -> x%.2f, de la frappe %.3f s à la frappe %.3f s (temps timeline)" % (sh["z0"], sh["z1"], sh["a"], sh["b"])
        if sp != 100:
            it["speed_pct"] = round(sh["speed_res"], 4); it["retime"] = "optical_flow"
            it["ralenti"] = "%d %% : clip 30 i/s à vitesse normale, Resolve à %g %% (Optical Flow, Speed Warp better)" % (sp, sh["speed_res"])
        vid.append(it)
    plan = {"name": "G6 - Glow - Guetté", "fps": 30, "w": 1080, "h": 1920, "duree_s": END,
            "note": "Lot 4, glow COULEUR (aucune image N&B). Coupes sur les frappes réelles d'Experience (rythme/frappes.json). Plans ProRes 9:16 30 i/s prêts (recadrés, poussées, étalonnés, texte cuit sur A0/A1, flash cuit sur A1/B1, fondu cuit sur B9). Sources 25 i/s. Ralentis : speed_pct + Optical Flow. Générateur : lot4/_claude/gen/G6/genG6.py, halo #%02X%02X%02X" % GLOW,
            "musique": {"fichier": "lot4/sons/G6-einaudi-experience_complet.wav", "debut_extrait_s": round(MOFF, 3), "entree_pleine_timeline_s": DROP, "bpm_reel": 92.4,
                        "frappes_timeline_s": [k for k in K if k <= END],
                        "sous_la_voix": "morceau -8 dB (passe-bas 2,5 kHz) de 0 à %.2f s, remonte au drop %.2f s" % (VEND, DROP)},
            "phrase": {"source": "https://youtu.be/hl8dSp1e_o8 401,94-406,37 s (franceinfo / Télé Matin « Les 4 vérités », 22/10/2026)",
                       "texte": " ".join(t["w"] for t in T), "timeline_s": [round(VOICE[0] - V, 3), round(VEND, 3)]},
            "textes": [{"t0": round(c["words"][0][1], 2), "t1": round(c["t1"], 2), "ligne": " ".join(w[0] for w in c["words"]), "taille_px": round(card_layout(c)[0][4]),
                        "lignes": len(set(round(w[3]) for w in card_layout(c)))} for c in CARDS],
            "zone_texte": "zone sûre TikTok : bloc ≤ 60 % de large centré (x 0,20-0,80), centre à y 0,60 (dans 0,12-0,75)",
            "halo": "#%02X%02X%02X (fond lever de soleil du plateau Télé Matin)" % GLOW,
            "video": vid,
            "audio": [{"id": "mix", "clip": "G6-mix.wav", "folder": "G6", "path": OUT + "G6-mix.wav", "rec": 0, "track": 1,
                       "note": "mix final -14 LUFS : voix %.2f-%.2f s, Experience baissé dessous puis plein au drop %.2f s, fondu de fin" % (VOICE[0] - V, VEND, DROP)}]}
    json.dump(plan, open(D + "plan-G6.json", "w"), indent=1, ensure_ascii=False)

# ---------------- aperçu ffmpeg 540×960 ----------------
def preview():
    out = HK + "/preview/apercu-G6.mp4"; args = [FF, "-v", "error", "-y"]; fl = []
    for i, sh in enumerate(SHOTS):
        args += ["-i", OUT + sh["clip"]]; sp = sh["speed_res"] / 100
        fl.append("[%d:v]setpts=(PTS-STARTPTS)/%.6f,fps=30,trim=end_frame=%d,setpts=PTS-STARTPTS,scale=540:960,setsar=1[v%d]" % (i, sp, sh["dur"], i))
    args += ["-i", OUT + "G6-mix.wav"]
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
