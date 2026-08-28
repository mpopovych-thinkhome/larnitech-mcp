Digest of this file lives in [device_types.md](_device_types.md#leak-sensor) — keep both in sync.

## XML attributes

Not yet pulled from the vendor wiki — add when needed.

## API

Normal (non-fault) status shape is **unconfirmed** this session.

Confirmed live on a real device (not the test stand): `leak-sensor` can
report a fault via
```json
{"malfunction": <code>}
```
**instead of** its normal state — a companion "sensor itself is broken"
signal, separate from "leak detected". Code values not yet enumerated.

## Script

Not documented.

## Notes

`malfunction` appears to replace the normal status key entirely when
active, rather than being an additional field alongside it — treat a
`malfunction` key as "sensor health fault", not as a leak reading.

<!-- Add live-tested quirks here as found. -->

- (2026-08-20/21) `malfunction` fault-status key confirmed live on a real
  (non-stand) device. Normal status shape not yet confirmed.

## Known bugs

None recorded yet.
