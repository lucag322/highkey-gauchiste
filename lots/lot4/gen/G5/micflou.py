# Floute le logo du micro Le Média (bonnette rouge vive) : composante rouge saturée compacte près du visage, remplie,
# flou fort (médian + gaussien) dans son contour. Sources Le Média seulement.
import numpy as np, cv2
def hide_mic(fr, xr=(450, 1450)):
    b, g, r = [fr[..., i].astype(np.int16) for i in range(3)]
    m = ((r > 120) & (r - g > 70) & (r - b > 55)).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)
    best = None
    for i in range(1, n):
        x, y, w, h, a = st[i]
        if a < 1200 or w < 35 or h < 35 or not (xr[0] < x + w / 2 < xr[1]) or y + h / 2 > 800: continue
        if max(w, h) / min(w, h) > 1.9: continue                              # cravate : allongée, écartée
        cs, _ = cv2.findContours((lab == i).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        hull = cv2.convexHull(max(cs, key=cv2.contourArea)); ha = cv2.contourArea(hull)
        if ha / (w * h) < 0.55: continue
        if best is None or ha > best[1]: best = (hull, ha, (x, y, w, h))
    if best is None: return fr, None
    hull, _, (x, y, w, h) = best; p = 14
    x0, y0, x1, y1 = max(x - p, 0), max(y - p, 0), min(x + w + p, fr.shape[1]), min(y + h + p, fr.shape[0])
    full = np.zeros(fr.shape[:2], np.uint8); cv2.drawContours(full, [hull], -1, 255, -1)
    full = cv2.dilate(full, np.ones((5, 5), np.uint8))
    out = fr.copy(); roi = out[y0:y1, x0:x1]
    bl = cv2.GaussianBlur(cv2.medianBlur(roi, 31), (0, 0), 6)
    mk = cv2.GaussianBlur(full[y0:y1, x0:x1], (0, 0), 2.5).astype(np.float32)[..., None] / 255
    out[y0:y1, x0:x1] = (roi * (1 - mk) + bl * mk).astype(np.uint8)
    return out, (x0, y0, x1, y1)
