import sys, json, pcbnew
src, out = sys.argv[1:3]
b = pcbnew.LoadBoard(src)
mm = lambda v: v / 1e6
bb = b.GetBoardEdgesBoundingBox()
names = [b.GetLayerName(l) for l in b.GetEnabledLayers().CuStack()]
pads, nets = [], {}
for f in b.GetFootprints():
    for p in f.Pads():
        n = p.GetNet()
        if n.GetNetCode() == 0 or p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH: continue
        lyr = [b.GetLayerName(l) for l in p.GetLayerSet().CuStack()]
        pos = p.GetPosition()
        d = {"x": mm(pos.x), "y": mm(pos.y), "component": f.GetReference(), "name": p.GetNumber(),
             "net_name": n.GetNetname(), "net_code": n.GetNetCode(),
             "width": mm(p.GetSize().x), "height": mm(p.GetSize().y),
             "drill": mm(p.GetDrillSizeX()) if p.GetDrillSizeX() else None, "layers": lyr,
             "type": "through" if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH else "smd"}
        pads.append(d)
        nets.setdefault(n.GetNetname(), {"name": n.GetNetname(), "code": n.GetNetCode(), "pads": []})["pads"].append(d)
bd = {"filename": "board.kicad_pcb", "x_min": mm(bb.GetLeft()), "y_min": mm(bb.GetTop()), "x_max": mm(bb.GetRight()), "y_max": mm(bb.GetBottom()),
      "width": mm(bb.GetWidth()), "height": mm(bb.GetHeight()), "layers": len(names), "layer_names": names, "thickness": 1.6,
      "pads": pads, "nets": nets, "track_width": 0.152, "clearance": 0.152, "via_diameter": 0.6, "via_drill": 0.25,
      "min_track_width": 0.152, "min_clearance": 0.152, "min_via_diameter": 0.55, "min_via_drill": 0.25, "grid_resolution": 0.35}
json.dump(bd, open(out, "w"))
print(len(pads), "pads", len(nets), "nets", names)
