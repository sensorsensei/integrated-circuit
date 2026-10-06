"""Apply fab design rules to a .kicad_pro file in place. Usage: setrules.py <file.kicad_pro>"""
import json, sys

f = sys.argv[1]
p = json.load(open(f, encoding="utf-8"))
ds = p["board"]["design_settings"]
ds["rules"].update({
    "min_clearance": 0.152,
    "min_track_width": 0.152,
    "min_connection": 0.152,
    "min_via_annular_width": 0.254,
    "min_via_diameter": 0.762,
    "min_hole_clearance": 0.254,
    "min_copper_edge_clearance": 0.3,
    "min_through_hole_diameter": 0.254,
    "min_hole_to_hole": 0.254,
    "min_silk_clearance": 0.1524,
    "min_text_height": 0.8,
    "min_text_thickness": 0.08,
})
ds["via_dimensions"] = [{"diameter": 0.762, "drill": 0.254}]
ds["defaults"]["zones"]["min_clearance"] = 0.152
for c in p["net_settings"]["classes"]:
    if c["name"] == "Default":
        c.update({"clearance": 0.152, "track_width": 0.152,
                  "via_diameter": 0.762, "via_drill": 0.254})
json.dump(p, open(f, "w", encoding="utf-8"), indent=2)
