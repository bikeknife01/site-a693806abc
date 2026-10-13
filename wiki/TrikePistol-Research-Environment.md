# TrikePistol Research Environment

This guide keeps the `TrikePistol` throwaway research instance operationally separate
from the protected `Bikeknife` instance. It supplements the mandatory boundaries in
`AGENTS.md`; it does not make the two instances anonymous or unlinkable to a service.

## Observed local state

Read-only discovery on 2026-10-10 found:

- MuMu CLI `6.8.3.0`.
- `Bikeknife` resolved to VM `0` and was running.
- `TrikePistol` resolved to VM `1` and was stopped.
- TrikePistol network bridge mode, root permission, and system-disk writes were disabled.
- The Windows host had one active Wi-Fi adapter and two disconnected physical Ethernet
  adapters. Adapter names, VM indexes, and state can change and must be rediscovered.

Do not record or commit IMEIs, remote UUIDs, account identifiers, or authentication
material when inspecting MuMu settings.

## Repository safeguards

`Game_Details/Resources/_mumu_research_guard.ps1` inventories all MuMu instances and
returns a sanitized target only when exactly one instance is named `TrikePistol`, exactly
one protected instance is named `Bikeknife`, and their VM indexes differ. With
`-RequireRunning`, it also requires a unique live ADB endpoint. It never launches a VM.

Prepare a new ignored evidence directory without overwriting an existing date:

```powershell
& 'Game_Details\Resources\prepare_trikepistol_snapshot.ps1' `
    -Investigation 'short-investigation-name'
```

`capture_game_network.ps1` now uses the same guard and cannot target Bikeknife by index.
Because its packet monitor operates at the Windows NIC layer, it also refuses to begin
while Bikeknife is running; shared server addresses could otherwise contaminate a capture.

## Recommended network topology

The preferred topology gives TrikePistol its own router-visible client and network while
Bikeknife continues using MuMu's default host NAT:

```text
Internet
  |
UniFi gateway
  |-- trusted network ---------------- Windows normal Wi-Fi -- Bikeknife via host NAT
  |
  `-- isolated research VLAN/SSID ----- dedicated host NIC ---- TrikePistol bridge
```

MuMu exposes per-instance bridge settings (`net_bridge_*`). Its own support guidance
recommends bridging to a non-virtual adapter. A dedicated physical Ethernet adapter is
the clearest local option; a separate USB Wi-Fi adapter associated with a research SSID
is the wireless alternative. Do not try to make one Windows Wi-Fi association belong to
two different VLANs simultaneously.

## UniFi setup

Current UniFi interfaces vary by Network application version, but the intended result is:

1. In **Settings > Networks**, create a virtual network such as `Dragonfire Research`
   with its own VLAN ID, subnet, and DHCP service.
2. Enable **Network Isolation** so that the research VLAN cannot initiate traffic to the
   trusted VLAN. Retain ordinary internet access and required DHCP/DNS access.
3. For wired separation, assign one UniFi switch port's native network to
   `Dragonfire Research`, allow no unnecessary tagged networks on that port, and connect
   one of the host's otherwise unused physical Ethernet adapters.
4. For wireless separation, create a dedicated SSID in **Settings > WiFi**, assign it to
   `Dragonfire Research`, and connect a dedicated USB Wi-Fi adapter to that SSID.
5. If the research VLAN contains other clients, optionally enable client/device
   isolation. This is supplementary to inter-VLAN Network Isolation.

Relevant official references:

- [Creating Virtual Networks (VLANs)](https://help.ui.com/hc/en-us/articles/9761080275607-Creating-Virtual-Networks-VLANs)
- [Implementing Network and Client Isolation](https://help.ui.com/hc/en-us/articles/18965560820247-Implementing-Network-and-Client-Isolation-in-UniFi)
- [Creating UniFi WiFi SSIDs](https://help.ui.com/hc/en-us/articles/26136823938583-Creating-UniFi-WiFi-SSIDs)
- [MuMu network bridge troubleshooting](https://www.mumuplayer.com/help/win/fix-network-error.html)

## MuMu bridge rollout

Do not change bridge settings until the dedicated adapter is connected to the isolated
network and has been identified unambiguously.

1. Leave TrikePistol stopped and export or record its current `net_bridge_*` settings.
2. In TrikePistol's per-instance network settings, enable Network Bridge, select only the
   dedicated non-virtual adapter, and use DHCP initially.
3. Re-query `mumu-cli.exe info --vmindex all` and confirm the display-name mapping before
   launching only TrikePistol.
4. After launch, verify its Android address, default route, and DNS configuration. Confirm
   in UniFi that it appears on `Dragonfire Research`, not the trusted network.
5. Test that TrikePistol has internet access but cannot initiate connections to trusted
   LAN addresses. Confirm Bikeknife remains on its original path and unchanged.
6. Record the adapter name, VLAN, subnet, UniFi isolation mode, MuMu bridge settings, and
   validation results in the local snapshot manifest. Do not record Wi-Fi passwords or
   other network secrets.

If MuMu cannot bridge reliably through the chosen adapter, revert TrikePistol to its
recorded network settings. Do not weaken trusted-network firewall rules as a workaround.
