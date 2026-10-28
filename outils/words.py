# Mots du dérush -> jetons d'affichage, mise en page par mot (mesures PIL de la même police que Fusion)
from PIL import ImageFont
def tokens(words, kstart="start", kend="end"):
    toks = []
    for w in words:
        t = w["w"]; s = w.get(kstart, w.get("s")); e = w.get(kend, w.get("e"))
        if toks and (t.startswith("'") or t.startswith("-") or toks[-1]["w"] in ("«",)):
            sep = "" if (t.startswith("'") or t.startswith("-")) else " "
            toks[-1]["w"] += sep + t; toks[-1]["end"] = e
        else:
            toks.append({"w": t, "start": s, "end": e})
    # « collé au mot suivant ; » collé au précédent
    out = []
    for t in toks:
        if t["w"].startswith("»") and out: out[-1]["w"] += " »"; out[-1]["end"] = t["end"]; continue
        out.append(t)
    for t in out:
        t["punct"] = t["w"].rstrip("»").rstrip()[-1:] in ".,?!;:"
    return out
def clean(s, keep_quotes=True):
    s = s.replace(",", "").replace(".", "").replace("?", "").replace("!", "").replace(";", "").replace(":", "")
    if not keep_quotes: s = s.replace("«", "").replace("»", "")
    return " ".join(s.split())
class Layout:
    def __init__(self, font_path, index, em_px, frame_w=1080, tracking=0.0):
        self.f = ImageFont.truetype(font_path, 200, index=index); self.em = em_px; self.W = frame_w; self.tr = tracking
    def width(self, s):
        return self.f.getlength(s) / 200 * self.em + self.tr * self.em * max(len(s) - 1, 0)
    def line(self, words, y, cx=0.5):
        """words = textes ; renvoie [(texte, x_gauche_norm, y)] pour une ligne centrée."""
        sp = self.width(" ") if not self.tr else self.f.getlength(" ") / 200 * self.em + self.tr * self.em
        ws = [self.width(w) for w in words]; tot = sum(ws) + sp * (len(words) - 1)
        x = cx * self.W - tot / 2; out = []
        for w, wd in zip(words, ws):
            out.append((w, x / self.W, y)); x += wd + sp + (self.tr * self.em if self.tr else 0)
        return out
