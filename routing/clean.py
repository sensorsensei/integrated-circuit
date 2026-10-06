import sys, re, subprocess, os, pcbnew
from pcbnew import FromMM, VECTOR2I
src, dst = sys.argv[1:3]
K = r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe"
b = pcbnew.LoadBoard(src)
SILK = (b.GetLayerID("F.SilkS"), b.GetLayerID("B.SilkS"))
keep = []
# A: reference/value text to fab layer; widen thin tracks
for f in b.GetFootprints():
    fab = b.GetLayerID("B.Fab" if f.IsFlipped() else "F.Fab")
    for fld in (f.Reference(), f.Value()):
        if fld.GetLayer() in SILK: fld.SetLayer(fab)
for f in b.GetFootprints():
    for g in list(f.GraphicalItems()):
        if g.GetClass() == "PCB_TEXT" and g.GetLayer() in SILK:
            f.Remove(g); keep.append(g)
for t in b.GetTracks():
    if t.GetClass() == "PCB_TRACK" and t.GetWidth() < FromMM(0.152): t.SetWidth(FromMM(0.152))
tmp = dst + ".tmp.kicad_pcb"
def drc():
    pcbnew.SaveBoard(tmp, b)
    shutil_pro = os.path.splitext(src)[0] + ".kicad_pro"
    if os.path.exists(shutil_pro):
        import shutil; shutil.copy(shutil_pro, os.path.splitext(tmp)[0] + ".kicad_pro")
    rpt = dst + ".rpt"
    subprocess.run([K, "pcb", "drc", "--severity-all", "--format", "report", "-o", rpt, tmp], capture_output=True)
    return open(rpt, encoding="utf-8").read()
for it in range(8):
    txt = drc(); removed = 0; seen = set()
    for blk in txt.split("\n[")[1:]:
        head = blk.split("\n")[0]
        if not re.match(r"(silk_overlap|silk_over_copper|text_thickness|text_height)\]", head): continue
        for m in re.finditer(r"@\(([\d.]+) mm, ([\d.]+) mm\): (.*?) of (\w+)(?: \(.*?\))? on ([FB])\.Silkscreen", blk):
            x, y, kind, ref, side = float(m.group(1)), float(m.group(2)), m.group(3), m.group(4), m.group(5)
            pos = VECTOR2I(FromMM(x), FromMM(y))
            for f in b.GetFootprints():
                if f.GetReference() != ref: continue
                for g in list(f.GraphicalItems()):
                    if g.GetLayer() in SILK and g.HitTest(pos, FromMM(0.3)) and id(g) not in seen:
                        f.Remove(g); keep.append(g); removed += 1; break
    print("iter", it, "removed", removed, "violations:", re.findall(r"Found (\d+) violations", txt))
    if not removed: break
pcbnew.SaveBoard(dst, b)
for e in (tmp, os.path.splitext(tmp)[0] + ".kicad_pro", os.path.splitext(tmp)[0] + ".kicad_prl"):
    if os.path.exists(e): os.remove(e)
