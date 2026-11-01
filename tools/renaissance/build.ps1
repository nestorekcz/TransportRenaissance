# Build, test and stage a native Windows playable. GPL-2.0-only.
[CmdletBinding()]
param(
    [string]$Workspace = (Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent),
    [switch]$Baseline,
    [switch]$Dedicated,
    [switch]$SkipTests
)
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$Workspace = [IO.Path]::GetFullPath($Workspace)
$toolRoot = Join-Path $Workspace 'tools'
$artifactRoot = Join-Path $Workspace 'artifacts'
$lock = Get-Content (Join-Path $PSScriptRoot 'dependencies.json') -Raw | ConvertFrom-Json
$compiler = Join-Path $toolRoot $lock.compiler.name
$env:PATH = "$compiler/bin;$toolRoot/python/Scripts;$env:PATH"
function Run([string]$Executable, [string[]]$Arguments) {
    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) { throw "$Executable failed with exit code $LASTEXITCODE" }
}
$source = $repo
$name = 'fork'
if ($Baseline) {
    $source = "$artifactRoot/upstream-source"
    if (!(Test-Path -LiteralPath $source)) { Run 'git' @('-C', $repo, 'worktree', 'add', '--detach', $source, $lock.upstream.commit) }
    $actual = & git -C $source rev-parse HEAD
    $dirty = & git -C $source status --porcelain
    if ($actual -ne $lock.upstream.commit -or $dirty) { throw 'Baseline source must be pristine and pinned' }
    $name = 'pinned-baseline'
}
if ($Dedicated) { $name += '-dedicated' }
$build = "$artifactRoot/$name-build"
$options = @('-S', $source, '-B', $build, '-G', 'Ninja', '-DCMAKE_BUILD_TYPE=Release', '-DCMAKE_CXX_COMPILER=clang++', '-DCMAKE_C_COMPILER=clang', '-DCMAKE_RC_COMPILER=llvm-windres', '-DCMAKE_CXX_FLAGS=-include stdlib.h', "-DCMAKE_PREFIX_PATH=$toolRoot/deps", "-DZLIB_LIBRARY=$toolRoot/deps/lib/libzs.a", '-DOPTION_USE_ASSERTS=ON')
if ($Dedicated) { $options += '-DOPTION_DEDICATED=ON' }
Run 'cmake' $options
Run 'cmake' @('--build', $build, '--parallel', '8')
if (!$SkipTests) { Run 'ctest' @('--test-dir', $build, '--output-on-failure', '--timeout', '120') }
$runtime = "$artifactRoot/$name-runtime"
New-Item -ItemType Directory -Force $runtime, "$runtime/baseset", "$runtime/newgrf", "$runtime/save", "$runtime/scripts", "$runtime/scenario/heightmap", "$runtime/game/renaissance-coast" | Out-Null
Copy-Item "$build/openttd.exe" $runtime
Copy-Item "$build/lang" $runtime -Recurse -Force
Copy-Item "$build/baseset/*" "$runtime/baseset" -Recurse -Force
Copy-Item "$artifactRoot/content/*.tar" "$runtime/baseset"
Copy-Item "$compiler/x86_64-w64-mingw32/bin/libunwind.dll" $runtime
Copy-Item "$repo/media/renaissance/demo/*.nut" "$runtime/game/renaissance-coast"
Copy-Item "$repo/media/renaissance/demo/renaissance-coast.png" "$runtime/scenario/heightmap"
Copy-Item "$repo/media/renaissance/demo/*.sav" "$runtime/save"
if (!$Baseline) {
    Copy-Item "$repo/media/renaissance/regional/*.sav" "$runtime/save"
    Copy-Item "$repo/media/renaissance/regional/regional-flat.png" "$runtime/scenario/heightmap"
}
$demoConfig = Get-Content "$repo/media/renaissance/demo/openttd.cfg" -Raw
$config = if ($Baseline) { $demoConfig } else { Get-Content "$repo/media/renaissance/openttd.cfg" -Raw }
if (!$Baseline) {
    & "$toolRoot/python/Scripts/python.exe" "$PSScriptRoot/build_assets.py" --output "$artifactRoot/assets" --check
    if ($LASTEXITCODE -ne 0) {
        Run "$toolRoot/python/Scripts/python.exe" @("$PSScriptRoot/build_assets.py", '--output', "$artifactRoot/assets")
    }
    Copy-Item "$artifactRoot/assets/renaissance-meadow.grf" "$runtime/newgrf"
    $config = $config.Replace('refresh_rate = 60', "refresh_rate = 60`nsmooth_water = true")
    $config += "`n[newgrf-static]`nrenaissance-meadow.grf =`n"
    $demoConfig = $demoConfig.Replace('refresh_rate = 60', "refresh_rate = 60`nsmooth_water = true")
    $demoConfig += "`n[newgrf-static]`nrenaissance-meadow.grf =`n"
}
Set-Content -LiteralPath "$runtime/openttd.cfg" -Value $config -Encoding utf8
Set-Content -LiteralPath "$runtime/coastal-demo.cfg" -Value $demoConfig -Encoding utf8
Copy-Item "$repo/tools/renaissance/launch.ps1" "$runtime/Launch-TransportRenaissance.ps1"
Copy-Item "$repo/tools/renaissance/launch.cmd" "$runtime/Launch-TransportRenaissance.cmd"
# Normal games and loaded saves retain their own camera; no demo script runs implicitly.
Set-Content -LiteralPath "$runtime/scripts/game_start.scr" -Value '' -Encoding utf8
Write-Output "Staged $runtime"
