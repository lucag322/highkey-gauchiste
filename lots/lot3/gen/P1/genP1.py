# P1 — Portrait couloir (inspi @caiden.agr), Antoine Léaument (lot 3), son « MONTAGEM TOMADA » (MXZI).
# Recette (fiche caiden.agr) : long plan-séquence caméra épaule en hook (voix diégétique, rythme lent), ici l'interview
# caméra épaule à la grève Ubisoft (aucune image de couloir de l'Assemblée exploitable : vlogs selfie, visage trop gros
# pour un 9:16 sans couper oreilles/cheveux),
# puis contextes enchaînés en coupes sèches (tribune, bureau/plateau, terrain), 2 coupes / 10 s, AUCUN texte, pas de
# traitement visuel lourd (étalonnage naturel chaud, palette #2B2B2B #8C7B6B #E8E0D4), 9:16 visage centré.
# Aperçu hors Resolve : plans ProRes 1080x1920 30 i/s (recadrés, poussée lente, étalonnés), mix -14 LUFS, aperçu 540x960.
# Usage : python genP1.py [plans] [audio] [apercu] [only=ID,ID]
import sys, os, json, subprocess
import numpy as np
ROOT = "/Users/luca.grousset/Movies/highkey-gauchiste"; LOT = ROOT + "/lot3"
sys.path.insert(0, ROOT + "/_claude/outils")
import framing
from framing import plan_views
from fx import crop_view, vignette, grain, gblur
FF = "/opt/homebrew/bin/ffmpeg"
D = LOT + "/_claude/gen/P1/"; OUT = D + "out/"; os.makedirs(OUT, exist_ok=True)
framing.ROOT = LOT; framing.CACHE = D + "cache"
W, H, TFPS = 1080, 1920, 30
SON = LOT + "/sons/P1-mxzi-montagem-tomada_complet.wav"

# ---------------- sources (extraits dans lot3/sources) ----------------
SRC = {
    "itw": dict(f="P1-leaument-interview-greve-2026-02.mp4", fps=60.0, yt="EA4uU-DL4uM", yt_in=62.0,
                desc="Point'n Think, « Interview de Antoine Léaument, député insoumis » (grève Ubisoft, 10/02/2026), caméra épaule"),
    "lcp": dict(f="P1-leaument-lcp-qag-2026-04.mp4", fps=25.0, yt="CwaWePGUP8w", yt_in=98.0,
                desc="LCP, questions au gouvernement 28/04/2026, debout dans l'hémicycle"),
    "bureau": dict(f="P1-leaument-bureau-2026-06.mp4", fps=24000 / 1001, yt="mvSD-5YHhlk", yt_in=486.0,
                   desc="chaîne officielle, « La campagne de la victoire ! » (13/06/2026), face caméra au bureau"),
    "chenu": dict(f="P1-leaument-lcp-chenu-2026-01b.mp4", fps=24000 / 1001, yt="5VJWCXdOKyg", yt_in=106.0,
                  desc="LCP, hémicycle 22/01/2026 (altercation avec Sébastien Chenu, RN), seul debout devant les bancs rouges"),
}
# zones source autorisées (sans logo, sans bandeau, sans visage voisin coupé)
B_FULL = (0, 0, 1920, 1080)
B_LCP = (560, 100, 1420, 850)      # LCP : voisine à gauche (x<560), collègue debout derrière (y<125), interprète LSF + chrono à droite (x>1440), bandeaux en bas (y>860)
B_CHENU = (0, 0, 1920, 1080)       # LCP 22/01 : logo en haut à droite, hors champ du recadrage (vérifié)
B_GREVE = (0, 0, 1740, 1080)       # Point'n Think : logo en haut à droite (x>1760, y<120), même logo sur l'interview

# ---------------- temps (frappes réelles, rythme/frappes.json) ----------------
FR = json.load(open(D + "rythme/frappes.json"))
MOFF = FR["MOFF"]                  # temps morceau = timeline + MOFF
DROP, C1, C2 = FR["coupes_tl"]     # entrée de la basse 808 (drop) puis 2 caisses claires fortes
END = 15.0                         # règle lot 3 : portrait couloir 15 s max
V = 5.28                           # voix : timeline = temps extrait interview - V
VOIX = (5.40, 13.12)               # « Et ça, c'est ce que les gros bonnets des boîtes comme Ubisoft n'ont pas l'air de comprendre, c'est que la richesse de leur entreprise, c'est pas eux, c'est pas le capital, c'est les salariés. »
PHRASE = "Et ça, c'est ce que les gros bonnets des boîtes comme Ubisoft n'ont pas l'air de comprendre, c'est que la richesse de leur entreprise, c'est pas eux, c'est pas le capital, c'est les salariés." 
def f30(t): return int(round(t * TFPS))

def S(i, a, b, src, t_in, hint, bnd, vh, z0, z1, fx="", note="", dx=()):
    return dict(id=i, a=a, b=b, src=src, t_in=t_in, hint=hint, bnd=bnd, vh=vh, z0=z0, z1=z1, fx=fx, note=note, dx=dx)
def shift_at(sh, t):
    # décalage horizontal doux du cadre (fraction de largeur) pour garder entiers les visages qui passent au bord : (t0, t1, dx) temps timeline, rampes 0,25 s
    d = 0.0
    for t0, t1, v in sh["dx"]:
        d += v * min(max((t - t0 + 0.25) / 0.25, 0), 1) * min(max((t1 + 0.25 - t) / 0.25, 0), 1)
    return d
SHOTS = [
    S("A", 0.0, DROP, "itw", V, (800, 260), B_GREVE, 1080, 1.0, 1.08, "", "hook : plan-séquence caméra épaule sans coupe (interview à la grève), phrase entière en voix synchro, poussée très lente"),
    S("B", DROP, C1, "chenu", 3.10, (900, 250), B_CHENU, 1080, 1.0, 1.05, "", "drop : seul debout dans l'hémicycle, il tient tête (22/01/2026)"),
    S("C", C1, C2, "lcp", 13.00, (1000, 260), B_LCP, 750, 1.0, 1.04, "", "debout dans l'hémicycle, micro, regard relevé (QAG 28/04/2026)"),
    S("D", C2, END, "bureau", 12.40, (960, 300), B_FULL, 1080, 1.0, 1.05, "fin", "face caméra au bureau, geste de la main ; fondu au noir 0,6 s",
      dx=[(12.45, END + 1, -0.08)]),
]
for sh in SHOTS:
    sh["rec"] = f30(sh["a"]); sh["dur"] = f30(sh["b"]) - sh["rec"]
    sh["clip"] = "P1_%s.mov" % sh["id"]
def zoom_at(sh, t):
    u = min(max((t - sh["a"]) / (sh["b"] - sh["a"]), 0), 1)
    return sh["z0"] + (sh["z1"] - sh["z0"]) * u      # poussée avant régulière (jamais de dézoom)

# ---------------- étalonnage « authentique » (naturel, chaud, noirs légèrement relevés) ----------------
VIG = None
def grade(img):
    global VIG
    x = np.clip((img - 0.015) * 1.04, 0, 1)
    x = x * x * (3 - 2 * x) * 0.22 + x * 0.78                           # contraste doux
    lum = x @ np.array([0.114, 0.587, 0.299], np.float32)
    x = lum[..., None] + (x - lum[..., None]) * 0.92                       # saturation un peu baissée
    x = x * np.array([0.965, 1.0, 1.03], np.float32)                       # BGR : chaud (bleu -3,5 %, rouge +3 %)
    x = 0.045 + x * (0.955 - 0.045 * 0.2)                                  # noirs relevés vers #2B2B2B, blancs crème
    if VIG is None: VIG = vignette(np.ones((H, W, 3), np.float32), strength=0.30, power=2.4)
    return grain(np.clip(x, 0, 1) * VIG, 0.010, 1.4)

# ---------------- rendu d'un plan ----------------
def read_frames(src, t, n):
    p = subprocess.Popen([FF, "-v", "error", "-ss", "%.4f" % t, "-i", LOT + "/sources/" + src, "-frames:v", str(n),
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
    src_i = lambda k: int(round(k * spd)); n_src = src_i(n - 1) + 1
    tl_t = lambda k: sh["a"] + k / TFPS
    views, ok = plan_views(s["f"], s0, n, sf, speed=spd, hint=sh["hint"], bounds=sh["bnd"], vh=sh["vh"], zoom=lambda k: zoom_at(sh, tl_t(k)),
                             shake=lambda k: (shift_at(sh, tl_t(k)), 0.0), top=0.16)
    frames = list(read_frames(s["f"], s0 / sf, n_src))
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
    v = fade(load(LOT + "/sources/" + SRC["itw"]["f"], VOIX[0], VOIX[1] - VOIX[0]), 0.03, 0.06)
    v = sosfilt(butter(2, 90, "high", fs=SR, output="sos"), v, axis=0).astype(np.float32)     # coupe le grondement (vent, foule)
    lv, _ = lufs(v); v *= db(-15 - lv)
    m = load(SON, MOFF, END)
    lm, _ = lufs(m[int(DROP * SR):]); m *= db(-14 - lm)
    t = np.arange(len(m)) / SR
    lo = sosfilt(butter(4, 450, "low", fs=SR, output="sos"), m, axis=0).astype(np.float32)   # sous la voix : morceau étouffé
    a = np.interp(t, [0, DROP - 0.05, DROP], [1, 1, 0])[:, None].astype(np.float32)
    mus = lo * db(-9) * a + m * (1 - a)                                                       # ducking : musique baissée sous la voix, reprend au drop
    mus *= (np.clip((END - t) / 1.2, 0, 1) ** 1.5)[:, None].astype(np.float32)              # fondu de fin avec l'image
    mus = fade(mus, 0.25, 0)
    mix[:len(mus)] += mus; i0 = int((VOIX[0] - V) * SR); mix[i0:i0 + len(v)] += v[:n - i0]
    tmp = OUT + "_tmp_mix.wav"; sf_write(tmp, mix); g = 0.0; li, _ = lufs(mix)
    for _ in range(4):
        g += -14.0 - li
        subprocess.run([FF, "-v", "error", "-y", "-i", tmp, "-af", "volume=%.2fdB,alimiter=limit=0.80:attack=3:release=60:level=false,aresample=192000,alimiter=limit=0.82:attack=1:release=40:level=false,aresample=48000" % g,
                        "-c:a", "pcm_s24le", OUT + "P1-mix.wav"], check=True)
        li, tp = lufs(load(OUT + "P1-mix.wav"))
        if abs(li + 14) < 0.3 and tp < -1.0: break
    os.remove(tmp)
    return "mix %.1f LUFS, true peak %.1f dBTP" % (li, tp)

# ---------------- plan-P1.json ----------------
def write_plan():
    vid = []
    for sh in SHOTS:
        s = SRC[sh["src"]]; used = sh["dur"] / TFPS
        vid.append({"id": sh["id"], "clip": sh["clip"], "folder": "P1", "path": OUT + sh["clip"], "s": 0, "e": sh["dur"], "clip_fps": TFPS,
                    "rec": sh["rec"], "dur": sh["dur"], "track": 1, "speed_pct": 100, "note": sh["note"],
                    "source": {"fichier": "lot3/sources/" + s["f"], "in_s": round(sh["t_in"], 3), "out_s": round(sh["t_in"] + used, 3),
                               "youtube": "https://youtu.be/%s?t=%d" % (s["yt"], int(s["yt_in"] + sh["t_in"])), "desc": s["desc"]},
                    "effets": "recadrage 9:16 suivi visage, poussée x%.2f -> x%.2f, étalonnage naturel chaud%s" % (sh["z0"], sh["z1"], ", fondu au noir 0,6 s cuit" if sh["fx"] == "fin" else ""),
                    "coupe_sur_frappe_s": round(sh["a"], 3)})
    plan = {"name": "P1 - Portrait couloir - Leaument", "fps": 30, "w": 1080, "h": 1920, "duree_s": END,
            "note": "Lot 3, recette caiden.agr (portrait couloir) : hook plan-séquence caméra épaule (interview grève) avec voix diégétique, puis tribune / bureau / terrain en coupes sèches sur les frappes réelles, aucun texte. Plans ProRes 9:16 30 i/s prêts, aucun ralenti (speed_pct 100). Générateur : lot3/_claude/gen/P1/genP1.py",
            "musique": {"fichier": "lot3/sons/P1-mxzi-montagem-tomada_complet.wav", "debut_extrait_s": round(MOFF, 3), "fin_extrait_s": round(MOFF + END, 3),
                        "drop_timeline_s": DROP, "coupes_timeline_s": [DROP, C1, C2], "sous_la_voix": "ducking : passe-bas 450 Hz -9 dB jusqu'au drop"},
            "phrase": {"source": "https://youtu.be/EA4uU-DL4uM?t=67 (67,4-75,1 s)", "texte": PHRASE,
                       "timeline_s": [round(VOIX[0] - V, 2), round(VOIX[1] - V, 2)]},
            "video": vid,
            "audio": [{"id": "mix", "clip": "P1-mix.wav", "folder": "P1", "path": OUT + "P1-mix.wav", "rec": 0, "track": 1,
                       "note": "mix final -14 LUFS : voix 0,12-7,84 s sur le break baissé (ducking), morceau plein au drop %.3f s, fondu de fin" % DROP}]}
    json.dump(plan, open(D + "plan-P1.json", "w"), indent=1, ensure_ascii=False)

# ---------------- aperçu ffmpeg 540x960 ----------------
def preview():
    out = ROOT + "/preview/apercu-P1.mp4"; args = [FF, "-v", "error", "-y"]; fl = []
    for i, sh in enumerate(SHOTS):
        args += ["-i", OUT + sh["clip"]]
        fl.append("[%d:v]trim=end_frame=%d,setpts=PTS-STARTPTS,scale=540:960,setsar=1[v%d]" % (i, sh["dur"], i))
    args += ["-i", OUT + "P1-mix.wav"]
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
