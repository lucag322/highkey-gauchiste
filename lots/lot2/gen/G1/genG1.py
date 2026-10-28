# Lot 2 / G1 — Glow, Louis Boyard (audition à l'Assemblée, 29/04/2026). Copie de la structure de _claude/gen/4/gen4.py (validé par Luca)
# et du pipeline d'aperçu de lot2/_claude/gen/C2/genC2.py.
# Phrase réelle mot à mot (4,15-8,60 s), cartons Avenir Next Bold Italic TOUT EN BLANC + halo ambre (mur, bois, cheveux de la source)
# + contour sombre ; musique Apocalypse (Cigarettes After Sex) du début à la fin, entrée de la batterie juste après « c'est vous ».
# Ralentis : PAS précalculés. Clip livré à vitesse normale (n = durée_tl × fps_source), speed_pct + retime dans plan-G1.json.
# Usage : python genG1.py [plans] [audio] [apercu] [only=ID,ID]
import sys, os, json, subprocess
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
HK = "/Users/luca.grousset/Movies/highkey-gauchiste"
L2 = HK + "/lot2"
sys.path.insert(0, HK + "/_claude/outils")
import framing
framing.ROOT = L2; framing.CACHE = L2 + "/_claude/cache/faces"          # sources du lot 2
from framing import plan_views
from fx import crop_view, gblur, over
from words import tokens, clean
FF = "/opt/homebrew/bin/ffmpeg"
D = L2 + "/_claude/gen/G1/"; OUT = D + "out/"; os.makedirs(OUT, exist_ok=True)
W, H, TFPS = 1080, 1920, 30
LUT = HK + "/_claude/luts/s4_rose.cube"                                # même étalonnage que le test 4
FONT = ("/System/Library/Fonts/Avenir Next.ttc", 1)                     # Avenir Next Bold Italic
GLOW_RGB = (242, 182, 90)                                              # ambre : mur #5B4C39, bois #99663E, cheveux #6E4A34 (teinte 22-34°), saturé
GLOW = np.array(GLOW_RGB[::-1], np.float32) / 255                       # images en BGR
SRC = {"A": "G1-boyard-an-santementale-2026-04.mp4"}
SFPS = {"A": 25}
# bornes sans logo : LFI en haut à gauche (x < 260), AN en haut à droite (x 1570-1760, y < 190) ; voisin coupé au bord gauche (x < 230)
B_A = (260, 0, 1560, 1080)
HINT = (1310, 260)

# ---------------- temps ----------------
MUSIC = L2 + "/sons/G1-cas-apocalypse_complet.wav"
V0, VOUT = 4.15, 8.60                    # phrase (dérush G1) : « Le problème … c'est vous. » (dernier mot fini à 8,44)
C_DRUM = 14.02                           # entrée batterie mesurée (librosa : énergie < 150 Hz x200 à 14,0 s du morceau complet)
DROP = 4.50                              # timeline : la batterie tombe 0,06 s après « vous. »
C_OFF = C_DRUM - DROP                    # musique : timeline = complet - C_OFF
CUTS_C = [14.02, 15.395, 16.718, 18.088, 19.412, 20.735, 22.036, 24.056]   # temps mesurés (92,3 BPM), coupes tous les 2 temps
def tc(c): return c - C_OFF
END = tc(CUTS_C[-1])                     # 14,54 s (max 15 s)
def f30(t): return int(round(t * TFPS))

# ---------------- texte (mot à mot du dérush, derush-AG.json) ----------------
G = [f for f in json.load(open(L2 + "/_claude/derush-AG.json"))["figures"].values() if f.get("figure") == "Louis Boyard"][0]
PH = G["phrase"]
T = tokens(PH["mots"])
def up(w): return clean(w, keep_quotes=False).replace("'", "’").upper()
SIZES = [2, 3, 1, 2, 2, 1, 2, 2, 2]      # LE PROBLÈME | DE LA SANTÉ | MENTALE | DES JEUNES | C’EST PAS | TIKTOK | LE PROBLÈME | DES JEUNES | C’EST VOUS
assert sum(SIZES) == len(T), (len(T), [t["w"] for t in T])
CARDS, i = [], 0
for z in SIZES:
    CARDS.append({"words": [(up(t["w"]), t["start"] - V0) for t in T[i:i + z]]}); i += z
for k, c in enumerate(CARDS): c["end"] = CARDS[k + 1]["words"][0][1] if k + 1 < len(CARDS) else DROP
EM_MAX, WFRAC, YC = 150, 0.88, 0.60      # comme le test 4 (y Fusion 0,40 = 60 % depuis le haut)
_F = {}
def font(px):
    px = int(round(px))
    if px not in _F: _F[px] = ImageFont.truetype(FONT[0], px, index=FONT[1])
    return _F[px]
_L = {}
def layer(ci, nv):
    """Couches (masque lettres) du carton ci avec ses nv premiers mots, mise en page du carton complet (pas de saut)."""
    key = (ci, nv)
    if key in _L: return _L[key]
    words = [w[0] for w in CARDS[ci]["words"]]
    f100 = font(100); sp = f100.getlength(" ") / 100
    tot = sum(f100.getlength(w) / 100 for w in words) + sp * (len(words) - 1)
    em = min(EM_MAX, WFRAC * W / tot); f = font(em)
    asc, desc = f.getmetrics(); cap = f.getbbox("H")
    y_top = YC * H - (cap[1] + cap[3]) / 2                       # centre des capitales à 60 % de la hauteur
    m = Image.new("L", (W, H), 0); dr = ImageDraw.Draw(m)
    x = W / 2 - em * tot / 2
    for k, w in enumerate(words):
        if k < nv: dr.text((x, y_top), w, font=f, fill=255)
        x += f.getlength(w) + f.getlength(" ")
    a = np.asarray(m, np.float32) / 255
    g1 = np.clip(gblur(a, 16) * 2.2, 0, 1); g2 = np.clip(gblur(a, 5) * 1.6, 0, 1)   # halo large + halo serré
    sh = 1 - (1 - np.clip(gblur(a, 2.0) * 1.0, 0, 1)) ** 3                          # contour sombre serré
    _L[key] = (a, g1, g2, sh); return _L[key]
def draw_text(img, t):
    for ci, c in enumerate(CARDS):
        if c["words"][0][1] <= t < c["end"]:
            nv = sum(1 for w in c["words"] if w[1] <= t)
            a, g1, g2, sh = layer(ci, nv)
            img = over(img, GLOW, g1); img = over(img, GLOW, g2)
            img = over(img, np.zeros(3, np.float32), sh)
            return over(img, np.ones(3, np.float32), a)
    return img

# ---------------- étalonnage : LUT s4_rose (dans ffmpeg) + SoftGlow (seuil 0,6, gain 0,7) comme le test 4 ----------------
def grade(img, nb=False):
    lum = img @ np.array([0.114, 0.587, 0.299], np.float32)
    hi = img * np.clip((lum - 0.6) / 0.4, 0, 1)[..., None]
    img = img + 0.7 * gblur(hi, 14)
    if nb:
        y = img @ np.array([0.114, 0.587, 0.299], np.float32)
        img = np.repeat(y[..., None], 3, 2) * 0.62
    return img

# ---------------- plans ----------------
def S(i, a, b, t_in, sp, z0, z1, nb=False, txt=False, fixed=None, note=""):
    return dict(id=i, a=a, b=b, src="A", t_in=t_in, sp=sp, z0=z0, z1=z1, nb=nb, txt=txt, fixed=fixed, note=note)
C = [tc(c) for c in CUTS_C]
# poings levés (117-125 s) écartés : poing à x 600-750, visage à x 1050-1300, impossible en 9:16 sans couper le visage
SHOTS = [
    S("A", 0.0, DROP, V0, 100, 1.0, 1.1, txt=True, note="phrase en synchro, plan frontal au pupitre, poussée lente, cartons mot à mot"),
    S("B1", C[0], C[1], 54.2, 50, 1.02, 1.08, note="entrée batterie : bras levé haut, regard intense"),
    S("B2", C[1], C[2], 65.6, 100, 1.02, 1.07, note="geste de la main, rythme"),
    S("B3", C[2], C[3], 85.9, 50, 1.02, 1.08, note="temps fort : face caméra, main levée"),
    S("B4", C[3], C[4], 75.6, 100, 1.02, 1.07, note="index levé (Parcoursup)"),
    S("B5", C[4], C[5], 9.3, 50, 1.0, 1.06, nb=True, note="temps fort, N&B : main qui s'élève"),
    S("B6", C[5], C[6], 46.9, 100, 1.02, 1.07, note="geste puis regard levé"),
    S("B7", C[6], END, 39.8, 50, 1.0, 1.06, note="regard caméra, ralenti, fondu au noir"),
]
FADE_ID, FADE_S = "B7", 0.9
for sh in SHOTS:
    sh["rec"] = f30(sh["a"]); sh["dur"] = f30(sh["b"]) - sh["rec"]
    fps = SFPS[sh["src"]]; sh["fps"] = fps
    sh["n"] = int(round(sh["dur"] / TFPS * fps))
    sh["clip"] = "G1_%s.mov" % sh["id"]

def read_frames(src, t, n):
    p = subprocess.Popen([FF, "-v", "error", "-ss", "%.4f" % t, "-i", L2 + "/sources/" + SRC[src], "-frames:v", str(n),
                          "-vf", "lut3d=file='%s'" % LUT, "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE)
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
    n, fps = sh["n"], sh["fps"]; w = writer(OUT + sh["clip"], fps)
    s = int(round(sh["t_in"] * fps)); z0, z1 = sh["z0"], sh["z1"]; bd = B_A
    zoom = lambda f: z0 + (z1 - z0) * f / max(n - 1, 1)
    vh = min(1080, bd[3] - bd[1], (bd[2] - bd[0]) * 16 / 9)
    views, ok = plan_views(SRC[sh["src"]], s, n, fps, speed=1.0, hint=sh["fixed"] or HINT, bounds=bd, vh=vh, zoom=zoom, top=0.16, fixed=sh["fixed"])
    info = ("fixe " if sh["fixed"] else "") + ("visage" if ok else "SANS VISAGE")
    k = 0; vmin = 9e9
    for fr in read_frames(sh["src"], s / fps, n):
        cx, cy, v = views[min(k, len(views) - 1)]; vw = v * 9 / 16; vmin = min(vmin, v)
        assert bd[0] - 1 <= cx - vw / 2 and cx + vw / 2 <= bd[2] + 1 and bd[1] - 1 <= cy - v / 2 and cy + v / 2 <= bd[3] + 1, (sh["id"], k, cx, cy, v)
        img = grade(crop_view(fr.astype(np.float32) / 255, cx, cy, vw, W, H), sh["nb"])
        if sh["txt"]: img = draw_text(img, sh["a"] + k / fps)
        w.stdin.write((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8).tobytes()); k += 1
    w.stdin.close(); w.wait()
    info += " vue min %d px (agrandi x%.2f)" % (vmin, 1920 / vmin)
    if k < n: info += " court:%d/%d" % (k, n)
    return info

# ---------------- audio ----------------
SR = 48000
def load(path, t=0.0, d=None):
    cmd = [FF, "-v", "error", "-ss", "%.4f" % t, "-i", path] + (["-t", "%.4f" % d] if d else []) + ["-vn", "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"]
    return np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, np.float32).reshape(-1, 2).copy()
def fade(x, fi, fo):
    a = np.ones(len(x), np.float32)
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
    n = int(round(END * SR)); mix = np.zeros((n, 2), np.float32)
    v = fade(load(L2 + "/sources/" + SRC["A"], V0, VOUT - V0), 0.02, 0.08)
    mus = load(MUSIC, C_OFF, END + 0.05)[:n]
    lv, _ = lufs(v); lm, _ = lufs(mus[int(DROP * SR):])
    v *= db(-14 - lv); mus *= db(-14 - lm)                       # voix -14 LUFS ; musique après la batterie -14 LUFS
    t = np.arange(len(mus)) / SR
    env = np.where(t < DROP - 0.03, db(-9), 1.0).astype(np.float32)   # guitare d'intro nettement sous la voix, plein à la batterie
    env *= np.clip(t / 0.15, 0, 1)
    env *= np.where(t > END - 1.1, np.clip((END - t) / 1.1, 0, 1) ** 1.5, 1)
    mix[:len(mus)] += mus * env[:, None]; mix[:len(v)] += v
    tmp = OUT + "_tmp_mix.wav"; sf_write(tmp, mix); g = 0.0; li2 = None
    for _ in range(3):
        li = lufs(mix)[0] if li2 is None else li2
        g += -14.0 - li
        subprocess.run([FF, "-v", "error", "-y", "-i", tmp, "-af", "volume=%.2fdB,alimiter=limit=0.80:attack=3:release=60:level=false,aresample=192000,alimiter=limit=0.82:attack=1:release=40:level=false,aresample=48000" % g,
                        "-c:a", "pcm_s24le", OUT + "G1-mix.wav"], check=True)
        li2, tp2 = lufs(load(OUT + "G1-mix.wav"))
        if abs(li2 + 14) < 0.3 and tp2 < -1.0: break
    os.remove(tmp)
    sf_write(OUT + "G1-voix.wav", v); sf_write(OUT + "G1-musique.wav", mus)
    return "mix %.1f LUFS, true peak %.1f dBTP (voix %.1f, musique %.1f d'origine)" % (li2, tp2, lv, lm)

# ---------------- plan-G1.json ----------------
def write_plan():
    vid = []
    for sh in SHOTS:
        sp = sh["sp"]; used = sh["n"] * sp / 100 / sh["fps"]
        it = {"id": sh["id"], "clip": sh["clip"], "folder": "genG1", "path": OUT + sh["clip"], "s": 0, "e": sh["n"], "clip_fps": sh["fps"],
              "rec": sh["rec"], "dur": sh["dur"], "track": 1, "note": sh["note"],
              "source": {"fichier": "lot2/sources/" + SRC[sh["src"]], "in_s": round(sh["t_in"], 3), "out_s": round(sh["t_in"] + used, 3)},
              "effets": "recadrage 9:16 %s (bornes %s, logos exclus), poussée %.2f->%.2f, LUT s4_rose + SoftGlow%s%s" % (
                  "fixe centre %s" % (sh["fixed"],) if sh["fixed"] else "suivi visage", list(B_A), sh["z0"], sh["z1"], ", N&B" if sh["nb"] else "", ", cartons cuits" if sh["txt"] else "")}
        if sp != 100: it["speed_pct"] = sp; it["retime"] = "optical_flow"
        if sh["id"] == FADE_ID: it["fade_out_s"] = FADE_S
        vid.append(it)
    src = [s for s in G["sources"] if s["fichier"].endswith(SRC["A"])][0]
    plan = {"name": "G1 - Glow - Boyard", "fps": 30, "w": 1080, "h": 1920, "duree_s": round(END, 3),
            "note": "Plans ProRes 9:16 prêts (recadrés hors logos, étalonnés, cartons cuits sur A). Ralentis à faire dans Resolve : speed_pct + Optical Flow ; e-s = images source à vitesse normale. Générateur : lot2/_claude/gen/G1/genG1.py",
            "phrase": {"texte": PH["texte"], "fichier": "lot2/sources/" + SRC["A"], "in_s": V0, "out_s": VOUT, "source_url": src["url"], "chaine": src["chaine"], "date": src["date"]},
            "musique": {"titre": "Apocalypse", "artiste": "Cigarettes After Sex", "fichier": "lot2/sons/G1-cas-apocalypse_complet.wav",
                        "debut_dans_complet_s": round(C_OFF, 3), "batterie_timeline_s": DROP, "coupes_timeline_s": [round(c, 3) for c in C]},
            "textes": {"police": "Avenir Next Bold Italic", "couleur": "blanc", "halo": "#%02X%02X%02X" % GLOW_RGB, "contour": "sombre",
                       "cartons": [{"t0": round(c["words"][0][1], 2), "t1": round(c["end"], 2), "texte": " ".join(w[0] for w in c["words"])} for c in CARDS]},
            "video": vid,
            "audio": [{"id": "mix", "clip": "G1-mix.wav", "folder": "genG1", "path": OUT + "G1-mix.wav", "rec": 0, "track": 1,
                       "note": "mix -14 LUFS : voix 4,15-8,60 s (fondus 20/80 ms) + musique complet %.2f-%.2f s, intro -9 dB sous la voix, batterie à %.2f s, fondu de fin 1,1 s" % (C_OFF, C_OFF + END, DROP)}]}
    json.dump(plan, open(D + "plan-G1.json", "w"), indent=1, ensure_ascii=False)

# ---------------- aperçu ffmpeg 540×960 (ralentis simples setpts) ----------------
def preview():
    out = L2 + "/exports/apercu-G1.mp4"; args = [FF, "-v", "error", "-y"]; fl = []
    for i, sh in enumerate(SHOTS):
        args += ["-i", OUT + sh["clip"]]
        fl.append("[%d:v]setpts=(PTS-STARTPTS)/%.4f,fps=30,trim=end_frame=%d,setpts=PTS-STARTPTS,scale=540:960,setsar=1%s[v%d]" % (
            i, sh["sp"] / 100, sh["dur"], ",fade=t=out:st=%.3f:d=%.2f" % (sh["dur"] / 30 - FADE_S, FADE_S) if sh["id"] == FADE_ID else "", i))
    args += ["-i", OUT + "G1-mix.wav"]
    fl.append("".join("[v%d]" % i for i in range(len(SHOTS))) + "concat=n=%d:v=1:a=0[v]" % len(SHOTS))
    args += ["-filter_complex", ";".join(fl), "-map", "[v]", "-map", "%d:a" % len(SHOTS), "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p",
             "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out]
    subprocess.run(args, check=True)
    return out

if __name__ == "__main__":
    only = None
    for a in sys.argv:
        if a.startswith("only="): only = a[5:].split(",")
    if "plans" in sys.argv:
        for sh in SHOTS:
            if only and sh["id"] not in only: continue
            print(sh["id"], "%.2f-%.2f" % (sh["a"], sh["b"]), sh["dur"], "img tl", sh["n"], "img src", render(sh), flush=True)
    if "audio" in sys.argv: print(build_audio())
    write_plan()
    if "apercu" in sys.argv: print(preview())
    print("total %.2f s ; %d plans ; batterie %.2f" % (END, len(SHOTS), DROP))
