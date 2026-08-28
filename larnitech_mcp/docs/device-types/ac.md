Digest of this file lives in [device_types.md](_device_types.md#ac) — keep both in sync.

## XML attributes

Source: https://wiki.larnitech.com/AC

| Attribute | Type | Description | Default | Values |
|---|---|---|---|---|
| `type` | — | fixed | — | `"AC"` |
| `name` | string | device identifier | — | any |
| `addr` | string | device address | — | `"123:4"` format |
| `path` | string | path to script | — | — |
| `script-id` | string | script identifier from interface | — | — |
| `modes` | bitmask, 5 bits | operation modes | `0x1F` | bit0 fan, bit1 cool, bit2 dry, bit3 heat, bit4 auto |
| `fans` | bitmask, 5 bits | airflow settings | `0x1F` | auto, speed 1-5, silent |
| `vane-ver` | bitmask, 7 bits | vertical fins | `0x7E` | auto, top, top-center, center, center-bottom, bottom, swing |
| `vane-hor` | bitmask, 8 bits | horizontal fins | `0x00` | left, left-center, center, center-right, right, sides-low, sides-high, sides-to-center |
| `t-min` | number | min temperature threshold | 16 | integer |
| `t-delta` | number | temperature range (max = t-min + t-delta) | 16 | integer |
| `t-step` | number | temperature increment | 1 | integer |
| `temperature-sensors` | list | valve temperature sensor references | — | — |
| `t-outside` | address | external temperature sensor | — | `MODULE:ADDR` |
| `t-outside-treshold` | value | critical low temperature limit | — | — |
| `t-outside-hyst` | value | temperature hysteresis margin | — | — |

## API

Read/write via `status-get`/`status-set` (API2), `status:"detailed"` required for decoded values.

- `fan`: string enum — write-reliable set only:
  - `auto`
  - `low`
  - `middle`
  - `high`
  - anything else (`medium`, numbers, `silent`) rejected with
    `{"code":9,"description":"set-status has invalid parameter"}`
  - reading a live speed above `high` returns `null` — [BUG-003](../bugs.md#bug-003)
- `state`: on/off — exact API key not yet confirmed live (documented here as
  the byte0 bit0 equivalent, unverified against a real `status-get` response)
- Device-level masks `modes` / `vane-ver` / `vane-hor` come through as hex
  strings once set in XML, and are **live** — re-read every poll, do not
  cache at entity creation (observed `vane-hor` change between sessions on `1:101`)
- `fans` mask is **never** returned via API regardless of XML config —
  [BUG-001](../bugs.md#bug-001) — always assume default `0x1F`
- `modes` on plain `AC` (not `conditioner`) reads correctly — confirmed live
  on `1:101` (`modes="0x1A"` → exposes off/cool/heat/auto only)

## Script

Read: 9 bytes ([BUG-004](../bugs.md#bug-004) — vendor wiki says 8, verified working with 9)

- byte 0 — status: bit0 on/off, bits4-7 mode as a number (0 fan, 1 cool, 2 dry, 3 heat, 4 auto)
- byte 1 — fan speed
- byte 2 — setpoint, °C, integer
- byte 3 — reserved
- byte 4 — reserved
- byte 5 — current temp, fractional part: `(t%10)*250/10`
- byte 6 — current temp, integer part: `t/10`
- byte 7 — reserved
- byte 8 — alarm flag (0=ok, 1=alarm)

```c
V-ID/WGT_AC {
    u8 state = opt(0) & 0x01;
    u8 mode  = (opt(0) >> 4) & 0x0F;
    u8 sp    = opt(2);
    u8 fan   = opt(1);
}
```

Write: `setStatus(WGT_AC, {(mode<<4)+state, fan, setpoint, 0, 0, (temp%10)*250/10, temp/10, 0, alarm}, 9)`

## Notes

Most complex widget in the system. Used for HVAC, ventilation, heat pumps,
DHW control. **API and script encodings are independent** — the API `fan`
string enum and the script's numeric fan-speed byte do not map 1:1, and
neither has been proven to line up with the XML `fans` bitmask bit
positions live (that mask can't even be read back — see BUG-001).

<!-- Add live-tested quirks here as found. -->

- (2026-08-18) **Resolves the earlier "immediate verify may show stale state" note: it was write latency, not a failure.** Re-tested on `1:101` with a proper confirmation flow — subscribe to the device, send `status-set`, wait up to 1s for the controller's own pushed `statuses` event instead of reading immediately. Under that flow, `{"state": "on", "target": 24.0}` confirmed via the push at `after={'state': 'on', 'target': 24.0}`, no mismatch, and the restore round-trip also confirmed clean. An immediate `status-get` right after the ack is simply too fast for this type; waiting for the push (or an explicit 1s-delayed read) is required.

- (2026-08-18) `vane-ver` / `vane-hor` exist at **two levels with different meanings and types**: device-level (`'0x7F'`, hex string) is the capability mask, while `status.vane-ver` / `status.vane-hor` (int, e.g. 6 and 2) is the *current position*. Same key name, different value type depending on where you read it — do not conflate them.

- (2026-08-18) Full status key set confirmed live on `1:101` (stand, 89-device object): `{state, auto-state, target, current, mode, fan, vane-hor, vane-ver}`. `state` is real and present — the earlier "exact API key not yet confirmed live" caveat is resolved. `target` is the setpoint (float °C) and `current` the measured temperature; neither was previously documented for this type.

## Known bugs

- [BUG-001](../bugs.md#bug-001) — `fans` mask never returned via API2
- [BUG-003](../bugs.md#bug-003) — fan speeds 4/5/silent unreadable
- [BUG-004](../bugs.md#bug-004) — official wiki documents 8 status bytes, actual is 9
