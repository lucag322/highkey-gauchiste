# Style 4 — glow (réf @lbn7182), plein écran 9:16 : phrase forte de Boyard (51,72-57,12 s, entière) en cartons lisibles, puis rafales sur la musique
import sys, json, os
ROOT = "/Users/luca.grousset/Movies/highkey-gauchiste"
sys.path.insert(0, ROOT + "/_claude/outils")
exec(open(ROOT + "/_claude/outils/compkit.py").read())
exec(open(ROOT + "/_claude/outils/cards.py").read())
from framing import plan_views, merge_keys
from words import tokens, clean
LUT = ROOT + "/_claude/luts/s4_rose.cube"
A = "4-boyard-franceinfo-duel-a.mp4"; Bf = "4-boyard-franceinfo-duel-b.mp4"; Cn = "4-boyard-cnews-debat.mp4"
FS = 25; GLOW = "#A58BE8"        # violet pris dans le décor du plateau franceinfo (palette de la source)
PANEL_A = (966, 135, 1920, 825); PANEL_B = (0, 132, 630, 795); CNEWS = (0, 20, 1920, 800)   # bornes sans bandeaux
FONT = ("/System/Library/Fonts/Avenir Next.ttc", 1, "Avenir Next", "Bold Italic")
# ---- cartons (mots réels, au mot près) ----
d = [w for w in json.load(open(ROOT + "/_claude/derush.json"))["styles"]["4"]["plans_retenus"][0]["words"] if w["start"] >= 51.8]
toks = tokens(d)
SIZES = [3, 2, 3, 3, 2, 1, 2, 2, 2, 2]    # QUE VOUS SOYEZ | DE GAUCHE | OU DE DROITE | JE PENSE QUE | VOUS DEVRIEZ | ALLER | POUR DÉFENDRE | CES ADOLESCENTS | QUI RISQUENT | LEUR VIE
KEY = {"ADOLESCENTS", "RISQUENT", "LEUR", "VIE"}
assert sum(SIZES) == len(toks)
cards, i = [], 0
for z in SIZES:
    g = toks[i:i + z]; i += z
    cards.append({"words": [(clean(t["w"]).upper(), t["start"], clean(t["w"]).upper() in KEY) for t in g]})
for k, c in enumerate(cards): c["end"] = cards[k + 1]["words"][0][1] if k + 1 < len(cards) else 57.1
# ---- plan ----
IN_A, OUT_A = 1293, 1428
plan = {"name": "4 - Glow", "fps": 30, "video": [{"id": "A", "clip": A, "folder": "sources", "s": IN_A, "e": OUT_A, "rec": 0}], "audio": [
    {"id": "voix", "clip": "4-voix.wav", "folder": "gen4", "rec": 0, "track": 1},
    {"id": "musique", "clip": "4-musique.wav", "folder": "gen4", "rec": 162, "track": 2}]}
CUTS = [162, 181, 218, 255, 273, 310, 348, 385, 403, 432]     # coupes sur les temps (97 BPM, 1 temps = 18,6 images), aucun plan < 1 temps
SHOTS = [(A, 96.0, (1500, 300), PANEL_A, 1.0, "nb"),          # N&B sur le 1er temps fort de la musique (0,63 s)
         (Bf, 36.0, (1500, 300), PANEL_A, 0.5, "ralenti"), (A, 112.0, (1500, 300), PANEL_A, 0.5, "zoom"),
         (Bf, 2.0, (320, 330), PANEL_B, 1.0, "zoom"), (A, 26.0, (1500, 300), PANEL_A, 0.5, "ralenti"),
         (A, 22.0, (1480, 290), PANEL_A, 1.0, "zoom"), (Bf, 8.0, (320, 330), PANEL_B, 0.5, "zoom"),
         (Bf, 56.0, (1500, 300), PANEL_A, 1.0, "zoom"), (A, 64.0, (1500, 300), PANEL_A, 0.5, "fin")]
for k, (a, b) in enumerate(zip(CUTS, CUTS[1:])):
    src, ts, face, bnd, sp, fx = SHOTS[k]
    if src is None: continue
    n_src = int((b - a) / 30 * FS + 0.999); s = round(ts * FS)
    plan["video"].append({"id": "B%d" % k, "clip": src, "folder": "sources", "s": s, "e": s + n_src, "rec": a,
                          "face": face, "bounds": bnd, "speed": sp, "fx": fx, **({"speed_pct": sp * 100} if sp < 1 else {})})
json.dump(plan, open(ROOT + "/_claude/plan4.json", "w"), indent=1)
CD = ROOT + "/_claude/comps/4/"
def graded(bb, glow=0.5, speed=1.0, n=0):     # ralenti : SetSpeed + Optical Flow dans Resolve (build.py), rien dans Fusion
    src = Ref("MediaIn1")
    lut = bb.node("FileLUT", "LUT"); lut.link("Input", src.name); lut.set("LUTFile", LUT)
    sg = bb.node("SoftGlow", "SG"); sg.link("Input", lut.name)
    for k, v in (("Threshold", 0.6), ("Gain", glow), ("XGlowSize", 20.0)): sg.set(k, v)
    return sg
def placed(bb, img, views):
    bg = bb.bg("#000000"); m = bb.merge(bg, img)
    sk, ck = merge_keys(views); bb.anim(m, "Size", sk); bb.anim_xy(m, "Center", ck); return m
def flash(bb, base, keys, color="#FFFFFF"):
    w = bb.bg(color); m = bb.merge(base, w); bb.anim(m, "Blend", keys); return m
def ramp(keys):
    def z(f):
        for (f0, v0), (f1, v1) in zip(keys, keys[1:]):
            if f0 <= f <= f1: t = (f - f0) / max(f1 - f0, 1); return v0 + (v1 - v0) * (1 - (1 - t) ** 3)
        return keys[-1][1]
    return z
def comp_A():
    dp = CD + "def_0.comp"
    if not os.path.exists(dp): return
    n = OUT_A - IN_A; bb = B("A", last=n - 1, w=1080, h=1920)
    f1 = round((53.20 - 51.72) * FS); f2 = round((54.82 - 51.72) * FS)
    zoom = ramp([(0, 1.0), (n - 1, 1.1)])      # poussée lente continue, aucun saut
    views, _ = plan_views(A, IN_A, n, FS, hint=(1490, 300), bounds=PANEL_A, vh=690, zoom=zoom, top=0.14)
    m = placed(bb, graded(bb), views)
    m = text_cards(bb, m, cards, IN_A / FS, FS, n, FONT[0], FONT[1], FONT[2], FONT[3], GLOW, em_max=150, y=0.40,
                   red="#FFFFFF")   # retour Luca : tout en blanc, police unique, aucun mot rouge
    write_clip_comp(bb, m, CD + "F_0.comp", open(dp).read())
def comp_B(v):
    dp = CD + "def_%d.comp" % v["rec"]
    if not os.path.exists(dp): return
    import re as _re
    rr = _re.search(r"RenderRange = \{ (-?\d+), (-?\d+) \}", open(dp).read()); n = int(rr.group(2)) - int(rr.group(1)) + 1
    bb = B("B%d" % v["rec"], last=n - 1, w=1080, h=1920); fx = v["fx"]
    comp_speed = 1.0     # comp en images source ; Resolve ralentit APRÈS Fusion (Optical Flow)
    bnd = v["bounds"]; vh = bnd[3] - bnd[1]
    zoom = {"zoom": ramp([(0, 1.0), (n - 1, 1.06)]), "flash_in": ramp([(0, 1.0), (n - 1, 1.06)]),
            "ralenti": ramp([(0, 1.0), (n - 1, 1.08)]), "fin": ramp([(0, 1.0), (n - 1, 1.08)])}.get(fx, ramp([(0, 1.03), (n - 1, 1.07)]))
    views, _ = plan_views(v["clip"], v["s"], n, FS, speed=comp_speed, hint=tuple(v["face"]), bounds=tuple(bnd), vh=vh, zoom=zoom, top=0.16)
    img = graded(bb, glow=0.7 if fx != "nb" else 0.3, speed=v["speed"], n=n)
    if fx == "nb":
        bc = bb.node("BrightnessContrast", "BC"); bc.link("Input", img.name); bc.set("Saturation", 0.0); bc.set("Gain", 0.45); img = bc
    m = placed(bb, img, views)
    if fx == "flou":   # balayage : tout le cadre glisse avec flou de mouvement (entrée / sortie)
        xf = bb.xf(m); bb.anim_xy(xf, "Center", [(0, (0.75, 0.5), "lin"), (4, (0.5, 0.5), "out"), (n - 5, (0.5, 0.5), "lin"), (n - 1, (0.3, 0.5), "in")]); m = xf
    if fx == "flash_in": m = flash(bb, m, [(0, 1.0, "lin"), (3, 0.0, "out")])
    if fx == "fin": m = flash(bb, m, [(0, 0.0, "lin"), (n - 13, 0.0, "lin"), (n - 1, 1.0, "lin")], "#000000")
    write_clip_comp(bb, m, CD + "F_%d.comp" % v["rec"], open(dp).read())
if __name__ == "__main__":
    comp_A()
    for v in plan["video"][1:]: comp_B(v)
    print("ok", [" ".join(w[0] for w in c["words"]) for c in cards])
