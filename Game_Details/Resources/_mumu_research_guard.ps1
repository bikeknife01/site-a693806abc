Set-StrictMode -Version Latest

function Get-MuMuResearchTarget {
    [CmdletBinding()]
    param(
        [string]$MuMuPath = 'C:\Program Files\Netease\MuMuPlayer\nx_main\mumu-cli.exe',
        [string]$TargetName = 'TrikePistol',
        [string]$ProtectedName = 'Bikeknife',
        [switch]$RequireRunning
    )

    if ($TargetName -cne 'TrikePistol') {
        throw "Research operations are authorized only for the exact MuMu display name 'TrikePistol'."
    }
    if (-not (Test-Path -LiteralPath $MuMuPath)) {
        throw "MuMu CLI not found: $MuMuPath"
    }

    $infoText = (& $MuMuPath info --vmindex all | Out-String).Trim()
    if ($LASTEXITCODE -ne 0 -or -not $infoText) {
        throw 'Could not inventory MuMu instances.'
    }
    $infoDocument = $infoText | ConvertFrom-Json
    $instances = @($infoDocument.PSObject.Properties | ForEach-Object { $_.Value })
    $targets = @($instances | Where-Object { [string]$_.name -ceq $TargetName })
    $protected = @($instances | Where-Object { [string]$_.name -ceq $ProtectedName })

    if ($targets.Count -ne 1) {
        throw "Expected exactly one MuMu instance named '$TargetName'; found $($targets.Count)."
    }
    if ($protected.Count -ne 1) {
        throw "Expected exactly one protected MuMu instance named '$ProtectedName'; found $($protected.Count)."
    }

    $target = $targets[0]
    $protectedInstance = $protected[0]
    if ([string]$target.index -eq [string]$protectedInstance.index) {
        throw 'Research and protected display names resolve to the same VM index.'
    }

    $targetAndroidStarted = $target.PSObject.Properties['is_android_started']
    $targetProcessStarted = $target.PSObject.Properties['is_process_started']
    $isRunning = $null -ne $targetAndroidStarted -and [bool]$targetAndroidStarted.Value -and
        $null -ne $targetProcessStarted -and [bool]$targetProcessStarted.Value
    if ($RequireRunning -and -not $isRunning) {
        throw "MuMu instance '$TargetName' (VM $($target.index)) is not already running. This guard does not launch it."
    }
    if ($isRunning -and (-not $target.adb_host_ip -or -not $target.adb_port)) {
        throw "Running MuMu instance '$TargetName' did not report a complete ADB endpoint."
    }

    $protectedAndroidStarted = $protectedInstance.PSObject.Properties['is_android_started']
    $protectedProcessStarted = $protectedInstance.PSObject.Properties['is_process_started']
    $protectedIsRunning = $null -ne $protectedAndroidStarted -and [bool]$protectedAndroidStarted.Value -and
        $null -ne $protectedProcessStarted -and [bool]$protectedProcessStarted.Value
    if ($isRunning -and $protectedIsRunning -and
        $target.adb_host_ip -eq $protectedInstance.adb_host_ip -and
        [string]$target.adb_port -eq [string]$protectedInstance.adb_port) {
        throw 'Research and protected instances report the same ADB endpoint.'
    }

    [pscustomobject]@{
        name = [string]$target.name
        vm_index = [int]$target.index
        android_version = [string]$target.android_version
        is_running = $isRunning
        adb_host_ip = if ($isRunning) { [string]$target.adb_host_ip } else { $null }
        adb_port = if ($isRunning) { [int]$target.adb_port } else { $null }
        protected_name = [string]$protectedInstance.name
        protected_vm_index = [int]$protectedInstance.index
        protected_is_running = $protectedIsRunning
    }
}
