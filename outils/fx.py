# Petits effets image (numpy/cv2) partagés entre styles. Images float32 0..1, HxWx3.
import numpy as np, cv2, os, subprocess
RNG = np.random.default_rng(7)
def ease_out(t): t = min(max(t, 0.0), 1.0); return 1 - (1 - t) ** 4
def ease_in(t): t = min(max(t, 0.0), 1.0); return t ** 3
def ease_io(t): t = min(max(t, 0.0), 1.0); return 4*t**3 if t < .5 else 1 - (-2*t + 2) ** 3 / 2
def crop_view(src, cx, cy, cw, W, H, angle=0.0):
    """Vue de largeur cw (px source) centrée (cx,cy), sortie WxH (sous-pixel)."""
    s = W / cw
    M = cv2.getRotationMatrix2D((cx, cy), angle, s)
    M[0, 2] += W / 2 - cx; M[1, 2] += H / 2 - cy
    return cv2.warpAffine(src, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
def gblur(img, sigma):
    if sigma <= 0.3: return img
    return cv2.GaussianBlur(img, (0, 0), sigma)
def motion_blur(img, dx, dy, steps=None):
    """Flou de mouvement le long du vecteur (dx,dy) px."""
    L = int(max(abs(dx), abs(dy)))
    if L < 2: return img
    n = steps or min(L, 24); acc = np.zeros_like(img)
    for i in range(n):
        f = i / (n - 1) - 0.5
        M = np.float32([[1, 0, dx * f], [0, 1, dy * f]])
        acc += cv2.warpAffine(img, M, (img.shape[1], img.shape[0]), borderMode=cv2.BORDER_REFLECT)
    return acc / n
def zoom_blur(img, amount, n=16):
    """Flou radial (zoom) : amount = échelle max (ex 0.15)."""
    if amount < 0.01: return img
    H, W = img.shape[:2]; acc = np.zeros_like(img)
    for i in range(n):
        s = 1 + amount * i / (n - 1)
        M = cv2.getRotationMatrix2D((W / 2, H / 2), 0, s)
        acc += cv2.warpAffine(img, M, (W, H), borderMode=cv2.BORDER_REFLECT)
    return acc / n
def vignette(img, strength=0.5, power=2.2, tint=(0, 0, 0)):
    H, W = img.shape[:2]
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((x - W / 2) / (W / 2)) ** 2 + ((y - H / 2) / (H / 2)) ** 2) / np.sqrt(2)
    v = (1 - strength * np.clip(r, 0, 1) ** power)[..., None]
    return img * v + np.array(tint, np.float32) * (1 - v)
def grain(img, amt=0.035, size=1.0):
    H, W = img.shape[:2]
    if size > 1:
        n = RNG.normal(0, 1, (int(H / size), int(W / size), 1)).astype(np.float32)
        n = cv2.resize(n, (W, H))[..., None]
    else:
        n = RNG.normal(0, 1, (H, W, 1)).astype(np.float32)
    return img + n * amt
def rgb_split(img, px):
    out = img.copy(); px = int(px)
    out[..., 2] = np.roll(img[..., 2], px, axis=1)   # canal R (BGR) à droite
    out[..., 0] = np.roll(img[..., 0], -px, axis=1)  # canal B à gauche
    return out
def slices(img, n, maxshift, rng=RNG, hmin=6, hmax=70):
    out = img.copy(); H = img.shape[0]
    for _ in range(n):
        h = int(rng.integers(hmin, hmax)); y = int(rng.integers(0, H - h)); s = int(rng.integers(-maxshift, maxshift + 1))
        out[y:y + h] = np.roll(img[y:y + h], s, axis=1)
    return out
def over(bg, fg_rgb, alpha):
    a = alpha[..., None] if alpha.ndim == 2 else alpha
    return bg * (1 - a) + fg_rgb * a
def to8(img): return (np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)
def write_seq(frames_dir, idx, img):
    cv2.imwrite(os.path.join(frames_dir, "f%04d.png" % idx), to8(img))
def encode(frames_dir, out, fps=30, alpha=False):
    FF = "/opt/homebrew/bin/ffmpeg"
    if alpha:
        cmd = [FF, "-v", "error", "-y", "-framerate", str(fps), "-i", frames_dir + "/f%04d.png", "-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le", out]
    else:
        cmd = [FF, "-v", "error", "-y", "-framerate", str(fps), "-i", frames_dir + "/f%04d.png", "-c:v", "prores_ks", "-profile:v", "3", "-pix_fmt", "yuv422p10le", out]
    subprocess.run(cmd, check=True)
