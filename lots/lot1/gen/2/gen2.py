# Style 2 — speech edit : plan de timeline + compos Fusion (cadre, sous-titres mot par mot, yeux qui brillent)
import sys, json, os, re
ROOT = "/Users/luca.grousset/Movies/highkey-gauchiste"
exec(open(ROOT + "/_claude/outils/compkit.py").read())
from PIL import ImageFont
FPS_SRC, FPS = 25, 30
IN = 5563                                   # 222,52 s
CUTS = [5563, 5570, 5685, 5807, 5841, 6027, 6094, 6239, 6513, 6685]
CROP_X0, CROP_W = 312, 1240                 # exclut le logo LCP (x<305) et le chrono (x>1560)
SCALE = 1080 / CROP_W; IMG_CY = 0.505       # image 1080x941, centre à 50,5 % (réf : 50,5 %)
FONT, STYLE = "Avenir Next", "Medium"
PIL_FONT = ImageFont.truetype("/System/Library/Fonts/Avenir Next.ttc", 100, index=5)
SUB_Y1, SUB_DY = 0.22, 0.042                # 1re ligne à 78 % du haut (réf), 2e ligne dessous
RED = "#E4002B"; WHITE = "#FFFFFF"
KEYWORDS = {"contrôle", "démissionnez"}
K_SIZE = float(sys.argv[1]) if len(sys.argv) > 1 else 0.572   # calibrage Text+ (em px = Size*1080*K)
# --- mots ---
d = json.load(open(ROOT + "/_claude/derush.json"))["styles"]["2"]["plans_retenus"][0]["words"]
toks = []
for w in d:
    t = w["w"]
    if toks and (t.startswith("'") or t.startswith("-")):
        toks[-1]["w"] += t; toks[-1]["end"] = w["end"]
    else:
        toks.append({"w": t, "start": w["start"], "end": w["end"]})
PROPER = {"Jeune", "Garde"}
for i, t in enumerate(toks):
    raw = t["w"]; t["punct"] = raw[-1] in ".,?!;:"
    s = raw.rstrip(".,?!;:")
    if s.split("'")[0] not in PROPER: s = s[0].lower() + s[1:]
    t["txt"] = s; t["red"] = s in KEYWORDS
MAXC = 20
# --- groupes : phrases coupées à la ponctuation / aux silences, puis en paquets de <= 4 mots équilibrés,
#     sans finir un paquet sur un mot-outil (le, de, et...)
import math
FUNC = {"le", "la", "les", "l'", "de", "des", "du", "un", "une", "et", "sur", "aux", "au", "qui", "que", "vos", "vous", "ce", "à", "dans", "je", "ne", "c'est", "ça"}
sents, cur = [], []
for i, t in enumerate(toks):
    cur.append(t); nxt = toks[i + 1] if i + 1 < len(toks) else None
    if t["punct"] or nxt is None or nxt["start"] - t["end"] > 0.35: sents.append(cur); cur = []
SIZES = {0: [4, 3, 4, 3], 4: [3, 2], 6: [4, 3, 4, 3], 13: [5, 3, 2, 2, 2, 4], 14: [4, 3]}   # découpage choisi à la main (sens)
groups = []
for si, snt in enumerate(sents):
    if si in SIZES and sum(SIZES[si]) == len(snt):
        acc = 0
        for z in SIZES[si]: groups.append(snt[acc:acc + z]); acc += z
        continue
    n = len(snt); k = math.ceil(n / 4); bounds = [round(n * j / k) for j in range(k + 1)]
    for j in range(1, k):
        while bounds[j] - 1 > bounds[j - 1] + 1 and snt[bounds[j] - 1]["txt"].lower() in FUNC: bounds[j] -= 1
    for j in range(k): groups.append(snt[bounds[j]:bounds[j + 1]])
EM_TARGET = None
# taille : « je dénonce monsieur » = 59 % de la largeur dans la réf
w_ref = PIL_FONT.getlength("je dénonce monsieur") / 100.0       # largeur par px d'em
EM = 0.59 * 1080 / w_ref                                        # em en px
SIZE = EM / (1080 * K_SIZE)
SPACE = PIL_FONT.getlength(" ") / 100 * EM
def layout(g):
    ls, line = [], []
    for u in g:
        cand = " ".join(x["txt"] for x in line + [u])
        if len(cand) > MAXC and line: ls.append(line); line = [u]
        else: line.append(u)
    ls.append(line)
    out = []
    for li, line in enumerate(ls):
        widths = [PIL_FONT.getlength(u["txt"]) / 100 * EM for u in line]
        tot = sum(widths) + SPACE * (len(line) - 1); x = (1080 - tot) / 2
        for u, wd in zip(line, widths):
            out.append((u, x / 1080, SUB_Y1 - li * SUB_DY)); x += wd + SPACE
    return out
# fenêtres d'affichage des groupes
for gi, g in enumerate(groups):
    nxt = groups[gi + 1][0]["start"] if gi + 1 < len(groups) else 1e9
    g_end = min(g[-1]["end"] + 0.25, nxt)
    for u in g: u["show_end"] = g_end
# --- plan timeline ---
def rec(src_frame): return round((src_frame - IN) / FPS_SRC * FPS)
plan = {"name": "2 - Speech edit", "fps": 30, "video": [], "audio": [
    {"id": "voix", "clip": "2-voix.wav", "folder": "gen2", "rec": 0, "track": 1}]}
plan["video"].append({"id": "S", "clip": "2-bompard-nunez-qag.mp4", "folder": "sources", "s": CUTS[0], "e": CUTS[-1], "rec": 0})
plan["video"].append({"id": "glow", "clip": "2_glow.mov", "folder": "gen2", "s": 0, "e": 46, "rec": 511, "track": 2, "composite": "COMPOSITE_SCREEN"})
json.dump(plan, open(ROOT + "/_claude/plan2.json", "w"), indent=1)
# --- compos ---
CD = ROOT + "/_claude/comps/2/"
def make_comps():
    tag = "0"; dp = CD + "def_0.comp"
    a, b = CUTS[0], CUTS[-1]; n = b - a
    bb = B("S", last=n - 1, w=1080, h=1920)
    bg = bb.bg("#000000"); src = Ref("MediaIn1")
    # E (Bompard, 233,64-241,08 s) : yeux qui brillent sur « vous démissionnez » + montée en tension
    e0, e1 = 5841 - a, 6027 - a
    xf = bb.xf(src, pivot=(782 / 1920, 1 - 373 / 1080), mb=False)
    bb.anim(xf, "Size", [(0, 1.0, "lin"), (e0, 1.0, "lin"), (e1 - 1, 1.12, "lin"), (e1, 1.0, "lin")]); src = xf
    cr = bb.node("Crop", "CR"); cr.link("Input", src.name)
    for k, v in (("XOffset", CROP_X0), ("YOffset", 0), ("XSize", CROP_W), ("YSize", 1080)): cr.set(k, v)
    m = bb.merge(bg, cr, size=SCALE, center=(0.5, IMG_CY))
    bb.anim(m, "Blend", [(0, 0.0, "lin"), (15, 1.0, "io")])      # fondu d'ouverture depuis le noir (réf)
    t0s = a / FPS_SRC
    for g in groups:
        for (u, x, y) in layout(g):
            tx = bb.text(u["txt"], font=FONT, style=STYLE, size=SIZE, hexc=RED if u["red"] else WHITE, center=(x, y), anchor="left")
            f_on = round((u["start"] - t0s) * FPS_SRC); f_off = min(round((u["show_end"] - t0s) * FPS_SRC), n)
            mm = bb.merge(m, tx)
            keys = [(0, 0.0, "lin"), (f_on - 1, 0.0, "lin"), (f_on, 1.0, "lin")]
            if f_off < n: keys += [(f_off - 1, 1.0, "lin"), (f_off, 0.0, "lin")]
            bb.anim(mm, "Blend", keys)
            m = mm
    write_clip_comp(bb, m, CD + "F_%s.comp" % tag, open(dp).read())
    return True
if __name__ == "__main__":
    os.makedirs(CD, exist_ok=True)
    make_comps()
    print([(i, len(x), " ".join(u["txt"] for u in x)) for i, x in enumerate(sents)])
    print("groupes", len(groups), "EM", round(EM, 1), "SIZE", round(SIZE, 4))
    for g in groups[:40]: print(round(g[0]["start"], 2), " | ".join(" ".join(u["txt"] for u, _, _ in [(u, 0, 0) for u in g]) for _ in [0]))
