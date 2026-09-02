Digest of this file lives in [device_types.md](_device_types.md#rgb-lamp) — keep both in sync.

## XML attributes

Source: https://wiki.larnitech.com/RGB-lamp (page not directly reachable at
fetch time — attributes below are inferred from the parallel `Dimmer-lamp`
page structure, which the vendor wiki documents identically; verify against
the live page when convenient).

| Attribute | Type | Description | Default | Values |
|---|---|---|---|---|
| `addr` | string | device address | required | `"ID:SUBID"` |
| `name` | string | device identifier | required | any |
| `type` | — | fixed | required | `"rgb-lamp"` |
| `auto-period` | integer | automation interval | optional | seconds |
| `system` | boolean | system device flag | optional | `yes`/`no` |
| `color-temp` | string | color-temperature dimmer control | optional | `"ID:SUBID"` |
| `color-white` | string | white-brightness dimmer control | optional | `"ID:SUBID"` |

## API

- `level`, `saturation`, `hue`: all **integer percent 0-100**, including `hue`.
  Confirmed live 2026-08-14.
- `hue` is a position on the color wheel **in percent**, not degrees 0-360 —
  selecting green (120°) rendered orange, blue (240°) rendered acid-yellow
  until scaled: multiply by 3.6 to get degrees on read, divide by 3.6 on
  write.

## Motion automations

Carries the same `<automation>` motion rules as `lamp` — `on-by-moving`, `off-by-moving`, `off-by-door`, invisible through API2 apart from the `auto-state` flag. Documented once in [lamp.md](lamp.md#motion-automations-automation).

## Script

Device status (4 bytes), VSH color system:
- byte 0 — status/flags: bit0 on/off, bit3 automation, bit7 alarm
- byte 1 — brightness (V), 0-250
- byte 2 — saturation (S), 0-250
- byte 3 — hue (H), 0-250

`setStatus` formats:
- **1 byte:** status only — 0 off, 1 on, 0xFF toggle
- **4 bytes:** status, brightness, saturation, hue (0xFE = unchanged, 0xFF
  toggle status)
- **5 bytes:** adds transition time (×0.1 s)

## Notes

Three independent 0-100 percent scales at the API level (`level`,
`saturation`, `hue`) map to three 0-250 byte scales at the script level —
same relationship as [dimmer-lamp](dimmer-lamp.md)'s `level`/brightness,
but `hue` additionally needs the ×3.6/÷3.6 degree conversion that the other
two don't.

<!-- Add live-tested quirks here as found. -->

## Known bugs

None recorded yet.
