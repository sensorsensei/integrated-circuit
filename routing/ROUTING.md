# How the board was routed (reference)

Board: `intg circt.kicad_pcb`, 4 layers (F.Cu, In1.Cu, In2.Cu, B.Cu), about 18 x 41 mm, 55 footprints, 80 nets.
Result: `intg circt_routed.kicad_pcb` with its `.kicad_pro`. It has 0 unconnected nets and 0 DRC violations
(KiCad 10 DRC, all severities, run with `--severity-all`). The original board file is never modified.

## 1. Design rules used

Taken from the Lion Circuits "Custom service" capabilities page (1 oz copper) and the constraints the project owner supplied.
Where the two differed, the stricter value was kept. They are applied by `setrules.py`, which `route.ps1` runs on a temporary copy of the `.kicad_pro`.

| Rule | Value |
|---|---|
| Track width, clearance, connection width | 0.152 mm (6 mil) |
| Via | 0.56 mm pad, 0.25 mm drill (annular ring 0.155 mm, minimum 0.152 mm) |
| Minimum via diameter / drill | 0.55 mm / 0.25 mm |
| Copper to board edge | 0.3 mm |
| Copper to hole, hole to hole | 0.254 mm |
| Silk clearance | 0.1524 mm |
| Silk text | height at least 0.5842 mm, thickness at least 0.152 mm |
| Microvia | 0.1 mm diameter, 0.5 mm hole (not used) |

Drill 0.25 mm needs the Custom service. The cheaper MII service starts at 0.35 mm.
Two library-sync checks (`lib_footprint_mismatch`, `lib_footprint_issues`) are set to ignore, because they depend on each PC's library tables and not on the board.
Everything else that was ignored in the project (courtyard, footprint filters and so on) was already ignored before.

## 2. Tools

- KiCad 10 (`C:\Program Files\KiCad\10.0\bin`): its bundled `python.exe` has `pcbnew`; `kicad-cli.exe` runs DRC.
- Freerouting 2.4.1 jar from the KiCad Freerouting plugin, run with Java 21 or newer.
- Everything is driven by `route.ps1`: apply rules, export Specctra DSN, run Freerouting, import the SES result.

```powershell
.\routing\route.ps1 -Board "<path>\board.kicad_pcb" -MaxPasses 100 -TimeoutMinutes 30
```

Output goes next to the input as `<name>_routed.kicad_pcb` and `.kicad_pro`.

## 2a. Running Freerouting step by step

Freerouting does the autorouting. These are the exact steps used, from a plain board file to a routed one.

**Requirements**
- KiCad 10 and Java 21 or newer (`java -version`).
- The Freerouting jar. It ships with the KiCad Freerouting plugin at `Documents\KiCad.0rdparty\pluginspp_freerouting_kicad-plugin\jarreerouting-2.4.1.jar`. Install the plugin from KiCad's Plugin and Content Manager if the folder is missing.

**Option A: one command (recommended)**

```powershell
cd "D:. saurabh\watch\integrated circuit"
.outingoute.ps1 -Board ".\intg circt.kicad_pcb" -MaxPasses 100 -TimeoutMinutes 30
```

The script does these five things in a temp folder with no spaces in its name:
1. Copies the board and `.kicad_pro` there, so the original is never touched.
2. Runs `setrules.py` to write the fab rules from section 1 into the copied `.kicad_pro`.
3. Exports a Specctra DSN with KiCad's Python (`export_dsn.py`, which calls `pcbnew.ExportSpecctraDSN`). The DSN carries the rules, pads, nets and existing tracks.
4. Runs Freerouting on the DSN and writes a session file:

   ```
   java -jar freerouting-2.4.1.jar --gui.enabled=false -de board.dsn -do board.ses -mp 100
   ```

   The flags are: `--gui.enabled=false` for headless mode, `-de` for the input DSN, `-do` for the output SES, `-mp` for the maximum number of passes.
5. Imports the session back into the board with KiCad's Python (`import_ses.py`, which calls `pcbnew.ImportSpecctraSES`) and saves `<name>_routed.kicad_pcb` plus the matching `.kicad_pro` next to the input.

**Reading the progress**

Freerouting prints one line per pass in `freerouting.log` in the temp folder (for example `%TEMP%oute_intg_circtreerouting.log`):
- A fanout stage escapes the SMD pins first.
- An auto-routing stage then reports `N unrouted and M violations` after each pass. It is finished when the unrouted count reaches 0 or stops falling.
- An optimization stage follows and tidies the tracks.

The line `Saving output file ...board.ses` means the result was written. If no `.ses` appears, read the log. The two failures we hit were a path with spaces (Java reports `file not found`) and the GUI crash on save, which headless mode avoids.

**Option B: run several variants in parallel (what produced the final board)**

Freerouting gives different results from run to run, and a small placement change gives a different result again. Run many copies and keep the best one.

```powershell
$r = "D:. saurabh\watch\integrated circuitoutingoute.ps1"
foreach ($v in 'q1','q2','q3','q4','q5','q6','q7','q8') {
  # each variant lives in its own folder: <v>\<v>.kicad_pcb and <v>\<v>.kicad_pro
  Start-Process powershell -WindowStyle Hidden -ArgumentList '-NoProfile','-File',"`"$r`"",
    '-Board',"`"C:\work\$v\$v.kicad_pcb`"",'-MaxPasses','100','-TimeoutMinutes','30'
}
```

Each run needs a different base name, because the temp work folder is named after the board. Eight runs at once used about 25 GB of memory and finished in roughly 10 minutes on a 32-thread machine. To compare them afterwards, look at the last auto-routing line in each `freerouting.log` for the unrouted count, or run KiCad DRC on each `*_routed.kicad_pcb`. Then continue with the cleanup in section 4 on the best one.

**Option C: interactive, with the window**

In the KiCad PCB editor use Tools, External Plugins, Freerouting. This opens the Freerouting window so you can watch the routing live. It was not used for the final board, because the headless run is repeatable and scriptable.

## 3. Problems found in the original script, and fixes

- **Spaces in the path.** The project folder and board name contain spaces. The temp folder name was derived from the board name, and the jar arguments were not quoted, so Java saw a split path and failed with "file not found". Fixed by sanitising the work folder name and quoting the arguments.
- **GUI crash.** Freerouting's GUI mode threw a NullPointerException when saving the session, so no `.ses` was produced. Fixed by running with `--gui.enabled=false`.
- **Too few passes.** The default stopped after about 3 passes with 43 unrouted. `-MaxPasses 100` is now the default.

## 4. The routing pipeline (what actually produced the final board)

Run in this order. Helper scripts live in `routing/` and use KiCad's Python.

1. **Fix footprint geometry that violates the rules by itself** (`shrink.py`).
   Some footprints have pad gaps of 0.146 to 0.150 mm (rule 0.152 mm): U2, U7, U3, J3, J5. The USB-C connector J2 has GND pads closer to its mounting hole than 0.254 mm.
   The script reads the DRC report and shrinks only the offending pads by just enough (a few hundredths of a mm). For J2 only the long dimension was shrunk, so the pad width and pitch stay as they were.
   This removed every pad-to-pad clearance error before routing even started.
2. **Placement tweaks** (`randplace.py`).
   Routing the original placement left 3 to 4 nets open, always in the same dense corner (U2, U4, R1, R4, C2 and the USB data lines).
   The script moves a random subset of bottom-side resistors, capacitors and diodes by 1 to 4 mm to free spots, rejecting any move that collides with another part or the board edge.
   Eight seeds were generated. Seed 3 was the best.
3. **Autoroute many variants in parallel.**
   Freerouting is not deterministic with many threads, and a tiny placement change gives a different result. Eight runs at once finished in about 10 minutes.
   Pick the run with the fewest unrouted nets. The winning run (seed 3) completed all 80 nets. Earlier batches of 4 had stopped at 1 to 3 unrouted.
4. **Cleanup** (`clean.py`).
   - Move reference and value text from silkscreen to the fab layers (this removes about 150 silk clearance and text thickness warnings).
   - Delete mirrored pin labels on U7.
   - Widen any track narrower than 0.152 mm. Freerouting necks some tracks down to 0.114 mm near fine-pitch pads.
   - Loop on DRC and delete only the silkscreen graphics that DRC still flags.
5. **Residual repair** (`repair.py` then `fixer.py`).
   Each one reads the DRC report, applies a small repair and re-runs DRC until nothing changes:
   - track too close to a pad: shrink that pad slightly,
   - track too close to a via: move the via a few hundredths of a mm and drag the attached track ends with it,
   - "copper connection too narrow": widen the tracks at that point to 0.19 mm,
   - un-mirror text on the back layer.
6. **Verify** with `kicad-cli pcb drc --severity-all --all-track-errors`. Expect 0 violations and 0 unconnected.

## 5. Things that did not work

- **Re-routing an already routed board** (feeding the routed result back into Freerouting) made it worse (3 unrouted became 5).
- **A GND copper plane on In1.Cu**: Freerouting did not use it and ended with more unrouted nets (13 against 4).
- **Moving many parts toward their connected pins** (`nudge`, 29 parts): 3 unrouted. Moving 6 specific parts: worse. Random small moves plus many parallel runs was what worked.
- **A custom maze router for the last few nets**: it correctly proved that the pad escape areas were boxed in on the bottom layer, so no local fix existed. Rip-up of neighbours was needed, which is what the parallel runs achieve.
- **GPU routing.** Freerouting has no GPU mode. OrthoRoute (GPU) was tried, see below.

## 6. OrthoRoute on the GPU (tried)

OrthoRoute is a CuPy/CUDA router meant for large backplanes. It is a KiCad IPC plugin, and its headless mode needs an `.ORP` file that only the plugin exports.
It was run anyway on the RTX 4000 Ada:

- Environment: a Python venv with `cupy-cuda12x`, `numpy`, `kicad-python`, and the NVIDIA runtime wheels (`nvidia-cuda-nvrtc-cu12`, `nvidia-cublas-cu12`, `nvidia-cusparse-cu12`, `nvidia-cusolver-cu12`, `nvidia-curand-cu12`, `nvidia-cufft-cu12`, `nvidia-nvjitlink-cu12`). About 1.5 GB of downloads. On Windows the DLL folders must be added with `os.add_dll_directory`, which `orthoroute_gpu/gpu_run.py` does.
- `orthoroute_gpu/ortho_export.py` builds the router's board description straight from the `.kicad_pcb`, `ortho_orp.py` writes the `.ORP`, and `ortho_import.py` turns the `.ORS` solution back into tracks and vias.
- The router's design rules are built-in defaults, not read from the board. They were patched in the local clone to 0.152 mm track and clearance, 0.56 mm via, 0.35 mm grid.
- Outcome: it ran on the GPU and reported "converged" with zero congestion, but only 23 of 34 nets were routed. Imported into KiCad, the result still had 183 unconnected items (the unrouted board started with 179) and 528 DRC violations. It models pads as circles and ignores existing obstacles, and its own README says it is not a general-purpose autorouter. Freerouting on the CPU was far better for this small dense board, so OrthoRoute was not used for the final result.

## 7. Reproducing from scratch

1. Run `route.ps1` on the board (or on several `randplace.py` variants in parallel) and take the best `*_routed.kicad_pcb`.
2. `clean.py in.kicad_pcb c.kicad_pcb`, then `repair.py c.kicad_pcb d.kicad_pcb`, then `fixer.py d.kicad_pcb e.kicad_pcb`. Each script needs a `.kicad_pro` with the same base name next to its input.
3. Run DRC with all severities and confirm 0 violations.

Notes: the helper scripts assume KiCad 10 at `C:\Program Files\KiCad\10.0`. Run them with KiCad's own `python.exe`. Freerouting results vary from run to run, so do not expect the exact same board twice. The final board in this repo is the reference result.
