# A2 — Aura N&B, Manuel Bompard (lot 2). Modèle : _claude/gen/1/gen1.py (test 1 validé par Luca).
# Aperçu HORS Resolve : plans 9:16 recadrés (visage suivi, Apple Vision), N&B contrasté + bloom, texte Arial Black cuit sur le plan parlé.
# Ralentis PAS précalculés : clip à vitesse normale, speed_pct + retime optical_flow dans plan-A2.json (setpts simple dans l'aperçu).
# Usage : python genA2.py [shots] [cards] [audio] [plan] [apercu] [only=ID,ID]   (sans argument = tout)
import sys, os, json, subprocess, math
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
ROOT = "/Users/luca.grousset/Movies/highkey-gauchiste"; LOT = ROOT + "/lot2"
sys.path.insert(0, ROOT + "/_claude/outils")
import framing
from fx import gblur, motion_blur, vignette, to8, ease_out
from framing import plan_views
D = LOT + "/_claude/gen/A2/"; OUT = D + "out/"; os.makedirs(OUT, exist_ok=True)
framing.ROOT = LOT; framing.CACHE = D + "cache"                 # detect() lit LOT/sources/<src>
FF = "/opt/homebrew/bin/ffmpeg"; FPS = 30; W, H = 1080, 1920
RED = (0xE4, 0x00, 0x2B); WHITE = (255, 255, 255)
F_BLACK = "/System/Library/Fonts/Supplemental/Arial Black.ttf"
F_AURA = ("/System/Library/Fonts/Helvetica.ttc", 2)              # Helvetica Oblique (« aura. » du test 1)
SA, SB = "A2-bompard-convention-a.mp4", "A2-bompard-convention-b.mp4"
SRCFPS = {SA: 25, SB: 25}
# zone utilisable : exclut l'incrustation CONVENTION MUNICIPALES (haut gauche, x < 370) et le logo LFI (haut droite, x > 1640)
# + l'écran géant du plan large (x > 1300) => la fenêtre 9:16 ne les atteint jamais
BOUNDS = {SA: (380, 0, 1600, 1080), SB: (380, 0, 1600, 1080)}
BOUNDS_WIDE = (380, 0, 1300, 1080)
# ---------------- musique : Kaaris - Zoo (sons-lot2.json A2, 126 BPM = 63 en demi-temps) ----------------
SON = [x for x in json.load(open(LOT + "/_claude/sons-lot2.json"))["sons"] if x["id"] == "A2"][0]
# Retour Luca : GARDER les paroles. Extrait CONTINU du complet : montée instrumentale sous la phrase de Bompard, drop de la prod
# lourde à 50,22 s (clic du 1er kick) = 3,80 s timeline, puis le morceau tel quel (rap dès 51,50 s du complet), aucun raccord.
MFILE = LOT + "/" + SON["fichier_complet"]; MGAIN = SON["niveau"]["gain_conseille_db_vers_moins14LUFS"]
MDROP = 50.2198                                  # entrée de la prod lourde (clic du 1er kick, complet ; la sous-basse culmine ~40 ms après)
SPLICE_A = None                                  # extrait continu (pas de raccord)
DROP = 3.80                                      # drop dans la timeline = juste après « pouvoir. » (fin 3,69 s)
MUSIC_IN = MDROP - DROP - 0.008                  # décalage sous-image choisi pour que les frappes coupées tombent au plus près des images
def fr(t): return int(round(t * FPS))
INTRO = 1.25                                     # carton « aura. » d'ouverture
END = 14.97                                      # règle Luca : aura N&B 15 s max
# frappes réelles (kick/808 < 150 Hz pris sur son clic 150-1500 Hz, caisse > 1,5 kHz ; attaque à 30 % de l'enveloppe) mesurées sur la musique POSÉE (out/A2-musique.wav)
# coupes = frappes choisies (temps timeline approx., recalées sur la frappe détectée la plus proche) ; grille 126 BPM depuis le drop (t = temps) :
#   3,81 drop kick (t0) | 4,75 caisse (t2) | 6,19 kick (t5, rien de fort entre les deux dans le vrai drop) | 6,66 caisse (t6)
#   | 7,37 kick (t7½) | 8,09 kick (t9) | 8,56 caisse (t10) | 9,99 kick (t13) | 10,46 caisse (t14) | 11,18 kick (t15½)
#   | 11,90 kick (t17) | 12,36 caisse (t18) | 13,80 kick (t21) -> carton de fin
CUT_APPROX = [3.808, 4.754, 6.191, 6.657, 7.375, 8.089, 8.560, 9.993, 10.463, 11.181, 11.895, 12.364, 13.797]
# ---------------- phrase (derush-AG.json A2, mots Whisper dans le fichier source) ----------------
PH = json.load(open(LOT + "/_claude/derush-AG.json"))["figures"]["A2"]["phrase"]
WORDS = [(w["start"], w["w"]) for w in PH["mots"]]  # Oui, 44,78 / nous / sommes / candidats 45,56 / au 46,20 / pouvoir. 46,42-46,84
T_LONG = 44.40                                   # début image du plan large (voix dès 44,62, après « …dans le monde. »)
# ---------------- plans ----------------
SHOTS = {
    "long":     dict(src=SA, t=T_LONG, n=fr(DROP) - fr(INTRO), fixed=(950, 470), zoom=(1.0, 1.15), bounds=BOUNDS_WIDE,
                     why="plan large salle, phrase « Oui, nous sommes candidats au pouvoir. » (synchrone)"),
    "poing_b":  dict(src=SB, t=10.9, n=45, face=(930, 300), dx=95, zoom=(1.0, 1.06), why="gros plan fond orange, poing serré"),
    "doigt":    dict(src=SA, t=5.85, n=45, face=(900, 280), dx=-100, zoom=(1.0, 1.06), why="gros plan fond vert, doigt levé"),
    "cote":     dict(src=SA, t=25.4, n=45, face=(690, 150), zoom=(1.0, 1.06), why="au pupitre vu de côté, bras tendu, fond multicolore"),
    "poing":    dict(src=SA, t=37.4, n=45, face=(900, 280), dx=-110, zoom=(1.0, 1.06), why="gros plan, poing serré, voix forte"),
    "audience": dict(src=SA, t=82.6, n=45, fixed=(700, 540), zoom=(1.0, 1.05), speed=60, why="depuis le public, silhouettes, Bompard au pupitre"),
    "cri":      dict(src=SA, t=7.55, n=45, face=(900, 280), dx=-100, zoom=(1.0, 1.06), why="gros plan, poing levé"),
    "mains":    dict(src=SB, t=25.9, n=45, face=(900, 280), zoom=(1.0, 1.06), why="gros plan, mains ouvertes"),
    "regard":   dict(src=SA, t=58.9, n=45, face=(900, 280), zoom=(1.0, 1.06), why="gros plan, regard droit"),
    "orange":   dict(src=SB, t=7.0, n=45, face=(930, 300), zoom=(1.0, 1.06), why="gros plan fond orange, voix forte"),
    "doigt2":   dict(src=SA, t=11.9, n=45, face=(900, 280), dx=100, zoom=(1.0, 1.06), why="gros plan, doigt levé"),
    "index":    dict(src=SA, t=88.5, n=45, face=(900, 280), zoom=(1.0, 1.06), why="gros plan, index levé"),
    "poing2":   dict(src=SA, t=39.2, n=45, face=(900, 280), zoom=(1.0, 1.06), why="gros plan, poing levé"),
    "pupitre":  dict(src=SA, t=27.6, n=45, face=(690, 150), zoom=(1.0, 1.04), speed=60, why="au pupitre vu de côté (fin)"),
}
# ---------------- frappes réelles dans la musique posée ----------------
def music_raw(sr=48000):
    """Musique telle que posée dans la timeline (avant gain/ducking) : complet lu en continu dès MUSIC_IN."""
    import soundfile as sf_
    x, r = sf_.read(MFILE, dtype="float32"); assert r == sr
    i0 = int(round(MUSIC_IN * sr)); return x[i0:i0 + int((END + 0.5) * sr)]
def detect_hits(y, sr=48000):
    """Frappes réelles : repérage par bande (kick/808 < 150 Hz, caisse > 1,5 kHz), puis instant d'attaque.
    La sous-basse d'une 808 monte en 30-40 ms : l'instant du kick est pris sur son CLIC (bande 150-1500 Hz) juste avant."""
    import scipy.signal as ss, librosa
    m = y.mean(1); out = []
    def envel(typ, fc):   # enveloppe de Hilbert lissée 2 ms, filtre à phase nulle (pas de retard)
        return np.convolve(np.abs(ss.hilbert(ss.sosfiltfilt(ss.butter(4, fc, typ, fs=sr, output="sos"), m))), np.ones(96) / 96, "same")
    def attack(env, c):   # retour en arrière depuis le sommet c jusqu'à 30 % du sommet
        thr = 0.3 * env[c]; i = c
        while i > c - int(0.06 * sr) and i > 0 and env[i - 1] > thr: i -= 1
        return i
    clic = envel("bp", [150, 1500])
    for band, (typ, fc) in (("kick", ("lp", 150)), ("caisse", ("hp", 1500))):
        env = envel(typ, fc)
        hop = 128; e = env[::hop]; d = np.maximum(0, np.diff(e, prepend=e[0])); d /= d.max()
        for p in librosa.util.peak_pick(d, pre_max=20, post_max=20, pre_avg=40, post_avg=40, delta=0.15, wait=40):
            c0 = p * hop; lo, hi = max(0, c0 - int(0.01 * sr)), min(len(env), c0 + int(0.05 * sr))
            i = attack(env, lo + int(np.argmax(env[lo:hi])))
            if band == "kick":   # clic du kick : sommet de la bande médium dans [-60 ms, +10 ms] autour de l'attaque basse
                lo, hi = max(0, i - int(0.06 * sr)), i + int(0.01 * sr); c = lo + int(np.argmax(clic[lo:hi]))
                if clic[c] > 2 * np.median(clic[max(0, lo - int(0.1 * sr)):lo]): i = attack(clic, c)
            out.append((round(i / sr, 4), band, round(float(d[p]), 2)))
    return sorted(out)
HITS_JSON = OUT + "A2-frappes.json"
def frappes(refresh=False):
    key = [MUSIC_IN, SPLICE_A, END]
    if not refresh and os.path.exists(HITS_JSON):
        js = json.load(open(HITS_JSON))
        if js["cle"] == key: return js["frappes"]
    h = detect_hits(music_raw()); json.dump({"cle": key, "frappes": h}, open(HITS_JSON, "w")); return h
HITS = frappes()
def snap(t):
    c = min(HITS, key=lambda h: abs(h[0] - t)); assert abs(c[0] - t) < 0.03, ("pas de frappe près de", t); return c[0]
CUTS = [snap(t) for t in CUT_APPROX]              # temps réels des frappes coupées (timeline)
CUTF = [fr(c) for c in CUTS]                      # images de coupe (30 i/s)
# montage après le drop : (id, effet d'entrée) ; le plan i va de la frappe CUTS[i] à CUTS[i+1], le carton de fin de CUTS[-1] à END
EDIT = [("poing_b", "drop"), ("doigt", "whip"), ("cote", "whip"), ("poing", "whip"),          # 1re mesure du drop (8 temps)
        ("cri", "drop"), ("mains", "whip"),                                                    # 2e mesure
        ("audience", "cut"), ("aura", "cut"),                                                  # ralenti sur le roulement de 808, carton sur la caisse
        ("regard", "whip"), ("doigt2", "drop"), ("index", "whip"), ("pupitre", "cut")]         # 3e mesure, ralenti de fin
assert len(EDIT) == len(CUTS) - 1
PLAN_N = {sid: CUTF[i + 1] - CUTF[i] for i, (sid, eff) in enumerate(EDIT)}
BEAT = 60 / 126.1                                 # 1 temps (126 BPM)
assert min(np.diff(CUTS)) >= BEAT - 0.01 and min(PLAN_N.values()) >= 14, ("plan < 1 temps", PLAN_N)   # 1 temps = 14,3 images
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
# ---------------- lecture source ----------------
def read_frames(src, t, n_out):
    sf = SRCFPS[src]; cap = cv2.VideoCapture(LOT + "/sources/" + src)
    s0 = int(round(t * sf)); cap.set(cv2.CAP_PROP_POS_FRAMES, s0)
    need = [int(round(i * sf / FPS)) for i in range(n_out)]; buf = []; k = 0; out = []
    while k <= need[-1]:
        ok, f = cap.read()
        if not ok: break
        buf.append(f); k += 1
    for i in need: out.append(buf[min(i, len(buf) - 1)].astype(np.float32) / 255)
    return out, s0
def crop_916(img, cx, cy, vh):
    vw = vh * 9 / 16; s = W / vw
    M = np.float32([[s, 0, W / 2 - cx * s], [0, s, H / 2 - cy * s]])
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
# ---------------- texte (Arial Black, contour noir + ombre, mot-clé rouge) ----------------
def font(path, size, idx=0): return ImageFont.truetype(path, size, index=idx)
def fit_size(txt, maxw, start=260):
    s = start
    while font(F_BLACK, s).getlength(txt) > maxw: s -= 4
    return s
def text_layer(lines, alpha_scale=1.0, scale=1.0):
    """lines = [(mots, nb_visibles, couleur, taille_px, y_centre_px)] ; la ligne est centrée sur la phrase ENTIÈRE (pas de glissement)."""
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay); ds = ImageDraw.Draw(sh)
    for words, nv, col, size, yc in lines:
        f = font(F_BLACK, max(8, int(size * scale))); sw = max(4, int(size * 0.045))
        full = " ".join(words); x0, y0, x1, y1 = d.textbbox((0, 0), full, font=f, stroke_width=sw)
        x = (W - (x1 - x0)) / 2 - x0; y = yc - (y1 - y0) / 2 - y0
        txt = " ".join(words[:nv])
        ds.text((x, y + size * 0.05), txt, font=f, fill=(0, 0, 0, 200), stroke_width=sw * 3, stroke_fill=(0, 0, 0, 200))
        d.text((x, y), txt, font=f, fill=col + (255,), stroke_width=sw, stroke_fill=(0, 0, 0, 255))
    sh = sh.filter(ImageFilter.GaussianBlur(18))
    a = np.asarray(Image.alpha_composite(sh, lay)).astype(np.float32) / 255
    a[..., 3] *= alpha_scale
    return a
def over_rgba(img_bgr, rgba):
    a = rgba[..., 3:4]; rgb = rgba[..., 2::-1]
    return img_bgr * (1 - a) + rgb * a
Y1 = 1250
S1 = min(110, fit_size("OUI, NOUS SOMMES", 940)); SV = fit_size("CANDIDATS", 1000); SP = fit_size("POUVOIR", 960)
def long_text(t_src):
    """Carton 1 : OUI, NOUS SOMMES (mot à mot) / CANDIDATS (géant blanc). Carton 2 : AU / POUVOIR (géant rouge). Entrée 3 images sans rebond."""
    on = [w for w in WORDS if t_src >= w[0]]
    if not on: return None
    up = [w[1].rstrip(".").upper() for w in WORDS]          # pas de point final à l'écran, virgule gardée
    n = len(on)
    if n <= 4:
        lines = [(up[0:3], min(n, 3), WHITE, S1, Y1)]
        if n == 4: lines.append(([up[3]], 1, WHITE, SV, Y1 + 60 + SV * 0.62))
    else:
        lines = [([up[4]], 1, WHITE, 150, Y1)]
        if n == 6: lines.append(([up[5]], 1, RED, SP, Y1 + 75 + SP * 0.62))
    k = (t_src - on[-1][0]) * FPS
    e = ease_out(min(k / 3.0, 1.0))
    if n in (4, 6):                                          # mot géant : entrée échelle 1,12 -> 1 sur 3 images
        base = text_layer(lines[:-1]); top = text_layer(lines[-1:], alpha_scale=min(1.0, 0.35 + e), scale=1.12 - 0.12 * e)
        a = top[..., 3:4]; out = base * (1 - a) + top * a; out[..., 3:4] = np.maximum(base[..., 3:4], a); return out
    return text_layer(lines, alpha_scale=1.0 if n > 1 else min(1.0, 0.35 + e))
# ---------------- rendu des plans ----------------
def write_mov(frames, path, fps=FPS):
    p = subprocess.Popen([FF, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", "%dx%d" % (W, H), "-r", str(fps), "-i", "-",
                          "-c:v", "prores_ks", "-profile:v", "3", "-pix_fmt", "yuv422p10le", "-vendor", "apl0", path], stdin=subprocess.PIPE)
    for f in frames: p.stdin.write(to8(f).tobytes())
    p.stdin.close(); p.wait()
def render_shot(sid):
    sh = SHOTS[sid]; src = sh["src"]; n = PLAN_N.get(sid, sh["n"]); bounds = sh.get("bounds", BOUNDS[src])
    raw, s0 = read_frames(src, sh["t"], n)
    # poussée lente avant qui se termine pile sur la frappe de sortie du plan (ralenti : sur les images source réellement lues)
    m = math.ceil(n * sh.get("speed", 100) / 100) if sid != "long" else n
    z0, z1 = sh["zoom"]; zoom = lambda f: z0 + (z1 - z0) * min(f / max(m - 1, 1), 1.0)
    sf = SRCFPS[src]
    if "fixed" in sh:
        views, _ = plan_views(src, s0, n, sf, speed=sf / FPS, bounds=bounds, vh=1080, zoom=zoom, fixed=sh["fixed"])
    else:
        dx = sh.get("dx", 0)                       # décalage px source vers le geste (main / poing), la tête reste entière
        views, ok = plan_views(src, s0, n, sf, speed=sf / FPS, hint=sh["face"], bounds=bounds, vh=1080, zoom=zoom, top=0.12,
                               shake=(lambda f: (dx / 600.0, 0)) if dx else None)
        if not ok: print("  ! pas de visage détecté :", sid)
    frames = []
    for i, (img, (cx, cy, vh)) in enumerate(zip(raw, views)):
        g = grade(crop_916(img, cx, cy, vh))
        if sid == "long":
            tl = long_text(sh["t"] + i / FPS)
            if tl is not None: g = over_rgba(g, tl)
        frames.append(g)
    write_mov(frames, OUT + "A2_%s.mov" % sid)
    print("  plan", sid, n, "images, vue0", tuple(round(v) for v in views[0]), "vue fin", tuple(round(v) for v in views[-1]))
# ---------------- cartes « aura. » ----------------
def aura_card(n, fade_in=3, fade_out=0):
    im = Image.new("L", (W, H), 0); d = ImageDraw.Draw(im); f = font(F_AURA[0], 120, F_AURA[1])
    tw = d.textlength("aura.", font=f); d.text(((W - tw) / 2, H / 2 - 80), "aura.", font=f, fill=255)
    a = np.asarray(im).astype(np.float32) / 255
    glow = gblur(a, 22) * 0.9 + gblur(a, 6) * 0.5
    base = np.clip(a * 0.92 + glow, 0, 0.95)
    out = []
    for i in range(n):
        k = 1.0
        if fade_in and i < fade_in: k = ease_out((i + 1) / fade_in)
        if fade_out and i >= n - fade_out: k = (n - i) / fade_out
        out.append(np.repeat((0.008 + base * k)[..., None], 3, 2))
    return out
def make_cards():
    write_mov(aura_card(fr(INTRO)), OUT + "A2_aura_intro.mov")
    write_mov(aura_card(PLAN_N["aura"]), OUT + "A2_aura.mov")
    write_mov(aura_card(fr(END) - CUTF[-1], fade_in=3, fade_out=10), OUT + "A2_aura_fin.mov")
# ---------------- effets d'entrée (whip = flou de mouvement 3 images, drop = bloom 8 images) ----------------
def entry_variant(sid, kind):
    path_in = OUT + "A2_%s.mov" % sid; path = OUT + "A2_%s_%s.mov" % (sid, kind)
    p = subprocess.run([FF, "-v", "error", "-i", path_in, "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True)
    fr_ = np.frombuffer(p.stdout, np.uint8).reshape(-1, H, W, 3).astype(np.float32) / 255
    out = []
    for i, f in enumerate(fr_):
        if kind == "whip" and i < 3: f = motion_blur(f, 0, [220, 90, 25][i], steps=16)
        if kind == "drop" and i < 8:
            k = (1 - i / 8) ** 2; f = np.clip(f + k * 0.55 + gblur(f, 25) * k * 0.6, 0, 1)
        out.append(f)
    write_mov(out, path)
# ---------------- plan ----------------
def build_plan():
    video = []
    def add(id_, clip, s, e, rec, kind, extra=None):
        v = {"id": id_, "clip": clip, "folder": "genA2", "s": s, "e": e, "rec": rec, "track": 1, "kind": kind}
        if extra: v.update(extra)
        video.append(v)
    add("hook", "A2_aura_intro.mov", 0, fr(INTRO), 0, "card")
    add("long", "A2_long.mov", 0, fr(DROP) - fr(INTRO), fr(INTRO), "shot",
        {"source": "%s @ %.2f s" % (SA, T_LONG), "texte": "OUI, NOUS SOMMES / CANDIDATS · AU / POUVOIR (rouge)"})
    for k, (sid, eff) in enumerate(EDIT):
        a, b = CUTF[k], CUTF[k + 1]; n = b - a; nb = round((CUTS[k + 1] - CUTS[k]) / BEAT, 1)
        if sid == "aura":
            add("aura_%d" % a, "A2_aura.mov", 0, n, a, "card")
        else:
            sh = SHOTS[sid]; clip = "A2_%s.mov" % sid if eff == "cut" else "A2_%s_%s.mov" % (sid, eff)
            extra = {"source": "%s @ %.2f s" % (sh["src"], sh["t"]), "effet": eff, "temps": nb}
            if sh.get("speed"): extra.update({"speed_pct": sh["speed"], "retime": "optical_flow"})
            add("%s_%d" % (sid, a), clip, 0, n, a, "shot", extra)
    add("fin", "A2_aura_fin.mov", 0, fr(END) - CUTF[-1], CUTF[-1], "card")
    plan = {"name": "A2 - Aura N&B - Manuel Bompard", "fps": FPS, "w": W, "h": H, "duree_s": END,
            "note": "Plans 9:16 recadrés + étalonnés N&B (gen/A2/out). s/e en images du clip (30 i/s), rec en images timeline 30 i/s. "
                    "speed_pct : ralenti Resolve Optical Flow + Speed Warp (e - s = durée timeline à vitesse normale). "
                    "Coupes sur les frappes réelles de Kaaris - Zoo mesurées dans la musique posée (out/A2-frappes.json) : drop = 1er kick de la prod lourde "
                    "(clic du kick à 50,22 s du complet = 3,808 s timeline, image 114), extrait continu du morceau (rap dès 51,50 s du complet = 5,09 s timeline, aucun raccord) ; "
                    "temps = 0,476 s (126 BPM) ; aucun plan < 1 temps ; zooms terminés sur la frappe de sortie.",
            "phrase": PH["texte"], "video": video,
            "audio": [{"id": "mix", "clip": "A2-mix.wav", "folder": "genA2", "rec": 0, "track": 1,
                       "note": "mix -14 LUFS : voix synchrone 1,47-3,85 s + musique de 0 à la fin (complet lu dès %.3f s, ducking -7 dB sous la voix)" % MUSIC_IN}],
            "stems": ["lot2/_claude/gen/A2/out/A2-voix.wav", "lot2/_claude/gen/A2/out/A2-musique.wav"],
            "musique": {"fichier": "lot2/" + SON["fichier_complet"], "frappes_timeline_s": [h[0] for h in HITS], "coupes_frappes_s": CUTS,
                        "extrait": "continu", "titre": "%s - %s" % (SON["artiste"], SON["titre"]), "debut_complet_s": round(MUSIC_IN, 4),
                        "gain_db": MGAIN},
            "sources": {sid: {"fichier": "lot2/sources/" + v["src"], "t": v["t"], "pourquoi": v["why"]} for sid, v in SHOTS.items()},
            "sources_url": {SA: "youtube tknIilnZnYI (chaîne Manuel Bompard, Convention municipales LFI), offset_yt 440 s",
                            SB: "youtube tknIilnZnYI, offset_yt 105 s"}}
    json.dump(plan, open(D + "plan-A2.json", "w"), indent=1, ensure_ascii=False)
    return plan
# ---------------- audio ----------------
def make_audio():
    import soundfile as sf
    sr = 48000; N = int(END * sr)
    def dec(args):
        p = subprocess.run([FF, "-v", "error"] + args + ["-ac", "2", "-ar", str(sr), "-f", "f32le", "-"], capture_output=True)
        return np.frombuffer(p.stdout, np.float32).reshape(-1, 2).copy()
    def place(buf, x, t, gain_db=0, fin=0.0, fout=0.0):
        g = 10 ** (gain_db / 20); n = len(x); env = np.ones(n, np.float32)
        if fin: m = int(fin * sr); env[:m] = np.linspace(0, 1, m)
        if fout: m = int(fout * sr); env[-m:] *= np.linspace(1, 0, m)
        a = int(t * sr); b = min(N, a + n); buf[a:b] += x[:b - a] * env[:b - a, None] * g
    voix = np.zeros((N, 2), np.float32); mus = np.zeros((N, 2), np.float32)
    t_in, t_out = 44.62, 47.00                                    # « Oui, nous sommes candidats au pouvoir. » (44,78-46,84)
    v = dec(["-ss", "%.3f" % t_in, "-t", "%.3f" % (t_out - t_in), "-i", LOT + "/sources/" + SA])
    place(voix, v, INTRO + (t_in - T_LONG), +4, fin=0.06, fout=0.15)
    m = music_raw(sr)
    duck = np.ones(len(m), np.float32); g = 10 ** (-7 / 20)            # musique -7 dB sous la phrase, remontée pile au drop
    a0, a1, b0, b1 = [int(t * sr) for t in (1.20, 1.45, DROP - 0.06, DROP - 0.005)]
    duck[a0:a1] = np.linspace(1, g, a1 - a0); duck[a1:b0] = g; duck[b0:b1] = np.linspace(g, 1, b1 - b0)
    place(mus, m * duck[:, None], 0.0, MGAIN, fin=0.3, fout=0.6)
    sf.write(OUT + "A2-voix.wav", voix, sr, subtype="PCM_24"); sf.write(OUT + "A2-musique.wav", mus, sr, subtype="PCM_24")
    mix = voix + mus; sf.write(D + "tmp_mix.wav", mix, sr, subtype="FLOAT")
    r = subprocess.run([FF, "-hide_banner", "-i", D + "tmp_mix.wav", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    js = json.loads(r[r.rindex("{"):r.rindex("}") + 1])
    af = ("loudnorm=I=-14:TP=-1.5:LRA=11:measured_I=%s:measured_TP=%s:measured_LRA=%s:measured_thresh=%s:offset=%s:linear=true,"
          "aresample=48000" % (js["input_i"], js["input_tp"], js["input_lra"], js["input_thresh"], js["target_offset"]))
    subprocess.run([FF, "-v", "error", "-y", "-i", D + "tmp_mix.wav", "-af", af, "-c:a", "pcm_s24le", OUT + "A2-mix.wav"], check=True)
    os.remove(D + "tmp_mix.wav"); print("audio : mix avant normalisation", js["input_i"], "LUFS")
# ---------------- aperçu ffmpeg 540x960 ----------------
def apercu():
    plan = json.load(open(D + "plan-A2.json")); ins = []; fl = []
    for i, v in enumerate(plan["video"]):
        n = v["e"] - v["s"]; sp = v.get("speed_pct", 100) / 100
        ins += ["-i", OUT + v["clip"]]
        if sp < 1:   # ralenti simple pour l'aperçu seulement (Resolve fera l'Optical Flow)
            used = n * sp
            fl.append("[%d:v]trim=start_frame=%d:end_frame=%d,setpts=(PTS-STARTPTS)/%.4f,fps=30,trim=end_frame=%d,setpts=PTS-STARTPTS,scale=540:960,setsar=1[v%d]"
                      % (i, v["s"], v["s"] + math.ceil(used) + 1, sp, n, i))
        else:
            fl.append("[%d:v]trim=start_frame=%d:end_frame=%d,setpts=PTS-STARTPTS,scale=540:960,setsar=1[v%d]" % (i, v["s"], v["e"], i))
    k = len(plan["video"])
    fl.append("".join("[v%d]" % i for i in range(k)) + "concat=n=%d:v=1:a=0[v]" % k)
    ins += ["-i", OUT + "A2-mix.wav"]
    out = ROOT + "/preview/apercu-A2.mp4"          # dossier des aperçus (Luca, 26/10)
    subprocess.run([FF, "-v", "error", "-y"] + ins + ["-filter_complex", ";".join(fl), "-map", "[v]", "-map", "%d:a" % k,
                    "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "aac", "-b:a", "192k", "-shortest", out], check=True)
    print("aperçu", out)
if __name__ == "__main__":
    args = set(a for a in sys.argv[1:] if not a.startswith("only=")) or {"shots", "cards", "audio", "plan", "apercu"}
    only = [x for a in sys.argv[1:] if a.startswith("only=") for x in a.split("=", 1)[1].split(",")]
    if "shots" in args or only:
        for sid in (only or ["long"] + [e[0] for e in EDIT if e[0] != "aura"]): render_shot(sid)
        done = set()
        for sid, eff in EDIT:
            if eff in ("whip", "drop") and (not only or sid in only) and (sid, eff) not in done:
                entry_variant(sid, eff); done.add((sid, eff))
    if "cards" in args: make_cards()
    if "plan" in args: build_plan()
    if "audio" in args: make_audio()
    if "apercu" in args: apercu()
