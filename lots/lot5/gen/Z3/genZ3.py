# Z3 — Archivage lazy (recette prepa85, modèles lot3 Z1 et lot4 Z2, version bloom + zooms), Mélenchon, archives 2017,
# son Benny Benassi – Satisfaction (Ultra Records, officiel).
# Bloc 1 : la prise du meeting pour la paix (Vieux-Port, Marseille, 9/4/2017, chaîne officielle JLM) : plan de la foule puis gros plan
# (coupe d'origine), voix audible + sous-titres blancs natifs, musique filtrée et baissée dessous, montée sur la fin de la phrase.
# Drop sur l'entrée de la basse « Satisfaction » (78,01 s du morceau) = début de « Push me, and then just touch me… ».
# Coupes sèches sur les vraies frappes ; bloom couleur des zones claires (fort au drop puis retombe, rebond à chaque coupe) ;
# poussées avant (ease-in) qui finissent sur la frappe suivante. Jamais de dézoom. Archives 2017 sans filtre (Marseille 9/4/2017,
# place de la République 18/3/2017), AUTRES moments que Z1 / M1. Sous-titres incrustés, interprète LSF et bandeaux hors cadre.
# Usage : python genZ3.py [plans] [audio] [apercu] [only=ID,ID]
import sys, os, json, subprocess
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
HK = "/Users/luca.grousset/Movies/highkey-gauchiste"; L5 = HK + "/lot5"
sys.path.insert(0, HK + "/_claude/outils"); sys.path.insert(0, HK + "/lot2/_claude/gen/C1")
import framing
from fx import crop_view
from temps_forts import attaques, load as tf_load
FF = "/opt/homebrew/bin/ffmpeg"
D = L5 + "/_claude/gen/Z3/"; OUT = D + "out/"; os.makedirs(OUT, exist_ok=True)
framing.CACHE = D + "cache/faces"                          # cache visages dans notre dossier
SRC = {"fo": "lot5/sources/Z3-marseille2017-forces.mp4", "md": "lot3/sources/Z1-marseille2017-debut.mp4",
       "mf": "lot3/sources/Z1-marseille2017-fin.mp4", "rf": "lot3/sources/Z1-republique2017-fin.mp4"}
ORIG = {"fo": ("yrjWwsV4zS4", 2975), "md": ("yrjWwsV4zS4", 0), "mf": ("yrjWwsV4zS4", 3515), "rf": ("b5atq_VZd2M", 3690)}
# zones source sans sous-titres incrustés (bas), interprète LSF (droite) ni bandeau
BOUNDS = {"fo": (0, 0, 1620, 880), "md": (0, 0, 1920, 1080), "mf": (0, 0, 1620, 880), "rf": (0, 0, 1460, 870)}
FULL = (0, 0, 1920, 1080); MDSUB = (0, 0, 1700, 880)       # md après 79 s : sous-titres + interprète ; mf après 41 s : plus rien
SFPS = 25; W, H, TFPS = 1080, 1920, 30
def f30(t): return int(round(t * TFPS))

# ---------------- son ----------------
MUSIC = L5 + "/sons/Z3-benassi-satisfaction_complet.wav"
CUTS_M = [78.010, 79.160, 80.085, 81.005, 81.945, 82.850, 83.780, 84.700, 85.625, 86.525, 87.940, 88.405, 89.325, 91.175]
_att = [a for a, s in attaques(tf_load(MUSIC, 76.0, 17.0), 76.0, 3.0, half=0.10)]
def snap(t):
    a = min(_att, key=lambda x: abs(x - t)); assert abs(a - t) < 0.03, ("pas de frappe près de", t); return a
HITS = [snap(t) for t in CUTS_M]                            # vraies frappes (temps du morceau) ; HITS[0] = entrée de la basse
BIAS = 0.004
def err(dt): return max(abs((h - HITS[0] + dt + BIAS) * TFPS - round((h - HITS[0] + dt) * TFPS)) for h in HITS)
DROP = min((6.56 + k / 1000 for k in range(0, 271)), key=err)   # juste après « …faites la vôtre ! » (6,40 s) ; fin <= 20 s
M0 = HITS[0] - DROP
CUTF = [f30(h - M0) for h in HITS]; END = CUTF[-1] / TFPS
VIN = 9.60                                                  # voix : Z3-marseille2017-forces.mp4 (= YouTube ~2975,06 s + fichier)
SENT_END = 16.00 - VIN                                      # fin de « vôtre ! »
FORCES_END = 12.56 - VIN                                    # fin de « forces, »
SRC_CUT = 67                                                # coupe d'origine foule -> gros plan (11,84 s du fichier)
P0B_IN = 11.84

# ---------------- sous-titres natifs (blancs, sans animation) ----------------
SUBS = [(0.0, FORCES_END + 0.12, ["Ne comptez que sur", "vos propres forces,"]),
        (FORCES_END + 0.12, None, ["je ferai ma part", "de travail,", "faites la vôtre !"])]
FONT = "/Users/luca.grousset/Library/Fonts/Inter-VariableFont_opsz,wght.ttf"
SUB_PX, SUB_Y0, SUB_LH = 64, int(H * 0.56), 84
def sub_font(px):
    f = ImageFont.truetype(FONT, px)
    try: f.set_variation_by_axes([32, 600])
    except Exception: pass
    return f
_SUBL = {}
def sub_layer(i):
    if i not in _SUBL:
        f = sub_font(SUB_PX); lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dr = ImageDraw.Draw(lay)
        sh = Image.new("L", (W, H), 0); ds = ImageDraw.Draw(sh)
        for k, line in enumerate(SUBS[i][2]):
            assert dr.textlength(line, font=f) <= 0.62 * W, line
            ds.text((W / 2, SUB_Y0 + k * SUB_LH), line, font=f, anchor="ma", fill=200, stroke_width=4, stroke_fill=200)
            dr.text((W / 2, SUB_Y0 + k * SUB_LH), line, font=f, anchor="ma", fill=(255, 255, 255, 255), stroke_width=2, stroke_fill=(20, 20, 20, 255))
        m = np.asarray(sh.filter(ImageFilter.GaussianBlur(6)), np.float32)[..., None] / 255
        _SUBL[i] = (m, np.asarray(lay, np.float32) / 255)
    return _SUBL[i]
def draw_sub(img, t):
    for i, (t0, t1, _) in enumerate(SUBS):
        if t0 <= t < (t1 if t1 is not None else DROP):
            m, a = sub_layer(i); out = img * (1 - 0.55 * m)
            return out * (1 - a[..., 3:4]) + a[..., [2, 1, 0]] * a[..., 3:4]
    return img

# ---------------- effets : bloom + poussées avant ----------------
CUT_T = [c / TFPS for c in CUTF[:-1]]
RISE0 = 4.80                                                # montée sous « …faites la vôtre ! » (+ roulement du morceau)
def bloom_k(t):
    if t < DROP: return 0.08 + 0.30 * np.clip((t - RISE0) / (DROP - RISE0), 0, 1) ** 2
    k = 0.30 + 0.80 * np.exp(-(t - DROP) / 0.50)
    for c in CUT_T[1:]:
        if t >= c: k += 0.25 * np.exp(-(t - c) / 0.20)
    return k
def bloom(img, k):
    if k <= 0.01: return img
    sm = cv2.resize(img, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    l = sm.max(2, keepdims=True); hi = sm * np.clip((l - 0.58) / 0.32, 0, 1)
    g = cv2.GaussianBlur(hi, (0, 0), 5) * 0.55 + cv2.GaussianBlur(hi, (0, 0), 16) * 0.75 + cv2.GaussianBlur(hi, (0, 0), 40) * 0.45
    g = cv2.resize(g, (W, H), interpolation=cv2.INTER_LINEAR)
    return 1 - (1 - img) * (1 - np.clip(g * k, 0, 1))
ZOOM = {"P0a": 0.05, "P0b": 0.06}
def zoom_amt(sh): return ZOOM.get(sh["id"], 0.06 if sh["dur"] < 20 else 0.10)

# ---------------- plans ----------------
def S(i, src, t_in, mode, c, note, vh=1080, bd=None): return dict(id=i, src=src, t_in=t_in, mode=mode, c=c, note=note, bd=bd or BOUNDS[src], vh=vh)
SHOTS = [S("P0a", "fo", VIN, "fix", (900, 440), "Meeting pour la paix, Vieux-Port 9/4/2017 : foule, drapeaux et ampoules phi, « Ne comptez que sur vos propres forces, » (voix off du discours)"),
         S("P0b", "fo", P0B_IN, "face", (700, 330), "même prise, gros plan (coupe d'origine) : « …je ferai ma part de travail, faites la vôtre ! »")]
BROLL = [
    S("B01", "md", 36.0, "fix", (700, 540), "Vieux-Port : Mélenchon entre en scène face à la marée de drapeaux (drop)"),
    S("B02", "mf", 24.5, "fix", (1000, 440), "Vieux-Port : drapeaux et pancartes phi"),
    S("B03", "mf", 0.3, "face", (800, 330), "Vieux-Port : Mélenchon poing levé, gros plan"),
    S("B04", "rf", 80.5, "fix", (720, 435), "République 18/3/2017 : marée de drapeaux"),
    S("B05", "md", 5.0, "fix", (960, 540), "Vieux-Port vu de la scène : foule jusqu'au port"),
    S("B06", "md", 76.5, "fix", (960, 540), "Vieux-Port : foule et grande roue"),
    S("B07", "fo", 19.5, "fix", (800, 440), "Vieux-Port : foule, drapeaux et ampoules phi jusqu'au port"),
    S("B08", "rf", 64.0, "fix", (960, 370), "République : foule et drapeaux devant la scène (pancartes du bas hors cadre)", vh=740),
    S("B09", "md", 55.5, "fix", (700, 540), "Vieux-Port : drapeaux au soleil"),
    S("B10", "fo", 0.5, "fix", (1100, 440), "Vieux-Port : ampoule phi et drapeaux devant le port"),
    S("B11", "md", 78.80, "face", (845, 330), "Vieux-Port : Mélenchon au pupitre, gros plan", bd=MDSUB),
    S("B12", "rf", 1.3, "face", (330, 300), "République 18/3/2017 : Mélenchon rit sur scène"),
    S("B13", "rf", 32.0, "fix", (960, 435), "place de la République pleine jusqu'à la scène (fin, fondu au noir)"),
]
SHOTS += BROLL
bounds_rec = [0, SRC_CUT] + CUTF
for k, sh in enumerate(SHOTS):
    sh["rec"] = bounds_rec[k]; sh["dur"] = bounds_rec[k + 1] - bounds_rec[k]
    sh["clip"] = "Z3_%s.mov" % sh["id"]
    sh["n_src"] = int(np.ceil(sh["dur"] / TFPS * SFPS)) + 1
assert len(SHOTS) == len(CUTF) + 1
assert min(s["dur"] for s in SHOTS) >= 13, "plan < 1 temps"
assert END <= 20.0

def read_frames(src, t, n):
    p = subprocess.Popen([FF, "-v", "error", "-ss", "%.4f" % t, "-i", HK + "/" + SRC[src], "-vf", "fps=30", "-frames:v", str(n),
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
    n = sh["dur"]; w = writer(OUT + sh["clip"]); bd = sh["bd"]; s = int(round(sh["t_in"] * SFPS))
    A = zoom_amt(sh); ns = sh["n_src"]
    zf = lambda f: 1 + A * (min(f, ns - 1) / max(ns - 1, 1)) ** 2   # ease-in : la poussée finit sur la frappe suivante
    kw = dict(speed=1.0, hint=sh["c"], bounds=bd, vh=min(sh["vh"], bd[3] - bd[1]), zoom=zf)
    if sh["mode"] == "fix": kw["fixed"] = sh["c"]
    views, ok = framing.plan_views("../" + SRC[sh["src"]], s, sh["n_src"], SFPS, **kw)
    info = ("visage" if ok else "SANS VISAGE") if sh["mode"] == "face" else "fixe"
    xs = [v[0] - v[2] * 9 / 32 for v in views] + [v[0] + v[2] * 9 / 32 for v in views]
    info += " x %d-%d vh %d-%d" % (min(xs), max(xs), views[0][2], views[-1][2]); k = 0
    for fr in read_frames(sh["src"], sh["t_in"], n):
        cx, cy, vh = views[min(int(k * SFPS / TFPS), len(views) - 1)]
        img = crop_view(fr.astype(np.float32) / 255, cx, cy, vh * 9 / 16, W, H)
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
VOICE_END = DROP + 0.30                                     # la clameur déborde un peu sur le drop, puis s'efface
def build_audio():
    from scipy.signal import butter, sosfilt
    n = int(END * SR); t = np.arange(n) / SR
    voice = load(HK + "/" + SRC["fo"], VIN, VOICE_END)[:int(VOICE_END * SR)]
    a = np.ones(len(voice), np.float32); k0 = int(0.04 * SR); a[:k0] = np.linspace(0, 1, k0)
    k1 = int((SENT_END + 0.10) * SR); a[k1:] = np.linspace(1, 0, len(voice) - k1) ** 2; voice *= a[:, None]
    mus = load(MUSIC, M0, END + 0.05)[:n]
    lv, _ = lufs(voice[:int(SENT_END * SR)]); lm, _ = lufs(load(MUSIC, 78.0, 13.0))
    voice *= db(-15 - lv); mus *= db(-14 - lm)
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
                        "-c:a", "pcm_s24le", OUT + "Z3-mix.wav"], check=True)
        li, tp = lufs(load(OUT + "Z3-mix.wav"))
        if abs(li + 14) < 0.3 and tp < -1.0: break
    os.remove(tmp); sf_write(OUT + "Z3-musique-posee.wav", bed)
    return "mix %.1f LUFS, true peak %.1f dBTP (voix %.1f, section d'origine %.1f)" % (li, tp, lv, lm)

# ---------------- plan-Z3.json + son.json ----------------
PHRASE = "Ne comptez que sur vos propres forces, je ferai ma part de travail, faites la vôtre !"
def write_plan():
    vid = []
    for sh in SHOTS:
        yid, off = ORIG[sh["src"]]; used = sh["dur"] / TFPS
        it = {"id": sh["id"], "clip": sh["clip"], "folder": "genZ3", "path": OUT + sh["clip"], "s": 0, "e": sh["dur"], "clip_fps": 30,
              "rec": sh["rec"], "dur": sh["dur"], "track": 1, "speed_pct": 100, "note": sh["note"],
              "source": {"fichier": SRC[sh["src"]], "in_s": round(sh["t_in"], 3), "out_s": round(sh["t_in"] + used, 3),
                         "youtube": "https://www.youtube.com/watch?v=%s&t=%d" % (yid, int(off + sh["t_in"]))},
              "effets": "recadrage 9:16 %s (sans sous-titres incrustés, interprète ni bandeau), poussée avant ease-in 1,00->%.2f finissant sur la %s, bloom couleur des zones claires (%s), couleurs d'origine%s" % (
                  "suivi visage" if sh["mode"] == "face" else "fixe", 1 + zoom_amt(sh), "frappe" if sh["id"] != "P0a" else "coupe d'origine",
                  "fort au drop puis retombe" if sh["rec"] >= CUTF[0] else "léger, monte vers le drop", ", sous-titre blanc cuit" if sh["id"].startswith("P0") else "")}
        if sh["id"] == SHOTS[-1]["id"]: it["fade_out_s"] = 0.7
        vid.append(it)
    plan = {"name": "Z3 - Archivage lazy Melenchon 2017 (Satisfaction)", "fps": 30, "w": 1080, "h": 1920, "duree_s": round(END, 3),
            "phrase": PHRASE,
            "source_phrase": "https://www.youtube.com/watch?v=yrjWwsV4zS4&t=2984 (chaîne JEAN-LUC MÉLENCHON, meeting pour la paix, Marseille 9/4/2017) 2984,96-2991,0 s",
            "note": "Plans ProRes 1080x1920 30 i/s recadrés (sources 25 i/s), aucun ralenti. Générateur : lot5/_claude/gen/Z3/genZ3.py",
            "sous_titre": {"blocs": [{"lignes": l, "t0": round(a, 3), "t1": round(b if b is not None else DROP, 3)} for a, b, l in SUBS],
                           "police": "Inter SemiBold %d px blanc, contour 2 px + ombre douce, haut du bloc à 0,56 H, interligne %d px, lignes <= 62 %% de la largeur (zone sûre TikTok x 0,17-0,83, y 0,12-0,75)" % (SUB_PX, SUB_LH)},
            "musique": {"fichier": "lot5/sons/Z3-benassi-satisfaction_complet.wav", "depart_dans_complet_s": round(M0, 3),
                        "drop_timeline_s": round(DROP, 3), "frappes_coupes_timeline_s": [round(h - M0, 3) for h in HITS]},
            "video": vid,
            "audio": [{"id": "mix", "clip": "Z3-mix.wav", "folder": "genZ3", "path": OUT + "Z3-mix.wav", "rec": 0, "track": 1,
                       "note": "mix -14 LUFS : voix du fichier forces %.2f-%.2f s à 0 s (clameur fondue après « vôtre ! ») ; musique passe-bas -12 dB sous la phrase, s'ouvre à %.1f s, pleine au drop %.3f s, fondu 0,9 s" % (VIN, VIN + VOICE_END, RISE0, DROP)}]}
    json.dump(plan, open(D + "plan-Z3.json", "w"), indent=1, ensure_ascii=False)
    son = {"titre": "Satisfaction", "artiste": "Benny Benassi", "url": "https://www.youtube.com/watch?v=a0fkNdPiIL4",
           "chaine": "Ultra Records (label, chaîne vérifiée)", "fichier": "lot5/sons/Z3-benassi-satisfaction_complet.wav",
           "extrait_debut_s": round(M0, 3), "extrait_fin_s": round(M0 + END, 3), "bpm": 130.0,
           "drop_dans_morceau_s": HITS[0], "drop_timeline_s": round(DROP, 3),
           "paroles_dans_extrait": "sous la phrase (filtré -12 dB) : riff seul puis roulement, « Push me » juste avant le drop ; après le drop : « Push me, and then just touch me, till I can get my satisfaction / Push me, and then just touch me, till I can get my satisfaction »",
           "drop": "entrée de la basse saturée après le roulement (78,01 s du morceau, ~1:18 du clip officiel), sur le refrain « Push me… satisfaction »",
           "frappes_morceau_s": HITS, "frappes_timeline_s": [round(h - M0, 3) for h in HITS]}
    json.dump(son, open(D + "son.json", "w"), indent=1, ensure_ascii=False)

def preview():
    out = HK + "/preview/apercu-Z3.mp4"; args = [FF, "-v", "error", "-y"]; fl = []
    for i, sh in enumerate(SHOTS):
        args += ["-i", OUT + sh["clip"]]; last = sh["id"] == SHOTS[-1]["id"]
        fl.append("[%d:v]trim=end_frame=%d,setpts=PTS-STARTPTS,scale=540:960,setsar=1%s[v%d]" % (
            i, sh["dur"], ",fade=t=out:st=%.3f:d=0.7" % (sh["dur"] / 30 - 0.7) if last else "", i))
    args += ["-i", OUT + "Z3-mix.wav"]
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
