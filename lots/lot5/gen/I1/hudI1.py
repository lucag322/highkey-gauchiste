# I1 — inserts « hologramme » et étiquettes de données (réf @nvidia.rtx.2060 10,0-11,25 s), adaptés du prototype lot1/_claude/gen/5/hud5.py
# (lu, pas modifié). Tous les textes dans la zone sûre TikTok (x 0,17-0,83 ; y 0,12-0,75). Apparition par balayage, sortie sèche sur la coupe.
# Chiffres : seulement ceux dits par Mélenchon (1 700 €, Saint-Denis 7/06/2026) et le SMIC net officiel (1 477,93 €, service-public.gouv.fr, 1/06/2026).
import sys, os, numpy as np, cv2
sys.path.insert(0, "/Users/luca.grousset/Movies/highkey-gauchiste/_claude/outils")
from fx import gblur, rgb_split, grain, ease_out, vignette
from PIL import Image, ImageDraw, ImageFont
W, H = 1080, 1920
TEAL = np.array([208, 214, 63], np.float32) / 255       # BGR de #3FD6D0 (hologramme de la réf)
BG = np.array([28, 24, 14], np.float32) / 255           # #0E181C
RED = np.array([0x2B, 0x00, 0xE4], np.float32) / 255     # BGR de #E4002B
FB = "/System/Library/Fonts/Supplemental/DIN Condensed Bold.ttf"; FA = "/System/Library/Fonts/Supplemental/DIN Alternate Bold.ttf"
_fc = {}
def F(path, px):
    k = (path, int(px))
    if k not in _fc: _fc[k] = ImageFont.truetype(path, int(px))
    return _fc[k]
X0, X1 = int(0.19 * W), int(0.81 * W)                    # bornes des textes (marge sur la zone sûre 0,17-0,83)

def proj(p, ang, tilt, cam=5.2, f=1250, cx=W / 2, cy=H * 0.40):
    x, y, z = p; ca, sa = np.cos(ang), np.sin(ang)
    x, z = x * ca + z * sa, -x * sa + z * ca
    t = np.radians(tilt); y, z = y * np.cos(t) - z * np.sin(t), y * np.sin(t) + z * np.cos(t)
    s = f / (cam + z); return (cx + x * s, cy - y * s)
def P(a): return tuple(int(round(v)) for v in a)

def frame_hud(lay_lines, hud_txt):
    """fond sombre + couche de traits (lay, 0..1) en teal avec halo + couche texte PIL (L) en teal."""
    img = np.zeros((H, W, 3), np.float32) + BG
    glow = gblur(lay_lines, 12) * 1.5 + gblur(lay_lines, 4) * 0.7
    img = img + (lay_lines + glow)[..., None] * TEAL
    t = np.asarray(hud_txt).astype(np.float32) / 255
    return img + (t + gblur(t, 6))[..., None] * TEAL

def corners(d, top=150, bot=H - 330, m=60, L=90):
    for (x, y, sx, sy) in ((m, top, 1, 1), (W - m, top, -1, 1), (m, bot, 1, -1), (W - m, bot, -1, -1)):
        d.line((x, y, x + sx * L, y), fill=200, width=4); d.line((x, y, x, y + sy * L), fill=200, width=4)
    for yy in range(top + 110, bot - 90, 40): d.line((m, yy, m + (22 if yy % 200 == 60 else 10), yy), fill=120, width=2)

def red_number(img, txt, y, px, k, sub=None):
    """chiffre rouge #E4002B révélé gauche -> droite en 5 images, contour sombre, halo rouge ; sous-ligne teal."""
    pil = Image.new("L", (W, H), 0); dd = ImageDraw.Draw(pil)
    dd.text((W / 2, y), txt, font=F(FB, px), fill=255, anchor="mm")
    mask = np.asarray(pil).astype(np.float32) / 255
    wx = int(W * (0.15 + 0.75 * ease_out((k + 1) / 5))); mask[:, wx:] = 0
    st = cv2.dilate(mask, np.ones((15, 15), np.uint8))
    img = img * (1 - st[..., None] * 0.85)
    img = img + gblur(mask, 22)[..., None] * RED * 1.1
    img = img * (1 - mask[..., None]) + mask[..., None] * RED
    yl = int(y + px * 0.47); w = int(330 * ease_out((k - 1) / 8))
    if w > 0: img[yl:yl + 5, W // 2 - w:W // 2 + w] = TEAL
    if sub and k >= 3:
        pil = Image.new("L", (W, H), 0); dd = ImageDraw.Draw(pil)
        dd.text((W / 2, yl + 34), sub, font=F(FA, 30), fill=int(230 * min(1, (k - 2) / 3)), anchor="mm")
        t = np.asarray(pil).astype(np.float32) / 255; img = img + (t + gblur(t, 4) * 0.6)[..., None] * TEAL
    return img

# ---------- HUD1 : pièce € filaire qui tourne + étiquette SMIC + « 1 700 € » au moment où il le dit ----------
def hud1(i, n, reveal):
    """i image du plan, reveal = image où « mille sept cents » commence (révélation du chiffre)."""
    lay = np.zeros((H, W), np.float32)
    tilt = 16 + 40 * ease_out(i / max(n - 1, 1)) * 0.5     # légère plongée progressive (pas de saut)
    ang = -0.6 + i * 0.035
    for k in range(-10, 11):
        cv2.line(lay, P(proj((k * 0.45, -1.4, -4.5), 0, tilt)), P(proj((k * 0.45, -1.4, 4.5), 0, tilt)), 0.28, 1, cv2.LINE_AA)
        cv2.line(lay, P(proj((-4.5, -1.4, k * 0.45), 0, tilt)), P(proj((4.5, -1.4, k * 0.45), 0, tilt)), 0.28, 1, cv2.LINE_AA)
    R = 1.15; th = np.linspace(0, 2 * np.pi, 96)
    for zz in (-0.14, 0.14):
        pts = np.array([P(proj((R * np.cos(t), R * np.sin(t), zz), ang, tilt)) for t in th], np.int32)
        cv2.polylines(lay, [pts], True, 1.0, 3, cv2.LINE_AA)
        pts = np.array([P(proj((R * 0.86 * np.cos(t), R * 0.86 * np.sin(t), zz), ang, tilt)) for t in th], np.int32)
        cv2.polylines(lay, [pts], True, 0.55, 1, cv2.LINE_AA)
    for t in th[::4]:
        cv2.line(lay, P(proj((R * np.cos(t), R * np.sin(t), -0.14), ang, tilt)), P(proj((R * np.cos(t), R * np.sin(t), 0.14), ang, tilt)), 0.6, 1, cv2.LINE_AA)
    eu = [P(proj((0.62 * np.cos(t) + 0.08, 0.62 * np.sin(t), 0.15), ang, tilt)) for t in np.linspace(0.8, 2 * np.pi - 0.8, 48)]
    cv2.polylines(lay, [np.array(eu, np.int32)], False, 1.0, 5, cv2.LINE_AA)
    for yy in (-0.13, 0.13):
        cv2.line(lay, P(proj((-0.72, yy, 0.15), ang, tilt)), P(proj((0.18, yy, 0.15), ang, tilt)), 1.0, 5, cv2.LINE_AA)
    rev = ease_out((i + 1) / 5); cut = int(H * 0.75 * rev); lay[cut:] = 0
    if rev < 1: lay[max(cut - 4, 0):cut] = 1.0
    hud = Image.new("L", (W, H), 0); d = ImageDraw.Draw(hud); corners(d)
    if i >= 3:                                            # étiquette SMIC reliée à la pièce
        a = min(1.0, (i - 2) / 3); cxy = proj((R * 0.7, R * 0.7, 0.14), ang, tilt)
        bx, by, bw, bh = int(W * 0.56), int(H * 0.145), 260, 96
        d.rectangle((bx, by, bx + bw, by + bh), outline=int(255 * a), width=4)
        d.text((bx + bw / 2, by + bh / 2 + 4), "SMIC", font=F(FA, 64), fill=int(255 * a), anchor="mm")
        d.line((bx, by + bh, int(cxy[0]), int(cxy[1])), fill=int(220 * a), width=3)
        d.ellipse((int(cxy[0]) - 9, int(cxy[1]) - 9, int(cxy[0]) + 9, int(cxy[1]) + 9), outline=int(255 * a), width=3)
    img = frame_hud(lay, hud)
    if i >= reveal: img = red_number(img, "1 700 €", H * 0.655, 250, i - reveal, "J.-L. MÉLENCHON - SAINT-DENIS - 07/06/2026")
    img[::4] *= 0.88
    img = vignette(img, 0.45)
    return grain(np.clip(img, 0, 1), 0.015)

# ---------- HUD2 : deux colonnes filaires (SMIC net aujourd'hui / 1 700 €), axe depuis 0 ----------
def box_edges(lay, x0, x1, z0, z1, h, ang, tilt, val):
    c = [(x, y, z) for x in (x0, x1) for y in (-1.4, -1.4 + h) for z in (z0, z1)]
    E = [(0, 1), (2, 3), (4, 5), (6, 7), (0, 2), (1, 3), (4, 6), (5, 7), (0, 4), (1, 5), (2, 6), (3, 7)]
    for a, b in E: cv2.line(lay, P(proj(c[a], ang, tilt, cy=H * 0.47)), P(proj(c[b], ang, tilt, cy=H * 0.47)), val, 3, cv2.LINE_AA)
    for k in range(1, 8):                                  # graduations horizontales sur la face avant
        yy = -1.4 + h * k / 8
        cv2.line(lay, P(proj((x0, yy, z1), ang, tilt, cy=H * 0.47)), P(proj((x1, yy, z1), ang, tilt, cy=H * 0.47)), val * 0.35, 1, cv2.LINE_AA)
def hud2(i, n):
    lay = np.zeros((H, W), np.float32); red = np.zeros((H, W), np.float32)
    tilt = 12; ang = -0.32 + i * 0.012
    for k in range(-10, 11):
        cv2.line(lay, P(proj((k * 0.45, -1.4, -4.5), 0, tilt, cy=H * 0.47)), P(proj((k * 0.45, -1.4, 4.5), 0, tilt, cy=H * 0.47)), 0.25, 1, cv2.LINE_AA)
        cv2.line(lay, P(proj((-4.5, -1.4, k * 0.45), 0, tilt, cy=H * 0.47)), P(proj((4.5, -1.4, k * 0.45), 0, tilt, cy=H * 0.47)), 0.25, 1, cv2.LINE_AA)
    HMAX = 3.1                                            # 1 700 € = HMAX ; 1 477,93 € = HMAX x 0,869 (axe depuis 0)
    g1 = ease_out((i + 1) / 7); g2 = ease_out((i - 2) / 7)
    box_edges(lay, -1.05, -0.25, -0.4, 0.4, HMAX * 1477.93 / 1700 * g1, ang, tilt, 1.0)
    if i >= 3: box_edges(red, 0.25, 1.05, -0.4, 0.4, HMAX * g2, ang, tilt, 1.0)
    hud = Image.new("L", (W, H), 0); d = ImageDraw.Draw(hud); corners(d)
    top1 = proj((-0.65, -1.4 + HMAX * 1477.93 / 1700 * g1, 0.4), ang, tilt, cy=H * 0.47)
    top2 = proj((0.65, -1.4 + HMAX * max(g2, 0), 0.4), ang, tilt, cy=H * 0.47)
    base1 = proj((-0.65, -1.4, 0.4), ang, tilt, cy=H * 0.47); base2 = proj((0.65, -1.4, 0.4), ang, tilt, cy=H * 0.47)
    a1 = min(1, (i + 1) / 4)
    d.text((top1[0], top1[1] - 105), "1 477,93 €", font=F(FB, 84), fill=int(255 * a1), anchor="mm")
    d.text((base1[0], base1[1] + 44), "SMIC NET", font=F(FA, 38), fill=int(235 * a1), anchor="mm")
    d.text((base1[0], base1[1] + 86), "AUJOURD'HUI", font=F(FA, 30), fill=int(200 * a1), anchor="mm")
    if i >= 4:
        a2 = min(1, (i - 3) / 3)
        d.text((base2[0], base2[1] + 44), "MÉLENCHON", font=F(FA, 38), fill=int(235 * a2), anchor="mm")
        d.text((base2[0], base2[1] + 86), "SAINT-DENIS", font=F(FA, 30), fill=int(200 * a2), anchor="mm")
    d.text((W / 2, H * 0.715), "SMIC NET 35 H - SERVICE-PUBLIC.GOUV.FR - 1ER JUIN 2026", font=F(FA, 26), fill=int(170 * a1), anchor="mm")
    rev = ease_out((i + 1) / 5); cut = int(H * 0.75 * rev); lay[cut:] = 0; red[cut:] = 0
    img = frame_hud(lay, hud)
    img = img + (red + gblur(red, 10) * 1.4)[..., None] * RED
    if i >= 4:                                            # chiffre rouge au-dessus de la 2e colonne
        pil = Image.new("L", (W, H), 0); dd = ImageDraw.Draw(pil)
        dd.text((top2[0], top2[1] - 110), "1 700 €", font=F(FB, 110), fill=255, anchor="mm")
        m = np.asarray(pil).astype(np.float32) / 255
        wx = int(top2[0] - 200 + 400 * ease_out((i - 3) / 4)); m[:, wx:] = 0
        st = cv2.dilate(m, np.ones((11, 11), np.uint8)); img = img * (1 - st[..., None] * 0.85)
        img = img + gblur(m, 16)[..., None] * RED; img = img * (1 - m[..., None]) + m[..., None] * RED
    img[::4] *= 0.88
    img = vignette(img, 0.45)
    return grain(np.clip(img, 0, 1), 0.015)

# ---------- étiquette de donnée posée sur le B-roll ----------
def label(img, k, title, sub, box_y, dot, red_title=False):
    """Cadre teal + titre + source, relié par un trait à un point de l'image (dot, px sortie). Balayage 4 images."""
    a = ease_out((k + 1) / 4)
    lay = Image.new("L", (W, H), 0); d = ImageDraw.Draw(lay)
    ft = F(FB, 92); fs = F(FA, 28)
    tw = max(ft.getlength(title), fs.getlength(sub)) + 60; bw = min(tw, X1 - X0); bx = W / 2 - bw / 2; bh = 150
    by = box_y
    d.rectangle((bx, by, bx + bw * a, by + bh), outline=255, width=4)
    for (x, y, sx, sy) in ((bx - 10, by - 10, 1, 1), (bx + bw + 10, by - 10, -1, 1), (bx - 10, by + bh + 10, 1, -1), (bx + bw + 10, by + bh + 10, -1, -1)):
        if a > 0.5: d.line((x, y, x + sx * 30, y), fill=255, width=3); d.line((x, y, x, y + sy * 30), fill=255, width=3)
    if k >= 2:
        sy0 = by + bh; ex = dot[0] if dot else None
        if dot:
            px = dot[0] * 0.0 + (bx + bw / 2); d.line((px, sy0, px, sy0 + (dot[1] - sy0) * a), fill=220, width=3)
            d.line((px, dot[1], dot[0], dot[1]), fill=220, width=3)
            d.ellipse((dot[0] - 11, dot[1] - 11, dot[0] + 11, dot[1] + 11), outline=255, width=4)
    txt = Image.new("L", (W, H), 0); dt = ImageDraw.Draw(txt)
    if k >= 1:
        dt.text((W / 2, by + 60), title, font=ft, fill=255, anchor="mm")
        dt.text((W / 2, by + 122), sub, font=fs, fill=225, anchor="mm")
    L = np.asarray(lay).astype(np.float32) / 255; T = np.asarray(txt).astype(np.float32) / 255
    wx = int(bx + (bw + 40) * a) + 1; T[:, wx:] = 0
    # fond sombre translucide derrière le cadre pour la lisibilité
    sh = np.zeros((H, W), np.float32); sh[int(by):int(by + bh), int(bx):int(bx + bw * a)] = 0.62
    img = img * (1 - gblur(sh, 6)[..., None])
    img = img + (L + gblur(L, 5) * 1.2)[..., None] * TEAL
    col = RED if red_title else np.array([1, 1, 1], np.float32)
    img = img * (1 - T[..., None]) + T[..., None] * col
    img = img + gblur(T, 8)[..., None] * TEAL * 0.35
    return img
