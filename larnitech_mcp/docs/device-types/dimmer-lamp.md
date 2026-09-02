Digest of this file lives in [device_types.md](_device_types.md#dimmer-lamp) — keep both in sync.

## XML attributes

Source: https://wiki.larnitech.com/Dimmer-lamp

| Attribute | Type | Description | Default | Values |
|---|---|---|---|---|
| `addr` | string | device address | required | `"ID:SUBID"`, e.g. `"100:10"` |
| `name` | string | device identifier | required | any |
| `type` | — | fixed | required | `"dimmer-lamp"` |
| `auto-period` | integer | automation interval | optional | seconds, e.g. `600` |
| `system` | boolean | system device flag | optional | `yes`/`no` |
| `color-temp` | string | color-temperature control dimmer | optional | `"dimmer ID:SUBID"` |
| `color-white` | string | white-brightness control dimmer | optional | `"dimmer ID:SUBID"` |
| `virtual` | — | script-tracked widget | — | `yes` |
| `image` | string | UI icon | optional | e.g. `pump` |

## API

- `state`: on/off
- `level`: **integer percent, 0-100** — not the script byte's raw 0-250
  range, and not a 0.0-1.0 fraction. Confirmed live 2026-08-14.
- `color-temp`: integer percent, same 0-100 scale as `level`

## Motion automations

Carries the same `<automation>` motion rules as `lamp` — `on-by-moving`, `off-by-moving`, `off-by-door`, invisible through API2 apart from the `auto-state` flag. Documented once in [lamp.md](lamp.md#motion-automations-automation).

## Script

Status bytes (2 bytes read-back):
- byte 0 — status bits: bit0 on/off, bit3 automation, bit7 alarm
- byte 1 — brightness, **0-250** (not 255)

`setStatus` — two formats:
- **1 byte:** on/off only — `{0}` off, `{1}` on, `{0xFF}` toggle
- **3 bytes:** `{state, brightness, time_sec}` — state: 0 off/1 on/0xFE no
  change/0xFF toggle; brightness: 0 off, 1-250 level, 0xFE no change;
  time_sec: transition time in seconds (0 = instant)

```c
V-ID/WGT_DIM {
    u8 state = opt(0) & 0x01;
    u8 brightness = opt(1);     // 0-250
}
```

## Notes

The API's `level` (0-100 percent) and the script's raw brightness byte
(0-250) are two different scales for the same physical value — do not pass
one where the other is expected. Roughly `level = brightness / 2.5`.

<!-- Add live-tested quirks here as found. -->

## Known bugs

None recorded yet.
