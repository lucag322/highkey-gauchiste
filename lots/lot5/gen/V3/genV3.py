# Lot 5 — V3 Longue pose N&B (inspi nobleactually, Bernie ; modèles lot3 V1 et lot4 V2) : David Guiraud, meeting de Roubaix 31/01/2026
# (chaîne Jean-Luc Mélenchon, fin du discours de Guiraud), son Michael Jackson – Bad (clip officiel, chaîne Michael Jackson).
# Recette : une longue pose de 7,2 s SANS coupe en son direct (« préparez-vous à quelques nuits blanches. Car si vous nous empêchez de rêver,
# nous, on vous empêchera de dormir. »), la musique monte dessous (fin du pré-refrain « …just wait 'til I get through »), puis le refrain
# « Because I'm BAD » tombe juste après « dormir » avec l'ovation de la salle ; coupes sur les vraies frappes (3, 2, 2 temps puis 1 temps x5, fin 2 temps).
# N&B très contrasté + grain. Texte (DA) : phrase réelle mot à mot, Arial Black, contour noir, RÊVER / DORMIR en rouge, sans guillemets.
# Règles : 15 s max, 9:16 plein écran, aucun visage coupé, plans >= 1 temps, pas de dézoom, aucun ralenti précalculé, -14 LUFS.
# Autre edit de Guiraud : A4 (lot 2) = « alors cette population devient invincible… » (YouTube 1688-1694 s) et plans des extraits
# meeting-a/b/c (YouTube 1310-1890 s) + 1er tour. V3 = autre phrase (YouTube 3061-3068 s) et plans neufs (YouTube 2898-3093 s, lot5/sources).
# Usage : python genV3.py [shots] [plan] [audio] [apercu] [check] [mesure]   (sans argument = tout) | only=<id>
import sys, os, json, subprocess, shutil
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
HG = "/Users/luca.grousset/Movies/highkey-gauchiste"; L5 = HG + "/lot5"
sys.path.insert(0, HG + "/_claude/outils")
from fx import vignette, to8, ease_out
import framing
D = L5 + "/_claude/gen/V3/"; OUT = D + "out/"; os.makedirs(OUT, exist_ok=True)
framing.ROOT = L5; framing.CACHE = D + "cache/faces"                      # sources du lot 5, cache visages dans gen/V3
from framing import plan_views
FF = "/opt/homebrew/bin/ffmpeg"; FACES = HG + "/_claude/outils/faces"; FPS = 30; W, H = 1080, 1920
TMP = "/private/tmp/claude-502/-Users-luca-grousset-Documents-GitHub-perso/a34e79cf-b36f-4413-8b7e-459475c5f14e/scratchpad/V3"
RED = (0xE4, 0x00, 0x2B); WHITE = (255, 255, 255)
F_BLACK = "/System/Library/Fonts/Supplemental/Arial Black.ttf"
RV, FN = "V3-guiraud-roubaix-reves.mp4", "V3-guiraud-roubaix-final.mp4"
YT = {RV: ("o-1R3UFtXiQ", 3040.0), FN: ("o-1R3UFtXiQ", 2895.0)}           # chaîne JEAN-LUC MÉLENCHON, meeting Roubaix 31/01/2026
SRCFPS = 30
B_POD = (0, 0, 1670, 740)          # plans au pupitre : texte du pupitre « MEETING ROUBAIX 31 JANVIER 2026 » (y > 745) et logo LFI (x > 1680, y < 150) exclus
B_ALL = (0, 0, 1670, 1080)         # plans de salle : logo LFI en haut à droite exclu
# ---------------- son : Bad (clip officiel). Fin du pré-refrain qui monte sous la phrase, puis le REFRAIN « Because I'm BAD » ----------------
SONG = L5 + "/sons/V3-mj-bad_complet.wav"
HITS = json.load(open(D + "frappes.json"))
MOFF = HITS["MOFF"]; DROP = HITS["drop_t"]; K = [t for t in HITS["temps_t"] if t >= DROP - 1e-3]
def fr(t): return int(round(t * FPS))
# ---------------- plans ----------------
SHOTS = {
    "pose":      dict(src=RV, t=21.00, face=(930, 250), b=B_POD, zoom=(1.0, 1.08), why="longue pose en son direct : « préparez-vous à quelques nuits blanches… on vous empêchera de dormir. »"),
    "foule":     dict(src=RV, t=31.0, fixed=(800, 540), vh=1080, b=B_ALL, zoom=(1.0, 1.04), why="la salle se lève juste après la phrase (ovation, entrée du refrain)"),
    "sourire":   dict(src=RV, t=45.0, face=(1064, 150), b=B_POD, zoom=(1.0, 1.04), why="Guiraud sous l'ovation"),
    "drapeaux":  dict(src=RV, t=38.5, fixed=(1360, 540), vh=1080, b=B_ALL, zoom=(1.0, 1.04), why="drapeaux LFI agités dans la salle"),
    "profil":    dict(src=FN, t=3.0, face=(883, 261), b=B_POD, zoom=(1.0, 1.03), why="profil au pupitre (autre caméra)"),
    "geste":     dict(src=FN, t=30.5, face=(979, 184), b=B_POD, zoom=(1.0, 1.03), why="main ouverte, il argumente"),
    "foule2":    dict(src=FN, t=66.0, fixed=(640, 540), vh=1080, b=B_ALL, zoom=(1.0, 1.03), why="salle comble qui applaudit"),
    "lunettes":  dict(src=FN, t=42.0, face=(1018, 204), b=B_POD, vh=600, zoom=(1.0, 1.03), why="gros plan, main aux lunettes"),
    "drapeaux2": dict(src=RV, t=41.0, fixed=(1100, 540), vh=1080, b=B_ALL, zoom=(1.0, 1.03), why="mer de drapeaux, salle debout"),
    "fin":       dict(src=RV, t=52.5, face=(1056, 188), b=B_POD, zoom=(1.02, 1.08), why="fin, il sourit à la salle"),
}
# après le refrain : 3, 2, 2 temps, puis 1 temps x5 (accélération comme la réf), dernier plan 2 temps jusqu'à la fin (14 temps)
EDIT = ["foule", "sourire", "drapeaux", "profil", "geste", "foule2", "lunettes", "drapeaux2", "fin"]
BEATS = [3, 2, 2, 1, 1, 1, 1, 1, 2]
END = K[sum(BEATS)]                                                         # 15e frappe depuis le drop (≈ 14,6 s)
def cut_times():
    ts = [DROP]; k = 0
    for b in BEATS[:-1]: k += b; ts.append(K[k])
    return ts + [END]
# ---------------- look : N&B très contrasté (lift bas, gain haut), grain fin ----------------
RNG = np.random.default_rng(5)
def grade(bgr):
    g = 0.12 * bgr[..., 0] + 0.48 * bgr[..., 1] + 0.40 * bgr[..., 2]         # fond bleu de la scène qui descend, visage lisible
    g = np.clip((g - 0.03) / 0.80, 0, 1)
    g = np.power(g, 0.82)
    g = 0.35 * g + 0.65 * (g * g * (3 - 2 * g))                             # courbe en S forte
    small = cv2.resize(g, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    hi = np.clip(small - 0.6, 0, None) * 2.0
    g = g + cv2.resize(cv2.GaussianBlur(hi, (0, 0), 8), (W, H)) * 0.30      # léger halo des hautes lumières
    g = vignette(g[..., None], 0.42, 2.2)[..., 0]
    g = 0.039 + np.clip(g, 0, 1) * (0.91 - 0.039)                            # noirs #0A0A0A, blancs #E8E8E8 (réf)
    n = cv2.resize(RNG.normal(0, 1, (H // 2, W // 2)).astype(np.float32), (W, H))
    g = g + n * 0.03
    return np.repeat(np.clip(g, 0, 1)[..., None], 3, 2)
def read_frames(src, t, n_out):
    cap = cv2.VideoCapture(L5 + "/sources/" + src)
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
        ds.text((x, y + sz * 0.05), txt, font=f, fill=(0, 0, 0, 225), stroke_width=sw * 5, stroke_fill=(0, 0, 0, 225))
        d.text((x, y), txt, font=f, fill=col + (255,), stroke_width=sw, stroke_fill=(0, 0, 0, 255))
    sh = sh.filter(ImageFilter.GaussianBlur(22))
    a = np.asarray(Image.alpha_composite(sh, lay)).astype(np.float32) / 255
    a[..., 3] *= alpha_scale
    return a
def over_rgba(img_bgr, rgba):
    a = rgba[..., 3:4]; rgb = rgba[..., 2::-1]
    return img_bgr * (1 - a) + rgb * a
# Voix (son direct, extrait « reves » = YouTube 3040 s + t) : « préparez-vous à quelques nuits blanches. Car si vous nous empêchez de rêver,
# nous, on vous empêchera de dormir. » Le plan commence à 21,00 s ; attaques mesurées sur l'énergie de la voix (temps timeline) :
# préparez 0,23 / à quelques 0,74 / nuits 0,90 / blanches 1,08 / car 2,08 / si vous nous 3,44 / empêchez 3,80 / de rêver 4,20-4,60 /
# nous 5,16 / on vous 6,12 / empêchera 6,40 / de dormir 6,70-7,05. La salle explose à 7,45 (ovation gardée sous le refrain, en fondu).
# Phrase précédente (« À tous ceux qui veulent nous empêcher d'évoluer, de progresser, de nous émanciper, ») non gardée : 15 s max.
POSE_T0 = 21.00; V_IN, V_OUT, V_TAIL = 21.05, 28.17, 29.80
# Zone sûre TikTok : bloc <= 66 % de large, centré (x 0,17-0,83) ; y entre 0,12 et 0,75 (230-1440 px). Bloc ancré par le BAS à 1420 px.
Y_BOT = 1420; M_TXT, M_BIG = 640, 640
def stack(items, gap=0.18):
    out = []; y = 0.0
    for i, (t, txt, col, size) in enumerate(items):
        if i: y += out[-1][3] * (0.5 + gap) + size * 0.5
        out.append([t, txt, col, size, y])
    shift = Y_BOT - (out[-1][4] + out[-1][3] * 0.5)
    return [(t, txt, col, size, y + shift) for t, txt, col, size, y in out]
def cards():
    M = M_TXT
    s1 = min(fit_size("PRÉPAREZ-VOUS", M, 160), fit_size("À QUELQUES", M, 160))
    nb = fit_size("NUITS BLANCHES", M, 200)
    s2 = min(fit_size("SI VOUS NOUS", M, 160), fit_size("EMPÊCHEZ", M, 160))
    rv = fit_size("DE RÊVER", M_BIG, 240)
    s3 = min(fit_size("ON VOUS", M, 160), fit_size("EMPÊCHERA", M, 160))
    dm = fit_size("DE DORMIR", M_BIG, 240)
    return [
        (0.23, stack([(0.23, "PRÉPAREZ-VOUS", WHITE, s1), (0.74, "À QUELQUES", WHITE, s1), (0.90, "NUITS BLANCHES", WHITE, nb)])),
        (2.08, stack([(2.08, "CAR", WHITE, fit_size("CAR", M, 150)), (3.44, "SI VOUS NOUS", WHITE, s2), (3.80, "EMPÊCHEZ", WHITE, s2), (4.20, "DE RÊVER", RED, rv)])),
        (5.16, stack([(5.16, "NOUS", WHITE, fit_size("NOUS", M, 150)), (6.12, "ON VOUS", WHITE, s3), (6.40, "EMPÊCHERA", WHITE, s3), (6.70, "DE DORMIR", RED, dm)])),
    ]
CARDS = None
def pose_text(t):
    global CARDS
    if CARDS is None: CARDS = cards()
    cur = [c for c in CARDS if t >= c[0]]
    if not cur: return None
    out = None
    for (t1, txt, col, size, y) in cur[-1][1]:                              # chaque ligne entre à son mot (3 images, sans rebond)
        if t < t1: continue
        e = ease_out(min((t - t1) * FPS / 3.0 + 1 / 3.0, 1.0))
        big = col == RED
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
    sh = SHOTS[sid]; src = sh["src"]; s0 = int(round(sh["t"] * SRCFPS)); b = sh["b"]; vh = sh.get("vh", b[3] - b[1])
    z0, z1 = sh["zoom"]; zoom = lambda f: z0 + (z1 - z0) * f / max(n - 1, 1)
    if "fixed" in sh:
        return plan_views(src, s0, n, SRCFPS, speed=1.0, bounds=b, vh=vh, zoom=zoom, fixed=sh["fixed"])
    return plan_views(src, s0, n, SRCFPS, speed=1.0, hint=sh["face"], bounds=b, vh=vh, zoom=zoom, top=0.13)
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
        if sid == EDIT[0] and i < 4: g = np.clip(g + (1 - i / 4) ** 2 * 0.35, 0, 1)      # flash blanc court sur le drop
        if sid == "fin":
            k = n - i
            if k <= 9: g = g * (k - 1) / 9                                          # fondu au noir final (0,3 s)
        frames.append(g)
    write_mov(frames, OUT + "V3_%s.mov" % sid)
    print("  plan", sid, n, "vue0", tuple(round(x) for x in views[0]), "vh fin", round(views[-1][2]))
# ---------------- plan ----------------
def yt_url(src): return "https://www.youtube.com/watch?v=" + YT[src][0]
PHRASE = "À tous ceux qui veulent nous empêcher d'évoluer, de progresser, de nous émanciper, préparez-vous à quelques nuits blanches. Car si vous nous empêchez de rêver, nous, on vous empêchera de dormir."
AUDIBLE = "préparez-vous à quelques nuits blanches. Car si vous nous empêchez de rêver, nous, on vous empêchera de dormir."
PAROLES = ("sous la voix (bas, qui monte) : « …and to me that's really true / And my friend you have seen nothing / Just wait 'til I get through » ; "
           "refrain plein : « Because I'm bad, I'm bad (shamone) / You know I'm bad, I'm bad (you know it) / You know it, you know… »")
TEXTE = "PRÉPAREZ-VOUS / À QUELQUES / NUITS BLANCHES · CAR / SI VOUS NOUS / EMPÊCHEZ / DE RÊVER (rouge) · NOUS / ON VOUS / EMPÊCHERA / DE DORMIR (rouge) (zone sûre TikTok : x 0,17-0,83, bas du bloc y 1420)"
def build_plan():
    video = []; ts = cut_times()
    def add(id_, sid, rec, n, extra=None):
        sh = SHOTS[sid]
        v = {"id": id_, "clip": "V3_%s.mov" % sid, "folder": "genV3", "path": OUT + "V3_%s.mov" % sid, "s": 0, "e": n, "rec": rec, "dur": n,
             "clip_fps": FPS, "speed_pct": 100, "track": 1, "note": sh["why"],
             "source": {"fichier": "lot5/sources/" + sh["src"], "in_s": sh["t"], "out_s": round(sh["t"] + n / FPS, 3),
                        "url": yt_url(sh["src"]), "t_youtube_s": round(YT[sh["src"]][1] + sh["t"], 2)}}
        if extra: v.update(extra)
        video.append(v)
    add("pose", "pose", 0, fr(DROP), {"texte": TEXTE, "effets": "longue pose sans coupe %.2f s en son direct (voix synchro), poussée lente 1,00 -> 1,08, N&B contrasté, grain, cartons cuits mot à mot" % DROP})
    for i, sid in enumerate(EDIT):
        a, b = fr(ts[i]), fr(ts[i + 1])
        add(sid, sid, a, b - a, {"temps": BEATS[i], "coupe_sur_t": round(ts[i], 3)})
    plan = {"name": "V3 - Longue pose N&B - David Guiraud", "fps": FPS, "w": W, "h": H, "duree_s": round(END, 3),
            "note": "Plans ProRes 9:16 recadrés, N&B, texte cuit (gen/V3/out). s/e en images du clip (30 i/s), rec en images timeline. "
                    "Aucun ralenti : speed_pct 100 partout. Coupes sur les frappes réelles du refrain (frappes.json). Générateur : lot5/_claude/gen/V3/genV3.py",
            "phrase": {"texte": PHRASE, "extrait_audible": AUDIBLE, "url": yt_url(RV),
                       "source": "David Guiraud, meeting de Roubaix du 31/01/2026, conclusion de son discours (chaîne JEAN-LUC MÉLENCHON, « Meeting avec Jean-Luc Mélenchon, David Guiraud et Shéhérazade Bentorki à Roubaix ! »)",
                       "in_s": round(YT[RV][1] + V_IN, 2), "out_s": round(YT[RV][1] + V_OUT, 2), "voix": "son direct synchro sur la longue pose, musique qui monte dessous, refrain juste après « dormir », ovation de la salle en fondu sous le refrain"},
            "texte_style": {"police": "Arial Black", "couleur": "#FFFFFF, mots-clés DE RÊVER / DE DORMIR #E4002B", "contour": "noir + ombre floue", "position": "centré, largeur <= 640 px, bas du bloc à y 1420 (zone sûre TikTok)"},
            "musique": {"fichier": "lot5/sons/V3-mj-bad.wav", "complet": "lot5/sons/V3-mj-bad_complet.wav",
                        "debut_dans_complet_s": MOFF, "refrain_timeline_s": DROP, "coupes_timeline_s": [round(x, 3) for x in ts], "paroles_audibles": PAROLES},
            "video": video,
            "audio": [{"id": "mix", "clip": "V3-mix.wav", "folder": "genV3", "path": OUT + "V3-mix.wav", "rec": 0, "track": 1,
                       "note": "voix + salle (son direct %.2f-%.2f s de l'extrait reves, ovation en fondu jusqu'à %.2f s) sur la longue pose ; Bad %.3f-%.3f s du clip officiel : fin du pré-refrain qui monte de -20 à -7 dB sous la voix, puis refrain plein à %.3f s, -14 LUFS, fondu de fin 0,5 s" % (V_IN, V_OUT, V_TAIL, MOFF, MOFF + END, DROP)}]}
    json.dump(plan, open(D + "plan-V3.json", "w"), indent=1, ensure_ascii=False)
    son = {"titre": "Bad", "artiste": "Michael Jackson", "url": "https://www.youtube.com/watch?v=dsUXAEzaC3Q", "chaine": "Michael Jackson (chaîne officielle certifiée, « Michael Jackson - Bad (Shortened Version) »)",
           "fichier_complet": "lot5/sons/V3-mj-bad_complet.wav", "fichier_extrait": "lot5/sons/V3-mj-bad.wav",
           "extrait_debut_s": MOFF, "extrait_fin_s": round(MOFF + END, 3), "bpm": round(60 / HITS["beat_s"], 1),
           "drop_morceau_s": round(MOFF + DROP, 3), "drop_timeline_s": DROP, "paroles_audibles": PAROLES,
           "frappes_coupes_timeline_s": [round(x, 3) for x in ts], "frappes_temps_timeline_s": K, "note": "frappes détaillées dans frappes.json (frappes.py)"}
    json.dump(son, open(D + "son.json", "w"), indent=1, ensure_ascii=False)
# ---------------- audio ----------------
def make_audio():
    import soundfile as sf
    sr = 48000; N = int(END * sr)
    cmd = [FF, "-v", "error", "-ss", "%.3f" % MOFF, "-t", "%.3f" % END, "-i", SONG, "-ac", "2", "-ar", str(sr), "-f", "f32le", "-"]
    mu = np.frombuffer(subprocess.run(cmd, capture_output=True).stdout, np.float32).reshape(-1, 2).copy()[:N]
    sf.write(L5 + "/sons/V3-mj-bad.wav", mu, sr, subtype="PCM_24")
    t = np.arange(len(mu)) / sr; g = np.ones(len(mu), np.float32)
    g[t < 0.03] = t[t < 0.03] / 0.03; s = t > END - 0.5; g[s] *= (END - t[s]) / 0.5
    a0, a1 = 7.05 - 0.2, DROP - 0.02                                         # musique qui MONTE sous la phrase (-20 -> -7 dB), pleine au refrain
    gdb = np.where(t < a0, -20 + 13 * np.clip(t / a0, 0, 1) ** 1.5, np.where(t < a1, -7 + 7 * (t - a0) / (a1 - a0), 0.0))
    mu *= (g * (10 ** (gdb / 20)).astype(np.float32))[:, None]
    cmd = [FF, "-v", "error", "-ss", "%.3f" % V_IN, "-t", "%.3f" % (V_TAIL - V_IN), "-i", L5 + "/sources/" + RV, "-ac", "2", "-ar", str(sr), "-f", "f32le", "-"]
    v = np.frombuffer(subprocess.run(cmd, capture_output=True).stdout, np.float32).reshape(-1, 2).copy()
    tv = np.arange(len(v)) / sr + V_IN
    env = np.ones(len(v), np.float32); m = int(0.02 * sr); env[:m] = np.linspace(0, 1, m)
    tail = tv > V_OUT; env[tail] = 0.35 * np.clip((V_TAIL - tv[tail]) / (V_TAIL - V_OUT), 0, 1)   # ovation de la salle, en fondu sous le refrain
    voix = np.zeros_like(mu); i0 = max(int((V_IN - POSE_T0) * sr), 0); voix[i0:i0 + len(v)] = (v * env[:, None])[:len(voix) - i0]
    voix *= 10 ** (16 / 20)                                                 # son du meeting plus faible que LCI (V2) : voix ≈ 7 dB au-dessus de la musique
    sf.write(OUT + "V3-voix.wav", voix, sr, subtype="FLOAT"); sf.write(OUT + "V3-musique.wav", mu, sr, subtype="FLOAT")   # float : pas d écrêtage des stems
    sf.write(D + "tmp_mix.wav", mu + voix, sr, subtype="FLOAT")
    r = subprocess.run([FF, "-hide_banner", "-i", D + "tmp_mix.wav", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    js = json.loads(r[r.rindex("{"):r.rindex("}") + 1])
    af = ("loudnorm=I=-14:TP=-1.5:LRA=11:measured_I=%s:measured_TP=%s:measured_LRA=%s:measured_thresh=%s:offset=%s:linear=true,aresample=48000"
          % (js["input_i"], js["input_tp"], js["input_lra"], js["input_thresh"], js["target_offset"]))
    subprocess.run([FF, "-v", "error", "-y", "-i", D + "tmp_mix.wav", "-af", af, "-c:a", "pcm_s24le", OUT + "V3-mix.wav"], check=True)
    os.remove(D + "tmp_mix.wav")
# ---------------- aperçu ffmpeg 540x960 ----------------
APERCU = HG + "/preview/apercu-V3.mp4"
def apercu():
    plan = json.load(open(D + "plan-V3.json")); ins = []; fl = []
    for i, v in enumerate(plan["video"]):
        ins += ["-i", OUT + v["clip"]]
        fl.append("[%d:v]trim=start_frame=%d:end_frame=%d,setpts=PTS-STARTPTS,scale=540:960,setsar=1[v%d]" % (i, v["s"], v["e"], i))
    k = len(plan["video"]); fl.append("".join("[v%d]" % i for i in range(k)) + "concat=n=%d:v=1:a=0[v]" % k)
    subprocess.run([FF, "-v", "error", "-y"] + ins + ["-i", OUT + "V3-mix.wav", "-filter_complex", ";".join(fl), "-map", "[v]", "-map", "%d:a" % k,
                    "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "aac", "-b:a", "192k", "-shortest", APERCU], check=True)
    print("aperçu", APERCU)
# ---------------- contrôle visages : tout visage > 5 % de la hauteur doit être entier ----------------
def check_faces():
    plan = json.load(open(D + "plan-V3.json")); bad = []
    for v in plan["video"]:
        d = TMP + "/chk_" + v["clip"]; shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
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
    errs = []
    for c in cuts:
        t = c / FPS
        if t < DROP - 0.1: print("  (changement de carton %.3f s, pas une coupe)" % t); continue
        k = min(K, key=lambda x: abs(x - t)); errs.append(t - k)
        print("  coupe %6.3f s (img %3d) -> frappe %6.3f : %+4.0f ms" % (t, c, k, (t - k) * 1000))
    print("images", len(frm), "durée %.3f s" % (len(frm) / FPS), "coupes", len(cuts), "écart max %.0f ms" % (max(abs(e) for e in errs) * 1000 if errs else 0))
    r = subprocess.run([FF, "-hide_banner", "-i", APERCU, "-af", "loudnorm=I=-14:TP=-1:print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
    js = json.loads(r[r.rindex("{"):r.rindex("}") + 1]); print("export : %s LUFS, TP %s dBTP" % (js["input_i"], js["input_tp"]))
if __name__ == "__main__":
    args = set(a for a in sys.argv[1:] if "=" not in a) or {"shots", "plan", "audio", "apercu", "check", "mesure"}
    only = [x for a in sys.argv[1:] if a.startswith("only=") for x in a.split("=", 1)[1].split(",")]
    if "shots" in args or only:
        for sid in (only or ["pose"] + EDIT): render_shot(sid)
    if "plan" in args: build_plan()
    if "audio" in args: make_audio()
    if "apercu" in args: apercu()
    if "check" in args: check_faces()
    if "mesure" in args: mesure()
