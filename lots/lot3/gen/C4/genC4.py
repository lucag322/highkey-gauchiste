# Lot 3 / C4 — Citation ciné, Jean-Luc Mélenchon, son Angèle « Balance ton quoi » (copie de la structure de lot2/_claude/gen/C2/genC2.py, préféré de Luca).
# Citation : meeting de Saint-Denis, 7 juin 2026 (chaîne officielle JEAN-LUC MÉLENCHON, https://www.youtube.com/watch?v=1dkY_JVFx9I, 1:02:54-1:03:06) :
#   « Nous vivons, aimons, pensons tellement autrement parce que les femmes ont gagné de larges pans de liberté et que ce n'est pas fini. »
# Son (règle Luca lot 3 : refrain, pas l'intro) : sous la citation, fin du 2e refrain puis la coupure sans basse (105,5-113 s, montée
# « Un jour peut-être ça changera… ») baissée sous la voix ; la voix finit juste avant « Balance ton » ; le drop (retour de la basse,
# 113,435 s) tombe sur le refrain « Balance ton quoi ? ». Coupes après le drop = claps mesurés (grille 1,034 s = 2 temps à 116 BPM).
# Plans ProRes 9:16 recadrés (visage suivi, logos exclus), sépia lavé + vignette + grain, texte cuit. Ralentis : speed_pct + optical_flow dans plan-C4.json.
# Usage : python genC4.py [plans] [audio] [apercu] [only=ID,ID]
import sys, os, json, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
HK = "/Users/luca.grousset/Movies/highkey-gauchiste"
L3 = HK + "/lot3"
sys.path.insert(0, HK + "/_claude/outils")
D = L3 + "/_claude/gen/C4/"; OUT = D + "out/"; os.makedirs(OUT, exist_ok=True)
import framing
framing.ROOT = L3; framing.CACHE = D + "cache/faces"                   # sources du lot 3, cache dans notre dossier
from framing import plan_views
from fx import crop_view, vignette, grain, gblur, ease_out
from words import clean
FF = "/opt/homebrew/bin/ffmpeg"
W, H, TFPS = 1080, 1920, 30
RED = (228, 0, 43); WHITE = (242, 238, 232)
FONT = "/System/Library/Fonts/Supplemental/Baskerville.ttc"; FIDX = 4      # Baskerville SemiBold (test 3 / C2)
TRACK = 0.20

# ---------------- sources (toutes 1080p 30 i/s) ----------------
SRC = {"CIT": "C4-melenchon-stdenis-citation.mp4", "IS": "C4-melenchon-intersyndicale.mp4"}
for i in range(1, 9): SRC["SD%d" % i] = "C4-melenchon-stdenis-0%d.mp4" % i
SFPS = {k: 30 for k in SRC}
B_CU = (0, 0, 1570, 800)      # gros plans Saint-Denis : filigrane MELENCHON2027.fr (x 1590-1840, y 70-160) et pupitre (texte SAINT-DENIS, y > 800) exclus
B_WIDE = (0, 175, 1570, 1080) # plans larges : sous et à gauche du filigrane d'angle
B_CIT = (0, 0, 1570, 1080)   # plan large citation : filigrane exclu
B_IS = (0, 175, 1570, 880)    # intersyndicale : filigrane d angle et autocollants syndicaux du premier rang exclus

# ---------------- citation (mots : whisper, débuts recalés sur l'énergie de la voix) ----------------
CIT_FILE_IN = 3760.0          # le fichier citation commence à 3760 s de la vidéo YouTube
V0 = 14.45                    # voix : timeline = fichier citation - V0
VOUT = 25.68                  # fin de « fini »
WORDS = [("Nous", 14.57), ("vivons,", 14.84), ("aimons,", 16.04), ("pensons", 17.29), ("tellement", 17.87), ("autrement", 18.82),
         ("parce", 19.62), ("que", 20.92), ("les", 21.12), ("femmes", 21.28), ("ont", 21.74), ("gagné", 22.44), ("de", 22.92),
         ("larges", 23.07), ("pans", 23.48), ("de", 23.73), ("liberté", 23.92), ("et", 24.41), ("que", 24.71), ("ce", 24.76),
         ("n'est", 24.92), ("pas", 25.14), ("fini.", 25.36)]
TEXTE = "Nous vivons, aimons, pensons tellement autrement parce que les femmes ont gagné de larges pans de liberté et que ce n'est pas fini."
T = [{"w": w, "start": t} for w, t in WORDS]

# ---------------- musique ----------------
MUSIC = L3 + "/sons/C4-angele-balance-ton-quoi_complet.wav"
M_DROP = 113.435              # retour de la basse + clap (morceau complet), refrain « Balance ton quoi ? » après la coupure
M_PICK = 112.54               # attaque de « Balance ton » (voix d'Angèle, avant le drop)
DROP = (VOUT - V0) + 0.10 + (M_DROP - M_PICK)   # « Balance ton » démarre 0,10 s après la fin de la voix
C_OFF = M_DROP - DROP         # musique : timeline = complet - C_OFF
KICKS = [113.435, 114.475, 115.51, 116.80, 118.605, 119.635]   # claps mesurés (3-12 kHz) ; 116,80 = attaque du 2e « Balance » (les claps de la grille y sont masqués par la voix)
def tc(c): return c - C_OFF
END = tc(KICKS[-1])
def f30(t): return int(round(t * TFPS))

# ---------------- texte ----------------
def up(t): return clean(t["w"], keep_quotes=False).replace("'", "’").upper()
YB, YI = 0.47, 0.80
WFRAC = 0.62                  # zone sûre TikTok (x 0,17-0,83, y 0,12-0,75) : cartons sur noir ≤ 62 % de large, centrés à YB ;
# cartons sur l'image calés par le bas (yb = ligne de base de la dernière ligne) et plus étroits (wf) : les pointes de la grille
# du pupitre (Q2, Q6) et la foule (Q4) sont lues comme des lettres par la vérif Vision si le texte les frôle.
def ts(i): return T[i]["start"] - V0
def card(lines, red, y, em, t1, wf=WFRAC, yb=None):
    Ls = [[[up(T[i]), ts(i), i in red] for i in li] for li in lines]
    return {"lines": Ls, "t0": Ls[0][0][1], "t1": t1, "y": y, "em": em, "tr": TRACK if y == YB else 0.13, "wf": wf, "yb": yb}
CARDS = [
    card([[0], [1]], [], YB, 130, ts(2)),                 # NOUS / VIVONS
    card([[2]], [], YB, 130, ts(3)),                      # AIMONS
    card([[3], [4], [5]], [], YI, 118, ts(6), 0.54, 0.66),  # PENSONS / TELLEMENT / AUTREMENT (sur l'image)
    card([[6], [7, 8], [9]], [9], YB, 130, ts(10)),       # PARCE / QUE LES / FEMMES (FEMMES rouge, Caslon)
    card([[10, 11], [12, 13], [14]], [], YI, 118, ts(15), 0.54, 0.715),  # ONT GAGNÉ / DE LARGES / PANS
    card([[15], [16]], [16], YB, 140, ts(17)),            # DE / LIBERTÉ (LIBERTÉ rouge, Caslon)
    card([[17, 18], [19, 20], [21, 22]], [], YI, 118, DROP, 0.50, 0.66),  # ET QUE / CE N’EST / PAS FINI
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
def card_em(c): return min(c["em"], min(c["wf"] * W / (line_w(li, 100, c["tr"]) / 100) for li in c["lines"]))
def draw_text(img, t, on_image):
    act = [c for c in CARDS if c["t0"] - 1e-3 <= t < c["t1"]]
    if not act: return img
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dr = ImageDraw.Draw(layer)
    sh = Image.new("L", (W, H), 0); ds = ImageDraw.Draw(sh); em = 100
    for c in act:
        em = card_em(c); lh = em * 1.32; tr = c["tr"]
        vis = [[w for w in li if w[1] <= t + 1e-3] for li in c["lines"]]
        y0 = c["y"] * H - len(c["lines"]) * lh / 2 if c["yb"] is None else c["yb"] * H - (len(c["lines"]) - 1) * lh - em * 0.95
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

# ---------------- étalonnage « sépia lavé » (identique test 3 / C2) ----------------
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
def S(i, a, b, src, t_in, sp, mode, hint, z0, z1, bounds=B_CIT, txt=False, note=""):
    return dict(id=i, a=a, b=b, src=src, t_in=t_in, sp=sp, mode=mode, hint=hint, z0=z0, z1=z1, bounds=bounds, txt=txt, note=note)
C = [tc(k) for k in KICKS]
SHOTS = [
    S("Q1", 0.0, ts(3), None, None, 100, "noir", None, 1, 1, txt=True, note="NOUS / VIVONS puis AIMONS sur noir"),
    S("Q2", ts(3), ts(6), "CIT", V0 + ts(3), 100, "fix", (942, 440), 1.20, 1.23, B_CIT, True, "Saint-Denis, Mélenchon au pupitre (plan large, synchro), PENSONS TELLEMENT AUTREMENT"),
    S("Q3", ts(6), ts(10), None, None, 100, "noir", None, 1, 1, txt=True, note="PARCE QUE / LES FEMMES (rouge) sur noir"),
    S("Q4", ts(10), ts(15), "SD2", 0.3, 100, "fix", (900, 640), 1.0, 1.05, B_WIDE, True, "place de Saint-Denis vue d'en haut, foule, voix off"),
    S("Q5", ts(15), ts(17), None, None, 100, "noir", None, 1, 1, txt=True, note="DE LIBERTÉ (rouge) sur noir"),
    S("Q6", ts(17), DROP, "CIT", V0 + ts(17), 100, "fix", (942, 440), 1.23, 1.26, B_CIT, True, "Saint-Denis plan large synchro, ET QUE CE N'EST PAS FINI, coupe sur le drop"),
    S("B01", C[0], C[1], "SD4", 8.3, 50, "fix", (1000, 600), 1.0, 1.05, B_WIDE, note="drop : Mélenchon de dos face à la foule et aux drapeaux"),
    S("B02", C[1], C[2], "SD5", 4.6, 50, "face", (945, 250), 1.0, 1.05, B_CU, note="Mélenchon bras grands ouverts"),
    S("B03", C[2], C[3], "IS", 116.5, 50, "fix", (800, 520), 1.0, 1.05, B_IS, note="manifestation intersyndicale 29/09/2026, foule et drapeaux violets"),
    S("B04", C[3], C[4], "SD6", 5.4, 50, "face", (930, 240), 1.0, 1.05, B_CU, note="Mélenchon, index levés (1,8 s)"),
    S("B05", C[4], END, "SD8", 19.8, 50, "fix", (900, 640), 1.0, 1.05, B_WIDE, note="foule vue d'en haut, fondu au noir"),
]
FADE_ID, FADE_S = "B05", 0.9
for sh in SHOTS:
    sh["rec"] = f30(sh["a"]); sh["dur"] = f30(sh["b"]) - sh["rec"]
    fps = SFPS.get(sh["src"], TFPS); sh["fps"] = fps
    sh["n"] = int(round(sh["dur"] / TFPS * fps))
    sh["clip"] = "C4_%s.mov" % sh["id"]

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
            img = draw_text(img, sh["a"] + k / fps, False)
            w.stdin.write((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8).tobytes())
    else:
        s = int(round(sh["t_in"] * fps)); z0, z1 = sh["z0"], sh["z1"]; bd = sh["bounds"]
        zoom = lambda f: z0 + (z1 - z0) * f / max(n - 1, 1)
        vh = min(1080, bd[3] - bd[1], (bd[2] - bd[0]) * 16 / 9)
        if sh["mode"] == "face":
            views, ok = plan_views(SRC[sh["src"]], s, n, fps, speed=1.0, hint=sh["hint"], bounds=bd, vh=vh, zoom=zoom)
            info = "visage" if ok else "SANS VISAGE"
        else:
            views, ok = plan_views(SRC[sh["src"]], s, n, fps, speed=1.0, hint=sh["hint"], bounds=bd, vh=vh, zoom=zoom, fixed=sh["hint"])
        k = 0; vmin = 9e9
        for fr in read_frames(sh["src"], s / fps, n):
            cx, cy, v = views[min(k, len(views) - 1)]; vw = v * 9 / 16; vmin = min(vmin, v)
            assert bd[0] - 1 <= cx - vw / 2 and cx + vw / 2 <= bd[2] + 1 and bd[1] - 1 <= cy - v / 2 and cy + v / 2 <= bd[3] + 1, (sh["id"], k, cx, cy, v)
            img = crop_view(fr.astype(np.float32) / 255, cx, cy, vw, W, H)
            img = grade(img)
            if sh["txt"]: img = draw_text(img, sh["a"] + k / fps, True)
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
    n = int(round(END * SR)); mix = np.zeros((n, 2), np.float32)
    v = fade(load(L3 + "/sources/" + SRC["CIT"], V0, VOUT - V0), 0.04, 0.08)
    mus = load(MUSIC, C_OFF, END + 0.05)[:n]
    lv, _ = lufs(v); lm, _ = lufs(mus[int(DROP * SR):])
    v *= db(-15 - lv); mus *= db(-14 - lm)                      # voix -15 LUFS ; musique après drop -14 LUFS
    t = np.arange(len(mus)) / SR
    env = np.where(t < VEND, db(-8), 1.0).astype(np.float32)    # couplet d’Angèle sous la voix (-8 dB, ducking), plein dès « Balance ton »
    r = (t >= VEND) & (t < VEND + 0.08); env[r] = db(-8) + (1 - db(-8)) * (t[r] - VEND) / 0.08
    env *= np.clip(t / 0.3, 0, 1)                                # entrée 0,3 s
    env *= np.where(t > END - 1.0, np.clip((END - t) / 1.0, 0, 1) ** 1.5, 1)
    mix[:len(mus)] += mus * env[:, None]; mix[:len(v)] += v
    tmp = OUT + "_tmp_mix.wav"; sf_write(tmp, mix); g = 0.0; li2 = None
    for _ in range(4):
        li = lufs(mix)[0] if li2 is None else li2
        g += -14.0 - li
        subprocess.run([FF, "-v", "error", "-y", "-i", tmp, "-af", "volume=%.2fdB,alimiter=limit=0.80:attack=3:release=60:level=false,aresample=192000,alimiter=limit=0.82:attack=1:release=40:level=false,aresample=48000" % g,
                        "-c:a", "pcm_s24le", OUT + "C4-mix.wav"], check=True)
        li2, tp2 = lufs(load(OUT + "C4-mix.wav"))
        if abs(li2 + 14) < 0.3 and tp2 < -1.0: break
    os.remove(tmp)
    return "mix %.1f LUFS, true peak %.1f dBTP (voix %.1f, musique %.1f d'origine)" % (li2, tp2, lv, lm)

# ---------------- plan-C4.json ----------------
def write_plan():
    vid = []
    for sh in SHOTS:
        it = {"id": sh["id"], "clip": sh["clip"], "folder": "genC4", "path": OUT + sh["clip"], "s": 0, "e": sh["n"], "clip_fps": sh["fps"],
              "rec": sh["rec"], "dur": sh["dur"], "track": 1, "note": sh["note"]}
        if sh["src"]:
            sp = sh["sp"]; used = sh["n"] * sp / 100 / sh["fps"]
            it["source"] = {"fichier": "lot3/sources/" + SRC[sh["src"]], "in_s": round(sh["t_in"], 3), "out_s": round(sh["t_in"] + used, 3)}
            it["effets"] = "recadrage 9:16 %s (bornes %s), zoom %.2f->%.2f, sépia lavé + vignette + grain%s" % (
                "suivi visage" if sh["mode"] == "face" else "fixe", list(sh["bounds"]), sh["z0"], sh["z1"], ", texte cuit" if sh["txt"] else "")
            if sp != 100: it["speed_pct"] = sp; it["retime"] = "optical_flow"
        else:
            it["effets"] = "noir + grain, texte cuit (Baskerville SemiBold approche 0,20 em ; mot rouge en CaslonGraphique-Opti)"
        if sh["id"] == FADE_ID: it["fade_out_s"] = FADE_S
        vid.append(it)
    plan = {"name": "C4 - Citation cine - Melenchon - Balance ton quoi", "fps": 30, "w": 1080, "h": 1920, "duree_s": round(END, 3),
            "note": "Plans ProRes 9:16 prêts (recadrés hors logos, étalonnés, texte cuit). Ralentis à faire dans Resolve : speed_pct + Optical Flow ; e-s = images source à vitesse normale. Générateur : lot3/_claude/gen/C4/genC4.py",
            "citation": {"texte": TEXTE, "fichier": "lot3/sources/" + SRC["CIT"], "in_s": V0, "out_s": VOUT,
                         "source_url": "https://www.youtube.com/watch?v=1dkY_JVFx9I&t=%d" % (CIT_FILE_IN + V0),
                         "source_temps_s": [round(CIT_FILE_IN + V0, 2), round(CIT_FILE_IN + VOUT, 2)]},
            "musique": {"fichier": "lot3/sons/C4-angele-balance-ton-quoi_complet.wav", "debut_dans_complet_s": round(C_OFF, 3),
                        "drop_timeline_s": round(DROP, 3), "coupes_timeline_s": [round(c, 3) for c in C]},
            "textes": [{"t0": round(c["t0"], 2), "t1": round(c["t1"], 2), "lignes": [" ".join(w[0] for w in li) for li in c["lines"]],
                        "rouge": [w[0] for li in c["lines"] for w in li if w[2]]} for c in CARDS],
            "video": vid,
            "audio": [{"id": "mix", "clip": "C4-mix.wav", "folder": "genC4", "path": OUT + "C4-mix.wav", "rec": 0, "track": 1,
                       "note": "mix -14 LUFS : voix citation %.2f-%.2f s + musique complet %.2f-%.2f s, couplet -8 dB sous la voix (ducking), fondu de fin 1,0 s" % (V0, VOUT, C_OFF, C_OFF + END)}]}
    json.dump(plan, open(D + "plan-C4.json", "w"), indent=1, ensure_ascii=False)
    son = {"titre": "Balance ton quoi", "artiste": "Angèle", "url": "https://youtu.be/Hi7Rx3En7-k", "fichier": "lot3/sons/C4-angele-balance-ton-quoi_complet.wav",
           "extrait_debut_s": round(C_OFF, 3), "extrait_fin_s": round(C_OFF + END, 3), "bpm": 116.0, "drop_s": M_DROP, "drop_timeline_s": round(DROP, 3),
           "frappes_s": KICKS, "frappes_timeline_s": [round(c, 3) for c in C],
           "paroles_audibles": ["(sous la voix, -8 dB) Balance ton quoi / Un jour peut-être ça changera / Y'a plus d'respect dans la rue / Tu sais très bien quand t'abuses",
                                "Balance ton quoi ? (x2, refrain après le drop)"]}
    json.dump(son, open(D + "son.json", "w"), indent=1, ensure_ascii=False)

# ---------------- aperçu ffmpeg 540×960 ----------------
def preview():
    out = HK + "/preview/apercu-C4.mp4"; args = [FF, "-v", "error", "-y"]; fl = []
    for i, sh in enumerate(SHOTS):
        args += ["-i", OUT + sh["clip"]]
        fl.append("[%d:v]setpts=(PTS-STARTPTS)/%.4f,fps=30,trim=end_frame=%d,setpts=PTS-STARTPTS,scale=540:960,setsar=1%s[v%d]" % (
            i, sh["sp"] / 100, sh["dur"], ",fade=t=out:st=%.3f:d=%.2f" % (sh["dur"] / 30 - FADE_S, FADE_S) if sh["id"] == FADE_ID else "", i))
    args += ["-i", OUT + "C4-mix.wav"]
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
    print("total %.2f s ; %d plans ; drop %.2f ; musique %.2f-%.2f" % (END, len(SHOTS), DROP, C_OFF, C_OFF + END))
