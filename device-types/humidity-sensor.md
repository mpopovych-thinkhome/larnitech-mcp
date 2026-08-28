Digest of this file lives in [device_types.md](_device_types.md#humidity-sensor) — keep both in sync.

## XML attributes

Source: https://wiki.larnitech.com/Humidity-sensor

| Attribute | Type | Description | Default | Values |
|---|---|---|---|---|
| `addr` | string | device address | — | `"###:##"` |
| `name` | string | device identifier | — | any |
| `type` | — | fixed | — | `"humidity-sensor"` |
| `scale` | string | display range | — | `auto` or `"MIN:MAX"` |
| `value-min` | integer | min indication-bar value | 0 | — |
| `value-max` | integer | max indication-bar value | 100 | — |

```xml
<item addr="333:13" name="Humidity" type="humidity-sensor" scale="auto"/>
```

## API

- `current-humidity`: float, % (read-only per vendor docs — no write path
  documented)

## Script

Status (2 bytes), read-only:
- byte 0 — fractional value
- byte 1 — integer value

## Notes

Vendor docs don't distinguish separate read/write capability — treat as
sensor/read-only.

<!-- Add live-tested quirks here as found. -->

## Known bugs

None recorded yet.
