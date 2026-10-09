[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$VideoPath
)

$ErrorActionPreference = 'Stop'
$repoRoot = $PSScriptRoot
$venvPython = Join-Path $repoRoot '.venv\Scripts\python.exe'
$ingestScript = Join-Path $repoRoot 'projects\combat-report-extractor\ingest_combat_report.py'

if (Test-Path -LiteralPath $venvPython -PathType Leaf) {
    $python = $venvPython
} else {
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($null -eq $pythonCommand) {
        throw 'Python was not found. Follow the Combat Report Extractor install steps first.'
    }
    $python = $pythonCommand.Source
}

& $python $ingestScript $VideoPath
exit $LASTEXITCODE
