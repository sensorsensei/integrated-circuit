import sys, re, os, shutil, subprocess, pcbnew
from pcbnew import FromMM, VECTOR2I
src, dst = sys.argv[1:3]
K = r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe"
b = pcbnew.LoadBoard(src)
for f in b.GetFootprints():
    if f.IsFlipped():
        for fld in f.GetFields():
            if fld.GetLayerName().startswith("B.") and not fld.IsMirrored(): fld.SetMirrored(True)
tmp = dst + ".tmp.kicad_pcb"
def drc():
    pcbnew.SaveBoard(tmp, b)
    shutil.copy(os.path.splitext(src)[0] + ".kicad_pro", os.path.splitext(tmp)[0] + ".kicad_pro")
    subprocess.run([K, "pcb", "drc", "--severity-all", "--format", "report", "-o", dst + ".rpt", tmp], capture_output=True)
    return open(dst + ".rpt", encoding="utf-8").read()
for it in range(4):
    txt = drc(); need = {}
    for blk in txt.split("\n[")[1:]:
        l = blk.split("\n"); m = re.search(r"clearance ([\d.]+) mm; actual ([\d.]+)", l[0])
        if not (l[0].startswith("clearance]") or l[0].startswith("hole_clearance]")) or not m: continue
        deficit = float(m.group(1)) - float(m.group(2))
        for x in l[2:5]:
            pm = re.search(r"(?:PTH |SMD )?Pad (\S+)(?: \[.*?\])? of (\w+)", x)
            if pm and pm.group(1) != "of": need[(pm.group(2), pm.group(1))] = max(need.get((pm.group(2), pm.group(1)), 0), 2*deficit + 0.006)
    print("iter", it, "pads to shrink", need)
    if not need: break
    for f in b.GetFootprints():
        for p in f.Pads():
            k = (f.GetReference(), p.GetNumber())
            if k in need:
                s = p.GetSize(); d = FromMM(need[k]); p.SetSize(VECTOR2I(max(s.x - d, FromMM(0.15)), max(s.y - d, FromMM(0.15))))
pcbnew.SaveBoard(dst, b)
for e in (tmp, os.path.splitext(tmp)[0] + ".kicad_pro", os.path.splitext(tmp)[0] + ".kicad_prl"):
    if os.path.exists(e): os.remove(e)
