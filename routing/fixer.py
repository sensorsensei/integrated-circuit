import sys, re, os, shutil, subprocess, math, pcbnew
from pcbnew import FromMM, ToMM, VECTOR2I
src, dst = sys.argv[1:3]
K = r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe"
b = pcbnew.LoadBoard(src)
tmp = dst + ".tmp.kicad_pcb"
def drc():
    pcbnew.SaveBoard(tmp, b)
    shutil.copy(os.path.splitext(src)[0] + ".kicad_pro", os.path.splitext(tmp)[0] + ".kicad_pro")
    subprocess.run([K, "pcb", "drc", "--severity-all", "--format", "report", "-o", dst + ".rpt", tmp], capture_output=True)
    return open(dst + ".rpt", encoding="utf-8").read()
def items(blk):
    out = []
    for m in re.finditer(r"@\(([\d.]+) mm, ([\d.]+) mm\): (Track|Via|(?:PTH |SMD |NPTH )?[Pp]ad(?: \S+)?) (?:\[.*?\] )?(?:of (\w+) )?(?:on ([\w.]+)(?: - ([\w.]+))?)?", blk):
        out.append((float(m.group(1)), float(m.group(2)), m.group(3).split()[0] if m.group(3)[0] in "TV" else "Pad", m.group(3), m.group(4), m.group(5)))
    return out
def find_track(x, y, kind, layer):
    pos = VECTOR2I(FromMM(x), FromMM(y)); best = None
    for t in b.GetTracks():
        isvia = t.GetClass() == "PCB_VIA"
        if (kind == "Via") != isvia: continue
        if not isvia and layer and t.GetLayerName() != layer: continue
        if t.HitTest(pos, FromMM(0.03)): return t
    return None
def seg_nearest(a, c, p):
    ax, ay, cx, cy, px, py = a.x, a.y, c.x, c.y, p.x, p.y
    dx, dy = cx-ax, cy-ay; L = dx*dx+dy*dy
    t = 0 if L == 0 else max(0, min(1, ((px-ax)*dx + (py-ay)*dy)/L))
    return ax+t*dx, ay+t*dy
for it in range(12):
    txt = drc(); changed = 0; log = []
    for blk in txt.split("\n[")[1:]:
        head = blk.split("\n")[0]
        its = items(blk)
        if head.startswith("connection_width]"):
            for (x, y, kind, full, ref, layer) in its:
                if kind == "Track":
                    pos = VECTOR2I(FromMM(x), FromMM(y))
                    for t in b.GetTracks():
                        if t.GetClass() == "PCB_TRACK" and (not layer or t.GetLayerName() == layer) and t.HitTest(pos, FromMM(0.03)) and t.GetWidth() < FromMM(0.19):
                            t.SetWidth(FromMM(0.19)); changed += 1; log.append("widen")
        elif head.startswith("clearance]") and len(its) >= 2:
            m = re.search(r"clearance ([\d.]+) mm; actual ([\d.]+)", head); deficit = float(m.group(1)) - float(m.group(2))
            vias = [i for i in its if i[2] == "Via"]; trks = [i for i in its if i[2] == "Track"]; pads = [i for i in its if i[2] == "Pad" and i[4]]
            if vias and (trks or pads):
                v = find_track(vias[0][0], vias[0][1], "Via", None)
                if not v: continue
                p0 = v.GetPosition()
                if trks:
                    t = find_track(trks[0][0], trks[0][1], "Track", trks[0][5])
                    if not t: continue
                    nx, ny = seg_nearest(t.GetStart(), t.GetEnd(), p0)
                else:
                    nx, ny = FromMM(pads[0][0]), FromMM(pads[0][1])
                dx, dy = p0.x - nx, p0.y - ny; d = math.hypot(dx, dy) or 1
                mv = FromMM(deficit + 0.012); np_ = VECTOR2I(int(p0.x + dx/d*mv), int(p0.y + dy/d*mv))
                for t2 in b.GetTracks():
                    if t2.GetClass() == "PCB_TRACK":
                        if t2.GetStart() == p0: t2.SetStart(np_)
                        if t2.GetEnd() == p0: t2.SetEnd(np_)
                v.SetPosition(np_); changed += 1; log.append("via")
            elif pads and len(pads) == 1 and trks:
                key = pads[0][4]
                for f in b.GetFootprints():
                    if f.GetReference() == key:
                        num = re.search(r"[Pp]ad (\S+)", pads[0][3])
                        for p in f.Pads():
                            if num and p.GetNumber() == num.group(1):
                                s = p.GetSize(); d = FromMM(2*deficit + 0.006); p.SetSize(VECTOR2I(max(s.x-d, FromMM(0.15)), max(s.y-d, FromMM(0.15)))); changed += 1; log.append("pad")
    print("iter", it, "actions", log)
    if not changed: break
pcbnew.SaveBoard(dst, b)
for e in (tmp, os.path.splitext(tmp)[0] + ".kicad_pro", os.path.splitext(tmp)[0] + ".kicad_prl"):
    if os.path.exists(e): os.remove(e)
