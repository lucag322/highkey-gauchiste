# Micros fixes (pieds col-de-cygne + têtes en mousse) devant Rima Hassan : tracés relevés à la main sur l'image MÉDIANE de chaque plan
# caméra (sheets/grid_*.jpg : caméra fixe -> micro net, elle floue), en px de la source 1920x1080.
# Chaque image est réparée par inpaint (TELEA) dans ce masque avant la découpe N&B ; dans la zone du micro, la découpe est ouverte
# (morphologie) pour enlever les bouts de pied qui dépassent du corps.
import numpy as np, cv2
MICS = {
    "PH": dict(heads=[(800, 447, 20, 26), (1100, 463, 20, 24)],
               polys=[[(800, 447), (700, 555), (600, 665), (510, 780), (462, 845)],
                      [(1100, 463), (1150, 500), (1220, 580), (1290, 670), (1350, 750), (1392, 800)]]),
    "SC": dict(heads=[(693, 475, 22, 28), (1043, 490, 22, 26)],
               polys=[[(690, 490), (630, 560), (500, 710), (400, 820), (300, 930)],
                      [(1050, 500), (1200, 630), (1300, 730), (1400, 830), (1455, 905)]]),
    "SA": dict(heads=[(797, 447, 20, 26), (1082, 465, 20, 24)],
               polys=[[(797, 447), (770, 470), (680, 580), (590, 700), (500, 810), (475, 850)],
                      [(1082, 465), (1110, 480), (1200, 560), (1270, 650), (1340, 740), (1390, 795)]]),
    "SB": dict(heads=[(797, 457, 20, 26), (1085, 475, 20, 24)],
               polys=[[(797, 457), (770, 480), (670, 580), (590, 680), (520, 780), (470, 850)],
                      [(1085, 475), (1110, 490), (1200, 580), (1280, 670), (1350, 750), (1390, 790)]]),
    "CO": dict(heads=[(822, 392, 22, 28), (985, 412, 22, 28)],
               polys=[[(822, 395), (820, 420), (790, 490), (730, 530), (660, 560), (640, 600), (635, 720)],
                      [(985, 412), (1000, 440), (1030, 500), (1080, 540), (1150, 550), (1200, 570), (1215, 610), (1220, 720)]],
               posts=[[(635, 595), (635, 720)], [(1218, 600), (1218, 720)]]),
}
def mic_mask(cam, shape=(1080, 1920), width=23):
    m = np.zeros(shape, np.uint8); c = MICS[cam]
    for pl in c["polys"]: cv2.polylines(m, [np.array(pl, np.int32)], False, 255, width, cv2.LINE_AA)
    for pl in c.get("posts", []): cv2.polylines(m, [np.array(pl, np.int32)], False, 255, 34)
    for (x, y, rx, ry) in c["heads"]: cv2.ellipse(m, (x, y), (rx, ry), 0, 0, 360, 255, -1)
    return (m > 60).astype(np.uint8) * 255
def clean(frame_u8, m, box):
    x0, y0, x1, y1 = box; pad = 30
    a, b, c, d = max(0, x0 - pad), max(0, y0 - pad), min(frame_u8.shape[1], x1 + pad), min(frame_u8.shape[0], y1 + pad)
    out = frame_u8.copy(); out[b:d, a:c] = cv2.inpaint(np.ascontiguousarray(frame_u8[b:d, a:c]), np.ascontiguousarray(m[b:d, a:c]), 9, cv2.INPAINT_TELEA)
    return out
def trim(mask, mm_box):
    """Dans la zone du micro (élargie), la découpe est refermée (fermeture 45 px) : l'encoche laissée par la tête ou le pied du micro
    (retirés par decoupe.py) est rebouchée, l'image y est déjà réparée par inpaint ; rien n'est ajouté hors de cette zone."""
    zone = cv2.dilate(mm_box, np.ones((41, 41), np.uint8)) > 0
    cl = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (45, 45)))
    return np.where(zone, np.maximum(mask, cl), mask).astype(np.float32)
