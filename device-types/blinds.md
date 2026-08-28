Digest of this file lives in [device_types.md](_device_types.md#blinds) — keep both in sync.

## XML attributes

Not yet pulled from the vendor wiki — add when needed.

## API

Confirmed live 2026-08-20 on object `a1b2c3d4`: has a real
`position`/`target` numeric field on a **0-100 scale**, where Larnitech's
own convention is **0 = fully open, 100 = fully closed** — inverted from
what you'd naturally guess (most systems have "position" mean "how open").

A moving motor can transiently read slightly past either end (e.g. `-2` or
`102`) — this is motor coast, not a bug.

## Script

Not documented.

## Notes

**Distinct control model from [jalousie](jalousie.md)/[gate](gate.md).**
Those types have no position at all — state-only, verb-form open/close
writes. `blinds` is a genuine position/target device. Don't conflate the
two.

<!-- Add live-tested quirks here as found. -->

- (2026-08-20) `position`/`target` 0-100 scale and inverted (0=open,
  100=closed) convention confirmed live on `a1b2c3d4`; overshoot past 0/100
  during motion also observed.

## Known bugs

None recorded yet.
