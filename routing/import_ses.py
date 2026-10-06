import sys, pcbnew
board = pcbnew.LoadBoard(sys.argv[1])
if not pcbnew.ImportSpecctraSES(board, sys.argv[2]):
    sys.exit(1)
pcbnew.SaveBoard(sys.argv[3], board)
