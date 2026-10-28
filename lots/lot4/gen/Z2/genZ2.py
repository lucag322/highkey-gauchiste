# Z2 — Archivage lazy (recette prepa85, modèle lot3 Z1 v2), Mélenchon, son Daft Punk – Harder, Better, Faster, Stronger.
# Bloc 1 : la prise du soir du 1er tour (10/4/2022, chaîne officielle JLM) : plan large de la scène puis gros plan (coupe d'origine,
# sur la pause), voix audible + sous-titres blancs natifs, musique filtrée et baissée dessous (montée sur la fin).
# Drop sur le retour du kick après le break (98,29 s du morceau) = début de la section « Work it harder, make it better… » ;
# coupes sèches sur les vraies frappes (kick) ; bloom couleur des zones claires, fort au drop puis qui retombe (rebond sur chaque coupe) ;
# poussées avant (ease-in) qui finissent sur la frappe de la coupe suivante. Jamais de dézoom. Archives 2022 sans filtre :
# soir du 1er tour (Paris), marche pour la 6e République (Paris 20/3/2022), meeting du Capitole (Toulouse 3/4/2022).
# Usage : python genZ2.py [plans] [audio] [apercu] [only=ID,ID]
import sys, os, json, subprocess
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
HK = "/Users/luca.grousset/Movies/highkey-gauchiste"; L4 = HK + "/lot4"
sys.path.insert(0, HK + "/_claude/outils"); sys.path.insert(0, HK + "/lot2/_claude/gen/C1")
import framing
from fx import crop_view
from temps_forts import attaques, load as tf_load
FF = "/opt/homebrew/bin/ffmpeg"
D = L4 + "/_claude/gen/Z2/"; OUT = D + "out/"; os.makedirs(OUT, exist_ok=True)
framing.CACHE = D + "cache/faces"                          # cache visages dans notre dossier
REL = "../lot4/sources/"
SRC = {"regard": "Z2-premiertour2022-regard.mp4", "fb": "Z2-premiertour2022-foule-b.mp4",
       "m3266": "Z2-marche2022-3266.mp4", "m3793": "Z2-marche2022-3793.mp4", "m4018": "Z2-marche2022-4018.mp4",
       "m4633": "Z2-marche2022-4633.mp4", "m4895": "Z2-marche2022-4895.mp4", "m5179": "Z2-marche2022-5179.mp4",
       "m5437": "Z2-marche2022-5437.mp4", "t3293": "Z2-toulouse2022-3293.mp4", "t5692": "Z2-toulouse2022-5692.mp4"}
ORIG = {"regard": ("izCL2pR8UCE", 268), "fb": ("izCL2pR8UCE", 502),
        "m3266": ("Zlwij7ZXLts", 3266), "m3793": ("Zlwij7ZXLts", 3793), "m4018": ("Zlwij7ZXLts", 4018), "m4633": ("Zlwij7ZXLts", 4633),
        "m4895": ("Zlwij7ZXLts", 4895), "m5179": ("Zlwij7ZXLts", 5179), "m5437": ("Zlwij7ZXLts", 5437),
        "t3293": ("znUyK4s2pNs", 3293), "t5692": ("znUyK4s2pNs", 5692)}
NOLOGO = (0, 0, 1600, 1080)                                 # logo « L'UNION POPULAIRE » en haut à droite (x > 1620) : exclu
BOUNDS = {k: (NOLOGO if k[0] in "mt" else (0, 0, 1920, 1080)) for k in SRC}
SFPS = 30; W, H, TFPS = 1080, 1920, 30
def f30(t): return int(round(t * TFPS))

# ---------------- son ----------------
MUSIC = L4 + "/sons/Z2-daftpunk-hbfs_complet.wav"
HOOK = 98.295                                               # retour du kick après le break (début « Work it harder… »), mesuré
PER = 0.48603                                               # 123,45 BPM (98,295 -> 112,390 en 29 temps, frappes mesurées)
BEATS = [0, 2, 4, 6, 8, 9, 10, 12, 14, 16, 17, 18, 20, 24]  # temps après le drop où l'on coupe (dernier = fin)
_att = [a for a, s in attaques(tf_load(MUSIC, 96.0, 16.0), 96.0, 4.0, half=0.12)]   # kick à chaque temps (fenêtre courte)
def snap(t):
    a = min(_att, key=lambda x: abs(x - t)); assert abs(a - t) < 0.03, ("pas de frappe près de", t); return a
HITS = [snap(HOOK + PER * j) for j in BEATS]                # vraies frappes (temps du morceau)
BIAS = 0.004                                                # retard mesuré des attaques sur l'export (AAC + fenêtres 5 ms)
def err(dt): return max(abs((h - HITS[0] + dt + BIAS) * TFPS - round((h - HITS[0] + dt) * TFPS)) for h in HITS)
DROP = min((6.62 + k / 1000 for k in range(0, 281)), key=err)   # juste après « …baissé le regard. » (6,32 s)
M0 = HITS[0] - DROP                                         # temps du morceau à t=0 timeline
CUTF = [f30(h - M0) for h in HITS]; END = CUTF[-1] / TFPS
VIN = 10.00                                                 # voix : Z2-premiertour2022-regard.mp4 (= YouTube 268 s + fichier), timeline = fichier - 10,00
SENT_END = 16.32 - VIN                                      # fin de « regard. » (énergie mesurée, YouTube 284,32 s)
NEXT_WORD = 17.15 - VIN                                     # « Et c'est… » : la voix doit être coupée avant
SRC_CUT = f30(14.3667 - VIN)                                # coupe d'origine plan large -> gros plan (pause après « cédé, »)

# ---------------- sous-titres natifs (blancs, 2 lignes, sans animation) ----------------
SUBS = [(0.0, SRC_CUT / TFPS, ["Je n'ai jamais", "lâché prise,", "je n'ai jamais cédé,"]),
        (SRC_CUT / TFPS, None, ["je n'ai jamais", "baissé le regard."])]
FONT = "/Users/luca.grousset/Library/Fonts/Inter-VariableFont_opsz,wght.ttf"
def sub_font(px):
    f = ImageFont.truetype(FONT, px)
    try: f.set_variation_by_axes([32, 600])               # opsz, wght (SemiBold)
    except Exception: pass
    return f
_SUBL = {}
def sub_layer(i):
    if i not in _SUBL:
        f = sub_font(72); lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dr = ImageDraw.Draw(lay)
        sh = Image.new("L", (W, H), 0); ds = ImageDraw.Draw(sh); y0 = int(H * 0.56); lh = 92
        for k, line in enumerate(SUBS[i][2]):
            ds.text((W / 2, y0 + k * lh), line, font=f, anchor="ma", fill=200, stroke_width=4, stroke_fill=200)
            dr.text((W / 2, y0 + k * lh), line, font=f, anchor="ma", fill=(255, 255, 255, 255), stroke_width=2, stroke_fill=(20, 20, 20, 255))
        m = np.asarray(sh.filter(ImageFilter.GaussianBlur(6)), np.float32)[..., None] / 255
        a = np.asarray(lay, np.float32) / 255
        _SUBL[i] = (m, a)
    return _SUBL[i]
def draw_sub(img, t):
    for i, (t0, t1, _) in enumerate(SUBS):
        if t0 <= t < (t1 if t1 is not None else DROP):
            m, a = sub_layer(i); out = img * (1 - 0.55 * m)
            return out * (1 - a[..., 3:4]) + a[..., [2, 1, 0]] * a[..., 3:4]
    return img

# ---------------- effets : bloom + poussées avant ----------------
CUT_T = [c / TFPS for c in CUTF[:-1]]                       # temps des coupes (frappes) après le drop
RISE0 = SRC_CUT / TFPS                                      # la montée commence sur le gros plan
def bloom_k(t):
    if t < DROP: return 0.08 + 0.30 * np.clip((t - RISE0) / (DROP - RISE0), 0, 1) ** 2      # montée sous la fin de la phrase
    k = 0.30 + 0.80 * np.exp(-(t - DROP) / 0.50)                                             # flash au drop puis retombe
    for c in CUT_T[1:]:
        if t >= c: k += 0.25 * np.exp(-(t - c) / 0.20)                                          # petit rebond sur chaque frappe
    return k
def bloom(img, k):
    if k <= 0.01: return img
    sm = cv2.resize(img, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    l = sm.max(2, keepdims=True); hi = sm * np.clip((l - 0.58) / 0.32, 0, 1)
    g = cv2.GaussianBlur(hi, (0, 0), 5) * 0.55 + cv2.GaussianBlur(hi, (0, 0), 16) * 0.75 + cv2.GaussianBlur(hi, (0, 0), 40) * 0.45
    g = cv2.resize(g, (W, H), interpolation=cv2.INTER_LINEAR)
    return 1 - (1 - img) * (1 - np.clip(g * k, 0, 1))          # écran : les clairs (drapeaux, ciel, projecteurs) rayonnent, en couleur
ZOOM = {"P0a": 0.05, "P0b": 0.06}                           # poussée avant totale par plan (défaut B-roll ci-dessous)
def zoom_amt(sh): return ZOOM.get(sh["id"], 0.06 if sh["dur"] < 20 else 0.10)

# ---------------- plans ----------------
def S(i, src, t_in, mode, c, note, vh=1080, bd=None): return dict(id=i, src=src, t_in=t_in, mode=mode, c=c, note=note, bd=bd or BOUNDS[src], vh=vh)
SHOTS = [S("P0a", "regard", VIN, "fix", (945, 605), "Prise du soir du 1er tour (10/4/2022) : plan large de la scène, « Je n'ai jamais lâché prise, je n'ai jamais cédé, » (bandeau texte du décor hors champ)", bd=(0, 130, 1920, 1080)),
         S("P0b", "regard", VIN + SRC_CUT / TFPS, "right", (1000, 420), "même prise, gros plan (coupe d'origine sur la pause) : « je n'ai jamais baissé le regard. » ; cadre calé sur le bord droit de la tête pour laisser hors champ « avec Jean-Luc Mélenchon » du décor")]
BROLL = [
    S("B01", "t3293", 0.30, "fix", (720, 540), "Toulouse, Capitole : Mélenchon de dos face à la foule (drop)"),
    S("B02", "m3793", 4.00, "fix", (760, 540), "Marche 6e République : foule et drapeaux"),
    S("B03", "m3793", 9.00, "fix", (1050, 540), "Marche : marée de drapeaux (autre moment et autre cadre que B02)"),
    S("B04", "m4018", 3.20, "face", (990, 260), "Marche : Mélenchon, drapeaux au premier plan"),
    S("B05", "m4895", 3.00, "fix", (760, 540), "Marche : drapeaux de l'Union populaire"),
    S("B06", "m3266", 6.00, "fix", (900, 540), "Marche : foule et drapeaux tricolores"),
    S("B07", "t5692", 1.00, "fix", (1000, 540), "Toulouse : place du Capitole pleine"),
    S("B08", "m5437", 4.00, "face", (1065, 250), "Marche : Mélenchon devant le drapeau phi"),
    S("B09", "m4633", 5.00, "fix", (960, 540), "Marche : la place de la République jusqu'à la scène"),
    S("B10", "m4633", 0.50, "face", (900, 300), "Marche : Mélenchon au pupitre, arbres de la place"),
    S("B11", "t5692", 5.00, "fix", (450, 540), "Toulouse : foule devant les façades de la place du Capitole"),
    S("B12", "m4018", 0.30, "fix", (700, 540), "Marche : foule et drapeaux devant la scène"),
    S("B13", "m3793", 0.00, "face", (990, 250), "Marche : Mélenchon les bras levés (fin, fondu au noir)"),
]
SHOTS += BROLL
bounds_rec = [0, SRC_CUT] + CUTF
for k, sh in enumerate(SHOTS):
    sh["rec"] = bounds_rec[k]; sh["dur"] = bounds_rec[k + 1] - bounds_rec[k]
    sh["clip"] = "Z2_%s.mov" % sh["id"]
    sh["n_src"] = int(np.ceil(sh["dur"] / TFPS * SFPS)) + 1
assert len(SHOTS) == len(CUTF) + 1
assert min(s["dur"] for s in SHOTS) >= 12, "plan < 1 temps"

def read_frames(src, t, n):
    p = subprocess.Popen([FF, "-v", "error", "-ss", "%.4f" % t, "-i", L4 + "/sources/" + SRC[src], "-vf", "fps=30", "-frames:v", str(n),
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
BGBLUR = {"P0b"}                                            # gros plan : « avec Jean-Luc Mélenchon » du décor collé à sa tête -> flou de fond
def bg_masks(sh, views):
    import shutil, glob
    dd = D + "cache/seg_%s/" % sh["id"]; shutil.rmtree(dd, ignore_errors=True); os.makedirs(dd + "in"); k = 0
    for fr in read_frames(sh["src"], sh["t_in"], sh["dur"]):
        cx, cy, vh = views[min(k, len(views) - 1)]
        img = crop_view(fr.astype(np.float32) / 255, cx, cy, vh * 9 / 16, W // 2, H // 2)
        cv2.imwrite(dd + "in/f%04d.png" % k, (np.clip(img, 0, 1) * 255).astype(np.uint8)); k += 1
    subprocess.run([HK + "/_claude/outils/segment", dd + "in", dd + "m"], check=True, capture_output=True)
    out = []
    for f in sorted(glob.glob(dd + "m/*.png")):
        m = cv2.imread(f, 0).astype(np.float32) / 255
        m = cv2.dilate(m, np.ones((7, 7), np.uint8)); m = cv2.GaussianBlur(cv2.resize(m, (W, H)), (0, 0), 6)
        out.append(np.clip(m, 0, 1)[..., None])
    shutil.rmtree(dd)
    return out
def render(sh):
    n = sh["dur"]; w = writer(OUT + sh["clip"]); bd = sh["bd"]; s = int(round(sh["t_in"] * SFPS))
    A = zoom_amt(sh); ns = sh["n_src"]
    zf = lambda f: 1 + A * (min(f, ns - 1) / max(ns - 1, 1)) ** 2   # ease-in : la poussée finit sur la frappe de la coupe suivante
    kw = dict(speed=1.0, hint=sh["c"], bounds=bd, vh=min(sh["vh"], bd[3] - bd[1]), zoom=zf)
    if sh["mode"] == "fix": kw["fixed"] = sh["c"]
    if sh["mode"] == "right":                                # bord droit du cadre collé à la tête (le texte du décor commence juste à droite)
        hd = framing.pick(framing.detect(REL + SRC[sh["src"]], s, sh["n_src"] + 2, SFPS), sh["c"], bd); ok = hd is not None
        views = []
        for f in range(sh["n_src"]):
            x, y, fw, fh = hd[min(f, len(hd) - 1)]; v = 1080 / zf(f); vw = v * 9 / 16
            views.append((x + fw * 1.13 + 50 - vw / 2, 540, v))
    else: views, ok = framing.plan_views(REL + SRC[sh["src"]], s, sh["n_src"], SFPS, **kw)
    info = ("visage" if ok else "SANS VISAGE") if sh["mode"] in ("face", "right") else "fixe"
    xs = [v[0] - v[2] * 9 / 32 for v in views] + [v[0] + v[2] * 9 / 32 for v in views]
    info += " x %d-%d vh %d-%d" % (min(xs), max(xs), views[0][2], views[-1][2]); k = 0
    masks = bg_masks(sh, views) if sh["id"] in BGBLUR else None
    for fr in read_frames(sh["src"], sh["t_in"], n):
        cx, cy, vh = views[min(k, len(views) - 1)]
        img = crop_view(fr.astype(np.float32) / 255, cx, cy, vh * 9 / 16, W, H)
        if masks is not None:                                  # décor flouté derrière la personne (texte du décor illisible)
            m = masks[min(k, len(masks) - 1)]
            img = img * m + cv2.GaussianBlur(img, (0, 0), 22) * (1 - m)
        t = (sh["rec"] + k) / TFPS
        img = bloom(img, bloom_k(t))
        if sh["id"].startswith("P0"): img = draw_sub(img, t)
        w.stdin.write((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8).tobytes()); k += 1
    if k < n: info += " COURT:%d/%d" % (k, n)
    w.stdin.close(); w.wait()
    return info

# ---------------- audio ----------------
SR = 48000
def load(path, t=0.0, d=None):
    cmd = [FF, "-v", "error", "-ss", "%.4f" % t, "-i", path] + (["-t", "%.4f" % d] if d else []) + ["-f", "f32le", "-ac", "2", "-ar", str(SR), "-"]
    return np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, np.float32).reshape(-1, 2).copy()
def sf_write(p, x):
    import soundfile as sf; sf.write(p, x, SR, subtype="PCM_24")
def lufs(x):
    p = OUT + "_tmp_meas.wav"; sf_write(p, x)
    r = subprocess.run([FF, "-v", "info", "-i", p, "-af", "loudnorm=print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
    js = json.loads(r[r.rindex("{"):r.rindex("}") + 1]); os.remove(p)
    return float(js["input_i"]), float(js["input_tp"])
def db(g): return 10 ** (g / 20)
VOICE_END = min(DROP + 0.08, NEXT_WORD - 0.08)              # voix coupée juste après le drop, avant le mot suivant
def build_audio():
    from scipy.signal import butter, sosfilt
    n = int(END * SR); t = np.arange(n) / SR
    voice = load(L4 + "/sources/" + SRC["regard"], VIN, VOICE_END)[:int(VOICE_END * SR)]
    a = np.ones(len(voice), np.float32); k0 = int((SENT_END + 0.06) * SR)
    a[k0:] = np.linspace(1, 0, len(voice) - k0) ** 2; voice *= a[:, None]      # la salle s'efface entre « regard. » et le drop
    mus = load(MUSIC, M0, END + 0.05)[:n]
    lv, _ = lufs(voice[:int(SENT_END * SR)]); lm, _ = lufs(load(MUSIC, 98.3, 11.0))
    voice *= db(-15 - lv); mus *= db(-14 - lm)
    # sous la phrase : musique passe-bas 500 Hz à -12 dB ; s'ouvre un peu pendant le gros plan, pleine au drop
    lp = sosfilt(butter(4, 500, "low", fs=SR, output="sos"), mus, axis=0).astype(np.float32)
    x = np.clip((t - RISE0) / (DROP - RISE0), 0, 1) ** 2 * 0.40
    x = np.where(t >= DROP - 0.002, 1.0, x)[:, None].astype(np.float32)
    g = (db(-12) + (1 - db(-12)) * x).astype(np.float32)
    fo = (np.clip((END - t) / 0.9, 0, 1) ** 1.5)[:, None].astype(np.float32)
    bed = (lp * (1 - x) + mus * x) * g * fo
    mix = bed.copy(); mix[:len(voice)] += voice[:n]
    tmp = OUT + "_tmp_mix.wav"; sf_write(tmp, mix); gain = 0.0; li, _ = lufs(mix)
    for _ in range(4):
        gain += -14.0 - li
        subprocess.run([FF, "-v", "error", "-y", "-i", tmp, "-af", "volume=%.2fdB,alimiter=limit=0.80:attack=3:release=60:level=false,aresample=192000,alimiter=limit=0.82:attack=1:release=40:level=false,aresample=48000" % gain,
                        "-c:a", "pcm_s24le", OUT + "Z2-mix.wav"], check=True)
        li, tp = lufs(load(OUT + "Z2-mix.wav"))
        if abs(li + 14) < 0.3 and tp < -1.0: break
    os.remove(tmp); sf_write(OUT + "Z2-musique-posee.wav", bed)
    return "mix %.1f LUFS, true peak %.1f dBTP (voix %.1f, section d'origine %.1f)" % (li, tp, lv, lm)

# ---------------- plan-Z2.json + son.json ----------------
PHRASE = "Je n'ai jamais lâché prise, je n'ai jamais cédé, je n'ai jamais baissé le regard."
def write_plan():
    vid = []
    for sh in SHOTS:
        yid, off = ORIG[sh["src"]]; used = sh["dur"] / TFPS
        it = {"id": sh["id"], "clip": sh["clip"], "folder": "genZ2", "path": OUT + sh["clip"], "s": 0, "e": sh["dur"], "clip_fps": 30,
              "rec": sh["rec"], "dur": sh["dur"], "track": 1, "speed_pct": 100, "note": sh["note"],
              "source": {"fichier": "lot4/sources/" + SRC[sh["src"]], "in_s": round(sh["t_in"], 3), "out_s": round(sh["t_in"] + used, 3),
                         "youtube": "https://www.youtube.com/watch?v=%s&t=%d" % (yid, int(off + sh["t_in"]))},
              "effets": "recadrage 9:16 %s, poussée avant ease-in 1,00->%.2f finissant sur la %s, bloom couleur des zones claires (%s), couleurs d'origine%s%s" % (
                  {"face": "suivi visage", "right": "suivi visage (bord droit)"}.get(sh["mode"], "fixe"), 1 + zoom_amt(sh), "frappe" if sh["rec"] >= CUTF[0] or sh["id"] == "P0b" else "coupe d'origine",
                  "fort au drop puis retombe" if sh["rec"] >= CUTF[0] else "léger, monte vers le drop", ", sous-titre blanc cuit" if sh["id"].startswith("P0") else "", ", décor flouté derrière lui (masque personne Vision) pour rendre illisible le texte du décor collé à sa tête (zone boutons TikTok)" if sh["id"] in BGBLUR else "")}
        if sh["id"] == SHOTS[-1]["id"]: it["fade_out_s"] = 0.7
        vid.append(it)
    plan = {"name": "Z2 - Archivage lazy Melenchon (Harder Better Faster Stronger)", "fps": 30, "w": 1080, "h": 1920, "duree_s": round(END, 3),
            "phrase": PHRASE,
            "source_phrase": "https://www.youtube.com/watch?v=izCL2pR8UCE (chaîne JEAN-LUC MÉLENCHON, « La lutte continue ! », discours du soir du 1er tour, 10/4/2022) 278,25-284,32 s",
            "note": "Plans ProRes 1080x1920 30 i/s recadrés (sources 30 i/s), aucun ralenti. Générateur : lot4/_claude/gen/Z2/genZ2.py",
            "sous_titre": {"blocs": [{"lignes": l, "t0": round(a, 3), "t1": round(b if b is not None else DROP, 3)} for a, b, l in SUBS],
                           "police": "Inter SemiBold 72 px blanc, contour 2 px + ombre douce, lignes de 2 à 4 mots, haut du bloc à 0,56 H, bloc dans x 0,20-0,80 et y 0,55-0,72 (zone sûre TikTok)"},
            "musique": {"fichier": "lot4/sons/Z2-daftpunk-hbfs_complet.wav", "depart_dans_complet_s": round(M0, 3),
                        "drop_timeline_s": round(DROP, 3), "frappes_coupes_timeline_s": [round(h - M0, 3) for h in HITS]},
            "video": vid,
            "audio": [{"id": "mix", "clip": "Z2-mix.wav", "folder": "genZ2", "path": OUT + "Z2-mix.wav", "rec": 0, "track": 1,
                       "note": "mix -14 LUFS : voix du fichier regard %.2f-%.2f s à 0 s (fondu après « regard. ») ; musique passe-bas -12 dB sous la phrase, s'ouvre sur le gros plan, pleine au drop %.3f s, fondu 0,9 s" % (VIN, VIN + VOICE_END, DROP)}]}
    json.dump(plan, open(D + "plan-Z2.json", "w"), indent=1, ensure_ascii=False)
    son = {"titre": "Harder, Better, Faster, Stronger", "artiste": "Daft Punk", "url": "https://youtu.be/gAjR4_CbPpQ",
           "chaine": "Daft Punk (officielle, Official Video)", "fichier": "lot4/sons/Z2-daftpunk-hbfs_complet.wav",
           "extrait_debut_s": round(M0, 3), "extrait_fin_s": round(M0 + END, 3), "bpm": 123.45,
           "drop_dans_morceau_s": HITS[0], "drop_timeline_s": round(DROP, 3),
           "paroles_dans_extrait": "sous la phrase (filtré -12 dB) : « Harder, better, faster, stronger » puis le break sans basse ; après le drop : « Work it harder, make it better, do it faster, makes us stronger, more than ever, hour after hour, work is never over »",
           "drop": "retour du kick après le break, début de la section « Work it harder, make it better… » (98,29 s du morceau, ~1:38 de la vidéo officielle)",
           "frappes_morceau_s": HITS, "frappes_timeline_s": [round(h - M0, 3) for h in HITS]}
    json.dump(son, open(D + "son.json", "w"), indent=1, ensure_ascii=False)

def preview():
    out = HK + "/preview/apercu-Z2.mp4"; args = [FF, "-v", "error", "-y"]; fl = []
    for i, sh in enumerate(SHOTS):
        args += ["-i", OUT + sh["clip"]]; last = sh["id"] == SHOTS[-1]["id"]
        fl.append("[%d:v]trim=end_frame=%d,setpts=PTS-STARTPTS,scale=540:960,setsar=1%s[v%d]" % (
            i, sh["dur"], ",fade=t=out:st=%.3f:d=0.7" % (sh["dur"] / 30 - 0.7) if last else "", i))
    args += ["-i", OUT + "Z2-mix.wav"]
    fl.append("".join("[v%d]" % i for i in range(len(SHOTS))) + "concat=n=%d:v=1:a=0[v]" % len(SHOTS))
    args += ["-filter_complex", ";".join(fl), "-map", "[v]", "-map", "%d:a" % len(SHOTS), "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p",
             "-r", "30", "-c:a", "aac", "-b:a", "192k", "-shortest", out]
    subprocess.run(args, check=True)
    return out

if __name__ == "__main__":
    only = None
    for a in sys.argv:
        if a.startswith("only="): only = a[5:].split(",")
    print("drop %.3f s (frappe %.3f), départ morceau %.3f, fin %.2f s, écart arrondi image max %.1f ms" % (DROP, HITS[0], M0, END, err(DROP) / TFPS * 1000))
    print("plans", [(s["id"], s["rec"], s["dur"]) for s in SHOTS])
    if "plans" in sys.argv:
        for sh in SHOTS:
            if only and sh["id"] not in only: continue
            print(sh["id"], sh["rec"], sh["dur"], render(sh), flush=True)
    if "audio" in sys.argv: print(build_audio())
    write_plan()
    if "apercu" in sys.argv: print(preview())
