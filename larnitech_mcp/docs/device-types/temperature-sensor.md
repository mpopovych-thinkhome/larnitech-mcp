<a id="temperature-sensor"></a>

Index entry (status keys and issue titles only): [_device_types.md](_device_types.md#temperature-sensor) — keep those in sync.

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

Status bytes (2 bytes), a signed fixed-point value:
- byte 0 — fraction × 256 (0…255, always positive)
- byte 1 — whole degrees, signed, **rounded down**

`value` = temperature × 10 (e.g. from Modbus with scale 0.1). For negatives the whole part is rounded down and the fraction counted up from it: −5.3 °C = −6 + 179/256.

```c
// value x10 -> status; works for negatives
i16 _int  = value / 10;
i16 _frac = value % 10;
if (_frac < 0) {          // C division truncates toward zero
    _int = _int - 1;
    _frac = _frac + 10;
}
setStatus(WGT_TEMP, {_frac*256/10, _int});
```

**Wrong for negatives:** `{(value % 10) * 256 / 10, value / 10}` — −5.3 °C becomes −5 + 180/256 = −4.3 °C. Fine only for values ≥ 0; it was in TCL, WallPanel_ISMA and the old block (fixed in HeatPump_Nibe V0.2, confirmed live: glycol −1.8 °C shown correctly on object 194, 2026-10-21).

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
