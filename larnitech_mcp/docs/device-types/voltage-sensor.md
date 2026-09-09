Digest of this file lives in [device_types.md](_device_types.md#voltage-sensor) — keep both in sync.

## XML attributes

No vendor wiki page. Plain item, seen with `area: "Setup"`.

## API

A simple scalar readout of voltage. Read-only:

```json
{"state": 16}
```

Confirmed live 2026-09-04 across four devices, which read 16, 17, 18 and
one more in the same range — plausible for a low-voltage bus, but the unit
and any scaling factor are unconfirmed.

## Script

Not documented.

## Notes

Same family as [current-sensor](current-sensor.md),
[percent-sensor](percent-sensor.md) and [float-sensor](float-sensor.md) —
generic scalar readouts differing in display formatting.

<!-- Add live-tested quirks here as found. -->

## Known bugs

None recorded yet.
