<#
.SYNOPSIS
  Apply fab rules, export DSN, run Freerouting, import the result. Works on any Windows user/PC.
.EXAMPLE
  .\routing\route.ps1
  .\routing\route.ps1 -Board "..\other.kicad_pcb" -MaxPasses 100
  .\routing\route.ps1 -JarPath D:\tools\freerouting.jar -KiCadPython "D:\KiCad\10.0\bin\python.exe"
.NOTES
  Original board is never modified. Output: <name>_routed.kicad_pcb (+ .kicad_pro) next to the input.
#>
[CmdletBinding()]
param(
    [string]$Board,
    [string]$JarPath,
    [string]$KiCadPython,
    [int]$MaxPasses = 100,           # 0 = Freerouting default
    [int]$TimeoutMinutes = 60,
    [switch]$SkipRules              # keep the .kicad_pro rules untouched
)
$ErrorActionPreference = 'Stop'
$here = $PSScriptRoot

# --- board ---
if (-not $Board) {
    $Board = (Get-ChildItem (Split-Path $here) -Filter *.kicad_pcb | Select-Object -First 1).FullName
}
if (-not $Board -or -not (Test-Path -LiteralPath $Board)) { throw "Board not found. Pass -Board <file.kicad_pcb>." }
$Board = (Resolve-Path -LiteralPath $Board).Path
$name  = [IO.Path]::GetFileNameWithoutExtension($Board)
$dir   = Split-Path $Board
$pro   = Join-Path $dir "$name.kicad_pro"

# --- KiCad python ---
if (-not $KiCadPython) {
    $roots = @($env:ProgramFiles, ${env:ProgramFiles(x86)}, "$env:LOCALAPPDATA\Programs") | Where-Object { $_ }
    $KiCadPython = $roots | ForEach-Object { Get-ChildItem "$_\KiCad\*\bin\python.exe" -ErrorAction SilentlyContinue } |
        Sort-Object { [version]($_.Directory.Parent.Name -replace '[^\d\.]', '') } -Descending |
        Select-Object -First 1 -ExpandProperty FullName
}
if (-not $KiCadPython -or -not (Test-Path $KiCadPython)) { throw "KiCad python.exe not found. Pass -KiCadPython." }

# --- Freerouting jar ---
if (-not $JarPath) {
    $docs = [Environment]::GetFolderPath('MyDocuments')
    $cands = @(
        "$docs\KiCad\*\3rdparty\plugins\app_freerouting_kicad-plugin\jar\freerouting*.jar",
        "$env:USERPROFILE\Documents\KiCad\*\3rdparty\plugins\app_freerouting_kicad-plugin\jar\freerouting*.jar",
        "$env:USERPROFILE\Downloads\freerouting*.jar",
        "$here\freerouting*.jar"
    )
    $JarPath = $cands | ForEach-Object { Get-ChildItem $_ -ErrorAction SilentlyContinue } |
        Sort-Object Name -Descending | Select-Object -First 1 -ExpandProperty FullName
}
if (-not $JarPath -or -not (Test-Path $JarPath)) { throw "freerouting jar not found. Pass -JarPath." }

# --- java ---
$java = if ($env:JAVA_HOME -and (Test-Path "$env:JAVA_HOME\bin\java.exe")) { "$env:JAVA_HOME\bin\java.exe" }
        else { (Get-Command java -ErrorAction SilentlyContinue).Source }
if (-not $java) { throw "java not found. Install JDK 21+ or set JAVA_HOME." }

Write-Host "Board  : $Board`nPython : $KiCadPython`nJar    : $JarPath`nJava   : $java"

# --- work dir (copy, original untouched) ---
$work = Join-Path ([IO.Path]::GetTempPath()) ("route_" + ($name -replace '[^A-Za-z0-9_]', '_'))
if (Test-Path $work) { Remove-Item $work -Recurse -Force }
New-Item -ItemType Directory $work | Out-Null
Copy-Item -LiteralPath $Board (Join-Path $work 'board.kicad_pcb')
if (Test-Path -LiteralPath $pro) { Copy-Item -LiteralPath $pro (Join-Path $work 'board.kicad_pro') }

if (-not $SkipRules -and (Test-Path (Join-Path $work 'board.kicad_pro'))) {
    & $KiCadPython (Join-Path $here 'setrules.py') (Join-Path $work 'board.kicad_pro')
    if ($LASTEXITCODE) { throw "setrules.py failed" }
}

& $KiCadPython (Join-Path $here 'export_dsn.py') (Join-Path $work 'board.kicad_pcb') (Join-Path $work 'board.dsn')
if ($LASTEXITCODE) { throw "DSN export failed" }

# --- route ---
$args = @('-jar', "`"$JarPath`"", '--gui.enabled=false', '-de', "`"$(Join-Path $work 'board.dsn')`"", '-do', "`"$(Join-Path $work 'board.ses')`"")
if ($MaxPasses -gt 0) { $args += @('-mp', $MaxPasses) }
$log = Join-Path $work 'freerouting.log'
$proc = Start-Process $java -ArgumentList $args -NoNewWindow -PassThru -RedirectStandardOutput $log -RedirectStandardError "$log.err"
if (-not $proc.WaitForExit($TimeoutMinutes * 60000)) { $proc.Kill(); Write-Warning "Timeout, using whatever was saved." }
Get-Content $log | Select-String 'score|Saving|unrouted' | Select-Object -Last 5 | ForEach-Object { $_.Line }
if (-not (Test-Path (Join-Path $work 'board.ses'))) { throw "No .ses produced. See $log" }

# --- import ---
$out = Join-Path $dir "${name}_routed.kicad_pcb"
& $KiCadPython (Join-Path $here 'import_ses.py') (Join-Path $work 'board.kicad_pcb') (Join-Path $work 'board.ses') $out
if ($LASTEXITCODE) { throw "SES import failed" }
if (Test-Path (Join-Path $work 'board.kicad_pro')) { Copy-Item (Join-Path $work 'board.kicad_pro') (Join-Path $dir "${name}_routed.kicad_pro") -Force }
Write-Host "Done: $out"
