# Render a routed board (Specctra .dsn + .ses) to a two-panel PNG (F.Cu, mirrored B.Cu).
# Usage: python3 -I render_board.py board.dsn board.ses out.png   (needs Pillow)
# Quick check view only: no silkscreen/mask/net names; not a DRC.
import sys, math
from PIL import Image, ImageDraw, ImageFont
dsn, ses, out = sys.argv[1:4]

def parse(path):
    s = open(path).read(); i = 0; n = len(s); stack = [[]]
    while i < n:
        c = s[i]
        if c == '(':
            stack.append([]); i += 1
        elif c == ')':
            t = stack.pop(); stack[-1].append(t); i += 1
        elif c == '"':
            j = s.index('"', i+1); stack[-1].append(s[i+1:j]); i = j+1
        elif c.isspace(): i += 1
        else:
            j = i
            while j < n and not s[j].isspace() and s[j] not in '()': j += 1
            stack[-1].append(s[i:j]); i = j
    return stack[0][0]
def sub(t, k): return [x for x in t if isinstance(x, list) and x and x[0] == k]
def f(x): return float(x)

D = parse(dsn); S_ = parse(ses)
lib = sub(D, 'library')[0]
padstacks = {p[1]: p for p in sub(lib, 'padstack')}
images = {im[1]: im for im in sub(lib, 'image')}
bnd = sub(sub(D, 'structure')[0], 'boundary')[0]
bpts = [f(v) for v in sub(bnd, 'path')[0][3:]]
bpts = list(zip(bpts[0::2], bpts[1::2]))

# SES placements (units: um*10 -> um)
placements = {}
for comp in sub(sub(S_, 'placement')[0], 'component'):
    for pl in sub(comp, 'place'):
        placements[pl[1]] = (comp[1], f(pl[2])/10, f(pl[3])/10, pl[4], f(pl[5]))
# DSN component -> image name (same name)
def shape_polys(sh):
    kind = sh[0]
    layer = sh[1]
    a = sh[2:]
    if kind == 'circle':
        d = f(a[0]); cx = f(a[1]) if len(a) > 1 else 0; cy = f(a[2]) if len(a) > 2 else 0
        return layer, [[(cx+d/2*math.cos(t*math.pi/16), cy+d/2*math.sin(t*math.pi/16)) for t in range(32)]]
    if kind == 'rect':
        x1, y1, x2, y2 = map(f, a[:4]); return layer, [[(x1,y1),(x2,y1),(x2,y2),(x1,y2)]]
    if kind == 'polygon':
        v = list(map(f, a[1:])); return layer, [list(zip(v[0::2], v[1::2]))]
    if kind == 'path':
        w = f(a[0]); v = list(map(f, a[1:])); p = list(zip(v[0::2], v[1::2]))
        polys = []
        for (x1,y1),(x2,y2) in zip(p, p[1:]) if len(p) > 1 else [(p[0],p[0])]:
            polys += [[(x1+w/2*math.cos(t*math.pi/16), y1+w/2*math.sin(t*math.pi/16)) for t in range(32)],
                      [(x2+w/2*math.cos(t*math.pi/16), y2+w/2*math.sin(t*math.pi/16)) for t in range(32)]]
            L = math.hypot(x2-x1, y2-y1)
            if L > 0:
                nx, ny = -(y2-y1)/L*w/2, (x2-x1)/L*w/2
                polys.append([(x1+nx,y1+ny),(x2+nx,y2+ny),(x2-nx,y2-ny),(x1-nx,y1-ny)])
        return layer, polys
    return layer, []
def rot(p, deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return (p[0]*c - p[1]*s, p[0]*s + p[1]*c)

pads = {'F.Cu': [], 'B.Cu': []}   # list of polygons
padinfo = []
for ref, (img, px, py, side, ang) in placements.items():
    im = images.get(img)
    if not im: continue
    for pin in sub(im, 'pin'):
        ps = padstacks[pin[1]]; rest = pin[2:]
        prot = 0
        if isinstance(rest[0], list): prot = f(rest[0][1]); rest = rest[1:]
        lx, ly = f(rest[1]), f(rest[2])
        for shp in ps[2:]:
            if not (isinstance(shp, list) and shp[0] == 'shape'): continue
            layer, polys = shape_polys(shp[1])
            for poly in polys:
                q = [rot(p, prot) for p in poly]
                q = [(x+lx, y+ly) for x, y in q]
                if side == 'back':
                    q = [(-x, y) for x, y in q]
                    layer_ = 'B.Cu' if layer == 'F.Cu' else 'F.Cu'
                else: layer_ = layer
                q = [rot(p, ang) for p in q]
                q = [(x+px, y+py) for x, y in q]
                pads[layer_].append(q)
    # courtyard-ish silkscreen skipped

wires = {'F.Cu': [], 'B.Cu': []}; vias = []
no = sub(sub(S_, 'routes')[0], 'network_out')[0]
for net in sub(no, 'net'):
    for w in sub(net, 'wire'):
        for p in sub(w, 'path'):
            v = list(map(f, p[3:])); pts = [(x/10, y/10) for x, y in zip(v[0::2], v[1::2])]
            wires[p[1]].append((f(p[2])/10, pts))
    for vi in sub(net, 'via'):
        vias.append((f(vi[2])/10, f(vi[3])/10))
VD = 600
SC = 32  # px per mm
xs = [p[0] for p in bpts]; ys = [p[1] for p in bpts]
x0, x1, y0, y1 = min(xs)-2000, max(xs)+2000, min(ys)-2000, max(ys)+2000
W = int((x1-x0)/1000*SC); H = int((y1-y0)/1000*SC)
def T(p, mirror=False):
    x = (p[0]-x0)/1000*SC
    if mirror: x = W - x
    return (x, (y1-p[1])/1000*SC)
def draw_layer(layer, mirror):
    img = Image.new('RGB', (W, H), (16, 24, 16)); d = ImageDraw.Draw(img, 'RGBA')
    d.polygon([T(p, mirror) for p in bpts], fill=(24, 40, 24), outline=(230, 230, 80))
    col_t = (214, 60, 60, 255) if layer == 'F.Cu' else (60, 110, 230, 255)
    col_o = (60, 110, 230, 110) if layer == 'F.Cu' else (214, 60, 60, 110)
    other = 'B.Cu' if layer == 'F.Cu' else 'F.Cu'
    for w, pts in wires[other]:
        d.line([T(p, mirror) for p in pts], fill=col_o, width=max(1, int(w/1000*SC)), joint='curve')
    for q in pads[other]: d.polygon([T(p, mirror) for p in q], fill=col_o)
    for w, pts in wires[layer]:
        tp = [T(p, mirror) for p in pts]; lw = max(1, int(w/1000*SC))
        d.line(tp, fill=col_t, width=lw, joint='curve')
        for (x, y) in tp: d.ellipse([x-lw/2, y-lw/2, x+lw/2, y+lw/2], fill=col_t)
    for q in pads[layer]: d.polygon([T(p, mirror) for p in q], fill=(235, 200, 90, 255))
    for (vx, vy) in vias:
        x, y = T((vx, vy), mirror); r = VD/2/1000*SC
        d.ellipse([x-r, y-r, x+r, y+r], fill=(200, 200, 200, 255)); r2 = 400/2/1000*SC
        d.ellipse([x-r2, y-r2, x+r2, y+r2], fill=(16, 24, 16, 255))
    d.text((8, 6), f"{layer} ({'viewed from top' if layer=='F.Cu' else 'viewed from bottom, mirrored'})", fill=(255,255,255,255))
    return img
a = draw_layer('F.Cu', False); b = draw_layer('B.Cu', True)
canvas = Image.new('RGB', (W*2+10, H), (0,0,0)); canvas.paste(a, (0,0)); canvas.paste(b, (W+10, 0))
canvas.save(out); print(canvas.size, len(wires['F.Cu']), len(wires['B.Cu']), len(vias))
