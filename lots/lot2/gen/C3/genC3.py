# C3 — Citation ciné, Mélenchon, convention LFI municipales (23/11/2025). Modèle : _claude/gen/3/gen3.py (test 3).
# « La longue marche des insoumis va franchir une étape décisive. Alors, chacun à son poste de combat. »
# Son : VØJ & Narvent — Memory Reboot (fichier complet, départ à 4,71 s pour que la fin de la citation tombe sur le downbeat 15,013 s, début du plateau).
# v1b (Luca aime la v1) : rythme et son inchangés ; seuls B06, B09, B13, B16 remplacés (visages > 5 % de la hauteur au bord du cadre).
# Plans ProRes 9:16 recadrés (visage suivi), sépia lavé + vignette + grain, texte cuit. Ralentis : speed_pct + optical_flow dans plan-C3.json (setpts dans l'aperçu seulement).
# Logos : bounds par source -> le cadre 9:16 n'entre jamais dans les coins à logo (MELENCHON2027.fr, LFI, CONVENTION MUNICIPALES).
# Usage : python genC3.py [plans] [audio] [apercu] [only=ID,ID]
import sys, os, json, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
HK = "/Users/luca.grousset/Movies/highkey-gauchiste"; L2 = HK + "/lot2"
sys.path.insert(0, HK + "/_claude/outils")
from framing import plan_views
from fx import crop_view, vignette, grain, gblur, ease_out
from words import clean
FF = "/opt/homebrew/bin/ffmpeg"
D = L2 + "/_claude/gen/C3/"; OUT = D + "out/"; os.makedirs(OUT, exist_ok=True)
SRC = {k: "C3-melenchon-%s.mp4" % v for k, v in {
    "cit": "convention-citation", "cl01": "clermont-01", "cl02": "clermont-02", "cl03": "clermont-03", "cl04": "clermont-04",
    "cl05": "clermont-05", "cl06": "clermont-06", "cl07": "clermont-07", "cv01": "convention-01", "cv02": "convention-02",
    "cv04": "convention-04", "cv05": "convention-05", "cv06": "convention-06", "cv07": "convention-07"}.items()}
SFPS = 60
REL = "../lot2/sources/"                                   # framing.py lit ROOT/sources/<src>
def bounds(src):                                           # zone source sans logo (le cadre 9:16 y reste)
    if src.startswith("cl"): return (0, 0, 1570, 1080)     # MELENCHON2027.fr : x 1580-1860, y 60-175
    return (355, 0, 1670, 1080)                            # CONVENTION MUNICIPALES x 55-345 ; logo LFI x 1675-1880
W, H, TFPS = 1080, 1920, 30
RED = (228, 0, 43); WHITE = (242, 238, 232)
FONT = "/System/Library/Fonts/Supplemental/Baskerville.ttc"; FIDX = 4
TRACK = 0.20

# ---------------- temps ----------------
MUSIC = L2 + "/sons/C3-voj-narvent-memory-reboot_complet.wav"
M0 = 4.710                                                 # temps du morceau complet à t=0 timeline
PER = 0.83194                                              # 72,1 BPM (sons-lot2.json)
DROP = 15.013 - M0                                         # downbeat 15,013 s du morceau (plateau) = fin de la citation
def tb(j): return DROP + PER * j                           # temps j après le drop (downbeat tous les 4)
END = tb(25)
V = 7.14                                                   # voix : timeline = fichier - V
VIN, VOUT = 7.50, 17.40                                    # extrait voix (s fichier) ; « Vive la nouvelle France » commence à 18,04 -> exclu
def f30(t): return int(round(t * TFPS))

# ---------------- mots (whisper large-v3-turbo sur 7,3-17,6 s ; « la » recalé sur l'attaque à 7,60 s) ----------------
WORDS = [("la", 7.60), ("longue", 7.76), ("marche", 8.18), ("des", 8.66), ("insoumis", 8.88), ("va", 9.50), ("franchir", 10.48),
         ("une", 11.28), ("étape", 11.82), ("décisive.", 12.30), ("Alors,", 14.32), ("chacun", 15.10), ("à", 15.82), ("son", 16.06),
         ("poste", 16.18), ("de", 16.64), ("combat.", 16.74)]
T = [{"w": w, "start": s} for w, s in WORDS]
def up(i): return clean(T[i]["w"], keep_quotes=False).replace("'", "’").upper()
def ts(i): return T[i]["start"] - V
YB, YI = 0.47, 0.70
def card(lines, red, y, em, t1):
    L = [[[up(i), ts(i), i in red] for i in li] for li in lines]
    return {"lines": L, "t0": L[0][0][1], "t1": t1, "y": y, "em": em, "tr": TRACK if y == YB else 0.13}
CARDS = [
    card([[0], [1, 2]], [], YB, 130, ts(3)),               # LA / LONGUE MARCHE (noir)
    card([[3], [4]], [4], YI, 124, ts(5)),                 # DES / INSOUMIS (gros plan, synchro)
    card([[5], [6]], [], YI, 124, ts(7)),                  # VA / FRANCHIR
    card([[7], [8]], [], YI, 124, ts(9)),                  # UNE / ÉTAPE
    card([[9]], [9], YB, 150, ts(10)),                     # DÉCISIVE (noir, rouge)
    card([[10]], [], YI, 124, ts(11)),                     # ALORS
    card([[11], [12, 13, 14]], [], YI, 124, ts(15)),       # CHACUN / À SON POSTE
    card([[15], [16]], [16], YI, 124, DROP),               # DE / COMBAT
]
_fc, _dc = {}, {}
def font(px):
    px = int(round(px))
    if px not in _fc: _fc[px] = ImageFont.truetype(FONT, px, index=FIDX)
    return _fc[px]
DFONT = os.path.expanduser("~/Library/Fonts/CaslonGraphique-Opti.otf"); DSC, DTR = 1.22, 0.03
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
def card_em(c): return min(c["em"], min(0.90 * W / (line_w(li, 100, c["tr"]) / 100) for li in c["lines"]))
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

# ---------------- étalonnage sépia lavé (identique au test 3) ----------------
TINT = np.array([0.93, 1.0, 1.05], np.float32); VIG = None
def grade(img):
    global VIG
    y = img @ np.array([0.114, 0.587, 0.299], np.float32)
    x = np.clip(y[..., None] * 0.84 + img * 0.16, 0, 1); x = x * x * (3 - 2 * x) * 0.55 + x * 0.45
    x = gblur((0.055 + x * 0.83) * TINT, 0.8)
    if VIG is None: VIG = vignette(np.ones((H, W, 3), np.float32), strength=0.62, power=2.0)
    return grain(x * VIG, 0.028, 1.6)

# ---------------- plans ----------------
def S(i, a, b, src, t_in, sp, mode, hint, z0, z1, txt=False, note=""):
    return dict(id=i, a=a, b=b, src=src, t_in=t_in, sp=sp, mode=mode, hint=hint, z0=z0, z1=z1, txt=txt, note=note)
GP = (1150, 360)                                           # gros plan convention (fond violet)
SHOTS = [
    S("Q1", 0.0, ts(3), None, None, 100, "noir", None, 1, 1, True, "LA LONGUE MARCHE sur noir"),
    S("Q2", ts(3), ts(9), "cit", T[3]["start"], 100, "face", GP, 1.14, 1.22, True, "gros plan convention, synchro labiale (des insoumis va franchir une étape)"),
    S("Q3", ts(9), ts(10), None, None, 100, "noir", None, 1, 1, True, "DÉCISIVE rouge sur noir"),
    S("Q4", ts(10), DROP, "cit", T[10]["start"], 100, "face", GP, 1.22, 1.32, True, "gros plan serré, synchro (alors, chacun à son poste de combat)"),
    S("B01", tb(0), tb(2), "cl02", 0.6, 50, "fix", (1250, 540), 1.0, 1.06, note="Clermont, arena pleine vue aérienne, projecteurs"),
    S("B02", tb(2), tb(3), "cv01", 4.4, 50, "face", (1100, 330), 1.05, 1.10, note="Convention, Mélenchon lève le bras"),
    S("B03", tb(3), tb(5), "cl01", 1.0, 50, "fix", (700, 540), 1.0, 1.06, note="Clermont, tribunes pleines en plongée"),
    S("B04", tb(5), tb(6), "cl03", 0.8, 50, "face", (900, 300), 1.05, 1.10, note="Clermont, Mélenchon au pupitre poing levé"),
    S("B05", tb(6), tb(8), "cv05", 1.0, 50, "fix", (960, 540), 1.0, 1.06, note="Convention, salle immense vue du fond"),
    S("B06", tb(8), tb(9), "cl02", 2.6, 50, "fix", (700, 540), 1.0, 1.05, note="Clermont, arena pleine vue aérienne, côté gauche (remplace les jeunes : visages au bord)"),
    S("B07", tb(9), tb(11), "cv04", 1.0, 50, "fix", (1000, 540), 1.0, 1.06, note="Convention, scène large, militants debout"),
    S("B08", tb(11), tb(12), "cl04", 2.0, 50, "face", (900, 300), 1.08, 1.12, note="Clermont, Mélenchon sourit au pupitre"),
    S("B09", tb(12), tb(14), "cl01", 4.0, 50, "fix", (1150, 540), 1.0, 1.06, note="Clermont, tribunes pleines, autre zone (remplace la foule de près : visages au bord)"),
    S("B10", tb(14), tb(15), "cv02", 2.0, 50, "face", (980, 330), 1.08, 1.12, note="Convention, Mélenchon parle"),
    S("B11", tb(15), tb(17), "cl06", 1.0, 50, "fix", (960, 540), 1.0, 1.05, note="Clermont, scène CLERMONT-FERRAND, public au premier plan"),
    S("B12", tb(17), tb(18), "cit", 0.8, 50, "face", (580, 330), 1.0, 1.04, note="Convention, Mélenchon au pupitre, militants qui applaudissent"),
    S("B13", tb(18), tb(20), "cit", 4.5, 50, "fix", (1000, 540), 1.0, 1.06, note="Convention, salle pleine de côté (remplace équipe + foule : visages au bord)"),
    S("B14", tb(20), tb(21), "cl03", 3.5, 50, "face", (900, 300), 1.08, 1.12, note="Clermont, Mélenchon poing serré"),
    S("B15", tb(21), tb(22), "cv01", 1.0, 50, "face", (1100, 330), 1.05, 1.09, note="Convention, Mélenchon doigt levé"),
    S("B16", tb(22), END, "cit", 1.6, 50, "face", (580, 330), 1.0, 1.08, note="Convention, Mélenchon au pupitre, militants qui applaudissent, fondu au noir (remplace l'équipe : visages au bord)"),
]
for sh in SHOTS:
    sh["rec"] = f30(sh["a"]); sh["dur"] = f30(sh["b"]) - sh["rec"]
    sh["fps"] = SFPS if sh["src"] else TFPS
    sh["n"] = int(round(sh["dur"] / TFPS * sh["fps"]))      # images source à vitesse NORMALE (règle LISEZMOI)
    sh["clip"] = "C3_%s.mov" % sh["id"]

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
            t = sh["a"] + k / fps
            img = draw_text(grain(np.zeros((H, W, 3), np.float32) + 0.012, 0.012, 1.6), t, False)
            w.stdin.write((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8).tobytes())
    else:
        s = int(round(sh["t_in"] * fps)); z0, z1 = sh["z0"], sh["z1"]; bd = bounds(sh["src"])
        zoom = lambda f: z0 + (z1 - z0) * f / max(n - 1, 1)
        kw = dict(speed=1.0, hint=sh["hint"], bounds=bd, vh=1080, zoom=zoom)
        if sh["mode"] == "fix": kw["fixed"] = sh["hint"]
        views, ok = plan_views(REL + SRC[sh["src"]], s, n, fps, **kw)
        if sh["mode"] == "face": info = "visage" if ok else "SANS VISAGE"
        xs = [v[0] - v[2] * 9 / 32 for v in views] + [v[0] + v[2] * 9 / 32 for v in views]
        info += " x %d-%d (bornes %d-%d)" % (min(xs), max(xs), bd[0], bd[2])
        k = 0
        for fr in read_frames(sh["src"], s / fps, n):
            cx, cy, vh = views[min(k, len(views) - 1)]
            img = grade(crop_view(fr.astype(np.float32) / 255, cx, cy, vh * 9 / 16, W, H))
            if sh["txt"]: img = draw_text(img, sh["a"] + k / fps, True)
            w.stdin.write((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8).tobytes()); k += 1
        if k < n: info += " court:%d/%d" % (k, n)
    w.stdin.close(); w.wait()
    return info

# ---------------- audio ----------------
SR = 48000
def load(path, t=0.0, d=None):
    cmd = [FF, "-v", "error", "-ss", "%.4f" % t, "-i", path] + (["-t", "%.4f" % d] if d else []) + ["-f", "f32le", "-ac", "2", "-ar", str(SR), "-"]
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
    from scipy.signal import butter, sosfilt
    n = int(END * SR); t = np.arange(n) / SR
    voice = fade(load(L2 + "/sources/" + SRC["cit"], VIN, VOUT - VIN), 0.03, 0.12)
    mus = load(MUSIC, M0, END + 0.05)[:n]
    lv, _ = lufs(voice); lm, _ = lufs(load(MUSIC, 15.0, 20.0))          # musique mesurée sur le plateau
    voice *= db(-15 - lv); mus *= db(-14 - lm)
    # sous la voix : musique passe-bas + -10 dB, ouverture pleine bande au downbeat de la fin de citation (effet de drop)
    lp = sosfilt(butter(4, 500, "low", fs=SR, output="sos"), mus, axis=0).astype(np.float32)
    x = np.clip((t - (DROP - 0.25)) / 0.25, 0, 1)[:, None].astype(np.float32)   # 0 = filtré, 1 = plein
    g = (db(-10) + (1 - db(-10)) * x).astype(np.float32)
    fo = np.clip((END - t) / 1.1, 0, 1) ** 1.5; g = g * fo[:, None].astype(np.float32)
    mix = (lp * (1 - x) + mus * x) * g
    i = int(round((VIN - V) * SR)); mix[i:i + len(voice)] += voice[:n - i]
    tmp = OUT + "_tmp_mix.wav"; sf_write(tmp, mix); gain = 0.0; li, _ = lufs(mix)
    for _ in range(3):
        gain += -14.0 - li
        subprocess.run([FF, "-v", "error", "-y", "-i", tmp, "-af", "volume=%.2fdB,alimiter=limit=0.80:attack=3:release=60:level=false,aresample=192000,alimiter=limit=0.82:attack=1:release=40:level=false,aresample=48000" % gain,
                        "-c:a", "pcm_s24le", OUT + "C3-mix.wav"], check=True)
        li, tp = lufs(load(OUT + "C3-mix.wav"))
        if abs(li + 14) < 0.3 and tp < -1.0: break
    os.remove(tmp)
    sf_write(OUT + "C3-voix.wav", voice)
    return "mix %.1f LUFS, true peak %.1f dBTP (voix %.1f, musique plateau %.1f d'origine)" % (li, tp, lv, lm)

# ---------------- plan-C3.json ----------------
def write_plan():
    vid = []
    for sh in SHOTS:
        it = {"id": sh["id"], "clip": sh["clip"], "folder": "genC3", "path": OUT + sh["clip"], "s": 0, "e": sh["n"], "clip_fps": sh["fps"],
              "rec": sh["rec"], "dur": sh["dur"], "track": 1, "note": sh["note"]}
        if sh["src"]:
            sp = sh["sp"]; used = sh["n"] * sp / 100 / sh["fps"]
            it["source"] = {"fichier": "lot2/sources/" + SRC[sh["src"]], "in_s": round(sh["t_in"], 3), "out_s": round(sh["t_in"] + used, 3)}
            it["effets"] = "recadrage 9:16 %s, zoom %.2f->%.2f, sépia lavé + vignette + grain%s" % (
                "suivi visage" if sh["mode"] == "face" else "fixe", sh["z0"], sh["z1"], ", texte cuit" if sh["txt"] else "")
            if sp != 100: it["speed_pct"] = sp; it["retime"] = "optical_flow"
        else:
            it["effets"] = "noir + grain, texte cuit (Baskerville SemiBold approche 0,20 em ; mot rouge CaslonGraphique-Opti)"
        if sh["id"] == SHOTS[-1]["id"]: it["fade_out_s"] = 0.7
        vid.append(it)
    plan = {"name": "C3 - Citation cine Melenchon convention", "fps": 30, "w": 1080, "h": 1920, "duree_s": round(END, 3),
            "citation": " ".join(w for w, _ in WORDS), "source_citation": "lot2/sources/" + SRC["cit"] + " %.2f-%.2f s (discours 23/11/2025, YouTube Yc46p2zQZxY ~1640 s)" % (VIN, VOUT),
            "note": "Plans ProRes 9:16 (recadrés, étalonnés, texte cuit), sources 60 i/s. Ralentis à faire dans Resolve : speed_pct + Optical Flow ; e-s = images source à vitesse normale. Générateur : lot2/_claude/gen/C3/genC3.py",
            "musique": {"fichier": "lot2/sons/C3-voj-narvent-memory-reboot_complet.wav", "titre": "VØJ & Narvent - Memory Reboot", "depart_dans_complet_s": M0,
                        "depart_dans_extrait_s": round(M0 - 2.25, 3), "drop_timeline_s": round(DROP, 3), "bpm": 72.1,
                        "beats_timeline_s": [round(tb(j), 3) for j in range(26)]},
            "textes": [{"t0": round(c["t0"], 2), "t1": round(c["t1"], 2), "lignes": [" ".join(w[0] for w in li) for li in c["lines"]],
                        "rouge": [w[0] for li in c["lines"] for w in li if w[2]]} for c in CARDS],
            "video": vid,
            "audio": [{"id": "mix", "clip": "C3-mix.wav", "folder": "genC3", "path": OUT + "C3-mix.wav", "rec": 0, "track": 1,
                       "note": "mix -14 LUFS : voix %.2f-%.2f s du fichier citation à %.2f s timeline, musique passe-bas -10 dB sous la voix, pleine au drop %.2f s, fondu 1,1 s" % (VIN, VOUT, VIN - V, DROP)}]}
    json.dump(plan, open(D + "plan-C3.json", "w"), indent=1, ensure_ascii=False)

def preview():
    out = L2 + "/exports/apercu-C3.mp4"; args = [FF, "-v", "error", "-y"]; fl = []
    for i, sh in enumerate(SHOTS):
        args += ["-i", OUT + sh["clip"]]
        last = sh["id"] == SHOTS[-1]["id"]
        fl.append("[%d:v]setpts=(PTS-STARTPTS)/%.4f,fps=30,trim=end_frame=%d,setpts=PTS-STARTPTS,scale=540:960,setsar=1%s[v%d]" % (
            i, sh["sp"] / 100, sh["dur"], ",fade=t=out:st=%.3f:d=0.7" % (sh["dur"] / 30 - 0.7) if last else "", i))
    args += ["-i", OUT + "C3-mix.wav"]
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
            print(sh["id"], sh["dur"], "img tl", sh["n"], "img src", render(sh), flush=True)
    if "audio" in sys.argv: print(build_audio())
    write_plan()
    if "apercu" in sys.argv: print(preview())
    print("total %.2f s ; %d plans ; drop %.2f s" % (sum(s["dur"] for s in SHOTS) / 30, len(SHOTS), DROP))
