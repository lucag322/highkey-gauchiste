# Recadrage 9:16 qui suit le visage (Apple Vision) et garde la tête ENTIÈRE dans le cadre, zooms et secousses compris.
import os, json, subprocess, math
ROOT = "/Users/luca.grousset/Movies/highkey-gauchiste"
CACHE = ROOT + "/_claude/cache/faces"
FF = "/opt/homebrew/bin/ffmpeg"; FACES = ROOT + "/_claude/outils/faces"
SW, SH = 1920, 1080
def detect(src, s, n, fps):
    """Boîtes de visages (px source) pour les images source s..s+n-1."""
    d = "%s/%s_%d_%d" % (CACHE, os.path.splitext(src)[0], s, n)
    if not os.path.exists(d + "/faces.json"):
        os.makedirs(d, exist_ok=True)
        subprocess.run([FF, "-v", "error", "-y", "-ss", "%.4f" % (s / fps), "-i", os.path.normpath(ROOT + "/sources/" + src), "-frames:v", str(n),
                        "-vf", "scale=960:-2", "-fps_mode", "passthrough", "-start_number", "0", "-q:v", "3", d + "/f%04d.jpg"], check=True)
        subprocess.run([FACES, d], check=True, capture_output=True)
    js = json.load(open(d + "/faces.json"))
    return [[(b[0] * SW, b[1] * SH, b[2] * SW, b[3] * SH) for b in js.get("f%04d.jpg" % i, [])] for i in range(n)]
def pick(faces, hint, bounds, min_w=40):
    """Suit un visage (le plus proche de l'indice puis du précédent), comble les trous, lisse."""
    bx0, by0, bx1, by1 = bounds; prev = hint; out = []
    for fl in faces:
        cand = [f for f in fl if f[2] >= min_w and bx0 <= f[0] + f[2] / 2 <= bx1 and by0 <= f[1] + f[3] / 2 <= by1]
        if cand:
            f = min(cand, key=lambda f: (f[0] + f[2] / 2 - prev[0]) ** 2 + (f[1] + f[3] / 2 - prev[1]) ** 2)
            if out and out[-1] and math.hypot(f[0] + f[2] / 2 - prev[0], f[1] + f[3] / 2 - prev[1]) > max(f[2], 80) * 1.5:
                f = None
        else: f = None
        out.append(f)
        if f: prev = (f[0] + f[2] / 2, f[1] + f[3] / 2)
    # combler : tenir la dernière valeur connue (avant / après)
    known = [i for i, f in enumerate(out) if f]
    if not known: return None
    for i in range(len(out)):
        if not out[i]:
            j = min(known, key=lambda k: abs(k - i)); out[i] = out[j]
    # lissage (moyenne glissante 7)
    sm = []
    for i in range(len(out)):
        win = out[max(0, i - 3): i + 4]
        sm.append(tuple(sum(f[k] for f in win) / len(win) for k in range(4)))
    return sm
def head_box(f):
    x, y, w, h = f
    return (x - 0.2 * w, y - 0.5 * h, x + w * 1.2, y + h * 1.2)    # cheveux (~0,4 h au-dessus de la boîte Vision), oreilles, menton
def view_for(head, vh, bounds, top=0.17, margin=0.05, shake=(0, 0)):
    bx0, by0, bx1, by1 = bounds
    hx0, hy0, hx1, hy1 = head
    vh = min(vh, by1 - by0, (bx1 - bx0) * 16 / 9)
    for _ in range(40):
        need_h = max((hy1 - hy0) / (1 - 2 * margin - top + margin), (hx1 - hx0) * 16 / 9 / (1 - 2 * margin))
        vh = min(max(vh, need_h), by1 - by0, (bx1 - bx0) * 16 / 9); vw = vh * 9 / 16
        cx = (hx0 + hx1) / 2 + shake[0] * vw; vy0 = hy0 - top * vh + shake[1] * vh
        x0 = min(max(cx - vw / 2, bx0), bx1 - vw); y0 = min(max(vy0, by0), by1 - vh)
        ok = (hx0 >= x0 + margin * vw and hx1 <= x0 + vw - margin * vw and hy0 >= y0 + margin * vh * 0.6 and hy1 <= y0 + vh - margin * vh)
        if ok or vh >= min(by1 - by0, (bx1 - bx0) * 16 / 9) - 1: break
        vh *= 1.04
    return (x0 + vw / 2, y0 + vh / 2, vh)
def merge_keys(views, W=1080, H=1920):
    """(cx, cy, vh) source px -> clés Merge (Size, Center) par image."""
    size, cen = [], []
    for f, (cx, cy, vh) in enumerate(views):
        m = H / vh
        size.append((f, m, "lin")); cen.append((f, (0.5 + (SW / 2 - cx) * m / W, 0.5 - (SH / 2 - cy) * m / H), "lin"))
    return size, cen
def plan_views(src, s, n_comp, fps, speed=1.0, hint=None, bounds=(0, 0, SW, SH), vh=1080, zoom=None, shake=None, top=0.17, fixed=None, monotonic=True):
    """monotonic : la hauteur de vue ne fait que diminuer (zoom avant seulement, jamais de dézoom)."""
    views, ok = _plan_views(src, s, n_comp, fps, speed, hint, bounds, vh, zoom, shake, top, fixed)
    if not monotonic or not views: return views, ok
    hs = [v[2] for v in views]
    for i in range(len(hs) - 2, -1, -1): hs[i] = max(hs[i], hs[i + 1])
    fz = lambda f: vh / hs[f]
    views2, _ = _plan_views(src, s, n_comp, fps, speed, hint, bounds, vh, fz, shake, top, fixed)
    hs2 = [v[2] for v in views2]
    for i in range(len(hs2) - 2, -1, -1):
        if hs2[i] < hs2[i + 1]: hs2[i] = hs2[i + 1]
    return [(v[0], v[1], h) for v, h in zip(views2, hs2)], ok
def _plan_views(src, s, n_comp, fps, speed=1.0, hint=None, bounds=(0, 0, SW, SH), vh=1080, zoom=None, shake=None, top=0.17, fixed=None):
    """Vues par image du comp. zoom(f)->facteur (>1 = plus serré), shake(f)->(dx,dy) en fraction de vue. fixed=(cx,cy) sans visage."""
    n_src = int(n_comp * speed) + 2
    heads = None
    if fixed is None:
        faces = detect(src, s, n_src, fps)
        heads = pick(faces, hint or ((bounds[0] + bounds[2]) / 2, (bounds[1] + bounds[3]) / 2), bounds)
    views = []
    for f in range(n_comp):
        z = zoom(f) if zoom else 1.0; sh = shake(f) if shake else (0, 0)
        if heads:
            views.append(view_for(head_box(heads[min(int(f * speed), len(heads) - 1)]), vh / z, bounds, top=top, shake=sh))
        else:
            cx, cy = fixed if fixed else hint; v = min(vh / z, bounds[3] - bounds[1]); vw = v * 9 / 16
            cx = min(max(cx + sh[0] * vw, bounds[0] + vw / 2), bounds[2] - vw / 2); cy = min(max(cy + sh[1] * v, bounds[1] + v / 2), bounds[3] - v / 2)
            views.append((cx, cy, v))
    return views, heads is not None
