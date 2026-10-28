# Lot 3 / C5 — Citation ciné, Bally Bagayoko (maire LFI de Saint-Denis). Copie de la structure de lot2/_claude/gen/C2/genC2.py (préféré de Luca).
# « Ici, on a su dire non. Non aux fascistes, non à la collaboration et non à la haine. » (meeting de Saint-Denis, 7 juin 2026, chaîne officielle JLM)
# Son : Stromae — Alors on danse (StromaeVEVO). La fin de la citation tombe juste avant « Alors on danse », le boom 63,535 s du morceau = drop.
# Plans ProRes 9:16 recadrés (visage suivi, logos exclus) + sépia lavé + vignette + grain, texte cuit sur la citation.
# Ralentis : PAS précalculés. Clip livré à vitesse normale (n = durée_tl × fps_source), speed_pct + retime dans plan-C5.json.
# Usage : python genC5.py [plans] [audio] [apercu] [only=ID,ID]
import sys, os, json, subprocess
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
HK = "/Users/luca.grousset/Movies/highkey-gauchiste"
L2 = HK + "/lot3"                                                        # (nom gardé du modèle : racine du lot)
sys.path.insert(0, HK + "/_claude/outils")
import framing
D = L2 + "/_claude/gen/C5/"; OUT = D + "out/"; os.makedirs(OUT, exist_ok=True)
framing.ROOT = L2; framing.CACHE = D + "cache"
from framing import plan_views
from fx import crop_view, vignette, grain, gblur, ease_out
from words import clean
FF = "/opt/homebrew/bin/ffmpeg"
W, H, TFPS = 1080, 1920, 30
RED = (228, 0, 43); WHITE = (242, 238, 232)
FONT = "/System/Library/Fonts/Supplemental/Baskerville.ttc"; FIDX = 4      # Baskerville SemiBold (test 3 / C2)
TRACK = 0.20

# ---------------- sources ----------------
SRC = {"CIT": "C5-bagayoko-meeting-citation.mp4", "ARR": "C5-bagayoko-meeting-arrivee.mp4", "GAG": "C5-bagayoko-meeting-gagner.mp4",
       "FIN": "C5-bagayoko-meeting-final.mp4", "VIL": "C5-bagayoko-meeting-ville.mp4", "CLP": "C5-bagayoko-clpress-stdenis.mp4"}
URL = {"CIT": ("https://www.youtube.com/watch?v=1dkY_JVFx9I", 505), "ARR": ("https://www.youtube.com/watch?v=1dkY_JVFx9I", 296),
       "GAG": ("https://www.youtube.com/watch?v=1dkY_JVFx9I", 795), "FIN": ("https://www.youtube.com/watch?v=1dkY_JVFx9I", 1004),
       "VIL": ("https://www.youtube.com/watch?v=1dkY_JVFx9I", 405), "CLP": ("https://www.youtube.com/watch?v=evum5gQACBw", 2130)}
SFPS = {k: (25 if k == "CLP" else 30) for k in SRC}
B_MT = (0, 0, 1570, 1080)            # meeting : filigrane MELENCHON2027.fr x 1590-1890 / y 40-170 exclu
B_CLP = (300, 0, 1235, 660)          # CLPRESS : logo x 1240-1750 / y 120-250 exclu ; pancarte CONTRE LE RACISME (y > 670, coupée) et foule exclues

# ---------------- temps ----------------
MUSIC = L2 + "/sons/C5-stromae-alors-on-danse_complet.wav"
V0 = 16.10                           # voix : timeline = fichier citation - V0 (« Ici » 16,30)
VOUT = 23.00                         # fin de « haine » 22,92 (+80 ms) ; pause jusqu'à 25,6
C_DROP = 63.535                      # boom du morceau (attaque mesurée, score 46,8) sur « danse » du 1er « Alors on danse »
DROP = 7.80                          # « Alors » (62,56 du morceau) démarre à 6,83, juste après « haine » (fin 6,82)
C_OFF = C_DROP - DROP                # musique : timeline = complet - C_OFF
# coupes après le drop = attaques RÉELLES mesurées (temps_forts.py, morceau complet) ; pas de grille
CUTS_C = [63.535, 65.330, 67.605, 69.385, 70.650, 71.670, 73.455]   # 65,330 : attaque 65,315 -> image 288 (écart export -12 ms au lieu de +22 ms avec 287)
C_END = 74.40                        # avant le 4e « Alors » (74,44) : fin <= 20 s
DUCK_END = 6.80
def tc(c): return c - C_OFF
END = tc(C_END)
def f30(t): return int(round(t * TFPS))

# ---------------- texte (whisper large-v3-turbo sur le fichier citation, mot à mot) ----------------
WORDS = [("Ici,", 16.30), ("on", 17.22), ("a", 17.78), ("su", 17.94), ("dire", 18.10), ("non.", 18.28),
         ("Non", 19.34), ("aux", 19.90), ("fascistes,", 20.08), ("non", 20.74), ("à", 21.10), ("la", 21.18), ("collaboration", 21.30),
         ("et", 21.72), ("non", 22.22), ("à", 22.42), ("la", 22.56), ("haine.", 22.68)]
TEXTE = "Ici, on a su dire non. Non aux fascistes, non à la collaboration et non à la haine."
T = [{"w": w, "start": s} for w, s in WORDS]
def up(t): return clean(t["w"], keep_quotes=False).replace("'", "’").upper()
# Zone sûre TikTok (26/10) : bloc <= 66 % de large centré (x 0,17-0,83), y 0,12-0,75. Avant : lignes <= 90 % de W, YI = 0,70
# (FASCISTES / À LA HAINE descendaient à y 1462 > 1440, DIRE NON et COLLABORATION débordaient sur les bords).
YB, YI = 0.47, 0.66
TXT_MAXW = 0.64 * W                  # largeur max d'une ligne (691 px, marge sous les 713 px de la zone)
def card(lines, red, y, em, t1):
    Ls = [[[up(T[i]), T[i]["start"] - V0, i in red] for i in li] for li in lines]
    return {"lines": Ls, "t0": Ls[0][0][1], "t1": t1, "y": y, "em": em, "tr": TRACK if y == YB else 0.13}
def ts(i): return T[i]["start"] - V0
CARDS = [
    card([[0]], [], YB, 130, ts(1)),                      # ICI (noir)
    card([[1, 2, 3], [4, 5]], [5], YB, 130, ts(6)),       # ON A SU / DIRE NON (NON rouge, Caslon)
    card([[6, 7], [8]], [], YI, 124, ts(9)),              # NON AUX / FASCISTES (synchro)
    dict(card([[9, 10, 11], [12]], [], YB, 130, ts(13)), tr=0.07),   # NON À LA / COLLABORATION (noir, approche réduite : mot long)
    card([[13, 14], [15, 16, 17]], [17], YI, 124, DROP),  # ET NON / À LA HAINE (HAINE rouge, synchro)
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
def card_em(c): return min(c["em"], min(TXT_MAXW / (line_w(li, 100, c["tr"]) / 100) for li in c["lines"]))
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

# ---------------- étalonnage « sépia lavé » (identique test 3) ----------------
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
def S(i, a, b, src, t_in, sp, mode, hint, z0, z1, bounds=B_MT, txt=False, note=""):
    return dict(id=i, a=a, b=b, src=src, t_in=t_in, sp=sp, mode=mode, hint=hint, z0=z0, z1=z1, bounds=bounds, txt=txt, note=note)
C = [tc(c) for c in CUTS_C]
SHOTS = [
    S("Q1", 0.0, ts(6), None, None, 100, "noir", None, 1, 1, txt=True, note="ICI / ON A SU / DIRE NON sur noir"),
    S("Q2", ts(6), ts(9), "CIT", T[6]["start"], 100, "face", (1020, 220), 1.30, 1.36, txt=True, note="au pupitre SAINT-DENIS, synchro labiale"),
    S("Q3", ts(9), ts(13), None, None, 100, "noir", None, 1, 1, txt=True, note="NON À LA / COLLABORATION sur noir"),
    S("Q4", ts(13), DROP, "CIT", T[13]["start"], 100, "face", (1020, 220), 1.36, 1.46, txt=True, note="pupitre serré, synchro, « haine » puis « Alors » de Stromae, coupe au boom"),
    S("B01", C[0], C[1], "ARR", 4.0, 50, "fix", (800, 620), 1.0, 1.05, note="drop : vue aérienne, place noire de monde devant la basilique"),
    S("B02", C[1], C[2], "ARR", 32.0, 50, "face", (1110, 210), 1.0, 1.06, note="Bagayoko au pupitre, grand sourire"),
    S("B03", C[2], C[3], "CLP", 5.6, 50, "face", (1040, 280), 1.0, 1.05, B_CLP, note="rassemblement contre le racisme (04/2026), écharpe tricolore, main levée"),
    S("B04", C[3], C[4], "GAG", 9.0, 50, "fix", (1000, 560), 1.0, 1.05, note="foule devant l'hôtel de ville de Saint-Denis"),
    S("B05", C[4], C[5], "FIN", 1.0, 50, "face", (980, 230), 1.0, 1.05, note="pupitre, geste de la main"),
    S("B06", C[5], C[6], "ARR", 34.0, 50, "face", (1110, 210), 1.0, 1.06, note="index levé vers la foule"),
    S("B07", C[6], END, "FIN", 29.0, 50, "fix", (900, 600), 1.0, 1.04, note="place pleine, drapeaux, fondu au noir"),
]
FADE_ID, FADE_S = "B07", 0.8
for sh in SHOTS:
    sh["rec"] = f30(sh["a"]); sh["dur"] = f30(sh["b"]) - sh["rec"]
    fps = SFPS.get(sh["src"], TFPS); sh["fps"] = fps
    sh["n"] = int(round(sh["dur"] / TFPS * fps))
    sh["clip"] = "C5_%s.mov" % sh["id"]

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
            # garde-fou : la vue reste dans les bornes (logos exclus)
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
def build_audio():
    n = int(round(END * SR)); mix = np.zeros((n, 2), np.float32)
    v = fade(load(L2 + "/sources/" + SRC["CIT"], V0, VOUT - V0), 0.02, 0.06)
    mus = load(MUSIC, C_OFF, END + 0.05)[:n]
    lv, _ = lufs(v); lm, _ = lufs(mus[int(DROP * SR):])
    v *= db(-15 - lv); mus *= db(-14 - lm)                      # voix -15 LUFS ; musique après drop -14 LUFS
    t = np.arange(len(mus)) / SR
    # sous la voix : couplet de Stromae à -9 dB (voix lisible) ; remonte à 0 dB entre 6,80 et 6,95 s (fin de « haine » -> « Alors on danse »)
    env = (db(-9) + (1 - db(-9)) * np.clip((t - DUCK_END) / 0.15, 0, 1)).astype(np.float32)
    env *= np.clip(t / 0.3, 0, 1)                                # entrée 0,3 s
    env *= np.where(t > END - 1.1, np.clip((END - t) / 1.1, 0, 1) ** 1.5, 1)
    mix[:len(mus)] += mus * env[:, None]; mix[:len(v)] += v
    tmp = OUT + "_tmp_mix.wav"; sf_write(tmp, mix); g = 0.0; li2 = None
    for _ in range(3):
        li = lufs(mix)[0] if li2 is None else li2
        g += -14.0 - li
        subprocess.run([FF, "-v", "error", "-y", "-i", tmp, "-af", "volume=%.2fdB,alimiter=limit=0.80:attack=3:release=60:level=false,aresample=192000,alimiter=limit=0.82:attack=1:release=40:level=false,aresample=48000" % g,
                        "-c:a", "pcm_s24le", OUT + "C5-mix.wav"], check=True)
        li2, tp2 = lufs(load(OUT + "C5-mix.wav"))
        if abs(li2 + 14) < 0.3 and tp2 < -1.0: break
    os.remove(tmp)
    sf_write(OUT + "C5-voix.wav", v); sf_write(OUT + "C5-musique.wav", mus)
    return "mix %.1f LUFS, true peak %.1f dBTP (voix %.1f, musique %.1f d'origine)" % (li2, tp2, lv, lm)

# ---------------- plan-C5.json ----------------
def write_plan():
    vid = []
    for sh in SHOTS:
        it = {"id": sh["id"], "clip": sh["clip"], "folder": "genC5", "path": OUT + sh["clip"], "s": 0, "e": sh["n"], "clip_fps": sh["fps"],
              "rec": sh["rec"], "dur": sh["dur"], "track": 1, "note": sh["note"]}
        if sh["src"]:
            sp = sh["sp"]; used = sh["n"] * sp / 100 / sh["fps"]
            it["source"] = {"fichier": "lot3/sources/" + SRC[sh["src"]], "url": URL[sh["src"]][0], "yt_in_s": round(URL[sh["src"]][1] + sh["t_in"], 2), "in_s": round(sh["t_in"], 3), "out_s": round(sh["t_in"] + used, 3)}
            it["effets"] = "recadrage 9:16 %s (bornes %s), zoom %.2f->%.2f, sépia lavé + vignette + grain%s" % (
                "suivi visage" if sh["mode"] == "face" else "fixe", list(sh["bounds"]), sh["z0"], sh["z1"], ", texte cuit" if sh["txt"] else "")
            if sp != 100: it["speed_pct"] = sp; it["retime"] = "optical_flow"
        else:
            it["effets"] = "noir + grain, texte cuit (Baskerville SemiBold approche 0,20 em ; mot rouge en CaslonGraphique-Opti)"
        if sh["id"] == FADE_ID: it["fade_out_s"] = FADE_S
        vid.append(it)
    plan = {"name": "C5 - Citation cine - Bagayoko", "fps": 30, "w": 1080, "h": 1920, "duree_s": round(END, 3),
            "note": "Plans ProRes 9:16 prêts (recadrés hors logos, étalonnés, texte cuit). Ralentis à faire dans Resolve : speed_pct + Optical Flow ; e-s = images source à vitesse normale. Générateur : lot3/_claude/gen/C5/genC5.py",
            "citation": {"texte": TEXTE, "fichier": "lot3/sources/" + SRC["CIT"], "in_s": V0, "out_s": VOUT, "source_url": URL["CIT"][0],
                         "yt_in_s": round(URL["CIT"][1] + V0, 2), "yt_out_s": round(URL["CIT"][1] + VOUT, 2), "date": "2026-06-07, meeting de Saint-Denis (chaîne JEAN-LUC MÉLENCHON)"},
            "musique": {"fichier": "lot3/sons/C5-stromae-alors-on-danse_complet.wav", "url": "https://youtu.be/VHoT4N43jK8", "fin_dans_complet_s": round(C_END, 3), "debut_dans_complet_s": round(C_OFF, 3),
                        "drop_timeline_s": round(DROP, 3), "coupes_timeline_s": [round(c, 3) for c in C]},
            "textes": [{"t0": round(c["t0"], 2), "t1": round(c["t1"], 2), "lignes": [" ".join(w[0] for w in li) for li in c["lines"]],
                        "rouge": [w[0] for li in c["lines"] for w in li if w[2]]} for c in CARDS],
            "video": vid,
            "audio": [{"id": "mix", "clip": "C5-mix.wav", "folder": "genC5", "path": OUT + "C5-mix.wav", "rec": 0, "track": 1,
                       "note": "mix -14 LUFS : voix citation %.2f-%.2f s (fondu 60 ms) + musique complet %.2f-%.2f s, couplet -9 dB sous la voix, plein à 6,95 s, fondu de fin 1,1 s" % (V0, VOUT, C_OFF, C_OFF + END)}]}
    json.dump(plan, open(D + "plan-C5.json", "w"), indent=1, ensure_ascii=False)

# ---------------- aperçu ffmpeg 540×960 ----------------
def preview():
    out = HK + "/preview/apercu-C5.mp4"; args = [FF, "-v", "error", "-y"]; fl = []
    for i, sh in enumerate(SHOTS):
        args += ["-i", OUT + sh["clip"]]
        fl.append("[%d:v]setpts=(PTS-STARTPTS)/%.4f,fps=30,trim=end_frame=%d,setpts=PTS-STARTPTS,scale=540:960,setsar=1%s[v%d]" % (
            i, sh["sp"] / 100, sh["dur"], ",fade=t=out:st=%.3f:d=%.2f" % (sh["dur"] / 30 - FADE_S, FADE_S) if sh["id"] == FADE_ID else "", i))
    args += ["-i", OUT + "C5-mix.wav"]
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
