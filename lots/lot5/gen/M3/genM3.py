# M3 (lot 5) — Aura couleur multi-contextes (inspi jaxnotpl3, comme M1/M2), Louis Boyard, son PNL – Le monde ou rien (clip officiel, chaîne PNL).
# Recette jaxnotpl3 : 4-6 contextes de la figure (jeune -> actuel), coupes posées (~2 s) sur les vraies frappes, plan « cool » sur le drop
# (ici : Boyard, 21 ans, de dos, qui entre au Palais Bourbon en juin 2022, à la place des lunettes noires de Macron),
# couleur naturelle (correction légère, pas de LUT, pas de N&B), archives brutes sans texte ajouté.
# Phrase (son direct) : « Alors, à vous, les dirigeants du XXe siècle, nous vous regardons et nous vous jugeons. »
#   (meeting « Nouveau Paris populaire », 31/01/2026, chaîne Louis Boyard, youtu.be/cNkMqVnlUl0 255,80-261,48 s)
#   -> autre phrase que G1 (santé mentale), K1 (QAG « La jeunesse vient de prendre conscience… ») et A9 (« La jeune génération a commencé… »).
#   Synchro sur le 1er plan, puis en off sur Boyard muet qui fixe son contradicteur (Le Duel franceinfo, oct. 2026).
# Son : Le monde ou rien, refrain ; montée sous la phrase (« ouais ouais… pour les miens… »), drop = kick du refrain juste avant « Le monde ou rien ».
# Règles : 9:16 plein écran, aucun visage coupé, aucun logo, plans >= 1 temps, pas de dézoom, <= 15 s, ralentis = speed_pct (Resolve).
# Usage : python genM3.py [shots] [audio] [plan] [apercu] [mesure] [only=ID,ID]   (sans argument = shots audio plan apercu)
import sys, os, json, subprocess, math, re
import numpy as np, cv2
HG = "/Users/luca.grousset/Movies/highkey-gauchiste"
sys.path.insert(0, HG + "/_claude/outils")
import framing
from fx import gblur, vignette, grain, to8
D = HG + "/lot5/_claude/gen/M3/"; OUT = D + "out/"; CACHE = D + "cache/faces"; os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, D)
from hits import detect_hits
FF = "/opt/homebrew/bin/ffmpeg"; FACES = HG + "/_claude/outils/faces"; FPS = 30; W, H = 1080, 1920
def fr(t): return int(round(t * FPS))

# ---------------- sources (chemins relatifs au projet) : fichier, fps, url, décalage YouTube, contexte ----------------
SRC = {
    "NPPB": ("lot3/sources/K1-boyard-meeting-npp-b.mp4", 25.0, "https://www.youtube.com/watch?v=cNkMqVnlUl0", 252.0,
             "meeting « Nouveau Paris populaire », Paris, 31/01/2026 (chaîne Louis Boyard)"),
    "NPPA": ("lot3/sources/K1-boyard-meeting-npp-a.mp4", 25.0, "https://www.youtube.com/watch?v=cNkMqVnlUl0", 140.0,
             "meeting « Nouveau Paris populaire », Paris, 31/01/2026 (chaîne Louis Boyard)"),
    "DUEL": ("lot1/sources/4-boyard-franceinfo-duel-a.mp4", 25.0, "https://www.youtube.com/watch?v=dn01kQrjkBo", 390.0,
             "Le Duel franceinfo face à Ian Boucard (LR), révolte lycéenne, 06/10/2026 (chaîne franceinfo)"),
    "PAR": ("lot5/sources/M3-boyard-parisien-2022.mp4", 25.0, "https://www.youtube.com/watch?v=sR6LUFh-oUI", 22.0,
            "premiers pas à l'Assemblée du député de 21 ans, juin 2022 (chaîne Le Parisien)"),
    "COM": ("lot2/sources/G1-boyard-an-santementale-2026-04.mp4", 25.0, "https://www.youtube.com/watch?v=C_qSIfecvAw", 0.0,
            "rapport sur la santé mentale des jeunes, Assemblée nationale, 29/04/2026 (chaîne La France insoumise à l'Assemblée nationale)"),
    "PARIS": ("lot5/sources/M3-boyard-meeting-paris-2026-10.mp4", 25.0, "https://www.youtube.com/watch?v=3QUZoFMQQig", 795.0,
              "meeting de Paris (Mélenchon 2027), intervention de Louis Boyard « Les jeunes nous font honneur », publiée le 14/10/2026 (chaîne Louis Boyard)"),
}
B_NPP = (0, 0, 1690, 790)            # pupitre « Nouveau Paris populaire » et logo LFI haut droite exclus (A9)
B_DUEL = (966, 135, 1920, 825)       # panneau de Boyard, sans le bandeau « Le Duel » ni Ian Boucard (test 4)
B_PAR = (0, 0, 1480, 1080)           # logo Le Parisien 2022 (haut droite) exclu
B_COM = (230, 90, 1650, 960)         # logos LFI / AN (coins hauts) et plaque nominative exclus
B_PARIS = (300, 0, 1560, 700)       # logo MELENCHON2027.fr (haut droite), pupitre « PARIS » et visages du public (bas) exclus

# têtes : boîte un peu plus large que celle de Vision (cheveux)
framing.head_box = lambda f: (f[0] - 0.25 * f[2], f[1] - 0.55 * f[3], f[0] + 1.25 * f[2], f[1] + 1.22 * f[3])
def detect(src, s, n, fps):
    """framing.detect avec cache dans gen/M3 (les sources des lots 1-4 ne sont que lues) ; boîtes en px d'une image 1920x1080."""
    path = SRC[src][0]
    d = "%s/%s_%d_%d" % (CACHE, os.path.splitext(os.path.basename(path))[0], s, n)
    if not os.path.exists(d + "/faces.json"):
        os.makedirs(d, exist_ok=True)
        subprocess.run([FF, "-v", "error", "-y", "-ss", "%.4f" % (s / fps), "-i", HG + "/" + path, "-frames:v", str(n), "-vf", "scale=960:540",
                        "-fps_mode", "passthrough", "-start_number", "0", "-q:v", "3", d + "/f%04d.jpg"], check=True)
        subprocess.run([FACES, d], check=True, capture_output=True)
    js = json.load(open(d + "/faces.json"))
    return [[(b[0] * 1920, b[1] * 1080, b[2] * 1920, b[3] * 1080) for b in js.get("f%04d.jpg" % i, [])] for i in range(n)]
framing.detect = detect

# ---------------- musique : PNL – Le monde ou rien ----------------
SON_FILE = HG + "/lot5/sons/M3-pnl-le-monde-ou-rien.wav"; SON_URL = "https://www.youtube.com/watch?v=umF1kfVujhM"
MDROP = 101.07                       # kick qui ouvre la 2e moitié du refrain, 0,6 s avant « Le monde ou rien » (101,66)
DROP = 6.0; END = 15.0               # aura : 15 s max ; fin sur le kick 110,06
MUSIC_IN0 = MDROP - DROP
# coupes (s timeline, avant calage) : A->B sur le kick 96,99 (avant le changement de plan de la source), drop, puis cycle 102,81 / 105,13 / 107,47
CUT_T = [96.99 - MUSIC_IN0, DROP, 102.81 - MUSIC_IN0, 105.13 - MUSIC_IN0, 107.47 - MUSIC_IN0]
HITS_JSON = OUT + "M3-frappes.json"
def music_raw(mi, dur=END + 0.5, sr=48000):
    import soundfile as sf
    i0 = int(round(mi * sr)); x, r = sf.read(SON_FILE, start=i0, frames=int(dur * sr), dtype="float32"); assert r == sr; return x
def is_hit(h): return (h[1] == "kick" and h[3] > 0.3) or (h[1] == "caisse" and h[2] > 0.4)
def frappes():
    """Décalage sous-image de l'extrait pour que les frappes des coupes tombent au plus près des images ; frappes re-mesurées sur l'extrait posé."""
    if os.path.exists(HITS_JSON):
        js = json.load(open(HITS_JSON))
        if js["cle"] == [MUSIC_IN0, END, CUT_T]: return js["music_in"], js["frappes"]
    best, bad = None, 9
    for off in np.arange(-0.016, 0.0165, 0.001):
        h = detect_hits(music_raw(MUSIC_IN0 + off)); ks = [x[0] for x in h if is_hit(x)]
        near = [min(ks, key=lambda k: abs(k - t)) for t in CUT_T]
        if max(abs(c - t) for c, t in zip(near, CUT_T)) > 0.04: continue
        e = max(abs(c - round(c * FPS) / FPS) for c in near)
        if e < bad: best, bad, hb = off, e, h
    mi = MUSIC_IN0 + best
    json.dump({"cle": [MUSIC_IN0, END, CUT_T], "music_in": mi, "frappes": hb}, open(HITS_JSON, "w")); return mi, hb
MUSIC_IN, HITS = frappes()
KICKS = [h[0] for h in HITS if is_hit(h)]
def snap(t):
    c = min(KICKS, key=lambda x: abs(x - t)); assert abs(c - t) < 0.04, ("pas de frappe près de", t, c); return c
CUTS = [snap(t) for t in CUT_T]; CUTF = [fr(c) for c in CUTS]
# ---------------- voix ----------------
V_SRC0 = 3.55                         # source NPPB à t = 0 : « Alors » (3,80) à 0,25 s ; « jugeons. » finit à 9,48 -> 5,93 s, avant le drop
V_IN, V_OUT = 3.72, 9.62              # « Alors » 3,80 … « jugeons. » fin 9,48 (Whisper) + queue ; « Nous tirons… » (9,76) non gardé
def t_of_src(s): return s - V_SRC0
# ---------------- plans ----------------
SHOTS = [
    dict(id="phrase", src="NPPB", t=V_SRC0, b=B_NPP, face=(950, 320), vh=790, zoom=(1.0, 1.05), top=0.12,
         why="janv. 2026 — meeting Nouveau Paris populaire : « Alors, à vous, … » en son direct (avant le plan de salle de la source à 5,56 s)"),
    dict(id="regard", src="DUEL", t=73.60, b=B_DUEL, face=(1500, 300), vh=690, zoom=(1.0, 1.08), top=0.14,
         why="oct. 2026 — Le Duel franceinfo : muet, la main au menton, il fixe Ian Boucard pendant que sa voix dit « …nous vous regardons et nous vous jugeons » (Boucard et bandeau hors cadre)"),
    dict(id="2022", src="PAR", t=5.35, b=B_PAR, fixed=(400, 540), vh=1080, zoom=(1.0, 1.05), expo=1.35,
         why="DROP — juin 2022, 21 ans, nouveau député : de dos, il pousse la porte vitrée et entre au Palais Bourbon (plan « cool » à la place des lunettes, comme le couloir de M2)"),
    dict(id="commission", src="COM", t=29.50, b=B_COM, face=(1000, 300), vh=860, zoom=(1.0, 1.05), top=0.12,
         why="avr. 2026 — Assemblée, rapport santé mentale des jeunes : deux doigts levés"),
    dict(id="balcon", src="NPPA", t=43.00, b=B_NPP, face=(1040, 150), vh=790, zoom=(1.0, 1.05), top=0.12,
         why="janv. 2026 — meeting Nouveau Paris populaire : de profil, regard levé vers le balcon, main levée"),
    dict(id="paris", src="PARIS", t=4.30, b=B_PARIS, face=(1000, 240), vh=700, zoom=(1.0, 1.04), top=0.12, fade=12,
         why="oct. 2026 (aujourd'hui) — meeting de Paris, gros plan, il harangue la salle (fin, fondu au noir)"),
]
BOUNDS_T = [0] + CUTF + [fr(END)]
for i, sh in enumerate(SHOTS):
    sh["a"], sh["bb"] = BOUNDS_T[i], BOUNDS_T[i + 1]; sh["n"] = sh["bb"] - sh["a"]; sh["clip"] = "M3_%s.mov" % sh["id"]
assert min(sh["n"] for sh in SHOTS) >= 18, [(s["id"], s["n"]) for s in SHOTS]
assert SHOTS[0]["t"] + SHOTS[0]["n"] / FPS <= 5.54, SHOTS[0]["t"] + SHOTS[0]["n"] / FPS   # avant le plan de salle de la source
assert t_of_src(9.48) < CUTS[1], "la phrase doit finir avant le drop"

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
# ---------------- lecture source (mise à 1920x1080) + recadrage ----------------
def read_frames(src, t, n_out):
    path, sfps = SRC[src][0], SRC[src][1]
    need = [int(round(i * sfps / FPS)) for i in range(n_out)]
    p = subprocess.run([FF, "-v", "error", "-ss", "%.4f" % t, "-i", HG + "/" + path, "-frames:v", str(need[-1] + 1),
                        "-vf", "scale=1920:1080:flags=lanczos", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True)
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
def views_of(sh):
    n = sh["n"]; sfps = SRC[sh["src"]][1]
    m = math.ceil(n * sh.get("speed", 100) / 100)
    z0, z1 = sh["zoom"]; zoom = lambda f: z0 + (z1 - z0) * min(f / max(m - 1, 1), 1.0)
    s0 = int(round(sh["t"] * sfps))
    if "fixed" in sh:
        return framing.plan_views(sh["src"], s0, n, sfps, speed=sfps / FPS, bounds=sh["b"], vh=sh["vh"], zoom=zoom, fixed=sh["fixed"])
    return framing.plan_views(sh["src"], s0, n, sfps, speed=sfps / FPS, hint=sh["face"], bounds=sh["b"], vh=sh["vh"], zoom=zoom, top=sh.get("top", 0.15))
def render(sh):
    n = sh["n"]
    raw = read_frames(sh["src"], sh["t"], n)                         # vitesse normale (ralenti éventuel = Resolve)
    views, ok = views_of(sh)
    if not ok and "fixed" not in sh: print("  ! pas de visage :", sh["id"])
    frames = []
    for i, (img, (cx, cy, vh)) in enumerate(zip(raw, views)):
        g = grade(crop_916(img, cx, cy, vh), sh.get("expo", 1.0))
        if sh.get("fade") and i >= n - sh["fade"]: g = g * ((n - i - 1) / sh["fade"])
        frames.append(g)
    write_mov(frames, OUT + sh["clip"])
    v0, v1 = views[0], views[-1]
    print("  %-10s %3d im  vue %d,%d h%d -> %d,%d h%d" % (sh["id"], n, v0[0], v0[1], v0[2], v1[0], v1[1], v1[2]))
# ---------------- audio ----------------
def make_audio():
    import soundfile as sf
    sr = 48000; N = int(round(END * sr))
    def grab(path, t, dur):
        p = subprocess.run([FF, "-v", "error", "-ss", "%.3f" % t, "-t", "%.3f" % dur, "-i", path, "-ac", "2", "-ar", str(sr), "-f", "f32le", "-"], capture_output=True)
        return np.frombuffer(p.stdout, np.float32).reshape(-1, 2).copy()
    voix = np.zeros((N, 2), np.float32); mus = np.zeros((N, 2), np.float32)
    v = grab(HG + "/" + SRC["NPPB"][0], V_IN, V_OUT - V_IN); env = np.ones(len(v), np.float32)
    k = int(0.03 * sr); env[:k] = np.linspace(0, 1, k); k = int(0.10 * sr); env[-k:] = np.linspace(1, 0, k)
    a = int(round(t_of_src(V_IN) * sr)); voix[a:a + len(v)] = v * env[:, None] * 10 ** (4 / 20)
    m = music_raw(MUSIC_IN)[:N]
    # musique qui monte sous la phrase (-24 -> -15 -> -9 dB), pleine sur le drop (kick avant « Le monde ou rien »)
    t = np.arange(len(m)) / sr; td = CUTS[1]
    gdb = np.interp(t, [0, 0.4, t_of_src(9.48), td - 0.02, td, END], [-24, -15, -9, -7, 0, 0])
    k = int(0.45 * sr); fo = np.ones(len(m), np.float32); fo[-k:] = np.linspace(1, 0, k)
    mus[:len(m)] = m * (10 ** (gdb / 20) * fo)[:, None] * 10 ** (4 / 20)
    sf.write(OUT + "M3-voix.wav", voix, sr, subtype="PCM_24"); sf.write(OUT + "M3-musique.wav", mus, sr, subtype="PCM_24")
    sf.write(D + "tmp_mix.wav", voix + mus, sr, subtype="FLOAT")
    r = subprocess.run([FF, "-hide_banner", "-i", D + "tmp_mix.wav", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    js = json.loads(r[r.rindex("{"):r.rindex("}") + 1])
    af = ("loudnorm=I=-14:TP=-1.5:LRA=11:measured_I=%s:measured_TP=%s:measured_LRA=%s:measured_thresh=%s:offset=%s:linear=true,"
          "alimiter=limit=0.85:level=false:attack=1:release=60,aresample=48000" % (js["input_i"], js["input_tp"], js["input_lra"], js["input_thresh"], js["target_offset"]))
    subprocess.run([FF, "-v", "error", "-y", "-i", D + "tmp_mix.wav", "-af", af, "-c:a", "pcm_s24le", OUT + "M3-mix.wav"], check=True)
    os.remove(D + "tmp_mix.wav"); print("audio : mix avant normalisation", js["input_i"], "LUFS")
# ---------------- plan + fiche son ----------------
PHRASE = "Alors, à vous, les dirigeants du XXe siècle, nous vous regardons et nous vous jugeons."
def build_plan():
    video = []
    for sh in SHOTS:
        path, sfps, url, off, ctx = SRC[sh["src"]]
        n_src = int(round(sh["n"] / FPS * sfps))
        v = {"id": sh["id"], "clip": sh["clip"], "folder": "genM3", "path": OUT + sh["clip"], "s": 0, "e": sh["n"], "rec": sh["a"], "dur": sh["n"],
             "clip_fps": FPS, "speed_pct": sh.get("speed", 100), "track": 1, "note": sh["why"],
             "source": {"fichier": path, "in_s": round(sh["t"], 3), "out_s": round(sh["t"] + n_src / sfps * sh.get("speed", 100) / 100, 3),
                        "fps": round(sfps, 3), "url": url, "t_youtube_s": round(off + sh["t"], 2), "contexte": ctx},
             "temps": round(sh["n"] / FPS / (60 / 103.4), 2)}
        if sh.get("speed"): v["retime"] = "optical_flow"
        if sh.get("fade"): v["fade_out_s"] = round(sh["fade"] / FPS, 2)
        video.append(v)
    plan = {"name": "M3 - Aura couleur multi-contextes - Louis Boyard", "fps": FPS, "w": W, "h": H, "duree_s": END,
            "note": "Plans ProRes 9:16 recadrés + étalonnage couleur léger (lot5/_claude/gen/M3/out), aucun texte (recette jaxnotpl3). s/e en images du clip (30 i/s), "
                    "rec en images timeline. Coupes sur les frappes réelles de Le monde ou rien (out/M3-frappes.json), drop = kick avant « Le monde ou rien ». "
                    "Aucun ralenti. Générateur : lot5/_claude/gen/M3/genM3.py",
            "phrase": {"texte": PHRASE, "url": SRC["NPPB"][2], "source": SRC["NPPB"][0], "in_s": 3.80, "out_s": 9.48,
                       "t_youtube_s": [255.80, 261.48], "timeline_s": [round(t_of_src(3.80), 2), round(t_of_src(9.48), 2)],
                       "voix": "son direct synchro sur le 1er plan (« Alors, à vous, »), puis en off sur Boyard muet au Duel franceinfo ; finit 0,07 s avant le drop"},
            "musique": {"fichier": "lot5/sons/M3-pnl-le-monde-ou-rien.wav", "titre": "PNL - Le monde ou rien", "url": SON_URL,
                        "debut_complet_s": round(MUSIC_IN, 4), "fin_complet_s": round(MUSIC_IN + END, 3), "drop_timeline_s": CUTS[1],
                        "coupes_frappes_s": CUTS, "coupes_images": CUTF},
            "video": video,
            "audio": [{"id": "mix", "clip": "M3-mix.wav", "folder": "genM3", "path": OUT + "M3-mix.wav", "rec": 0, "track": 1,
                       "note": "mix -14 LUFS : voix NPPB %.2f-%.2f s (+4 dB) à %.2f s ; Le monde ou rien dès %.3f s du morceau, -24 -> -15 -> -9 dB sous la voix, plein au drop, fondu de fin 0,45 s"
                               % (V_IN, V_OUT, t_of_src(V_IN), MUSIC_IN)}],
            "stems": ["lot5/_claude/gen/M3/out/M3-voix.wav", "lot5/_claude/gen/M3/out/M3-musique.wav"],
            "logos_exclus": "meeting : pupitre « Nouveau Paris populaire » et logo LFI hors cadre ; Duel : bandeau franceinfo et Ian Boucard hors cadre ; "
                            "Le Parisien : logo haut droite hors cadre ; Assemblée : logos LFI/AN et plaque hors cadre ; meeting de Paris : logo MELENCHON2027.fr, pupitre et public hors cadre"}
    json.dump(plan, open(D + "plan-M3.json", "w"), indent=1, ensure_ascii=False)
    son = {"id": "M3", "titre": "Le monde ou rien", "artiste": "PNL", "url": SON_URL,
           "chaine": "PNL (officielle, vérifiée, « PNL - Le monde ou rien [Clip Officiel] », 12/06/2015)",
           "fichier": "lot5/sons/M3-pnl-le-monde-ou-rien.wav",
           "extrait_complet_s": {"debut": round(MUSIC_IN, 4), "fin": round(MUSIC_IN + END, 3)},
           "paroles_audibles": "sous la phrase (musique -15 -> -9 dB) : « Ouais ouais ouais… / Pour les miens / Ouais ouais ouais… » ; drop puis "
                               "« Le monde ou rien / Ouais ouais ouais… / Moi ça m'convient / Ouais ouais… » (2e moitié du 1er refrain)",
           "bpm": 103.4, "temps_s": round(60 / 103.4, 3),
           "drop": {"complet_s": round(MUSIC_IN + CUTS[1], 4), "timeline_s": CUTS[1], "nature": "kick qui ouvre la 2e moitié du refrain, 0,6 s avant « Le monde ou rien », après le creux de basse 99,5-100,5 s"},
           "frappes_timeline_s": [round(h[0], 4) for h in HITS if is_hit(h)],
           "coupes_sur_frappes_s": CUTS, "mix": "lot5/_claude/gen/M3/out/M3-mix.wav"}
    json.dump(son, open(D + "son.json", "w"), indent=1, ensure_ascii=False)
# ---------------- aperçu 540x960 ----------------
def apercu():
    plan = json.load(open(D + "plan-M3.json")); ins = []; fl = []
    for i, v in enumerate(plan["video"]):
        ins += ["-i", OUT + v["clip"]]
        fl.append("[%d:v]trim=start_frame=%d:end_frame=%d,setpts=PTS-STARTPTS,scale=540:960,setsar=1[v%d]" % (i, v["s"], v["e"], i))
    k = len(plan["video"]); fl.append("".join("[v%d]" % i for i in range(k)) + "concat=n=%d:v=1:a=0[v]" % k)
    ins += ["-i", OUT + "M3-mix.wav"]; out = HG + "/preview/apercu-M3.mp4"
    subprocess.run([FF, "-v", "error", "-y"] + ins + ["-filter_complex", ";".join(fl), "-map", "[v]", "-map", "%d:a" % k,
                    "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "aac", "-b:a", "192k", "-shortest", out], check=True)
    print("aperçu", out)
# ---------------- mesure sur l'export : coupes vs frappes, LUFS / TP ----------------
def mesure():
    out = HG + "/preview/apercu-M3.mp4"
    r = subprocess.run([FF, "-v", "info", "-i", out, "-vf", "scale=135:240,select='gt(scene,0.25)',showinfo", "-an", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    cuts = [float(x) for x in re.findall(r"pts_time:([0-9.]+)", r)]
    p = subprocess.run([FF, "-v", "error", "-i", out, "-vn", "-ac", "2", "-ar", "48000", "-f", "f32le", "-"], capture_output=True)
    y = np.frombuffer(p.stdout, np.float32).reshape(-1, 2)
    h = [x[0] for x in detect_hits(y) if (x[1] == "kick" and x[3] > 0.2) or (x[1] == "caisse" and x[2] > 0.4)]
    print("coupes image (export) :", cuts)
    for c in cuts:
        k = min(h, key=lambda t: abs(t - c)); print("  coupe %.3f  frappe %.4f  écart %+.1f ms" % (c, k, (c - k) * 1000))
    r = subprocess.run([FF, "-hide_banner", "-i", out, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    print(r[r.rindex("Summary"):])
if __name__ == "__main__":
    args = set(a for a in sys.argv[1:] if not a.startswith("only=")) or {"shots", "audio", "plan", "apercu"}
    only = [x for a in sys.argv[1:] if a.startswith("only=") for x in a.split("=", 1)[1].split(",")]
    print("musique dès %.4f s ; coupes (s) :" % MUSIC_IN, [round(c, 4) for c in CUTS], "images :", CUTF)
    if "shots" in args or only:
        for sh in SHOTS:
            if not only or sh["id"] in only: render(sh)
    if "audio" in args: make_audio()
    if "plan" in args: build_plan()
    if "apercu" in args: apercu()
    if "mesure" in args: mesure()
