# Z1 — Archivage lazy (recette prepa85), Mélenchon, son Gigi D'Agostino – L'Amour Toujours.
# Bloc 1 : un seul plan discours (Marseille, 9/4/2017), voix audible + sous-titres blancs natifs, musique filtrée et baissée dessous (montée).
# v2 (retour Luca « ça dégage rien, drop pas au bon moment ») : drop sur le RIFF SYNTHÉ (1re frappe du riff complet, 34,38 s du morceau,
# ~0:36 de la vidéo officielle) ; coupes sèches sur les vraies frappes du riff ; bloom/glow sur les zones claires, fort au drop puis qui
# retombe (petit rebond sur chaque coupe) ; poussées avant (ease-in) qui finissent sur la frappe de la coupe suivante. Jamais de dézoom.
# Archives : Vieux-Port 2017, place de la République 18/3/2017, couleurs d'origine.
# Usage : python genZ1.py [plans] [audio] [apercu] [only=ID,ID]
import sys, os, json, subprocess
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
HK = "/Users/luca.grousset/Movies/highkey-gauchiste"; L3 = HK + "/lot3"
sys.path.insert(0, HK + "/_claude/outils"); sys.path.insert(0, HK + "/lot2/_claude/gen/C1")
import framing
from fx import crop_view
from temps_forts import attaques, load as tf_load
FF = "/opt/homebrew/bin/ffmpeg"
D = L3 + "/_claude/gen/Z1/"; OUT = D + "out/"; os.makedirs(OUT, exist_ok=True)
framing.CACHE = D + "cache/faces"                          # cache visages dans notre dossier (règle : n'écrire que dans gen/Z1)
REL = "../lot3/sources/"
SRC = {"riches": "Z1-marseille2017-riches.mp4", "md": "Z1-marseille2017-debut.mp4", "mf": "Z1-marseille2017-fin.mp4",
       "rf": "Z1-republique2017-fin.mp4"}
ORIG = {"riches": ("yrjWwsV4zS4", 2640), "md": ("yrjWwsV4zS4", 0), "mf": ("yrjWwsV4zS4", 3515), "rf": ("b5atq_VZd2M", 3690)}
BOUNDS = {"riches": (0, 0, 1620, 895),                     # sous-titres incrustés y > 900, interprète LSF x > 1630
          "md": (0, 0, 1920, 1080), "mf": (0, 0, 1920, 900), "rf": (0, 0, 1920, 880)}   # bandeau de sous-titres en bas
SFPS = 25; W, H, TFPS = 1080, 1920, 30
def f30(t): return int(round(t * TFPS))

# ---------------- son ----------------
MUSIC = L3 + "/sons/Z1-gigi-dagostino-lamour-toujours_complet.wav"
HOOK = 34.380                                               # 1re frappe du riff synthé complet (kick + riff), mesurée
PER = 0.43104                                               # 139,2 BPM (34,380 -> 44,725 en 24 temps)
BEATS = [0, 2, 4, 6, 7, 8, 10, 12, 14, 15, 16, 20, 24]      # temps après le drop où l'on coupe (dernier = fin)
_att = [a for a, s in attaques(tf_load(MUSIC, 32.0, 16.0), 32.0, 4.0)]
def snap(t):
    a = min(_att, key=lambda x: abs(x - t)); assert abs(a - t) < 0.03, ("pas de frappe près de", t); return a
HITS = [snap(HOOK + PER * j) for j in BEATS]                # vraies frappes (temps du morceau)
# position du drop dans la timeline : ~7,1 s (fin du plan long), choisie pour que toutes les frappes tombent au plus près d'une image
BIAS = 0.004                                                # retard mesuré des attaques sur l'export (AAC + fenêtres 5 ms)
def err(dt): return max(abs((h - HITS[0] + dt + BIAS) * TFPS - round((h - HITS[0] + dt) * TFPS)) for h in HITS)
DROP = min((6.95 + k / 1000 for k in range(0, 201)), key=err)
M0 = HITS[0] - DROP                                         # temps du morceau à t=0 timeline
CUTF = [f30(h - M0) for h in HITS]; END = CUTF[-1] / TFPS
VIN = 6.00; V = VIN                                         # voix : Z1-marseille2017-riches.mp4, timeline = fichier - 6,00
SENT_END = 10.80 - V                                        # fin de « moyens. » (énergie mesurée 2650,80 s)

# ---------------- sous-titre natif (blanc, 3 lignes, sans animation) ----------------
# Zone sûre TikTok : bloc centré <= 66 % de large (lignes <= 670 px, x 0,17-0,83) et entre y 0,12 et 0,75 -> 3 lignes en 70 px, bas du bloc vers y 1390.
SUB = ["Les riches en France", "vivent au-dessus", "de nos moyens."]
SUB_PX, SUB_Y0, SUB_LH = 70, 1128, 92
SUB_T0, SUB_T1 = 0.0, SENT_END + 0.45
FONT = "/Users/luca.grousset/Library/Fonts/Inter-VariableFont_opsz,wght.ttf"
def sub_font(px):
    f = ImageFont.truetype(FONT, px)
    try: f.set_variation_by_axes([32, 600])               # opsz, wght (SemiBold)
    except Exception: pass
    return f
_SUBL = None
def sub_layer():
    global _SUBL
    if _SUBL is None:
        f = sub_font(SUB_PX); lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dr = ImageDraw.Draw(lay)
        sh = Image.new("L", (W, H), 0); ds = ImageDraw.Draw(sh); y0 = SUB_Y0; lh = SUB_LH
        for i, line in enumerate(SUB):
            ds.text((W / 2, y0 + i * lh), line, font=f, anchor="ma", fill=200, stroke_width=4, stroke_fill=200)
            dr.text((W / 2, y0 + i * lh), line, font=f, anchor="ma", fill=(255, 255, 255, 255), stroke_width=2, stroke_fill=(20, 20, 20, 255))
        m = np.asarray(sh.filter(ImageFilter.GaussianBlur(6)), np.float32)[..., None] / 255
        a = np.asarray(lay, np.float32) / 255
        _SUBL = (m, a)
    return _SUBL
def draw_sub(img, t):
    if not (SUB_T0 <= t < SUB_T1): return img
    m, a = sub_layer(); out = img * (1 - 0.55 * m)
    return out * (1 - a[..., 3:4]) + a[..., [2, 1, 0]] * a[..., 3:4]

# ---------------- effets : bloom + poussées avant ----------------
CUT_T = [c / TFPS for c in CUTF[:-1]]                       # temps des coupes (frappes) après le drop
def bloom_k(t):
    if t < DROP: return 0.08 + 0.30 * np.clip((t - SENT_END) / (DROP - SENT_END), 0, 1) ** 2      # montée pendant l'ovation
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
ZOOM = {"P0": 0.07}                                          # poussée avant totale par plan (défaut B-roll ci-dessous)
def zoom_amt(sh): return ZOOM.get(sh["id"], 0.06 if sh["dur"] < 20 else 0.10)

# ---------------- plans ----------------
def S(i, src, t_in, mode, c, note, bd=None): return dict(id=i, src=src, t_in=t_in, mode=mode, c=c, note=note, bd=bd or BOUNDS[src])
FULL = (0, 0, 1920, 1080)                                   # fin du meeting de Marseille après 41 s : plus de sous-titres ni d'interprète
SHOTS = [S("P0", "riches", VIN, "face", (760, 340), "Plan long unique : Mélenchon, Vieux-Port 9/4/2017, phrase + ovation, sous-titre blanc")]
BROLL = [
    S("B01", "md", 16.3, "fix", (1350, 540), "Vieux-Port, marée humaine, scène et grande roue (drop sur le riff)"),
    S("B02", "md", 51.0, "fix", (900, 540), "drapeaux et pancartes phi"),
    S("B03", "rf", 125.0, "fix", (930, 520), "République 18/3/2017, statue de la République au-dessus de la foule"),
    S("B04", "mf", 72.0, "fix", (960, 540), "Vieux-Port, drapeaux", FULL),
    S("B05", "rf", 84.0, "fix", (960, 440), "République, foule et drapeaux"),
    S("B06", "md", 71.6, "face", (1050, 270), "Mélenchon au pupitre, drapeaux"),
    S("B07", "md", 67.6, "fix", (1100, 600), "foule vue d'un immeuble"),
    S("B08", "rf", 9.0, "fix", (960, 540), "République, foule et drapeaux"),
    S("B09", "md", 45.0, "fix", (960, 600), "marée de drapeaux devant le port"),
    S("B10", "md", 28.0, "fix", (1000, 540), "drapeaux, pancartes"),
    S("B11", "mf", 94.2, "fix", (1215, 540), "Mélenchon bras levé vers la foule", FULL),
    S("B12", "mf", 52.0, "fix", (960, 540), "foule et drapeaux devant la mer, fondu au noir", FULL),
]
SHOTS += BROLL
bounds_rec = [0] + CUTF
for k, sh in enumerate(SHOTS):
    sh["rec"] = bounds_rec[k]; sh["dur"] = bounds_rec[k + 1] - bounds_rec[k]
    sh["clip"] = "Z1_%s.mov" % sh["id"]
    sh["n_src"] = int(np.ceil(sh["dur"] / TFPS * SFPS)) + 1
assert len(SHOTS) == len(CUTF)
assert min(s["dur"] for s in SHOTS) >= 12, "plan < 1 temps"

def read_frames(src, t, n):                                   # images 30 i/s (duplication 25 -> 30), comme la timeline
    p = subprocess.Popen([FF, "-v", "error", "-ss", "%.4f" % t, "-i", L3 + "/sources/" + SRC[src], "-vf", "fps=30", "-frames:v", str(n),
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
    zf = lambda f: 1 + A * (min(f, ns - 1) / max(ns - 1, 1)) ** 2   # ease-in : la poussée finit sur la frappe de la coupe suivante
    kw = dict(speed=1.0, hint=sh["c"], bounds=bd, vh=bd[3] - bd[1], zoom=zf)
    if sh["mode"] == "fix": kw["fixed"] = sh["c"]
    views, ok = framing.plan_views(REL + SRC[sh["src"]], s, sh["n_src"], SFPS, **kw)
    info = ("visage" if ok else "SANS VISAGE") if sh["mode"] == "face" else "fixe"
    xs = [v[0] - v[2] * 9 / 32 for v in views] + [v[0] + v[2] * 9 / 32 for v in views]
    info += " x %d-%d vh %d" % (min(xs), max(xs), views[0][2]); k = 0
    for fr in read_frames(sh["src"], sh["t_in"], n):
        cx, cy, vh = views[min(int(k * SFPS / TFPS), len(views) - 1)]
        img = crop_view(fr.astype(np.float32) / 255, cx, cy, vh * 9 / 16, W, H)
        img = bloom(img, bloom_k((sh["rec"] + k) / TFPS))
        if sh["id"] == "P0": img = draw_sub(img, k / TFPS)
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
def build_audio():
    from scipy.signal import butter, sosfilt
    n = int(END * SR); t = np.arange(n) / SR
    vd = DROP + 0.35                                          # la clameur déborde un peu sur le drop, puis s'efface
    voice = load(L3 + "/sources/" + SRC["riches"], VIN, vd)[:int(vd * SR)]
    a = np.ones(len(voice), np.float32); k = int(0.35 * SR); a[-k:] = np.linspace(1, 0, k) ** 2; voice *= a[:, None]
    mus = load(MUSIC, M0, END + 0.05)[:n]
    lv, _ = lufs(voice[:int(SENT_END * SR)]); lm, _ = lufs(load(MUSIC, 34.4, 10.0))
    voice *= db(-15 - lv); mus *= db(-14 - lm)
    # sous la phrase : musique passe-bas 500 Hz à -12 dB ; montée pendant l'ovation (ouverture progressive), pleine au drop
    lp = sosfilt(butter(4, 500, "low", fs=SR, output="sos"), mus, axis=0).astype(np.float32)
    x = np.clip((t - SENT_END) / (DROP - SENT_END), 0, 1) * 0.45
    x = np.where(t >= DROP - 0.002, 1.0, x)[:, None].astype(np.float32)
    g = (db(-12) + (1 - db(-12)) * x).astype(np.float32)
    fo = (np.clip((END - t) / 0.9, 0, 1) ** 1.5)[:, None].astype(np.float32)
    mix = (lp * (1 - x) + mus * x) * g * fo
    mix[:len(voice)] += voice[:n]
    tmp = OUT + "_tmp_mix.wav"; sf_write(tmp, mix); gain = 0.0; li, _ = lufs(mix)
    for _ in range(4):
        gain += -14.0 - li
        subprocess.run([FF, "-v", "error", "-y", "-i", tmp, "-af", "volume=%.2fdB,alimiter=limit=0.80:attack=3:release=60:level=false,aresample=192000,alimiter=limit=0.82:attack=1:release=40:level=false,aresample=48000" % gain,
                        "-c:a", "pcm_s24le", OUT + "Z1-mix.wav"], check=True)
        li, tp = lufs(load(OUT + "Z1-mix.wav"))
        if abs(li + 14) < 0.3 and tp < -1.0: break
    os.remove(tmp); sf_write(OUT + "Z1-musique-posee.wav", (lp * (1 - x) + mus * x) * g * fo)
    return "mix %.1f LUFS, true peak %.1f dBTP (voix %.1f, refrain %.1f d'origine)" % (li, tp, lv, lm)

# ---------------- plan-Z1.json + son.json ----------------
def write_plan():
    vid = []
    for sh in SHOTS:
        yid, off = ORIG[sh["src"]]; used = sh["dur"] / TFPS
        it = {"id": sh["id"], "clip": sh["clip"], "folder": "genZ1", "path": OUT + sh["clip"], "s": 0, "e": sh["dur"], "clip_fps": 30,
              "rec": sh["rec"], "dur": sh["dur"], "track": 1, "speed_pct": 100, "note": sh["note"],
              "source": {"fichier": "lot3/sources/" + SRC[sh["src"]], "in_s": round(sh["t_in"], 3), "out_s": round(sh["t_in"] + used, 3),
                         "youtube": "https://www.youtube.com/watch?v=%s&t=%d" % (yid, int(off + sh["t_in"]))},
              "effets": "recadrage 9:16 %s, poussée avant ease-in 1,00->%.2f finissant sur la frappe, bloom couleur des zones claires (fort au drop puis retombe), couleurs d'origine%s" % ("suivi visage" if sh["mode"] == "face" else "fixe", 1 + zoom_amt(sh),
                                                                                   ", sous-titre blanc cuit" if sh["id"] == "P0" else "")}
        if sh["id"] == SHOTS[-1]["id"]: it["fade_out_s"] = 0.7
        vid.append(it)
    plan = {"name": "Z1 - Archivage lazy Melenchon (L'Amour Toujours)", "fps": 30, "w": 1080, "h": 1920, "duree_s": round(END, 3),
            "phrase": "Les riches en France vivent au-dessus de nos moyens.",
            "source_phrase": "https://www.youtube.com/watch?v=yrjWwsV4zS4 (chaîne JEAN-LUC MÉLENCHON, meeting pour la paix, Marseille 9/4/2017) 2646,05-2650,80 s",
            "note": "Plans ProRes 1080x1920 30 i/s recadrés (sources 25 i/s), aucun ralenti. Générateur : lot3/_claude/gen/Z1/genZ1.py",
            "sous_titre": {"lignes": SUB, "t0": SUB_T0, "t1": round(SUB_T1, 3), "police": "Inter SemiBold %d px blanc, contour 2 px + ombre douce, haut du bloc y = %d (%.3f H), interligne %d px : zone sûre TikTok x 0,17-0,83, y 0,12-0,75" % (SUB_PX, SUB_Y0, SUB_Y0 / H, SUB_LH)},
            "musique": {"fichier": "lot3/sons/Z1-gigi-dagostino-lamour-toujours_complet.wav", "depart_dans_complet_s": round(M0, 3),
                        "drop_timeline_s": round(DROP, 3), "frappes_coupes_timeline_s": [round(h - M0, 3) for h in HITS]},
            "video": vid,
            "audio": [{"id": "mix", "clip": "Z1-mix.wav", "folder": "genZ1", "path": OUT + "Z1-mix.wav", "rec": 0, "track": 1,
                       "note": "mix -14 LUFS : voix + ovation du fichier riches 6,00-%.2f s à 0 s ; musique passe-bas -12 dB sous la phrase, montée pendant l'ovation, pleine au drop %.3f s, fondu 0,9 s" % (VIN + DROP + 0.35, DROP)}]}
    json.dump(plan, open(D + "plan-Z1.json", "w"), indent=1, ensure_ascii=False)
    son = {"titre": "L'Amour Toujours", "artiste": "Gigi D'Agostino", "url": "https://youtu.be/w15oWDh02K4",
           "chaine": "GIGI D'AGOSTINO (officielle)", "fichier": "lot3/sons/Z1-gigi-dagostino-lamour-toujours_complet.wav",
           "extrait_debut_s": round(M0, 3), "extrait_fin_s": round(M0 + END, 3), "bpm": 139.0,
           "drop_dans_morceau_s": HITS[0], "drop_timeline_s": round(DROP, 3),
           "paroles_dans_extrait": "aucune : intro (riff seul, filtré à -12 dB sous la phrase, montée sur la fin) puis riff synthé complet avec kick dès le drop ; la voix du morceau ne commence qu'à 54,7 s",
           "drop": "1re frappe du riff synthé complet (34,38 s du morceau, ~0:36 de la vidéo officielle)",
           "frappes_morceau_s": HITS, "frappes_timeline_s": [round(h - M0, 3) for h in HITS]}
    json.dump(son, open(D + "son.json", "w"), indent=1, ensure_ascii=False)

def preview():
    out = HK + "/preview/apercu-Z1.mp4"; args = [FF, "-v", "error", "-y"]; fl = []
    for i, sh in enumerate(SHOTS):
        args += ["-i", OUT + sh["clip"]]; last = sh["id"] == SHOTS[-1]["id"]
        fl.append("[%d:v]trim=end_frame=%d,setpts=PTS-STARTPTS,scale=540:960,setsar=1%s[v%d]" % (
            i, sh["dur"], ",fade=t=out:st=%.3f:d=0.7" % (sh["dur"] / 30 - 0.7) if last else "", i))
    args += ["-i", OUT + "Z1-mix.wav"]
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
    if "plans" in sys.argv:
        for sh in SHOTS:
            if only and sh["id"] not in only: continue
            print(sh["id"], sh["rec"], sh["dur"], render(sh), flush=True)
    if "audio" in sys.argv: print(build_audio())
    write_plan()
    if "apercu" in sys.argv: print(preview())
