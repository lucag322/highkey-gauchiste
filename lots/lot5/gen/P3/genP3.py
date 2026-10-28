# P3 — Portrait (comme lot3/P1 et lot4/P2, recette « caiden.agr - portrait corridor authentique »), Manuel Bompard,
# son « I Don't Like » (Chief Keef ft. Lil Reese).
# Recette : hook lent en voix diégétique synchro (QAG du 20/10/2026 face à Nuñez, la phrase entière, angles LCP d'origine gardés
# en synchro, poussée lente), puis contextes enchaînés en coupes sèches sur les frappes réelles : arrivée dans la foule
# (réunion publique d'Angoulême, caméra épaule) → plateau TV (C à vous) → pupitre d'Angoulême → Internationale sur scène.
# AUCUN texte, étalonnage naturel chaud (palette #2B2B2B #8C7B6B #E8E0D4). Autre phrase et autres plans que A2 (convention LFI).
# Aperçu hors Resolve : plans ProRes 1080x1920 30 i/s (recadrés, poussée lente, étalonnés), mix -14 LUFS, aperçu 540x960.
# Usage : python genP3.py [plans] [audio] [apercu] [only=ID,ID]
import sys, os, json, subprocess
import numpy as np
ROOT = "/Users/luca.grousset/Movies/highkey-gauchiste"; LOT = ROOT + "/lot5"
sys.path.insert(0, ROOT + "/_claude/outils")
import framing
from framing import plan_views
from fx import crop_view, vignette, grain
FF = "/opt/homebrew/bin/ffmpeg"
D = LOT + "/_claude/gen/P3/"; OUT = D + "out/"; os.makedirs(OUT, exist_ok=True)
framing.CACHE = D + "cache/faces"          # cache propre à P3 (les sources des lots 1-4 sont lues, jamais modifiées)
W, H, TFPS = 1080, 1920, 30
SON = LOT + "/sons/P3-chief-keef-i-dont-like_complet.wav"

# ---------------- sources ----------------
SRC = {
    "qag": dict(lot="lot1", f="2-bompard-nunez-qag.mp4", fps=25.0, yt="6KmW4swF4Uk", yt_in=0.0,
                desc="LCP - Assemblée nationale, QAG 20/10/2026, Bompard face à Laurent Nuñez (déjà au lot 1 ; phrase et plans 64,7-70,9 s jamais utilisés)"),
    "arr": dict(lot="lot5", f="P3-bompard-angouleme-arrivee.mp4", fps=30.0, yt="ATRtW3ULK1U", yt_in=1836.0,
                desc="La France insoumise, réunion publique à Angoulême avec Manuel Bompard (30/09/2026), arrivée dans la salle, caméra épaule"),
    "pup": dict(lot="lot5", f="P3-bompard-angouleme-pupitre.mp4", fps=30.0, yt="ATRtW3ULK1U", yt_in=1872.0,
                desc="La France insoumise, réunion publique à Angoulême (30/09/2026), au pupitre"),
    "fin": dict(lot="lot5", f="P3-bompard-angouleme-final.mp4", fps=30.0, yt="ATRtW3ULK1U", yt_in=4632.0,
                desc="La France insoumise, réunion publique à Angoulême (30/09/2026), Internationale sur scène"),
    "cav": dict(lot="lot5", f="P3-bompard-cavous-plateau.mp4", fps=25.0, yt="Ri9XYs1F98U", yt_in=10.0,
                desc="C à vous - France Télévisions (06/10/2026), « Lycées : Manuel Bompard dans la manifestation à Paris », plateau"),
}
def src_path(k): return ROOT + "/" + SRC[k]["lot"] + "/sources/" + SRC[k]["f"]
# zones source autorisées (sans logo, sans bandeau, sans visage voisin coupé)
B_QAG = (620, 0, 1190, 1080)        # QAG gros plan : logo LCP haut gauche, chrono AN haut droite ; voisins (femme à g. x<600, femme derrière à dr. x>1140)
B_QAGW = (560, 0, 1350, 1080)       # QAG plan large : logo LCP (x<290, y<230) et chrono (x>1560) hors champ ; lui debout vers x 910, vue centrée en 860 (aucune tête coupée au bord) ; vue pleine hauteur (visages du public < 5 %)
B_ARR = (720, 0, 1580, 1080)        # arrivée : public au premier plan à gauche (x<715), filigrane MELENCHON2027.fr haut droite (x>1590, y<170)
B_CAV = (250, 0, 1500, 965)         # C à vous : bandeau rouge en bas (y>975), logo C bas gauche (x<240, y>880), logo france.tv haut droite (x>1520)
B_PUP = (300, 0, 1560, 820)          # pupitre : filigrane haut droite (x>1570) ; panneau « ANGOULÊME » du pupitre (y>835) hors champ (texte sous l interface TikTok)
B_FIN = (560, 0, 915, 1080)         # Internationale (plan de face) : voisine en rouge (x<505) et M. aux cheveux gris (x>925) hors champ, filigrane hors champ

# ---------------- temps (frappes réelles, rythme/frappes_morceau.json) ----------------
FR = json.load(open(D + "rythme/frappes_morceau.json"))
HITS = sorted(set(FR["sub"] + FR["mid"] + FR["low"]))
DROP = 170 / 30                     # image 170 : entrée de la 808 (drop) du morceau, 36,918 s
MOFF = 36.918 - DROP                # temps morceau = timeline + MOFF  (extrait 31,251 → 46,251 s)
END = 15.0                          # portrait 15 s max
V = 64.68                           # voix : timeline = temps source qag - V ; coupe régie LCP 67,68 s = image 90 (frappe 34,238 s du morceau)
VOIX = (64.80, 70.05)               # « Il n'y a pas d'autre réponse à une crise politique qu'une réponse politique. »
PHRASE = "Il n'y a pas d'autre réponse à une crise politique qu'une réponse politique."
def f30(t): return int(round(t * TFPS))

def S(i, a, b, src, t_in, t_max, hint, bnd, vh, z0, z1, fx="", note=""):
    # a, b : temps timeline (frontières d'image) ; t_in : temps source de la 1re image ; t_max : fin de la prise source (jamais d'image de la prise suivante)
    return dict(id=i, a=a, b=b, src=src, t_in=t_in, t_max=t_max, hint=hint, bnd=bnd, vh=vh, z0=z0, z1=z1, fx=fx, note=note)
SHOTS = [
    # hook : captation LCP d'origine en synchro (coupe de la régie à 67,68 s, tombe sur une frappe réelle de l'intro)
    S("A", 0.0, 90 / 30, "qag", V, 67.64, (900, 300), B_QAG, 830, 1.00, 1.03, "", "hook : à son banc, gros plan, voix synchro « Il n'y a pas d'autre réponse à une crise politique »"),
    S("B", 90 / 30, DROP, "qag", 67.68, 70.92, (860, 450), B_QAGW, 1080, 1.00, 1.03, "", "hook : plan large LCP, seul debout dans l'hémicycle, voix synchro « qu'une réponse politique »"),
    # drop puis contextes, coupes sur les frappes réelles (39,191 / 41,237 / 43,283 s du morceau)
    S("E", DROP, 238 / 30, "arr", 3.10, 6.33, (990, 330), B_ARR, 1000, 1.00, 1.04, "", "drop : arrivée à Angoulême au milieu du public qui applaudit (caméra épaule)"),
    S("F", 238 / 30, 300 / 30, "cav", 48.00, 72.48, (830, 340), B_CAV, 965, 1.00, 1.04, "", "plateau TV (C à vous), gros plan, il explique les mains ouvertes"),
    S("G", 300 / 30, 361 / 30, "pup", 13.37, 15.40, (960, 300), B_PUP, 820, 1.00, 1.04, "", "pupitre d'Angoulême, geste ample"),
    S("H", 361 / 30, END, "fin", 53.90, 58.83, (740, 290), B_FIN, 631, 1.00, 1.04, "fin", "fin : sur scène, il chante l'Internationale avec les insoumis, poings levés autour ; fondu au noir 0,6 s"),
]
for sh in SHOTS:
    sh["rec"] = f30(sh["a"]); sh["dur"] = f30(sh["b"]) - sh["rec"]
    sh["clip"] = "P3_%s.mov" % sh["id"]
def zoom_at(sh, t):
    u = min(max((t - sh["a"]) / (sh["b"] - sh["a"]), 0), 1)
    return sh["z0"] + (sh["z1"] - sh["z0"]) * u      # poussée avant régulière (jamais de dézoom)

# ---------------- étalonnage « authentique » (repris de P1/P2 : naturel, chaud, noirs légèrement relevés) ----------------
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
def read_frames(path, t, n):
    p = subprocess.Popen([FF, "-v", "error", "-ss", "%.4f" % t, "-i", path, "-frames:v", str(n),
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
    framing.ROOT = ROOT + "/" + s["lot"]                           # framing lit ROOT/sources/<fichier>
    views, ok = plan_views(s["f"], s0, n, sf, speed=spd, hint=sh["hint"], bounds=sh["bnd"], vh=sh["vh"], zoom=lambda k: zoom_at(sh, tl_t(k)), top=0.16)
    frames = list(read_frames(src_path(sh["src"]), s0 / sf, n_src))
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
    v = fade(load(src_path("qag"), VOIX[0], VOIX[1] - VOIX[0]), 0.04, 0.15)
    v = sosfilt(butter(2, 90, "high", fs=SR, output="sos"), v, axis=0).astype(np.float32)
    lv, _ = lufs(v); v *= db(-15 - lv)
    m = load(SON, MOFF, END)
    lm, _ = lufs(m[int(DROP * SR):]); m *= db(-14 - lm)
    t = np.arange(len(m)) / SR
    lo = sosfilt(butter(4, 450, "low", fs=SR, output="sos"), m, axis=0).astype(np.float32)
    # montée sous la phrase : morceau étouffé (passe-bas 450 Hz, -9 dB) qui s'ouvre peu à peu à partir de 3,6 s, plein au drop
    a = np.interp(t, [0, 3.6, DROP - 0.06, DROP], [1, 1, 0.55, 0])[:, None].astype(np.float32)
    mus = lo * db(-9) * a + m * (1 - a) * np.interp(t, [0, DROP - 0.06, DROP], [0.55, 0.55, 1.0])[:, None].astype(np.float32)
    mus *= (np.clip((END - t) / 1.2, 0, 1) ** 1.5)[:, None].astype(np.float32)
    mus = fade(mus, 0.25, 0)
    mix[:len(mus)] += mus; i0 = int((VOIX[0] - V) * SR); mix[i0:i0 + len(v)] += v[:n - i0]
    tmp = OUT + "_tmp_mix.wav"; sf_write(tmp, mix); g = 0.0; li, _ = lufs(mix)
    for _ in range(4):
        g += -14.0 - li
        subprocess.run([FF, "-v", "error", "-y", "-i", tmp, "-af", "volume=%.2fdB,alimiter=limit=0.80:attack=3:release=60:level=false,aresample=192000,alimiter=limit=0.82:attack=1:release=40:level=false,aresample=48000" % g,
                        "-c:a", "pcm_s24le", OUT + "P3-mix.wav"], check=True)
        li, tp = lufs(load(OUT + "P3-mix.wav"))
        if abs(li + 14) < 0.3 and tp < -1.0: break
    os.remove(tmp)
    return "mix %.1f LUFS, true peak %.1f dBTP" % (li, tp)

# ---------------- frappes en temps timeline + plan-P3.json ----------------
def hits_tl(kind=None):
    L = HITS if kind is None else FR[kind]
    return [round(h - MOFF, 3) for h in L if 0 <= h - MOFF <= END]
def write_plan():
    vid = []
    for sh in SHOTS:
        s = SRC[sh["src"]]; used = sh["dur"] / TFPS
        vid.append({"id": sh["id"], "clip": sh["clip"], "folder": "P3", "path": OUT + sh["clip"], "s": 0, "e": sh["dur"], "clip_fps": TFPS,
                    "rec": sh["rec"], "dur": sh["dur"], "track": 1, "speed_pct": 100, "note": sh["note"],
                    "source": {"fichier": s["lot"] + "/sources/" + s["f"], "in_s": round(sh["t_in"], 3), "out_s": round(min(sh["t_in"] + used, sh["t_max"]), 3),
                               "youtube": "https://youtu.be/%s?t=%d" % (s["yt"], int(s["yt_in"] + sh["t_in"])), "desc": s["desc"]},
                    "effets": "recadrage 9:16 suivi visage, poussée x%.2f -> x%.2f, étalonnage naturel chaud%s" % (sh["z0"], sh["z1"], ", fondu au noir 0,6 s cuit" if sh["fx"] == "fin" else ""),
                    "coupe_sur_frappe_s": round(sh["a"], 3)})
    plan = {"name": "P3 - Portrait - Bompard", "fps": 30, "w": 1080, "h": 1920, "duree_s": END,
            "note": "Lot 5, recette caiden.agr (portrait) comme lot3/P1 et lot4/P2 : hook lent en voix diégétique synchro (QAG LCP 20/10/2026, angles de la captation d'origine), drop après « réponse politique » puis arrivée dans la foule à Angoulême / plateau C à vous / pupitre / Internationale en coupes sèches sur les frappes réelles, aucun texte. Plans ProRes 9:16 30 i/s prêts, aucun ralenti (speed_pct 100). Générateur : lot5/_claude/gen/P3/genP3.py",
            "musique": {"fichier": "lot5/sons/P3-chief-keef-i-dont-like_complet.wav", "debut_extrait_s": round(MOFF, 3), "fin_extrait_s": round(MOFF + END, 3),
                        "drop_timeline_s": round(DROP, 3), "coupes_timeline_s": [round(sh["a"], 3) for sh in SHOTS[1:]],
                        "sous_la_voix": "passe-bas 450 Hz -9 dB, s'ouvre de 3,6 s au drop (montée), plein au drop"},
            "phrase": {"source": "https://youtu.be/6KmW4swF4Uk?t=64 (QAG LCP 20/10/2026, 64,92-69,90 s de la vidéo)",
                       "texte": PHRASE, "timeline_s": [round(64.92 - V, 2), round(69.90 - V, 2)]},
            "video": vid,
            "audio": [{"id": "mix", "clip": "P3-mix.wav", "folder": "P3", "path": OUT + "P3-mix.wav", "rec": 0, "track": 1,
                       "note": "mix final -14 LUFS : voix %.2f-%.2f s sur le morceau étouffé qui monte, morceau plein au drop %.3f s, fondu de fin" % (64.92 - V, 69.90 - V, DROP)}]}
    json.dump(plan, open(D + "plan-P3.json", "w"), indent=1, ensure_ascii=False)
    json.dump({"MOFF": round(MOFF, 3), "drop_tl": round(DROP, 3), "coupes_tl": [round(sh["a"], 3) for sh in SHOTS[1:]], "frappes_tl": hits_tl(),
               "low_tl": hits_tl("low")}, open(D + "rythme/frappes_tl.json", "w"), indent=0)

# ---------------- aperçu ffmpeg 540x960 ----------------
def preview():
    out = ROOT + "/preview/apercu-P3.mp4"; args = [FF, "-v", "error", "-y"]; fl = []
    for i, sh in enumerate(SHOTS):
        args += ["-i", OUT + sh["clip"]]
        fl.append("[%d:v]trim=end_frame=%d,setpts=PTS-STARTPTS,scale=540:960,setsar=1[v%d]" % (i, sh["dur"], i))
    args += ["-i", OUT + "P3-mix.wav"]
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
