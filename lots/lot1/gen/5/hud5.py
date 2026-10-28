# Insert « hologramme » 9:16 (réf @nvidia.rtx.2060 10,0-11,25 s) : fond sombre, grille, pièce € filaire teal qui tourne,
# deux angles (profil puis vue plongeante, comme le porte-avions de la réf), étiquette « SMIC », chiffre « 1 700 € » en rouge.
# Textes = mots de la phrase de Mélenchon seulement. Pas de flash : apparition par balayage, sortie sèche sur la coupe.
import sys, os, numpy as np, cv2
sys.path.insert(0, "/Users/luca.grousset/Movies/highkey-gauchiste/_claude/outils")
from fx import gblur, rgb_split, grain, ease_out, vignette
from PIL import Image, ImageDraw, ImageFont
D = os.path.dirname(os.path.abspath(__file__))
W, H = 1080, 1920; N = int(sys.argv[1]) if len(sys.argv) > 1 else 37
TEAL = np.array([208, 214, 63], np.float32) / 255       # BGR de #3FD6D0
BG = np.array([28, 24, 14], np.float32) / 255           # #0E181C
RED = (0xE4, 0x00, 0x2B)
FB = "/System/Library/Fonts/Supplemental/DIN Condensed Bold.ttf"; FA = "/System/Library/Fonts/Supplemental/DIN Alternate Bold.ttf"
F_BIG = ImageFont.truetype(FB, 300); F_LAB = ImageFont.truetype(FA, 64); F_SM = ImageFont.truetype(FA, 30)
CUT2 = 19                                                # changement d'angle (1,5 temps)
def proj(p, ang, tilt, cam=5.2, f=1250, cx=W / 2, cy=H * 0.40):
    x, y, z = p; ca, sa = np.cos(ang), np.sin(ang)
    x, z = x * ca + z * sa, -x * sa + z * ca
    t = np.radians(tilt); y, z = y * np.cos(t) - z * np.sin(t), y * np.sin(t) + z * np.cos(t)
    s = f / (cam + z); return (cx + x * s, cy - y * s)
def P(a): return tuple(int(round(v)) for v in a)
def frame(i):
    img = np.zeros((H, W, 3), np.float32) + BG
    lay = np.zeros((H, W), np.float32)
    second = i >= CUT2
    tilt = 62 if second else 16
    ang = (0.45 + (i - CUT2) * 0.025) if second else (-0.6 + i * 0.035)
    # grille au sol
    for k in range(-10, 11):
        cv2.line(lay, P(proj((k * 0.45, -1.4, -4.5), 0, tilt)), P(proj((k * 0.45, -1.4, 4.5), 0, tilt)), 0.28, 1, cv2.LINE_AA)
        cv2.line(lay, P(proj((-4.5, -1.4, k * 0.45), 0, tilt)), P(proj((4.5, -1.4, k * 0.45), 0, tilt)), 0.28, 1, cv2.LINE_AA)
    # pièce filaire : deux faces + tranche
    R = 1.15; th = np.linspace(0, 2 * np.pi, 96)
    for zz in (-0.14, 0.14):
        pts = np.array([P(proj((R * np.cos(t), R * np.sin(t), zz), ang, tilt)) for t in th], np.int32)
        cv2.polylines(lay, [pts], True, 1.0, 3, cv2.LINE_AA)
        pts = np.array([P(proj((R * 0.86 * np.cos(t), R * 0.86 * np.sin(t), zz), ang, tilt)) for t in th], np.int32)
        cv2.polylines(lay, [pts], True, 0.55, 1, cv2.LINE_AA)
    for t in th[::4]:
        cv2.line(lay, P(proj((R * np.cos(t), R * np.sin(t), -0.14), ang, tilt)), P(proj((R * np.cos(t), R * np.sin(t), 0.14), ang, tilt)), 0.6, 1, cv2.LINE_AA)
    # symbole € sur la face avant
    eu = [P(proj((0.62 * np.cos(t) + 0.08, 0.62 * np.sin(t), 0.15), ang, tilt)) for t in np.linspace(0.8, 2 * np.pi - 0.8, 48)]
    cv2.polylines(lay, [np.array(eu, np.int32)], False, 1.0, 5, cv2.LINE_AA)
    for yy in (-0.13, 0.13):
        cv2.line(lay, P(proj((-0.72, yy, 0.15), ang, tilt)), P(proj((0.18, yy, 0.15), ang, tilt)), 1.0, 5, cv2.LINE_AA)
    # apparition par balayage (5 images) à chaque angle
    k = i - CUT2 if second else i
    rev = ease_out((k + 1) / 5); cut = int(H * 0.75 * rev)
    lay[cut:] = 0
    if rev < 1: lay[max(cut - 4, 0):cut] = 1.0          # ligne de balayage
    glow = gblur(lay, 12) * 1.5 + gblur(lay, 4) * 0.7
    img = img + (lay + glow)[..., None] * TEAL
    # cadre HUD : coins + graduations
    hud = Image.new("L", (W, H), 0); d = ImageDraw.Draw(hud)
    m, L = 60, 90
    for (x, y, sx, sy) in ((m, 150, 1, 1), (W - m, 150, -1, 1), (m, H - 330, 1, -1), (W - m, H - 330, -1, -1)):
        d.line((x, y, x + sx * L, y), fill=200, width=4); d.line((x, y, x, y + sy * L), fill=200, width=4)
    for yy in range(260, H - 420, 40): d.line((m, yy, m + (22 if yy % 200 == 60 else 10), yy), fill=120, width=2)
    d.text((m + 30, 175), "SMIC", font=F_SM, fill=150)
    # étiquette SMIC reliée à la pièce
    if k >= 4:
        a = min(1.0, (k - 3) / 3)
        cxy = proj((R * 0.7, R * 0.7, 0.14), ang, tilt)
        x0, y0 = int(W * 0.60), int(H * 0.14)
        d.rectangle((x0, y0, x0 + 300, y0 + 100), outline=int(255 * a), width=4)
        d.text((x0 + 150, y0 + 52), "SMIC", font=F_LAB, fill=int(255 * a), anchor="mm")
        d.line((x0, y0 + 100, int(cxy[0]), int(cxy[1])), fill=int(220 * a), width=3)
        d.ellipse((int(cxy[0]) - 9, int(cxy[1]) - 9, int(cxy[0]) + 9, int(cxy[1]) + 9), outline=int(255 * a), width=3)
    t = np.asarray(hud).astype(np.float32) / 255
    img = img + (t + gblur(t, 6))[..., None] * TEAL
    # chiffre « 1 700 € » révélé par balayage ; rouge #E4002B, contour sombre, halo rouge
    if i >= 2:
        txt = "1\u202f700\u202f€"     # chiffre réel uniquement (pas de compteur qui afficherait de faux montants)
        pil = Image.new("RGB", (W, H), 0); dd = ImageDraw.Draw(pil)
        dd.text((W / 2, H * 0.70), txt, font=F_BIG, fill=(255, 255, 255), anchor="mm", stroke_width=0)
        mask = np.asarray(pil)[..., 0].astype(np.float32) / 255
        wx = int(W * (0.12 + 0.8 * ease_out((i - 1) / 5))); mask[:, wx:] = 0      # révélation gauche -> droite (5 images)
        st = cv2.dilate(mask, np.ones((15, 15), np.uint8))
        red = np.array(RED[::-1], np.float32) / 255
        img = img * (1 - st[..., None] * 0.85)
        img = img + gblur(mask, 22)[..., None] * red * 1.1
        img = img * (1 - mask[..., None]) + mask[..., None] * red
        # sous-ligne teal
        y = int(H * 0.70) + 150; w = int(380 * ease_out((i - 2) / 8))
        img[y:y + 5, W // 2 - w:W // 2 + w] = TEAL
    # lignes de balayage + petite aberration au changement d'angle
    img[::4] *= 0.88
    if i in (CUT2, CUT2 + 1): img = rgb_split(img, 8 if i == CUT2 else 4)
    img = vignette(img, 0.45)
    return grain(np.clip(img, 0, 1), 0.015)
if __name__ == "__main__":
    import subprocess
    out = D + "/out/5_HUD.mov"
    enc = subprocess.Popen(["/opt/homebrew/bin/ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", "%dx%d" % (W, H), "-r", "30", "-i", "-",
                            "-c:v", "prores_ks", "-profile:v", "3", "-pix_fmt", "yuv422p10le", "-vendor", "apl0", out], stdin=subprocess.PIPE)
    for i in range(N):
        f = frame(i); enc.stdin.write((np.clip(f, 0, 1) * 255 + 0.5).astype(np.uint8).tobytes())
        if i in (8, 30): cv2.imwrite(D + "/chk/hud_%02d.jpg" % i, cv2.resize((np.clip(f, 0, 1) * 255).astype(np.uint8), (540, 960)))
    enc.stdin.close(); enc.wait(); print("ok", out, N)
