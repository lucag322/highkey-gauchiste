# Style 5 — Phonk infographie (réf @nvidia.rtx.2060), version plein écran 9:16.
# Règles Luca : aucun plan < 1 temps (0,41 s), pas de flash 1-2 images, pas de dézoom ni saut de zoom (poussée lente seulement).
# Plans ProRes 1080x1920 recadrés (suivi visage Apple Vision), étalonnés, poussée lente cuite.
# AUCUN ralenti précalculé : le plan ralenti est livré à vitesse normale, "speed" + "retime": "optical_flow" dans plan5.json.
# usage : python gen5.py [stills]   (stills = planche de contrôle des cadrages seulement)
import sys, os, json, math, subprocess
import numpy as np, cv2
ROOT = "/Users/luca.grousset/Movies/highkey-gauchiste"
D = ROOT + "/_claude/gen/5"
sys.path.insert(0, ROOT + "/_claude/outils")
import framing
framing.CACHE = D + "/cache_faces"            # cache local au style 5
from fx import ease_out, crop_view, gblur, motion_blur, zoom_blur, grain
FF = "/opt/homebrew/bin/ffmpeg"
FPS = 30; W, H = 1080, 1920
BEAT = 60 / 145.0; DROP = 5.99                 # musique 5-eclipser_depuis-ref.wav
def fr(t): return int(round(t * FPS))
SD, VA, HU = "5-melenchon-saintdenis-smic.mp4", "1-melenchon-valence-amfis.mp4", "3-melenchon-huma-citation.mp4"
SFPS = {SD: 30, VA: 30, HU: 50}
NOWM = (0, 0, 1580, 1080)                      # exclut le filigrane MELENCHON2027.fr (x>1590, y<170) de SD et Valence
FULL = (0, 0, 1920, 1080)
# (id, source, t_in source s, mode, param, vh, fx, note)   mode: "face" -> param = indice (x,y) ; "fix" -> centre (x,y)
INTRO = [
    ("A1", SD, 119.0, "fix", (1000, 540), 1080, "push", "Mélenchon de dos face à la foule (voix : « Nous réparerons les dégâts »)"),
    ("A2", SD, 101.0, "fix", (1130, 540), 1080, "push", "place de Saint-Denis noire de monde"),
    ("A3", SD, 106.02, "fix", (960, 560), 1040, "push", "drapeaux, image d'origine synchrone de « passera à 1 700 euros »"),
]
POST = [  # durées en temps (noires) après le drop
    ("B1", SD, 137.3, "fix", (960, 560), 1080, "push+", 2, "DROP : foule immense devant l'hôtel de ville"),
    ("B2", VA, 56.5, "fix", (1100, 560), 1080, "push+", 2, "Valence : Mélenchon de dos sur la passerelle vers la scène"),
    ("B3", VA, 73.5, "fix", (700, 540), 1080, "push+", 1.5, "Valence : mer de drapeaux, foule"),
    ("B4", HU, 22.3, "face", (1150, 300), 1080, "push+", 1.5, "Fête de l'Huma : Mélenchon bras tendu"),
    ("B5", VA, 100.8, "fix", (900, 540), 1080, "push+", 1, "Valence : drapeaux violets"),
    ("B6", SD, 112.9, "face", (760, 330), 1080, "push", 2, "Saint-Denis : Mélenchon serré au pupitre"),
    ("HUD", None, 0, None, None, 0, "hud", 3, "insert hologramme SMIC / 1 700 €"),
    ("C1", VA, 66.5, "fix", (760, 560), 1080, "push+", 1.5, "Valence : drone, foule immense"),
    ("C2", HU, 256.5, "fix", (960, 540), 1080, "push+", 1.5, "Huma : chapiteau, foule"),
    ("C3", SD, 184.5, "fix", (700, 600), 1080, "push+", 1, "Saint-Denis : foule, arbres, drapeau au premier plan"),
    ("C4", HU, 124.55, "face", (1120, 300), 1080, "push+", 1, "Huma : Mélenchon bras ouvert"),
    ("C5", SD, 233.5, "fix", (900, 600), 1080, "push", 2, "Saint-Denis : foule vue de haut, immeubles"),
    ("C6", HU, 285.0, "fix", (960, 680), 800, "push+", 1, "Huma : mer de bras"),
    ("C7", VA, 157.0, "fix", (780, 560), 1080, "fin", 3, "FIN : Valence, Mélenchon de dos au pupitre face à la foule (ralenti 50 % Resolve)"),
]
SLOW = {"C7": 50}                               # % de vitesse, appliqué dans Resolve (Optical Flow)
def timeline():
    shots = []; a = 0
    for (i, (sid, src, t, mode, par, vh, fx, note)) in enumerate(INTRO):
        b = fr([1.852, 3.921, DROP][i])
        shots.append(dict(id=sid, src=src, t=t, mode=mode, par=par, vh=vh, fx=fx, note=note, rec=a, n=b - a)); a = b
    tb = DROP
    for (sid, src, t, mode, par, vh, fx, beats, note) in POST:
        tb += beats * BEAT; b = fr(tb)
        shots.append(dict(id=sid, src=src, t=t, mode=mode, par=par, vh=vh, fx=fx, note=note, rec=a, n=b - a)); a = b
    return shots, a
def grade(img):
    """couleurs naturelles, un peu de punch : courbe en S douce, saturation +12 %, netteté."""
    s = img * img * (3 - 2 * img); img = img * 0.65 + s * 0.35
    g = img.mean(axis=2, keepdims=True); img = g + (img - g) * 1.12
    img = img + 0.45 * (img - gblur(img, 1.6))
    return np.clip(img, 0, 1)
def read_frames(src, t, n, sfps):
    p = subprocess.run([FF, "-v", "error", "-ss", "%.4f" % t, "-i", ROOT + "/sources/" + src, "-frames:v", str(n),
                        "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True, check=True).stdout
    a = np.frombuffer(p, np.uint8); k = len(a) // (1920 * 1080 * 3)
    return a[:k * 1920 * 1080 * 3].reshape(k, 1080, 1920, 3)
def motion(sh, f, n):
    """Règle Luca : cadrage fixe ou poussée lente et continue dans un seul sens (jamais de saut de zoom ni de zoom arrière, pas de secousse)."""
    rate = {"push": 0.07, "push+": 0.10, "fin": 0.08}.get(sh["fx"], 0.07)
    return 1 + rate * f / max(n - 1, 1), (0.0, 0.0)
def render(sh, stills=False):
    src = sh["src"]; sfps = SFPS[src]; n = sh["n"]
    speed = sfps / FPS
    n_out = n     # ralenti éventuel : livré à vitesse normale, même durée (Resolve SetSpeed garde la durée et raccourcit la source)
    n_src = int(math.ceil(n_out * speed)) + 2
    s0 = int(round(sh["t"] * sfps))
    zf = lambda f: motion(sh, f, n_out)[0]; shf = lambda f: motion(sh, f, n_out)[1]
    bounds = NOWM if src in (SD, VA) else FULL
    if sh["mode"] == "face":
        views, ok = framing.plan_views(src, s0, n_out, sfps, speed=speed, hint=sh["par"], bounds=bounds, vh=sh["vh"], zoom=zf, shake=shf, top=0.16)
        if not ok: print("!! pas de visage", sh["id"])
    else:
        views, _ = framing.plan_views(src, s0, n_out, sfps, speed=speed, hint=sh["par"], bounds=bounds, vh=sh["vh"], zoom=zf, shake=shf, fixed=sh["par"])
    up = max([views[f][2] - views[f - 1][2] for f in range(1, len(views))] + [0])
    if up > 0.5: print("!! dézoom détecté", sh["id"], "+%.1f px" % up)
    idx = [min(int(round(f * speed)), n_src - 1) for f in range(n_out)]
    if stills:
        frames = read_frames(src, sh["t"], n_src, sfps)
        outs = []
        for f in sorted(set([0, n_out // 2, n_out - 1])):
            cx, cy, vh = views[f]; img = frames[min(idx[f], len(frames) - 1)].astype(np.float32) / 255
            outs.append(cv2.resize(grade(crop_view(img, cx, cy, vh * 9 / 16, W, H)), (180, 320)))
        return outs
    frames = read_frames(src, sh["t"], n_src, sfps)
    out = D + "/out/5_%s.mov" % sh["id"]
    enc = subprocess.Popen([FF, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", "%dx%d" % (W, H), "-r", str(FPS), "-i", "-",
                            "-c:v", "prores_ks", "-profile:v", "3", "-pix_fmt", "yuv422p10le", "-vendor", "apl0", out], stdin=subprocess.PIPE)
    prev = None
    for f in range(n_out):
        cx, cy, vh = views[f]; cw = vh * 9 / 16
        img = frames[min(idx[f], len(frames) - 1)].astype(np.float32) / 255
        img = crop_view(img, cx, cy, cw, W, H)
        if prev is not None:      # flou de mouvement = vitesse du cadre
            pcx, pcy, pvh = prev; m = W / cw
            vx = (cx - pcx) * m; vy = (cy - pcy) * m
            if abs(vx) + abs(vy) > 6: img = motion_blur(img, -vx * 0.9, -vy * 0.9)
            zr = abs(pvh / vh - 1)
            if zr > 0.015: img = zoom_blur(img, min(zr * 1.6, 0.12))
        prev = (cx, cy, vh)
        img = grade(img)
        img = grain(img, 0.012)
        enc.stdin.write((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8).tobytes())
    enc.stdin.close(); enc.wait()
    return out, n_out
def job(sh):
    out, n_out = render(sh); return sh["id"], n_out
if __name__ == "__main__":
    shots, total = timeline()
    os.makedirs(D + "/out", exist_ok=True)
    work = [s for s in shots if s["fx"] != "hud" and (len(sys.argv) < 3 or s["id"] in sys.argv[2:])]
    if len(sys.argv) > 1 and sys.argv[1] == "stills":
        tiles = []
        for s in work:
            ims = render(s, stills=True)
            row = np.hstack(ims + [np.zeros((320, 180, 3), np.float32)] * (3 - len(ims)))
            row = (np.clip(row, 0, 1) * 255).astype(np.uint8)
            cv2.putText(row, s["id"], (6, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)
            tiles.append(row)

        rows = [np.hstack(tiles[i:i + 3] + [np.zeros_like(tiles[0])] * (3 - len(tiles[i:i + 3]))) for i in range(0, len(tiles), 3)]
        cv2.imwrite(D + "/chk/stills.jpg", np.vstack(rows)); print("stills ok"); sys.exit()
    from multiprocessing import Pool
    with Pool(6) as p: done = dict(p.map(job, work))
    json.dump({"shots": shots, "total": total, "n_out": done}, open(D + "/shots.json", "w"), indent=1, ensure_ascii=False, default=str)
    print("ok", len(work), "plans, total", total, "images")
