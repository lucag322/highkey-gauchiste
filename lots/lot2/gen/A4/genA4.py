# A4 — Aura N&B, David Guiraud (lot 2). Modèle : _claude/gen/1/gen1.py (test 1 validé par Luca).
# Aperçu hors Resolve : plans ProRes 9:16 recadrés (visage suivi) + N&B contrasté + texte Arial Black (mot-clé rouge) cuit.
# Ralentis PAS précalculés : clip à vitesse normale, speed_pct + retime optical_flow dans plan-A4.json (aperçu = setpts simple).
# Usage : python genA4.py [shots] [cards] [audio] [plan] [apercu] [only=ID,ID]   (sans argument = tout)
import sys, os, json, subprocess, math
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
ROOT = "/Users/luca.grousset/Movies/highkey-gauchiste"; LOT = ROOT + "/lot2"
sys.path.insert(0, ROOT + "/_claude/outils")
import framing
from framing import plan_views
from fx import gblur, motion_blur, vignette, to8, ease_out
D = LOT + "/_claude/gen/A4/"; OUT = D + "out/"; os.makedirs(OUT, exist_ok=True)
framing.ROOT = LOT; framing.CACHE = D + "cache"                     # detect() lit LOT/sources/<src>
FF = "/opt/homebrew/bin/ffmpeg"; FPS = 30; W, H = 1080, 1920
RED = (0xE4, 0x00, 0x2B); WHITE = (255, 255, 255)
F_BLACK = "/System/Library/Fonts/Supplemental/Arial Black.ttf"
F_AURA = ("/System/Library/Fonts/Helvetica.ttc", 2)                 # Helvetica Oblique (« aura. » du test 1)
SA, SB, SC, ST = ("A4-guiraud-roubaix-meeting-a.mp4", "A4-guiraud-roubaix-meeting-b.mp4",
                  "A4-guiraud-roubaix-meeting-c.mp4", "A4-guiraud-roubaix-1ertour.mp4")
SRCFPS = {SA: 30, SB: 30, SC: 30, ST: 30}
# zone source utilisable : logo LFI incrusté en haut à droite (x > 1610) exclu ; 1er tour = vidéo verticale native au centre (x 656-1264)
BOUNDS = {SA: (0, 0, 1600, 1080), SB: (0, 0, 1600, 1080), SC: (0, 0, 1600, 1080), ST: (662, 0, 1258, 1080)}
VH = {ST: 1056}
# ---------------- grille musicale (sons-lot2.json, A4 Sahara slowed, extrait posé à 0 s) ----------------
SON = [x for x in json.load(open(LOT + "/_claude/sons-lot2.json"))["sons"] if x["id"] == "A4"][0]
BEATS = SON["beats_s"]; DROP = SON["drop_s"]; K0 = min(range(len(BEATS)), key=lambda i: abs(BEATS[i] - DROP))
def beat(k): return BEATS[K0 + k]                                    # temps k après le drop (6,009 s)
def fr(t): return int(round(t * FPS))
END = 15.0                                                           # règle Luca : aura N&B 15 s max
HOOK_END = BEATS[1]                                                  # 0,771 s = premier downbeat
# ---------------- phrase (meeting-a 48,94-53,56 s) ----------------
# coupe caméra dans la source à l'image 1477 (profil -> face) : calée sur le temps 1,426 s => timeline = source - 1434 images
OFFF = 1434
def tl(src_s): return src_s - OFFF / FPS
CUT_SRC = 1477; PUNCH = BEATS[5]                                     # 3,39 s (downbeat) : coupe plus serrée sur « rien »
# ---------------- plans ----------------
# t = début source (s) ; face = indice visage (px source) ; fixed = centre imposé (foule, de dos) ; speed = % Resolve
SHOTS = {
    "profil":   dict(src=SA, f0=fr(HOOK_END) + OFFF, n=CUT_SRC - fr(HOOK_END) - OFFF, face=(890, 300), zoom=(1.0, 1.02), text=True, why="profil au pupitre, début de la phrase"),
    "face":     dict(src=SA, f0=CUT_SRC, n=fr(PUNCH) + OFFF - CUT_SRC, face=(950, 230), zoom=(1.0, 1.04), text=True, why="face au pupitre ROUBAIX, « population devient invincible »"),
    "serre":    dict(src=SA, f0=fr(PUNCH) + OFFF, n=fr(DROP) - fr(PUNCH), face=(950, 230), zoom=(1.32, 1.38), text=True, why="même plan plus serré, « rien, ni personne ne peut l'arrêter »"),
    "index":    dict(src=SC, t=26.75, n=26, face=(980, 240), zoom=(1.0, 1.06), why="index levé (meeting c)"),
    "mer":      dict(src=SB, t=36.0, n=26, fixed=(1290, 540), zoom=(1.0, 1.06), why="mer de drapeaux, lumières jaunes (meeting b)"),
    "visage":   dict(src=SC, t=10.0, n=26, face=(950, 230), zoom=(1.30, 1.36), why="gros plan de face, fond noir (meeting c)"),
    "drapeaux": dict(src=SA, t=4.0, n=26, fixed=(900, 540), zoom=(1.0, 1.06), why="plan large, drapeau LFI au premier plan (meeting a)"),
    "couloir":  dict(src=SB, t=18.2, n=45, fixed=(1000, 540), zoom=(1.0, 1.04), speed=60, lift=2.2, why="de dos vers la scène, coulisses (meeting b)"),
    "foule":    dict(src=SA, t=55.0, n=26, fixed=(960, 540), zoom=(1.0, 1.04), speed=60, lift=1.6, why="salle debout, drapeaux (meeting a)"),
    "geste":    dict(src=SC, t=17.2, n=26, face=(950, 240), zoom=(1.0, 1.06), lift=1.0, why="geste de la main, voix appuyée (meeting c)"),
    "drapeaux2": dict(src=SB, t=38.7, n=26, fixed=(1000, 540), zoom=(1.0, 1.06), why="salle debout, drapeaux LFI (meeting b)"),
    "victoire": dict(src=ST, t=17.2, n=26, face=(950, 220), zoom=(1.0, 1.04), why="soir du 1er tour, rire, micro (vertical amateur)"),
    "mains":    dict(src=SC, t=29.6, n=26, face=(950, 240), zoom=(1.0, 1.06), why="mains ouvertes, regard salle (meeting c)"),
}
# montage après le drop : (id, nb de temps, effet d'entrée) -- 12 temps = 3 mesures, puis carton « aura. » de fin
EDIT = [("index", 1, "drop"), ("mer", 1, "whip"), ("visage", 1, "whip"), ("drapeaux", 1, "whip"),
        ("couloir", 2, "cut"), ("foule", 1, "cut"), ("aura", 1, "cut"),
        ("geste", 1, "drop"), ("drapeaux2", 1, "whip"), ("victoire", 1, "whip"), ("mains", 1, "whip")]
assert sum(nb for _, nb, _ in EDIT) == 12
# ---------------- look N&B (identique au test 1) ----------------
RNG = np.random.default_rng(11)
def grade(bgr):
    g = (0.114 * bgr[..., 0] + 0.587 * bgr[..., 1] + 0.299 * bgr[..., 2])
    g = np.clip((g - 0.07) / 0.85, 0, 1)
    g = 0.45 * g + 0.55 * (g * g * (3 - 2 * g))
    small = cv2.resize(g, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    hi = np.clip(small - 0.55, 0, None) * 2.0
    glow = cv2.resize(cv2.GaussianBlur(hi, (0, 0), 9), (W, H)) * 0.45
    soft = cv2.resize(cv2.GaussianBlur(small, (0, 0), 4), (W, H))
    g = 1 - (1 - g) * (1 - 0.18 * soft) + glow
    g = vignette(g[..., None], 0.38, 2.4)[..., 0]
    g = 0.008 + np.clip(g, 0, 1) * 0.86
    g = g + RNG.normal(0, 0.018, g.shape).astype(np.float32)
    return np.repeat(np.clip(g, 0, 1)[..., None], 3, 2)
def lift(bgr, k):                                                    # sources de meeting sombres : remonte un peu avant la courbe
    return np.clip(bgr * k, 0, 1) if k != 1 else bgr
# ---------------- lecture source ----------------
def read_frames(src, f0, n):
    p = subprocess.run([FF, "-v", "error", "-ss", "%.4f" % ((f0 - 0.25) / SRCFPS[src]), "-i", LOT + "/sources/" + src, "-frames:v", str(n),
                        "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True, check=True)
    a = np.frombuffer(p.stdout, np.uint8).reshape(-1, 1080, 1920, 3)
    return [x.astype(np.float32) / 255 for x in a]
def crop_916(img, cx, cy, vh):
    vw = vh * 9 / 16; s = W / vw
    M = np.float32([[s, 0, W / 2 - cx * s], [0, s, H / 2 - cy * s]])
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
# ---------------- texte (mot à mot, Arial Black, contour noir + ombre douce) ----------------
def font(path, size, idx=0): return ImageFont.truetype(path, size, index=idx)
def fit_size(txt, maxw, start=250):
    s = start
    while font(F_BLACK, s).getlength(txt) > maxw: s -= 4
    return s
# cartons : liste de lignes (la dernière = ligne forte) ; mot = (texte, début source s, rouge)
# « ET RIEN / NI / PERSONNE » sur 3 lignes : sur 2 lignes, NI PERSONNE ne tenait dans la zone sûre TikTok qu'à 57 px de haut de lettre.
CARDS = [[[("ALORS", 48.94, 0), ("CETTE", 49.14, 0)], [("POPULATION", 49.66, 0)]],
         [[("DEVIENT", 50.16, 0)], [("INVINCIBLE", 50.60, 1)]],
         [[("ET", 51.12, 0), ("RIEN", 51.66, 0)], [("NI", 52.24, 0)], [("PERSONNE", 52.50, 0)]],
         [[("NE", 52.92, 0), ("PEUT", 53.10, 0)], [("L’ARRÊTER", 53.22, 0)]]]
Y0 = 1150
# zone sûre TikTok (1080×1920) : texte centré dans x 0,17-0,83 (≤ 66 % de la largeur), y 0,12-0,75 ;
# la taille garantit que même le mot qui entre (112 %) reste dans la zone.
SAFE_L, SAFE_R = 192, 888
def line_fits(words, s, pop=1.12):
    f = font(F_BLACK, s); sw = max(4, int(s * 0.045)); sp = f.getlength(" ")
    ws = [f.getlength(w) for w in words]; tot = sum(ws) + sp * (len(ws) - 1); x = (W - tot) / 2
    if x - sw < SAFE_L or x + tot + sw > SAFE_R: return False
    for w in ws:
        cx = x + w / 2; half = (w / 2 + sw) * pop
        if cx - half < SAFE_L or cx + half > SAFE_R: return False
        x += w + sp
    return True
def safe_size(words, start):
    s = start
    while s > 8 and not line_fits(words, s): s -= 2
    return s
def sizes(c):
    big = safe_size([w[0] for w in c[-1]], 250)
    return [min(safe_size([w[0] for w in li], 120), big) for li in c[:-1]] + [big]
def line_ys(sz):
    ys = [Y0]
    for s in sz[1:]: ys.append(ys[-1] + 70 + s * 0.62)
    off = (ys[-2] - ys[0]) / 2                                       # 3 lignes : bloc remonté pour garder le même centre
    return [y - off for y in ys]
def text_layer(t_src):
    act = [c for c in CARDS if t_src >= c[0][0][1]]
    if not act: return None
    card = act[-1]; SZ = sizes(card); YS = line_ys(SZ)
    words = [w for li in card for w in li]; last = max(w[1] for w in words if w[1] <= t_src)
    k = (t_src - last) * FPS; e = ease_out(min(k / 3.0, 1.0))           # entrée 3 images, sans rebond
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay); ds = ImageDraw.Draw(sh)
    for line, size, yc in zip(card, SZ, YS):
        f = font(F_BLACK, size); sp = f.getlength(" ")
        widths = [f.getlength(w[0]) for w in line]; x = (W - (sum(widths) + sp * (len(line) - 1))) / 2
        for (txt, ts, red), wd in zip(line, widths):
            cx = x + wd / 2; x += wd + sp
            if ts > t_src: continue
            sc, al = (1.12 - 0.12 * e, min(1.0, 0.35 + e)) if ts == last else (1.0, 1.0)
            fs = font(F_BLACK, max(8, int(size * sc))); sw = max(4, int(size * sc * 0.045))
            x0, y0, x1, y1 = d.textbbox((0, 0), txt, font=fs, stroke_width=sw)
            px = cx - (x1 - x0) / 2 - x0; py = yc - (y1 - y0) / 2 - y0
            col = RED if red else WHITE
            ds.text((px, py + size * 0.05), txt, font=fs, fill=(0, 0, 0, int(200 * al)), stroke_width=sw * 3, stroke_fill=(0, 0, 0, int(200 * al)))
            d.text((px, py), txt, font=fs, fill=col + (int(255 * al),), stroke_width=sw, stroke_fill=(0, 0, 0, int(255 * al)))
    sh = sh.filter(ImageFilter.GaussianBlur(18))
    return np.asarray(Image.alpha_composite(sh, lay)).astype(np.float32) / 255
def over_rgba(img_bgr, rgba):
    a = rgba[..., 3:4]; rgb = rgba[..., 2::-1]
    return img_bgr * (1 - a) + rgb * a
# ---------------- rendu des plans ----------------
def write_mov(frames, path, fps=FPS):
    p = subprocess.Popen([FF, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", "%dx%d" % (W, H), "-r", str(fps), "-i", "-",
                          "-c:v", "prores_ks", "-profile:v", "3", "-pix_fmt", "yuv422p10le", "-vendor", "apl0", path], stdin=subprocess.PIPE)
    for f in frames: p.stdin.write(to8(f).tobytes())
    p.stdin.close(); p.wait()
def src_f0(sh): return sh["f0"] if "f0" in sh else int(round(sh["t"] * SRCFPS[sh["src"]]))
def render_shot(sid):
    sh = SHOTS[sid]; src = sh["src"]; n = sh["n"]; s0 = src_f0(sh)
    raw = read_frames(src, s0, n)
    z0, z1 = sh["zoom"]; zoom = lambda f: z0 + (z1 - z0) * f / max(n - 1, 1)
    vh = VH.get(src, 1080)
    if "fixed" in sh:
        views, _ = plan_views(src, s0, n, SRCFPS[src], speed=1.0, bounds=BOUNDS[src], vh=vh, zoom=zoom, fixed=sh["fixed"])
    else:
        views, ok = plan_views(src, s0, n, SRCFPS[src], speed=1.0, hint=sh["face"], bounds=BOUNDS[src], vh=vh, zoom=zoom, top=0.12)
        if not ok: print("  ! pas de visage détecté :", sid)
    frames = []
    for i, (img, (cx, cy, v)) in enumerate(zip(raw, views)):
        g = grade(lift(crop_916(img, cx, cy, v), sh.get("lift", 1.25)))
        if sh.get("text"):
            tlr = text_layer((s0 + i) / FPS)
            if tlr is not None: g = over_rgba(g, tlr)
        frames.append(g)
    write_mov(frames, OUT + "A4_%s.mov" % sid)
    SHOTS[sid]["vue0"] = [round(x) for x in views[0]]
    print("  plan", sid, n, "images", "vue0", SHOTS[sid]["vue0"])
# ---------------- cartes « aura. » ----------------
def aura_card(n, fade_in=3, fade_out=0):
    im = Image.new("L", (W, H), 0); d = ImageDraw.Draw(im); f = font(F_AURA[0], 120, F_AURA[1])
    tw = d.textlength("aura.", font=f); d.text(((W - tw) / 2, H / 2 - 80), "aura.", font=f, fill=255)
    a = np.asarray(im).astype(np.float32) / 255
    base = np.clip(a * 0.92 + gblur(a, 22) * 0.9 + gblur(a, 6) * 0.5, 0, 0.95)
    out = []
    for i in range(n):
        k = 1.0
        if fade_in and i < fade_in: k = ease_out((i + 1) / fade_in)
        if fade_out and i >= n - fade_out: k = (n - i) / fade_out
        out.append(np.repeat((0.008 + base * k)[..., None], 3, 2))
    return out
def make_cards():
    write_mov(aura_card(fr(HOOK_END)), OUT + "A4_aura_intro.mov")
    write_mov(aura_card(fr(beat(7)) - fr(beat(6))), OUT + "A4_aura.mov")
    write_mov(aura_card(fr(END) - fr(beat(12)), fade_in=3, fade_out=12), OUT + "A4_aura_fin.mov")
def entry_variant(sid, kind):
    p = subprocess.run([FF, "-v", "error", "-i", OUT + "A4_%s.mov" % sid, "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True)
    fr_ = np.frombuffer(p.stdout, np.uint8).reshape(-1, H, W, 3).astype(np.float32) / 255
    out = []
    for i, f in enumerate(fr_):
        if kind == "whip" and i < 3: f = motion_blur(f, 0, [220, 90, 25][i], steps=16)
        if kind == "drop" and i < 8:
            k = (1 - i / 8) ** 2; f = np.clip(f + k * 0.35 + gblur(f, 25) * k * 0.4, 0, 1)      # bloom adouci (pas d'image blanche)
        out.append(f)
    write_mov(out, OUT + "A4_%s_%s.mov" % (sid, kind))
# ---------------- plan ----------------
def build_plan():
    video = []
    def add(id_, clip, s, e, rec, kind, extra=None):
        v = {"id": id_, "clip": clip, "folder": "genA4", "s": s, "e": e, "rec": rec, "dur": e - s, "track": 1, "kind": kind}
        if extra: v.update(extra)
        video.append(v)
    def srcinfo(sid):
        sh = SHOTS[sid]; return "lot2/sources/%s @ %.2f s" % (sh["src"], src_f0(sh) / SRCFPS[sh["src"]])
    add("hook", "A4_aura_intro.mov", 0, fr(HOOK_END), 0, "card")
    a = fr(HOOK_END)
    for sid in ("profil", "face", "serre"):
        n = SHOTS[sid]["n"]; add(sid, "A4_%s.mov" % sid, 0, n, a, "shot", {"source": srcinfo(sid), "son": "synchrone"}); a += n
    assert a == fr(DROP), (a, fr(DROP))
    k = 0
    for sid, nb, eff in EDIT:
        a, b = fr(beat(k)), fr(beat(k + nb)); n = b - a
        if sid == "aura":
            add("aura_%d" % a, "A4_aura.mov", 0, n, a, "card")
        else:
            sh = SHOTS[sid]; clip = "A4_%s.mov" % sid if eff == "cut" else "A4_%s_%s.mov" % (sid, eff)
            extra = {"source": srcinfo(sid), "effet": eff, "temps": nb}
            if sh.get("speed"): extra.update({"speed_pct": sh["speed"], "retime": "optical_flow"})
            add("%s_%d" % (sid, a), clip, 0, n, a, "shot", extra)
        k += nb
    add("fin", "A4_aura_fin.mov", 0, fr(END) - fr(beat(12)), fr(beat(12)), "card")
    plan = {"name": "A4 - Aura N&B - David Guiraud", "fps": FPS, "w": W, "h": H, "duree_s": END,
            "note": "Aperçu lot 2. Plans 9:16 recadrés + N&B (lot2/_claude/gen/A4/out), texte cuit sur profil/face/serre. s/e en images du clip, rec en images "
                    "timeline 30 i/s. speed_pct : ralenti Resolve Optical Flow (e - s = durée timeline à vitesse normale). Coupes sur les temps "
                    "(91,6 BPM, drop 6,009 s) ; aucun plan < 1 temps. Générateur : lot2/_claude/gen/A4/genA4.py",
            "phrase": {"source": "lot2/sources/%s 48,94-53,56 s (YouTube o-1R3UFtXiQ, +1640 s), timeline = source - %.3f s" % (SA, OFFF / FPS),
                       "texte": "alors cette population devient invincible et rien, ni personne, ne peut l'arrêter.",
                       "cartons": [[" ".join(w[0] for w in li) for li in c] for c in CARDS], "rouge": ["INVINCIBLE"]},
            "musique": {"fichier": "lot2/" + SON["fichier"], "titre": "%s - %s" % (SON["artiste"], SON["titre"]), "rec": 0, "gain_db": GAIN_MUS,
                        "duck_db_sous_voix": DUCK, "drop_timeline_s": DROP, "bpm": SON["bpm"]},
            "video": video,
            "audio": [{"id": "mix", "clip": "A4-mix.wav", "folder": "genA4", "rec": 0, "track": 1, "note": "mix -14 LUFS (musique dès 0 s, voix synchrone 0,77-6,4 s)"}],
            "stems": ["lot2/_claude/gen/A4/out/A4-voix.wav", "lot2/_claude/gen/A4/out/A4-musique.wav"],
            "sources": {sid: {"fichier": "lot2/sources/" + v["src"], "t": round(src_f0(v) / SRCFPS[v["src"]], 3), "pourquoi": v["why"]} for sid, v in SHOTS.items()},
            "sources_url": {SA: "youtube o-1R3UFtXiQ (chaîne JEAN-LUC MÉLENCHON, meeting Roubaix 31/01/2026, +1640 s)",
                            SB: "youtube o-1R3UFtXiQ (+1310 s)", SC: "youtube o-1R3UFtXiQ (+1855 s)",
                            ST: "youtube p8W_23AWUVA (chaîne David Guiraud, soir du 1er tour 15/03/2026)"}}
    json.dump(plan, open(D + "plan-A4.json", "w"), indent=1, ensure_ascii=False)
    return plan
# ---------------- audio ----------------
GAIN_MUS = SON["niveau"]["gain_conseille_db_vers_moins14LUFS"]; DUCK = -12.0
def make_audio():
    import soundfile as sf
    sr = 48000; N = int(END * sr)
    def load(path, t=0.0, dur=None):
        cmd = [FF, "-v", "error", "-ss", "%.3f" % t] + (["-t", "%.3f" % dur] if dur else []) + ["-i", path, "-ac", "2", "-ar", str(sr), "-f", "f32le", "-"]
        return np.frombuffer(subprocess.run(cmd, capture_output=True).stdout, np.float32).reshape(-1, 2).copy()
    def place(buf, x, t, gain_db=0, fin=0.0, fout=0.0):
        g = 10 ** (gain_db / 20); n = len(x); env = np.ones(n, np.float32)
        if fin: m = int(fin * sr); env[:m] = np.linspace(0, 1, m)
        if fout: m = int(fout * sr); env[-m:] *= np.linspace(1, 0, m)
        a = int(t * sr); b = min(N, a + n); buf[a:b] += x[:b - a] * env[:b - a, None] * g
    voix = np.zeros((N, 2), np.float32); mus = np.zeros((N, 2), np.float32)
    v_in, v_out = 48.88, 54.40                                        # « alors » 48,94 -> « l'arrêter » 53,56 + applaudissements (aucune parole après)
    place(voix, load(LOT + "/sources/" + SA, v_in, v_out - v_in), tl(v_in), +4, fin=0.04, fout=0.5)
    m = load(LOT + "/" + SON["fichier"], 0, END + 0.2)
    env = np.ones(len(m), np.float32); t = np.arange(len(m)) / sr
    d = 10 ** (DUCK / 20)
    env = np.where((t > 0.70) & (t < 5.75), d, 1.0).astype(np.float32)
    for a0, a1, up in ((0.55, 0.75, False), (5.75, 6.0, True)):       # rampes du duck
        sel = (t >= a0) & (t < a1); r = (t[sel] - a0) / (a1 - a0)
        env[sel] = (d + (1 - d) * r) if up else (1 + (d - 1) * r)
    m = m * env[:, None]
    place(mus, m, 0.0, GAIN_MUS, fout=0.6)
    sf.write(OUT + "A4-voix.wav", voix, sr, subtype="PCM_24"); sf.write(OUT + "A4-musique.wav", mus, sr, subtype="PCM_24")
    sf.write(D + "tmp_mix.wav", voix + mus, sr, subtype="FLOAT")
    r = subprocess.run([FF, "-hide_banner", "-i", D + "tmp_mix.wav", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    js = json.loads(r[r.rindex("{"):r.rindex("}") + 1])
    af = ("loudnorm=I=-14:TP=-1.5:LRA=11:measured_I=%s:measured_TP=%s:measured_LRA=%s:measured_thresh=%s:offset=%s:linear=true,"
          "aresample=48000" % (js["input_i"], js["input_tp"], js["input_lra"], js["input_thresh"], js["target_offset"]))
    subprocess.run([FF, "-v", "error", "-y", "-i", D + "tmp_mix.wav", "-af", af, "-c:a", "pcm_s24le", OUT + "A4-mix.wav"], check=True)
    os.remove(D + "tmp_mix.wav")
# ---------------- aperçu ffmpeg 540x960 conforme au plan ----------------
def apercu():
    plan = json.load(open(D + "plan-A4.json")); ins = []; fl = []
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
    ins += ["-i", OUT + "A4-mix.wav"]
    out = ROOT + "/preview/apercu-A4.mp4"
    subprocess.run([FF, "-v", "error", "-y"] + ins + ["-filter_complex", ";".join(fl), "-map", "[v]", "-map", "%d:a" % k,
                    "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "aac", "-b:a", "192k", "-shortest", out], check=True)
    print("aperçu", out)
if __name__ == "__main__":
    args = set(a for a in sys.argv[1:] if not a.startswith("only=")) or {"shots", "cards", "audio", "plan", "apercu"}
    only = [x for a in sys.argv[1:] if a.startswith("only=") for x in a.split("=", 1)[1].split(",")]
    if only: args = set()
    if "shots" in args or only:
        for sid in (only or SHOTS): render_shot(sid)
        for sid, nb, eff in EDIT:
            if eff in ("whip", "drop") and (not only or sid in only): entry_variant(sid, eff)
    if "cards" in args: make_cards()
    if "plan" in args: build_plan()
    if "audio" in args: make_audio()
    if "apercu" in args: apercu()
