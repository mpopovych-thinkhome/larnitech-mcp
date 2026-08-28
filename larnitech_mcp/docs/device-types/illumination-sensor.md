Digest of this file lives in [device_types.md](_device_types.md#illumination-sensor) — keep both in sync.

## XML attributes

Source: https://wiki.larnitech.com/Illumination-sensor

| Attribute | Type | Description | Default | Values |
|---|---|---|---|---|
| `addr` | string | device address | — | e.g. `"333:11"` |
| `name` | string | device identifier | — | any |
| `type` | — | fixed | — | `"illumination-sensor"` |
| `scale` | string | display range | `auto` | `auto` or `"MIN:MAX"` |
| `value-min` | integer | min indication-bar value | 0 | — |
| `value-max` | integer | max indication-bar value | 100 | — |

```xml
<item addr="333:11" name="Illumination" type="illumination-sensor" scale="auto"/>
```

## API

- `state`: numeric light level (read-only, no write documented)

## Script

Status (2 bytes), read-only: byte 0 fractional, byte 1 integral.

## Notes

Read-only, no discrete states — continuous range only.

<!-- Add live-tested quirks here as found. -->

## Known bugs

None recorded yet.
