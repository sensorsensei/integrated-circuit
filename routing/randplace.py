import sys, random, pcbnew
from pcbnew import VECTOR2I, FromMM, ToMM
src, dst, seed, nmove = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
random.seed(seed)
b = pcbnew.LoadBoard(src)
ol = pcbnew.SHAPE_POLY_SET(); b.GetBoardPolygonOutlines(ol, True)
inset = pcbnew.SHAPE_POLY_SET(ol); inset.Inflate(-FromMM(0.5), pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, FromMM(0.1))
M = FromMM(0.1)
def bbox(f):
    r = f.GetBoundingBox(False); r.Inflate(M); return r
def inside(r): return all(inset.Contains(VECTOR2I(x, y)) for x in (r.GetLeft(), r.GetRight()) for y in (r.GetTop(), r.GetBottom()))
fps = list(b.GetFootprints())
def free(f):
    r = bbox(f)
    if not inside(r): return False
    for o in fps:
        if o.GetReference() == f.GetReference(): continue
        if o.GetLayer() == f.GetLayer() or any(p.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH) for p in o.Pads()):
            if r.Intersects(bbox(o)): return False
    return True
cands = [f for f in fps if f.IsFlipped() and not f.IsLocked() and f.GetReference()[0] in "RCD" or f.GetReference() == "TH1"]
moved = []
for f in random.sample(cands, min(nmove, len(cands))):
    home = f.GetPosition(); rot = f.GetOrientationDegrees()
    for _ in range(60):
        r = random.choice([1.0, 1.5, 2.5, 4.0]); dx = random.uniform(-r, r); dy = random.uniform(-r, r)
        f.SetPosition(VECTOR2I(home.x + FromMM(dx), home.y + FromMM(dy)))
        if random.random() < 0.3: f.SetOrientationDegrees(rot + 90)
        if free(f): moved.append(f.GetReference()); break
        f.SetOrientationDegrees(rot); f.SetPosition(home)
print(seed, "moved", moved)
pcbnew.SaveBoard(dst, b)
