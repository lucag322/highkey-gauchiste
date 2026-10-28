# Lot 4 / C6 — Citation ciné, Rima Hassan (eurodéputée LFI). Copie de la structure de lot3/_claude/gen/C5/genC5.py (elle-même copie de C2, préféré de Luca).
# « Quand un pouvoir commence à confondre contestation et menace, ce n'est pas la sécurité qu'il protège, c'est sa complicité. »
#   (meeting LFI de soutien à la Palestine, Strasbourg, 17/06/2026, chaîne La France insoumise, youtu.be/lML9ZGssEac?t=2384) — autre phrase que A7.
# Son : SDM — Bolide allemand (SDM Officiel). Montée sous la phrase (couplet filtré, volume qui monte), la phrase finit dans le break,
# DROP sur « Sortie d'Fresnes » du refrain (attaque 808 mesurée 68,160 s), fin après « j'suis dans l'bolide allemand ».
# Sources réutilisées (lecture seule) : lot3/sources/A7-hassan-strasbourg-{a,b,c}.mp4, moments NON utilisés par A7.
# Ralentis : PAS précalculés. Clip livré à vitesse normale (n = durée_tl × fps_source), speed_pct + retime dans plan-C6.json.
# Usage : python genC6.py [plans] [audio] [apercu] [only=ID,ID]
import sys, os, json, subprocess
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
HK = "/Users/luca.grousset/Movies/highkey-gauchiste"
L4 = HK + "/lot4"; L3 = HK + "/lot3"
sys.path.insert(0, HK + "/_claude/outils")
import framing
D = L4 + "/_claude/gen/C6/"; OUT = D + "out/"; os.makedirs(OUT, exist_ok=True)
framing.ROOT = L3; framing.CACHE = D + "cache"                         # sources lues dans lot3/sources, cache visages chez C6
from framing import plan_views
from fx import crop_view, vignette, grain, gblur, ease_out
from words import clean
FF = "/opt/homebrew/bin/ffmpeg"
W, H, TFPS = 1080, 1920, 30
RED = (228, 0, 43); WHITE = (242, 238, 232)
FONT = "/System/Library/Fonts/Supplemental/Baskerville.ttc"; FIDX = 4      # Baskerville SemiBold (test 3 / C2 / C5)
TRACK = 0.20

# ---------------- sources ----------------
SRC = {"SA": "A7-hassan-strasbourg-a.mp4", "SB": "A7-hassan-strasbourg-b.mp4", "SC": "A7-hassan-strasbourg-c.mp4"}
URL = {"SA": ("https://www.youtube.com/watch?v=lML9ZGssEac", 2195), "SB": ("https://www.youtube.com/watch?v=lML9ZGssEac", 2368),
       "SC": ("https://www.youtube.com/watch?v=lML9ZGssEac", 2634)}
SFPS = {k: 30 for k in SRC}
# Strasbourg : logo ELA x 1615-1820 / y 95-160 ; pupitre (JUSTICE POUR LA PALESTINE + logos) y > 912 sur les gros plans.
B_ST = (130, 0, 1600, 912); B_WIDE = (0, 0, 1600, 1080)

# ---------------- temps ----------------
MUSIC = L4 + "/sons/C6-sdm-bolide-allemand_complet.wav"
V0 = 16.23                           # voix : timeline = fichier SB - V0 (« Quand » 16,38 -> 0,15 s)
VOUT = 25.32                         # fin de « complicité » 25,24 (+80 ms) ; silence puis applaudissements
C_OFF = 58.435                       # musique : timeline = complet - C_OFF (choisi pour que les coupes synchro-mots tombent sur de vraies attaques)
C_DROP = 68.160                      # attaque 808 (score 34,5) sur « Sortie d'Fresnes », 1er temps du refrain, après le break 66,5-67,7
DROP = C_DROP - C_OFF                # 9,725
# coupes = attaques RÉELLES mesurées (temps_forts.py sur le morceau complet), pas de grille
CUTS_V = [60.320, 62.505, 64.745, 66.525]                 # sous la phrase : « commence », « contestation », « ce n'est », « c'est sa »
CUTS_C = [68.160, 69.955, 71.775, 73.590, 75.415]         # après le drop : 808 / caisse claire
C_END = 77.60                        # après « j'suis dans l'bolide allemand » (76,54), avant « J'vais chercher » (78,0) : fin <= 20 s
def tc(c): return c - C_OFF
END = tc(C_END)
def f30(t): return int(round(t * TFPS))

# ---------------- texte (onsets mesurés sur l'enveloppe de la voix, mots vérifiés par Whisper large-v3-turbo) ----------------
WORDS = [("Quand", 16.38), ("un", 16.60), ("pouvoir", 16.90), ("commence", 18.097), ("à", 18.46), ("confondre", 19.00),
         ("contestation", 20.33), ("et", 21.46), ("menace,", 21.58), ("ce", 22.563), ("n'est", 22.62), ("pas", 22.76), ("la", 22.86),
         ("sécurité", 23.00), ("qu'il", 23.46), ("protège,", 23.64), ("c'est", 24.46), ("sa", 24.56), ("complicité.", 24.72)]
TEXTE = "Quand un pouvoir commence à confondre contestation et menace, ce n'est pas la sécurité qu'il protège, c'est sa complicité."
T = [{"w": w, "start": s} for w, s in WORDS]
def up(t): return clean(t["w"], keep_quotes=False).replace("'", "’").upper()
YB, YI = 0.47, 0.62                                      # zone sûre TikTok : x 0,17-0,83, y 0,12-0,75 (retour Luca)
def card(lines, red, y, em, t1):
    Ls = [[[up(T[i]), T[i]["start"] - V0, i in red] for i in li] for li in lines]
    return {"lines": Ls, "t0": Ls[0][0][1], "t1": t1, "y": y, "em": em, "tr": TRACK if y == YB else 0.13}
def ts(i): return T[i]["start"] - V0
CARDS = [
    card([[0, 1], [2]], [], YB, 130, ts(3)),                         # QUAND UN / POUVOIR (noir)
    card([[3, 4], [5]], [], YI, 124, ts(6)),                         # COMMENCE À / CONFONDRE (scène, synchro)
    dict(card([[6], [7, 8]], [8], YB, 130, ts(9)), tr=0.04),         # CONTESTATION / ET MENACE (noir, MENACE rouge Caslon ; approche réduite : mot long)
    card([[9, 10, 11], [12, 13], [14, 15]], [], YI, 112, ts(16)),    # CE N'EST PAS / LA SÉCURITÉ / QU'IL PROTÈGE (gros plan, synchro)
    card([[16, 17], [18]], [18], YI, 124, DROP),                     # C'EST SA / COMPLICITÉ (COMPLICITÉ rouge, synchro)
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

# ---------------- étalonnage « sépia lavé » (identique test 3 / C2 / C5) ----------------
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
def S(i, a, b, src, t_in, sp, mode, hint, z0, z1, bounds=B_ST, txt=False, note="", gain=1.0, shake=None):
    return dict(shake=shake, id=i, a=a, b=b, src=src, t_in=t_in, sp=sp, mode=mode, hint=hint, z0=z0, z1=z1, bounds=bounds, txt=txt, note=note, gain=gain)
CV = [tc(c) for c in CUTS_V]; C = [tc(c) for c in CUTS_C]
SYNC = None                                # t_in = None -> synchro labiale (temps timeline + V0)
SHOTS = [
    S("Q1", 0.0, CV[0], None, None, 100, "noir", None, 1, 1, txt=True, note="QUAND UN / POUVOIR sur noir"),
    S("Q2", CV[0], CV[1], "SB", SYNC, 100, "fix", (875, 540), 1.0, 1.08, B_WIDE, txt=True, note="plan large de la scène, Rima Hassan au pupitre, synchro (« commence à confondre »)"),
    S("Q3", CV[1], CV[2], None, None, 100, "noir", None, 1, 1, txt=True, note="CONTESTATION / ET MENACE sur noir"),
    S("Q4", CV[2], CV[3], "SB", SYNC, 100, "face", (1000, 260), 1.05, 1.12, txt=True, note="gros plan pupitre JUSTICE POUR LA PALESTINE, synchro labiale"),
    S("Q5", CV[3], DROP, "SB", SYNC, 100, "face", (1000, 260), 1.20, 1.30, txt=True, note="même plan resserré (punch-in sur la frappe), « c'est sa complicité », coupe au drop"),
    S("B01", C[0], C[1], "SC", 1.00, 50, "fix", (960, 540), 1.0, 1.05, B_WIDE, note="drop : salle comble vue du fond, bras levés, scène éclairée"),
    S("B02", C[1], C[2], "SA", 31.02, 40, "face", (1000, 420), 1.0, 1.03, note="lève le poing au pupitre (suivi visage décalé à droite pour faire entrer le poing ; 40 % pour rester avant la coupe source 31,767)", shake=(-0.17, 0)),
    S("B03", C[2], C[3], "SA", 14.40, 50, "face", (1000, 260), 1.0, 1.06, note="regard levé vers la salle, fière"),
    S("B04", C[3], C[4], "SA", 21.00, 50, "fix", (1250, 720), 1.35, 1.42, B_WIDE, note="la salle pleine vue de la scène, lumières (cadrage sur la foule, exposition +40 %)", gain=1.4),
    S("B05", C[4], END, "SC", 30.50, 50, "face", (600, 330), 1.0, 1.06, note="éclat de rire, main levée près du visage, fondu au noir"),
]
FADE_ID, FADE_S = "B05", 0.6
# images de coupe ajustées d'une image vers l'attaque MESURÉE sur l'export (verif.py) : arrondi f30 donnait +20 / -30 / -25 / -20 ms
REC_FIX = {"Q2": 56, "Q3": 123, "Q4": 190, "B05": 510}
for i, sh in enumerate(SHOTS):
    sh["rec"] = REC_FIX.get(sh["id"], f30(sh["a"]))
for i, sh in enumerate(SHOTS):
    sh["dur"] = (SHOTS[i + 1]["rec"] if i + 1 < len(SHOTS) else f30(END)) - sh["rec"]
    fps = SFPS.get(sh["src"], TFPS); sh["fps"] = fps
    sh["n"] = int(round(sh["dur"] / TFPS * fps))
    sh["clip"] = "C6_%s.mov" % sh["id"]
    if sh["src"] and sh["t_in"] is None: sh["t_in"] = sh["rec"] / TFPS + V0

def read_frames(src, t, n):
    p = subprocess.Popen([FF, "-v", "error", "-ss", "%.4f" % t, "-i", L3 + "/sources/" + SRC[src], "-frames:v", str(n),
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
    n, fps = sh["n"], sh["fps"]; w = writer(OUT + sh["clip"], fps); info = ""
    if sh["mode"] == "noir":
        for k in range(n):
            img = grain(np.zeros((H, W, 3), np.float32) + 0.012, 0.012, 1.6)
            img = draw_text(img, sh["rec"] / TFPS + k / fps, False)
            w.stdin.write((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8).tobytes())
    else:
        s = int(round(sh["t_in"] * fps)); z0, z1 = sh["z0"], sh["z1"]; bd = sh["bounds"]
        used = max(int(round(n * sh["sp"] / 100)), 2)              # images réellement montrées (ralenti Resolve)
        zoom = lambda f: z0 + (z1 - z0) * min(f, used - 1) / max(used - 1, 1)
        vh = min(1080, bd[3] - bd[1], (bd[2] - bd[0]) * 16 / 9)
        if sh["mode"] == "face":
            views, ok = plan_views(SRC[sh["src"]], s, n, fps, speed=1.0, hint=sh["hint"], bounds=bd, vh=vh, zoom=zoom, shake=(lambda f: sh["shake"]) if sh["shake"] else None)
            info = "visage" if ok else "SANS VISAGE"
        else:
            views, ok = plan_views(SRC[sh["src"]], s, n, fps, speed=1.0, hint=sh["hint"], bounds=bd, vh=vh, zoom=zoom, fixed=sh["hint"])
        k = 0; vmin = 9e9
        for fr in read_frames(sh["src"], s / fps, n):
            cx, cy, v = views[min(k, len(views) - 1)]; vw = v * 9 / 16; vmin = min(vmin, v)
            assert bd[0] - 1 <= cx - vw / 2 and cx + vw / 2 <= bd[2] + 1 and bd[1] - 1 <= cy - v / 2 and cy + v / 2 <= bd[3] + 1, (sh["id"], k, cx, cy, v)
            img = crop_view(fr.astype(np.float32) / 255 * sh["gain"], cx, cy, vw, W, H)
            img = grade(img)
            if sh["txt"]: img = draw_text(img, sh["rec"] / TFPS + k / fps, True)
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
VEND = VOUT - V0
def build_audio():
    from scipy.signal import butter, sosfiltfilt
    n = int(round(END * SR)); mix = np.zeros((n, 2), np.float32)
    v = fade(load(L3 + "/sources/" + SRC["SB"], V0, VOUT - V0), 0.02, 0.06)
    mus = load(MUSIC, C_OFF, END + 0.05)[:n]
    lv, _ = lufs(v); lm, _ = lufs(mus[int(DROP * SR):])
    v *= db(-15 - lv); mus *= db(-14 - lm)                      # voix -15 LUFS ; refrain après drop -14 LUFS
    t = np.arange(len(mus)) / SR
    # MONTÉE sous la phrase : couplet filtré (passe-bas 1,2 kHz) qui s'ouvre de 6,3 s au drop, volume -11 dB -> -5 dB, plein sur la frappe du drop
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
                        "-c:a", "pcm_s24le", OUT + "C6-mix.wav"], check=True)
        li2, tp2 = lufs(load(OUT + "C6-mix.wav"))
        if abs(li2 + 14) < 0.3 and tp2 < -1.0: break
    os.remove(tmp)
    sf_write(OUT + "C6-voix.wav", v); sf_write(OUT + "C6-musique.wav", out)
    return "mix %.1f LUFS, true peak %.1f dBTP (voix %.1f, musique %.1f d'origine)" % (li2, tp2, lv, lm)

# ---------------- plan-C6.json ----------------
def write_plan():
    vid = []
    for sh in SHOTS:
        it = {"id": sh["id"], "clip": sh["clip"], "folder": "genC6", "path": OUT + sh["clip"], "s": 0, "e": sh["n"], "clip_fps": sh["fps"],
              "rec": sh["rec"], "dur": sh["dur"], "track": 1, "note": sh["note"]}
        if sh["src"]:
            sp = sh["sp"]; used = sh["n"] * sp / 100 / sh["fps"]
            it["source"] = {"fichier": "lot3/sources/" + SRC[sh["src"]], "url": URL[sh["src"]][0], "yt_in_s": round(URL[sh["src"]][1] + sh["t_in"], 2), "in_s": round(sh["t_in"], 3), "out_s": round(sh["t_in"] + used, 3)}
            it["effets"] = "recadrage 9:16 %s (bornes %s), zoom %.2f->%.2f, sépia lavé + vignette + grain%s" % (
                "suivi visage" if sh["mode"] == "face" else "fixe", list(sh["bounds"]), sh["z0"], sh["z1"], ", texte cuit" if sh["txt"] else "")
            it["speed_pct"] = sp
            if sp != 100: it["retime"] = "optical_flow"
        else:
            it["speed_pct"] = 100
            it["effets"] = "noir + grain, texte cuit (Baskerville SemiBold approche 0,20 em ; mot rouge en CaslonGraphique-Opti)"
        if sh["id"] == FADE_ID: it["fade_out_s"] = FADE_S
        vid.append(it)
    plan = {"name": "C6 - Citation cine - Rima Hassan", "fps": 30, "w": 1080, "h": 1920, "duree_s": round(END, 3),
            "note": "Aperçu lot 4. Plans ProRes 9:16 prêts (recadrés hors logos, étalonnés, texte cuit). Ralentis à faire dans Resolve : speed_pct + Optical Flow ; e-s = images source à vitesse normale. Générateur : lot4/_claude/gen/C6/genC6.py",
            "citation": {"texte": TEXTE, "fichier": "lot3/sources/" + SRC["SB"], "in_s": V0, "out_s": VOUT, "source_url": URL["SB"][0],
                         "yt_in_s": round(URL["SB"][1] + V0, 2), "yt_out_s": round(URL["SB"][1] + VOUT, 2), "date": "2026-06-17, meeting LFI de soutien à la Palestine, Strasbourg (chaîne La France insoumise)"},
            "musique": {"fichier": "lot4/sons/C6-sdm-bolide-allemand_complet.wav", "url": "https://youtu.be/WcX37NouKxw", "debut_dans_complet_s": round(C_OFF, 3), "fin_dans_complet_s": round(C_END, 3),
                        "drop_timeline_s": round(DROP, 3), "coupes_timeline_s": [round(sh["rec"] / 30, 3) for sh in SHOTS[1:]]},
            "textes": [{"t0": round(c["t0"], 2), "t1": round(c["t1"], 2), "lignes": [" ".join(w[0] for w in li) for li in c["lines"]],
                        "rouge": [w[0] for li in c["lines"] for w in li if w[2]]} for c in CARDS],
            "video": vid,
            "audio": [{"id": "mix", "clip": "C6-mix.wav", "folder": "genC6", "path": OUT + "C6-mix.wav", "rec": 0, "track": 1,
                       "note": "mix -14 LUFS : voix SB %.2f-%.2f s (fondu 60 ms) + musique complet %.3f-%.2f s ; sous la voix couplet filtré passe-bas 1,2 kHz qui s'ouvre de 6,3 s au drop et volume -11 -> -5 dB (montée), plein sur le drop %.2f s, fondu de fin %.1f s" % (V0, VOUT, C_OFF, C_END, DROP, FADE_S)}],
            "stems": [OUT + "C6-voix.wav", OUT + "C6-musique.wav"]}
    json.dump(plan, open(D + "plan-C6.json", "w"), indent=1, ensure_ascii=False)

# ---------------- aperçu ffmpeg 540×960 ----------------
def preview():
    out = HK + "/preview/apercu-C6.mp4"; args = [FF, "-v", "error", "-y"]; fl = []
    for i, sh in enumerate(SHOTS):
        args += ["-i", OUT + sh["clip"]]
        fl.append("[%d:v]setpts=(PTS-STARTPTS)/%.4f,fps=30,trim=end_frame=%d,setpts=PTS-STARTPTS,scale=540:960,setsar=1%s[v%d]" % (
            i, sh["sp"] / 100, sh["dur"], ",fade=t=out:st=%.3f:d=%.2f" % (sh["dur"] / 30 - FADE_S, FADE_S) if sh["id"] == FADE_ID else "", i))
    args += ["-i", OUT + "C6-mix.wav"]
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
