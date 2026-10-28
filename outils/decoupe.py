# Découpe propre d'UNE personne pour les collages (Luca, 27/10 : rien que la personne, pas de voisin ; jamais un membre
# coupé en l'air ; jamais coupé sous le cou ou en haut des épaules : garder au moins mi-poitrine, quitte à garder un bout
# de micro ou de pupitre, donc ne pas recadrer le box au-dessus des micros). À importer dans les gen*.py :
#   sys.path.insert(0, ROOT + "/_claude/outils"); from decoupe import masques, bas_dechire, controle, planche
# masques(frames, box, pt, dossier) : frames = images float BGR 0-1 (ou uint8) pleine taille, box = (x0, y0, x1, y1) en px,
#   pt = point sur la poitrine, normalisé dans le box. Croise l'instance Vision de cette personne avec la segmentation
#   personne « accurate » (enlève pupitre, micro, bouts d'objets), garde la seule forme qui contient le point, bouche les
#   petits trous, lisse dans le temps (médiane sur 3 images). Cache : <dossier>/in, i, p.
# controle(m) : part de chaque bord du box touchée par la découpe, nombre de morceaux, bas_net (buste coupé à plat,
#   au bord du box ou au pupitre, si > 0,2). Bord gauche/droit/haut touché = membre ou tête coupé : élargir le box ou
#   écarter le plan. Bas net : poser ce bord sur le bas du cadre 9:16, sinon bas_dechire(m) en fait un bord de papier déchiré.
# planche(frames, ms, box, chemin) : découpes sur fond magenta pour vérifier à l'œil (à regarder avant de rendre).
import os, subprocess
import numpy as np, cv2

PERSO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "perso")

def _u8(f):
    return f if f.dtype == np.uint8 else (np.clip(f, 0, 1) * 255).astype(np.uint8)

def _lire(chemin):
    m = cv2.imread(chemin, 0)
    return m.astype(np.float32) / 255 if m is not None else None

def _nettoie(m, p, pt):
    if p is not None: m = np.minimum(m, cv2.dilate(p, np.ones((9, 9), np.uint8)))   # hors personne (pupitre, micro) : coupé
    b = (m > 0.5).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(b, 8)
    if n <= 1: return np.zeros_like(m)
    h, w = b.shape; k = lab[min(h - 1, int(pt[1] * h)), min(w - 1, int(pt[0] * w))]
    if k == 0: k = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
    garde = (lab == k).astype(np.uint8)
    inv = 1 - garde; n2, lab2, st2, _ = cv2.connectedComponentsWithStats(inv, 4)       # petits trous bouchés, pas l'espace bras-corps
    aire = garde.sum()
    for j in range(1, n2):
        x, y, ww, hh, a = st2[j]
        if a < 0.004 * aire and x > 0 and y > 0 and x + ww < w and y + hh < h: garde[lab2 == j] = 1
    # fentes fines (pied de micro qui traverse le buste) refermées : on y voit l'image d'origine, pas un trou
    ferme = cv2.morphologyEx(garde, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (31, 31)))
    m = np.where(ferme > garde, 1.0, m)
    return np.where(ferme > 0, m, 0).astype(np.float32)

def _bas(t):
    """(dernière ligne de la découpe, part de sa largeur coupée net à cette hauteur) ; > 0,2 = buste coupé à plat."""
    ys = np.where(t.any(1))[0]
    if len(ys) == 0: return 0, 0.0
    yb = int(ys[-1]); larg = max(int(t.any(0).sum()), 1)
    return yb, float(t[max(0, yb - 4):yb + 1].any(0).sum()) / larg

def masques(frames, box, pt, dossier):
    x0, y0, x1, y1 = box; di, dm = dossier + "/in", dossier
    if not (os.path.isdir(dm + "/i") and len(os.listdir(dm + "/i")) >= len(frames)):
        os.makedirs(di, exist_ok=True)
        for i, f in enumerate(frames): cv2.imwrite("%s/f%04d.png" % (di, i), _u8(f[y0:y1, x0:x1]))
        subprocess.run([PERSO, di, dm, str(pt[0]), str(pt[1])], check=True, capture_output=True)
    brut = []
    for i in range(len(frames)):
        m = _lire("%s/i/f%04d.png" % (dm, i)); p = _lire("%s/p/f%04d.png" % (dm, i))
        if m is None: m = p if p is not None else (brut[-1] if brut else np.zeros((y1 - y0, x1 - x0), np.float32))
        brut.append(_nettoie(m, p, pt))
    out = []
    for i in range(len(brut)):
        m = np.median(np.stack(brut[max(0, i - 1):i + 2]), axis=0) if len(brut) > 2 else brut[i]
        m = cv2.erode(m, np.ones((3, 3), np.uint8))                                      # pas de liseré du fond
        out.append(np.clip((cv2.GaussianBlur(m, (0, 0), 1.1) - 0.5) * 2.4 + 0.5, 0, 1).astype(np.float32))
    return out

def controle(m):
    t = m > 0.5; aire = max(int(t.sum()), 1)
    n, _, st, _ = cv2.connectedComponentsWithStats(t.astype(np.uint8), 8)
    return {"bas_net": round(_bas(t)[1], 3), "bas": round(float(t[-3:].any(0).mean()), 3), "haut": round(float(t[:3].any(0).mean()), 3),
            "gauche": round(float(t[:, :3].any(1).mean()), 3), "droite": round(float(t[:, -3:].any(1).mean()), 3),
            "morceaux": int(sum(1 for j in range(1, n) if st[j, cv2.CC_STAT_AREA] > 0.002 * aire))}

def bas_dechire(m, seed=0, bande=34):
    """Buste coupé à plat (bord du box ou haut d'un pupitre) -> bord de papier déchiré (dents irrégulières).
    Inutile si ce bord est posé sur le bas du cadre 9:16."""
    h, w = m.shape; t = m > 0.5; yb, net = _bas(t)
    if net < 0.2: return m
    rng = np.random.default_rng(seed)
    def creneaux(pas): return np.interp(np.arange(w), np.arange(0, w + pas, pas), rng.uniform(0, 1, len(range(0, w + pas, pas))))
    bruit = 0.75 * creneaux(28) + 0.25 * creneaux(7)                                      # déchirure : grandes dents + petites
    ligne = (yb + 1 - bande + bruit * bande * 0.8).astype(int)
    yy = np.arange(h)[:, None]
    return np.where(yy < ligne[None, :], m, 0).astype(np.float32)

def planche(frames, ms, box, chemin, n=6, larg=360):
    x0, y0, x1, y1 = box; idx = np.linspace(0, len(ms) - 1, min(n, len(ms))).astype(int); tuiles = []
    for i in idx:
        c = frames[i][y0:y1, x0:x1].astype(np.float32); c = c / 255 if c.max() > 1.5 else c
        fond = np.ones_like(c) * np.array([0.85, 0.1, 0.85], np.float32)
        a = ms[i][..., None]; img = _u8(c * a + fond * (1 - a))
        s = larg / img.shape[1]; tuiles.append(cv2.resize(img, (larg, int(img.shape[0] * s)), interpolation=cv2.INTER_AREA))
    hmax = max(t.shape[0] for t in tuiles)
    tuiles = [cv2.copyMakeBorder(t, 0, hmax - t.shape[0], 0, 4, cv2.BORDER_CONSTANT, value=(255, 255, 255)) for t in tuiles]
    cv2.imwrite(chemin, np.hstack(tuiles))
