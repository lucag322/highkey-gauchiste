# Lot 4 — M1 Aura couleur multi-contextes (inspi jaxnotpl3) : Jean-Luc Mélenchon sur Ninho - Jefe.
# Phrase (Fête de l'Huma) : « Oui, nous le disons, nous sommes prêts, nous allons gagner, nous sommes prêts à gouverner. »
# Recette jaxnotpl3 : 5 contextes (Huma 9/2026, Marseille 2017, Valence 8/2026, Saint-Denis 6/2026, Clermont 10/2026), arc jeune -> actuel après le drop,
# rythme posé (coupes 1,2-2 s sur les frappes réelles), plan « cool » sur le drop (Marseille 2017 qui sourit et salue, ralenti),
# couleur naturelle (expo/contraste légers, pas de LUT), aucune caption ajoutée, coupes franches.
# Modèle de code : lot3/_claude/gen/A6/genA6.py. Aperçu HORS Resolve (ffmpeg/numpy). Ralentis = Resolve (speed_pct + optical flow).
# Usage : python genM1.py [shots] [plan] [audio] [apercu] [check] [mesure] [only=ID,ID]   (sans argument = tout)
import sys, os, json, subprocess, math, shutil
import numpy as np, cv2
ROOT = "/Users/luca.grousset/Movies/highkey-gauchiste"; LOT = ROOT + "/lot4"
sys.path.insert(0, ROOT + "/_claude/outils")
import framing
from fx import gblur, vignette, to8
from framing import plan_views
D = LOT + "/_claude/gen/M1/"; OUT = D + "out/"; os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, D)
from hits import detect_hits
framing.ROOT = D + "src"; framing.CACHE = D + "cache/faces"          # src/sources = liens vers lot1/lot3 (lecture seule)
FF = "/opt/homebrew/bin/ffmpeg"; FACES = ROOT + "/_claude/outils/faces"; FPS = 30; W, H = 1080, 1920
HUMA, MARS, VAL, SDN, CLF = ("3-melenchon-huma-citation.mp4", "Z1-marseille2017-debut.mp4", "1-melenchon-valence-amfis.mp4",
                             "5-melenchon-saintdenis-smic.mp4", "A6-melenchon-clermont-2040.mp4")
SRC_INFO = {  # fichier -> (dossier, fps, url YouTube, décalage du fichier dans la vidéo YouTube (s) ou None, contexte)
    HUMA: ("lot1/sources", 50, "https://www.youtube.com/watch?v=80bBtk2lTiI", 4710, "Fête de l'Humanité, 12/9/2026 (chaîne JLM)"),
    MARS: ("lot3/sources", 25, "https://www.youtube.com/watch?v=yrjWwsV4zS4", 0, "meeting pour la paix, Vieux-Port de Marseille, 9/4/2017 (chaîne JLM)"),
    VAL:  ("lot1/sources", 30, "https://www.youtube.com/watch?v=IYegq2-6-go", 1620, "AMFiS 2026, Valence, 23/8/2026 (chaîne JLM)"),
    SDN:  ("lot1/sources", 30, "https://www.youtube.com/watch?v=1dkY_JVFx9I", 3000, "meeting de Saint-Denis, 7/6/2026 (chaîne JLM)"),
    CLF:  ("lot3/sources", 60, "https://www.youtube.com/watch?v=sBvVfHxcJp4", 2040, "meeting de Clermont-Ferrand, 11/10/2026 (chaîne JLM)"),
}
# ---------------- musique : Ninho - Jefe (clip officiel, chaîne Ninho) ----------------
MFILE = LOT + "/sons/M1-ninho-jefe-full.wav"; MURL = "https://youtu.be/pxjsZK_fkO4"
# extrait continu : fin du couplet (« Ils sont remplis… j'les ai cramés, j'suis trop vénère », baissé sous la phrase), drop = « Jefe, jefe »
# (1er temps du refrain, caisse 64,672 s du complet), puis « on arrivera sur le trône un peu blessé / la seule chose qu'aura changé /
# c'est peut-être le prix du blouson », fin juste après « blouson » (~71,7 s).
S0_BASE = 57.420                    # kick du complet (début de l'extrait) ; décalage sous-image choisi plus bas
END = 14.3
CUT_SONG = [58.713, 61.441, 62.688, 64.672, 66.647, 68.639, 69.871]   # caisses réelles (hits.py) ; 64,672 = drop
BEAT = 0.4935                        # 121,6 BPM (caisse toutes les 2 mesures de trap demi-temps : 1,98 s)
def fr(t): return int(round(t * FPS))
def music_raw(s0, sr=48000, dur=END + 0.5):
    import soundfile as sf_
    x, r = sf_.read(MFILE, dtype="float32"); assert r == sr
    i0 = int(round(s0 * sr)); return x[i0:i0 + int(dur * sr)]
def choose_s0():
    js = OUT + "M1-frappes.json"
    if os.path.exists(js):
        d = json.load(open(js))
        if d.get("base") == S0_BASE and d.get("cuts") == CUT_SONG: return d["s0"], d["frappes"]
    hits = detect_hits(music_raw(S0_BASE - 0.02, dur=END + 0.6))
    hits = [(round(h[0] + S0_BASE - 0.02, 4), h[1], h[2]) for h in hits]
    real = []
    for c in CUT_SONG:
        h = min(hits, key=lambda h: abs(h[0] - c)); assert abs(h[0] - c) < 0.03, ("pas de frappe près de", c, h); real.append(h[0])
    best = None
    for k in range(-16, 17):
        s0 = S0_BASE + k / 1000.0
        err = max(abs((r - s0) - fr(r - s0) / FPS) for r in real)
        if best is None or err < best[0]: best = (err, s0)
    s0 = round(best[1], 4)
    tl = [(round(h[0] - s0, 4), h[1], h[2]) for h in hits if 0 <= h[0] - s0 <= END]
    json.dump({"base": S0_BASE, "cuts": CUT_SONG, "s0": s0, "err_max_s": round(best[0], 4), "frappes": tl, "coupes_complet": real}, open(js, "w"), indent=0)
    return s0, tl
S0, HITS = choose_s0()
_d = json.load(open(OUT + "M1-frappes.json"))
CUTS = [round(r - S0, 4) for r in _d["coupes_complet"]]
CUTF = [fr(c) for c in CUTS]
DROP = CUTS[3]
assert min(np.diff([0] + CUTS + [END])) >= 2 * BEAT, "plan < 2 temps"
# ---------------- phrase (Fête de l'Huma, fichier lot1/sources/3-melenchon-huma-citation.mp4) ----------------
# voix (Whisper + enveloppe) : Oui 186,43 / nous le disons 187,28-188,05 / nous sommes prêts 188,10-188,95 / nous allons gagner 189,50-190,60 /
# nous sommes prêts à gouverner 190,83-192,42 (puis ovation 192,75)
F_END = 192.42
def f2t(f): return f - F_END + DROP - 0.10                         # « gouverner » se termine 100 ms avant le drop
V_IN, V_OUT = 186.36, 192.56
# ---------------- plans ----------------
B_HUMA = (0, 0, 1920, 790)          # au-dessus du pupitre « Fête de l'Huma / Mélenchon 2027 »
B_SDN = (0, 0, 1500, 800)           # sans le filigrane MELENCHON2027.fr (haut droite) ni le pupitre « Meeting Saint-Denis »
B_CLF = (0, 0, 1570, 830)           # idem Clermont (A6)
SHOTS = {
    "prets":   dict(src=HUMA, t=None, face=(1000, 300), b=B_HUMA, vh=760, zoom=(1.0, 1.06), why="Fête de l'Huma 2026 : « Oui, nous le disons, nous sommes prêts » (synchrone)"),
    "foule":   dict(src=HUMA, t=197.0, fixed=(430, 560), b=(0, 0, 1920, 1080), vh=1080, zoom=(1.0, 1.04), why="Fête de l'Huma 2026 : la foule et les drapeaux en ovation (banderole « se syndiquer » hors fenêtre)"),
    "arene":   dict(src=CLF, t=63.0, fixed=(700, 560), b=(0, 0, 1560, 1080), vh=1080, zoom=(1.0, 1.04), why="Clermont-Ferrand 2026 : l'arène pleine, voix « nous allons gagner »"),
    "gouv":    dict(src=HUMA, t=None, face=(1000, 300), b=B_HUMA, vh=700, zoom=(1.0, 1.06), why="Fête de l'Huma : « nous sommes prêts à gouverner » (synchrone)"),
    "jefe":    dict(src=MARS, t=38.95, face=(1030, 340), b=(520, 0, 1920, 1080), vh=900, zoom=(1.0, 1.05), speed=50, why="DROP « Jefe, jefe » : Marseille 2017, sourit et salue, Vieux-Port au soleil (plan cool, ralenti)"),
    "trone":   dict(src=VAL, t=40.6, fixed=(850, 560), b=(0, 0, 1480, 1080), vh=1060, zoom=(1.0, 1.06), why="« on arrivera sur le trône » : Valence 2026, marche de dos vers la scène"),
    "bras":    dict(src=SDN, t=176.05, face=(780, 300), b=B_SDN, vh=780, zoom=(1.0, 1.04), why="Saint-Denis 2026 : gros plan, il harangue la foule (bras levés hors cadre : pupitre et filigrane exclus)"),
    "fin":     dict(src=CLF, t=50.45, face=(960, 250), b=B_CLF, vh=830, zoom=(1.0, 1.05), why="Clermont-Ferrand oct. 2026 : bras grands ouverts (aujourd'hui)"),
}
SHOTS["prets"]["t"] = CUTS[0] - f2t(0)                               # synchrone : t_source = t_timeline - f2t(0)
SHOTS["gouv"]["t"] = CUTS[2] - f2t(0)
EDIT = ["foule", "prets", "arene", "gouv", "jefe", "trone", "bras", "fin"]
assert len(EDIT) == len(CUTS) + 1
def slots():
    b = [0] + CUTF + [fr(END)]
    return [(sid, b[i], b[i + 1]) for i, sid in enumerate(EDIT)]
# ---------------- look : couleur naturelle, expo/contraste légers (recette jaxnotpl3 : pas de filtre lourd) ----------------
RNG = np.random.default_rng(4)
def grade(bgr):
    x = np.clip(bgr, 0, 1)
    l = 0.114 * x[..., 0] + 0.587 * x[..., 1] + 0.299 * x[..., 2]
    s = l * l * (3 - 2 * l)
    x = x + (s - l)[..., None] * 0.22                                 # contraste doux (courbe en S sur la luminance)
    l2 = (0.114 * x[..., 0] + 0.587 * x[..., 1] + 0.299 * x[..., 2])[..., None]
    x = l2 + (x - l2) * 1.06                                          # saturation +6 %
    small = cv2.resize(x, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    hi = np.clip(small - 0.72, 0, None)
    x = x + cv2.resize(cv2.GaussianBlur(hi, (0, 0), 10), (W, H)) * 0.35   # léger bloom des hautes lumières (aura discrète)
    x = vignette(x, 0.22, 2.4)
    x = x + RNG.normal(0, 0.010, x.shape[:2]).astype(np.float32)[..., None]
    return np.clip(x, 0, 1)
def read_frames(src, t, n_out):
    folder, sfps = SRC_INFO[src][0], SRC_INFO[src][1]
    need = [int(round(i * sfps / FPS)) for i in range(n_out)]; n_src = need[-1] + 1
    p = subprocess.run([FF, "-v", "error", "-ss", "%.4f" % t, "-i", ROOT + "/" + folder + "/" + src, "-frames:v", str(n_src),
                        "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True)
    a = np.frombuffer(p.stdout, np.uint8).reshape(-1, 1080, 1920, 3)
    return [a[min(i, len(a) - 1)].astype(np.float32) / 255 for i in need], int(round(t * sfps)), sfps
def crop_916(img, cx, cy, vh):
    vw = vh * 9 / 16; s = W / vw
    M = np.float32([[s, 0, W / 2 - cx * s], [0, s, H / 2 - cy * s]])
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
def write_mov(frames, path, fps=FPS):
    p = subprocess.Popen([FF, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", "%dx%d" % (W, H), "-r", str(fps), "-i", "-",
                          "-c:v", "prores_ks", "-profile:v", "3", "-pix_fmt", "yuv422p10le", "-vendor", "apl0", path], stdin=subprocess.PIPE)
    for f in frames: p.stdin.write(to8(f).tobytes())
    p.stdin.close(); p.wait()
def render_slot(sid, a, b):
    sh = SHOTS[sid]; n = b - a
    raw, s0, sfps = read_frames(sh["src"], sh["t"], n)
    m = math.ceil(n * sh.get("speed", 100) / 100)                    # zoom fini sur la frappe de sortie (ralenti : images vues)
    z0, z1 = sh["zoom"]; zoom = lambda f: z0 + (z1 - z0) * min(f / max(m - 1, 1), 1.0)
    if "fixed" in sh:
        views, _ = plan_views(sh["src"], s0, n, sfps, speed=sfps / FPS, bounds=sh["b"], vh=sh["vh"], zoom=zoom, fixed=sh["fixed"])
    else:
        views, ok = plan_views(sh["src"], s0, n, sfps, speed=sfps / FPS, hint=sh["face"], bounds=sh["b"], vh=sh["vh"], zoom=zoom, top=0.12)
        if not ok: print("  ! pas de visage :", sid)
    frames = [grade(crop_916(img, cx, cy, vh)) for img, (cx, cy, vh) in zip(raw, views)]
    write_mov(frames, OUT + "M1_%s.mov" % sid)
    vx, vz = views[0], views[-1]
    print("  %-6s %3d im  vue %d,%d h%d -> h%d  (x %d-%d, y %d-%d)" % (sid, n, vx[0], vx[1], vx[2], vz[2], vx[0] - vx[2] * 9 / 32, vx[0] + vx[2] * 9 / 32, vx[1] - vx[2] / 2, vx[1] + vx[2] / 2))
# ---------------- plan ----------------
def build_plan():
    video = []
    for sid, a, b in slots():
        sh = SHOTS[sid]; n = b - a; folder, sfps, url, off, ctx = SRC_INFO[sh["src"]]
        yt = "%s @ %.2f s" % (url, off + sh["t"]) if off is not None else url
        v = {"id": "%s_%d" % (sid, a), "clip": "M1_%s.mov" % sid, "folder": "genM1", "s": 0, "e": n, "rec": a, "track": 1, "kind": "shot",
             "clip_fps": FPS, "dur": n, "speed_pct": sh.get("speed", 100),
             "source": "%s/%s @ %.3f s (%s)" % (folder, sh["src"], sh["t"], yt), "contexte": ctx, "effet": "coupe franche",
             "temps": round(n / FPS / BEAT, 1), "pourquoi": sh["why"]}
        if sh.get("speed"): v["retime"] = "optical_flow"; v["note_ralenti"] = "clip rendu à vitesse normale ; Resolve : SetSpeed %d %% + Optical Flow (aperçu = setpts)" % sh["speed"]
        video.append(v)
    plan = {"name": "M1 - Aura couleur multi-contextes - Jean-Luc Mélenchon (Ninho - Jefe)", "fps": FPS, "w": W, "h": H, "duree_s": END,
            "note": "Plans 9:16 recadrés + étalonnés couleur naturelle (lot4/_claude/gen/M1/out). s/e en images du clip (30 i/s), rec en images timeline. "
                    "speed_pct < 100 : ralenti Resolve Optical Flow + Speed Warp (aperçu = setpts simple). Coupes sur les caisses réelles de la musique posée "
                    "(out/M1-frappes.json), drop = « Jefe, jefe » (1er temps du refrain) ; aucun plan < 2 temps ; poussées lentes avant seulement ; aucune caption (recette jaxnotpl3).",
            "phrase": {"texte": "Oui, nous le disons, nous sommes prêts, nous allons gagner, nous sommes prêts à gouverner.",
                       "source": "https://www.youtube.com/watch?v=80bBtk2lTiI (chaîne JEAN-LUC MÉLENCHON, Fête de l'Humanité 12/9/2026), 4896,43-4902,42 s — fichier lot1/sources/3-melenchon-huma-citation.mp4 186,43-192,42 s",
                       "timeline_s": [round(f2t(186.43), 3), round(f2t(192.42), 3)]},
            "video": video,
            "audio": [{"id": "mix", "clip": "M1-mix.wav", "folder": "genM1", "rec": 0, "track": 1, "note": "mix -14 LUFS, TP <= -1 dBTP"}],
            "stems": ["lot4/_claude/gen/M1/out/M1-voix.wav", "lot4/_claude/gen/M1/out/M1-musique.wav"],
            "musique": {"fichier": "lot4/sons/M1-ninho-jefe-full.wav", "titre": "Ninho - Jefe", "url": MURL,
                        "debut_complet_s": S0, "fin_complet_s": round(S0 + END, 3), "coupes_timeline_s": CUTS, "drop_timeline_s": DROP},
            "logos_exclus": "pupitres (Huma, Saint-Denis, Clermont) hors cadre, filigranes MELENCHON2027.fr (haut droite) hors fenêtre, pancarte rouge de Marseille hors fenêtre"}
    json.dump(plan, open(D + "plan-M1.json", "w"), indent=1, ensure_ascii=False)
    son = {"id": "M1", "titre": "Jefe", "artiste": "Ninho", "url": MURL, "version": "clip officiel, chaîne YouTube Ninho (178 s)",
           "fichier": "lot4/sons/M1-ninho-jefe-full.wav",
           "extrait_utilise": {"debut_complet_s": S0, "fin_complet_s": round(S0 + END, 3), "duree_s": END,
                               "contenu": "fin du couplet (« Ils sont remplis d'… j'les ai cramés / J'suis trop vénère », baissé -9 dB sous la phrase) puis refrain « Jefe, jefe / On arrivera sur le trône un peu blessé / La seule chose qu'aura changé / C'est peut-être le prix du blouson »"},
           "bpm": round(60 / BEAT, 1), "drop": {"complet_s": _d["coupes_complet"][3], "timeline_s": DROP, "note": "« Jefe, jefe », 1er temps du refrain (caisse)"},
           "coupes_timeline_s": CUTS, "frappes_timeline_s": HITS,
           "methode": "hits.py (copie de lot3/_claude/gen/A6/hits.py) sur la musique posée ; mesure sur l'export dans mesure()"}
    json.dump(son, open(D + "son.json", "w"), indent=1, ensure_ascii=False)
    return plan
# ---------------- audio ----------------
def loud(path):
    r = subprocess.run([FF, "-hide_banner", "-i", path, "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True).stderr
    return float([l for l in r.splitlines() if l.strip().startswith("I:")][-1].split()[1])
def make_audio():
    import soundfile as sf
    sr = 48000; N = int(round(END * sr))
    p = subprocess.run([FF, "-v", "error", "-ss", "%.3f" % V_IN, "-t", "%.3f" % (V_OUT - V_IN), "-i", ROOT + "/lot1/sources/" + HUMA,
                        "-ac", "2", "-ar", str(sr), "-f", "f32le", "-"], capture_output=True)
    v = np.frombuffer(p.stdout, np.float32).reshape(-1, 2).copy()
    fi, fo = int(0.03 * sr), int(0.12 * sr); v[:fi] *= np.linspace(0, 1, fi)[:, None]; v[-fo:] *= np.linspace(1, 0, fo)[:, None]
    m = music_raw(S0, sr, END + 0.1)[:N].copy()
    sf.write(D + "tmp_v.wav", v, sr, subtype="FLOAT"); sf.write(D + "tmp_m.wav", m, sr, subtype="FLOAT")
    lv, lm = loud(D + "tmp_v.wav"), loud(D + "tmp_m.wav"); os.remove(D + "tmp_v.wav"); os.remove(D + "tmp_m.wav")
    gv = 10 ** ((lm - lv) / 20)                                       # voix au niveau de la musique pleine, musique -9 dB dessous
    voix = np.zeros((N, 2), np.float32); a = int(round(f2t(V_IN) * sr)); voix[a:a + len(v)] = v[:N - a] * gv
    tv0, tv1 = f2t(V_IN), f2t(V_OUT)
    t = np.arange(N) / sr; g = np.ones(N, np.float32); lo = 10 ** (-9 / 20)
    def ramp(t0, t1, g0, g1):
        s = (t >= t0) & (t < t1); g[s] = g0 + (g1 - g0) * (t[s] - t0) / (t1 - t0)
    g[(t >= tv0) & (t < DROP - 0.02)] = lo; ramp(tv0 - 0.30, tv0, 1.0, lo)
    ramp(f2t(F_END) + 0.01, DROP - 0.005, lo, 0.75)                  # remontée entre « gouverner » et le drop
    s = t > END - 0.22; g[s] *= np.clip((END - t[s]) / 0.22, 0, 1)
    f0 = int(0.008 * sr); g[:f0] *= np.linspace(0, 1, f0)
    mus = m * g[:, None]
    sf.write(OUT + "M1-voix.wav", voix, sr, subtype="PCM_24"); sf.write(OUT + "M1-musique.wav", mus, sr, subtype="PCM_24")
    sf.write(D + "tmp_mix.wav", voix + mus, sr, subtype="FLOAT")
    r_ = subprocess.run([FF, "-hide_banner", "-i", D + "tmp_mix.wav", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                        capture_output=True, text=True).stderr
    js = json.loads(r_[r_.rindex("{"):r_.rindex("}") + 1])
    af = ("loudnorm=I=-13.6:TP=-2:LRA=11:measured_I=%s:measured_TP=%s:measured_LRA=%s:measured_thresh=%s:offset=%s:linear=true,"
          "alimiter=limit=0.83:level=false:attack=1:release=60,aresample=48000"
          % (js["input_i"], js["input_tp"], js["input_lra"], js["input_thresh"], js["target_offset"]))
    subprocess.run([FF, "-v", "error", "-y", "-i", D + "tmp_mix.wav", "-af", af, "-c:a", "pcm_s24le", OUT + "M1-mix.wav"], check=True)
    os.remove(D + "tmp_mix.wav"); print("audio : voix %.1f / musique %.1f LUFS, gain voix %+.1f dB ; mix avant normalisation %s LUFS" % (lv, lm, 20 * math.log10(gv), js["input_i"]))
# ---------------- aperçu 540x960 ----------------
APERCU = ROOT + "/preview/apercu-M1.mp4"
def apercu():
    plan = json.load(open(D + "plan-M1.json")); ins = []; fl = []
    for i, v in enumerate(plan["video"]):
        n = v["e"] - v["s"]; sp = v.get("speed_pct", 100) / 100
        ins += ["-i", OUT + v["clip"]]
        if sp < 1:
            fl.append("[%d:v]trim=start_frame=%d:end_frame=%d,setpts=(PTS-STARTPTS)/%.4f,fps=30,trim=end_frame=%d,setpts=PTS-STARTPTS,scale=540:960,setsar=1[v%d]"
                      % (i, v["s"], v["s"] + math.ceil(n * sp) + 1, sp, n, i))
        else:
            fl.append("[%d:v]trim=start_frame=%d:end_frame=%d,setpts=PTS-STARTPTS,scale=540:960,setsar=1[v%d]" % (i, v["s"], v["e"], i))
    k = len(plan["video"])
    fl.append("".join("[v%d]" % i for i in range(k)) + "concat=n=%d:v=1:a=0[v]" % k)
    ins += ["-i", OUT + "M1-mix.wav"]
    subprocess.run([FF, "-v", "error", "-y"] + ins + ["-filter_complex", ";".join(fl), "-map", "[v]", "-map", "%d:a" % k,
                    "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "aac", "-b:a", "192k", "-shortest", APERCU], check=True)
    print("aperçu", APERCU)
# ---------------- contrôle visages : tout visage > 5 % de la hauteur doit être entier, dans chaque plan ----------------
def check_faces():
    plan = json.load(open(D + "plan-M1.json")); bad = []
    for v in plan["video"]:
        n = v["e"] - v["s"]
        if v.get("speed_pct", 100) < 100: n = math.ceil(n * v["speed_pct"] / 100) + 1
        d = D + "cache/chk_" + v["clip"]; shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
        subprocess.run([FF, "-v", "error", "-i", OUT + v["clip"], "-vf", "select='lt(n\\,%d)',scale=540:960" % n, "-fps_mode", "passthrough",
                        "-q:v", "3", d + "/f%04d.jpg"], check=True)
        subprocess.run([FACES, d], check=True, capture_output=True)
        js = json.load(open(d + "/faces.json")); nb = 0
        for k, fl in js.items():
            for x, y, w, h in fl:
                if h < 0.05: continue
                top, bot, l, r = y - 0.3 * h, y + h * 1.05, x - 0.08 * w, x + w * 1.08
                if top < 0 or bot > 1 or l < 0 or r > 1: nb += 1; bad.append("%s %s (%.2f %.2f %.2f %.2f h%.2f)" % (v["clip"], k, top, bot, l, r, h))
        print("  visages", v["clip"], "images", len(js), "coupés", nb)
        shutil.rmtree(d, ignore_errors=True)
    print("TOTAL visages coupés :", len(bad)); print("\n".join(bad[:30]))
# ---------------- mesure sur l'export : coupes (changement d'image) vs frappes (audio de l'export) ----------------
def mesure():
    p = subprocess.run([FF, "-v", "error", "-i", APERCU, "-vf", "scale=54:96", "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True)
    fr_ = np.frombuffer(p.stdout, np.uint8).reshape(-1, 96, 54).astype(np.float32)
    diff = np.abs(np.diff(fr_, axis=0)).mean((1, 2))
    cuts_exp = [(i + 1) / FPS for i in range(len(diff)) if diff[i] > 12 and diff[i] > 2.5 * np.median(diff[max(0, i - 5):i + 6])]
    p = subprocess.run([FF, "-v", "error", "-i", APERCU, "-ac", "2", "-ar", "48000", "-f", "f32le", "-"], capture_output=True)
    y = np.frombuffer(p.stdout, np.float32).reshape(-1, 2)
    # attaque de la caisse sur l'export : enveloppe passe-haut 1,5 kHz (crête 2 ms), 1er point à 50 % du max local (±50 ms autour de la coupe)
    import scipy.signal as ss
    mono = y.mean(1); sr = 48000
    hp = np.abs(ss.sosfiltfilt(ss.butter(4, 1500, "hp", fs=sr, output="sos"), mono))
    env = np.array([hp[i:i + 96].max() for i in range(0, len(hp) - 96, 24)]); et = np.arange(len(env)) * 24 / sr
    def onset(c):
        s = (et >= c - 0.05) & (et <= c + 0.05); idx = np.where(s)[0]; seg = env[idx]
        k = int(np.argmax(seg)); thr = 0.5 * seg[k]; j = k
        while j > 0 and seg[j - 1] > thr: j -= 1
        return et[idx[j]] + 0.001
    print("images", len(fr_), "durée %.3f s" % (len(fr_) / FPS), "| coupes détectées :", ["%.3f" % c for c in cuts_exp])
    errs = []
    for c in CUTS:
        ce = min(cuts_exp, key=lambda x: abs(x - c)) if cuts_exp else float("nan")
        h = onset(c)
        e = (ce - h) * 1000; errs.append(abs(e))
        print("  coupe prévue %.3f | image de coupe export %.3f | attaque caisse export %.4f | écart %+.1f ms" % (c, ce, h, e))
    print("ÉCART MAX coupes/frappes : %.1f ms" % max(errs))
    r = subprocess.run([FF, "-hide_banner", "-i", APERCU, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    print("\n".join(l for l in r.splitlines()[-12:] if "I:" in l or "Peak:" in l or "LRA:" in l))
if __name__ == "__main__":
    args = set(a for a in sys.argv[1:] if not a.startswith("only=")) or {"shots", "plan", "audio", "apercu", "check", "mesure"}
    only = [x for a in sys.argv[1:] if a.startswith("only=") for x in a.split("=", 1)[1].split(",")]
    print("S0 = %.4f s du complet, coupes timeline :" % S0, CUTS, "drop", DROP)
    print("phrase timeline %.3f-%.3f, source prets %.3f gouv %.3f" % (f2t(186.43), f2t(F_END), SHOTS["prets"]["t"], SHOTS["gouv"]["t"]))
    if "shots" in args or only:
        for sid, a, b in slots():
            if not only or sid in only: render_slot(sid, a, b)
    if "plan" in args: build_plan()
    if "audio" in args: make_audio()
    if "apercu" in args: apercu()
    if "check" in args: check_faces()
    if "mesure" in args: mesure()
