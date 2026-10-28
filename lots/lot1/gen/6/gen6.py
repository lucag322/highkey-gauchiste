import sys, os, json, numpy as np, cv2, shutil
sys.path.insert(0, "/Users/luca.grousset/Movies/highkey-gauchiste/_claude/outils")
from fx import *
D = os.path.dirname(os.path.abspath(__file__)); os.chdir(D)
W, H = 1080, 1440; FPS = 30
page = cv2.imread("page.png").astype(np.float32) / 255
pj = json.load(open("page.json")); HLB = pj["hl"]
rng = np.random.default_rng(66)
def hl_center(i):
    b = HLB[i]; return ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)
# --- cutout (source 23.9 s = index 0, 29.97 i/s) ---
_cut = {}
def cutout(k):
    k = int(min(max(k, 0), 217))
    if k not in _cut:
        rgb = cv2.imread("frames/f%04d.png" % k).astype(np.float32) / 255
        m = cv2.imread("masks/f%04d.png" % k, 0).astype(np.float32) / 255
        m[:, 1480:] = 0
        m = cv2.GaussianBlur(m, (0, 0), 1.2)
        _cut[k] = (rgb[:, 300:1500], m[:, 300:1500])
    return _cut[k]
def src_k(f): return round((f / FPS + 21.0 - 23.9) * 29.97)
def paste_cutout(img, f, rise):   # rise 0 = hors champ (bas), 1 = en place
    rgb, m = cutout(src_k(f))
    s = 1.25; cw, ch = int(rgb.shape[1] * s), int(rgb.shape[0] * s)
    rgb = cv2.resize(rgb, (cw, ch)); m = cv2.resize(m, (cw, ch))
    y_final = H - int(ch * 0.78); y = int(y_final + (1 - rise) * (ch * 0.78)); x = (W - cw) // 2 + 60
    if y >= H: return img
    out = img.copy(); y0, y1 = max(y, 0), min(y + ch, H); x0, x1 = max(x, 0), min(x + cw, W)
    sub_rgb = rgb[y0 - y:y1 - y, x0 - x:x1 - x]; sub_m = m[y0 - y:y1 - y, x0 - x:x1 - x]
    out[y0:y1, x0:x1] = over(out[y0:y1, x0:x1], sub_rgb, sub_m)
    return out
def journal(cx, cy, cw, angle=0.0, mb=0.0, sharp_y=0.44):
    v = crop_view(page, cx, cy, cw, W, H, angle)
    # bords hors page -> papier sombre
    b = gblur(v, 9)
    yy = np.arange(H, dtype=np.float32)[:, None] / H
    m = np.clip((np.abs(yy - sharp_y) - 0.07) / 0.15, 0, 1)
    xx = np.arange(W, dtype=np.float32)[None, :] / W
    m = np.clip(m + np.clip((np.abs(xx - 0.5) - 0.32) / 0.2, 0, 1) * 0.6, 0, 1)[..., None]
    v = v * (1 - m) + b * m
    if mb: v = motion_blur(v, mb, 0)
    return v
def grade_paper(img):
    img = img * np.array([0.80, 0.92, 1.0], np.float32)[None, None, :]
    img = vignette(img, 0.62, 1.8, tint=(0.13, 0.17, 0.2))   # BGR brun sombre
    return grain(img, 0.03, 1.5)
# vues : (index surlignage, largeur vue, décalage x de la vue)
VIEWS = [(0, 1450, 0.10), (4, 1300, -0.05), (5, 1250, 0.05), (9, 1400, 0.0), (12, 1300, -0.08), (14, 1400, 0.06),
         (18, 1250, 0.0), (7, 1250, 0.1), (21, 1300, -0.1), (16, 1300, 0.0), (2, 1250, 0.05), (11, 1300, 0.0),
         (24, 1300, -0.04), (13, 1350, 0.02), (6, 1350, 0.0), (15, 1300, 0.0), (27, 1300, 0.0)]
def view_frame(vi, prog, slide=60, extra_angle=0.0, mb_scale=1.0):
    i, cw, off = VIEWS[vi % len(VIEWS)]; cw = cw * 0.72
    hx, hy = hl_center(i); sc = cw / W
    cx = hx + (0.5 - 0.45) * W * sc + off * W * sc - slide * sc * (prog - 0.5) * 2
    cy = hy + (0.5 - 0.44) * H * sc
    return journal(cx, cy, cw, extra_angle, mb=slide * 0.15 * mb_scale)
def seg(name, n, fn):
    fd = os.path.join(D, "seq_" + name)
    shutil.rmtree(fd, ignore_errors=True); os.makedirs(fd)
    for i in range(n): write_seq(fd, i, np.clip(fn(i), 0, 1))
    encode(fd, os.path.join(D, "out", "6_%s.mov" % name))
    print(name, n)
os.makedirs(os.path.join(D, "out"), exist_ok=True)
# J1 : 0-96, vues de 15 images puis rafale de 3 images à partir de 75
def J1(i):
    if i < 75: vi, p, sl = i // 15, (i % 15) / 14, 70
    else: vi, p, sl = 5 + (i - 75) // 3, ((i - 75) % 3) / 2, 25
    img = view_frame(vi, p, sl)
    # légères barres noires / décalage du cadre comme la réf (cadre qui bouge)
    if i >= 75 and (i // 3) % 2: img = np.roll(img, int(rng.integers(-30, 30)), axis=0)
    return grade_paper(img)
# J2 : 96-117 glitch + Macron qui surgit du bas
def J2(i):
    f = 96 + i
    img = view_frame(13, i / 20, 30)
    g = np.sin(np.pi * min(i / 14, 1)) if i < 14 else 0.25
    rise = ease_out(i / 16)
    img = paste_cutout(img, f, rise)
    if g > 0.05:
        img = rgb_split(img, 14 * g); img = slices(img, int(10 * g) + 2, int(110 * g), rng)
    if i >= 18: img = motion_blur(img, 0, 90 * (i - 17))
    return grade_paper(img)
# J3 : 165-198 journal « Votre Aura » + Macron qui surgit (sur « pognon de dingue »)
def J3(i):
    f = 165 + i
    img = view_frame(9, i / 32, 40)
    img = paste_cutout(img, f, ease_out((i - 1) / 9))
    if i >= 29:
        k = (i - 28) / 4; img = rgb_split(img, 18 * k); img = slices(img, 10, int(140 * k), rng); img = motion_blur(img, 0, 120 * k)
    return grade_paper(img)
# J4 : 240-258 rafale de vues + Macron qui surgit
def J4(i):
    f = 240 + i
    img = view_frame(1 + i // 6, (i % 6) / 5, 40)
    img = paste_cutout(img, f, ease_out((i - 5) / 12))
    if i >= 16: img = motion_blur(img, 0, 100 * (i - 15))
    return grade_paper(img)
# J5 : 330-342
def J5(i):
    img = view_frame(0, i / 11, 50)
    if i >= 9: img = zoom_blur(img, 0.08 * (i - 8))
    return grade_paper(img)
# Halo blanc final 342-390
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
def HALO(i):
    warm = np.array([0.80, 0.90, 1.0], np.float32)  # BGR blanc chaud
    if i < 18:
        r = 0.18 + 0.5 * ease_out(i / 16)
        d = np.sqrt(((xx - W / 2) / (W * r)) ** 2 + ((yy - H * 0.47) / (H * r * 0.85)) ** 2)
        a = np.clip(1 - d, 0, 1) ** 1.6 * min(1, (i + 2) / 5)
        return a[..., None] * warm
    if i < 33:
        j = i - 18; ang = np.arctan2(yy - H / 2, xx - W / 2) + j * 0.05
        rays = (0.5 + 0.5 * np.cos(ang * 8)) ** 3
        d = np.sqrt(((xx - W / 2) / W) ** 2 + ((yy - H / 2) / H) ** 2)
        core = np.clip(1 - d * 3.2, 0, 1) ** 1.5
        a = np.clip(rays * np.clip(1.2 - d * 1.3, 0, 1) + core, 0, 1) * (1 - ease_in(j / 14) * 0.9)
        return grain(a[..., None] * warm * np.array([0.85, 0.92, 1.0], np.float32), 0.02, 1.5)
    return np.zeros((H, W, 3), np.float32)
if __name__ == "__main__":
    which = sys.argv[1:] or ["J1", "J2", "J3", "J4", "J5", "HALO"]
    N = {"J1": 96, "J2": 21, "J3": 33, "J4": 18, "J5": 12, "HALO": 48}
    for w in which: seg(w, N[w], globals()[w])
