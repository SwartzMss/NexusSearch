[CmdletBinding()]
param(
    [string]$PortableDirectory = (Join-Path $env:RUNNER_TEMP "NexusSearch"),
    [string]$ArchivePath = (Join-Path $env:RUNNER_TEMP "NexusSearch-Windows-x64.zip")
)

$ErrorActionPreference = "Stop"
$dist = [IO.Path]::GetFullPath((Join-Path (Get-Location) "dist/nexussearch"))
$portable = [IO.Path]::GetFullPath($PortableDirectory)
$archive = [IO.Path]::GetFullPath($ArchivePath)

if (Test-Path $portable) { Remove-Item -Recurse -Force $portable }
if (Test-Path $archive) { Remove-Item -Force $archive }
Copy-Item -Recurse -Force $dist $portable
python packaging/prepare_portable.py $portable

foreach ($required_path in @(
    (Join-Path $portable "_internal/searx/engines/google.py"),
    (Join-Path $portable "_internal/searx/answerers/random.py"),
    (Join-Path $portable "_internal/searx/answerers/statistics.py"),
    (Join-Path $portable "settings.yml"),
    (Join-Path $portable "LICENSE"),
    (Join-Path $portable "AUTHORS.rst")
)) {
    if (-not (Test-Path $required_path)) { throw "required portable file missing: $required_path" }
}

$executable = Join-Path $portable "nexussearch.exe"
Remove-Item Env:SEARXNG_SETTINGS_PATH -ErrorAction SilentlyContinue
python packaging/smoke_test.py $executable --health-only
if ($LASTEXITCODE -ne 0) { throw "release settings health smoke failed: $LASTEXITCODE" }

$search_smoke_exit_code = 0
try {
    $env:SEARXNG_SETTINGS_PATH = Join-Path $portable "_internal/settings-smoke.yml"
    python packaging/smoke_test.py $executable
    $search_smoke_exit_code = $LASTEXITCODE
} finally {
    Remove-Item Env:SEARXNG_SETTINGS_PATH -ErrorAction SilentlyContinue
}
if ($search_smoke_exit_code -ne 0) { throw "deterministic search smoke failed: $search_smoke_exit_code" }

Compress-Archive -Path (Join-Path $portable "*") -DestinationPath $archive
Write-Host "Created $archive"
