# 02 — Environment and compatibility

## Evidence captured 2026-10-16

| Item | Observation | Status |
|---|---|---|
| MuMu CLI | `C:\Program Files\Netease\MuMuPlayer\nx_main\mumu-cli.exe version` → `6.8.5.0` | Observed locally |
| Instances | `info --vmindex all`: `Bikeknife` index 0 stopped; `TrikePistol` index 1 running, ADB `127.0.0.1:16416`, PID 31272 | Transient; rediscover each run |
| Guest | Android 15; ABI list `x86_64,arm64-v8a,x86`; Hyper-V enabled per MuMu CLI | Observed; backend implementation still unknown |
| Host association | PID 31272 is `MuMuNxDevice.exe`, parent `MuMuNxMain.exe`; command line names `MuMuPlayerGlobal-15.0-1`. `MuMuNxSVC.exe` was also running. | Strong instance→device-process clue, **not** proof that its address space holds readable guest RAM |
| Game | Package `com.wb.goog.hotd.socialstrategy`; arm64-v8a primary ABI; version `26.10.57632` (code 337); guest PID 6238 while running | Observed via read-only ADB; PID transient |
| Memory access | No process handle or guest memory read attempted | Unverified |

The [official MuMu multi-instance guide](https://www.mumuplayer.com/help/win/multi-instance-guide.html) confirms multiple instance management. On this installation, `mumu-cli.exe` itself documents `version`, `info`, `control`, and `adb` subcommands; its live JSON is the authoritative local inventory. `MuMuManager.exe` is installed, but no equivalent CLI contract was validated. Prefer `mumu-cli.exe` for this version. The process relationship must be rechecked after every restart; host PID and VM index are not durable identifiers.

## Bounded validation procedure

1. **Identity gate:** run `mumu-cli.exe info --vmindex all`; resolve `TrikePistol` to exactly one index; stop on missing/duplicate/renamed identity or if the selected instance reports `Bikeknife`. Save time, MuMu version, instance name/index, endpoint, host PID, process creation time, executable path and command line. Read-only ADB confirms package, guest PID, ABI and version. Do not launch or stop an instance unless that action is part of a documented experiment.
2. **Host attach:** build the hardened read-only fork. Open the exact CLI-reported PID with `PROCESS_QUERY_INFORMATION | PROCESS_VM_READ` only; first try without debug privilege. Verify image path/creation time before and after opening; verify the handle's target PID. If access requires elevation, record it, use only the least privilege needed, and do not silently enable `SeDebugPrivilege`. Windows documents [required access rights](https://learn.microsoft.com/en-us/windows/win32/procthread/process-security-and-access-rights) and [VirtualQueryEx query rights](https://learn.microsoft.com/en-us/windows/win32/api/memoryapi/nf-memoryapi-virtualqueryex).
3. **Guest discovery:** perform one capped discovery with cancellation and progress logs. Require a unique page-table root whose module list and address-space features are consistent with the game. Cross-check with guest PID/package from ADB. If library cannot establish a unique binding, result is ambiguous and no memory samples are accepted.
4. **Small known read:** select a non-sensitive, immutable, mapped module header or other known test bytes. Read at most one page initially. Repeat, compare with a second independent read and known on-disk/module evidence where valid. Record exact access mask, bytes requested/read, latency, mapping generation, and failure codes. No broad dump, string search, or credential-bearing ranges in M1.
5. **Lifecycle:** close/reopen game on `TrikePistol` only as a controlled test, then reboot only that instance if necessary. A stale address/root must fail. Reacquire identity and root; compare per-version results. Test invalid VA, unmapped page, split-page read, cancellation and loss of VMM. Multi-instance mapping is a separate M6 gate; do not involve `Bikeknife` in research.

Example discovery commands (read-only, substitute *fresh* name-derived index and endpoint; do not copy today's index):

```powershell
$mumu = 'C:\Program Files\Netease\MuMuPlayer\nx_main\mumu-cli.exe'
$adb = 'C:\Program Files\Netease\MuMuPlayer\nx_main\adb.exe'
& $mumu version
& $mumu info --vmindex all
# Resolve TrikePistol uniquely from that JSON before the next commands.
& $adb connect '<reported-host>:<reported-port>'
& $adb -s '<reported-host>:<reported-port>' shell pidof com.wb.goog.hotd.socialstrategy
& $adb -s '<reported-host>:<reported-port>' shell getprop ro.product.cpu.abilist
& $adb disconnect '<reported-host>:<reported-port>'
```

## Gate

**Current verdict: CONDITIONAL GO to M1.** Upgrade to GO for M2 only after unique instance/process binding and repeated read-only known-byte reads survive process restart with stale addresses rejected. Mark NO GO for this backend on failed least-privilege attach, inconsistent translation, ambiguous identity, protection requiring evasion, or unacceptable frame-time impact. A compatible attachment alone does not establish useful combat telemetry.
