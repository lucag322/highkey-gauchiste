# Lot 3 — V1 Longue pose N&B (inspi nobleactually, Bernie) : Manon Aubry, meeting Palestine Strasbourg 17/06/2026, son Stromae – Santé.
# Recette : une longue pose de 8,4 s SANS coupe (tension), puis coupes sur les vraies frappes du drop, qui accélèrent (2, 2 puis 1 temps).
# N&B très contrasté (noirs bas, blancs hauts) + grain, plan de dos vers la foule = entrée du drop (« rockstar qui monte sur scène »).
# Texte (DA) : phrase réelle d'Aubry mot à mot (AmFIs 2026), Arial Black, contour noir, mot-clé RIEN en rouge, sans guillemets.
# Règles : 15 s max, 9:16 plein écran, aucun visage coupé, plans >= 1 temps, pas de dézoom, aucun ralenti précalculé, -14 LUFS.
# Usage : python genV1.py [shots] [plan] [audio] [apercu] [check] [mesure]   (sans argument = tout) | only=<id>
import sys, os, json, subprocess, math, shutil
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
HG = "/Users/luca.grousset/Movies/highkey-gauchiste"; L3 = HG + "/lot3"
sys.path.insert(0, HG + "/_claude/outils")
from fx import gblur, vignette, to8, ease_out
import framing
D = L3 + "/_claude/gen/V1/"; OUT = D + "out/"; os.makedirs(OUT, exist_ok=True)
framing.ROOT = L3; framing.CACHE = D + "cache/faces"                      # sources du lot 3, cache visages dans gen/V1
from framing import plan_views
FF = "/opt/homebrew/bin/ffmpeg"; FACES = HG + "/_claude/outils/faces"; FPS = 30; W, H = 1080, 1920
RED = (0xE4, 0x00, 0x2B); WHITE = (255, 255, 255)
F_BLACK = "/System/Library/Fonts/Supplemental/Arial Black.ttf"
SA, SB, SC, SD, SE = ("V1-aubry-strasbourg-a.mp4", "V1-aubry-strasbourg-b.mp4", "V1-aubry-strasbourg-c.mp4", "V1-aubry-strasbourg-d.mp4",
                      "V1-aubry-strasbourg-e.mp4")
YT = "https://www.youtube.com/watch?v=c-KnJoiz928"                         # chaîne Manon Aubry, meeting Strasbourg 17/06/2026
OFFS = {SA: 0, SB: 84, SC: 440, SD: 770, SE: 725}                                   # début de l'extrait dans la vidéo YouTube (s)
SRCFPS = 25
BOUNDS = (0, 0, 1620, 1080)                                                # logo « ELA » en haut à droite (x > 1640) exclu
# ---------------- son : Stromae – Santé (clip officiel). Musique qui monte sous la phrase, puis le REFRAIN tombe juste après « rien » ----------------
SONG = L3 + "/sons/V1-stromae-sante_complet.wav"; END = 14.4
# vraies frappes mesurées (frappes.json) : caisse claire du refrain, puis kicks du drop (49,957 s dans le morceau)
HITS = json.load(open(D + "frappes.json"))
MOFF = HITS["MOFF"]; DROP = HITS["drop_t"]; K = HITS["kicks_drop_t"]; SN = HITS["cartons_t"]
def fr(t): return int(round(t * FPS))
# ---------------- plans ----------------
SHOTS = {
    "pose":  dict(src=SE, t=15.13, face=(1000, 300), zoom=(1.0, 1.08), why="longue pose en son direct : « un peuple à libérer, alors nous continuerons. Nous continuerons et nous ne lâcherons rien. »"),
    "dos":   dict(src=SA, t=36.0, fixed=(1010, 560), vh=1000, zoom=(1.0, 1.04), why="plan de dos, face à la foule (entrée du drop)"),
    "salle": dict(src=SD, t=14.0, fixed=(900, 640), vh=880, zoom=(1.0, 1.04), why="salle debout, ovation finale"),
    "poing": dict(src=SC, t=19.0, face=(1000, 300), zoom=(1.02, 1.06), why="poing levé"),
    "poing2": dict(src=SC, t=22.85, face=(1000, 300), zoom=(1.02, 1.06), why="poing levé, voix forte"),
    "foule": dict(src=SB, t=12.0, fixed=(960, 600), vh=1000, zoom=(1.0, 1.04), why="salle comble (plan large)"),
    "bras":  dict(src=SC, t=24.0, face=(1000, 300), zoom=(1.02, 1.06), why="bras levé"),
    "poing3": dict(src=SC, t=27.85, face=(1000, 300), zoom=(1.02, 1.06), why="poing serré"),
    "fin":   dict(src=SA, t=40.75, face=(1000, 300), zoom=(1.02, 1.07), why="poing levé, fin (autre caméra)"),
}
# après l'arrivée du refrain : 2, 2, 2, 2 puis 1 temps (accélération comme la réf), dernier plan jusqu'à 15 s
EDIT = ["dos", "salle", "poing", "poing2", "foule", "bras", "poing3", "fin"]
BEATS = [2, 2, 2, 2, 1, 1, 1, 2]
def cut_times():
    ts = [DROP]; k = 0
    for b in BEATS[:-1]: k += b; ts.append(K[k])
    return ts + [END]
# ---------------- look : N&B très contrasté (lift bas, gain haut), grain fin ----------------
RNG = np.random.default_rng(3)
def grade(bgr):
    # lumière magenta de la salle : la peau vit surtout dans le rouge -> mélange N&B orienté rouge
    g = 0.15 * bgr[..., 0] + 0.40 * bgr[..., 1] + 0.45 * bgr[..., 2]
    g = np.clip((g - 0.06) / 0.80, 0, 1)
    g = 0.35 * g + 0.65 * (g * g * (3 - 2 * g))                             # courbe en S forte
    small = cv2.resize(g, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    hi = np.clip(small - 0.6, 0, None) * 2.0
    g = g + cv2.resize(cv2.GaussianBlur(hi, (0, 0), 8), (W, H)) * 0.30      # léger halo des hautes lumières
    g = vignette(g[..., None], 0.42, 2.2)[..., 0]
    g = 0.039 + np.clip(g, 0, 1) * (0.91 - 0.039)                            # noirs #0A0A0A, blancs #E8E8E8 (réf)
    n = cv2.resize(RNG.normal(0, 1, (H // 2, W // 2)).astype(np.float32), (W, H))
    g = g + n * 0.028
    return np.repeat(np.clip(g, 0, 1)[..., None], 3, 2)
def read_frames(src, t, n_out):
    cap = cv2.VideoCapture(L3 + "/sources/" + src)
    s0 = int(round(t * SRCFPS)); cap.set(cv2.CAP_PROP_POS_FRAMES, s0)
    need = [int(i * SRCFPS / FPS) for i in range(n_out)]; buf = []; k = 0
    while k <= need[-1]:
        ok, f = cap.read()
        if not ok: break
        buf.append(f); k += 1
    return [buf[min(i, len(buf) - 1)].astype(np.float32) / 255 for i in need], s0
def crop_916(img, cx, cy, vh):
    vw = vh * 9 / 16; s = W / vw
    M = np.float32([[s, 0, W / 2 - cx * s], [0, s, H / 2 - cy * s]])
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
# ---------------- texte ----------------
def font(size): return ImageFont.truetype(F_BLACK, size)
def fit_size(txt, maxw, start=200):
    s = start
    while font(s).getlength(txt) > maxw: s -= 4
    return s
def text_layer(lines, alpha_scale=1.0, scale=1.0):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay); ds = ImageDraw.Draw(sh)
    for txt, col, size, yc in lines:
        sz = max(8, int(size * scale)); f = font(sz); sw = max(4, int(sz * 0.045))
        x0, y0, x1, y1 = d.textbbox((0, 0), txt, font=f, stroke_width=sw)
        x = W / 2 - (x1 - x0) / 2 - x0; y = yc - (y1 - y0) / 2 - y0
        ds.text((x, y + sz * 0.05), txt, font=f, fill=(0, 0, 0, 210), stroke_width=sw * 3, stroke_fill=(0, 0, 0, 210))
        d.text((x, y), txt, font=f, fill=col + (255,), stroke_width=sw, stroke_fill=(0, 0, 0, 255))
    sh = sh.filter(ImageFilter.GaussianBlur(18))
    a = np.asarray(Image.alpha_composite(sh, lay)).astype(np.float32) / 255
    a[..., 3] *= alpha_scale
    return a
def over_rgba(img_bgr, rgba):
    a = rgba[..., 3:4]; rgb = rgba[..., 2::-1]
    return img_bgr * (1 - a) + rgb * a
# Voix (son direct, extrait e) : « … un peuple à libérer, alors nous continuerons. Nous continuerons et nous ne lâcherons rien. »
# mots (tx/e/e.json, temps e) : une 13,22 / à défendre 13,90 / un peuple 15,18 / à libérer 15,78 / alors 17,34 / continuerons 17,88
#                               Nous 18,82 / continuerons 19,20 / et nous ne 19,92 / lâcherons 20,30 / rien 20,72-20,96
POSE_T0 = 15.13; V_IN, V_OUT = 15.15, 20.99
def tl(te): return te - POSE_T0
# Zone sûre TikTok : bloc centré <= 66 % de large (x 0,17-0,83 -> lignes <= 670 px, marge pour le contour et l'entrée à x1,02-1,03)
# et entre y 0,12 et 0,75 (230-1440 px) : le carton le plus haut (ET NOUS NE / LÂCHERONS / RIEN) finit vers y 1405.
TXT_W = 670
def cards():
    y0 = 1100
    def two(l1, l2, t1, t2, red2=False, big2=False):
        a1 = a2 = min(fit_size(l1, TXT_W, 200), fit_size(l2, TXT_W, 200))      # deux lignes de même taille
        return [(t1, l1, WHITE, a1, y0), (t2, l2, RED if red2 else WHITE, a2, y0 + a1 * 0.62 + a2 * 0.62)]
    lam = fit_size("LÂCHERONS", TXT_W, 230); rien = fit_size("RIEN", TXT_W, 190)
    return [
        (0.0,        two("UN PEUPLE", "À LIBÉRER", 0.0, tl(15.78))),
        (tl(17.34),  two("ALORS NOUS", "CONTINUERONS", tl(17.34), tl(17.88))),
        (tl(18.82),  two("NOUS", "CONTINUERONS", tl(18.82), tl(19.20))),
        (tl(19.92),  [(tl(19.92), "ET NOUS NE", WHITE, fit_size("ET NOUS NE", TXT_W, 230), y0 - 40),
                      (tl(20.30), "LÂCHERONS", WHITE, lam, y0 - 40 + lam * 1.15),
                      (tl(20.72), "RIEN", RED, rien, y0 - 40 + lam * 1.15 + lam * 0.55 + rien * 0.62)]),
    ]
CARDS = None
def pose_text(t):
    global CARDS
    if CARDS is None: CARDS = cards()
    cur = [c for c in CARDS if t >= c[0]][-1][1]
    out = None
    for (t1, txt, col, size, y) in cur:                                   # chaque ligne entre à son mot (3 images, sans rebond)
        if t < t1: continue
        e = ease_out(min((t - t1) * FPS / 3.0 + 1 / 3.0, 1.0))
        big = txt == "RIEN"
        lay = text_layer([(txt, col, size, y)], alpha_scale=min(1.0, 0.35 + e), scale=(1.15 - 0.15 * e) if big else (1.10 - 0.10 * e))
        if out is None: out = lay
        else:
            a = lay[..., 3:4]; o = out * (1 - a) + lay * a; o[..., 3:4] = np.maximum(out[..., 3:4], a); out = o
    return out
# ---------------- rendu ----------------
def write_mov(frames, path, fps=FPS):
    p = subprocess.Popen([FF, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", "%dx%d" % (W, H), "-r", str(fps), "-i", "-",
                          "-c:v", "prores_ks", "-profile:v", "3", "-pix_fmt", "yuv422p10le", "-vendor", "apl0", path], stdin=subprocess.PIPE)
    for f in frames: p.stdin.write(to8(f).tobytes())
    p.stdin.close(); p.wait()
def shot_len(sid):
    ts = cut_times()
    if sid == "pose": return fr(DROP)
    i = EDIT.index(sid); return fr(ts[i + 1]) - fr(ts[i])
def views_for(sid, n):
    sh = SHOTS[sid]; src = sh["src"]; s0 = int(round(sh["t"] * SRCFPS)); vh = sh.get("vh", 1080)
    z0, z1 = sh["zoom"]; zoom = lambda f: z0 + (z1 - z0) * f / max(n - 1, 1)
    if "fixed" in sh:
        return plan_views(src, s0, n, SRCFPS, speed=SRCFPS / FPS, bounds=BOUNDS, vh=vh, zoom=zoom, fixed=sh["fixed"])
    return plan_views(src, s0, n, SRCFPS, speed=SRCFPS / FPS, hint=sh["face"], bounds=BOUNDS, vh=vh, zoom=zoom, top=0.13)
def render_shot(sid):
    sh = SHOTS[sid]; n = shot_len(sid); raw, s0 = read_frames(sh["src"], sh["t"], n)
    views, ok = views_for(sid, n)
    if not ok and "fixed" not in sh: print("  ! pas de visage :", sid)
    frames = []
    for i, (img, (cx, cy, vh)) in enumerate(zip(raw, views)):
        g = grade(crop_916(img, cx, cy, vh))
        if sid == "pose":
            tx = pose_text(i / FPS)
            if tx is not None: g = over_rgba(g, tx)
        if sid == "dos" and i < 4: g = np.clip(g + (1 - i / 4) ** 2 * 0.35, 0, 1)      # flash blanc court sur le drop
        if sid == "fin":
            k = n - i
            if k <= 9: g = g * (k - 1) / 9                                          # fondu au noir final (0,3 s)
        frames.append(g)
    write_mov(frames, OUT + "V1_%s.mov" % sid)
    print("  plan", sid, n, "vue0", tuple(round(x) for x in views[0]), "vh fin", round(views[-1][2]))
# ---------------- plan ----------------
def build_plan():
    video = []; ts = cut_times()
    def add(id_, sid, rec, n, extra=None):
        sh = SHOTS[sid]
        v = {"id": id_, "clip": "V1_%s.mov" % sid, "folder": "genV1", "path": OUT + "V1_%s.mov" % sid, "s": 0, "e": n, "rec": rec, "dur": n,
             "clip_fps": FPS, "speed_pct": 100, "track": 1, "note": sh["why"],
             "source": {"fichier": "lot3/sources/" + sh["src"], "in_s": sh["t"], "out_s": round(sh["t"] + n / FPS, 3),
                        "url": YT, "t_youtube_s": round(OFFS[sh["src"]] + sh["t"], 2)}}
        if extra: v.update(extra)
        video.append(v)
    add("pose", "pose", 0, fr(DROP), {"texte": "UN PEUPLE / À LIBÉRER · ALORS NOUS / CONTINUERONS · NOUS / CONTINUERONS · ET NOUS NE / LÂCHERONS / RIEN (rouge)",
                                       "effets": "longue pose sans coupe 5,93 s en son direct (voix synchro), poussée lente 1,00 -> 1,08, N&B contrasté, grain, cartons cuits mot à mot"})
    for i, sid in enumerate(EDIT):
        a, b = fr(ts[i]), fr(ts[i + 1])
        add(sid, sid, a, b - a, {"temps": BEATS[i], "coupe_sur_t": round(ts[i], 3)})
    plan = {"name": "V1 - Longue pose N&B - Manon Aubry", "fps": FPS, "w": W, "h": H, "duree_s": END,
            "note": "Plans ProRes 9:16 recadrés, N&B, texte cuit (gen/V1/out). s/e en images du clip (30 i/s), rec en images timeline. "
                    "Aucun ralenti : speed_pct 100 partout. Coupes sur les kicks réels du drop (frappes.json). Générateur : lot3/_claude/gen/V1/genV1.py",
            "phrase": {"texte": "Tant qu'il y aura un enfant palestinien à sauver, une famille à protéger, une terre à défendre, un peuple à libérer, alors nous continuerons. Nous continuerons et nous ne lâcherons rien.",
                       "extrait_audible": "un peuple à libérer, alors nous continuerons. Nous continuerons et nous ne lâcherons rien.",
                       "url": YT, "source": "Manon Aubry, meeting « Justice pour la Palestine », Strasbourg, 17/06/2026 (chaîne Manon Aubry)",
                       "in_s": round(OFFS[SE] + V_IN, 2), "out_s": round(OFFS[SE] + V_OUT, 2), "voix": "son direct synchro sur la longue pose, musique qui monte dessous, refrain juste après"},
            "texte_style": {"police": "Arial Black", "couleur": "#FFFFFF, mot-clé RIEN #E4002B", "contour": "noir + ombre floue", "position": "centré, 1re ligne y ≈ 1100 (1060 pour le dernier carton), lignes ≤ 670 px : zone sûre TikTok x 0,17-0,83, y 0,12-0,75"},
            "musique": {"fichier": "lot3/sons/V1-stromae-sante.wav", "complet": "lot3/sons/V1-stromae-sante_complet.wav",
                        "debut_dans_complet_s": MOFF, "refrain_timeline_s": DROP, "paroles_audibles": "fin du couplet (« …vestes aux vestiaires / Arlette, arrête, toi la fête tu la passes aux toilettes ») sous la voix, puis refrain « Et si on célébrait ceux qui ne célèbrent pas / Pour une fois j'aimerais lever mon verre à ceux qui n'en ont pas »", "coupes_timeline_s": [round(x, 3) for x in ts]},
            "video": video,
            "audio": [{"id": "mix", "clip": "V1-mix.wav", "folder": "genV1", "path": OUT + "V1-mix.wav", "rec": 0, "track": 1,
                       "note": "voix + ambiance du meeting (son direct 15,15-20,99 s de l'extrait e) sur la longue pose ; Santé (Stromae) %.3f-%.3f s du clip officiel : couplet qui monte de -20 à -7 dB sous la voix, puis refrain plein à %.2f s (« Et si on célébrait… à ceux qui n'en ont pas »), -14 LUFS, fondu de fin 0,5 s" % (MOFF, MOFF + END, DROP)}]}
    json.dump(plan, open(D + "plan-V1.json", "w"), indent=1, ensure_ascii=False)
# ---------------- audio ----------------
def make_audio():
    import soundfile as sf
    sr = 48000; N = int(END * sr)
    cmd = [FF, "-v", "error", "-ss", "%.3f" % MOFF, "-t", "%.3f" % END, "-i", SONG, "-ac", "2", "-ar", str(sr), "-f", "f32le", "-"]
    mu = np.frombuffer(subprocess.run(cmd, capture_output=True).stdout, np.float32).reshape(-1, 2).copy()[:N]
    sf.write(L3 + "/sons/V1-stromae-sante.wav", mu, sr, subtype="PCM_24")
    t = np.arange(len(mu)) / sr; g = np.ones(len(mu), np.float32)
    g[t < 0.03] = t[t < 0.03] / 0.03; s = t > END - 0.5; g[s] *= (END - t[s]) / 0.5
    a0, a1 = tl(V_OUT), DROP - 0.02                                        # musique qui MONTE sous la phrase (-20 -> -7 dB), pleine au refrain
    gdb = np.where(t < a0, -20 + 13 * np.clip(t / a0, 0, 1) ** 1.5, np.where(t < a1, -7 + 7 * (t - a0) / (a1 - a0), 0.0))
    gd = (10 ** (gdb / 20)).astype(np.float32)
    mu *= (g * gd)[:, None]
    cmd = [FF, "-v", "error", "-ss", "%.3f" % V_IN, "-t", "%.3f" % (V_OUT - V_IN), "-i", L3 + "/sources/" + SE, "-ac", "2", "-ar", str(sr), "-f", "f32le", "-"]
    v = np.frombuffer(subprocess.run(cmd, capture_output=True).stdout, np.float32).reshape(-1, 2).copy()
    env = np.ones(len(v), np.float32); m = int(0.03 * sr); env[:m] = np.linspace(0, 1, m); m = int(0.04 * sr); env[-m:] = np.linspace(1, 0, m)
    voix = np.zeros_like(mu); i0 = int(tl(V_IN) * sr); voix[i0:i0 + len(v)] = (v * env[:, None])[:len(voix) - i0]
    voix *= 10 ** (7 / 20)
    sf.write(OUT + "V1-voix.wav", voix, sr, subtype="PCM_24"); sf.write(OUT + "V1-musique.wav", mu, sr, subtype="PCM_24")
    sf.write(D + "tmp_mix.wav", mu + voix, sr, subtype="FLOAT")
    r = subprocess.run([FF, "-hide_banner", "-i", D + "tmp_mix.wav", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    js = json.loads(r[r.rindex("{"):r.rindex("}") + 1])
    af = ("loudnorm=I=-14:TP=-1.5:LRA=11:measured_I=%s:measured_TP=%s:measured_LRA=%s:measured_thresh=%s:offset=%s:linear=true,aresample=48000"
          % (js["input_i"], js["input_tp"], js["input_lra"], js["input_thresh"], js["target_offset"]))
    subprocess.run([FF, "-v", "error", "-y", "-i", D + "tmp_mix.wav", "-af", af, "-c:a", "pcm_s24le", OUT + "V1-mix.wav"], check=True)
    os.remove(D + "tmp_mix.wav")
# ---------------- aperçu ffmpeg 540x960 ----------------
APERCU = HG + "/preview/apercu-V1.mp4"
def apercu():
    plan = json.load(open(D + "plan-V1.json")); ins = []; fl = []
    for i, v in enumerate(plan["video"]):
        ins += ["-i", OUT + v["clip"]]
        fl.append("[%d:v]trim=start_frame=%d:end_frame=%d,setpts=PTS-STARTPTS,scale=540:960,setsar=1[v%d]" % (i, v["s"], v["e"], i))
    k = len(plan["video"]); fl.append("".join("[v%d]" % i for i in range(k)) + "concat=n=%d:v=1:a=0[v]" % k)
    subprocess.run([FF, "-v", "error", "-y"] + ins + ["-i", OUT + "V1-mix.wav", "-filter_complex", ";".join(fl), "-map", "[v]", "-map", "%d:a" % k,
                    "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "aac", "-b:a", "192k", "-shortest", APERCU], check=True)
    print("aperçu", APERCU)
# ---------------- contrôle visages : tout visage > 5 % de la hauteur doit être entier ----------------
def check_faces():
    plan = json.load(open(D + "plan-V1.json")); bad = []
    for v in plan["video"]:
        d = "/private/tmp/claude-502/v1/chk_" + v["clip"]; shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
        subprocess.run([FF, "-v", "error", "-i", OUT + v["clip"], "-vf", "select='not(mod(n\\,2))',scale=540:960", "-fps_mode", "passthrough",
                        "-q:v", "3", d + "/f%04d.jpg"], check=True)
        subprocess.run([FACES, d], check=True, capture_output=True)
        js = json.load(open(d + "/faces.json")); nb = 0; nf = 0
        for k, fl in js.items():
            for x, y, w, h in fl:
                if h < 0.05: continue
                nf += 1
                top, bot, l, r = y - 0.3 * h, y + h * 1.05, x - 0.08 * w, x + w * 1.08
                if top < 0 or bot > 1 or l < 0 or r > 1: nb += 1; bad.append("%s %s (%.2f %.2f %.2f %.2f)" % (v["clip"], k, top, bot, l, r))
        print("  visages", v["clip"], "images", len(js), "visages>5%%", nf, "coupés", nb)
    print("TOTAL visages coupés :", len(bad)); print("\n".join(bad[:30]))
# ---------------- mesure : coupes de l'export vs frappes ----------------
def mesure():
    w, h = 180, 320
    raw = subprocess.run([FF, "-v", "error", "-i", APERCU, "-vf", "scale=%d:%d,format=gray" % (w, h), "-f", "rawvideo", "-"], capture_output=True).stdout
    frm = np.frombuffer(raw, np.uint8).reshape(-1, h, w).astype(np.float32)
    d = np.abs(np.diff(frm, axis=0)).mean(axis=(1, 2)); med = np.median(d)
    cuts = [i + 1 for i in range(len(d)) if d[i] > max(5 * med, 8) and d[i] == d[max(i - 2, 0):i + 3].max()]
    ref = K; errs = []
    for c in cuts:
        t = c / FPS
        if t < DROP - 0.1: print("  (changement de carton %.3f s, pas une coupe)" % t); continue
        k = min(ref, key=lambda x: abs(x - t)); errs.append(t - k)
        print("  coupe %6.3f s (img %3d) -> frappe %6.3f : %+4.0f ms" % (t, c, k, (t - k) * 1000))
    print("images", len(frm), "coupes", len(cuts), "écart max %.0f ms" % (max(abs(e) for e in errs) * 1000 if errs else 0))
    r = subprocess.run([FF, "-hide_banner", "-i", APERCU, "-af", "loudnorm=I=-14:TP=-1:print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
    js = json.loads(r[r.rindex("{"):r.rindex("}") + 1]); print("export : %s LUFS, TP %s dBTP" % (js["input_i"], js["input_tp"]))
if __name__ == "__main__":
    args = set(a for a in sys.argv[1:] if "=" not in a) or {"shots", "plan", "audio", "apercu", "check", "mesure"}
    only = [a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("only=")]
    if "shots" in args or only:
        for sid in (only or ["pose"] + EDIT): render_shot(sid)
    if "plan" in args: build_plan()
    if "audio" in args: make_audio()
    if "apercu" in args: apercu()
    if "check" in args: check_faces()
    if "mesure" in args: mesure()
