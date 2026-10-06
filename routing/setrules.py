"""Apply fab design rules to a .kicad_pro file in place. Usage: setrules.py <file.kicad_pro>"""
import json, sys

f = sys.argv[1]
p = json.load(open(f, encoding="utf-8"))
ds = p["board"]["design_settings"]
# Source: lioncircuits.com/pcb-manufacturing-capabilities, "Custom Service", 1oz copper
ds["rules"].update({
    "min_clearance": 0.152,            # 6 mil trace spacing
    "min_track_width": 0.152,          # 6 mil trace width
    "min_connection": 0.152,
    "min_via_annular_width": 0.152,    # 6 mil annular ring
    "min_via_diameter": 0.55,
    "min_hole_clearance": 0.254,       # via to trace >= 10 mil
    "min_copper_edge_clearance": 0.3,  # circuit to edge >= 0.3 mm
    "min_through_hole_diameter": 0.25,  # drill 0.25-6.3 mm
    "min_hole_to_hole": 0.254,         # via to via >= 10 mil
    "min_silk_clearance": 0.1524,      # silk to pad >= 6 mil
    "min_text_height": 0.5842,         # 23 mil
    "min_text_thickness": 0.152,       # 6 mil
    "min_microvia_diameter": 0.1,
    "min_microvia_drill": 0.5,
})
ds["via_dimensions"] = [{"diameter": 0.56, "drill": 0.25}]
ds["defaults"]["zones"]["min_clearance"] = 0.152
for c in p["net_settings"]["classes"]:
    if c["name"] == "Default":
        c.update({"clearance": 0.152, "track_width": 0.152,
                  "via_diameter": 0.56, "via_drill": 0.25})
# footprint-library sync warnings depend on each PC's library tables, not on the board itself
for k in ("lib_footprint_mismatch", "lib_footprint_issues"):
    ds.setdefault("rule_severities", {})[k] = "ignore"
json.dump(p, open(f, "w", encoding="utf-8"), indent=2)
