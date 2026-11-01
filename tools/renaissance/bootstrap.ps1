# Workspace-local native Windows toolchain. No system installation. GPL-2.0-only.
[CmdletBinding()]
param([string]$Workspace = (Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent))
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$Workspace = [IO.Path]::GetFullPath($Workspace)
$toolRoot = Join-Path $Workspace 'tools'
$artifactRoot = Join-Path $Workspace 'artifacts'
$lock = Get-Content (Join-Path $PSScriptRoot 'dependencies.json') -Raw | ConvertFrom-Json
New-Item -ItemType Directory -Force $toolRoot, "$toolRoot/sources", "$artifactRoot/downloads", "$artifactRoot/content", "$artifactRoot/source-archives" | Out-Null
function Run([string]$Executable, [string[]]$Arguments) {
    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) { throw "$Executable failed with exit code $LASTEXITCODE" }
}
function Download([string]$Url, [string]$Path, [string]$Hash) {
    if (!(Test-Path -LiteralPath $Path)) { Invoke-WebRequest -Uri $Url -OutFile $Path }
    if ((Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash -ne $Hash) { throw "Checksum mismatch: $Path" }
}
$compiler = Join-Path $toolRoot $lock.compiler.name
Download $lock.compiler.url "$toolRoot/llvm-mingw.zip" $lock.compiler.sha256
if (!(Test-Path -LiteralPath "$compiler/bin/clang++.exe")) {
    Expand-Archive -LiteralPath "$toolRoot/llvm-mingw.zip" -DestinationPath $toolRoot
}
if (!(Test-Path -LiteralPath "$toolRoot/python/Scripts/python.exe")) { Run 'python' @('-m', 'venv', "$toolRoot/python") }
Run "$toolRoot/python/Scripts/python.exe" @('-m', 'pip', 'install', '-r', "$PSScriptRoot/requirements.txt")
$env:PATH = "$compiler/bin;$toolRoot/python/Scripts;$env:PATH"
foreach ($library in $lock.libraries) {
    $path = Join-Path "$toolRoot/sources" $library.name
    if (!(Test-Path -LiteralPath $path)) { Run 'git' @('clone', '--depth', '1', '--branch', $library.tag, $library.url, $path) }
    $actual = & git -C $path rev-parse HEAD
    if ($LASTEXITCODE -ne 0 -or $actual -ne $library.commit) { throw "Unexpected source revision in $path" }
    if ($library.source_only) { continue }
    $build = Join-Path "$artifactRoot/deps-build" $library.name
    $options = @('-S', $path, '-B', $build, '-G', 'Ninja', '-DCMAKE_BUILD_TYPE=Release', '-DCMAKE_C_COMPILER=clang', "-DCMAKE_INSTALL_PREFIX=$toolRoot/deps", "-DCMAKE_PREFIX_PATH=$toolRoot/deps")
    switch ($library.name) {
        'zlib' { $options += @('-DZLIB_BUILD_SHARED=OFF', '-DZLIB_BUILD_TESTING=OFF') }
        'xz' { $options += @('-DBUILD_SHARED_LIBS=OFF', '-DBUILD_TESTING=OFF', '-DXZ_NLS=OFF', '-DXZ_TOOL_XZ=OFF', '-DXZ_TOOL_XZDEC=OFF', '-DXZ_TOOL_LZMADEC=OFF', '-DXZ_TOOL_LZMAINFO=OFF') }
        'libpng' { $options += @("-DZLIB_LIBRARY=$toolRoot/deps/lib/libzs.a", '-DPNG_SHARED=OFF', '-DPNG_TESTS=OFF', '-DPNG_TOOLS=OFF') }
    }
    Run 'cmake' $options
    Run 'cmake' @('--build', $build, '--parallel', '8')
    Run 'cmake' @('--install', $build)
}
foreach ($content in $lock.content) {
    $name = $content.name; $version = $content.version
    $zip = "$artifactRoot/downloads/$name-$version-all.zip"
    Download "https://cdn.openttd.org/$name-releases/$version/$name-$version-all.zip" $zip $content.sha256
    Expand-Archive -LiteralPath $zip -DestinationPath "$artifactRoot/content" -Force
    if ($content.source_url) {
        $sourceName = $content.source_url.Split('/')[-1]
        Download $content.source_url "$artifactRoot/source-archives/$sourceName" $content.source_sha256
    }
}
Write-Output "Toolchain ready in $toolRoot. Run build.ps1 next."
