import sys, re, pcbnew
from pcbnew import FromMM, ToMM, VECTOR2I
src, dst, rpt = sys.argv[1:4]
b = pcbnew.LoadBoard(src)
need = {}; holekeys = set()   # (ref,padname) -> shrink amount mm (total size reduction)
for blk in open(rpt, encoding='utf-8').read().split('\n[')[1:]:
    l = blk.split('\n'); head = l[0]
    m = re.search(r'(clearance|hole clearance) ([\d.]+) mm; actual ([\d.]+)', head)
    if not (head.startswith('clearance]') or head.startswith('hole_clearance]')) or not m: continue
    req, act = float(m.group(2)), float(m.group(3))
    items = [re.search(r'(?:PTH |SMD |NPTH )?[Pp]ad (\S+)(?: \[.*?\])? of (\w+)', x) for x in l[2:5]]
    items = [i for i in items if i]
    if (len(items) < 2 and not head.startswith('hole')) or any('Track' in x or 'Via' in x for x in l[2:5]): continue
    deficit = req - act
    hole = head.startswith('hole')
    for it in items:
        if it.group(1) == 'of': continue  # NPTH
        d = (2*deficit + 0.02) if hole else (deficit/1 + 0.004)
        key = (it.group(2), it.group(1)); holekeys.add(key) if hole else None
        need[key] = max(need.get(key, 0), d)
        if hole: break
n = 0
for f in b.GetFootprints():
    for p in f.Pads():
        k = (f.GetReference(), p.GetNumber())
        if k in need:
            s = p.GetSize(); d = FromMM(need[k])
            p.SetSize(VECTOR2I(s.x, s.y - d) if (k in holekeys and s.y >= s.x) else VECTOR2I(s.x - d, s.y) if k in holekeys else VECTOR2I(s.x - d, s.y - d)); n += 1
            print(k, round(ToMM(s.x),3), round(ToMM(s.y),3), "->", round(ToMM(s.x-d),3), round(ToMM(s.y-d),3), p.GetDrillSizeX()/1e6)
print(n, "pads shrunk"); pcbnew.SaveBoard(dst, b)
