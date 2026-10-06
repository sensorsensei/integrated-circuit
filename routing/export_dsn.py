import sys, pcbnew
board = pcbnew.LoadBoard(sys.argv[1])
ok = pcbnew.ExportSpecctraDSN(board, sys.argv[2])
sys.exit(0 if ok else 1)
