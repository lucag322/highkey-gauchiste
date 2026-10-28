# M2 (lot 4) — Aura couleur multi-contextes (inspi jaxnotpl3, Macron), Manon Aubry, son PNL – Au DD (clip officiel).
# Recette jaxnotpl3 : 4-6 contextes de la figure (jeune -> actuel), coupes posées toutes les 2 s sur les vraies frappes, plan « cool »
# sur le drop (ici : Aubry de dos qui avance dans le couloir vitré du Parlement en 2019, à la place des lunettes noires de Macron),
# couleur naturelle (correction légère, pas de LUT, pas de N&B), archives brutes sans texte ajouté.
# Phrase (son direct) : « Nous privilégierons les milliards d'êtres humains aux milliards de quelques humains. »
#   (plénière de Strasbourg, débat sur l'état de l'Union, 16/09/2026, chaîne Manon Aubry, youtu.be/nwc4Hd8pO8o 87,18-92,58 s)
#   -> autre phrase que G2 (même discours, 20,1-28,0 s) et V1 (meeting Strasbourg).
# Son : Au DD, extrait continu ; la phrase finit dans le break (« …mes pétales »), « Au DD » crié puis drop = 1er kick plein du refrain.
# Règles : 9:16 plein écran, aucun visage coupé, aucun logo, plans >= 1 temps, pas de dézoom, <= 15 s, ralentis = speed_pct (Resolve).
# Usage : python genM2.py [shots] [audio] [plan] [apercu] [mesure] [only=ID,ID]   (sans argument = tout)
import sys, os, json, subprocess, math
import numpy as np, cv2
HG = "/Users/luca.grousset/Movies/highkey-gauchiste"
sys.path.insert(0, HG + "/_claude/outils")
import framing
from fx import gblur, vignette, grain, to8
D = HG + "/lot4/_claude/gen/M2/"; OUT = D + "out/"; CACHE = D + "cache/faces"; os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, D)
from hits import detect_hits
FF = "/opt/homebrew/bin/ffmpeg"; FACES = HG + "/_claude/outils/faces"; FPS = 30; W, H = 1080, 1920
def fr(t): return int(round(t * FPS))

# ---------------- sources (chemins relatifs au projet) ----------------
SRC = {
    "SOT": ("lot2/sources/G2-aubry-sotEU-2026.mp4", 25.0, "https://www.youtube.com/watch?v=nwc4Hd8pO8o", 0.0,
            "plénière de Strasbourg, débat sur l'état de l'Union, 16/09/2026 (chaîne Manon Aubry)"),
    "PLE": ("lot2/sources/G2-aubry-plenaire-2025-10.mp4", 25.0, "https://www.youtube.com/watch?v=5hHVL1aaiHw", 0.0,
            "plénière du Parlement européen, 07/10/2025 (chaîne Manon Aubry)"),
    "COUL": ("lot4/sources/M2-aubry-vlog2019-couloir.mp4", 30000 / 1001, "https://www.youtube.com/watch?v=xmJ28JascwQ", 36.0,
             "vlog « Aubry qui court » ép. 2, Parlement de Strasbourg, juillet 2019 (chaîne Manon Aubry)"),
    "HEMI": ("lot4/sources/M2-aubry-vlog2019-hemicycle-b.mp4", 30000 / 1001, "https://www.youtube.com/watch?v=xmJ28JascwQ", 440.0,
             "vlog « Aubry qui court » ép. 2, hémicycle vide, juillet 2019 (chaîne Manon Aubry)"),
    "SOIR": ("lot4/sources/M2-aubry-soiree2024-b.mp4", 30.0, "https://www.youtube.com/watch?v=KnUCA72LZAY", 1498.0,
             "soirée électorale des européennes, 09/06/2024 (chaîne La France insoumise)"),
    "MEET": ("lot3/sources/V1-aubry-strasbourg-a.mp4", 25.0, "https://www.youtube.com/watch?v=c-KnJoiz928", 0.0,
             "meeting « Justice pour la Palestine », Strasbourg, 17/06/2026 (chaîne Manon Aubry)"),
}
B_FULL = (0, 0, 1920, 1080)
B_SOT = (200, 0, 1720, 752)          # pupitre + logo de l'hémicycle exclus (G2)
B_PLE = (200, 0, 1720, 788)          # idem plénière 2025
B_WIDE = (600, 0, 1920, 1080)        # plan large : von der Leyen (x ≈ 450) exclue
B_SOIR = (0, 0, 1760, 900)           # logo LFI haut droite, bandeau bas gauche et texte de la pancarte du pupitre (y > 900) exclus
B_MEET = (0, 0, 1620, 1080)          # logo « ELA » haut droite exclu (V1)

# têtes bouclées : boîte plus large que celle de Vision (cheveux)
framing.head_box = lambda f: (f[0] - 0.30 * f[2], f[1] - 0.60 * f[3], f[0] + 1.30 * f[2], f[1] + 1.25 * f[3])
def detect(src, s, n, fps):
    """framing.detect avec cache dans gen/M2 (les sources des lots 1-3 ne sont que lues)."""
    path, sfps = SRC[src][0], SRC[src][1]
    d = "%s/%s_%d_%d" % (CACHE, os.path.splitext(os.path.basename(path))[0], s, n)
    if not os.path.exists(d + "/faces.json"):
        os.makedirs(d, exist_ok=True)
        subprocess.run([FF, "-v", "error", "-y", "-ss", "%.4f" % (s / sfps), "-i", HG + "/" + path, "-frames:v", str(n), "-vf", "scale=960:-2",
                        "-fps_mode", "passthrough", "-start_number", "0", "-q:v", "3", d + "/f%04d.jpg"], check=True)
        subprocess.run([FACES, d], check=True, capture_output=True)
    js = json.load(open(d + "/faces.json"))
    return [[(b[0] * 1920, b[1] * 1080, b[2] * 1920, b[3] * 1080) for b in js.get("f%04d.jpg" % i, [])] for i in range(n)]
framing.detect = detect

# ---------------- musique : PNL – Au DD ----------------
SON_FILE = HG + "/lot4/sons/M2-pnl-au-dd_complet.wav"; SON_URL = "https://youtu.be/BtyHYIpykN0"
MDROP = 123.895                      # 1er kick plein du refrain, sur « DD » (« Au DD » crié 123,70-124,02), juste après le break 122,4-123,7
DROP = 6.0; END = 14.95              # aura : 15 s max
BAR = 2.0                            # 120 BPM : temps 0,5 s, kick plein toutes les 2 s (x,90 s du morceau)
MUSIC_IN0 = MDROP - DROP
# coupes (en s timeline, avant calage sur les frappes) : plan large sur le kick 121,90 (dernier avant le break), drop, puis toutes les 2 s
CUT_T = [DROP - BAR, DROP, DROP + BAR, DROP + 2 * BAR, DROP + 3 * BAR, DROP + 4 * BAR]
HITS_JSON = OUT + "M2-frappes.json"
def music_raw(mi, dur=END + 0.5, sr=48000):
    import soundfile as sf
    i0 = int(round(mi * sr)); x, r = sf.read(SON_FILE, start=i0, frames=int(dur * sr), dtype="float32"); assert r == sr; return x
def frappes():
    """Décalage sous-image de l'extrait pour que les kicks des coupes tombent au plus près des images ; frappes re-mesurées sur l'extrait posé."""
    if os.path.exists(HITS_JSON):
        js = json.load(open(HITS_JSON))
        if js["cle"] == [MUSIC_IN0, END, CUT_T]: return js["music_in"], js["frappes"]
    h0 = detect_hits(music_raw(MUSIC_IN0))
    k0 = [h[0] for h in h0 if h[1] == "kick" and h[3] > 0.4]
    cut0 = [min(k0, key=lambda k: abs(k - t)) for t in CUT_T]
    mean = float(np.mean([c * FPS - round(c * FPS) for c in cut0])) / FPS     # erreur moyenne kick -> image
    best, bad = None, 9
    for off in np.arange(mean - 0.004, mean + 0.0045, 0.001):                 # re-mesure sur l'extrait décalé (l'attaque dépend du début)
        h = detect_hits(music_raw(MUSIC_IN0 + off)); ks = [x[0] for x in h if x[1] == "kick" and x[3] > 0.4]
        e = max(abs(c - round(c * FPS) / FPS) for c in [min(ks, key=lambda k: abs(k - t)) for t in CUT_T])
        if e < bad: best, bad, hb = off, e, h
    mi = MUSIC_IN0 + best; h = hb
    json.dump({"cle": [MUSIC_IN0, END, CUT_T], "music_in": mi, "frappes": h}, open(HITS_JSON, "w")); return mi, h
MUSIC_IN, HITS = frappes()
KICKS = [h[0] for h in HITS if h[1] == "kick" and h[3] > 0.4]
def snap(t):
    c = min(KICKS, key=lambda x: abs(x - t)); assert abs(c - t) < 0.03, ("pas de kick plein près de", t, c); return c
CUTS = [snap(t) for t in CUT_T]; CUTF = [fr(c) for c in CUTS]
# ---------------- voix ----------------
V_TL0 = 0.10                          # « Nous » (87,18 s) à 0,10 s timeline
V_SRC0 = 87.18 - V_TL0                # source SOT à t = 0
V_IN, V_OUT = 87.12, 92.66            # « Nous » 87,18 … « humains. » fin 92,58 (Whisper) + queue ; « Madame von der Leyen » (92,94) non gardé
def t_of_src(s): return s - V_SRC0
# ---------------- plans (id, source, entrée source en s, bornes, cadrage, poussée, vitesse, pourquoi) ----------------
SHOTS = [
    dict(id="phrase", src="SOT", t=V_SRC0, b=B_SOT, face=(1000, 270), vh=752, zoom=(1.0, 1.06),
         why="2026 — plénière, état de l'Union : « Nous privilégierons les milliards d'êtres humains aux milliards… » en son direct"),
    dict(id="large", src="SOT", t=92.80, b=B_WIDE, fixed=(945, 430), vh=860, zoom=(1.0, 1.05),
         why="2026 — même plénière, plan large de l'hémicycle : Aubry au pupitre face aux eurodéputés (la phrase finit en off : « …de quelques humains »)"),
    dict(id="couloir", src="COUL", t=6.42, b=B_FULL, fixed=(930, 560), vh=1080, zoom=(1.0, 1.05), speed=80,
         why="2019 — 1er mandat : de dos, elle avance dans le couloir vitré du Parlement (plan « cool » du drop, à la place des lunettes)"),
    dict(id="hemicycle", src="HEMI", t=9.0, b=B_FULL, face=(1030, 500), vh=1080, zoom=(1.0, 1.05), top=0.14,
         why="2019 — jeune eurodéputée dans l'hémicycle vide de Strasbourg"),
    dict(id="soiree", src="SOIR", t=0.80, b=B_SOIR, fixed=(1065, 450), vh=900, zoom=(1.0, 1.03),
         why="2024 — soirée électorale des européennes (tête de liste), bras levé, lumière violette (cadre fixe : Aubry et Rima Hassan derrière elle entières)"),
    dict(id="pleniere", src="PLE", t=153.40, b=B_PLE, face=(1000, 300), vh=788, zoom=(1.0, 1.05), top=0.12,
         why="2025 — plénière, veste blanche, elle relève la tête vers l'hémicycle"),
    dict(id="meeting", src="MEET", t=24.60, b=B_MEET, face=(960, 300), vh=1080, zoom=(1.0, 1.03), top=0.12, fade=12,
         why="2026 — meeting Palestine à Strasbourg, gros plan, regard vers la salle (fin, fondu au noir)"),
]
BOUNDS_T = [0] + CUTF + [fr(END)]
for i, sh in enumerate(SHOTS):
    sh["a"], sh["bb"] = BOUNDS_T[i], BOUNDS_T[i + 1]; sh["n"] = sh["bb"] - sh["a"]; sh["clip"] = "M2_%s.mov" % sh["id"]
assert min(sh["n"] for sh in SHOTS) >= 15, [(s["id"], s["n"]) for s in SHOTS]
# la phrase en gros plan doit finir avant le plan large de la source (coupe à 92,70 s)
assert SHOTS[0]["t"] + SHOTS[0]["n"] / FPS <= 92.70, SHOTS[0]["t"] + SHOTS[0]["n"] / FPS

# ---------------- étalonnage : couleur naturelle, correction légère (recette : pas de LUT, pas de filtre lourd) ----------------
VIG = None
def grade(img, expo=1.0):
    global VIG
    x = np.clip(img * expo, 0, 1)
    x = 0.85 * x + 0.15 * (x * x * (3 - 2 * x))                     # S très douce
    L = x @ np.array([0.0722, 0.7152, 0.2126], np.float32)
    x = L[..., None] + (x - L[..., None]) * 1.06                      # +6 % de saturation
    hl = np.clip(x - 0.72, 0, 1)
    x = x + gblur(hl, 14) * 0.18                                      # léger halo des hautes lumières (aura discrète)
    if VIG is None: VIG = vignette(np.ones((H, W, 3), np.float32), strength=0.22, power=2.4)
    return grain(x * VIG, 0.008, 1.3)
# ---------------- lecture source + recadrage ----------------
def read_frames(src, t, n_out):
    path, sfps = SRC[src][0], SRC[src][1]
    need = [int(round(i * sfps / FPS)) for i in range(n_out)]
    p = subprocess.run([FF, "-v", "error", "-ss", "%.4f" % t, "-i", HG + "/" + path, "-frames:v", str(need[-1] + 1),
                        "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True)
    a = np.frombuffer(p.stdout, np.uint8).reshape(-1, 1080, 1920, 3)
    return [a[min(i, len(a) - 1)].astype(np.float32) / 255 for i in need]
def crop_916(img, cx, cy, vh):
    s = H / vh
    M = np.float32([[s, 0, W / 2 - cx * s], [0, s, H / 2 - cy * s]])
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
def write_mov(frames, path):
    p = subprocess.Popen([FF, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", "%dx%d" % (W, H), "-r", str(FPS), "-i", "-",
                          "-c:v", "prores_ks", "-profile:v", "3", "-pix_fmt", "yuv422p10le", "-vendor", "apl0", path], stdin=subprocess.PIPE)
    for f in frames: p.stdin.write(to8(f).tobytes())
    p.stdin.close(); p.wait()
def render(sh):
    n = sh["n"]; sfps = SRC[sh["src"]][1]
    raw = read_frames(sh["src"], sh["t"], n)                         # vitesse normale (ralenti = Resolve)
    m = math.ceil(n * sh.get("speed", 100) / 100)                     # poussée finie sur la coupe de sortie, ralenti compris
    z0, z1 = sh["zoom"]; zoom = lambda f: z0 + (z1 - z0) * min(f / max(m - 1, 1), 1.0)
    s0 = int(round(sh["t"] * sfps))
    if "fixed" in sh:
        views, ok = framing.plan_views(sh["src"], s0, n, sfps, speed=sfps / FPS, bounds=sh["b"], vh=sh["vh"], zoom=zoom, fixed=sh["fixed"])
    else:
        views, ok = framing.plan_views(sh["src"], s0, n, sfps, speed=sfps / FPS, hint=sh["face"], bounds=sh["b"], vh=sh["vh"], zoom=zoom,
                                       top=sh.get("top", 0.15))
        if not ok: print("  ! pas de visage :", sh["id"])
    frames = []
    for i, (img, (cx, cy, vh)) in enumerate(zip(raw, views)):
        g = grade(crop_916(img, cx, cy, vh), sh.get("expo", 1.0))
        if sh.get("fade") and i >= n - sh["fade"]: g = g * ((n - i - 1) / sh["fade"])
        frames.append(g)
    write_mov(frames, OUT + sh["clip"])
    v0, v1 = views[0], views[-1]
    print("  %-10s %3d im  vue %d,%d h%d -> h%d" % (sh["id"], n, v0[0], v0[1], v0[2], v1[2]))
# ---------------- audio ----------------
def make_audio():
    import soundfile as sf
    sr = 48000; N = int(round(END * sr))
    def grab(path, t, dur):
        p = subprocess.run([FF, "-v", "error", "-ss", "%.3f" % t, "-t", "%.3f" % dur, "-i", path, "-ac", "2", "-ar", str(sr), "-f", "f32le", "-"], capture_output=True)
        return np.frombuffer(p.stdout, np.float32).reshape(-1, 2).copy()
    voix = np.zeros((N, 2), np.float32); mus = np.zeros((N, 2), np.float32)
    v = grab(HG + "/" + SRC["SOT"][0], V_IN, V_OUT - V_IN); env = np.ones(len(v), np.float32)
    k = int(0.03 * sr); env[:k] = np.linspace(0, 1, k); k = int(0.08 * sr); env[-k:] = np.linspace(1, 0, k)
    a = int(round(t_of_src(V_IN) * sr)); voix[a:a + len(v)] = v * env[:, None] * 10 ** (4 / 20)
    m = music_raw(MUSIC_IN)[:N]
    # musique qui monte sous la phrase (-15 -> -9 dB), pleine pour « Au DD » et le drop
    t = np.arange(len(m)) / sr
    gdb = np.interp(t, [0, 0.4, t_of_src(V_OUT), t_of_src(V_OUT) + 0.12, END], [-24, -15, -9, 0, 0])
    k = int(0.5 * sr); fo = np.ones(len(m), np.float32); fo[-k:] = np.linspace(1, 0, k)
    mus[:len(m)] = m * (10 ** (gdb / 20) * fo)[:, None] * 10 ** (4 / 20)
    sf.write(OUT + "M2-voix.wav", voix, sr, subtype="PCM_24"); sf.write(OUT + "M2-musique.wav", mus, sr, subtype="PCM_24")
    sf.write(D + "tmp_mix.wav", voix + mus, sr, subtype="FLOAT")
    r = subprocess.run([FF, "-hide_banner", "-i", D + "tmp_mix.wav", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    js = json.loads(r[r.rindex("{"):r.rindex("}") + 1])
    af = ("loudnorm=I=-14:TP=-1.5:LRA=11:measured_I=%s:measured_TP=%s:measured_LRA=%s:measured_thresh=%s:offset=%s:linear=true,"
          "alimiter=limit=0.85:level=false:attack=1:release=60,aresample=48000" % (js["input_i"], js["input_tp"], js["input_lra"], js["input_thresh"], js["target_offset"]))
    subprocess.run([FF, "-v", "error", "-y", "-i", D + "tmp_mix.wav", "-af", af, "-c:a", "pcm_s24le", OUT + "M2-mix.wav"], check=True)
    os.remove(D + "tmp_mix.wav"); print("audio : mix avant normalisation", js["input_i"], "LUFS")
# ---------------- plan ----------------
def build_plan():
    video = []
    for sh in SHOTS:
        path, sfps, url, off, ctx = SRC[sh["src"]]
        n_src = int(round(sh["n"] / FPS * sfps))
        v = {"id": sh["id"], "clip": sh["clip"], "folder": "genM2", "path": OUT + sh["clip"], "s": 0, "e": sh["n"], "rec": sh["a"], "dur": sh["n"],
             "clip_fps": FPS, "speed_pct": sh.get("speed", 100), "track": 1, "note": sh["why"],
             "source": {"fichier": path, "in_s": round(sh["t"], 3), "out_s": round(sh["t"] + n_src / sfps * sh.get("speed", 100) / 100, 3),
                        "fps": round(sfps, 3), "url": url, "t_youtube_s": round(off + sh["t"], 2), "contexte": ctx},
             "temps": round(sh["n"] / FPS / 0.5, 2)}
        if sh.get("speed"): v["retime"] = "optical_flow"; v["note"] += " — ralenti %d %% (Optical Flow dans Resolve ; e - s = durée à vitesse normale)" % sh["speed"]
        if sh.get("fade"): v["fade_out_s"] = round(sh["fade"] / FPS, 2)
        video.append(v)
    plan = {"name": "M2 - Aura couleur multi-contextes - Manon Aubry", "fps": FPS, "w": W, "h": H, "duree_s": END,
            "note": "Plans ProRes 9:16 recadrés + étalonnage couleur léger (lot4/_claude/gen/M2/out), aucun texte (recette jaxnotpl3). s/e en images du clip (30 i/s), "
                    "rec en images timeline. Coupes sur les kicks pleins réels d'Au DD (out/M2-frappes.json), drop = 1er kick du refrain sur « DD ». "
                    "Générateur : lot4/_claude/gen/M2/genM2.py",
            "phrase": {"texte": "Nous privilégierons les milliards d'êtres humains aux milliards de quelques humains.",
                       "url": SRC["SOT"][2], "source": SRC["SOT"][0], "in_s": 87.18, "out_s": 92.58,
                       "timeline_s": [round(t_of_src(87.18), 2), round(t_of_src(92.58), 2)],
                       "voix": "son direct synchro sur le gros plan, puis en off sur le plan large (même discours) ; finit dans le break avant « Au DD »"},
            "musique": {"fichier": "lot4/sons/M2-pnl-au-dd_complet.wav", "titre": "PNL - Au DD", "url": SON_URL,
                        "debut_complet_s": round(MUSIC_IN, 4), "fin_complet_s": round(MUSIC_IN + END, 3), "drop_timeline_s": CUTS[1],
                        "coupes_kicks_s": CUTS, "coupes_images": CUTF},
            "video": video,
            "audio": [{"id": "mix", "clip": "M2-mix.wav", "folder": "genM2", "path": OUT + "M2-mix.wav", "rec": 0, "track": 1,
                       "note": "mix -14 LUFS : voix SOT %.2f-%.2f s (+4 dB) à %.2f s ; Au DD dès %.3f s du complet, -24 -> -15 -> -9 dB sous la voix, plein dès « Au DD », fondu de fin 0,5 s"
                               % (V_IN, V_OUT, t_of_src(V_IN), MUSIC_IN)}],
            "stems": ["lot4/_claude/gen/M2/out/M2-voix.wav", "lot4/_claude/gen/M2/out/M2-musique.wav"],
            "logos_exclus": "SOT/PLE : logo de l'hémicycle et pupitre hors cadre ; soirée 2024 : logo LFI, bandeau et pancarte hors cadre ; meeting : logo ELA hors cadre ; von der Leyen hors cadre"}
    json.dump(plan, open(D + "plan-M2.json", "w"), indent=1, ensure_ascii=False)
# ---------------- aperçu 540x960 ----------------
def apercu():
    plan = json.load(open(D + "plan-M2.json")); ins = []; fl = []
    for i, v in enumerate(plan["video"]):
        n = v["e"] - v["s"]; sp = v.get("speed_pct", 100) / 100; ins += ["-i", OUT + v["clip"]]
        if sp < 1:
            fl.append("[%d:v]trim=start_frame=0:end_frame=%d,setpts=(PTS-STARTPTS)/%.4f,fps=30,trim=end_frame=%d,setpts=PTS-STARTPTS,scale=540:960,setsar=1[v%d]"
                      % (i, math.ceil(n * sp) + 1, sp, n, i))
        else:
            fl.append("[%d:v]trim=start_frame=%d:end_frame=%d,setpts=PTS-STARTPTS,scale=540:960,setsar=1[v%d]" % (i, v["s"], v["e"], i))
    k = len(plan["video"]); fl.append("".join("[v%d]" % i for i in range(k)) + "concat=n=%d:v=1:a=0[v]" % k)
    ins += ["-i", OUT + "M2-mix.wav"]; out = HG + "/preview/apercu-M2.mp4"
    subprocess.run([FF, "-v", "error", "-y"] + ins + ["-filter_complex", ";".join(fl), "-map", "[v]", "-map", "%d:a" % k,
                    "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "aac", "-b:a", "192k", "-shortest", out], check=True)
    print("aperçu", out)
# ---------------- mesure sur l'export : coupes vs frappes, LUFS / TP ----------------
def mesure():
    out = HG + "/preview/apercu-M2.mp4"
    r = subprocess.run([FF, "-v", "info", "-i", out, "-vf", "scale=135:240,select='gt(scene,0.25)',showinfo", "-an", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    import re
    cuts = [float(x) for x in re.findall(r"pts_time:([0-9.]+)", r)]
    p = subprocess.run([FF, "-v", "error", "-i", out, "-vn", "-ac", "2", "-ar", "48000", "-f", "f32le", "-"], capture_output=True)
    y = np.frombuffer(p.stdout, np.float32).reshape(-1, 2)
    h = [x[0] for x in detect_hits(y) if x[1] == "kick" and x[3] > 0.2]
    print("coupes image (export) :", cuts)
    for c in cuts:
        k = min(h, key=lambda t: abs(t - c)); print("  coupe %.3f  kick %.4f  écart %+.1f ms" % (c, k, (c - k) * 1000))
    r = subprocess.run([FF, "-hide_banner", "-i", out, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    print(r[r.rindex("Summary"):])
if __name__ == "__main__":
    args = set(a for a in sys.argv[1:] if not a.startswith("only=")) or {"shots", "audio", "plan", "apercu"}
    only = [x for a in sys.argv[1:] if a.startswith("only=") for x in a.split("=", 1)[1].split(",")]
    print("musique dès %.4f s ; coupes (s) :" % MUSIC_IN, CUTS, "images :", CUTF)
    if "shots" in args or only:
        for sh in SHOTS:
            if not only or sh["id"] in only: render(sh)
    if "audio" in args: make_audio()
    if "plan" in args: build_plan()
    if "apercu" in args: apercu()
    if "mesure" in args: mesure()
