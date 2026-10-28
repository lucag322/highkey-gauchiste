# Lot 5 / I1 — Phonk infographie (DA n° 5, réf @nvidia.rtx.2060), Jean-Luc Mélenchon, son Kordhell « Live Another Day ».
# Phrase (meeting de Saint-Denis, 7 juin 2026, chaîne officielle JEAN-LUC MÉLENCHON, https://www.youtube.com/watch?v=1dkY_JVFx9I&t=3102) :
#   « Nous réparerons les dégâts, le SMIC passera à 1 700 euros »  (la phrase continue « et nous créerons une sécurité sociale intégrale… » : coupée
#   après « euros », sans changer le sens). NB : le brief disait 1 600 € net ; Mélenchon dit 1 700 euros (vérifié Whisper + transcription lot 2).
# Structure (réf) : la figure annonce la mesure (voix + sous-titres mot à mot), insert hologramme « SMIC -> 1 700 € » sur « 1 700 euros »,
# drop sur le retour du 808 après le roulement (50,08 s du morceau), B-roll du meeting + étiquettes de données + 2e insert (colonnes SMIC net / 1 700 €).
# Sous la voix : seulement des plans où il ne parle pas (muet pendant les applaudissements, de dos, foule) ou l'insert (règle Luca 27/10).
# Couleurs naturelles (léger contraste), 12-14 coupes / 10 s, coupes sur les frappes mesurées. Ralentis : aucun.
# Usage : python genI1.py [plans] [audio] [apercu] [only=ID,ID]
import sys, os, json, subprocess
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
HK = "/Users/luca.grousset/Movies/highkey-gauchiste"
D = HK + "/lot5/_claude/gen/I1/"; OUT = D + "out/"; os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, HK + "/_claude/outils"); sys.path.insert(0, D)
import framing
framing.ROOT = HK; framing.CACHE = D + "cache/faces"     # src = "../lotN/sources/x.mp4" -> cache sous I1/cache (rien écrit dans les lots 1-4)
from framing import plan_views
from fx import crop_view, vignette, grain, gblur, ease_out, rgb_split, motion_blur
import hudI1
FF = "/opt/homebrew/bin/ffmpeg"
W, H, TFPS = 1080, 1920, 30
def f30(t): return int(round(t * TFPS))

# ---------------- sources (toutes 1080p 30 i/s, chaîne officielle JLM, meeting Saint-Denis 7/06/2026 ; intersyndicale) ----------------
SRC = {"SD": "../lot1/sources/5-melenchon-saintdenis-smic.mp4",          # = 1dkY_JVFx9I 3000-3240 s
       "IS": "../lot3/sources/C4-melenchon-intersyndicale.mp4"}
for i in range(1, 9): SRC["SD%d" % i] = "../lot3/sources/C4-melenchon-stdenis-0%d.mp4" % i
B_CU = (0, 0, 1570, 800)      # gros plans : filigrane MELENCHON2027.fr (x > 1590, y < 170) et pupitre « SAINT-DENIS » (y > 800) exclus
B_WIDE = (0, 175, 1570, 1080) # plans larges : sous et à gauche du filigrane
B_FULL = (0, 0, 1570, 1080)
B_IS = (0, 175, 1570, 880)    # intersyndicale : filigrane et pancartes syndicales du premier rang (texte) exclus

# ---------------- voix (mots : Whisper large-v3-turbo, débuts recalés sur l'énergie 150-4000 Hz) ----------------
YT_OFF = 3000.0               # le fichier SD commence à 3000 s de la vidéo YouTube
V_IN, V_OUT = 102.30, 108.10  # « Nous » … fin de « euros »
T0 = 0.15                     # la voix démarre à 0,15 s
OFF = V_IN - T0               # timeline = source - OFF
WORDS = [("NOUS", 102.40), ("RÉPARERONS", 102.62), ("LES", 103.70), ("DÉGÂTS", 103.95), ("LE", 105.30), ("SMIC", 105.42),
         ("PASSERA", 105.78), ("À", 106.45), ("1 700", 106.78), ("EUROS", 107.55)]
TEXTE = "Nous réparerons les dégâts, le SMIC passera à 1 700 euros"
def wt(i): return WORDS[i][1] - OFF

# ---------------- musique : drop = retour du 808 après le roulement (morceau complet) ----------------
MUSIC = HK + "/lot5/sons/I1-kordhell-live-another-day_complet.wav"
SR = 48000
def _music_mono():
    import soundfile as sf
    y, sr = sf.read(MUSIC); return y.mean(1).astype(np.float32), sr
M_DROP_GRID = 50.083; BEAT = 0.5217                       # 115,0 BPM (charleston/cloche mesurés 43-61 s)
def measure_hits():
    """frappe réelle la plus forte (flux spectral graves + bas-médium + aigus) à ±40 ms de chaque temps de la grille, b-13 … b+16."""
    import librosa
    y, sr = _music_mono(); a0 = 42.0
    S = np.abs(librosa.stft(y[int(a0 * sr):int(60 * sr)], n_fft=1024, hop_length=128)); f = librosa.fft_frequencies(sr=sr, n_fft=1024)
    def flux(m):
        L = np.log1p(100 * S[m]); d = np.maximum(0, np.diff(L, axis=1)).sum(0); return d / np.percentile(d, 99)
    x = flux(f < 150) + flux((f > 150) & (f < 600)) + flux(f > 6000); t = a0 + (np.arange(len(x)) + 1) * 128 / sr
    hits = {}
    for k in range(-13, 17):
        g = M_DROP_GRID + k * BEAT; m = (t > g - 0.04) & (t < g + 0.04); hits[k] = round(float(t[m][np.argmax(x[m])]), 3)
    return hits
HITS_FILE = D + "hits.json"
if not os.path.exists(HITS_FILE): json.dump({str(k): v for k, v in measure_hits().items()}, open(HITS_FILE, "w"), indent=0)
HITS = {int(k): v for k, v in json.load(open(HITS_FILE)).items()}
DROP = 6.0
C_OFF = HITS[0] - DROP        # musique : timeline = complet - C_OFF
RECALE = D + "hits_mix.json"   # frappes re-mesurées dans le mix posé (voix + ducking), même mesure que verif_coupes.py ; 0 et 16 restent ceux du morceau
MIXHITS = {int(k): v for k, v in json.load(open(RECALE)).items()} if os.path.exists(RECALE) else {}
def hb(k):                                            # temps timeline de la frappe du temps k
    return MIXHITS.get(k, HITS[k] - C_OFF) if k not in (0, 16) else HITS[k] - C_OFF
def recale():
    import librosa, soundfile as sf
    a, sr = sf.read(OUT + "I1-mix.wav"); a = a.mean(1).astype(np.float32)
    S = np.abs(librosa.stft(a, n_fft=1024, hop_length=128)); f = librosa.fft_frequencies(sr=sr, n_fft=1024)
    def flux(m):
        L = np.log1p(100 * S[m]); dd = np.maximum(0, np.diff(L, axis=1)).sum(0); return dd / np.percentile(dd, 99)
    x = flux(f < 150) + flux((f > 150) & (f < 600)) + flux(f > 6000); t = (np.arange(len(x)) + 1) * 128 / sr
    out = {}
    for k in HITS:
        g = HITS[k] - C_OFF
        if g < 0.1 or k in (0, 16): continue
        m = (t > g - 0.06) & (t < g + 0.06); out[k] = round(float(t[m][np.argmax(x[m])]), 3)
    json.dump(out, open(RECALE, "w"), indent=0); return out
END = hb(16)

# ---------------- sous-titres pendant la voix (DIN Condensed, blanc, mot-clé rouge #E4002B) ----------------
FCAP = "/System/Library/Fonts/Supplemental/DIN Condensed Bold.ttf"
RED = (228, 0, 43); WHITE = (250, 250, 250)
CAPS = [([0, 1], wt(2)), ([2, 3], wt(4)), ([4, 5], wt(6)), ([6, 7], hb(-3))]   # groupes de mots (fin = début du groupe suivant)
KEY = {5}                     # SMIC en rouge
YCAP = 0.635; CAP_EM = 175; CAP_W = 0.62
_fc = {}
def font(px):
    px = int(round(px))
    if px not in _fc: _fc[px] = ImageFont.truetype(FCAP, px)
    return _fc[px]
def draw_caps(img, t):
    act = [c for c in CAPS if wt(c[0][0]) - 1e-3 <= t < c[1]]
    if not act: return img
    idx = act[0][0]; em = CAP_EM
    while True:
        f = font(em); sp = f.getlength(" "); tot = sum(f.getlength(WORDS[i][0]) for i in idx) + sp * (len(idx) - 1)
        if tot <= CAP_W * W: break
        em -= 5
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dr = ImageDraw.Draw(layer); sh = Image.new("L", (W, H), 0); ds = ImageDraw.Draw(sh)
    x = W / 2 - tot / 2; y = YCAP * H
    for i in idx:
        wd = WORDS[i][0]; ww = f.getlength(wd)
        if wt(i) <= t + 1e-3:
            k = (t - wt(i)) * TFPS; sc = 1 + 0.18 * (1 - ease_out(k / 4))           # entrée 4 images, sans rebond
            fs = font(em * sc)
            dr.text((x + ww / 2, y), wd, font=fs, fill=(RED if i in KEY else WHITE) + (255,), anchor="mm", stroke_width=9, stroke_fill=(0, 0, 0, 255))
            ds.text((x + ww / 2 + 5, y + 8), wd, font=fs, fill=190, anchor="mm", stroke_width=14)
        x += ww + sp
    m = np.asarray(sh.filter(ImageFilter.GaussianBlur(10)), np.float32)[..., None] / 255
    out = img * (1 - 0.6 * m)
    lay = np.asarray(layer, np.float32) / 255
    return out * (1 - lay[..., 3:4]) + lay[..., [2, 1, 0]] * lay[..., 3:4]

# ---------------- étalonnage : couleurs naturelles, un peu de punch (prototype gen5) ----------------
VIG = None
def grade(img):
    global VIG
    s = img * img * (3 - 2 * img); img = img * 0.68 + s * 0.32
    g = img.mean(axis=2, keepdims=True); img = g + (img - g) * 1.10
    img = img + 0.35 * (img - gblur(img, 1.6))
    if VIG is None: VIG = vignette(np.ones((H, W, 3), np.float32), strength=0.30, power=2.4)
    return grain(np.clip(img, 0, 1) * VIG, 0.012)

# ---------------- plans ----------------
def S(i, a, b, src, t_in, mode, hint, z0, z1, bounds=B_WIDE, note="", lab=None, hud=None):
    return dict(id=i, a=a, b=b, src=src, t_in=t_in, mode=mode, hint=hint, z0=z0, z1=z1, bounds=bounds, note=note, lab=lab, hud=hud)
LAB_SD = ("SAINT-DENIS", "MEETING - 7 JUIN 2026", 0.17 * H, (330, 1180))
LAB_PAUV = ("10 MILLIONS", "DANS LA PAUVRETÉ - J.-L. MÉLENCHON, 07/06/2026", 0.15 * H, (700, 1250))
LAB_AIDE = ("7 MILLIONS", "À L'AIDE ALIMENTAIRE - J.-L. MÉLENCHON, 07/06/2026", 0.15 * H, (380, 1280))
LAB_FIN = ("SMIC À 1 700 €", "J.-L. MÉLENCHON - SAINT-DENIS - 07/06/2026", 0.15 * H, (520, 1120))
SHOTS = [
    # --- la figure annonce la mesure (voix + sous-titres)
    S("V1", 0.0, hb(-10), "SD", 96.05, "face", (930, 300), 1.00, 1.02, B_CU, "Mélenchon au pupitre pendant les applaudissements (muet), NOUS"),
    S("V2", hb(-10), hb(-8), "SD", 166.0, "fix", (900, 640), 1.00, 1.03, B_WIDE, "place de Saint-Denis noire de monde, hôtel de ville, RÉPARERONS / LES"),
    S("V2b", hb(-8), hb(-6), "SD3", 1.0, "fix", (900, 640), 1.00, 1.03, B_WIDE, "place de Saint-Denis, arbres, foule, DÉGÂTS"),
    S("V3", hb(-6), hb(-5), "SD", 126.0, "fix", (950, 620), 1.00, 1.02, B_WIDE, "Mélenchon de dos face à la foule, LE SMIC"),
    S("V4", hb(-5), hb(-4), "SD", 109.0, "fix", (700, 560), 1.00, 1.02, B_WIDE, "drapeaux dans la foule (image synchrone de la phrase, 7 s plus loin), PASSERA"),
    S("V5", hb(-4), hb(-3), "SD", 203.0, "fix", (900, 600), 1.00, 1.02, B_WIDE, "foule, arbres, place de Saint-Denis (pas de plan où il parle sous sa voix), À (début du roulement)"),
    S("HUD1", hb(-3), DROP, None, None, "hud", None, 1, 1, note="insert hologramme : pièce € filaire, étiquette SMIC, 1 700 € rouge sur « 1 700 euros »", hud=1),
    # --- drop : B-roll + étiquettes + 2e insert
    S("D1", hb(0), hb(1), "SD8", 5.0, "fix", (700, 560), 1.00, 1.06, B_FULL, "DROP : drapeau Union populaire qui balaie l'image"),
    S("D2", hb(1), hb(2), "SD2", 6.2, "face", (930, 300), 1.00, 1.04, B_CU, "Mélenchon main levée"),
    S("D3", hb(2), hb(3), "IS", 155.0, "fix", (900, 560), 1.00, 1.05, B_IS, "intersyndicale : foule, drapeaux violets", LAB_PAUV),
    S("D4", hb(3), hb(4), "SD8", 7.3, "fix", (960, 560), 1.00, 1.03, B_FULL, "drapeaux tricolores et violets agités"),
    S("D5", hb(4), hb(6), "SD2", 11.0, "fix", (900, 600), 1.00, 1.05, B_WIDE, "basilique de Saint-Denis", LAB_SD),
    S("D6", hb(6), hb(7), "SD3", 29.0, "face", (930, 300), 1.00, 1.04, B_CU, "Mélenchon au pupitre, gros plan"),
    S("D7", hb(7), hb(8), "SD", 99.5, "fix", (900, 600), 1.00, 1.05, B_WIDE, "place noire de monde devant la basilique"),
    S("D8", hb(8), hb(9), "IS", 160.0, "fix", (800, 520), 1.00, 1.05, B_IS, "intersyndicale : foule", LAB_AIDE),
    S("HUD2", hb(9), hb(11), None, None, "hud", None, 1, 1, note="insert hologramme : colonnes SMIC net 1 477,93 € / 1 700 €", hud=2),
    S("D9", hb(11), hb(12), "SD5", 0.2, "fix", (960, 560), 1.00, 1.05, B_FULL, "foule et drapeaux devant la tribune"),
    S("D10", hb(12), hb(13), "SD1", 16.5, "fix", (900, 640), 1.00, 1.05, B_WIDE, "place de Saint-Denis vue large"),
    S("D11", hb(13), hb(14), "SD", 138.5, "fix", (900, 600), 1.00, 1.05, B_WIDE, "place de l'hôtel de ville noire de monde"),
    S("D12", hb(14), END, "SD", 128.5, "fix", (950, 620), 1.00, 1.05, B_WIDE, "FIN : Mélenchon de dos face à la foule immense", LAB_FIN),
]
for sh in SHOTS:
    sh["rec"] = f30(sh["a"]); sh["dur"] = f30(sh["b"]) - sh["rec"]; sh["fps"] = TFPS; sh["n"] = sh["dur"]
    sh["clip"] = "I1_%s.mov" % sh["id"]

def read_frames(src, t, n):
    p = subprocess.Popen([FF, "-v", "error", "-ss", "%.4f" % t, "-i", os.path.normpath(HK + "/sources/" + SRC[src]), "-frames:v", str(n),
                          "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE)
    sz = 1920 * 1080 * 3
    for _ in range(n):
        b = p.stdout.read(sz)
        if len(b) < sz: break
        yield np.frombuffer(b, np.uint8).reshape(1080, 1920, 3)
    p.stdout.close(); p.wait()
def writer(path):
    return subprocess.Popen([FF, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", "%dx%d" % (W, H), "-r", "30", "-i", "-",
                             "-c:v", "prores_ks", "-profile:v", "3", "-pix_fmt", "yuv422p10le", "-vendor", "apl0", path], stdin=subprocess.PIPE)
def render(sh):
    n = sh["n"]; w = writer(OUT + sh["clip"]); info = ""
    if sh["mode"] == "hud":
        for k in range(n):
            t = sh["a"] + k / TFPS
            img = hudI1.hud1(k, n, max(0, f30(wt(8)) - sh["rec"])) if sh["hud"] == 1 else hudI1.hud2(k, n)
            if sh["hud"] == 1 and k in (0, 1): img = rgb_split(img, 8 if k == 0 else 4)
            w.stdin.write((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8).tobytes())
    else:
        s = int(round(sh["t_in"] * TFPS)); z0, z1 = sh["z0"], sh["z1"]; bd = sh["bounds"]
        zoom = lambda f: z0 + (z1 - z0) * f / max(n - 1, 1)
        vh = min(1080, bd[3] - bd[1], (bd[2] - bd[0]) * 16 / 9)
        if sh["mode"] == "face":
            views, ok = plan_views(SRC[sh["src"]], s, n, TFPS, speed=1.0, hint=sh["hint"], bounds=bd, vh=vh, zoom=zoom)
            info = "visage" if ok else "SANS VISAGE"
        else:
            views, ok = plan_views(SRC[sh["src"]], s, n, TFPS, speed=1.0, hint=sh["hint"], bounds=bd, vh=vh, zoom=zoom, fixed=sh["hint"])
        k = 0; vmin = 9e9
        for fr in read_frames(sh["src"], s / TFPS, n):
            cx, cy, v = views[min(k, len(views) - 1)]; vw = v * 9 / 16; vmin = min(vmin, v)
            assert bd[0] - 1 <= cx - vw / 2 and cx + vw / 2 <= bd[2] + 1 and bd[1] - 1 <= cy - v / 2 and cy + v / 2 <= bd[3] + 1, (sh["id"], k, cx, cy, v)
            img = crop_view(fr.astype(np.float32) / 255, cx, cy, vw, W, H)
            img = grade(img)
            if sh["a"] >= DROP - 1e-6 and k < 2:                         # impact phonk sur la frappe : décalage RVB 2 images, sans flash
                img = rgb_split(img, 7 if k == 0 else 3)
            if sh["a"] < DROP: img = draw_caps(img, sh["a"] + k / TFPS)
            if sh["lab"]:
                ttl, sub, by, dot = sh["lab"]; img = hudI1.label(img, k, ttl, sub, int(by), dot, red_title=("1 700" in ttl))
            w.stdin.write((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8).tobytes()); k += 1
        info += " vue min %d px (agrandi x%.2f)" % (vmin, 1920 / vmin)
        if k < n: info += " court:%d/%d" % (k, n)
    w.stdin.close(); w.wait()
    return info

# ---------------- audio ----------------
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
VEND = V_OUT - OFF
def build_audio():
    n = int(round(END * SR)); mix = np.zeros((n, 2), np.float32)
    v = fade(load(os.path.normpath(HK + "/sources/" + SRC["SD"]), V_IN, V_OUT - V_IN), 0.04, 0.06)
    mus = load(MUSIC, C_OFF, END + 0.05)[:n]
    lv, _ = lufs(v); lm, _ = lufs(mus[int(DROP * SR):])
    v *= db(-14 - lv); mus *= db(-14 - lm)                       # voix -14 LUFS ; musique après le drop -14 LUFS
    t = np.arange(len(mus)) / SR
    R0 = hb(-4)                                                   # début du roulement (basse coupée) : montée sous « passera à 1 700 euros »
    env = np.full(len(t), db(-11), np.float32)
    r = (t >= R0) & (t < VEND); env[r] = db(-11 + 4 * (t[r] - R0) / (VEND - R0))
    r = (t >= VEND) & (t < DROP); env[r] = db(-7 + 7 * (t[r] - VEND) / max(DROP - VEND, 1e-3))
    env[t >= DROP] = 1.0
    env *= np.clip(t / 0.25, 0, 1)                                # entrée 0,25 s
    env *= np.where(t > END - 0.35, np.clip((END - t) / 0.35, 0, 1), 1)   # fin : 0,35 s sur la dernière frappe
    mix[:len(mus)] += mus * env[:, None]
    i0 = int(T0 * SR); mix[i0:i0 + len(v)] += v[:n - i0]
    tmp = OUT + "_tmp_mix.wav"; sf_write(tmp, mix); g = 0.0; li2 = None
    for _ in range(5):
        li = lufs(mix)[0] if li2 is None else li2
        g += -14.0 - li
        subprocess.run([FF, "-v", "error", "-y", "-i", tmp, "-af", "volume=%.2fdB,alimiter=limit=0.80:attack=3:release=60:level=false,aresample=192000,alimiter=limit=0.82:attack=1:release=40:level=false,aresample=48000" % g,
                        "-c:a", "pcm_s24le", OUT + "I1-mix.wav"], check=True)
        li2, tp2 = lufs(load(OUT + "I1-mix.wav"))
        if abs(li2 + 14) < 0.3 and tp2 < -1.0: break
    os.remove(tmp)
    return "mix %.1f LUFS, true peak %.1f dBTP (voix %.1f, musique %.1f d'origine)" % (li2, tp2, lv, lm)

# ---------------- plan-I1.json + son.json ----------------
def write_plan():
    vid = []
    for sh in SHOTS:
        it = {"id": sh["id"], "clip": sh["clip"], "folder": "genI1", "path": OUT + sh["clip"], "s": 0, "e": sh["n"], "clip_fps": 30,
              "rec": sh["rec"], "dur": sh["dur"], "track": 1, "speed_pct": 100, "note": sh["note"]}
        if sh["src"]:
            it["source"] = {"fichier": os.path.normpath("sources/" + SRC[sh["src"]]), "in_s": round(sh["t_in"], 3), "out_s": round(sh["t_in"] + sh["n"] / 30, 3)}
            it["effets"] = "recadrage 9:16 %s (bornes %s), poussée %.2f->%.2f, couleurs naturelles + grain%s%s%s" % (
                "suivi visage" if sh["mode"] == "face" else "fixe", list(sh["bounds"]), sh["z0"], sh["z1"],
                ", sous-titres cuits" if sh["a"] < DROP else "", ", étiquette « %s / %s »" % (sh["lab"][0], sh["lab"][1]) if sh["lab"] else "",
                ", décalage RVB 2 images sur la frappe" if sh["a"] >= DROP else "")
        else:
            it["effets"] = "insert hologramme généré (hudI1.py), teal #3FD6D0 + chiffre rouge #E4002B"
        vid.append(it)
    plan = {"name": "I1 - Phonk infographie - Melenchon - SMIC 1 700 € - Kordhell Live Another Day", "fps": 30, "w": 1080, "h": 1920, "duree_s": round(END, 3),
            "note": "Plans ProRes 9:16 prêts (recadrés hors filigrane et pupitre, étalonnés, textes et étiquettes cuits). Aucun ralenti. Générateur : lot5/_claude/gen/I1/genI1.py",
            "phrase": {"texte": TEXTE, "fichier": os.path.normpath("sources/" + SRC["SD"]), "in_s": V_IN, "out_s": V_OUT,
                       "source_url": "https://www.youtube.com/watch?v=1dkY_JVFx9I&t=%d" % (YT_OFF + V_IN), "source_temps_s": [YT_OFF + V_IN, YT_OFF + V_OUT]},
            "chiffres": [{"valeur": "1 700 €", "source": "J.-L. Mélenchon, meeting de Saint-Denis, 7/06/2026 (phrase ci-dessus)"},
                         {"valeur": "1 477,93 € (SMIC net mensuel 35 h)", "source": "service-public.gouv.fr/particuliers/vosdroits/F2300 ; arrêté du 22 mai 2026, en vigueur le 1er juin 2026"},
                         {"valeur": "10 millions dans la pauvreté", "source": "J.-L. Mélenchon, même discours, 1dkY_JVFx9I t=3071"},
                         {"valeur": "7 millions à l'aide alimentaire", "source": "J.-L. Mélenchon, même discours, 1dkY_JVFx9I t=3071"}],
            "musique": {"fichier": "lot5/sons/I1-kordhell-live-another-day_complet.wav", "debut_dans_complet_s": round(C_OFF, 3),
                        "drop_timeline_s": DROP, "coupes_timeline_s": [round(s["a"], 3) for s in SHOTS[1:]] + [round(END, 3)]},
            "video": vid,
            "audio": [{"id": "mix", "clip": "I1-mix.wav", "folder": "genI1", "path": OUT + "I1-mix.wav", "rec": 0, "track": 1,
                       "note": "mix -14 LUFS : voix %.2f-%.2f s (posée à %.2f s) + musique complet %.2f-%.2f s, -11 dB sous la voix, montée -11 -> -7 dB sur le roulement, plein au drop, fin 0,35 s" % (V_IN, V_OUT, T0, C_OFF, C_OFF + END)}]}
    json.dump(plan, open(D + "plan-I1.json", "w"), indent=1, ensure_ascii=False)
    son = {"titre": "Live Another Day", "artiste": "Kordhell", "url": "https://www.youtube.com/watch?v=j9SOauBSt9Q",
           "chaine": "KORDHELL (Provided to YouTube by The Orchard Enterprises, album Phonkageddon, 2021)",
           "fichier": "lot5/sons/I1-kordhell-live-another-day_complet.wav",
           "extrait_debut_s": round(C_OFF, 3), "extrait_fin_s": round(C_OFF + END, 3), "bpm": 115.0, "drop_s": HITS[0], "drop_timeline_s": DROP,
           "frappes_s": [HITS[k] for k in sorted(HITS)], "frappes_timeline_s": [round(hb(k), 3) for k in sorted(HITS) if hb(k) >= 0],
           "passage": "fin du 1er couplet (44,1 s) puis roulement de caisse sans basse (48-50 s) sous la phrase, drop sur le retour du 808 et de la cloche (50,08 s), section la plus forte du morceau (50-64 s)",
           "paroles_audibles": "aucune (instrumental phonk)"}
    json.dump(son, open(D + "son.json", "w"), indent=1, ensure_ascii=False)

# ---------------- aperçu ffmpeg 540×960 ----------------
def preview():
    out = HK + "/preview/apercu-I1.mp4"; args = [FF, "-v", "error", "-y"]; fl = []
    for i, sh in enumerate(SHOTS):
        args += ["-i", OUT + sh["clip"]]
        fl.append("[%d:v]trim=end_frame=%d,setpts=PTS-STARTPTS,scale=540:960,setsar=1[v%d]" % (i, sh["dur"], i))
    args += ["-i", OUT + "I1-mix.wav"]
    fl.append("".join("[v%d]" % i for i in range(len(SHOTS))) + "concat=n=%d:v=1:a=0,format=yuv420p[v]" % len(SHOTS))
    args += ["-filter_complex", ";".join(fl), "-map", "[v]", "-map", "%d:a" % len(SHOTS), "-r", "30", "-c:v", "libx264", "-crf", "20", "-preset", "medium",
             "-c:a", "aac", "-b:a", "256k", "-shortest", "-movflags", "+faststart", out]
    subprocess.run(args, check=True)
    return out

if __name__ == "__main__":
    only = None
    for a in sys.argv:
        if a.startswith("only="): only = a[5:].split(",")
    if "plans" in sys.argv:
        from concurrent.futures import ProcessPoolExecutor
        todo = [sh for sh in SHOTS if not only or sh["id"] in only]
        with ProcessPoolExecutor(6) as ex:
            for sh, info in zip(todo, ex.map(render, todo)):
                print(sh["id"], "%.3f-%.3f" % (sh["a"], sh["b"]), sh["dur"], "img", info, flush=True)
    if "recale" in sys.argv: print("frappes du mix :", recale()); sys.exit()
    if "audio" in sys.argv: print(build_audio())
    write_plan()
    if "apercu" in sys.argv: print(preview())
    cuts = len(SHOTS) - 1
    print("total %.2f s ; %d plans ; %d coupes (%.1f / 10 s) ; drop %.2f ; musique %.3f-%.3f" % (END, len(SHOTS), cuts, cuts / END * 10, DROP, C_OFF, C_OFF + END))
