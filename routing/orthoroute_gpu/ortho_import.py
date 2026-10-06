import sys, json, gzip, pcbnew
from pcbnew import FromMM, VECTOR2I
src, ors, dst = sys.argv[1:4]
b = pcbnew.LoadBoard(src)
try: d = json.load(gzip.open(ors, "rt", encoding="utf-8"))
except Exception: d = json.load(open(ors, encoding="utf-8"))
names = [b.GetLayerName(l) for l in b.GetEnabledLayers().CuStack()]
for t in list(b.GetTracks()): b.Remove(t)
nt = nv = 0
for net_id, g in d["geometry"]["by_net"].items():
    net = b.FindNet(net_id)
    if net is None: print("unknown net", net_id); continue
    for t in g["tracks"]:
        s, e = t["start"], t["end"]
        if abs(s["x"]-e["x"]) < 1e-6 and abs(s["y"]-e["y"]) < 1e-6: continue
        tr = pcbnew.PCB_TRACK(b); tr.SetStart(VECTOR2I(FromMM(s["x"]), FromMM(s["y"]))); tr.SetEnd(VECTOR2I(FromMM(e["x"]), FromMM(e["y"])))
        tr.SetLayer(b.GetLayerID(names[int(t["layer"])]) if not isinstance(t["layer"], str) else b.GetLayerID(t["layer"]))
        tr.SetWidth(max(FromMM(t["width"]), FromMM(0.152))); tr.SetNet(net); b.Add(tr); nt += 1
    for v in g["vias"]:
        via = pcbnew.PCB_VIA(b); via.SetPosition(VECTOR2I(FromMM(v["position"]["x"]), FromMM(v["position"]["y"])))
        via.SetViaType(pcbnew.VIATYPE_THROUGH); via.SetWidth(pcbnew.F_Cu, FromMM(0.6)); via.SetDrill(FromMM(0.25)); via.SetNet(net); b.Add(via); nv += 1
print(nt, "tracks", nv, "vias")
pcbnew.SaveBoard(dst, b)
