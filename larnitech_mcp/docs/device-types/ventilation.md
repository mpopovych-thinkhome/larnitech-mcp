Digest of this file lives in [device_types.md](_device_types.md#ventilation) — keep both in sync.

`type="virtual" sub-type="ventilation"` — see also [virtual.md](virtual.md)
for the other `virtual` sub-types.

## XML attributes

Source: https://wiki.larnitech.com/Ventilation

| Attribute | Type | Description | Default | Values |
|---|---|---|---|---|
| `addr` | string | device address | required | — |
| `length` | integer | status data length, bytes | 6 | — |
| `name` | string | device identifier | `"Ventilation"` | any |
| `sub-type` | — | fixed | `"ventilation"` | `"ventilation"` |
| `type` | — | fixed | `"virtual"` | `"virtual"` |
| `funs` | bitmask | mask of airflow modes | `0xFF` | — |
| `temperature-sensors` | list | sensor address(es) feeding `current`/`target` | — | e.g. `"119:10"` — confirmed live 2026-08-18, absent from the official page |

`import-script` element supports `VENT`, `RS485`, `path` parameters for
control-script configuration.

## API

Live-tested status: `{"state": "off"/"on", "target": <setpoint>, "current": <temp>, "fan": "auto"}`.

- `fan` is a **string preset** (e.g. `"auto"`) here — unlike [vent](vent.md)
  below, where `fan` is a number. Same key name, two different value types
  depending on `sub-type`/`type` — always check the device's `type` before
  assuming `fan`'s shape.
- `target`/`current` — real temperature setpoint/reading, present only when
  `temperature-sensors` is configured (XML, see above) — see Notes.

Typical hardware: Komfovent-class ventilation units.

## Script

6-byte status:
- byte 0 — power state, bit0 (0 off, 1 on)
- byte 1 — temperature, bits 0-3 = value + 16 offset
- byte 4 — airflow capacity, bits 0-3

Status setting: values set "from the 1st to the 6th correspondingly" (bytes 1-6).

## Notes

Do not confuse with [vent.md](vent.md) — same-sounding name, different
type, different `fan` value shape.

<!-- Add live-tested quirks here as found. -->

- (2026-08-18) `target`/`current` are real, but **conditional on XML config**: only present in `status` once `temperature-sensors` is set on the widget (see XML table above) — a widget without it never carries either key, confirmed by toggling the attribute live on a test widget. Corrects an earlier version of this file which assumed `target` wasn't used by anything.

## Known bugs

None recorded yet.
