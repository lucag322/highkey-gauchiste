# Cartons de texte lisibles : mots qui apparaissent au mot près, ombre portée noire + halo coloré DERRIÈRE les lettres.
# exec après compkit (utilise B, Node, hexrgb...). EMK = px d'em par unité de Size (comp 1080 de large).
from words import Layout
def text_cards(bb, base, cards, t0s, fps, n, font_path, font_index, font, style, glow_hex, em_max=150, y=0.62,
               width_frac=0.88, EMK=617.8, W=1080, white="#FFFFFF", red="#E4002B", glow_size=10.0, shadow=True, red_font=None):
    """red_font = (chemin, index, famille, style[, dy_em]) : police dramatique pour les mots rouges (règle Luca).
    dy_em = recalage vertical mesuré sur un rendu (Text+ ne place pas la ligne de base comme PIL), négatif = plus bas."""
    from PIL import ImageFont
    fb = ImageFont.truetype(font_path, 200, index=font_index)
    fr = ImageFont.truetype(red_font[0], 200, index=red_font[1]) if red_font else fb
    # Text+ dimensionne la police sur (ascendante + descendante) : EMK est calibré sur Avenir (1,37 em).
    def asz(f): a, d = f.getmetrics(); return (a + d) / 200.0
    def bl(f): a, d = f.getmetrics(); return (a - d) / 2 / 200.0      # ligne de base sous le centre, en em
    REF_A = 1.37
    """cards = [{"words": [(txt, t_start, is_red)], "end": t_end}] en secondes source ; n = nb d'images du comp."""
    lay_c = bb.bg("#000000", alpha=0.0); lay_g = bb.bg("#000000", alpha=0.0); cnt = 0
    for cd in cards:
        if cd["end"] <= t0s or cd["words"][0][1] >= t0s + n / fps: continue
        txts = [w[0] for w in cd["words"]]
        fonts = [fr if w[2] else fb for w in cd["words"]]
        wid1 = [f.getlength(t) / 200 for f, t in zip(fonts, txts)]; sp1 = fb.getlength(" ") / 200
        em = min(em_max, width_frac * W / (sum(wid1) + sp1 * (len(txts) - 1)))
        f_off = round((cd["end"] - t0s) * fps)
        x = W / 2 - em * (sum(wid1) + sp1 * (len(txts) - 1)) / 2; pos = []
        for wd in wid1: pos.append(x / W); x += em * (wd + sp1)
        for txt, x, (_, ts, is_red) in zip(txts, pos, cd["words"]):
            fobj = fr if (is_red and red_font) else fb
            yy = y + (bl(fobj) - bl(fb)) * em / 1920
            if is_red and red_font and len(red_font) > 4: yy += red_font[4] * em / 1920
            f_on = max(round((ts - t0s) * fps), 0)
            keys = [(0, 0.0, "lin")]
            if f_on > 0: keys += [(f_on - 1, 0.0, "lin")]
            keys += [(f_on, 1.0, "lin")]
            if f_off < n: keys += [(f_off - 1, 1.0, "lin"), (f_off, 0.0, "lin")]
            for which in ("c", "g"):
                col = (red if is_red else white) if which == "c" else glow_hex
                fam, sty = (red_font[2], red_font[3]) if (is_red and red_font) else (font, style)
                tx = bb.text(txt, font=fam, style=sty, size=em / EMK * asz(fobj) / REF_A, hexc=col, center=(x, yy), anchor="left")
                if which == "c":
                    lay_c = bb.merge(lay_c, tx); bb.anim(lay_c, "Blend", keys)
                else:
                    lay_g = bb.merge(lay_g, tx); bb.anim(lay_g, "Blend", keys)
            cnt += 1
    if not cnt: return base
    # halo extérieur lumineux (2 flous, le large boosté) DERRIÈRE les lettres
    g1 = bb.node("Blur", "GLB"); g1.link("Input", lay_g.name); g1.set("XBlurSize", glow_size * 2.4)
    g1b = bb.node("BrightnessContrast", "GLG"); g1b.link("Input", g1.name); g1b.set("Gain", 2.2)
    g2 = bb.node("Blur", "GLB"); g2.link("Input", lay_g.name); g2.set("XBlurSize", glow_size * 0.8)
    g2b = bb.node("BrightnessContrast", "GLG"); g2b.link("Input", g2.name); g2b.set("Gain", 1.6)
    m = bb.merge(base, g1b); m = bb.merge(m, g2b)
    if shadow:   # contour sombre serré pour la lisibilité
        sh = bb.node("BrightnessContrast", "SHC"); sh.link("Input", lay_g.name); sh.set("Gain", 0.0)
        sb = bb.node("Blur", "SHB"); sb.link("Input", sh.name); sb.set("XBlurSize", 2.2)
        m = bb.merge(m, sb); m = bb.merge(m, sb); m = bb.merge(m, sb)
    return bb.merge(m, lay_c)
