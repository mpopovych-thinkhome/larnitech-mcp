Digest of this file lives in [device_types.md](_device_types.md#lamp) — keep both in sync.

## XML attributes

Source: https://wiki.larnitech.com/Lamp_element

| Attribute | Type | Description | Default | Values |
|---|---|---|---|---|
| `addr` | string | device address | required | `"XXX:XX"` |
| `name` | string | device identifier | required | any |
| `type` | — | fixed | required | `"lamp"` |
| `sub-type` | enum | device variant | optional | `damper`, `air-fan`, `socket`, `lock`, `dehumidifier`, `closing-switch`, `valve-3`, `pump` |
| `auto-period` | integer | automation period | optional | seconds, default 600 |
| `system` | boolean | system device flag | optional | `yes`/`no` |
| `image` | string | UI icon identifier | optional | e.g. `pump` |
| `virtual` | — | script-tracked widget | — | `yes` |

## API

- `state`: on/off
- `auto-state`: boolean, present on plain (no sub-type) lamps

Sub-type behavior confirmed live:
- **`lock`** — polarity is inverted: `state=off` means "locked". Do not
  assume intuitive "on = locked".
- **`closing-switch`** ("impulse closer" per description) — behaves in
  practice as a normal persistent on/off switch, not an impulse/momentary
  output.

## Script

Status byte (1 byte):
- bit0 — power (0 off, 1 on)
- bit3 — automation (0 disabled, 1 enabled)
- bit7 — alarm (0 none, 1 active)

`setStatus(WGT_LAMP, {state})` — 0 off, 1 on, 0xFF toggle.

```xml
<additem type="lamp" sub-type="pump" virtual="yes" name="..."/>
```

## Notes

Generic on/off indicator widget — used for pumps, valves, relays, locks,
and switches via `sub-type`. `sub-type` changes semantics, not just the UI
icon (see `lock`/`closing-switch` above) — never assume a sub-type behaves
like plain on/off without checking here first.

<!-- Add live-tested quirks here as found. -->

## Known bugs

None recorded yet.
