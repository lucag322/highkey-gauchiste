# compkit : génère des .comp Fusion en réutilisant le bloc MediaIn1 exporté d'un clip de timeline.
import re, json
exec(open("/Users/luca.grousset/.claude/skills/resolve-studio-editor/scripts/fusion_comp_writer.py").read())

class Ref:
    def __init__(self, name): self.name = name

def mediain_block(default_comp_text):
    """Extrait le texte 'MediaIn1 = Loader { ... },' du comp exporté par Resolve."""
    i = default_comp_text.index("MediaIn1 = Loader {")
    depth = 0; j = i
    while True:
        c = default_comp_text[j]
        if c == "{": depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0: break
        j += 1
    return "\t\t" + default_comp_text[i:j+1] + ","

def write_clip_comp(b, last_node, path, default_comp_text):
    mi = mediain_block(default_comp_text)
    mo = Node("MediaOut1", "Saver"); mo.set("Index", "0"); mo.link("Input", last_node.name)
    tools = "\n".join([mi] + [n.dump() for n in b.nodes] + [mo.dump()])
    gr = re.search(r"GlobalRange = \{ (-?\d+), (-?\d+) \}", default_comp_text)
    open(path, "w").write(("Composition {\n\tCurrentTime = 0,\n\tRenderRange = { 0, %d },\n\tGlobalRange = { %s, %s },\n"
                           "\tHiQ = true,\n\tTools = ordered() {\n%s\n\t},\n}\n") % (b.last, gr.group(1), gr.group(2), tools))

def _frame_custom(self, t):
    for k, v in (("Width", self.w), ("Height", self.h), ("UseFrameFormatSettings", 0), ("GlobalOut", self.last)):
        t.set(k, v)
B._frame = _frame_custom

class Raw(str):
    pass
_lua_orig = _lua
def _lua(v):
    if isinstance(v, Raw): return str(v)
    if isinstance(v, str): return json.dumps(v, ensure_ascii=False)
    if isinstance(v, (list, tuple)): return "{ " + ", ".join(_lua(x) for x in v) + " }"
    return _lua_orig(v)
def fuid(s): return Raw('FuID { "%s" }' % s)

def loader_seq(b, path_first, n, start_index=0, gstart=0):
    """Séquence PNG : path_first = …/x_0000.png ; comp frame f -> fichier start_index+f."""
    t = b.node("Loader", "LD")
    clip = ("StartFrame = %d, Length = %d, LengthSetManually = true, TrimIn = 0, TrimOut = %d, ExtendFirst = 0, "
            "ExtendLast = 0, Loop = 0, AspectMode = 0, Depth = 0, TimeCode = 0, GlobalStart = %d, GlobalEnd = %d") % (start_index, n, n - 1, gstart, gstart + n - 1)
    t.extra = ('\t\t\tClips = {\n\t\t\t\tClip {\n\t\t\t\t\tID = "Clip1", Filename = %s, FormatID = "PNGFormat", %s\n\t\t\t\t}\n\t\t\t},\n'
               % (json.dumps(path_first), clip))
    t.set("Clip1.PNGFormat.PostMultiply", 1)
    for k, v in (("GlobalIn", 0), ("GlobalOut", n - 1), ("ClipTimeStart", 0), ("ClipTimeEnd", n - 1), ("Loop", 0)): t.set(k, v)
    return t

def win916(fx, fy, h, top=0.30, bounds=(0, 0, 1920, 1080)):
    """Fenêtre 9:16 (x0, y0, w, h) en px source (y vers le bas) : visage (fx,fy) centré en x et à `top` du haut, bornée."""
    w = h * 9 / 16; bx0, by0, bx1, by1 = bounds
    h = min(h, by1 - by0); w = h * 9 / 16
    x0 = min(max(fx - w / 2, bx0), bx1 - w); y0 = min(max(fy - top * h, by0), by1 - h)
    return int(round(x0)), int(round(y0)), int(round(w)), int(round(h))
def crop916(bb, src, win):
    x0, y0, w, h = win
    c = bb.node("Crop", "CR"); c.link("Input", src.name)
    for k, v in (("XOffset", x0), ("YOffset", 1080 - y0 - h), ("XSize", w), ("YSize", h)): c.set(k, v)
    return c
def place916(bb, img, win):
    """Pose l'image recadrée plein cadre 1080x1920."""
    bg = bb.bg("#000000"); return bb.merge(bg, img, size=1920 / win[3], center=(0.5, 0.5))
def pivot_of(fx, fy): return (fx / 1920, 1 - fy / 1080)
