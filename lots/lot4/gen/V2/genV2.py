# Lot 4 — V2 Longue pose N&B (inspi nobleactually, Bernie ; modèle lot3/_claude/gen/V1) : Danièle Obono, LCI 24/09/2026 + BFMTV 04/09/2026,
# son Michael Jackson – Beat It (clip officiel). Recette : une longue pose de 7,2 s SANS coupe en son direct (tension), puis le refrain
# « Just beat it » tombe et les coupes s'enchaînent sur les vraies frappes en accélérant (2 temps x5, puis 1 temps x4, fin 3 temps).
# N&B très contrasté (noirs bas, blancs hauts) + grain, plan large du plateau (Obono de dos face au studio) = entrée du drop.
# Texte (DA) : phrase réelle d'Obono mot à mot, Arial Black, contour noir, mots-clés JUSTICE SOCIALE en rouge, sans guillemets.
# Règles : 15 s max, 9:16 plein écran, aucun visage coupé, plans >= 1 temps, pas de dézoom, aucun ralenti précalculé, -14 LUFS.
# Phrase et plans différents de G4 (lot 3, même figure) : G4 = LCI-a 1540 s « Ce que les gens ne supportent pas… ».
# Usage : python genV2.py [shots] [plan] [audio] [apercu] [check] [mesure]   (sans argument = tout) | only=<id>
import sys, os, json, subprocess, shutil
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
HG = "/Users/luca.grousset/Movies/highkey-gauchiste"; L3 = HG + "/lot3"; L4 = HG + "/lot4"
sys.path.insert(0, HG + "/_claude/outils")
from fx import vignette, to8, ease_out
import framing
D = L4 + "/_claude/gen/V2/"; OUT = D + "out/"; os.makedirs(OUT, exist_ok=True)
framing.ROOT = L3; framing.CACHE = D + "cache/faces"                      # sources du lot 3 (lecture seule), cache visages dans gen/V2
from framing import plan_views
FF = "/opt/homebrew/bin/ffmpeg"; FACES = HG + "/_claude/outils/faces"; FPS = 30; W, H = 1080, 1920
TMP = "/private/tmp/claude-502/-Users-luca-grousset-Documents-GitHub-perso/a34e79cf-b36f-4413-8b7e-459475c5f14e/scratchpad/V2"
RED = (0xE4, 0x00, 0x2B); WHITE = (255, 255, 255)
F_BLACK = "/System/Library/Fonts/Supplemental/Arial Black.ttf"
LA, LB, BF = "G4-obono-lci-2026-09-24-a.mp4", "G4-obono-lci-2026-09-24-b.mp4", "G4-obono-bfmtv-2026-09-04.mp4"
YT = {LA: ("wn6qL6YseFY", 1400.0), LB: ("wn6qL6YseFY", 870.0), BF: ("XDCpNQsFZWc", 1500.0)}   # chaîne officielle D. Obono
SRCFPS = 30
B_LCI = (0, 0, 1560, 765)          # LCI : logo + heure en haut à droite (x > 1580) et bandeau nom / titre (y > 775) exclus
B_BFM = (300, 0, 1920, 815)        # BFMTV : logo en haut à gauche (x < 280) et bandeau rouge (y > 830) exclus
# ---------------- son : Beat It (clip officiel). Fin du couplet qui monte sous la phrase, puis le REFRAIN tombe juste après « appliquée » ----------------
SONG = L4 + "/sons/V2-mj-beat-it_complet.wav"
HITS = json.load(open(D + "frappes.json"))
MOFF = HITS["MOFF"]; DROP = HITS["drop_t"]; K = [t for t in HITS["temps_t"] if t >= DROP - 1e-3]
def fr(t): return int(round(t * FPS))
# ---------------- plans ----------------
SHOTS = {
    "pose":    dict(src=LB, t=138.20, face=(1000, 300), b=B_LCI, zoom=(1.0, 1.08), why="longue pose en son direct : « c'est de la responsabilité des politiques… mise en place et appliquée. »"),
    "plateau": dict(src=LB, t=149.0, fixed=(1150, 385), vh=770, b=B_LCI, zoom=(1.0, 1.04), why="plateau large, Obono de dos face au studio (entrée du drop)"),
    "gros":    dict(src=LA, t=96.5, face=(960, 330), b=B_LCI, zoom=(1.0, 1.04), why="plan poitrine, regard vif"),
    "mains":   dict(src=LA, t=107.0, face=(980, 320), b=B_LCI, zoom=(1.0, 1.04), why="mains ouvertes, elle argumente"),
    "bfm":     dict(src=BF, t=132.4, face=(1100, 300), b=B_BFM, zoom=(1.02, 1.06), why="BFMTV, gros plan veste jaune"),
    "regard":  dict(src=LB, t=51.0, face=(960, 330), b=B_LCI, zoom=(1.0, 1.04), why="elle fixe son contradicteur"),
    "face":    dict(src=LA, t=12.0, face=(1000, 300), b=B_LCI, zoom=(1.02, 1.05), why="face caméra"),
    "ots":     dict(src=BF, t=20.0, face=(1400, 330), b=(300, 136, 1920, 770), zoom=(1.0, 1.03), why="BFMTV, elle argumente face à Jad Zahab"),
    "geste":   dict(src=LA, t=133.0, face=(980, 300), b=B_LCI, zoom=(1.02, 1.05), why="main sur le cœur"),
    "voix":    dict(src=LB, t=61.6, face=(1000, 300), b=B_LCI, zoom=(1.02, 1.05), why="elle parle, voix forte"),
    "fin":     dict(src=LB, t=116.0, face=(1000, 300), b=B_LCI, zoom=(1.02, 1.07), why="fin, regard caméra"),
}
# après le refrain : 2 temps x5, puis 1 temps x4 (accélération comme la réf), dernier plan 3 temps jusqu'à la fin
EDIT = ["plateau", "gros", "mains", "bfm", "regard", "face", "ots", "geste", "voix", "fin"]
BEATS = [2, 2, 2, 2, 2, 1, 1, 1, 1, 3]
END = K[sum(BEATS)]                                                         # 17e temps après le drop (≈ 14,59 s)
def cut_times():
    ts = [DROP]; k = 0
    for b in BEATS[:-1]: k += b; ts.append(K[k])
    return ts + [END]
# ---------------- look : N&B très contrasté (lift bas, gain haut), grain fin ----------------
RNG = np.random.default_rng(4)
def grade(bgr):
    # plateau bleu, peau foncée : mélange N&B orienté rouge/vert (le fond bleu descend, le visage reste lisible)
    g = 0.12 * bgr[..., 0] + 0.48 * bgr[..., 1] + 0.40 * bgr[..., 2]
    g = np.clip((g - 0.04) / 0.82, 0, 1)
    g = np.power(g, 0.85)                                                   # remonte un peu les tons moyens (visages)
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
        ds.text((x, y + sz * 0.05), txt, font=f, fill=(0, 0, 0, 225), stroke_width=sw * 5, stroke_fill=(0, 0, 0, 225))   # ombre plus large : le motif de la veste ne colle plus au texte
        d.text((x, y), txt, font=f, fill=col + (255,), stroke_width=sw, stroke_fill=(0, 0, 0, 255))
    sh = sh.filter(ImageFilter.GaussianBlur(22))
    a = np.asarray(Image.alpha_composite(sh, lay)).astype(np.float32) / 255
    a[..., 3] *= alpha_scale
    return a
def over_rgba(img_bgr, rgba):
    a = rgba[..., 3:4]; rgb = rgba[..., 2::-1]
    return img_bgr * (1 - a) + rgb * a
# Voix (son direct, LCI-b) : « [Et je crois que] c'est de la responsabilité des politiques, c'est notre rôle, sinon à quoi on sert ?
# De faire en sorte que la justice sociale soit mise en place et appliquée. »  Le plan commence à 138,20 s (sur « c'est ») :
# « Et je crois que » (137,78-138,14) est sur le plan précédent (journaliste), il n'est pas gardé.
# mots (re-transcrits depuis 138,20, temps timeline) : responsabilité 0,24 / des politiques 0,72 / c'est notre rôle 1,30-1,78 /
# sinon 1,96 / à quoi on sert 2,26-3,06 / de faire en sorte 3,06-3,86 / que la 3,86 / justice 4,70 / sociale 4,94 / soit mise 5,40 /
# en place 6,04 / et appliquée 6,40-7,08
POSE_T0 = 138.20; V_IN, V_OUT = 138.17, 145.29
# Zone sûre TikTok (retour Luca) : bloc <= 66 % de large, centré (x 0,17-0,83) ; y entre 0,12 et 0,75 (230-1440 px).
# Bloc ancré par le BAS à 1370 px ; largeur max 580 px (lignes blanches, entrée x1,10) / 580 px (mots grossis, entrée x1,15) -> < 712 px.
Y_BOT = 1370; M_TXT, M_BIG = 580, 580
def stack(items, gap=0.18):
    """items = [(t, txt, col, size)] -> lignes centrées, empilées, bas du bloc à Y_BOT."""
    out = []; y = 0.0
    for i, (t, txt, col, size) in enumerate(items):
        if i: y += out[-1][3] * (0.5 + gap) + size * 0.5
        out.append([t, txt, col, size, y])
    shift = Y_BOT - (out[-1][4] + out[-1][3] * 0.5)
    return [(t, txt, col, size, y + shift) for t, txt, col, size, y in out]
def cards():
    M = M_TXT
    r = fit_size("RESPONSABILITÉ", M, 200)
    s4 = min(fit_size("DE FAIRE", M, 150), fit_size("EN SORTE", M, 150))
    j = fit_size("JUSTICE", M_BIG, 300)
    s6 = min(fit_size("SOIT MISE", M, 150), fit_size("EN PLACE", M, 150), fit_size("ET APPLIQUÉE", M, 150))
    q = fit_size("SINON À QUOI", 500, 170)                                     # plus étroit : un pétale blanc de la veste collait au « I » (faux texte à l OCR)
    return [
        (0.0,  stack([(0.0, "C'EST DE LA", WHITE, r), (0.24, "RESPONSABILITÉ", WHITE, r), (0.72, "DES POLITIQUES", WHITE, r)])),
        (1.30, stack([(1.30, "C'EST NOTRE", WHITE, fit_size("C'EST NOTRE", M, 160)), (1.52, "RÔLE", WHITE, fit_size("RÔLE", M_BIG, 260))])),
        (1.96, stack([(1.96, "SINON À QUOI", WHITE, q), (2.42, "ON SERT ?", WHITE, q)])),
        (3.06, stack([(3.06, "DE FAIRE", WHITE, s4), (3.44, "EN SORTE", WHITE, s4), (3.86, "QUE LA", WHITE, s4)])),
        (4.70, stack([(4.70, "JUSTICE", RED, j), (4.94, "SOCIALE", RED, j)], gap=0.05)),
        (5.40, stack([(5.40, "SOIT MISE", WHITE, s6), (6.04, "EN PLACE", WHITE, s6), (6.40, "ET APPLIQUÉE", WHITE, s6)])),
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
        big = col == RED or txt == "RÔLE"
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
        if sh["src"] in (LA, LB):                                                    # décor LCI « ROCHEBIN SOIR » (y source 45-85) : bande haute floutée + brûlée
            yb = (92 - (cy - vh / 2)) * H / vh                                      # bas du texte du décor, en px de sortie
            if yb > 0:
                ys = np.arange(H, dtype=np.float32)
                m = np.clip((yb + 30 - ys) / 60, 0, 1)[:, None, None]                # 1 au-dessus du texte, fondu sur 60 px
                g = g * (1 - m) + cv2.GaussianBlur(g, (0, 0), 22) * m
                ramp = 0.10 + 0.90 * np.clip(ys / (yb + 60), 0, 1) ** 1.2
                g = g * ramp[:, None, None]
        if sid == "pose":
            tx = pose_text(i / FPS)
            if tx is not None: g = over_rgba(g, tx)
        if sid == EDIT[0] and i < 4: g = np.clip(g + (1 - i / 4) ** 2 * 0.35, 0, 1)      # flash blanc court sur le drop
        if sid == "fin":
            k = n - i
            if k <= 9: g = g * (k - 1) / 9                                          # fondu au noir final (0,3 s)
        frames.append(g)
    write_mov(frames, OUT + "V2_%s.mov" % sid)
    print("  plan", sid, n, "vue0", tuple(round(x) for x in views[0]), "vh fin", round(views[-1][2]))
# ---------------- plan ----------------
def yt_url(src): return "https://www.youtube.com/watch?v=" + YT[src][0]
def build_plan():
    video = []; ts = cut_times()
    def add(id_, sid, rec, n, extra=None):
        sh = SHOTS[sid]
        v = {"id": id_, "clip": "V2_%s.mov" % sid, "folder": "genV2", "path": OUT + "V2_%s.mov" % sid, "s": 0, "e": n, "rec": rec, "dur": n,
             "clip_fps": FPS, "speed_pct": 100, "track": 1, "note": sh["why"],
             "source": {"fichier": "lot3/sources/" + sh["src"], "in_s": sh["t"], "out_s": round(sh["t"] + n / FPS, 3),
                        "url": yt_url(sh["src"]), "t_youtube_s": round(YT[sh["src"]][1] + sh["t"], 2)}}
        if extra: v.update(extra)
        video.append(v)
    add("pose", "pose", 0, fr(DROP), {"texte": "C'EST DE LA / RESPONSABILITÉ / DES POLITIQUES · C'EST NOTRE / RÔLE · SINON À QUOI / ON SERT ? · DE FAIRE / EN SORTE / QUE LA · JUSTICE / SOCIALE (rouge) · SOIT MISE / EN PLACE / ET APPLIQUÉE (zone sûre TikTok : x 0,17-0,83, bas du bloc y 1370)",
                                       "effets": "longue pose sans coupe %.2f s en son direct (voix synchro), poussée lente 1,00 -> 1,08, N&B contrasté, grain, cartons cuits mot à mot" % DROP})
    for i, sid in enumerate(EDIT):
        a, b = fr(ts[i]), fr(ts[i + 1])
        add(sid, sid, a, b - a, {"temps": BEATS[i], "coupe_sur_t": round(ts[i], 3)})
    plan = {"name": "V2 - Longue pose N&B - Danièle Obono", "fps": FPS, "w": W, "h": H, "duree_s": round(END, 3),
            "note": "Plans ProRes 9:16 recadrés, N&B, texte cuit (gen/V2/out). s/e en images du clip (30 i/s), rec en images timeline. "
                    "Aucun ralenti : speed_pct 100 partout. Coupes sur les frappes réelles du refrain (frappes.json). Générateur : lot4/_claude/gen/V2/genV2.py",
            "phrase": {"texte": "Et je crois que c'est de la responsabilité des politiques, c'est notre rôle, sinon à quoi on sert ? De faire en sorte que la justice sociale soit mise en place et appliquée.",
                       "extrait_audible": "c'est de la responsabilité des politiques, c'est notre rôle, sinon à quoi on sert ? De faire en sorte que la justice sociale soit mise en place et appliquée.",
                       "url": yt_url(LB), "source": "Danièle Obono sur LCI, 24/09/2026 (chaîne officielle Danièle Obono, vidéo « L'EXTRÊME richesse est immorale »)",
                       "in_s": round(YT[LB][1] + V_IN, 2), "out_s": round(YT[LB][1] + V_OUT, 2), "voix": "son direct synchro sur la longue pose, musique qui monte dessous, refrain juste après"},
            "texte_style": {"police": "Arial Black", "couleur": "#FFFFFF, mots-clés JUSTICE SOCIALE #E4002B", "contour": "noir + ombre floue", "position": "centré, largeur <= 580 px, bas du bloc à y 1370 (zone sûre TikTok)"},
            "musique": {"fichier": "lot4/sons/V2-mj-beat-it.wav", "complet": "lot4/sons/V2-mj-beat-it_complet.wav",
                        "debut_dans_complet_s": MOFF, "refrain_timeline_s": DROP, "coupes_timeline_s": [round(x, 3) for x in ts],
                        "paroles_audibles": "sous la voix (bas, qui monte) : « …wanna be tough, better do what you can / So beat it, but you wanna be bad » ; refrain plein : « Just beat it, beat it, beat it, beat it / No one wants to be defeated / Showin' how funky… »"},
            "video": video,
            "audio": [{"id": "mix", "clip": "V2-mix.wav", "folder": "genV2", "path": OUT + "V2-mix.wav", "rec": 0, "track": 1,
                       "note": "voix + ambiance du plateau LCI (son direct %.2f-%.2f s de LCI-b) sur la longue pose ; Beat It %.3f-%.3f s du clip officiel : fin du couplet qui monte de -20 à -7 dB sous la voix, puis refrain plein à %.3f s, -14 LUFS, fondu de fin 0,5 s" % (V_IN, V_OUT, MOFF, MOFF + END, DROP)}]}
    json.dump(plan, open(D + "plan-V2.json", "w"), indent=1, ensure_ascii=False)
    son = {"titre": "Beat It", "artiste": "Michael Jackson", "url": "https://youtu.be/oRdxUFDoQe0", "chaine": "Michael Jackson (clip officiel 4K)",
           "fichier_complet": "lot4/sons/V2-mj-beat-it_complet.wav", "fichier_extrait": "lot4/sons/V2-mj-beat-it.wav",
           "extrait_debut_s": MOFF, "extrait_fin_s": round(MOFF + END, 3), "bpm": round(60 / HITS["beat_s"], 1),
           "drop_morceau_s": round(MOFF + DROP, 3), "drop_timeline_s": DROP, "paroles_audibles": plan["musique"]["paroles_audibles"],
           "frappes_coupes_timeline_s": [round(x, 3) for x in ts], "frappes_temps_timeline_s": K, "note": "frappes détaillées dans frappes.json (frappes.py)"}
    json.dump(son, open(D + "son.json", "w"), indent=1, ensure_ascii=False)
# ---------------- audio ----------------
def make_audio():
    import soundfile as sf
    sr = 48000; N = int(END * sr)
    cmd = [FF, "-v", "error", "-ss", "%.3f" % MOFF, "-t", "%.3f" % END, "-i", SONG, "-ac", "2", "-ar", str(sr), "-f", "f32le", "-"]
    mu = np.frombuffer(subprocess.run(cmd, capture_output=True).stdout, np.float32).reshape(-1, 2).copy()[:N]
    sf.write(L4 + "/sons/V2-mj-beat-it.wav", mu, sr, subtype="PCM_24")
    t = np.arange(len(mu)) / sr; g = np.ones(len(mu), np.float32)
    g[t < 0.03] = t[t < 0.03] / 0.03; s = t > END - 0.5; g[s] *= (END - t[s]) / 0.5
    a0, a1 = V_OUT - POSE_T0, DROP - 0.02                                   # musique qui MONTE sous la phrase (-20 -> -7 dB), pleine au refrain
    gdb = np.where(t < a0, -20 + 13 * np.clip(t / a0, 0, 1) ** 1.5, np.where(t < a1, -7 + 7 * (t - a0) / (a1 - a0), 0.0))
    mu *= (g * (10 ** (gdb / 20)).astype(np.float32))[:, None]
    cmd = [FF, "-v", "error", "-ss", "%.3f" % V_IN, "-t", "%.3f" % (V_OUT - V_IN), "-i", L3 + "/sources/" + LB, "-ac", "2", "-ar", str(sr), "-f", "f32le", "-"]
    v = np.frombuffer(subprocess.run(cmd, capture_output=True).stdout, np.float32).reshape(-1, 2).copy()
    env = np.ones(len(v), np.float32); m = int(0.02 * sr); env[:m] = np.linspace(0, 1, m); m = int(0.04 * sr); env[-m:] = np.linspace(1, 0, m)
    voix = np.zeros_like(mu); i0 = max(int((V_IN - POSE_T0) * sr), 0); voix[i0:i0 + len(v)] = (v * env[:, None])[:len(voix) - i0]
    voix *= 10 ** (7 / 20)
    sf.write(OUT + "V2-voix.wav", voix, sr, subtype="PCM_24"); sf.write(OUT + "V2-musique.wav", mu, sr, subtype="PCM_24")
    sf.write(D + "tmp_mix.wav", mu + voix, sr, subtype="FLOAT")
    r = subprocess.run([FF, "-hide_banner", "-i", D + "tmp_mix.wav", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    js = json.loads(r[r.rindex("{"):r.rindex("}") + 1])
    af = ("loudnorm=I=-14:TP=-1.5:LRA=11:measured_I=%s:measured_TP=%s:measured_LRA=%s:measured_thresh=%s:offset=%s:linear=true,aresample=48000"
          % (js["input_i"], js["input_tp"], js["input_lra"], js["input_thresh"], js["target_offset"]))
    subprocess.run([FF, "-v", "error", "-y", "-i", D + "tmp_mix.wav", "-af", af, "-c:a", "pcm_s24le", OUT + "V2-mix.wav"], check=True)
    os.remove(D + "tmp_mix.wav")
# ---------------- aperçu ffmpeg 540x960 ----------------
APERCU = HG + "/preview/apercu-V2.mp4"
def apercu():
    plan = json.load(open(D + "plan-V2.json")); ins = []; fl = []
    for i, v in enumerate(plan["video"]):
        ins += ["-i", OUT + v["clip"]]
        fl.append("[%d:v]trim=start_frame=%d:end_frame=%d,setpts=PTS-STARTPTS,scale=540:960,setsar=1[v%d]" % (i, v["s"], v["e"], i))
    k = len(plan["video"]); fl.append("".join("[v%d]" % i for i in range(k)) + "concat=n=%d:v=1:a=0[v]" % k)
    subprocess.run([FF, "-v", "error", "-y"] + ins + ["-i", OUT + "V2-mix.wav", "-filter_complex", ";".join(fl), "-map", "[v]", "-map", "%d:a" % k,
                    "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "aac", "-b:a", "192k", "-shortest", APERCU], check=True)
    print("aperçu", APERCU)
# ---------------- contrôle visages : tout visage > 5 % de la hauteur doit être entier ----------------
def check_faces():
    plan = json.load(open(D + "plan-V2.json")); bad = []
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
