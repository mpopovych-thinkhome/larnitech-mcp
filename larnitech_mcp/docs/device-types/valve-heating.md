Digest of this file lives in [device_types.md](_device_types.md#valve-heating) — keep both in sync.

## XML attributes

Source: https://wiki.larnitech.com/Valve-heating

| Attribute | Type | Description | Default | Values |
|---|---|---|---|---|
| `type` | — | fixed | — | `"valve-heating"` |
| `addr` | string | device address | — | e.g. `"100:48"` |
| `name` | string | device identifier | — | any |
| `sub-type` | enum | variant | — | `"warm-floor"` (no documented behavior difference — see Notes) |
| `temperature-sensors` | list | valve automation sensors | — | e.g. `"119:10;119:11"` |
| `automation` | string | active automation mode | — | user-defined preset name |
| `undefined-behavior` | enum | failsafe valve position | `"last"` | `on`, `off`, `last` |
| `sensor-cr` | list | critical-temperature sensor(s) | — | sensor addresses |
| `sensor-cr-hi` | number | upper temperature threshold | — | e.g. 30°C |
| `sensor-cr-lo` | number | lower temperature threshold | — | e.g. 10°C |
| `temperature-lag` | number | hysteresis margin | 0.5 | decimal |
| `t-min` | number | minimum settable temperature | 0 | numeric |
| `t-max` | number | maximum settable temperature | 32 | numeric |

`<automation>` child elements (presets): `name` (identifier),
`temperature-level` (required setpoint), optional `time-interval` with
`temperature-level`/`start-time`/`end-time`/`week-days` for scheduling.

## API

`status.automation` always has (at least) two reserved states on top of any
named presets:

- **absent** — "manual" mode: device behaves as plain on/off, no
  setpoint/preset involved (example: `1:7` "Radiator", no `<automation>` in
  XML at all — status is always `{"state":"off"}`, no `target`)
- **`"<Name>"`** (`"Comfort"`, `"Eco"`, ...) — an active named preset from
  the XML `automations` list; status carries `target` (setpoint) and
  `automation`
- **`"always-off"`** — reserved: device is locked off and cannot turn on
  until switched to another mode/preset. **Not** part of the XML
  `automations` list (the list stays e.g. `["Comfort"]` no matter the
  current mode) — only ever seen via `status.automation`, same as named
  presets. This lines up with the vendor page's Script section below,
  which documents a `254 = "always off"` sentinel in the 6-byte status.
- Device-level `automations` (the preset list, separate from `status`)
  **does not change** when switching manual/always-off/preset — the only
  signal for current mode is `status.automation`.
- `sub-type="warm-floor"` behaves identically — no observed differences.

`target` resets to sentinel `-128` if `state`/`mode` are set in a
`status-set` call without `target` in the same call — always include
`target` when setting either.

`valve-heating="ADDR"` / `valve-cooling="ADDR"` attributes on a `fancoil`
widget (which point at this device) are **not visible via API2 in either
direction** — see [fancoil.md](fancoil.md).

## Script

- Event status (1 byte): bit0 on/off, bits4-7 automation mode number
- Status request (6 bytes): status byte, setpoint temperature (2 bytes),
  sensor average temperature (2 bytes), mode indicator (1 byte: `254` =
  always-off, `255` = manual)
- Write command (1 byte): 0 off, 1 on, 0xFF toggle — this direct per-device
  write does **not** cover setting the automation mode/preset

### Setting automation mode by index/name from script

There is no direct per-device `setStatus(ADDR, ...)` form for this. The
language reference documents a separate server pseudo-device, **"Heating
profile operation from script"** (`Larnitech_Scripts-language_2020.md`
around line 2178):

```c
setStatus(1000:100, "Komfort");                 // sub-id 100: broadcast to ALL heating circuits
setStatus(1000:101, "Area1\0Komfort");           // sub-id 101: all circuits in an Area
setStatus(1000:102, "16:1\0Komfort");            // sub-id 102: one circuit by "ID:SUBID" address
setStatus(1000:102, "16:1\0as:2");               // set automation by numeric index (as:N)
setStatus(1000:102, "16:1\0always-off");         // reserved lockout
setStatus(1000:102, "16:1\0ts:25");              // set setpoint temperature
```

Payload is a single string, built with `sprintf`, `\0`-joining an optional
`Area(...)`/`ID:SUBID` target prefix with the command: a literal preset
name, `as:<N>` (numeric automation index), `ts:<N>`/`t:<N>` (temperature),
or the literal `always-off`. Target addr uses plain `"ID:SID"` (decimal,
`:` separator), not the `ID:SUBID` script-address shorthand.

Numeric index `N` in `as:N` is the same value read back from bits4-7 of the
1-byte event status (`[ADDR.0] >> 4`) — confirmed live in a real production
script, `MasterSlaveValveHeating_V2_4.txt` (`scripts/Скрипты сапорта
Larnitech/Разные/Разные/`): it reads a master valve-heating's automation
index with `[MASTER.0]>>4` and re-applies it to slave devices with
`setStatus(1000:102, "ID:SID\0as:<index>")`. Preset-index-to-name mapping
(i.e. whether index 0/1 is the first named `<automation>` XML entry, or a
reserved slot before it) is **not confirmed** — no live test in this KB
maps a specific index number back to a specific preset name.

**Discrepancy, resolved (2026-09-03, live-tested):** the language doc's own
numeric shortcuts say `-1`=always-off, `-2`=previous mode, `-3`=manual — this
is **wrong**. Confirmed live: `setStatus(1000:102, "ID:SID\0as:-4")` switches
the circuit to Manual; `as:-3` does **not**. Use `-4` for manual, not `-3`.

**`ts:<N>` setpoint confirmed (2026-09-03):** live-tested working on
[fancoil](fancoil.md#script) — which shares this exact mechanism — including
with no active named automation (Manual mode). Not separately re-tested on
`valve-heating` itself in this KB, but same pseudo-device/command, so treat
as confirmed here too unless a live test shows otherwise.

## Notes

Always has at least 2 reserved modes (manual, always-off) on top of any
named presets — never assume `status.automation` absent means "no
automation configured at all" without also checking whether XML even
defines an `<automation>` block.

<!-- Add live-tested quirks here as found. -->

- (2026-08-18) **Resetting `automation` to manual and turning the channel off must be TWO separate, spaced-out `status-set` calls, not one combined write.** Confirmed live on `1:5` (had a named preset active, `state: "on"`): `{"automation": "", "state": "off"}` in one call, and two separate calls sent immediately back-to-back, both end with `automation` cleared (confirmed via a fresh `status-get`, not just the write ack) but `state` still `"on"`. The controller appears to re-evaluate the channel's own on/off logic right after an automation is cleared, and that re-evaluation turns it back on — landing *after* an `off` that arrived too soon in the same burst. Working sequence: write `{"automation": ""}` alone, wait **~1s**, then write `{"state": "off"}` alone. Confirmed working with exactly this pacing. Same mechanism reproduced on [fancoil](fancoil.md) and [vent](vent.md).
- (2026-09-03) **Manual mode via script is `as:-4`, not `as:-3`**: `setStatus(1000:102, "ID:SID\0as:-4")` confirmed live to switch a valve-heating circuit to Manual; `as:-3` (the value the language doc's own numeric-shortcut table lists for manual) does **not** work. Same mechanism confirmed identical on fancoil.
- (2026-08-18) Writing `automation: ""` (empty string) to return to manual mode is now **confirmed working** — the key disappears from `status` entirely on the next read, matching the "absent = manual" read-side convention documented above. (`"always-off"` as a write value is still unconfirmed.)

## Known bugs

- Automation-preset switch leaves the previous preset's outputs on — [BUG-010](../bugs.md#bug-010)
