Digest of this file lives in [device_types.md](_device_types.md#motion-sensor) — keep both in sync.

## XML attributes

Source: https://wiki.larnitech.com/Motion-sensor

| Attribute | Type | Description | Default | Values |
|---|---|---|---|---|
| `addr` | string | device address | — | e.g. `"333:10"` |
| `name` | string | device identifier | — | any |
| `type` | — | fixed | — | `"motion-sensor"` |
| `scale` | string | range spec | — | `"0:100"` or `auto` |
| `value-min` | integer | min indication-bar value | 0 | — |
| `value-max` | integer | max indication-bar value | 100 | — |

## API

- `state`: documented as the key status field, but see the mismatch below.

⚠️ **Unresolved conflict** — see Notes.

## Script

Status (2 bytes) per the official page: byte 0 fractional, byte 1
integral — a **continuous-range encoding**, no enumerated on/off values.

## Notes

**Mismatch, not yet resolved:** a motion sensor is conceptually a
boolean/triggered device (motion detected / not detected), but the vendor
page documents this type with the same continuous fractional/integral
2-byte encoding used for temperature/humidity/illumination sensors, and
gives no discrete "motion detected" value. Either the vendor page is a
generic sensor template misapplied here, or `state` decodes to something
non-boolean via API2 (e.g. a numeric level). Verify against a live device
before assuming `state` is a simple on/off boolean.

<!-- Add live-tested quirks here as found. -->

## Known bugs

None recorded yet.
