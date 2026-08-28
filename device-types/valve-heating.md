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
- Write command (1 byte): 0 off, 1 on, 0xFF toggle

## Notes

Always has at least 2 reserved modes (manual, always-off) on top of any
named presets — never assume `status.automation` absent means "no
automation configured at all" without also checking whether XML even
defines an `<automation>` block.

<!-- Add live-tested quirks here as found. -->

- (2026-08-18) **Resetting `automation` to manual and turning the channel off must be TWO separate, spaced-out `status-set` calls, not one combined write.** Confirmed live on `1:5` (had a named preset active, `state: "on"`): `{"automation": "", "state": "off"}` in one call, and two separate calls sent immediately back-to-back, both end with `automation` cleared (confirmed via a fresh `status-get`, not just the write ack) but `state` still `"on"`. The controller appears to re-evaluate the channel's own on/off logic right after an automation is cleared, and that re-evaluation turns it back on — landing *after* an `off` that arrived too soon in the same burst. Working sequence: write `{"automation": ""}` alone, wait **~1s**, then write `{"state": "off"}` alone. Confirmed working with exactly this pacing. Same mechanism reproduced on [fancoil](fancoil.md) and [vent](vent.md).
- (2026-08-18) Writing `automation: ""` (empty string) to return to manual mode is now **confirmed working** — the key disappears from `status` entirely on the next read, matching the "absent = manual" read-side convention documented above. (`"always-off"` as a write value is still unconfirmed.)

## Known bugs

None recorded yet.
