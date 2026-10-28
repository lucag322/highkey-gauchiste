# Efface les logos (NPA, LFI, REV) du fond gris du meeting de Saint-Ouen, dans l'image DÉJÀ recadrée 9:16.
# person : masque Vision (0-1) de la personne ; ylim : ligne (px de l'image recadrée) sous laquelle on ne touche à rien (pupitre, micro, lettres).
# Fond lisse : estimation par convolution normalisée (personne et logos exclus), logos = écart fort au fond, remplacés par le fond.
import numpy as np, cv2
def _nblur(img, w, s):
    a = cv2.GaussianBlur(img * w[..., None], (0, 0), s); b = cv2.GaussianBlur(w, (0, 0), s)
    return a / np.maximum(b, 1e-4)[..., None], b
def delogo(img, person, ylim, thr=0.055, work=4):
    H, W = img.shape[:2]; h, w = H // work, W // work
    sm = cv2.resize(img, (w, h), interpolation=cv2.INTER_AREA)
    pm = cv2.resize(person, (w, h), interpolation=cv2.INTER_AREA)
    pm = cv2.dilate((pm > 0.25).astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool)
    zone = np.zeros((h, w), bool); zone[:max(0, int(ylim / work))] = True
    clean = (~pm).astype(np.float32); logo = np.zeros((h, w), bool)
    for _ in range(3):
        bg, cov = _nblur(sm, clean, 18)
        dev = np.abs(sm - bg).max(2)
        logo = zone & ~pm & (dev > thr)
        logo = cv2.dilate(logo.astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool) & ~pm
        clean = ((~pm) & (~logo)).astype(np.float32)
    bg, _ = _nblur(sm, clean, 18)
    m = cv2.GaussianBlur(logo.astype(np.float32), (0, 0), 1.2)
    m = np.clip(m * 1.6, 0, 1)
    M = cv2.resize(m, (W, H), interpolation=cv2.INTER_LINEAR)[..., None]
    P = cv2.resize(person, (W, H), interpolation=cv2.INTER_LINEAR)[..., None]
    M = M * (1 - np.clip(P * 2, 0, 1))                     # jamais sur la personne
    BG = cv2.resize(bg, (W, H), interpolation=cv2.INTER_CUBIC)
    return img * (1 - M) + BG * M, float(logo.mean())
