import sys, json
sys.path.insert(0, sys.argv[1])
from orthoroute.infrastructure.serialization.orp_exporter import export_board_to_orp
export_board_to_orp(json.load(open(sys.argv[2])), sys.argv[3])
print("ORP written")
