# Page de journal générique sur l'« Aura » (texte encyclopédique, attribué à personne) — fond du style 6
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np, random, json
random.seed(6)
SUP = "/System/Library/Fonts/Supplemental/"
F_HEAD = ImageFont.truetype(SUP + "Rockwell.ttc", 120, index=2)   # Rockwell Bold
F_BODY = ImageFont.truetype(SUP + "Verdana.ttf", 64)
F_BODY_B = ImageFont.truetype(SUP + "Verdana Bold.ttf", 64)
F_CRUMB = ImageFont.truetype(SUP + "Verdana.ttf", 40)
W, H = 5400, 9000
INK = (38, 33, 28); GREY = (120, 110, 100); HL = (242, 212, 58)
img = Image.new("RGB", (W, H), (230, 220, 200)); d = ImageDraw.Draw(img)
blocks = [
 ("Bien-être / Esprit / Énergie", "Comprendre le concept d'Aura",
  "En physique comme en spiritualité, l'Aura est décrite comme un champ d'énergie subtil qui entoure un être vivant. Selon cette idée, l'Aura refléterait l'état émotionnel, mental et spirituel de chacun."),
 ("Société / Tendances", "L'Aura : nouvelle obsession des réseaux",
  "Sur les réseaux, avoir de l'Aura signifie dégager une présence, un charisme que l'on ne peut pas imiter. Une bonne Aura se gagne par des actes, une mauvaise Aura se perd en une seule phrase."),
 ("Accueil / Dossiers", "Mesurer son Aura : mode d'emploi",
  "Les adeptes affirment que l'Aura change de couleur selon l'humeur. Pour les sceptiques, l'Aura n'est qu'une métaphore : celle de l'impression que l'on laisse aux autres."),
 ("Esprit / Lexique", "Votre Aura : la métaphore du charisme",
  "Le mot Aura vient du grec et désigne un souffle léger. Aujourd'hui, l'Aura décrit surtout la façon dont une personne est perçue, admirée ou moquée."),
 ("Culture / Mots du moment", "Aura : définition et origines",
  "Dans le langage courant, perdre son Aura, c'est perdre la face. Gagner de l'Aura, c'est marquer les esprits. L'Aura se construit lentement et peut disparaître en un instant."),
]
hl_boxes = []
def draw_words(x0, y, text, font, fontb, maxw, lh):
    x = x0
    for w in text.split(" "):
        core = w.strip(".,:;")
        is_aura = core in ("Aura", "l'Aura", "d'Aura") or core.endswith("Aura")
        f = fontb if is_aura else font
        ww = d.textlength(w + " ", font=f)
        if x + d.textlength(w, font=f) > x0 + maxw: x = x0; y += lh
        if is_aura:
            # surligne seulement le mot Aura
            pre = w[:w.index("Aura")]; xa = x + d.textlength(pre, font=f); wa = d.textlength("Aura", font=f)
            bb = (xa - 10, y - 6, xa + wa + 10, y + lh * 0.82)
            d.rectangle(bb, fill=HL); hl_boxes.append([int(v) for v in bb])
        d.text((x, y), w, font=f, fill=INK)
        x += ww
    return y + lh
y = 1200
for crumb, head, body in blocks + blocks[::-1][1:]:
    d.text((1180, y), crumb, font=F_CRUMB, fill=GREY); y += 90
    # titre (Aura du titre surligné aussi)
    y = draw_words(1180, y, head, F_HEAD, F_HEAD, 3040, 150) + 40
    y = draw_words(1180, y, body, F_BODY, F_BODY_B, 3040, 104) + 130
print("hauteur utilisée", y)
img = img.crop((0, 0, W, min(H, y + 1200)))
a = np.asarray(img).astype(np.float32)
# texture papier : bruit basse fréquence + grain
rng = np.random.default_rng(6)
lf = Image.fromarray((rng.random((img.size[1] // 40, img.size[0] // 40)) * 255).astype(np.uint8)).resize(img.size, Image.BICUBIC).filter(ImageFilter.GaussianBlur(30))
lf = (np.asarray(lf).astype(np.float32) / 255 - 0.5)[..., None]
a = a * (1 + 0.10 * lf) + rng.normal(0, 4, a.shape)
Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).save("page.png")
json.dump({"size": img.size, "hl": hl_boxes}, open("page.json", "w"))
print(img.size, len(hl_boxes), hl_boxes[:6])
