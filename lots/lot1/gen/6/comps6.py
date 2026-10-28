import sys
sys.path.insert(0, "/Users/luca.grousset/Movies/highkey-gauchiste/_claude/outils")
exec(open("/Users/luca.grousset/Movies/highkey-gauchiste/_claude/outils/compkit.py").read())
C = "/Users/luca.grousset/Movies/highkey-gauchiste/_claude/comps/6/"
LUT = "/Users/luca.grousset/Movies/highkey-gauchiste/_claude/luts/s6_chaud.cube"
W, H = 1080, 1440
def base(b):
    lut = b.node("FileLUT", "LUT"); lut.link("Input", "MediaIn1"); lut.set("LUTFile", LUT)
    return lut
def grain(b, src):
    g = b.node("FilmGrain", "GR"); g.link("Input", src.name); g.set("MasterStrength", 0.06); g.set("Monochrome", 1)
    return g
def full(b, src, face_x, size=1.3333, face_y=None):
    """Plein cadre 3:4 centré sur le visage (face_x px source)."""
    cx = 0.5 + (960 - face_x) * size / W
    return cx
def comp_full(name, n, face_x, keys_center=None, keys_size=None, keys_angle=None, size=1.3333):
    b = B("F" + name, last=n - 1, w=W, h=H)
    bg = b.bg("#000000"); src = base(b)
    xf = b.xf(src)
    if keys_center: b.anim_xy(xf, "Center", keys_center)
    if keys_size: b.anim(xf, "Size", keys_size)
    if keys_angle: b.anim(xf, "Angle", keys_angle)
    m = b.merge(bg, xf, size=size, center=(full(b, src, face_x, size), 0.5))
    write_clip_comp(b, grain(b, m), C + "F_%s.comp" % name, open(C + "def_%s.comp" % name).read())
def comp_framed(name, n, face_x, frac, cropw=810, keys_rot=None, keys_center=None, keys_size=None, persp=0.6):
    b = B("F" + name, last=n - 1, w=W, h=H)
    bg = b.bg("#000000"); src = base(b)
    cr = b.node("Crop", "CR"); cr.link("Input", src.name)
    x0 = int(min(max(face_x - cropw / 2, 0), 1920 - cropw))
    for k, v in (("XOffset", x0), ("YOffset", 0), ("XSize", cropw), ("YSize", 1080)): cr.set(k, v)
    node = cr
    if keys_rot:
        dve = b.node("DVE", "DV"); dve.link("Input", node.name); dve.set("Perspective", persp)
        b.anim(dve, "YRotation", keys_rot); node = dve
    xf = b.xf(node)
    if keys_center: b.anim_xy(xf, "Center", keys_center)
    if keys_size: b.anim(xf, "Size", keys_size)
    size = frac * W / cropw
    m = b.merge(bg, xf, size=size, center=(0.5, 0.5))
    write_clip_comp(b, grain(b, m), C + "F_%s.comp" % name, open(C + "def_%s.comp" % name).read())
L = "lin"; O = "out"; I = "in"; IO = "io"
# F1 117-150 : entrée en balayage depuis le haut + push lent
comp_full("117", 33, 960, keys_center=[(0, (0.5, 0.80), L), (4, (0.5, 0.5), O)], keys_size=[(0, 1.0, L), (32, 1.06, L)])
# F2 150-165 : extrait encadré 85 % sur noir
comp_framed("150", 15, 900, 0.85, keys_center=[(0, (0.5, 0.49), L), (14, (0.5, 0.51), L)])
# F3 198-210 : plein cadre, balayage depuis le haut
comp_full("198", 12, 860, keys_center=[(0, (0.5, 0.85), L), (4, (0.5, 0.5), O)], keys_size=[(0, 1.08, L), (11, 1.0, O)])
# F4 210-216 : encadré 85 %, la carte pivote (sortie)
comp_framed("210", 6, 855, 0.85, keys_rot=[(0, 0.0, L), (1, 0.0, L), (5, 84.0, I)])
# F5 216-222 : carte de profil (fine lamelle) qui revient
comp_framed("216", 6, 855, 0.62, cropw=760, keys_rot=[(0, -86.0, L), (5, -70.0, L)])
# F6 222-240 : carte qui s'ouvre, encadré ~70 %, plus serré
comp_framed("222", 18, 840, 0.70, cropw=700, keys_rot=[(0, -70.0, L), (4, 0.0, O)], keys_size=[(0, 1.0, L), (17, 1.04, L)])
# F7 258-315 : plein cadre, secousses avec flou de mouvement (réf 9-10,5 s)
ck = [(0, (1.15, 0.5), L), (4, (0.5, 0.5), O), (13, (0.5, 0.5), L), (14, (0.47, 0.53), L), (16, (0.53, 0.47), L), (18, (0.5, 0.5), O),
      (29, (0.5, 0.5), L), (30, (0.5, 0.62), L), (33, (0.5, 0.5), O), (44, (0.5, 0.5), L), (45, (0.42, 0.5), L), (47, (0.57, 0.48), L), (50, (0.5, 0.5), O),
      (54, (0.5, 0.5), L), (56, (0.5, 1.1), I)]
comp_full("258", 57, 795, keys_center=ck, keys_size=[(0, 1.0, L), (29, 1.0, L), (31, 1.3, O), (36, 1.08, O), (56, 1.12, L)],
          keys_angle=[(0, 0.0, L), (13, 0.0, L), (14, -12.0, L), (18, 0.0, O), (44, 0.0, L), (46, 9.0, L), (50, 0.0, O)])
# F8 315-330 : gros plan (main au menton, source 40,5 s), push lent
comp_full("315", 15, 940, size=2.0, keys_size=[(0, 1.0, L), (14, 1.05, L)], keys_center=[(0, (0.5, 0.36), L), (14, (0.5, 0.36), L)])
print("ok")
