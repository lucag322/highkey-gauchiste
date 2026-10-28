# P2 — Portrait (comme lot3/P1, recette « caiden.agr - portrait corridor authentique »), Sébastien Delogu, son « Murder In My Mind » (Kordhell).
# Recette : hook lent en voix diégétique synchro (captation du meeting Quartiers Nord, 08/02/2026 : la phrase entière, angles de la
# captation d'origine gardés en synchro, poussée lente), puis contextes enchaînés en coupes sèches sur les frappes réelles
# (hémicycle → meeting caméra épaule → sourire de fin), 4 temps par plan, AUCUN texte, étalonnage naturel chaud (palette #2B2B2B #8C7B6B #E8E0D4).
# Aperçu hors Resolve : plans ProRes 1080x1920 30 i/s (recadrés, poussée lente, étalonnés), mix -14 LUFS, aperçu 540x960.
# Usage : python genP2.py [plans] [audio] [apercu] [only=ID,ID]
import sys, os, json, subprocess
import numpy as np
ROOT = "/Users/luca.grousset/Movies/highkey-gauchiste"; LOT3 = ROOT + "/lot3"; LOT = ROOT + "/lot4"
sys.path.insert(0, ROOT + "/_claude/outils")
import framing
from framing import plan_views
from fx import crop_view, vignette, grain
FF = "/opt/homebrew/bin/ffmpeg"
D = LOT + "/_claude/gen/P2/"; OUT = D + "out/"; os.makedirs(OUT, exist_ok=True)
framing.ROOT = LOT3; framing.CACHE = D + "cache/faces"          # sources réutilisées du lot 3 (lecture seule)
W, H, TFPS = 1080, 1920, 30
SON = LOT + "/sons/P2-kordhell-murder-in-my-mind_complet.wav"

# ---------------- sources (lot3/sources, déjà téléchargées pour A8 ; plans et phrase différents de A8) ----------------
SRC = {
    "nordA": dict(f="A8-delogu-quartiers-nord-a.mp4", fps=25.0, yt="oKStIbwdqHc", yt_in=4680.0,
                  desc="chaîne Sébastien Delogu, meeting Quartiers Nord de la liste Marseille fière et populaire (08/02/2026), captation multicaméra"),
    "nordB": dict(f="A8-delogu-quartiers-nord-b.mp4", fps=25.0, yt="oKStIbwdqHc", yt_in=5240.0,
                  desc="chaîne Sébastien Delogu, meeting Quartiers Nord (08/02/2026), fin du meeting caméra épaule"),
    "qag": dict(f="A8-delogu-qag-gaza-2025.mp4", fps=25.0, yt="gEZLJe_uJUs", yt_in=0.0,
                desc="La France insoumise à l'Assemblée nationale, QAG Gaza 28/05/2025, plan large : seul debout dans l'hémicycle"),
}
B_FULL = (0, 0, 1920, 1080)
B_PUPITRE = (700, 0, 1280, 1010)   # plan face pupitre : « VOTEZ LES 15 & 22 MARS » + logos à gauche (x<690), encart MARSEILLE à droite (x>1290), « soutenu par » en bas (y>1015)
B_QAG = (885, 0, 1165, 800)        # QAG : logo LFI haut gauche, chrono AN haut droite, sous-titres incrustés en bas (y>810) ; fenêtre resserrée sur lui : voisins assis (x<882 et x>1168) hors champ
B_SALLE = (0, 0, 760, 1080)        # plan de salle : lui à gauche, le public (petits visages) à droite

# ---------------- temps (frappes réelles, rythme/frappes_morceau.json) ----------------
FR = json.load(open(D + "rythme/frappes_morceau.json"))
HITS = sorted(set(FR["sub"] + FR["mid"] + FR["cow"]))
DROP = 8.2                          # image 246 : entrée de la 808 (drop) du morceau, 17,012 s
MOFF = 17.012 - DROP                # temps morceau = timeline + MOFF  (extrait 8,812 → 23,812 s)
END = 15.0                          # règle lot 4 : portrait 15 s max
V = 172.75                          # voix : timeline = temps source nordA - V
VOIX = (173.20, 180.95)             # « Alors oui, c'est un lieu hautement symbolique pour moi, un jeune des quartiers nord de Marseille, passé du quartier à l'Assemblée. »
PHRASE = "Alors oui, c'est un lieu hautement symbolique pour moi, un jeune des quartiers nord de Marseille, passé du quartier à l'Assemblée."
def f30(t): return int(round(t * TFPS))

def S(i, a, b, src, t_in, t_max, hint, bnd, vh, z0, z1, fx="", note=""):
    # a, b : temps timeline (frontières d'image) ; t_in : temps source de la 1re image ; t_max : fin de la prise source (jamais d'image de la prise suivante)
    return dict(id=i, a=a, b=b, src=src, t_in=t_in, t_max=t_max, hint=hint, bnd=bnd, vh=vh, z0=z0, z1=z1, fx=fx, note=note)
SHOTS = [
    # hook : captation d'origine en synchro (coupes de la régie du meeting, calées à ±1 image sur des frappes réelles de l'intro)
    S("A", 0.0, 51 / 30, "nordA", V, 174.48, (1000, 230), B_FULL, 1080, 1.00, 1.03, "", "hook : gros plan au pupitre, voix synchro (début de la phrase), poussée lente"),
    S("B", 51 / 30, 141 / 30, "nordA", 174.48, 177.44, (230, 170), B_SALLE, 1080, 1.00, 1.03, "", "hook : plan de salle, de profil face au public des quartiers Nord, voix synchro"),
    S("C", 141 / 30, 185 / 30, "nordA", 177.44, 178.92, (1000, 230), B_FULL, 1080, 1.03, 1.05, "", "hook : gros plan, « un jeune des quartiers nord de Marseille », voix synchro"),
    S("D", 185 / 30, DROP, "nordA", 178.92, 183.88, (960, 160), B_PUPITRE, 1000, 1.00, 1.03, "", "hook : face pupitre (cadre serré sans affiche ni logo), « passé du quartier à l'Assemblée »"),
    # drop puis contextes, coupes sur les kicks réels (19,011 et 20,527 s du morceau)
    S("E", DROP, 306 / 30, "qag", 104.00, 108.60, (1009, 212), B_QAG, 498, 1.00, 1.03, "", "drop sur « l'Assemblée » : seul debout dans l'hémicycle (QAG Gaza 28/05/2025, plan large)"),
    S("F", 306 / 30, 351 / 30, "nordB", 539.64, 543.72, (370, 240), B_FULL, 1080, 1.00, 1.04, "", "meeting, caméra épaule au milieu des siens : il pointe la caméra, sourire"),
    S("G", 351 / 30, END, "nordB", 478.40, 481.80, (1100, 300), B_FULL, 1080, 1.00, 1.05, "fin", "fin : gros plan, sourire ; fondu au noir 0,6 s"),
]
for sh in SHOTS:
    sh["rec"] = f30(sh["a"]); sh["dur"] = f30(sh["b"]) - sh["rec"]
    sh["clip"] = "P2_%s.mov" % sh["id"]
def zoom_at(sh, t):
    u = min(max((t - sh["a"]) / (sh["b"] - sh["a"]), 0), 1)
    return sh["z0"] + (sh["z1"] - sh["z0"]) * u      # poussée avant régulière (jamais de dézoom)

# ---------------- étalonnage « authentique » (repris de P1 : naturel, chaud, noirs légèrement relevés) ----------------
VIG = None
def grade(img):
    global VIG
    x = np.clip((img - 0.015) * 1.04, 0, 1)
    x = x * x * (3 - 2 * x) * 0.22 + x * 0.78
    lum = x @ np.array([0.114, 0.587, 0.299], np.float32)
    x = lum[..., None] + (x - lum[..., None]) * 0.90
    x = x * np.array([0.965, 1.0, 1.03], np.float32)
    x = 0.045 + x * (0.955 - 0.045 * 0.2)
    if VIG is None: VIG = vignette(np.ones((H, W, 3), np.float32), strength=0.30, power=2.4)
    return grain(np.clip(x, 0, 1) * VIG, 0.010, 1.4)

# ---------------- rendu d'un plan ----------------
def read_frames(src, t, n):
    p = subprocess.Popen([FF, "-v", "error", "-ss", "%.4f" % t, "-i", LOT3 + "/sources/" + src, "-frames:v", str(n),
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
    s = SRC[sh["src"]]; sf = s["fps"]; n = sh["dur"]
    s0 = int(round(sh["t_in"] * sf)); spd = sf / TFPS
    n_avail = int(round(sh["t_max"] * sf)) - s0                     # images de la prise (s'arrête avant la coupe source)
    src_i = lambda k: min(int(round(k * spd)), n_avail - 1); n_src = src_i(n - 1) + 1
    tl_t = lambda k: sh["a"] + k / TFPS
    views, ok = plan_views(s["f"], s0, n, sf, speed=spd, hint=sh["hint"], bounds=sh["bnd"], vh=sh["vh"], zoom=lambda k: zoom_at(sh, tl_t(k)), top=0.16)
    frames = list(read_frames(s["f"], s0 / sf, n_src))
    w = writer(OUT + sh["clip"], TFPS)
    for k in range(n):
        fr = frames[min(src_i(k), len(frames) - 1)]
        cx, cy, vh = views[k]; vw = vh * 9 / 16
        img = grade(crop_view(fr.astype(np.float32) / 255, cx, cy, vw, W, H))
        t = tl_t(k)
        if sh["fx"] == "fin": img = img * min(max((END - t) / 0.6, 0.0), 1.0)
        w.stdin.write((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8).tobytes())
    w.stdin.close(); w.wait()
    vhs = [v[2] for v in views]
    return ("visage" if ok else "SANS VISAGE") + " vh %.0f->%.0f" % (vhs[0], vhs[-1]) + ("" if len(frames) >= n_src else " court:%d/%d" % (len(frames), n_src))

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
def build_audio():
    from scipy.signal import butter, sosfilt
    n = int(END * SR); mix = np.zeros((n, 2), np.float32)
    v = fade(load(LOT3 + "/sources/" + SRC["nordA"]["f"], VOIX[0], VOIX[1] - VOIX[0]), 0.04, 0.12)
    v = sosfilt(butter(2, 90, "high", fs=SR, output="sos"), v, axis=0).astype(np.float32)
    lv, _ = lufs(v); v *= db(-15 - lv)
    m = load(SON, MOFF, END)
    lm, _ = lufs(m[int(DROP * SR):]); m *= db(-14 - lm)
    t = np.arange(len(m)) / SR
    lo = sosfilt(butter(4, 450, "low", fs=SR, output="sos"), m, axis=0).astype(np.float32)
    # montée sous la phrase : morceau étouffé (passe-bas 450 Hz, -9 dB) qui s'ouvre peu à peu à partir de 5,5 s, plein au drop
    a = np.interp(t, [0, 5.5, DROP - 0.06, DROP], [1, 1, 0.55, 0])[:, None].astype(np.float32)
    mus = lo * db(-9) * a + m * (1 - a) * np.interp(t, [0, DROP - 0.06, DROP], [0.55, 0.55, 1.0])[:, None].astype(np.float32)
    mus *= (np.clip((END - t) / 1.2, 0, 1) ** 1.5)[:, None].astype(np.float32)
    mus = fade(mus, 0.25, 0)
    mix[:len(mus)] += mus; i0 = int((VOIX[0] - V) * SR); mix[i0:i0 + len(v)] += v[:n - i0]
    tmp = OUT + "_tmp_mix.wav"; sf_write(tmp, mix); g = 0.0; li, _ = lufs(mix)
    for _ in range(4):
        g += -14.0 - li
        subprocess.run([FF, "-v", "error", "-y", "-i", tmp, "-af", "volume=%.2fdB,alimiter=limit=0.80:attack=3:release=60:level=false,aresample=192000,alimiter=limit=0.82:attack=1:release=40:level=false,aresample=48000" % g,
                        "-c:a", "pcm_s24le", OUT + "P2-mix.wav"], check=True)
        li, tp = lufs(load(OUT + "P2-mix.wav"))
        if abs(li + 14) < 0.3 and tp < -1.0: break
    os.remove(tmp)
    return "mix %.1f LUFS, true peak %.1f dBTP" % (li, tp)

# ---------------- frappes en temps timeline + plan-P2.json ----------------
def hits_tl(kind=None):
    L = HITS if kind is None else FR[kind]
    return [round(h - MOFF, 3) for h in L if 0 <= h - MOFF <= END]
def write_plan():
    vid = []
    for sh in SHOTS:
        s = SRC[sh["src"]]; used = sh["dur"] / TFPS
        vid.append({"id": sh["id"], "clip": sh["clip"], "folder": "P2", "path": OUT + sh["clip"], "s": 0, "e": sh["dur"], "clip_fps": TFPS,
                    "rec": sh["rec"], "dur": sh["dur"], "track": 1, "speed_pct": 100, "note": sh["note"],
                    "source": {"fichier": "lot3/sources/" + s["f"], "in_s": round(sh["t_in"], 3), "out_s": round(min(sh["t_in"] + used, sh["t_max"]), 3),
                               "youtube": "https://youtu.be/%s?t=%d" % (s["yt"], int(s["yt_in"] + sh["t_in"])), "desc": s["desc"]},
                    "effets": "recadrage 9:16 suivi visage, poussée x%.2f -> x%.2f, étalonnage naturel chaud%s" % (sh["z0"], sh["z1"], ", fondu au noir 0,6 s cuit" if sh["fx"] == "fin" else ""),
                    "coupe_sur_frappe_s": round(sh["a"], 3)})
    plan = {"name": "P2 - Portrait - Delogu", "fps": 30, "w": 1080, "h": 1920, "duree_s": END,
            "note": "Lot 4, recette caiden.agr (portrait) comme lot3/P1 : hook lent en voix diégétique synchro (meeting Quartiers Nord, angles de la captation d'origine), drop sur « l'Assemblée » puis hémicycle / meeting caméra épaule / sourire en coupes sèches sur les frappes réelles, aucun texte. Plans ProRes 9:16 30 i/s prêts, aucun ralenti (speed_pct 100). Générateur : lot4/_claude/gen/P2/genP2.py",
            "musique": {"fichier": "lot4/sons/P2-kordhell-murder-in-my-mind_complet.wav", "debut_extrait_s": round(MOFF, 3), "fin_extrait_s": round(MOFF + END, 3),
                        "drop_timeline_s": DROP, "coupes_timeline_s": [round(sh["a"], 3) for sh in SHOTS[1:]],
                        "sous_la_voix": "passe-bas 450 Hz -9 dB, s'ouvre de 5,5 s au drop (montée), plein au drop"},
            "phrase": {"source": "https://youtu.be/oKStIbwdqHc?t=%d (meeting Quartiers Nord 08/02/2026, %.2f-%.2f s de la vidéo)" % (4680 + 173, 4680 + 173.28, 4680 + 180.80),
                       "texte": PHRASE, "timeline_s": [round(173.28 - V, 2), round(180.80 - V, 2)]},
            "video": vid,
            "audio": [{"id": "mix", "clip": "P2-mix.wav", "folder": "P2", "path": OUT + "P2-mix.wav", "rec": 0, "track": 1,
                       "note": "mix final -14 LUFS : voix %.2f-%.2f s sur le morceau étouffé qui monte, morceau plein au drop %.3f s, fondu de fin" % (173.28 - V, 180.80 - V, DROP)}]}
    json.dump(plan, open(D + "plan-P2.json", "w"), indent=1, ensure_ascii=False)
    json.dump({"MOFF": round(MOFF, 3), "drop_tl": DROP, "coupes_tl": [round(sh["a"], 3) for sh in SHOTS[1:]], "frappes_tl": hits_tl(),
               "kicks_tl": hits_tl("sub")}, open(D + "rythme/frappes_tl.json", "w"), indent=0)

# ---------------- aperçu ffmpeg 540x960 ----------------
def preview():
    out = ROOT + "/preview/apercu-P2.mp4"; args = [FF, "-v", "error", "-y"]; fl = []
    for i, sh in enumerate(SHOTS):
        args += ["-i", OUT + sh["clip"]]
        fl.append("[%d:v]trim=end_frame=%d,setpts=PTS-STARTPTS,scale=540:960,setsar=1[v%d]" % (i, sh["dur"], i))
    args += ["-i", OUT + "P2-mix.wav"]
    fl.append("".join("[v%d]" % i for i in range(len(SHOTS))) + "concat=n=%d:v=1:a=0[v]" % len(SHOTS))
    args += ["-filter_complex", ";".join(fl), "-map", "[v]", "-map", "%d:a" % len(SHOTS), "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p",
             "-r", "30", "-c:a", "aac", "-b:a", "192k", "-shortest", out]
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
    write_plan()
    if "apercu" in sys.argv: print(preview())
    print("total", sum(s["dur"] for s in SHOTS) / 30, "s ;", len(SHOTS), "plans ; plus court", min(s["dur"] for s in SHOTS) / 30, "s")
