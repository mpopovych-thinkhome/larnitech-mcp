Digest of this file lives in [device_types.md](_device_types.md#temperature-sensor) — keep both in sync.

## XML attributes

Source: https://wiki.larnitech.com/Temperature-sensor

| Attribute | Type | Description | Default | Values |
|---|---|---|---|---|
| `addr` | string | device address | — | e.g. `"333:12"` |
| `name` | string | device identifier | — | any |
| `type` | — | fixed | — | `"temperature-sensor"` |
| `scale` | string | display range | — | `auto` or `"MIN:MAX"` |
| `log-levels` | list | server log warning/error/emergency thresholds | `60,80,90` | — |
| `value-min` | integer | min indication-bar value | 16 | — |
| `value-max` | integer | max indication-bar value | 32 | — |

## API

- `state`: float, °C

## Script

Status bytes (2 bytes):
- byte 0 — fractional part: `(value % 10) * 256 / 10`
- byte 1 — integer part: `value / 10`

Where `value` = temperature × 10 (e.g. from Modbus with scale 0.1).

```c
i16 temp = mbs_values[REG_TEMP];  // e.g., 235 = 23.5°C
setStatus(WGT_TEMP, {(temp % 10) * 256 / 10, temp / 10});
```

**Note:** the fractional encoding differs from the `AC` widget (×250/10
there vs ×256/10 here).

Reading back (decode) — the fractional byte spans the full 0-255 range; to
recover `value` (temp × 10):

```c
i16 value = [SENSOR.1]*10 + [SENSOR.0]*10/255;
```

**Do NOT use `[SENSOR.0]/26`** — it under-reads: byte 230 (.9) gives
`230/26 = 8` instead of 9. The `*10/255` form round-trips correctly with
the `*256/10` write (which truncates 230.4 → 230, so `/256` also
under-reads — use `/255`).

## Notes

The official page's byte description ("byte0 fractional, byte1 integral")
is correct but coarser than the working decode formula above — keep the
`*10/255` note, it is the one that actually round-trips.

<!-- Add live-tested quirks here as found. -->

## Known bugs

None recorded yet.
