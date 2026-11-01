# Local config and explicit log handles are required by this MinGW GUI build.
[CmdletBinding()]
param([switch]$Generate, [switch]$ReducedMotion)
$ErrorActionPreference = 'Stop'
$runtime = $PSScriptRoot
$config = 'openttd.cfg'
if ($ReducedMotion) {
    $config = 'reduced-motion.cfg'
    $text = Get-Content "$runtime/openttd.cfg" -Raw
    $text = $text.Replace('smooth_water = true', 'smooth_water = false')
    $text = $text.Replace('[misc]', "[misc]`ndisplay_opt = SHOW_TOWN_NAMES|SHOW_STATION_NAMES|SHOW_SIGNS|FULL_DETAIL|WAYPOINTS|SHOW_COMPETITOR_SIGNS")
    Set-Content -LiteralPath "$runtime/$config" -Value $text -Encoding utf8
}
$scene = if ($Generate) { 'scenario/heightmap/renaissance-coast.png' } else { 'save/renaissance-coast.sav' }
Start-Process -FilePath "$runtime/openttd.exe" -WorkingDirectory $runtime -ArgumentList @('-X', '-x', '-c', $config, '-g', $scene, '-G', '20261101') -RedirectStandardOutput "$runtime/stdout.log" -RedirectStandardError "$runtime/stderr.log"
