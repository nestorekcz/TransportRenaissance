# Local config and explicit log handles are required by this MinGW GUI build.
[CmdletBinding()]
param([switch]$Generate, [switch]$Demo, [switch]$ReducedMotion)
$ErrorActionPreference = 'Stop'
$runtime = $PSScriptRoot
$config = if ($Generate -or $Demo) { 'coastal-demo.cfg' } else { 'openttd.cfg' }
if ($ReducedMotion) {
    $text = Get-Content "$runtime/$config" -Raw
    $config = 'reduced-motion.cfg'
    $text = $text.Replace('smooth_water = true', 'smooth_water = false')
    $text = $text.Replace('[misc]', "[misc]`ndisplay_opt = SHOW_TOWN_NAMES|SHOW_STATION_NAMES|SHOW_SIGNS|FULL_DETAIL|WAYPOINTS|SHOW_COMPETITOR_SIGNS")
    Set-Content -LiteralPath "$runtime/$config" -Value $text -Encoding utf8
}
$gameArguments = @('-X', '-c', $config)
if ($Generate -or $Demo) { $gameArguments += '-x' }
if ($Generate) { $gameArguments += @('-g', 'scenario/heightmap/renaissance-coast.png', '-G', '20261101') }
elseif ($Demo) { $gameArguments += @('-g', 'save/renaissance-coast.sav') }
Start-Process -FilePath "$runtime/openttd.exe" -WorkingDirectory $runtime -ArgumentList $gameArguments -RedirectStandardOutput "$runtime/stdout.log" -RedirectStandardError "$runtime/stderr.log"
