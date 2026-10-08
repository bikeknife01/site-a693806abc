[CmdletBinding()]
param(
    [int]$VmIndex = 0,
    [int]$DurationSeconds = 0,
    [string]$OutputDirectory,
    [switch]$SkipLogcat,
    [switch]$NonInteractive
)

$ErrorActionPreference = 'Stop'

$mumu = 'C:\Program Files\Netease\MuMuPlayer\nx_main\mumu-cli.exe'
$adb = 'C:\Program Files\Netease\MuMuPlayer\nx_main\adb.exe'
$pktmon = 'C:\Windows\System32\PktMon.exe'
$package = 'com.wb.goog.hotd.socialstrategy'

foreach ($requiredTool in @($mumu, $adb, $pktmon)) {
    if (-not (Test-Path -LiteralPath $requiredTool)) {
        throw "Required tool not found: $requiredTool"
    }
}

$infoText = (& $mumu info --vmindex $VmIndex | Out-String).Trim()
if ($LASTEXITCODE -ne 0) {
    throw "MuMu info failed for VM $VmIndex."
}
$infoDocument = $infoText | ConvertFrom-Json
$vmProperty = $infoDocument.PSObject.Properties["$VmIndex"]
if ($vmProperty) {
    $vm = $vmProperty.Value
}
elseif ([string]$infoDocument.index -eq [string]$VmIndex) {
    $vm = $infoDocument
}
else {
    $vm = $null
}
if (-not $vm -or -not $vm.is_android_started -or -not $vm.is_process_started) {
    throw "MuMu VM $VmIndex is not already running. This script intentionally does not start it."
}

$device = '{0}:{1}' -f $vm.adb_host_ip, $vm.adb_port
$connectText = (& $adb connect $device | Out-String).Trim()
if ($LASTEXITCODE -ne 0) {
    throw "ADB could not connect to $device`: $connectText"
}

$packagePaths = (& $adb -s $device shell pm path $package | Out-String).Trim()
if ($LASTEXITCODE -ne 0 -or -not $packagePaths) {
    throw "Package $package was not found on $device."
}
$packageDetails = (& $adb -s $device shell dumpsys package $package |
    Select-String -Pattern 'versionName=|versionCode=|dataDir=|codePath=|appId=' |
    ForEach-Object { $_.Line.Trim() }) -join "`n"
$uidMatch = [regex]::Match($packageDetails, '(?m)^appId=(\d+)$')
$packageUid = if ($uidMatch.Success) { $uidMatch.Groups[1].Value } else { $null }
if (-not $packageUid) {
    throw "Could not determine the Android UID for $package."
}

function Convert-ProcNetAddress {
    param(
        [Parameter(Mandatory)][string]$HexAddress,
        [Parameter(Mandatory)][ValidateSet(4, 6)][int]$Family
    )
    if ($Family -eq 4 -or $HexAddress.StartsWith('0000000000000000FFFF0000')) {
        $ipv4Hex = $HexAddress.Substring($HexAddress.Length - 8)
        $value = [Convert]::ToUInt32($ipv4Hex, 16)
        return [System.Net.IPAddress]::new([BitConverter]::GetBytes($value)).ToString()
    }
    $bytes = [System.Collections.Generic.List[byte]]::new()
    for ($offset = 0; $offset -lt 32; $offset += 8) {
        $word = [Convert]::ToUInt32($HexAddress.Substring($offset, 8), 16)
        $bytes.AddRange([BitConverter]::GetBytes($word))
    }
    return [System.Net.IPAddress]::new($bytes.ToArray()).ToString()
}

function Get-PackageConnections {
    param(
        [Parameter(Mandatory)][string]$AndroidUid,
        [Parameter(Mandatory)][string]$AdbDevice
    )
    $results = [System.Collections.Generic.List[object]]::new()
    foreach ($table in @(
        @{ Path = '/proc/net/tcp'; Protocol = 'TCP'; Family = 4 },
        @{ Path = '/proc/net/tcp6'; Protocol = 'TCP'; Family = 6 },
        @{ Path = '/proc/net/udp'; Protocol = 'UDP'; Family = 4 },
        @{ Path = '/proc/net/udp6'; Protocol = 'UDP'; Family = 6 }
    )) {
        $lines = & $adb -s $AdbDevice shell "cat $($table.Path)" 2>$null
        foreach ($line in $lines | Select-Object -Skip 1) {
            $fields = $line.Trim() -split '\s+'
            if ($fields.Count -lt 8 -or $fields[7] -ne $AndroidUid) {
                continue
            }
            $remoteParts = $fields[2] -split ':'
            $remoteAddress = Convert-ProcNetAddress -HexAddress $remoteParts[0] -Family $table.Family
            $remotePort = [Convert]::ToInt32($remoteParts[1], 16)
            if ($remoteAddress -in @('0.0.0.0', '::') -or $remotePort -eq 0) {
                continue
            }
            $results.Add([pscustomobject]@{
                protocol = $table.Protocol
                remote_address = $remoteAddress
                remote_port = $remotePort
                state_hex = $fields[3]
            })
        }
    }
    return @($results | Sort-Object protocol, remote_address, remote_port -Unique)
}

$packageConnections = Get-PackageConnections -AndroidUid $packageUid -AdbDevice $device
$remoteAddresses = @($packageConnections.remote_address | Sort-Object -Unique)
if ($remoteAddresses.Count -eq 0) {
    throw 'Dragonfire has no current remote sockets. Open the game to its main screen before starting the capture.'
}

if (-not $OutputDirectory) {
    $repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
    $date = Get-Date -Format 'yyyy-MM-dd'
    $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
    $OutputDirectory = Join-Path $repositoryRoot "Game_Details\Resources\_snapshots\$date\analysis\network-capture-$stamp"
}
$OutputDirectory = [System.IO.Path]::GetFullPath($OutputDirectory)
[System.IO.Directory]::CreateDirectory($OutputDirectory) | Out-Null

$etlPath = Join-Path $OutputDirectory 'host-network.etl'
$pcapPath = Join-Path $OutputDirectory 'host-network.pcapng'
$pktmonTextPath = Join-Path $OutputDirectory 'pktmon.txt'
$logcatPath = Join-Path $OutputDirectory 'logcat.txt'
$logcatErrorPath = Join-Path $OutputDirectory 'logcat.stderr.txt'
$eventsPath = Join-Path $OutputDirectory 'events.tsv'
$metadataPath = Join-Path $OutputDirectory 'metadata.json'
$connectionsPath = Join-Path $OutputDirectory 'connections_at_start.json'

$statusText = (& $pktmon status 2>&1 | Out-String).Trim()
if ($LASTEXITCODE -ne 0) {
    throw "PktMon requires an elevated PowerShell session. Status response: $statusText"
}
if ($statusText -notmatch '(?i)not running|stopped') {
    throw "PktMon may already be active; refusing to stop or replace another capture. Status: $statusText"
}
$filterText = (& $pktmon filter list 2>&1 | Out-String).Trim()
if ($LASTEXITCODE -ne 0) {
    throw "Could not inspect existing PktMon filters: $filterText"
}
if ($filterText -and $filterText -notmatch '(?i)no filters|packet filters:\s*none') {
    throw "PktMon already has filters configured; refusing to modify them. Filters: $filterText"
}

$captureStart = Get-Date
$metadata = [ordered]@{
    capture_started_local = $captureStart.ToString('o')
    capture_started_utc = $captureStart.ToUniversalTime().ToString('o')
    capture_scope = 'Windows host NICs via PktMon; full packets; system-wide; TLS payload expected encrypted'
    package = $package
    package_uid = $packageUid
    package_paths = $packagePaths -split "`r?`n"
    package_details = $packageDetails -split "`n"
    mumu_vm_index = $VmIndex
    mumu_info = $vm
    adb_device = $device
    emulator_was_already_running = $true
    pktmon_filters_at_start = $filterText -split "`r?`n"
    filtered_remote_addresses = $remoteAddresses
}
$metadata | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $metadataPath -Encoding utf8
$packageConnections | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $connectionsPath -Encoding utf8
"elapsed_seconds`tlocal_time`tevent" | Set-Content -LiteralPath $eventsPath -Encoding utf8

function Add-EventMarker {
    param([Parameter(Mandatory)][string]$Label)
    $now = Get-Date
    $elapsed = ($now - $captureStart).TotalSeconds
    ("{0:F3}`t{1}`t{2}" -f $elapsed, $now.ToString('o'), ($Label -replace "[\r\n\t]", ' ')) |
        Add-Content -LiteralPath $eventsPath -Encoding utf8
}

$pktmonStarted = $false
$logcatProcess = $null
$addedFilters = [System.Collections.Generic.List[string]]::new()
try {
    for ($index = 0; $index -lt $remoteAddresses.Count; $index++) {
        $filterName = 'Dragonfire{0:D2}' -f ($index + 1)
        $filterResult = (& $pktmon filter add $filterName -i $remoteAddresses[$index] 2>&1 | Out-String).Trim()
        if ($LASTEXITCODE -ne 0) {
            throw "Could not add PktMon filter $filterName for $($remoteAddresses[$index]): $filterResult"
        }
        $addedFilters.Add($filterName)
    }
    $startText = (& $pktmon start --capture --comp nics --pkt-size 0 --file-name $etlPath --file-size 256 --log-mode circular 2>&1 | Out-String).Trim()
    if ($LASTEXITCODE -ne 0) {
        throw "PktMon capture failed to start: $startText"
    }
    $pktmonStarted = $true

    if (-not $SkipLogcat -and $packageUid) {
        $logcatArguments = @('-s', $device, 'logcat', '-T', '1', "--uid=$packageUid", '-v', 'threadtime')
        $logcatProcess = Start-Process -FilePath $adb -ArgumentList $logcatArguments `
            -RedirectStandardOutput $logcatPath -RedirectStandardError $logcatErrorPath `
            -NoNewWindow -PassThru
    }

    Add-EventMarker 'capture_started'
    Write-Host "Capturing Windows NIC traffic to: $OutputDirectory"
    Write-Host "Dragonfire Android UID: $packageUid"

    if ($NonInteractive) {
        if ($DurationSeconds -le 0) {
            throw '-NonInteractive requires -DurationSeconds greater than zero.'
        }
        Start-Sleep -Seconds $DurationSeconds
    }
    else {
        Write-Host 'Type a short event label and press Enter whenever useful.'
        Write-Host 'Suggested labels: baseline_end, main_screen, screen_opened, battle_started, ability_used, battle_ended, report_opened'
        Write-Host 'Submit a blank label to stop the capture.'
        while ($true) {
            $label = Read-Host 'Event label'
            if ([string]::IsNullOrWhiteSpace($label)) {
                break
            }
            Add-EventMarker $label
            if ($DurationSeconds -gt 0 -and ((Get-Date) - $captureStart).TotalSeconds -ge $DurationSeconds) {
                break
            }
        }
    }
}
finally {
    Add-EventMarker 'capture_stopping'
    if ($logcatProcess -and -not $logcatProcess.HasExited) {
        $logcatProcess.Kill()
        $logcatProcess.WaitForExit(2000) | Out-Null
    }
    if ($pktmonStarted) {
        & $pktmon stop | Out-Null
    }
    if ($addedFilters.Count -gt 0) {
        & $pktmon filter remove | Out-Null
    }
}

& $pktmon etl2pcap $etlPath --out $pcapPath | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw "PktMon could not convert $etlPath to PCAPNG."
}
& $pktmon etl2txt $etlPath --out $pktmonTextPath --brief --timestamp | Out-Null

$pcap = Get-Item -LiteralPath $pcapPath
$stream = [System.IO.File]::OpenRead($pcapPath)
try {
    $header = [byte[]]::new(4)
    $bytesRead = $stream.Read($header, 0, $header.Length)
}
finally {
    $stream.Dispose()
}
if ($bytesRead -ne 4) {
    throw 'Capture is too short to contain a PCAPNG header.'
}
$magic = ($header | ForEach-Object { $_.ToString('x2') }) -join ''
$validMagic = $magic -eq '0a0d0d0a'

$completion = [ordered]@{
    capture_stopped_local = (Get-Date).ToString('o')
    etl_bytes = (Get-Item -LiteralPath $etlPath).Length
    pcapng_bytes = $pcap.Length
    capture_magic = $magic
    capture_header_valid = $validMagic
}
$completion | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $OutputDirectory 'completion.json') -Encoding utf8

if (-not $validMagic) {
    throw "Capture does not have a recognized PCAPNG header (found $magic)."
}

Write-Host "Capture complete: $($pcap.Length) PCAPNG bytes"
Write-Host "Events: $eventsPath"
Write-Host "Logcat: $logcatPath"
