import os, sys, glob, runpy
site = os.path.join(sys.prefix, "Lib", "site-packages", "nvidia")
bins = glob.glob(os.path.join(site, "*", "bin"))
for d in bins: os.add_dll_directory(d)
os.environ["PATH"] = os.pathsep.join(bins) + os.pathsep + os.environ.get("PATH", "")
os.environ["CUDA_PATH"] = os.path.join(site, "cuda_nvrtc")
script = sys.argv[1]; sys.argv = sys.argv[1:]
sys.path.insert(0, os.path.dirname(os.path.abspath(script)))
runpy.run_path(script, run_name="__main__")
