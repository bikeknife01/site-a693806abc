[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidatePattern('^[a-z0-9][a-z0-9-]{0,63}$')]
    [string]$Investigation,
    [string]$OutputRoot
)

$ErrorActionPreference = 'Stop'
$mumu = 'C:\Program Files\Netease\MuMuPlayer\nx_main\mumu-cli.exe'
$guardPath = Join-Path $PSScriptRoot '_mumu_research_guard.ps1'
. $guardPath

$target = Get-MuMuResearchTarget -MuMuPath $mumu
$mumuVersion = (& $mumu version | Out-String).Trim() | ConvertFrom-Json

if (-not $OutputRoot) {
    $OutputRoot = Join-Path $PSScriptRoot '_snapshots'
}
$OutputRoot = [System.IO.Path]::GetFullPath($OutputRoot)
$date = Get-Date -Format 'yyyy-MM-dd'
$snapshotPath = Join-Path $OutputRoot "$date-trikepistol"
if (Test-Path -LiteralPath $snapshotPath) {
    throw "Snapshot already exists; refusing to overwrite it: $snapshotPath"
}

$directories = @(
    $snapshotPath,
    (Join-Path $snapshotPath 'apks'),
    (Join-Path $snapshotPath 'android_data\com.wb.goog.hotd.socialstrategy\files'),
    (Join-Path $snapshotPath 'private_data'),
    (Join-Path $snapshotPath 'analysis'),
    (Join-Path $snapshotPath 'decoded\old'),
    (Join-Path $snapshotPath 'decoded\new')
)
foreach ($directory in $directories) {
    [System.IO.Directory]::CreateDirectory($directory) | Out-Null
}

$manifest = [ordered]@{
    schema_version = '1.0.0'
    created_local = (Get-Date).ToString('o')
    investigation = $Investigation
    instance = $target
    mumu_cli_version = [string]$mumuVersion.version
    package = 'com.wb.goog.hotd.socialstrategy'
    capture_scope = @()
    modifications = @()
    source_hashes = [ordered]@{}
    sanitization_status = 'unreviewed-local-only'
    prohibited_contents = @(
        'account credentials',
        'reusable authentication tokens',
        'payment data',
        'private state copied from Bikeknife',
        'unrelated application or account data'
    )
}
$manifestPath = Join-Path $snapshotPath 'capture_manifest.json'
$manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $manifestPath -Encoding utf8

[pscustomobject]@{
    snapshot_path = $snapshotPath
    manifest_path = $manifestPath
    instance_name = $target.name
    vm_index = $target.vm_index
    instance_running = $target.is_running
}
