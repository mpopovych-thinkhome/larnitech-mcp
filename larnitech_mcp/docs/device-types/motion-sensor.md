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

- `state`: **a continuous number, not a boolean.** Confirmed live on `3:30`
  (demo case): read `39.65` on one poll and `0.0` on later polls. The
  vendor page was right and the earlier digest — which called this a
  boolean — was wrong.

Read as a motion *level* against a threshold, not as "detected / not
detected". This is exactly how the controller's own automations use it:
an `<automation>` rule carries a `motion-level` threshold, with a higher
value for switching on than for switching off — see
[lamp](lamp.md#motion-automations-automation).

## Script

Status (2 bytes) per the official page: byte 0 fractional, byte 1
integral — a **continuous-range encoding**, no enumerated on/off values.

## Notes

**Resolved 2026-09-02.** The conflict was between a digest that assumed a
boolean and a vendor page documenting a continuous 2-byte encoding. Live
readings settle it in the vendor page's favour: `39.65`, then `0.0`. There
is no discrete "motion detected" value — the caller picks a threshold.

The scale is not established: `39.65` was the highest value seen, and
nothing is known about its ceiling or units.

<!-- Add live-tested quirks here as found. -->

## Known bugs

None recorded yet.
