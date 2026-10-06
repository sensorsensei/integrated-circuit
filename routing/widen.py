import sys, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); n=0
for t in b.GetTracks():
    if t.GetClass()=="PCB_TRACK" and t.GetWidth() < 152000:
        t.SetWidth(152000); n+=1
print("widened", n)
pcbnew.SaveBoard(sys.argv[2], b)
